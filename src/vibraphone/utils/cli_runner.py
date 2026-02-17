"""Async CLI runner for br/bv commands.

Provides async subprocess execution for task management CLIs with JSON output parsing.
"""

import asyncio
import json
from pathlib import Path


class CliError(Exception):
    """Exception raised when a CLI command fails.

    Attributes:
        message: Human-readable error message
        command: The command that was executed
        returncode: Exit code from the command (or -1 if not available)
        stderr: Standard error output from the command
    """

    def __init__(
        self,
        message: str,
        command: str,
        returncode: int = -1,
        stderr: str = "",
    ) -> None:
        """Initialize CliError with context about the failed command."""
        self.message = message
        self.command = command
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(message)


async def run_cli(command: str, *args: str, cwd: Path | None = None) -> dict:
    """Run br/bv CLI command and parse JSON output.

    Uses asyncio.create_subprocess_exec (NOT subprocess.run - blocking).
    Captures stdout and stderr.
    Returns parsed JSON dict from stdout.
    Raises CliError on non-zero exit or JSON parse failure.

    Args:
        command: The CLI command to run (e.g., 'br' or 'bv')
        *args: Arguments to pass to the command
        cwd: Working directory for the command. If None, uses project root
            from config or current working directory.

    Returns:
        Parsed JSON dict from command stdout.

    Raises:
        CliError: If command exits with non-zero code or JSON parsing fails.
    """
    if cwd is None:
        cwd = Path.cwd()

    full_command = [command, *args]

    process = await asyncio.create_subprocess_exec(
        *full_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )

    stdout_bytes, stderr_bytes = await process.communicate()
    stdout = stdout_bytes.decode("utf-8", errors="replace")
    stderr = stderr_bytes.decode("utf-8", errors="replace")

    command_str = " ".join(full_command)

    if process.returncode != 0:
        raise CliError(
            message=f"Command failed with exit code {process.returncode}: {command_str}",
            command=command_str,
            returncode=process.returncode or -1,
            stderr=stderr,
        )

    try:
        return json.loads(stdout)
    except json.JSONDecodeError as e:
        raise CliError(
            message=f"Failed to parse JSON output from command: {command_str}",
            command=command_str,
            returncode=process.returncode or 0,
            stderr=f"JSON parse error: {e}\nOutput: {stdout[:500]}",
        ) from e
