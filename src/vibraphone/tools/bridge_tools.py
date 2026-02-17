"""GSD-to-Beads bridge tools - imports GSD plans into Beads tasks."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from vibraphone.config import get_config, get_project_root
from vibraphone.server import mcp
from vibraphone.utils.cli_runner import CliError, run_cli
from vibraphone.utils.errors import TaskError
from vibraphone.utils.plan_parser import (
    extract_frontmatter,
    extract_tasks_from_xml,
)

# Regex for plan file matching
_PLAN_FILE_RE = re.compile(r"^(\d+-\d+)-PLAN\.md$")


def _resolve_phase_dir(phase_number: int) -> Path | None:
    """Locate the phase directory for a given phase number.

    Searches in .planning/phases/ for directories matching patterns like:
    - 06-bridge-stack-tools (phase number as prefix)
    """
    project_root = get_project_root()
    phases_dir = project_root / ".planning" / "phases"

    if not phases_dir.exists():
        return None

    # Look for phase directories with the phase number as prefix
    for entry in sorted(phases_dir.iterdir()):
        if entry.is_dir():
            # Match patterns like "06-bridge-stack-tools"
            parts = entry.name.split("-", 1)
            if parts and parts[0].isdigit() and int(parts[0]) == phase_number:
                return entry

    return None


async def _existing_plan_ids() -> set[str]:
    """Return plan IDs that already have Beads tasks (for idempotency).

    Uses br list --json and extracts plan: labels.
    """
    try:
        result = await run_cli("br", "list", "--json", cwd=get_project_root())
    except CliError:
        return set()

    items = result.get("issues", [])
    ids = set()
    for item in items:
        for label in item.get("labels", []):
            if isinstance(label, str) and label.startswith("plan:"):
                ids.add(label.removeprefix("plan:"))
    return ids


async def _create_beads_task(
    plan_id: str,
    task_idx: int,
    task_data: dict,
    task_name_to_id: dict[str, str],
) -> tuple[str, str]:
    """Create a single Beads issue from a parsed task element.

    Args:
        plan_id: The plan ID (e.g., "06-02")
        task_idx: Index of the task in the plan (0-based)
        task_data: Parsed task dict with name, title, description, etc.
        task_name_to_id: Mapping of task names to Beads IDs (updated in place)

    Returns:
        Tuple of (beads_issue_id, task_name)
    """
    # Prefer name over title, fall back to "Task N"
    task_name = task_data.get("name") or task_data.get("title") or f"Task {task_idx + 1}"
    title_text = task_name

    # Build title as "[{plan_id}] {title_text}"
    title = f"[{plan_id}] {title_text}"

    # Get description from action or description field
    description = task_data.get("description") or task_data.get("action") or ""

    # Add plan:{plan_id} label for idempotency
    labels = f"plan:{plan_id}"

    # Get type from task_data, default to "task"
    type_ = task_data.get("type", "task")
    # Handle type="auto" - map to "task" since beads may not have "auto"
    if type_ == "auto":
        type_ = "task"

    # Build br create arguments
    args = ["create", title, "--json"]
    if description:
        # Truncate description if too long (beads may have limits)
        desc_clean = description[:2000] if len(description) > 2000 else description
        args.extend(["--description", desc_clean])
    if type_:
        args.extend(["--type", type_])
    if labels:
        args.extend(["--labels", labels])

    result = await run_cli("br", *args, cwd=get_project_root())
    beads_id = str(result.get("id", ""))

    # Update the mapping
    task_name_to_id[task_name] = beads_id

    return beads_id, task_name


async def _setup_plan_dependencies(
    plan_tasks: dict[str, list[str]],  # plan_id -> list of beads issue IDs
    plan_deps: dict[str, list[str]],  # plan_id -> list of depends_on plan IDs
    task_blocked_by: dict[str, str],  # task_name -> blocker_task_name (from XML)
    task_name_to_id: dict[str, str],  # task_name -> beads issue ID
    task_id_to_name: dict[str, str],  # beads issue ID -> task_name
) -> list[dict]:
    """Wire up intra-plan and inter-plan dependencies.

    CRITICAL: Per CONTEXT.md decisions:
    - Intra-plan: explicit ONLY via <blocked_by> - NO implicit sequential
    - Inter-plan: first task of dependent blocked by last task of dependency
    """
    deps_created = []

    for plan_id, task_ids in plan_tasks.items():
        # Intra-plan deps: ONLY if <blocked_by> specified (no implicit!)
        for task_id in task_ids:
            task_name = task_id_to_name.get(task_id, "")
            if task_name in task_blocked_by:
                blocker_name = task_blocked_by[task_name]
                blocker_id = task_name_to_id.get(blocker_name)
                if blocker_id:
                    try:
                        await run_cli(
                            "br",
                            "dep",
                            "add",
                            task_id,
                            blocker_id,
                            "--type",
                            "blocks",
                            cwd=get_project_root(),
                        )
                        deps_created.append({
                            "blocked": task_id,
                            "blocker": blocker_id,
                            "type": "intra-plan",
                            "blocked_name": task_name,
                            "blocker_name": blocker_name,
                        })
                    except CliError:
                        # Dependency may already exist, continue
                        pass

        # Inter-plan deps: first task blocked by last task of each dep plan
        if plan_id in plan_deps and task_ids:
            first_task = task_ids[0]
            for dep_plan_id in plan_deps[plan_id]:
                dep_task_ids = plan_tasks.get(dep_plan_id, [])
                if dep_task_ids:
                    last_dep_task = dep_task_ids[-1]
                    try:
                        await run_cli(
                            "br",
                            "dep",
                            "add",
                            first_task,
                            last_dep_task,
                            "--type",
                            "blocks",
                            cwd=get_project_root(),
                        )
                        deps_created.append({
                            "blocked": first_task,
                            "blocker": last_dep_task,
                            "type": "inter-plan",
                            "blocked_plan": plan_id,
                            "blocker_plan": dep_plan_id,
                        })
                    except CliError:
                        # Dependency may already exist, continue
                        pass

    return deps_created


def _extract_blocked_by_from_tasks(tasks: list[dict]) -> dict[str, str]:
    """Extract task_name -> blocker_name mapping from task list.

    Looks for <blocked_by> elements in each task.
    """
    blocked_by = {}
    for task in tasks:
        task_name = task.get("name") or task.get("title", "")
        blocker = task.get("blocked_by", "").strip()
        if task_name and blocker:
            blocked_by[task_name] = blocker
    return blocked_by


@mcp.tool
async def import_gsd_plan(phase_number: int, *, preview: bool = True) -> dict[str, Any]:
    """Import all GSD PLAN.md files for a phase into Beads tasks.

    Two-phase flow:
    - preview=True: returns what would be imported without creating tasks
    - preview=False: creates tasks, wires dependencies, syncs

    Idempotent: plans with existing plan:<id> labels are skipped.

    Args:
        phase_number: The GSD phase number to import (e.g., 6).
        preview: If True, return preview without creating tasks.

    Returns:
        dict with status, tasks_created (or tasks_preview), dependencies, next_steps.
        Returns TaskError dict on validation or configuration errors.
    """
    # Check for components config
    config = get_config()
    if not config.components:
        return TaskError(
            error_type="NoComponentsConfigured",
            message="No components configured in vibraphone.yaml",
            suggested_action="Configure components in vibraphone.yaml before importing plans, or use configure_stack to set up the project",
        ).model_dump()

    # Resolve phase directory
    phase_dir = _resolve_phase_dir(phase_number)
    if phase_dir is None:
        return TaskError(
            error_type="PhaseDirectoryNotFound",
            message=f"Phase directory not found for phase {phase_number}",
            suggested_action=f"Ensure .planning/phases/{phase_number:02d}-<name>/ directory exists with PLAN.md files",
        ).model_dump()

    # Discover plan files matching NN-NN-PLAN.md
    plan_files = []
    for path in sorted(phase_dir.iterdir()):
        match = _PLAN_FILE_RE.match(path.name)
        if match:
            plan_files.append((match.group(1), path))

    if not plan_files:
        return TaskError(
            error_type="NoPlanFilesFound",
            message=f"No PLAN.md files found in {phase_dir}",
            suggested_action=f"Create plan files matching NN-NN-PLAN.md pattern in {phase_dir}",
        ).model_dump()

    # Idempotency check - skip plans with existing plan:<id> labels
    existing = await _existing_plan_ids()
    skipped = [pid for pid, _ in plan_files if pid in existing]
    plan_files = [(pid, p) for pid, p in plan_files if pid not in existing]

    if not plan_files:
        return {
            "status": "already_imported",
            "skipped_plans": skipped,
            "message": f"All plans for phase {phase_number} already imported.",
            "next_steps": ["1. Use list_tasks() to see imported tasks"],
        }

    # Parse all plans for validation and preview
    parsed_plans = []
    for plan_id, plan_path in plan_files:
        content = plan_path.read_text(encoding="utf-8")
        frontmatter = extract_frontmatter(content)
        tasks = extract_tasks_from_xml(content)

        parsed_plans.append({
            "plan_id": plan_id,
            "path": str(plan_path),
            "frontmatter": frontmatter,
            "tasks": tasks,
            "blocked_by": _extract_blocked_by_from_tasks(tasks),
        })

    # Fail-fast validation: check all plans have tasks
    for plan_data in parsed_plans:
        if not plan_data["tasks"]:
            return TaskError(
                error_type="PlanHasNoTasks",
                message=f"Plan {plan_data['plan_id']} has no tasks",
                suggested_action=f"Add <tasks> block with <task> elements to {plan_data['path']} or remove the file",
            ).model_dump()

    # Preview mode: return what would be imported
    if preview:
        preview_data = []
        for plan_data in parsed_plans:
            tasks = plan_data["tasks"]
            preview_data.append({
                "plan_id": plan_data["plan_id"],
                "depends_on": plan_data["frontmatter"].get("depends_on", []),
                "task_count": len(tasks),
                "task_titles": [
                    t.get("name") or t.get("title") or f"Task {i}"
                    for i, t in enumerate(tasks)
                ],
                "blocked_by": plan_data["blocked_by"],
            })

        return {
            "status": "preview",
            "phase_number": phase_number,
            "plans": preview_data,
            "skipped_plans": skipped,
            "next_steps": [
                "1. Review the plans to be imported",
                f"2. Call import_gsd_plan({phase_number}, preview=False) to create tasks",
            ],
        }

    # Create tasks for all plans
    plan_tasks: dict[str, list[str]] = {}  # plan_id -> list of beads issue IDs
    plan_deps: dict[str, list[str]] = {}  # plan_id -> list of depends_on plan IDs
    task_name_to_id: dict[str, str] = {}  # task_name -> beads issue ID
    task_id_to_name: dict[str, str] = {}  # beads issue ID -> task_name
    all_blocked_by: dict[str, str] = {}  # merged from all plans
    tasks_created = []

    for plan_data in parsed_plans:
        plan_id = plan_data["plan_id"]
        tasks = plan_data["tasks"]
        frontmatter = plan_data["frontmatter"]

        # Store inter-plan dependencies from frontmatter
        deps = frontmatter.get("depends_on", [])
        if deps:
            plan_deps[plan_id] = deps if isinstance(deps, list) else [deps]

        # Create tasks for this plan
        plan_task_ids = []
        for idx, task in enumerate(tasks):
            beads_id, task_name = await _create_beads_task(
                plan_id, idx, task, task_name_to_id
            )
            plan_task_ids.append(beads_id)
            task_id_to_name[beads_id] = task_name

            tasks_created.append({
                "plan_id": plan_id,
                "beads_id": beads_id,
                "task_name": task_name,
            })

        plan_tasks[plan_id] = plan_task_ids

        # Merge blocked_by mappings
        all_blocked_by.update(plan_data["blocked_by"])

    # Wire up dependencies (intra-plan and inter-plan)
    dependencies = await _setup_plan_dependencies(
        plan_tasks,
        plan_deps,
        all_blocked_by,
        task_name_to_id,
        task_id_to_name,
    )

    # Sync with beads
    try:
        await run_cli("br", "sync", "--flush-only", cwd=get_project_root())
    except CliError:
        # Sync may fail if there are issues, but tasks are already created
        pass

    return {
        "status": "imported",
        "phase_number": phase_number,
        "tasks_created": tasks_created,
        "total_tasks": len(tasks_created),
        "dependencies": dependencies,
        "skipped_plans": skipped,
        "next_steps": [
            "1. Use next_ready() to get the first task to work on",
            "2. Use list_tasks() to see all imported tasks",
        ],
    }
