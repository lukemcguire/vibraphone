"""Prerequisite detection for vibraphone external dependencies."""

from __future__ import annotations

import platform
import shutil
from dataclasses import dataclass
from typing import Any


@dataclass
class Prerequisite:
    """Information about a required tool."""
    tool: str
    installed: bool
    install_command: str


# Per-platform install commands
# Key: tool name, Value: dict of platform -> install command
INSTALL_COMMANDS: dict[str, dict[str, str]] = {
    "br": {
        "Darwin": "brew install beads-rust  # or: cargo install beads_rust",
        "Linux": "cargo install beads_rust  # or build from source",
        "Windows": "cargo install beads_rust  # requires Rust toolchain",
    },
    "bv": {
        "Darwin": "brew install beads-viewer  # or: cargo install beads_viewer",
        "Linux": "cargo install beads_viewer",
        "Windows": "cargo install beads_viewer",
    },
    "git": {
        "Darwin": "brew install git",
        "Linux": "sudo apt install git  # or: brew install git",
        "Windows": "scoop install git",
    },
    "just": {
        "Darwin": "brew install just",
        "Linux": "sudo apt install just  # or: brew install just",
        "Windows": "scoop install just",
    },
    "node": {
        "Darwin": "brew install node",
        "Linux": "sudo apt install nodejs npm  # or: brew install node",
        "Windows": "scoop install nodejs",
    },
}

# Core dependencies that vibraphone cannot function without
CORE_DEPENDENCIES = ("br", "bv", "git")


def check_prerequisites() -> dict[str, Any]:
    """Check for required external dependencies.

    Returns both structured list and ready-to-run shell script.
    Core dependencies: br, bv, git (essential for vibraphone to function).

    Returns:
        Dict with:
        - platform: OS name (Darwin, Linux, Windows)
        - prerequisites: list of Prerequisite dicts
        - all_installed: bool
        - shell_script: str with install commands for missing tools
        - missing_core: list of missing core dependency names
    """
    system = platform.system()  # Darwin, Linux, Windows

    results: list[Prerequisite] = []
    install_commands: list[str] = []

    for tool in ["br", "bv", "git", "just", "node"]:
        path = shutil.which(tool)
        installed = path is not None

        install_cmd = INSTALL_COMMANDS.get(tool, {}).get(system, f"# Install {tool} for your platform")
        results.append(Prerequisite(
            tool=tool,
            installed=installed,
            install_command=install_cmd if not installed else "",
        ))

        if not installed:
            install_commands.append(install_cmd)

    # Build shell script for missing tools
    if install_commands:
        shell_script = "#!/bin/bash\n# Install missing prerequisites for vibraphone\n\n" + "\n".join(install_commands)
    else:
        shell_script = "#!/bin/bash\n# All prerequisites installed!"

    return {
        "platform": system,
        "prerequisites": [{"tool": r.tool, "installed": r.installed, "install_command": r.install_command} for r in results],
        "all_installed": all(r.installed for r in results),
        "shell_script": shell_script,
        "missing_core": [r.tool for r in results if r.tool in CORE_DEPENDENCIES and not r.installed],
    }
