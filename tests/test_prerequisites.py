"""Unit tests for prerequisites module.

Tests the prerequisite detection utilities for vibraphone external dependencies.
"""

from unittest.mock import patch

import pytest


class TestCheckPrerequisites:
    """Tests for check_prerequisites function."""

    def test_check_prerequisites_returns_structure(self) -> None:
        """Returns dict with platform, prerequisites, shell_script, missing_core."""
        from vibraphone.utils.prerequisites import check_prerequisites

        result = check_prerequisites()

        assert isinstance(result, dict)
        assert "platform" in result
        assert "prerequisites" in result
        assert "shell_script" in result
        assert "missing_core" in result
        assert "all_installed" in result

    def test_check_prerequisites_detects_git(self) -> None:
        """git.tool in prerequisites."""
        from vibraphone.utils.prerequisites import check_prerequisites

        result = check_prerequisites()

        tools = [p["tool"] for p in result["prerequisites"]]
        assert "git" in tools

        # Find git in prerequisites
        git_prereq = next(p for p in result["prerequisites"] if p["tool"] == "git")
        assert "installed" in git_prereq
        assert "install_command" in git_prereq

    def test_check_prerequisites_platform_detection(self) -> None:
        """Platform field is Darwin, Linux, or Windows."""
        from vibraphone.utils.prerequisites import check_prerequisites

        result = check_prerequisites()

        assert result["platform"] in ("Darwin", "Linux", "Windows")

    def test_check_prerequisites_missing_core_identified(self) -> None:
        """missing_core contains br, bv, git if not installed."""
        from vibraphone.utils.prerequisites import check_prerequisites

        with patch("vibraphone.utils.prerequisites.shutil.which", return_value=None):
            result = check_prerequisites()

            # All tools should be missing
            assert "br" in result["missing_core"]
            assert "bv" in result["missing_core"]
            assert "git" in result["missing_core"]

    def test_check_prerequisites_all_installed_when_present(self) -> None:
        """all_installed is True when all tools present."""
        from vibraphone.utils.prerequisites import check_prerequisites

        with patch("vibraphone.utils.prerequisites.shutil.which", return_value="/usr/bin/tool"):
            result = check_prerequisites()

            assert result["all_installed"] is True
            assert result["missing_core"] == []

    def test_check_prerequisites_returns_prerequisite_list(self) -> None:
        """prerequisites is list with correct structure."""
        from vibraphone.utils.prerequisites import check_prerequisites

        result = check_prerequisites()

        assert isinstance(result["prerequisites"], list)
        assert len(result["prerequisites"]) > 0

        for prereq in result["prerequisites"]:
            assert "tool" in prereq
            assert "installed" in prereq
            assert "install_command" in prereq


class TestInstallCommands:
    """Tests for INSTALL_COMMANDS configuration."""

    def test_install_commands_per_platform(self) -> None:
        """INSTALL_COMMANDS has entries for Darwin, Linux, Windows."""
        from vibraphone.utils.prerequisites import INSTALL_COMMANDS

        for tool in ["br", "bv", "git", "just", "node"]:
            assert tool in INSTALL_COMMANDS
            commands = INSTALL_COMMANDS[tool]
            assert "Darwin" in commands
            assert "Linux" in commands
            assert "Windows" in commands

    def test_install_commands_br_has_brew_for_darwin(self) -> None:
        """br install command for Darwin includes brew."""
        from vibraphone.utils.prerequisites import INSTALL_COMMANDS

        darwin_cmd = INSTALL_COMMANDS["br"]["Darwin"]
        assert "brew" in darwin_cmd or "cargo" in darwin_cmd

    def test_install_commands_git_has_apt_for_linux(self) -> None:
        """git install command for Linux includes apt."""
        from vibraphone.utils.prerequisites import INSTALL_COMMANDS

        linux_cmd = INSTALL_COMMANDS["git"]["Linux"]
        assert "apt" in linux_cmd or "brew" in linux_cmd

    def test_install_commands_have_scoop_for_windows(self) -> None:
        """Windows commands include scoop."""
        from vibraphone.utils.prerequisites import INSTALL_COMMANDS

        for tool in ["git", "just", "node"]:
            windows_cmd = INSTALL_COMMANDS[tool]["Windows"]
            assert "scoop" in windows_cmd


class TestPrerequisiteDataclass:
    """Tests for Prerequisite dataclass."""

    def test_prerequisite_fields(self) -> None:
        """Prerequisite has tool, installed, install_command fields."""
        from vibraphone.utils.prerequisites import Prerequisite

        prereq = Prerequisite(tool="test", installed=True, install_command="echo test")

        assert prereq.tool == "test"
        assert prereq.installed is True
        assert prereq.install_command == "echo test"


class TestShellScriptGeneration:
    """Tests for shell script generation."""

    def test_shell_script_all_installed(self) -> None:
        """Shell script indicates success when all tools present."""
        from vibraphone.utils.prerequisites import check_prerequisites

        with patch("vibraphone.utils.prerequisites.shutil.which", return_value="/usr/bin/tool"):
            result = check_prerequisites()

            assert "All prerequisites installed!" in result["shell_script"]

    def test_shell_script_missing_tools(self) -> None:
        """Shell script contains install commands for missing tools."""
        from vibraphone.utils.prerequisites import check_prerequisites

        with patch("vibraphone.utils.prerequisites.shutil.which", return_value=None):
            result = check_prerequisites()

            # Should be a bash script
            assert result["shell_script"].startswith("#!/bin/bash")
            # Should mention missing prerequisites
            assert "missing" in result["shell_script"].lower()

    def test_shell_script_includes_platform_specific_commands(self) -> None:
        """Shell script uses platform-specific install commands."""
        from vibraphone.utils.prerequisites import check_prerequisites

        with patch("vibraphone.utils.prerequisites.shutil.which", return_value=None):
            with patch("vibraphone.utils.prerequisites.platform.system", return_value="Linux"):
                result = check_prerequisites()

                # Should contain Linux-specific commands
                # (apt or cargo for br/bv which don't have Linux brew packages)
                assert "apt" in result["shell_script"] or "cargo" in result["shell_script"]


class TestNEW09PrerequisitesDetectsTools:
    """Verify NEW-09 requirement: check_prerequisites detects tools."""

    def test_NEW_09_prerequisites_detects_tools(self) -> None:
        """NEW-09: check_prerequisites detects br, bv, git, just, node/npx."""
        from vibraphone.utils.prerequisites import check_prerequisites

        # Test with all tools installed
        with patch("vibraphone.utils.prerequisites.shutil.which") as mock_which:
            # Simulate all tools installed
            mock_which.return_value = "/usr/bin/tool"

            result = check_prerequisites()

            tools_detected = [p["tool"] for p in result["prerequisites"]]
            assert "br" in tools_detected
            assert "bv" in tools_detected
            assert "git" in tools_detected
            assert "just" in tools_detected
            assert "node" in tools_detected

    def test_NEW_09_reports_install_commands_per_platform(self) -> None:
        """NEW-09: Reports platform-specific install commands."""
        from vibraphone.utils.prerequisites import INSTALL_COMMANDS

        # Verify each platform has commands for core tools
        for platform in ["Darwin", "Linux", "Windows"]:
            for tool in ["br", "bv", "git"]:
                assert tool in INSTALL_COMMANDS
                assert platform in INSTALL_COMMANDS[tool]
                assert len(INSTALL_COMMANDS[tool][platform]) > 0

    def test_NEW_09_core_dependencies_defined(self) -> None:
        """NEW-09: Core dependencies are br, bv, git."""
        from vibraphone.utils.prerequisites import CORE_DEPENDENCIES

        assert "br" in CORE_DEPENDENCIES
        assert "bv" in CORE_DEPENDENCIES
        assert "git" in CORE_DEPENDENCIES
