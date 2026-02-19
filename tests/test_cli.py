"""Unit tests for CLI module.

Tests the vibraphone CLI commands including setup-commands for installing
slash commands to ~/.claude/commands/.
"""

from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestCmdSetupCommandsSuccess:
    """Tests for successful cmd_setup_commands execution."""

    def test_cmd_setup_commands_success(self, tmp_path: Path, mocker) -> None:
        """cmd_setup_commands returns 0 and prints destination on success."""
        from vibraphone.cli import cmd_setup_commands

        # Mock get_bundled_command_path to return a temp file
        bundled_file = tmp_path / "v.md"
        bundled_file.write_text("# /v command")
        mocker.patch(
            "vibraphone.cli.get_bundled_command_path",
            return_value=bundled_file,
        )

        # Mock the destination path
        dest_dir = tmp_path / ".claude" / "commands"
        mocker.patch(
            "vibraphone.cli.COMMAND_DEST_PATH",
            dest_dir / "v.md",
        )

        # Mock shutil.copy2
        mock_copy = mocker.patch("shutil.copy2")

        # Capture stdout
        mock_stdout = StringIO()
        with patch("sys.stdout", mock_stdout):
            result = cmd_setup_commands()

        assert result == 0
        output = mock_stdout.getvalue()
        assert "Installed to" in output
        assert str(dest_dir / "v.md") in output
        assert "Restart Claude Code" in output
        mock_copy.assert_called_once()

    def test_cmd_setup_commands_creates_directory(
        self, tmp_path: Path, mocker
    ) -> None:
        """cmd_setup_commands creates ~/.claude/commands/ if missing."""
        from vibraphone.cli import cmd_setup_commands

        # Mock get_bundled_command_path
        bundled_file = tmp_path / "v.md"
        bundled_file.write_text("# /v command")
        mocker.patch(
            "vibraphone.cli.get_bundled_command_path",
            return_value=bundled_file,
        )

        # Set up destination that doesn't exist yet
        dest_dir = tmp_path / "newhome" / ".claude" / "commands"
        dest_file = dest_dir / "v.md"
        mocker.patch("vibraphone.cli.COMMAND_DEST_PATH", dest_file)

        # Mock shutil.copy2
        mocker.patch("shutil.copy2")

        # Run command
        with patch("sys.stdout", StringIO()):
            result = cmd_setup_commands()

        assert result == 0
        # Parent directory should have been created
        assert dest_dir.exists()


class TestCmdSetupCommandsErrors:
    """Tests for cmd_setup_commands error handling."""

    def test_cmd_setup_commands_missing_bundled_file(self, mocker) -> None:
        """cmd_setup_commands returns 1 when bundled file is missing."""
        from vibraphone.cli import cmd_setup_commands

        # Mock get_bundled_command_path to return None
        mocker.patch("vibraphone.cli.get_bundled_command_path", return_value=None)

        # Capture stderr
        mock_stderr = StringIO()
        with patch("sys.stderr", mock_stderr):
            result = cmd_setup_commands()

        assert result == 1
        error_output = mock_stderr.getvalue()
        assert "Bundled command file not found" in error_output
        assert "corrupt installation" in error_output

    def test_cmd_setup_commands_permission_error(
        self, tmp_path: Path, mocker
    ) -> None:
        """cmd_setup_commands returns 1 on permission error."""
        from vibraphone.cli import cmd_setup_commands

        # Mock get_bundled_command_path
        bundled_file = tmp_path / "v.md"
        bundled_file.write_text("# /v command")
        mocker.patch(
            "vibraphone.cli.get_bundled_command_path",
            return_value=bundled_file,
        )

        # Mock destination path
        dest_file = tmp_path / ".claude" / "commands" / "v.md"
        mocker.patch("vibraphone.cli.COMMAND_DEST_PATH", dest_file)

        # Mock shutil.copy2 to raise PermissionError
        mocker.patch("shutil.copy2", side_effect=PermissionError("Permission denied"))

        # Capture stderr
        mock_stderr = StringIO()
        with patch("sys.stderr", mock_stderr):
            result = cmd_setup_commands()

        assert result == 1
        error_output = mock_stderr.getvalue()
        assert "Permission denied" in error_output
        assert "Check file permissions" in error_output


class TestGetBundledCommandPath:
    """Tests for get_bundled_command_path function."""

    def test_get_bundled_command_path_dev_mode(self, tmp_path: Path, mocker) -> None:
        """get_bundled_command_path falls back to dev path when not installed."""
        from vibraphone.cli import get_bundled_command_path

        # Mock importlib.resources.files to raise ImportError (inside function)
        mocker.patch(
            "importlib.resources.files",
            side_effect=ImportError("No package"),
        )

        # Create a mock dev path that exists
        dev_commands = tmp_path / "commands"
        dev_commands.mkdir()
        v_md = dev_commands / "v.md"
        v_md.write_text("# /v command")

        # Mock __file__ to point to our temp directory
        cli_file = tmp_path / "cli.py"
        cli_file.write_text("# cli")
        mocker.patch("vibraphone.cli.__file__", str(cli_file))

        result = get_bundled_command_path()

        # Should find the dev path
        assert result is not None
        assert result.name == "v.md"

    def test_get_bundled_command_path_installed(self, mocker) -> None:
        """get_bundled_command_path uses importlib.resources when available."""
        from vibraphone.cli import get_bundled_command_path

        # Create a mock traversable file
        mock_file = MagicMock()
        mock_file.is_file.return_value = True
        mock_file.__str__ = lambda self: "/mock/installed/v.md"

        # Mock files() to return the mock file
        mock_files = MagicMock()
        mock_files.joinpath.return_value = mock_file
        mocker.patch("importlib.resources.files", return_value=mock_files)

        result = get_bundled_command_path()

        assert result is not None
        assert "v.md" in str(result)

    def test_get_bundled_command_path_not_found(self, mocker) -> None:
        """get_bundled_command_path returns None when file doesn't exist."""
        from vibraphone.cli import get_bundled_command_path

        # Mock importlib.resources.files to raise ImportError
        mocker.patch(
            "importlib.resources.files",
            side_effect=ImportError("No package"),
        )

        # Mock __file__ but don't create the commands directory
        mocker.patch("vibraphone.cli.__file__", "/nonexistent/cli.py")

        result = get_bundled_command_path()

        assert result is None


class TestSetupCommandsParser:
    """Tests for CLI parser integration."""

    def test_setup_commands_in_parser_help(self) -> None:
        """setup-commands is registered in CLI parser."""
        from vibraphone.cli import create_parser

        parser = create_parser()
        help_text = parser.format_help()

        assert "setup-commands" in help_text

    def test_setup_commands_subparser_callable(self, mocker) -> None:
        """setup-commands subparser calls cmd_setup_commands."""
        from vibraphone.cli import create_parser

        # Mock cmd_setup_commands
        mock_cmd = mocker.patch("vibraphone.cli.cmd_setup_commands", return_value=0)

        parser = create_parser()
        args = parser.parse_args(["setup-commands"])

        assert hasattr(args, "func")
        # Call the function stored in func
        result = args.func(args)
        assert result == 0
        mock_cmd.assert_called_once()
