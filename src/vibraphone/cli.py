"""Vibraphone CLI - command-line interface for vibraphone utilities.

This module provides CLI commands for vibraphone, including:
- skill install: Install the vibraphone slash-command skill
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

SKILL_NAME = "v"
SKILL_DEST_PATH = Path.home() / ".claude" / "skills" / SKILL_NAME

COMMAND_NAME = "v"
COMMAND_DEST_PATH = Path.home() / ".claude" / "commands" / f"{COMMAND_NAME}.md"


def get_bundled_skill_path() -> Path | None:
    """Get the path to the bundled skill directory.

    Returns:
        Path to the bundled skill directory, or None if not found.
    """
    # Try importlib.resources first (works for installed packages)
    try:
        from importlib.resources import files

        skill_dir = files("vibraphone.skills").joinpath(SKILL_NAME)
        if skill_dir.is_dir():
            # Return the path as a Path object
            return Path(str(skill_dir))
    except (ImportError, TypeError):
        pass

    # Fallback: check relative to this file (development mode)
    dev_path = Path(__file__).parent / "skills" / SKILL_NAME
    if dev_path.is_dir():
        return dev_path

    return None


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


def cmd_skill_install() -> int:
    """Install the vibraphone skill to ~/.claude/skills/.

    Returns:
        0 on success, 1 on error.
    """
    # Get bundled skill directory
    bundled_path = get_bundled_skill_path()
    if bundled_path is None:
        print("Error: Bundled skill directory not found in package.", file=sys.stderr)
        return 1

    # Remove existing installation if present
    if SKILL_DEST_PATH.exists():
        try:
            shutil.rmtree(SKILL_DEST_PATH)
        except OSError as e:
            print(f"Error removing existing skill: {e}", file=sys.stderr)
            return 1

    # Ensure parent directory exists
    SKILL_DEST_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Copy the skill directory
    try:
        shutil.copytree(bundled_path, SKILL_DEST_PATH)
    except OSError as e:
        print(f"Error copying skill directory: {e}", file=sys.stderr)
        return 1

    print(f"Skill installed to {SKILL_DEST_PATH}/")
    print("\nYou can now use /v commands in Claude Code:")
    print("  /v init --language python")
    print("  /v list --status ready")
    print("  /v next")
    print("\nRestart Claude Code if it's already running.")

    return 0


def cmd_skill_status() -> int:
    """Check if the skill is installed.

    Returns:
        0 if installed, 1 if not installed.
    """
    skill_md = SKILL_DEST_PATH / "SKILL.md"
    if SKILL_DEST_PATH.is_dir() and skill_md.exists():
        print(f"Skill is installed at {SKILL_DEST_PATH}/")
        return 0
    print("Skill is not installed.")
    print("Run 'vibraphone-cli skill install' to install it.")
    return 1


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


def cmd_skill(args: argparse.Namespace) -> int:
    """Handle skill subcommands.

    Args:
        args: Parsed arguments with subcommand in args.skill_command.

    Returns:
        Exit code.
    """
    if args.skill_command == "install":
        return cmd_skill_install()
    if args.skill_command == "status":
        return cmd_skill_status()
    print(f"Unknown skill command: {args.skill_command}", file=sys.stderr)
    return 1


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

    # skill subcommand
    skill_parser = subparsers.add_parser("skill", help="Manage vibraphone skills")
    skill_parser.add_argument(
        "skill_command",
        choices=["install", "status"],
        help="Skill command to run (install, status)",
    )
    skill_parser.set_defaults(func=cmd_skill)

    # setup-commands subcommand
    setup_parser = subparsers.add_parser(
        "setup-commands",
        help="Install /v slash commands to ~/.claude/commands/",
    )
    setup_parser.set_defaults(func=lambda args: cmd_setup_commands())

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
