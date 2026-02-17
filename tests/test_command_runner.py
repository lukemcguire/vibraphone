"""Unit tests for command_runner module.

Tests get_command for config resolution and run_command for async subprocess execution.
Uses pytest-mock for mocking asyncio subprocess and config.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from vibraphone.utils.command_runner import get_command, run_command


class TestGetCommand:
    """Tests for get_command function."""

    def test_get_command_returns_default(self, mocker) -> None:
        """get_command returns default 'just test' when no config override."""
        # Mock get_config to return config with no quality_gate.commands
        mock_config = MagicMock()
        mock_config.quality_gate = None
        # get_config is imported inside get_command from vibraphone.config
        mocker.patch("vibraphone.config.get_config", return_value=mock_config)

        result = get_command("test")

        assert result == "just test"

    def test_get_command_uses_config_override(self, mocker) -> None:
        """get_command uses config override when present."""
        # Mock get_config to return config with command override
        mock_config = MagicMock()
        mock_quality_gate = MagicMock()
        mock_quality_gate.commands = {"test": "pytest -xvs"}
        mock_config.quality_gate = mock_quality_gate
        mocker.patch("vibraphone.config.get_config", return_value=mock_config)

        result = get_command("test")

        assert result == "pytest -xvs"

    def test_get_command_with_component(self, mocker) -> None:
        """get_command appends component suffix for justfile commands."""
        mock_config = MagicMock()
        mock_config.quality_gate = None
        mocker.patch("vibraphone.config.get_config", return_value=mock_config)

        result = get_command("test", component="server")

        assert result == "just test-server"

    def test_get_command_component_no_justfile(self, mocker) -> None:
        """get_command leaves non-just command unchanged when component provided."""
        # Config has custom command that doesn't start with "just "
        mock_config = MagicMock()
        mock_quality_gate = MagicMock()
        mock_quality_gate.commands = {"test": "pytest -xvs"}
        mock_config.quality_gate = mock_quality_gate
        mocker.patch("vibraphone.config.get_config", return_value=mock_config)

        result = get_command("test", component="server")

        # Should NOT append -server since it's not a just command
        assert result == "pytest -xvs"

    def test_get_command_invalid_type(self, mocker) -> None:
        """get_command raises ValueError for unknown command type."""
        mock_config = MagicMock()
        mock_config.quality_gate = None
        mocker.patch("vibraphone.config.get_config", return_value=mock_config)

        with pytest.raises(ValueError) as exc_info:
            get_command("unknown")

        assert "Unknown command type" in str(exc_info.value)

    def test_get_command_partial_config_override(self, mocker) -> None:
        """get_command falls back to default for unconfigured command types."""
        # Config only has 'lint' override, not 'test'
        mock_config = MagicMock()
        mock_quality_gate = MagicMock()
        mock_quality_gate.commands = {"lint": "ruff check ."}
        mock_config.quality_gate = mock_quality_gate
        mocker.patch("vibraphone.config.get_config", return_value=mock_config)

        result = get_command("test")

        assert result == "just test"


class TestRunCommand:
    """Tests for run_command async function."""

    @pytest.mark.asyncio
    async def test_run_command_success(self, mocker, tmp_path: Path) -> None:
        """run_command returns 0 returncode with stdout on success."""
        # Mock asyncio.create_subprocess_exec
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"all tests passed\n", b""))
        mocker.patch("asyncio.create_subprocess_exec", return_value=mock_proc)

        returncode, stdout, stderr = await run_command("just test", cwd=tmp_path)

        assert returncode == 0
        assert stdout == "all tests passed\n"
        assert stderr == ""

    @pytest.mark.asyncio
    async def test_run_command_failure(self, mocker, tmp_path: Path) -> None:
        """run_command returns non-zero returncode with stderr on failure."""
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.communicate = AsyncMock(return_value=(b"", b"test failed\n"))
        mocker.patch("asyncio.create_subprocess_exec", return_value=mock_proc)

        returncode, stdout, stderr = await run_command("just test", cwd=tmp_path)

        assert returncode == 1
        assert stdout == ""
        assert stderr == "test failed\n"

    @pytest.mark.asyncio
    async def test_run_command_with_cwd(self, mocker, tmp_path: Path) -> None:
        """run_command passes cwd to subprocess."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))
        mock_create_subprocess = mocker.patch(
            "asyncio.create_subprocess_exec", return_value=mock_proc
        )

        await run_command("just test", cwd=tmp_path)

        # Verify cwd was passed to create_subprocess_exec
        call_kwargs = mock_create_subprocess.call_args
        assert call_kwargs[1]["cwd"] == tmp_path

    @pytest.mark.asyncio
    async def test_run_command_default_cwd(self, mocker) -> None:
        """run_command uses Path.cwd() when cwd not provided."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))
        mock_create_subprocess = mocker.patch(
            "asyncio.create_subprocess_exec", return_value=mock_proc
        )

        with patch("vibraphone.utils.command_runner.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/some/path")
            await run_command("just test")

            call_kwargs = mock_create_subprocess.call_args
            assert call_kwargs[1]["cwd"] == Path("/some/path")

    @pytest.mark.asyncio
    async def test_run_command_empty_command(self, mocker) -> None:
        """run_command returns error for empty command."""
        returncode, stdout, stderr = await run_command("")

        assert returncode == 1
        assert stdout == ""
        assert stderr == "Empty command"

    @pytest.mark.asyncio
    async def test_run_command_with_args(self, mocker, tmp_path: Path) -> None:
        """run_command parses and passes command args correctly."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"output\n", b""))
        mock_create_subprocess = mocker.patch(
            "asyncio.create_subprocess_exec", return_value=mock_proc
        )

        await run_command("pytest -xvs --tb=short", cwd=tmp_path)

        # Verify command was parsed correctly
        call_args = mock_create_subprocess.call_args
        # First positional arg is executable
        assert call_args[0][0] == "pytest"
        # Remaining positional args are the flags
        assert call_args[0][1] == "-xvs"
        assert call_args[0][2] == "--tb=short"

    @pytest.mark.asyncio
    async def test_run_command_captures_both_stdout_stderr(self, mocker, tmp_path: Path) -> None:
        """run_command captures both stdout and stderr."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(
            return_value=(b"some output\n", b"some warnings\n")
        )
        mocker.patch("asyncio.create_subprocess_exec", return_value=mock_proc)

        returncode, stdout, stderr = await run_command("just test", cwd=tmp_path)

        assert returncode == 0
        assert stdout == "some output\n"
        assert stderr == "some warnings\n"

    @pytest.mark.asyncio
    async def test_run_command_handles_unicode(self, mocker, tmp_path: Path) -> None:
        """run_command decodes output as UTF-8."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        # Unicode output
        mock_proc.communicate = AsyncMock(
            return_value=("Tests: \u2713 5 passed\n".encode(), b"")
        )
        mocker.patch("asyncio.create_subprocess_exec", return_value=mock_proc)

        returncode, stdout, stderr = await run_command("just test", cwd=tmp_path)

        assert "\u2713" in stdout
