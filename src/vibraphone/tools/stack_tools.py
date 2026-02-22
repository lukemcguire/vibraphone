"""Stack configuration tool - generates per-component Justfile recipes and vibraphone.yaml config."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

import yaml

from vibraphone.config import (
    STACK_DEFAULTS,
    clear_config_cache,
    find_config_file,
    get_config,
    get_project_root,
)
from vibraphone.mcp_instance import mcp

# Section markers for Justfile
_COMPONENT_RECIPES_START = "# === COMPONENT RECIPES ==="
_COMPONENT_RECIPES_END = "# === END COMPONENT RECIPES ==="

# Justfile header with shell settings
_JUSTFILE_HEADER = """set shell := ["bash", "-c"]
set dotenv-load := true
"""

# Worktree group - uses nested paths: ~/.vibraphone/worktrees/{project}/{task}
_STANDARD_WORKTREE_RECIPES = """
# Create worktree for a task
[group: 'worktree']
start-task id:
    @echo "Creating worktree for {{id}}..."
    mkdir -p ${VIBRAPHONE_WORKTREES_PATH}/${VIBRAPHONE_PROJECT_NAME}
    git worktree add -b feat/{{id}} ${VIBRAPHONE_WORKTREES_PATH}/${VIBRAPHONE_PROJECT_NAME}/{{id}} main
    @echo "Worktree ready at ${VIBRAPHONE_WORKTREES_PATH}/${VIBRAPHONE_PROJECT_NAME}/{{id}}"

# Merge task branch into main
[group: 'worktree']
merge-task id:
    @echo "Merging task {{id}}..."
    git rebase main feat/{{id}}
    git merge --no-ff feat/{{id}} -m "Merge feat/{{id}} into main"
    @echo "Merged feat/{{id}} into main"

# Remove worktree and branch for a task
[group: 'worktree']
cleanup-task id:
    @echo "Cleaning up task {{id}}..."
    git worktree remove ${VIBRAPHONE_WORKTREES_PATH}/${VIBRAPHONE_PROJECT_NAME}/{{id}} --force
    git branch -D feat/{{id}} 2>/dev/null || true
    @echo "Cleaned up feat/{{id}}"

# List active worktrees
[group: 'worktree']
list-worktrees:
    git worktree list
"""

_STANDARD_BEADS_RECIPES = """
# Initialize beads database
[group: 'beads']
beads-init:
    br init
    @echo "Beads initialized."

# Show all tasks as JSON
[group: 'beads']
beads-status:
    br list --json

# Show unblocked tasks as JSON
[group: 'beads']
beads-ready:
    br ready --json

# Flush beads sync queue
[group: 'beads']
beads-sync:
    br sync --flush-only

# Add a task interactively
[group: 'beads']
add-task:
    uv run python scripts/add_task.py
"""

_STANDARD_SETUP_RECIPES = """
# Reset project to blank slate (testing/development only)
[group: 'setup']
reset:
    @echo "Resetting project to blank slate..."
    git worktree list --porcelain | grep '^worktree' | grep -v "$(pwd)" | cut -d' ' -f2 | xargs -r -I{} git worktree remove --force {}
    rm -rf .vibraphone/ .beads/ .planning/
    rm -rf .venv __pycache__ .coverage htmlcov .ruff_cache node_modules
    git checkout -- .
    @echo "Done. Re-run init_project to reinitialize."
"""

# Stitch MCP entry template
STITCH_MCP_ENTRY = {
    "command": "npx",
    "args": ["-y", "stitch-mcp"],
    "env": {"GOOGLE_CLOUD_PROJECT": "${STITCH_PROJECT_ID}"},
    "_comment": "Optional. Remove this entry if stitch.enabled is false in vibraphone.yaml.",
}


def _render_component_recipes(name: str, root: str, commands: dict[str, str]) -> str:
    """Render per-component Justfile recipes for a single component.

    Per-component recipes are marked [private] so they don't clutter `just --list`.
    """
    lines = [
        f"# Run {name} tests",
        "[group: 'quality-gate']",
        "[private]",
        f"test-{name} *ARGS:",
        f"    cd {root} && {commands['test_command']} {{ARGS}}",
        "",
        f"# Run {name} linter",
        "[group: 'quality-gate']",
        "[private]",
        f"lint-{name}:",
        f"    cd {root} && {commands['lint_command']}",
        "",
        f"# Run {name} formatter",
        "[group: 'quality-gate']",
        "[private]",
        f"format-{name}:",
        f"    cd {root} && {commands['format_command']}",
    ]
    return "\n".join(lines)


def _render_component_section(components: dict[str, dict[str, Any]]) -> str:
    """Render the full component recipes section with markers."""
    sections = [_COMPONENT_RECIPES_START]

    # Aggregate recipes
    names = list(components.keys())
    test_deps = " ".join(f"test-{n}" for n in names)
    lint_deps = " ".join(f"lint-{n}" for n in names)
    format_deps = " ".join(f"format-{n}" for n in names)

    sections.extend(
        [
            "",
            "# Run lint + test",
            "[group: 'quality-gate']",
            "check: lint test",
            '    @echo "Quality gate passed."',
            "",
            "# Run all tests",
            "[group: 'quality-gate']",
            f"test *ARGS: {test_deps}",
            '    @echo "All tests passed."',
            "",
            "# Run all linters",
            "[group: 'quality-gate']",
            f"lint: {lint_deps}",
            '    @echo "All linting passed."',
            "",
            "# Run all formatters",
            "[group: 'quality-gate']",
            f"format: {format_deps}",
            '    @echo "All formatting done."',
            "",
            "# Run standalone code review on files",
            "[group: 'quality-gate']",
            "review *FILES:",
            "    uv run python scripts/review.py {FILES}",
            "",
        ]
    )

    # Per-component recipes
    for name, comp in components.items():
        root = comp.get("root", f"./{name}")
        language = comp.get("language", "python")
        defaults = STACK_DEFAULTS.get(language, {})
        commands = {
            "test_command": comp.get("test_command") or defaults.get("test_command", "echo 'no test command'"),
            "lint_command": comp.get("lint_command") or defaults.get("lint_command", "echo 'no lint command'"),
            "format_command": comp.get("format_command") or defaults.get("format_command", "echo 'no format command'"),
        }
        sections.append(_render_component_recipes(name, root, commands))
        sections.append("")

    sections.append(_COMPONENT_RECIPES_END)
    return "\n".join(sections)


def _update_justfile_section(justfile_path: Path, component_section: str) -> bool:
    """Generate complete Justfile with standard recipes + component recipes.

    When justfile exists with init_project stubs, replaces entirely.
    When justfile exists with component section markers, updates just that section.

    Returns True if file was modified.
    """
    # Build the full justfile content
    full_content = f"""{_JUSTFILE_HEADER}
{_STANDARD_WORKTREE_RECIPES}
{_STANDARD_BEADS_RECIPES}
{_STANDARD_SETUP_RECIPES}
{component_section}
"""

    if not justfile_path.exists():
        justfile_path.write_text(full_content)
        return True

    content = justfile_path.read_text()

    # Check if this is a stub justfile from init_project (has placeholder echo)
    is_stub = "Configure with configure_stack tool" in content

    if is_stub:
        # Replace entire file - it's just stubs from init_project
        justfile_path.write_text(full_content)
        return True

    # Existing justfile with real content - only update component section
    if _COMPONENT_RECIPES_START in content:
        start_idx = content.find(_COMPONENT_RECIPES_START)
        end_idx = content.find(_COMPONENT_RECIPES_END) + len(_COMPONENT_RECIPES_END)
        new_content = content[:start_idx] + component_section + content[end_idx:]
    else:
        new_content = content.rstrip() + "\n\n" + component_section + "\n"

    if new_content != content:
        justfile_path.write_text(new_content)
        return True
    return False


def _render_vibraphone_yaml(components: dict[str, dict[str, Any]], existing_config: dict) -> str:
    """Render vibraphone.yaml with updated components section, preserving other sections."""
    new_components = {}
    for name, comp in components.items():
        language = comp.get("language", "python")
        defaults = STACK_DEFAULTS.get(language, {})
        new_components[name] = {
            "language": language,
            "root": comp.get("root", f"./{name}"),
            "test_command": comp.get("test_command") or defaults.get("test_command", ""),
            "lint_command": comp.get("lint_command") or defaults.get("lint_command", ""),
            "format_command": comp.get("format_command") or defaults.get("format_command", ""),
            "coverage_threshold": comp.get("coverage_threshold", 80),
        }

    existing_config["components"] = new_components
    return yaml.dump(existing_config, default_flow_style=False, sort_keys=False)


def _update_env_var(key: str, value: str, project_root: Path) -> bool:
    """Update or append a key=value pair in .env.

    Returns True if file was modified.
    """
    env_path = project_root / ".env"
    env_line = f"{key}={value}"

    if not env_path.exists():
        env_path.write_text(env_line + "\n")
        return True

    content = env_path.read_text()
    lines = content.splitlines()
    found = False
    modified = False

    for i, line in enumerate(lines):
        if line.startswith(f"{key}=") or line == key:
            if lines[i] != env_line:
                lines[i] = env_line
                modified = True
            found = True
            break

    if not found:
        lines.append(env_line)
        modified = True

    if modified:
        env_path.write_text("\n".join(lines) + "\n")
    return modified


def _sync_mcp_config(*, stitch_enabled: bool, project_root: Path) -> dict:
    """Add or remove the stitch entry in .mcp/config.json based on stitch_enabled.

    Returns dict with sync status.
    """
    mcp_config_path = project_root / ".mcp" / "config.json"
    mcp_config_path.parent.mkdir(parents=True, exist_ok=True)

    config = {"mcpServers": {}}

    if mcp_config_path.exists():
        import json

        with mcp_config_path.open() as f:
            config = json.load(f)

    if "mcpServers" not in config:
        config["mcpServers"] = {}

    servers = config["mcpServers"]

    if stitch_enabled:
        servers["stitch"] = STITCH_MCP_ENTRY
    elif "stitch" in servers:
        del servers["stitch"]

    import json

    with mcp_config_path.open("w") as f:
        json.dump(config, f, indent=2)

    return {
        "mcp_config_path": str(mcp_config_path),
        "stitch_enabled": stitch_enabled,
    }


@mcp.tool
async def configure_stack(
    components: str | dict[str, dict[str, Any]],
    stitch_project_id: str | None = None,
    *,
    preview: bool = True,
) -> dict[str, Any]:
    """Generate per-component Justfile recipes and vibraphone.yaml config.

    Two-phase flow:
    - preview=True: returns proposed file contents for agent to present to user.
    - preview=False: writes files, reloads config, returns confirmation.

    Args:
        components: mapping of component name to config (language, root, test_command, etc.)
        preview: if True, return proposals without writing; if False, write and reload.
        stitch_project_id: if provided, enable stitch and write project ID to .env + vibraphone.yaml.

    Returns:
        dict with status, justfile content (preview) or path (written), vibraphone_yaml content (preview) or path (written).
    """
    import json

    # Handle stringified components parameter (Claude Code passes dicts as JSON strings)
    parsed_components: dict[str, dict[str, Any]]
    if isinstance(components, str):
        try:
            parsed_components = json.loads(components)
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "error_type": "ParameterParseError",
                "message": f"Failed to parse 'components' as JSON: {e}",
                "received": components[:100] if len(components) > 100 else components,
                "next_steps": [
                    "Ensure 'components' is a valid JSON object.",
                    'Example: {"backend": {"language": "python"}}',
                ],
            }
    else:
        parsed_components = components

    # Get project root
    project_root = get_project_root()

    # Get worktrees path and project name from config
    config = get_config()
    worktrees_path = config.worktrees_path
    project_name = config.project.name

    # Read existing vibraphone.yaml
    config_path = find_config_file()
    existing_config: dict[str, Any] = {}
    if config_path and config_path.exists():
        with config_path.open() as f:
            existing_config = yaml.safe_load(f) or {}

    # Handle stitch if provided
    if stitch_project_id:
        stitch_section = existing_config.setdefault("stitch", {})
        stitch_section["enabled"] = True
        stitch_section["project_id"] = "${STITCH_PROJECT_ID}"

    # Render content
    component_section = _render_component_section(parsed_components)
    yaml_content = _render_vibraphone_yaml(parsed_components, existing_config)

    if preview:
        result: dict[str, Any] = {
            "status": "preview",
            "component_section": component_section,
            "vibraphone_yaml": yaml_content,
            "components": list(parsed_components.keys()),
            "next_steps": [
                "1. Review the proposed Justfile section and vibraphone.yaml",
                "2. Call configure_stack(..., preview=False) to apply",
            ],
        }
        if stitch_project_id:
            result["stitch_note"] = f"Will enable stitch with project ID {stitch_project_id}"
        return result

    # Write files
    justfile_path = project_root / "Justfile"
    justfile_changed = _update_justfile_section(justfile_path, component_section)

    yaml_path = config_path if config_path else project_root / "vibraphone.yaml"
    yaml_path.write_text(yaml_content)

    # Write worktrees path and project name to .env for justfile recipes
    _update_env_var("VIBRAPHONE_WORKTREES_PATH", str(worktrees_path), project_root)
    _update_env_var("VIBRAPHONE_PROJECT_NAME", project_name, project_root)

    # Handle stitch if provided
    mcp_sync_result = None
    if stitch_project_id:
        _update_env_var("STITCH_PROJECT_ID", stitch_project_id, project_root)
        stitch_enabled = existing_config.get("stitch", {}).get("enabled", False)
        mcp_sync_result = _sync_mcp_config(stitch_enabled=stitch_enabled, project_root=project_root)

    # Reload config singleton
    clear_config_cache()

    return {
        "status": "configured",
        "justfile_path": str(justfile_path),
        "justfile_changed": justfile_changed,
        "vibraphone_yaml_path": str(yaml_path),
        "components": list(parsed_components.keys()),
        "stitch_config": mcp_sync_result,
        "next_steps": [
            "1. import_gsd_plan(phase_number) to import phase tasks",
        ],
    }
