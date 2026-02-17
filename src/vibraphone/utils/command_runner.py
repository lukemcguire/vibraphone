"""Async command runner for quality gate commands.

Provides async subprocess execution for test/lint/format/check commands
with config-based command discovery.
"""

import asyncio
import shlex
from pathlib import Path

# Default commands (justfile recipes)
DEFAULT_COMMANDS = {
    "test": "just test",
    "lint": "just lint",
    "format": "just format",
    "check": "just check",
}


def get_command(command_type: str, component: str | None = None) -> str:
    """Get command for quality gate type, checking config overrides.

    Priority:
    1. vibraphone.yaml quality_gate.commands.{type} override
    2. DEFAULT_COMMANDS justfile recipe

    For justfile commands, appends component suffix if provided.
    Example: command_type="test", component="server" -> "just test-server"

    Args:
        command_type: Type of command (test, lint, format, check).
        component: Optional component suffix for justfile commands.

    Returns:
        Command string to execute.

    Raises:
        ValueError: If command_type is not recognized.
    """
    if command_type not in DEFAULT_COMMANDS:
        raise ValueError(
            f"Unknown command type: {command_type}. "
            f"Valid types: {list(DEFAULT_COMMANDS.keys())}"
        )

    # Import here to avoid circular dependency
    from vibraphone.config import get_config

    config = get_config()

    # Check for config override
    config_command = None
    if hasattr(config, "quality_gate") and config.quality_gate is not None:
        # Check if there's a commands dict on quality_gate
        commands_dict = getattr(config.quality_gate, "commands", None)
        if commands_dict and command_type in commands_dict:
            config_command = commands_dict[command_type]

    # Use config override or fall back to default
    command = config_command if config_command else DEFAULT_COMMANDS[command_type]

    # Handle component suffix for justfile commands
    if component and command.startswith("just "):
        command = f"{command}-{component}"

    return command


async def run_command(
    command: str,
    cwd: Path | None = None,
) -> tuple[int, str, str]:
    """Run command asynchronously and return raw output.

    Uses asyncio.create_subprocess_exec (NOT subprocess.run - blocking).
    Captures stdout and stderr.
    Returns tuple of (returncode, stdout, stderr) for tools to process.

    Args:
        command: Command string to execute (will be parsed with shlex).
        cwd: Working directory for the command. If None, uses current directory.

    Returns:
        Tuple of (returncode, stdout, stderr).
    """
    if cwd is None:
        cwd = Path.cwd()

    # Parse command string into executable and args
    parts = shlex.split(command)
    if not parts:
        return (1, "", "Empty command")

    executable = parts[0]
    args = parts[1:]

    process = await asyncio.create_subprocess_exec(
        executable,
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )

    stdout_bytes, stderr_bytes = await process.communicate()
    stdout = stdout_bytes.decode("utf-8", errors="replace")
    stderr = stderr_bytes.decode("utf-8", errors="replace")

    return (process.returncode or 0, stdout, stderr)
