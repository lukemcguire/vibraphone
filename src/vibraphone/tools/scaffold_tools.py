"""Scaffolding tools for initializing vibraphone in projects."""

from __future__ import annotations

import sys
from difflib import unified_diff
from pathlib import Path
from typing import Any

from vibraphone.mcp_instance import mcp
from vibraphone.utils.auto_detect import detect_project_metadata
from vibraphone.utils.prerequisites import check_prerequisites as check_prereqs
from vibraphone.utils.template_loader import (
    get_all_template_paths,
    load_template,
    render_template,
)


def _progress(message: str, status: str = "OK") -> None:
    """Print progress step with status indicator."""
    indicators = {
        "OK": "\u2713",  # checkmark
        "FAIL": "\u2717",  # x mark
        "SKIP": "\u2192",  # arrow
    }
    indicator = indicators.get(status, status)
    print(f"{message}... {indicator}", file=sys.stderr)


def _celebration_message(project_name: str) -> str:
    """Generate celebratory success message with ASCII art."""
    return f"""
\u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510
\u2502  Vibraphone initialized!                    \u2502
\u2502                                            \u2502
\u2502  Project: {project_name:<30} \u2502
\u2502                                            \u2502
\u2502  Next steps:                                \u2502
\u2502  1. Run 'just bootstrap'                     \u2502
\u2502  2. Add tasks via br add                     \u2502
\u2502  3. Use MCP tools to execute tasks          \u2502
\u2502                                            \u2502
\u2502  Docs: https://github.com/lukemcguire/      \u2502
\u2502       vibraphone#readme                     \u2502
\u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518
"""


def _generate_diff(path: Path, existing: str, proposed: str) -> str:
    """Generate unified diff for conflict display."""
    existing_lines = existing.splitlines(keepends=True)
    proposed_lines = proposed.splitlines(keepends=True)
    return "".join(
        unified_diff(
            existing_lines,
            proposed_lines,
            fromfile=f"{path} (existing)",
            tofile=f"{path} (proposed)",
        )
    )


def _render_all_templates(variables: dict[str, Any]) -> dict[str, str]:
    """Render all templates with the given variables.

    Returns dict mapping relative destination path to rendered content.
    """
    rendered: dict[str, str] = {}
    template_paths = get_all_template_paths()

    for template_path in template_paths:
        # Skip __init__.py and __pycache__
        if "__init__" in template_path or "__pycache__" in template_path:
            continue

        content = load_template(template_path)

        # Determine destination path (remove .j2 extension for Jinja templates)
        dest_path = template_path[:-3] if template_path.endswith(".j2") else template_path

        # Render if it's a Jinja template (check for {{ in content)
        if "{{" in content or "{%" in content:
            rendered[dest_path] = render_template(content, variables)
        else:
            rendered[dest_path] = content

    return rendered


def _check_conflicts(project_root: Path, proposed_files: dict[str, str]) -> tuple[dict[str, str], list[dict[str, str]]]:
    """Check for file conflicts.

    Returns:
        Tuple of (non_conflicting_files, conflicts)
        conflicts is list of {path, diff, existing, proposed}
    """
    non_conflicting: dict[str, str] = {}
    conflicts: list[dict[str, str]] = []

    for rel_path, content in proposed_files.items():
        full_path = project_root / rel_path
        if full_path.exists():
            existing = full_path.read_text(encoding="utf-8")
            if existing.strip() != content.strip():
                conflicts.append(
                    {
                        "path": str(rel_path),
                        "diff": _generate_diff(full_path, existing, content),
                        "existing": existing,
                        "proposed": content,
                    }
                )
        else:
            non_conflicting[rel_path] = content

    return non_conflicting, conflicts


def _validate_init_params(
    project_path: str | None,
    values: str | dict[str, Any] | None,
) -> tuple[Path, dict[str, Any] | None] | tuple[None, dict[str, Any]]:
    """Validate init_project parameters.

    Returns:
        Tuple of (project_root, parsed_values) if valid, or (None, error_dict) if invalid.
    """
    import json

    # Handle stringified values parameter (Claude Code passes dicts as JSON strings)
    parsed_values: dict[str, Any] | None = None
    if values is not None:
        if isinstance(values, str):
            try:
                parsed_values = json.loads(values)
            except json.JSONDecodeError as e:
                return None, {
                    "status": "error",
                    "error_type": "ParameterParseError",
                    "message": f"Failed to parse 'values' as JSON: {e}",
                    "received": values[:100] if len(values) > 100 else values,
                    "next_steps": [
                        "Ensure 'values' is a valid JSON object.",
                        'Example: {"language": "go", "project_name": "my-app"}',
                    ],
                }
        else:
            parsed_values = values

    # Determine project root
    project_root = Path(project_path) if project_path else Path.cwd()
    if not project_root.exists():
        return None, {
            "status": "error",
            "error": f"Project path does not exist: {project_root}",
            "next_steps": ["Create the directory first or specify an existing path."],
        }

    return project_root, parsed_values


def _check_init_prerequisites() -> dict[str, Any] | None:
    """Check prerequisites for init_project.

    Returns:
        Error dict if prerequisites missing, None if all OK.
    """
    prereqs = check_prereqs()
    missing_core = prereqs.get("missing_core", [])
    if missing_core:
        _progress("Checking prerequisites", "FAIL")
        return {
            "status": "error",
            "error": f"Missing required tools: {', '.join(missing_core)}",
            "prerequisites": prereqs,
            "next_steps": [
                "Install missing tools using the shell_script below.",
                prereqs.get("shell_script", ""),
            ],
        }
    return None


def _write_non_conflicting_files(
    project_root: Path,
    non_conflicting: dict[str, str],
) -> list[str]:
    """Write non-conflicting files to disk.

    Returns list of relative paths written.
    """
    files_written: list[str] = []
    for rel_path, content in non_conflicting.items():
        full_path = project_root / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        files_written.append(rel_path)
    return files_written


def _handle_gitignore_append(project_root: Path) -> str | None:
    """Append vibraphone entries to .gitignore.

    Returns:
        File description if written/appended, None if skipped.
    """
    try:
        gitignore_append = load_template("gitignore_append.txt")
    except FileNotFoundError:
        return None

    gitignore_path = project_root / ".gitignore"
    if gitignore_path.exists():
        existing = gitignore_path.read_text(encoding="utf-8")
        if ".vibraphone/" not in existing:
            gitignore_path.write_text(
                existing.rstrip() + "\n\n# Vibraphone\n" + gitignore_append,
                encoding="utf-8",
            )
            return ".gitignore (appended)"
    else:
        gitignore_path.write_text(
            "# Vibraphone\n" + gitignore_append,
            encoding="utf-8",
        )
        return ".gitignore"
    return None


def _handle_justfile_creation(project_root: Path, project_name: str) -> str | None:
    """Create minimal Justfile if it doesn't exist.

    Returns:
        "Justfile" if created, None if already exists.
    """
    justfile_path = project_root / "Justfile"
    if justfile_path.exists():
        return None

    justfile_content = f"""# {project_name} - Justfile

# Bootstrap project dependencies
bootstrap:
    @echo "Project bootstrapped!"

# Run tests
test:
    @echo "Configure with configure_stack tool"

# Run linter
lint:
    @echo "Configure with configure_stack tool"

# Run formatter
format:
    @echo "Configure with configure_stack tool"
"""
    justfile_path.write_text(justfile_content, encoding="utf-8")
    return "Justfile"


@mcp.tool
async def check_prerequisites() -> dict[str, Any]:
    """Check for required external dependencies and get install commands.

    Detects br, bv, git, just, node/npx and reports platform-specific
    install commands for any missing tools.

    Returns:
        Dict with:
        - platform: OS name (Darwin, Linux, Windows)
        - prerequisites: list of {tool, installed, install_command}
        - all_installed: bool indicating if all tools present
        - shell_script: ready-to-run bash script for missing tools
        - missing_core: list of missing core dependencies (br, bv, git)
    """
    return check_prereqs()


@mcp.tool
async def init_project(
    project_path: str | None = None,
    values: str | dict[str, Any] | None = None,
    *,
    preview: bool = True,
) -> dict[str, Any]:
    """Scaffold vibraphone into a project.

    Two-phase flow:
    - preview=True: returns detected values, proposed files, any conflicts
    - preview=False: writes non-conflicting files, returns conflicts for resolution

    Conflict handling (per CONTEXT.md):
    - Non-conflicting files written immediately
    - Conflicting files returned with diff for user decision
    - Each file decision is independent (no rollback needed)

    Args:
        project_path: Path to project directory. Defaults to current working directory.
        preview: If True, return preview without writing. If False, write files.
        values: Override detected values. Keys: project_name, language, worktrees_path, etc.

    Returns:
        Dict with status, detected/final values, files info, conflicts, next_steps.
    """
    # Validate parameters (also parses JSON strings)
    validation_result = _validate_init_params(project_path, values)
    if validation_result[0] is None:
        return validation_result[1]  # Return error dict
    project_root, parsed_values = validation_result

    # Auto-detect values
    _progress("Detecting project metadata")
    detected = detect_project_metadata(project_root)
    final_values = {**detected, **(parsed_values or {})}

    # Check prerequisites
    _progress("Checking prerequisites")
    prereq_error = _check_init_prerequisites()
    if prereq_error:
        return prereq_error
    _progress("Checking prerequisites", "OK")

    # Render all templates
    _progress("Rendering templates")
    proposed_files = _render_all_templates(final_values)

    # Check for conflicts
    _progress("Checking for conflicts")
    non_conflicting, conflicts = _check_conflicts(project_root, proposed_files)

    if preview:
        return {
            "status": "preview",
            "detected_values": detected,
            "final_values": final_values,
            "files_to_create": list(proposed_files.keys()),
            "conflicts": [{"path": c["path"], "diff": c["diff"]} for c in conflicts],
            "prerequisites": check_prereqs(),
            "next_steps": [
                "1. Review detected values and edit if needed",
                "2. Review conflicts and decide: overwrite (yes) or skip (no) per file",
                "3. Call init_project(..., preview=False, values=final_values) to proceed",
            ],
        }

    # Write non-conflicting files
    files_written = _write_non_conflicting_files(project_root, non_conflicting)

    # Handle .gitignore append (NEW-06)
    gitignore_result = _handle_gitignore_append(project_root)
    if gitignore_result:
        files_written.append(gitignore_result)

    # Handle Justfile creation (NEW-05)
    justfile_result = _handle_justfile_creation(project_root, final_values["project_name"])
    if justfile_result:
        files_written.append(justfile_result)

    # Show celebration if complete
    if not conflicts:
        print(_celebration_message(final_values["project_name"]), file=sys.stderr)
        return {
            "status": "complete",
            "files_written": files_written,
            "final_values": final_values,
            "next_steps": [
                "1. Run 'just bootstrap' to initialize project",
                "2. Use configure_stack to set up test/lint commands",
                "3. Use import_gsd_plan to import GSD phase tasks",
            ],
        }

    return {
        "status": "partial",
        "files_written": files_written,
        "conflicts": [{"path": c["path"], "diff": c["diff"]} for c in conflicts],
        "final_values": final_values,
        "next_steps": [
            "1. For each conflict, decide: overwrite (yes) or skip (no)",
            "2. Call resolve_conflict(path, overwrite=True/False) for each",
        ],
    }
