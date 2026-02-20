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
    get_project_root,
)
from vibraphone.mcp_instance import mcp

# Section markers for Justfile
_COMPONENT_RECIPES_START = "# === COMPONENT RECIPES ==="
_COMPONENT_RECIPES_END = "# === END COMPONENT RECIPES ==="

# Stitch MCP entry template
STITCH_MCP_ENTRY = {
    "command": "npx",
    "args": ["-y", "stitch-mcp"],
    "env": {"GOOGLE_CLOUD_PROJECT": "${STITCH_PROJECT_ID}"},
    "_comment": "Optional. Remove this entry if stitch.enabled is false in vibraphone.yaml.",
}


def _build_stringification_error(
    param_name: str,
    received: str,
    example_wrong: str,
    example_right: str,
) -> dict[str, Any]:
    """Build educational error for stringified parameter.

    When Claude passes a dict parameter as a JSON string (due to MCP serialization),
    this helper returns a helpful error message with WRONG/RIGHT examples.
    """
    display_value = received if len(received) <= 100 else received[:97] + "..."

    return {
        "status": "error",
        "error_type": "ParameterStringified",
        "message": f"""Parameter `{param_name}` received as a JSON string
instead of a native object.

| WRONG                          | RIGHT                        |
| ------------------------------ | ---------------------------- |
| `{example_wrong}` | `{example_right}` |

Remove the quotes around the object.""",
        "received": display_value,
        "next_steps": [
            f"Pass `{param_name}` as a native object, not a JSON string.",
            "MCP protocol handles JSON serialization automatically.",
        ],
    }


def _render_component_recipes(name: str, root: str, commands: dict[str, str]) -> str:
    """Render per-component Justfile recipes for a single component.

    Per-component recipes are marked [private] so they don't clutter `just --list`.
    """
    lines = [
        f"# Run {name} tests",
        "[private]",
        f"test-{name} *ARGS:",
        f"    cd {root} && {commands['test_command']} {{ARGS}}",
        "",
        f"# Run {name} linter",
        "[private]",
        f"lint-{name}:",
        f"    cd {root} && {commands['lint_command']}",
        "",
        f"# Run {name} formatter",
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
            "# Aggregate test recipe",
            f"test *ARGS: {test_deps}",
            '    @echo "All tests passed."',
            "",
            "# Aggregate lint recipe",
            f"lint: {lint_deps}",
            '    @echo "All linting passed."',
            "",
            "# Aggregate format recipe",
            f"format: {format_deps}",
            '    @echo "All formatting done."',
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
    """Update or insert the component recipes section in Justfile.

    Returns True if file was modified.
    """
    if not justfile_path.exists():
        # Create new Justfile with component section
        justfile_path.write_text(component_section + "\n")
        return True

    content = justfile_path.read_text()

    if _COMPONENT_RECIPES_START in content:
        # Replace existing section
        start_idx = content.find(_COMPONENT_RECIPES_START)
        end_idx = content.find(_COMPONENT_RECIPES_END) + len(_COMPONENT_RECIPES_END)
        new_content = content[:start_idx] + component_section + content[end_idx:]
    else:
        # Append section
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
    components: dict[str, dict[str, Any]],
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
    # Defensive check for stringified components parameter
    if isinstance(components, str):
        return _build_stringification_error(
            param_name="components",
            received=components,
            example_wrong='components: "{\\"backend\\": {\\"language\\": \\"python\\"}}"',
            example_right='components: {"backend": {"language": "python"}}',
        )

    # Get project root
    project_root = get_project_root()

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
    component_section = _render_component_section(components)
    yaml_content = _render_vibraphone_yaml(components, existing_config)

    if preview:
        result: dict[str, Any] = {
            "status": "preview",
            "component_section": component_section,
            "vibraphone_yaml": yaml_content,
            "components": list(components.keys()),
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
        "components": list(components.keys()),
        "stitch_config": mcp_sync_result,
        "next_steps": [
            "1. import_gsd_plan(phase_number) to import phase tasks",
        ],
    }
