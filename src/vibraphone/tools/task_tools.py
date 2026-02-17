"""Task management MCP tools for vibraphone.

This module contains MCP tool implementations for task management operations
with br/bv CLIs. Tools follow the error handling pattern from CONTEXT.md.
"""

import re
import subprocess
from pathlib import Path

from pydantic import BaseModel

from vibraphone.server import mcp
from vibraphone.utils.cli_runner import CliError, run_cli


class TaskError(BaseModel):
    """Structured error response per CONTEXT.md locked decision.

    Provides consistent error format for task management tools with
    actionable guidance for users.
    """

    error_type: str  # e.g., "CannotCompleteBlockedTask"
    message: str  # Human-readable error message
    suggested_action: str  # What to do next


def get_project_root() -> Path:
    """Get project root directory for CLI commands.

    Returns the directory containing vibraphone.yaml or the current working
    directory if no config file is found.
    """
    from vibraphone.config import find_config_file

    config_path = find_config_file()
    if config_path is not None:
        return config_path.parent
    return Path.cwd()


@mcp.tool
async def list_tasks(status: str | None = None, plan: str | None = None) -> dict:
    """List tasks with optional filters.

    Args:
        status: Filter by status (ready, in_progress, completed, blocked)
        plan: Filter by plan/phase identifier

    Returns:
        Dict with tasks list, dependency graph, and total count.
        Tasks ordered by priority from beads_rust.
    """
    args = ["list", "--json"]

    if status is not None:
        args.extend(["--status", status])

    if plan is not None:
        args.extend(["--plan", plan])

    result = await run_cli("br", *args, cwd=get_project_root())

    tasks = result.get("issues", [])
    return {
        "tasks": tasks,
        "dependency_graph": result.get("dependency_graph", {}),
        "total": len(tasks),
    }


@mcp.tool
async def next_ready() -> dict:
    """Get the next unblocked task using critical path analysis.

    Uses PageRank/critical path algorithm from beads_viewer to identify
    the task that is most blocking or on the critical path.

    Returns:
        Dict with recommended task and claim command, or empty if none ready.
        Includes 'reason' explaining why this task was selected.
    """
    result = await run_cli("bv", "--robot-next", cwd=get_project_root())

    if not result.get("task"):
        return {"task": None, "message": "No ready tasks available"}

    return {
        "task": result["task"],
        "claim_command": result.get("claim_command"),
        "reason": result.get("reason", "critical path prioritization"),
    }


@mcp.tool
async def health_check() -> dict:
    """Check the health of the beads state.

    Returns graph metrics including PageRank, betweenness, critical path,
    cycle detection, and project health indicators.

    Returns:
        Dict with status, data_hash, as_of timestamp, and metrics dict.
    """
    result = await run_cli("bv", "--robot-insights", cwd=get_project_root())

    return {
        "status": result.get("status"),  # computed/approx/timeout/skipped
        "data_hash": result.get("data_hash"),
        "as_of": result.get("as_of"),
        "metrics": {
            "pagerank_top": result.get("pagerank", {}).get("top", []),
            "betweenness_top": result.get("betweenness", {}).get("top", []),
            "critical_path": result.get("critical_path", []),
            "cycles": result.get("cycles", []),
            "project_health": result.get("project_health", {}),
        },
    }


@mcp.tool
async def complete_task(task_id: str, notes: str | None = None) -> dict:
    """Mark a task as completed.

    Args:
        task_id: The task ID (e.g., bd-abc123)
        notes: Optional completion notes

    Returns:
        Updated task state and newly unblocked tasks.
        Returns TaskError if task is blocked.
    """
    # Verify task exists and is not blocked
    task = await run_cli("br", "show", task_id, "--json", cwd=get_project_root())

    if task.get("status") == "blocked":
        return TaskError(
            error_type="CannotCompleteBlockedTask",
            message=f"Task {task_id} is blocked by incomplete dependencies",
            suggested_action="Complete blocking tasks first or use abandon_task to reset",
        ).model_dump()

    # Complete the task
    args = ["close", task_id]
    if notes:
        args.extend(["--notes", notes])

    result = await run_cli("br", *args, cwd=get_project_root())

    return {
        "task": result.get("issue"),
        "unblocked": result.get("unblocked", []),
        "completed_at": result.get("closed_at"),
    }


@mcp.tool
async def abandon_task(task_id: str, reason: str) -> dict:
    """Abandon a task and reset its status to ready.

    Args:
        task_id: The task ID (e.g., bd-abc123)
        reason: Required reason for audit trail

    Returns:
        Updated task state with reason recorded.
    """
    # Reset status and capture reason
    args = ["update", task_id, "--status", "ready", "--notes", f"Abandoned: {reason}"]

    result = await run_cli("br", *args, cwd=get_project_root())

    return {
        "task": result.get("issue"),
        "abandoned_at": result.get("updated_at"),
        "reason": reason,
    }


def extract_mermaid_from_markdown(content: str) -> list[str]:
    """Extract mermaid code blocks from markdown content.

    Args:
        content: Markdown file contents

    Returns:
        List of mermaid diagram code blocks (without the ```mermaid wrappers).
    """
    pattern = r"```mermaid\n(.*?)```"
    return re.findall(pattern, content, re.DOTALL)


async def get_branch_commits(branch: str, limit: int = 5) -> list[dict]:
    """Get recent commits from a branch.

    Args:
        branch: Branch name to get commits from
        limit: Maximum number of commits to retrieve

    Returns:
        List of dicts with hash, subject, and date for each commit.
        Empty list if branch doesn't exist or git command fails.
    """
    import asyncio

    try:
        process = await asyncio.create_subprocess_exec(
            "git",
            "log",
            branch,
            f"--max-count={limit}",
            "--pretty=format:%H|%s|%ci",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=get_project_root(),
        )
        stdout_bytes, _ = await process.communicate()
        stdout = stdout_bytes.decode("utf-8", errors="replace")
    except (CliError, OSError, subprocess.SubprocessError):
        return []
    else:
        commits = []
        for line in stdout.strip().split("\n"):
            if line and "|" in line:
                parts = line.split("|", 2)
                if len(parts) == 3:
                    commits.append(
                        {
                            "hash": parts[0],
                            "subject": parts[1],
                            "date": parts[2],
                        }
                    )
        return commits


@mcp.tool
async def get_task_context(task_id: str) -> dict:
    """Load focused context bundle for a task.

    Returns task details, mermaid diagrams from architecture.md,
    and recent commits on the task branch.

    Args:
        task_id: The task ID (e.g., bd-abc123)

    Returns:
        Dict with task details, architecture diagrams, and git context.
    """
    # Get task details
    task = await run_cli("br", "show", task_id, "--json", cwd=get_project_root())

    # Read architecture.md for mermaid diagrams
    arch_path = get_project_root() / "docs" / "architecture.md"
    mermaid_diagrams = []
    if arch_path.exists():
        content = arch_path.read_text()
        mermaid_diagrams = extract_mermaid_from_markdown(content)

    # Get recent commits on task branch (if available)
    branch_name = task.get("branch")
    commits = []
    if branch_name:
        commits = await get_branch_commits(branch_name, limit=5)

    return {
        "task": task,
        "architecture_diagrams": mermaid_diagrams,
        "recent_commits": commits,
    }
