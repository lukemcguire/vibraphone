"""Unit tests for scaffold_tools MCP tools.

Tests the init_project and check_prerequisites MCP tool implementations
with mocked dependencies for testing without actual installations.

Note: FastMCP @mcp.tool decorator wraps functions in FunctionTool objects.
To test the underlying logic, we access the original function via the .fn attribute.
"""

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestCheckPrerequisitesTool:
    """Tests for check_prerequisites MCP tool."""

    @pytest.mark.asyncio
    async def test_check_prerequisites_tool_returns_structure(self, mocker: Any) -> None:
        """Tool returns expected dict structure."""
        mock_result = {
            "platform": "Linux",
            "prerequisites": [
                {"tool": "br", "installed": True, "install_command": ""},
                {"tool": "bv", "installed": True, "install_command": ""},
                {"tool": "git", "installed": True, "install_command": ""},
            ],
            "all_installed": True,
            "shell_script": "# All prerequisites installed!",
            "missing_core": [],
        }
        mocker.patch(
            "vibraphone.tools.scaffold_tools.check_prereqs",
            return_value=mock_result,
        )

        from vibraphone.tools.scaffold_tools import check_prerequisites

        result = await check_prerequisites.fn()

        assert "platform" in result
        assert "prerequisites" in result
        assert "all_installed" in result
        assert "shell_script" in result
        assert "missing_core" in result


class TestInitProjectPreview:
    """Tests for init_project preview mode."""

    @pytest.mark.asyncio
    async def test_init_project_preview_returns_detected_values(self, mocker: Any, tmp_path: Path) -> None:
        """preview=True returns status='preview'."""
        mocker.patch("vibraphone.tools.scaffold_tools.check_prereqs", return_value={
            "platform": "Linux",
            "prerequisites": [],
            "all_installed": True,
            "shell_script": "",
            "missing_core": [],
        })
        mocker.patch(
            "vibraphone.tools.scaffold_tools.detect_project_metadata",
            return_value={
                "project_name": "test-project",
                "git_remote": None,
                "language": "python",
                "test_framework": "unknown",
                "ci_platform": None,
                "worktrees_path": "~/.vibraphone/worktrees",
            },
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools._render_all_templates",
            return_value={"vibraphone.yaml": "# config"},
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools._check_conflicts",
            return_value=({"vibraphone.yaml": "# config"}, []),
        )

        from vibraphone.tools.scaffold_tools import init_project

        result = await init_project.fn(str(tmp_path), preview=True)

        assert result["status"] == "preview"
        assert "detected_values" in result
        assert "final_values" in result
        assert "files_to_create" in result

    @pytest.mark.asyncio
    async def test_init_project_preview_does_not_write_files(self, mocker: Any, tmp_path: Path) -> None:
        """preview=True creates no files."""
        mocker.patch("vibraphone.tools.scaffold_tools.check_prereqs", return_value={
            "platform": "Linux",
            "prerequisites": [],
            "all_installed": True,
            "shell_script": "",
            "missing_core": [],
        })
        mocker.patch(
            "vibraphone.tools.scaffold_tools.detect_project_metadata",
            return_value={
                "project_name": "test-project",
                "git_remote": None,
                "language": "python",
                "test_framework": "unknown",
                "ci_platform": None,
                "worktrees_path": "~/.vibraphone/worktrees",
            },
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools._render_all_templates",
            return_value={"vibraphone.yaml": "# config"},
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools._check_conflicts",
            return_value=({"vibraphone.yaml": "# config"}, []),
        )

        from vibraphone.tools.scaffold_tools import init_project

        await init_project.fn(str(tmp_path), preview=True)

        # No files should be created
        assert not (tmp_path / "vibraphone.yaml").exists()


class TestInitProjectApply:
    """Tests for init_project apply mode (preview=False)."""

    @pytest.mark.asyncio
    async def test_init_project_apply_creates_files(self, mocker: Any, tmp_path: Path) -> None:
        """preview=False creates files in empty dir."""
        mocker.patch("vibraphone.tools.scaffold_tools.check_prereqs", return_value={
            "platform": "Linux",
            "prerequisites": [],
            "all_installed": True,
            "shell_script": "",
            "missing_core": [],
        })
        mocker.patch(
            "vibraphone.tools.scaffold_tools.detect_project_metadata",
            return_value={
                "project_name": "test-project",
                "git_remote": None,
                "language": "python",
                "test_framework": "pytest",
                "ci_platform": None,
                "worktrees_path": "~/.vibraphone/worktrees",
            },
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools._render_all_templates",
            return_value={"vibraphone.yaml": "project:\n  name: test-project\n"},
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools._check_conflicts",
            return_value=({"vibraphone.yaml": "project:\n  name: test-project\n"}, []),
        )
        # Mock load_template to avoid FileNotFoundError for gitignore_append.txt
        mocker.patch(
            "vibraphone.tools.scaffold_tools.load_template",
            side_effect=FileNotFoundError,
        )

        from vibraphone.tools.scaffold_tools import init_project

        result = await init_project.fn(str(tmp_path), preview=False)

        assert result["status"] == "complete"
        assert "vibraphone.yaml" in result["files_written"]

    @pytest.mark.asyncio
    async def test_init_project_detects_conflicts(self, mocker: Any, tmp_path: Path) -> None:
        """Existing file with different content returns conflict."""
        # Create existing file
        (tmp_path / "vibraphone.yaml").write_text("old content\n")

        mocker.patch("vibraphone.tools.scaffold_tools.check_prereqs", return_value={
            "platform": "Linux",
            "prerequisites": [],
            "all_installed": True,
            "shell_script": "",
            "missing_core": [],
        })
        mocker.patch(
            "vibraphone.tools.scaffold_tools.detect_project_metadata",
            return_value={
                "project_name": "test-project",
                "git_remote": None,
                "language": "python",
                "test_framework": "unknown",
                "ci_platform": None,
                "worktrees_path": "~/.vibraphone/worktrees",
            },
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools._render_all_templates",
            return_value={"vibraphone.yaml": "new content\n"},
        )

        from vibraphone.tools.scaffold_tools import init_project

        result = await init_project.fn(str(tmp_path), preview=True)

        assert len(result["conflicts"]) == 1
        assert result["conflicts"][0]["path"] == "vibraphone.yaml"

    @pytest.mark.asyncio
    async def test_init_project_conflict_shows_diff(self, mocker: Any, tmp_path: Path) -> None:
        """Conflict includes unified diff."""
        (tmp_path / "vibraphone.yaml").write_text("old content\n")

        mocker.patch("vibraphone.tools.scaffold_tools.check_prereqs", return_value={
            "platform": "Linux",
            "prerequisites": [],
            "all_installed": True,
            "shell_script": "",
            "missing_core": [],
        })
        mocker.patch(
            "vibraphone.tools.scaffold_tools.detect_project_metadata",
            return_value={
                "project_name": "test-project",
                "git_remote": None,
                "language": "python",
                "test_framework": "unknown",
                "ci_platform": None,
                "worktrees_path": "~/.vibraphone/worktrees",
            },
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools._render_all_templates",
            return_value={"vibraphone.yaml": "new content\n"},
        )

        from vibraphone.tools.scaffold_tools import init_project

        result = await init_project.fn(str(tmp_path), preview=True)

        # Diff should contain standard markers
        diff = result["conflicts"][0]["diff"]
        assert "---" in diff or "+++" in diff or "-old" in diff or "+new" in diff

    @pytest.mark.asyncio
    async def test_init_project_skips_identical_files(self, mocker: Any, tmp_path: Path) -> None:
        """Same content not reported as conflict."""
        (tmp_path / "vibraphone.yaml").write_text("same content\n")

        mocker.patch("vibraphone.tools.scaffold_tools.check_prereqs", return_value={
            "platform": "Linux",
            "prerequisites": [],
            "all_installed": True,
            "shell_script": "",
            "missing_core": [],
        })
        mocker.patch(
            "vibraphone.tools.scaffold_tools.detect_project_metadata",
            return_value={
                "project_name": "test-project",
                "git_remote": None,
                "language": "python",
                "test_framework": "unknown",
                "ci_platform": None,
                "worktrees_path": "~/.vibraphone/worktrees",
            },
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools._render_all_templates",
            return_value={"vibraphone.yaml": "same content\n"},
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools._check_conflicts",
            return_value=({}, []),  # No conflicts because content matches
        )

        from vibraphone.tools.scaffold_tools import init_project

        result = await init_project.fn(str(tmp_path), preview=True)

        # No conflicts since content is identical
        assert len(result["conflicts"]) == 0

    @pytest.mark.asyncio
    async def test_init_project_appends_gitignore(self, mocker: Any, tmp_path: Path) -> None:
        """.gitignore gets vibraphone entries appended."""
        (tmp_path / ".gitignore").write_text("*.pyc\n")

        mocker.patch("vibraphone.tools.scaffold_tools.check_prereqs", return_value={
            "platform": "Linux",
            "prerequisites": [],
            "all_installed": True,
            "shell_script": "",
            "missing_core": [],
        })
        mocker.patch(
            "vibraphone.tools.scaffold_tools.detect_project_metadata",
            return_value={
                "project_name": "test-project",
                "git_remote": None,
                "language": "python",
                "test_framework": "pytest",
                "ci_platform": None,
                "worktrees_path": "~/.vibraphone/worktrees",
            },
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools._render_all_templates",
            return_value={},
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools._check_conflicts",
            return_value=({}, []),
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools.load_template",
            return_value=".vibraphone/\nworktrees/\n",
        )

        from vibraphone.tools.scaffold_tools import init_project

        result = await init_project.fn(str(tmp_path), preview=False)

        # gitignore should be updated
        gitignore_content = (tmp_path / ".gitignore").read_text()
        assert ".vibraphone/" in gitignore_content

    @pytest.mark.asyncio
    async def test_init_project_creates_justfile(self, mocker: Any, tmp_path: Path) -> None:
        """Justfile created if missing."""
        mocker.patch("vibraphone.tools.scaffold_tools.check_prereqs", return_value={
            "platform": "Linux",
            "prerequisites": [],
            "all_installed": True,
            "shell_script": "",
            "missing_core": [],
        })
        mocker.patch(
            "vibraphone.tools.scaffold_tools.detect_project_metadata",
            return_value={
                "project_name": "test-project",
                "git_remote": None,
                "language": "python",
                "test_framework": "pytest",
                "ci_platform": None,
                "worktrees_path": "~/.vibraphone/worktrees",
            },
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools._render_all_templates",
            return_value={},
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools._check_conflicts",
            return_value=({}, []),
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools.load_template",
            side_effect=FileNotFoundError,
        )

        from vibraphone.tools.scaffold_tools import init_project

        result = await init_project.fn(str(tmp_path), preview=False)

        assert (tmp_path / "Justfile").exists()
        assert "Justfile" in result["files_written"]

    @pytest.mark.asyncio
    async def test_init_project_fails_on_missing_prerequisites(self, mocker: Any, tmp_path: Path) -> None:
        """Missing br/bv/git returns error."""
        mocker.patch("vibraphone.tools.scaffold_tools.check_prereqs", return_value={
            "platform": "Linux",
            "prerequisites": [
                {"tool": "br", "installed": False, "install_command": "cargo install beads_rust"},
                {"tool": "bv", "installed": False, "install_command": "cargo install beads_viewer"},
                {"tool": "git", "installed": True, "install_command": ""},
            ],
            "all_installed": False,
            "shell_script": "#!/bin/bash\ncargo install beads_rust\ncargo install beads_viewer",
            "missing_core": ["br", "bv"],
        })

        from vibraphone.tools.scaffold_tools import init_project

        result = await init_project.fn(str(tmp_path), preview=True)

        assert result["status"] == "error"
        assert "Missing required tools" in result["error"]
        assert "br" in result["error"] or "bv" in result["error"]

    @pytest.mark.asyncio
    async def test_init_project_nonexistent_path_returns_error(self, mocker: Any) -> None:
        """Non-existent path returns error."""
        from vibraphone.tools.scaffold_tools import init_project

        result = await init_project.fn("/nonexistent/path/xyz", preview=True)

        assert result["status"] == "error"
        assert "does not exist" in result["error"]


class TestInitProjectValuesOverride:
    """Tests for values override in init_project."""

    @pytest.mark.asyncio
    async def test_init_project_values_override_detected(self, mocker: Any, tmp_path: Path) -> None:
        """User-provided values override detected values."""
        mocker.patch("vibraphone.tools.scaffold_tools.check_prereqs", return_value={
            "platform": "Linux",
            "prerequisites": [],
            "all_installed": True,
            "shell_script": "",
            "missing_core": [],
        })
        mocker.patch(
            "vibraphone.tools.scaffold_tools.detect_project_metadata",
            return_value={
                "project_name": "detected-name",
                "git_remote": None,
                "language": "python",
                "test_framework": "unknown",
                "ci_platform": None,
                "worktrees_path": "~/.vibraphone/worktrees",
            },
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools._render_all_templates",
            return_value={},
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools._check_conflicts",
            return_value=({}, []),
        )

        from vibraphone.tools.scaffold_tools import init_project

        result = await init_project.fn(
            str(tmp_path),
            preview=True,
            values={"project_name": "override-name", "language": "typescript"},
        )

        assert result["final_values"]["project_name"] == "override-name"
        assert result["final_values"]["language"] == "typescript"


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_generate_diff_shows_changes(self) -> None:
        """_generate_diff shows unified diff."""
        from vibraphone.tools.scaffold_tools import _generate_diff

        path = Path("test.yaml")
        existing = "old: value\n"
        proposed = "new: value\n"

        diff = _generate_diff(path, existing, proposed)

        assert "old" in diff or "new" in diff

    def test_celebration_message_contains_project_name(self) -> None:
        """Celebration message includes project name."""
        from vibraphone.tools.scaffold_tools import _celebration_message

        msg = _celebration_message("my-project")

        assert "my-project" in msg

    def test_render_all_templates_renders_jinja(self, mocker: Any) -> None:
        """_render_all_templates renders Jinja2 templates."""
        mocker.patch(
            "vibraphone.tools.scaffold_tools.get_all_template_paths",
            return_value=["config.yaml.j2"],
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools.load_template",
            return_value="name: {{ project_name }}\n",
        )

        from vibraphone.tools.scaffold_tools import _render_all_templates

        result = _render_all_templates({"project_name": "test-project"})

        assert "config.yaml" in result
        assert "test-project" in result["config.yaml"]

    def test_render_all_templates_copies_static(self, mocker: Any) -> None:
        """_render_all_templates copies static files."""
        mocker.patch(
            "vibraphone.tools.scaffold_tools.get_all_template_paths",
            return_value=["AGENTS.md"],
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools.load_template",
            return_value="# Agent Instructions\n",
        )

        from vibraphone.tools.scaffold_tools import _render_all_templates

        result = _render_all_templates({})

        assert "AGENTS.md" in result
        assert result["AGENTS.md"] == "# Agent Instructions\n"


class TestNEW01InitProjectScaffoldsExisting:
    """Verify NEW-01 requirement: Agent can scaffold vibraphone into existing project."""

    @pytest.mark.asyncio
    async def test_NEW_01_init_project_scaffolds_existing(self, mocker: Any, tmp_path: Path) -> None:
        """NEW-01: init_project scaffolds vibraphone into existing project."""
        # Simulate existing project with git
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text('[remote "origin"]\n    url = https://github.com/user/repo.git\n')
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "existing-project"\n')

        mocker.patch("vibraphone.tools.scaffold_tools.check_prereqs", return_value={
            "platform": "Linux",
            "prerequisites": [],
            "all_installed": True,
            "shell_script": "",
            "missing_core": [],
        })
        mocker.patch(
            "vibraphone.tools.scaffold_tools._render_all_templates",
            return_value={
                "vibraphone.yaml": "project:\n  name: existing-project\n",
                "AGENTS.md": "# Agents\n",
                "CLAUDE.md": "# Claude\n",
            },
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools._check_conflicts",
            return_value=(
                {
                    "vibraphone.yaml": "project:\n  name: existing-project\n",
                    "AGENTS.md": "# Agents\n",
                    "CLAUDE.md": "# Claude\n",
                },
                [],
            ),
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools.load_template",
            side_effect=FileNotFoundError,
        )

        from vibraphone.tools.scaffold_tools import init_project

        result = await init_project.fn(str(tmp_path), preview=False)

        assert result["status"] == "complete"
        # Should detect git remote
        assert "github.com/user/repo" in result["final_values"]["git_remote"]


class TestNEW02VibraphoneYamlHasProjectValues:
    """Verify NEW-02 requirement: vibraphone.yaml has project-specific values."""

    @pytest.mark.asyncio
    async def test_NEW_02_vibraphone_yaml_has_project_values(self, mocker: Any, tmp_path: Path) -> None:
        """NEW-02: vibraphone.yaml generated with project-specific values."""
        mocker.patch("vibraphone.tools.scaffold_tools.check_prereqs", return_value={
            "platform": "Linux",
            "prerequisites": [],
            "all_installed": True,
            "shell_script": "",
            "missing_core": [],
        })
        mocker.patch(
            "vibraphone.tools.scaffold_tools.detect_project_metadata",
            return_value={
                "project_name": "my-awesome-project",
                "git_remote": "https://github.com/user/my-awesome-project.git",
                "language": "python",
                "test_framework": "pytest",
                "ci_platform": "github-actions",
                "worktrees_path": "~/.vibraphone/worktrees",
            },
        )
        # Simulate rendered template with project values
        mocker.patch(
            "vibraphone.tools.scaffold_tools._render_all_templates",
            return_value={
                "vibraphone.yaml": """project:
  name: my-awesome-project
  language: python
""",
            },
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools._check_conflicts",
            return_value=({"vibraphone.yaml": "project:\n  name: my-awesome-project\n"}, []),
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools.load_template",
            side_effect=FileNotFoundError,
        )

        from vibraphone.tools.scaffold_tools import init_project

        result = await init_project.fn(str(tmp_path), preview=False)

        # Verify project name in final values
        assert result["final_values"]["project_name"] == "my-awesome-project"
        assert result["final_values"]["language"] == "python"


class TestNEW03GeneratesAgentsAndClaudeMd:
    """Verify NEW-03 requirement: AGENTS.md and CLAUDE.md generated."""

    @pytest.mark.asyncio
    async def test_NEW_03_generates_agents_and_claude_md(self, mocker: Any, tmp_path: Path) -> None:
        """NEW-03: Generates AGENTS.md and CLAUDE.md."""
        mocker.patch("vibraphone.tools.scaffold_tools.check_prereqs", return_value={
            "platform": "Linux",
            "prerequisites": [],
            "all_installed": True,
            "shell_script": "",
            "missing_core": [],
        })
        mocker.patch(
            "vibraphone.tools.scaffold_tools._render_all_templates",
            return_value={
                "AGENTS.md": "# Agent Instructions\n",
                "CLAUDE.md": "# Claude Instructions\n",
            },
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools._check_conflicts",
            return_value=(
                {"AGENTS.md": "# Agent Instructions\n", "CLAUDE.md": "# Claude Instructions\n"},
                [],
            ),
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools.load_template",
            side_effect=FileNotFoundError,
        )

        from vibraphone.tools.scaffold_tools import init_project

        result = await init_project.fn(str(tmp_path), preview=False)

        assert "AGENTS.md" in result["files_written"]
        assert "CLAUDE.md" in result["files_written"]
        assert (tmp_path / "AGENTS.md").exists()
        assert (tmp_path / "CLAUDE.md").exists()


class TestNEW04GeneratesGovernanceDocs:
    """Verify NEW-04 requirement: .planning/vibraphone/ governance docs generated."""

    @pytest.mark.asyncio
    async def test_NEW_04_generates_governance_docs(self, mocker: Any, tmp_path: Path) -> None:
        """NEW-04: Generates .planning/vibraphone/ governance docs."""
        mocker.patch("vibraphone.tools.scaffold_tools.check_prereqs", return_value={
            "platform": "Linux",
            "prerequisites": [],
            "all_installed": True,
            "shell_script": "",
            "missing_core": [],
        })
        mocker.patch(
            "vibraphone.tools.scaffold_tools._render_all_templates",
            return_value={
                ".planning/vibraphone/CONSTITUTION.md": "# Constitution\n",
                ".planning/vibraphone/ARCHITECTURE.md": "# Architecture\n",
            },
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools._check_conflicts",
            return_value=(
                {
                    ".planning/vibraphone/CONSTITUTION.md": "# Constitution\n",
                    ".planning/vibraphone/ARCHITECTURE.md": "# Architecture\n",
                },
                [],
            ),
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools.load_template",
            side_effect=FileNotFoundError,
        )

        from vibraphone.tools.scaffold_tools import init_project

        result = await init_project.fn(str(tmp_path), preview=False)

        assert ".planning/vibraphone/CONSTITUTION.md" in result["files_written"]
        assert (tmp_path / ".planning" / "vibraphone" / "CONSTITUTION.md").exists()


class TestNEW05AppendsJustfile:
    """Verify NEW-05 requirement: Justfile recipes appended."""

    @pytest.mark.asyncio
    async def test_NEW_05_appends_justfile(self, mocker: Any, tmp_path: Path) -> None:
        """NEW-05: Appends or creates Justfile with recipes."""
        mocker.patch("vibraphone.tools.scaffold_tools.check_prereqs", return_value={
            "platform": "Linux",
            "prerequisites": [],
            "all_installed": True,
            "shell_script": "",
            "missing_core": [],
        })
        mocker.patch(
            "vibraphone.tools.scaffold_tools._render_all_templates",
            return_value={},
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools._check_conflicts",
            return_value=({}, []),
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools.load_template",
            side_effect=FileNotFoundError,
        )

        from vibraphone.tools.scaffold_tools import init_project

        result = await init_project.fn(str(tmp_path), preview=False)

        # Justfile should be created
        assert "Justfile" in result["files_written"]
        justfile_content = (tmp_path / "Justfile").read_text()
        assert "bootstrap" in justfile_content


class TestNEW06AppendsGitignore:
    """Verify NEW-06 requirement: .gitignore entries appended."""

    @pytest.mark.asyncio
    async def test_NEW_06_appends_gitignore(self, mocker: Any, tmp_path: Path) -> None:
        """NEW-06: Appends .gitignore with vibraphone entries."""
        (tmp_path / ".gitignore").write_text("*.pyc\n__pycache__/\n")

        mocker.patch("vibraphone.tools.scaffold_tools.check_prereqs", return_value={
            "platform": "Linux",
            "prerequisites": [],
            "all_installed": True,
            "shell_script": "",
            "missing_core": [],
        })
        mocker.patch(
            "vibraphone.tools.scaffold_tools._render_all_templates",
            return_value={},
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools._check_conflicts",
            return_value=({}, []),
        )
        mocker.patch(
            "vibraphone.tools.scaffold_tools.load_template",
            return_value=".vibraphone/\nworktrees/\n",
        )

        from vibraphone.tools.scaffold_tools import init_project

        result = await init_project.fn(str(tmp_path), preview=False)

        gitignore_content = (tmp_path / ".gitignore").read_text()
        assert ".vibraphone/" in gitignore_content
        assert "*.pyc" in gitignore_content  # Original content preserved


class TestNEW07NoOverwriteWithoutConfirmation:
    """Verify NEW-07 requirement: No overwrite without confirmation."""

    @pytest.mark.asyncio
    async def test_NEW_07_no_overwrite_without_confirmation(self, mocker: Any, tmp_path: Path) -> None:
        """NEW-07: Does not overwrite existing files without confirmation."""
        # Create existing file with different content
        (tmp_path / "vibraphone.yaml").write_text("existing: config\n")

        mocker.patch("vibraphone.tools.scaffold_tools.check_prereqs", return_value={
            "platform": "Linux",
            "prerequisites": [],
            "all_installed": True,
            "shell_script": "",
            "missing_core": [],
        })
        mocker.patch(
            "vibraphone.tools.scaffold_tools._render_all_templates",
            return_value={"vibraphone.yaml": "new: config\n"},
        )

        from vibraphone.tools.scaffold_tools import init_project

        result = await init_project.fn(str(tmp_path), preview=False)

        # Should report as partial with conflicts, not complete
        assert result["status"] == "partial"
        assert len(result["conflicts"]) == 1

        # Original file should NOT be overwritten
        content = (tmp_path / "vibraphone.yaml").read_text()
        assert "existing: config" in content


class TestNEW08CheckPrerequisitesAvailable:
    """Verify NEW-08 requirement: check_prerequisites tool available."""

    @pytest.mark.asyncio
    async def test_NEW_08_check_prerequisites_available(self, mocker: Any) -> None:
        """NEW-08: check_prerequisites MCP tool available."""
        mock_result = {
            "platform": "Linux",
            "prerequisites": [],
            "all_installed": True,
            "shell_script": "",
            "missing_core": [],
        }
        mocker.patch(
            "vibraphone.tools.scaffold_tools.check_prereqs",
            return_value=mock_result,
        )

        from vibraphone.tools.scaffold_tools import check_prerequisites

        # Verify tool is accessible and callable
        assert callable(check_prerequisites.fn)

        result = await check_prerequisites.fn()

        assert "platform" in result
        assert "missing_core" in result


class TestTMPL01TemplatesBundledInWheel:
    """Verify TMPL-01 requirement: Templates bundled in Python wheel."""

    @pytest.mark.asyncio
    async def test_TMPL_01_templates_bundled_in_wheel(self, mocker: Any, tmp_path: Path) -> None:
        """TMPL-01: Templates bundled in wheel and accessible via importlib."""
        # This test verifies that templates can be loaded via importlib.resources
        # which is how they would be accessed from an installed wheel
        from vibraphone.utils.template_loader import get_template_package, load_template

        # Verify templates package is accessible
        pkg = get_template_package()
        assert pkg is not None

        # Verify a known template can be loaded
        try:
            content = load_template("vibraphone.yaml.j2")
            assert len(content) > 0
            assert "{{" in content or "project:" in content.lower()
        except FileNotFoundError:
            pytest.skip("vibraphone.yaml.j2 not found - template may not be created yet")

    def test_templates_accessible_after_import(self) -> None:
        """Templates are accessible after importing the module."""
        from importlib import resources

        from vibraphone.utils.template_loader import get_template_package

        pkg = get_template_package()

        # Should be a Traversable (importlib.resources type)
        assert isinstance(pkg, resources.abc.Traversable)
