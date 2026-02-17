"""Scaffolding tools for initializing vibraphone in projects."""

from __future__ import annotations

from typing import Any

from vibraphone.server import mcp
from vibraphone.utils.prerequisites import check_prerequisites as check_prereqs


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
