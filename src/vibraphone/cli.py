"""Vibraphone CLI - command-line interface for vibraphone utilities.

This module provides CLI commands for vibraphone, including:
- setup-commands: Install the /v slash command file
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

COMMAND_NAME = "v"
COMMAND_DEST_PATH = Path.home() / ".claude" / "commands" / f"{COMMAND_NAME}.md"


def get_bundled_command_path() -> Path | None:
    """Get the path to the bundled v.md command file.

    Returns:
        Path to the bundled command file, or None if not found.
    """
    # Try importlib.resources first (works for installed packages)
    try:
        from importlib.resources import files

        command_file = files("vibraphone.commands").joinpath(f"{COMMAND_NAME}.md")
        if command_file.is_file():
            return Path(str(command_file))
    except (ImportError, TypeError):
        pass

    # Fallback: check relative to this file (development mode)
    dev_path = Path(__file__).parent / "commands" / f"{COMMAND_NAME}.md"
    if dev_path.is_file():
        return dev_path

    return None


def cmd_setup_commands() -> int:
    """Install /v slash commands to ~/.claude/commands/.

    Returns:
        0 on success, 1 on error.
    """
    bundled_path = get_bundled_command_path()
    if bundled_path is None:
        print("Error: Bundled command file not found.", file=sys.stderr)
        print("This indicates a corrupt installation.", file=sys.stderr)
        return 1

    # Auto-create destination directory (per CONTEXT.md decision)
    COMMAND_DEST_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Copy file (silent overwrite per CONTEXT.md decision)
    try:
        shutil.copy2(bundled_path, COMMAND_DEST_PATH)
    except PermissionError:
        print(f"Error: Permission denied writing to {COMMAND_DEST_PATH}", file=sys.stderr)
        print("Check file permissions and try again.", file=sys.stderr)
        return 1

    print(f"Installed to {COMMAND_DEST_PATH}")
    print("Restart Claude Code for commands to take effect.")
    return 0


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for vibraphone CLI.

    Returns:
        Configured ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        prog="vibraphone-cli",
        description="Vibraphone CLI utilities",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # setup-commands subcommand
    setup_parser = subparsers.add_parser(
        "setup-commands",
        help="Install /v slash commands to ~/.claude/commands/",
    )
    setup_parser.set_defaults(func=lambda _args: cmd_setup_commands())

    return parser


def main() -> int:
    """Main entry point for vibraphone CLI.

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    if hasattr(args, "func"):
        return args.func(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
