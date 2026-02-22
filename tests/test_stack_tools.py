"""Unit tests for stack_tools - configure_stack."""

from pathlib import Path
from typing import Any

import pytest


class TestRenderComponentRecipes:
    """Tests for _render_component_recipes function."""

    def test_renders_test_recipe(self) -> None:
        """Should render test recipe with correct name."""
        from vibraphone.tools.stack_tools import _render_component_recipes

        commands = {"test_command": "pytest", "lint_command": "ruff", "format_command": "ruff format"}
        result = _render_component_recipes("backend", "./src", commands)
        assert "test-backend *ARGS:" in result
        assert "cd ./src && pytest {ARGS}" in result

    def test_renders_lint_recipe(self) -> None:
        """Should render lint recipe."""
        from vibraphone.tools.stack_tools import _render_component_recipes

        commands = {"test_command": "pytest", "lint_command": "ruff check", "format_command": "ruff format"}
        result = _render_component_recipes("backend", "./src", commands)
        assert "lint-backend:" in result
        assert "cd ./src && ruff check" in result

    def test_renders_format_recipe(self) -> None:
        """Should render format recipe."""
        from vibraphone.tools.stack_tools import _render_component_recipes

        commands = {"test_command": "pytest", "lint_command": "ruff", "format_command": "ruff format"}
        result = _render_component_recipes("backend", "./src", commands)
        assert "format-backend:" in result

    def test_marks_recipes_private(self) -> None:
        """Should mark per-component recipes as [private]."""
        from vibraphone.tools.stack_tools import _render_component_recipes

        commands = {"test_command": "pytest", "lint_command": "ruff", "format_command": "ruff format"}
        result = _render_component_recipes("backend", "./src", commands)
        assert result.count("[private]") == 3

    def test_uses_custom_root(self) -> None:
        """Should use custom root path in recipes."""
        from vibraphone.tools.stack_tools import _render_component_recipes

        commands = {"test_command": "pytest", "lint_command": "ruff", "format_command": "ruff format"}
        result = _render_component_recipes("frontend", "./packages/web", commands)
        assert "cd ./packages/web" in result


class TestRenderComponentSection:
    """Tests for _render_component_section function."""

    def test_includes_section_markers(self) -> None:
        """Should include start and end section markers."""
        from vibraphone.tools.stack_tools import _render_component_section

        components = {"backend": {"language": "python"}}
        result = _render_component_section(components)
        assert "# === COMPONENT RECIPES ===" in result
        assert "# === END COMPONENT RECIPES ===" in result

    def test_includes_aggregate_recipes(self) -> None:
        """Should include aggregate test/lint/format recipes."""
        from vibraphone.tools.stack_tools import _render_component_section

        components = {"backend": {"language": "python"}}
        result = _render_component_section(components)
        assert "test *ARGS:" in result
        assert "lint:" in result
        assert "format:" in result

    def test_aggregate_depends_on_components(self) -> None:
        """Aggregate recipes should depend on component recipes."""
        from vibraphone.tools.stack_tools import _render_component_section

        components = {"backend": {"language": "python"}, "frontend": {"language": "typescript"}}
        result = _render_component_section(components)
        assert "test-backend" in result
        assert "test-frontend" in result

    def test_uses_stack_defaults_for_language(self) -> None:
        """Should use STACK_DEFAULTS for language commands."""
        from vibraphone.tools.stack_tools import _render_component_section

        components = {"backend": {"language": "python"}}
        result = _render_component_section(components)
        # Python defaults: pytest, ruff check, ruff format
        assert "pytest" in result

    def test_custom_commands_override_defaults(self) -> None:
        """Custom commands should override STACK_DEFAULTS."""
        from vibraphone.tools.stack_tools import _render_component_section

        components = {
            "backend": {
                "language": "python",
                "test_command": "uv run pytest -x",
            }
        }
        result = _render_component_section(components)
        assert "uv run pytest -x" in result


class TestUpdateJustfileSection:
    """Tests for _update_justfile_section function."""

    def test_creates_new_justfile_if_missing(self, tmp_path: Path) -> None:
        """Should create new Justfile if it doesn't exist."""
        from vibraphone.tools.stack_tools import _update_justfile_section

        justfile = tmp_path / "Justfile"
        section = "# === COMPONENT RECIPES ===\ncontent\n# === END COMPONENT RECIPES ==="
        _update_justfile_section(justfile, section)
        assert justfile.exists()
        assert "content" in justfile.read_text()

    def test_replaces_existing_section(self, tmp_path: Path) -> None:
        """Should replace existing section between markers."""
        from vibraphone.tools.stack_tools import _update_justfile_section

        justfile = tmp_path / "Justfile"
        justfile.write_text("# === COMPONENT RECIPES ===\nold\n# === END COMPONENT RECIPES ===\nother content")
        section = "# === COMPONENT RECIPES ===\nnew\n# === END COMPONENT RECIPES ==="
        _update_justfile_section(justfile, section)
        content = justfile.read_text()
        assert "new" in content
        assert "old" not in content
        assert "other content" in content

    def test_preserves_content_outside_section(self, tmp_path: Path) -> None:
        """Should preserve content outside the section markers."""
        from vibraphone.tools.stack_tools import _update_justfile_section

        justfile = tmp_path / "Justfile"
        justfile.write_text("header\n# === COMPONENT RECIPES ===\nold\n# === END COMPONENT RECIPES ===\nfooter")
        section = "# === COMPONENT RECIPES ===\nnew\n# === END COMPONENT RECIPES ==="
        _update_justfile_section(justfile, section)
        content = justfile.read_text()
        assert "header" in content
        assert "footer" in content

    def test_appends_section_if_not_present(self, tmp_path: Path) -> None:
        """Should append section if markers not found."""
        from vibraphone.tools.stack_tools import _update_justfile_section

        justfile = tmp_path / "Justfile"
        justfile.write_text("existing content")
        section = "# === COMPONENT RECIPES ===\nnew\n# === END COMPONENT RECIPES ==="
        _update_justfile_section(justfile, section)
        content = justfile.read_text()
        assert "existing content" in content
        assert "# === COMPONENT RECIPES ===" in content

    def test_returns_true_when_modified(self, tmp_path: Path) -> None:
        """Should return True when file was modified."""
        from vibraphone.tools.stack_tools import _update_justfile_section

        justfile = tmp_path / "Justfile"
        section = "# === COMPONENT RECIPES ===\nnew\n# === END COMPONENT RECIPES ==="
        result = _update_justfile_section(justfile, section)
        assert result is True

    def test_returns_false_when_unchanged(self, tmp_path: Path) -> None:
        """Should return False when content unchanged."""
        from vibraphone.tools.stack_tools import _update_justfile_section

        justfile = tmp_path / "Justfile"
        section = "# === COMPONENT RECIPES ===\nnew\n# === END COMPONENT RECIPES ==="
        _update_justfile_section(justfile, section)
        # Second call with same content
        result = _update_justfile_section(justfile, section)
        assert result is False


class TestConfigureStackPreview:
    """Tests for configure_stack preview mode."""

    @pytest.mark.asyncio
    async def test_preview_returns_component_section(self, tmp_path: Path, mocker: Any) -> None:
        """Preview should return component section without writing."""
        mocker.patch("vibraphone.tools.stack_tools.get_project_root", return_value=tmp_path)
        mocker.patch("vibraphone.tools.stack_tools.find_config_file", return_value=None)

        from vibraphone.tools.stack_tools import configure_stack

        components = {"backend": {"language": "python"}}
        result = await configure_stack.fn(components, preview=True)

        assert result["status"] == "preview"
        assert "component_section" in result
        assert "# === COMPONENT RECIPES ===" in result["component_section"]

    @pytest.mark.asyncio
    async def test_preview_returns_vibraphone_yaml(self, tmp_path: Path, mocker: Any) -> None:
        """Preview should return vibraphone.yaml content."""
        mocker.patch("vibraphone.tools.stack_tools.get_project_root", return_value=tmp_path)
        mocker.patch("vibraphone.tools.stack_tools.find_config_file", return_value=None)

        from vibraphone.tools.stack_tools import configure_stack

        components = {"backend": {"language": "python"}}
        result = await configure_stack.fn(components, preview=True)

        assert "vibraphone_yaml" in result
        assert "backend" in result["vibraphone_yaml"]

    @pytest.mark.asyncio
    async def test_preview_does_not_write_files(self, tmp_path: Path, mocker: Any) -> None:
        """Preview should not write any files."""
        justfile = tmp_path / "Justfile"
        justfile.write_text("existing")

        mocker.patch("vibraphone.tools.stack_tools.get_project_root", return_value=tmp_path)
        mocker.patch("vibraphone.tools.stack_tools.find_config_file", return_value=None)

        from vibraphone.tools.stack_tools import configure_stack

        components = {"backend": {"language": "python"}}
        await configure_stack.fn(components, preview=True)

        # Justfile should be unchanged
        assert justfile.read_text() == "existing"


class TestConfigureStackExecution:
    """Tests for configure_stack execution (preview=False)."""

    @pytest.mark.asyncio
    async def test_writes_justfile_section(self, tmp_path: Path, mocker: Any) -> None:
        """Should update Justfile with component section."""
        justfile = tmp_path / "Justfile"

        mocker.patch("vibraphone.tools.stack_tools.get_project_root", return_value=tmp_path)
        mocker.patch("vibraphone.tools.stack_tools.find_config_file", return_value=None)
        mocker.patch("vibraphone.tools.stack_tools.clear_config_cache")

        from vibraphone.tools.stack_tools import configure_stack

        components = {"backend": {"language": "python"}}
        result = await configure_stack.fn(components, preview=False)

        assert result["status"] == "configured"
        assert justfile.exists()
        content = justfile.read_text()
        assert "test-backend" in content

    @pytest.mark.asyncio
    async def test_writes_vibraphone_yaml(self, tmp_path: Path, mocker: Any) -> None:
        """Should write vibraphone.yaml with components."""
        yaml_path = tmp_path / "vibraphone.yaml"

        mocker.patch("vibraphone.tools.stack_tools.get_project_root", return_value=tmp_path)
        mocker.patch("vibraphone.tools.stack_tools.find_config_file", return_value=yaml_path)
        mocker.patch("vibraphone.tools.stack_tools.clear_config_cache")

        from vibraphone.tools.stack_tools import configure_stack

        components = {"backend": {"language": "python"}}
        await configure_stack.fn(components, preview=False)

        assert yaml_path.exists()
        content = yaml_path.read_text()
        assert "backend" in content
        assert "python" in content

    @pytest.mark.asyncio
    async def test_uses_stack_defaults_for_language(self, tmp_path: Path, mocker: Any) -> None:
        """Should use STACK_DEFAULTS commands for configured language."""
        from vibraphone import config as config_module
        from vibraphone.tools.stack_tools import configure_stack

        mocker.patch("vibraphone.tools.stack_tools.get_project_root", return_value=tmp_path)
        mocker.patch("vibraphone.tools.stack_tools.find_config_file", return_value=None)
        mocker.patch("vibraphone.tools.stack_tools.clear_config_cache")

        # Get expected defaults for python
        python_defaults = config_module.STACK_DEFAULTS.get("python", {})

        components = {"backend": {"language": "python"}}
        result = await configure_stack.fn(components, preview=True)

        # Check that defaults are used in YAML output
        assert python_defaults["test_command"] in result["vibraphone_yaml"]

    @pytest.mark.asyncio
    async def test_clears_config_cache(self, tmp_path: Path, mocker: Any) -> None:
        """Should clear config cache after writing."""
        mock_clear = mocker.patch("vibraphone.tools.stack_tools.clear_config_cache")

        mocker.patch("vibraphone.tools.stack_tools.get_project_root", return_value=tmp_path)
        mocker.patch("vibraphone.tools.stack_tools.find_config_file", return_value=None)

        from vibraphone.tools.stack_tools import configure_stack

        components = {"backend": {"language": "python"}}
        await configure_stack.fn(components, preview=False)

        mock_clear.assert_called_once()


class TestConfigureStackStitch:
    """Tests for Stitch integration."""

    @pytest.mark.asyncio
    async def test_enables_stitch_in_yaml(self, tmp_path: Path, mocker: Any) -> None:
        """Should set stitch.enabled=True in vibraphone.yaml."""
        yaml_path = tmp_path / "vibraphone.yaml"

        mocker.patch("vibraphone.tools.stack_tools.get_project_root", return_value=tmp_path)
        mocker.patch("vibraphone.tools.stack_tools.find_config_file", return_value=yaml_path)
        mocker.patch("vibraphone.tools.stack_tools.clear_config_cache")

        from vibraphone.tools.stack_tools import configure_stack

        components = {"backend": {"language": "python"}}
        await configure_stack.fn(components, preview=False, stitch_project_id="my-project-123")

        content = yaml_path.read_text()
        assert "stitch:" in content
        assert "enabled: true" in content

    @pytest.mark.asyncio
    async def test_writes_stitch_project_id_to_env(self, tmp_path: Path, mocker: Any) -> None:
        """Should write STITCH_PROJECT_ID to .env."""
        env_path = tmp_path / ".env"

        mocker.patch("vibraphone.tools.stack_tools.get_project_root", return_value=tmp_path)
        mocker.patch("vibraphone.tools.stack_tools.find_config_file", return_value=None)
        mocker.patch("vibraphone.tools.stack_tools.clear_config_cache")

        from vibraphone.tools.stack_tools import configure_stack

        components = {"backend": {"language": "python"}}
        await configure_stack.fn(components, preview=False, stitch_project_id="my-project-123")

        assert env_path.exists()
        content = env_path.read_text()
        assert "STITCH_PROJECT_ID=my-project-123" in content

    @pytest.mark.asyncio
    async def test_updates_mcp_config(self, tmp_path: Path, mocker: Any) -> None:
        """Should update .mcp/config.json with stitch entry."""
        mcp_dir = tmp_path / ".mcp"
        mcp_config = mcp_dir / "config.json"

        mocker.patch("vibraphone.tools.stack_tools.get_project_root", return_value=tmp_path)
        mocker.patch("vibraphone.tools.stack_tools.find_config_file", return_value=None)
        mocker.patch("vibraphone.tools.stack_tools.clear_config_cache")

        from vibraphone.tools.stack_tools import configure_stack

        components = {"backend": {"language": "python"}}
        await configure_stack.fn(components, preview=False, stitch_project_id="my-project-123")

        assert mcp_config.exists()
        import json

        content = json.loads(mcp_config.read_text())
        assert "stitch" in content.get("mcpServers", {})


class TestConfigureStackDefensiveParsing:
    """Tests for configure_stack defensive parsing."""

    @pytest.mark.asyncio
    async def test_components_as_json_string_parses_successfully(self, tmp_path: Path, mocker: Any) -> None:
        """Passing components as JSON string parses successfully and proceeds."""
        mocker.patch("vibraphone.tools.stack_tools.get_project_root", return_value=tmp_path)
        mocker.patch("vibraphone.tools.stack_tools.find_config_file", return_value=None)

        from vibraphone.tools.stack_tools import configure_stack

        components_str = '{"backend": {"language": "python"}}'
        result = await configure_stack.fn(components_str, preview=True)

        # Should NOT return an error - JSON string parses successfully
        assert result["status"] == "preview"
        assert "component_section" in result

    @pytest.mark.asyncio
    async def test_components_as_invalid_json_returns_error(self) -> None:
        """Passing components as invalid JSON string returns ParameterParseError."""
        from vibraphone.tools.stack_tools import configure_stack

        result = await configure_stack.fn('{"unclosed', preview=True)

        assert result["status"] == "error"
        assert result["error_type"] == "ParameterParseError"
        assert "Failed to parse" in result["message"]

    @pytest.mark.asyncio
    async def test_components_as_dict_works_normally(self, tmp_path: Path, mocker: Any) -> None:
        """Passing components as dict should work normally."""
        mocker.patch("vibraphone.tools.stack_tools.get_project_root", return_value=tmp_path)
        mocker.patch("vibraphone.tools.stack_tools.find_config_file", return_value=None)

        from vibraphone.tools.stack_tools import configure_stack

        components = {"backend": {"language": "python"}}
        result = await configure_stack.fn(components, preview=True)

        # Should NOT return an error
        assert result["status"] == "preview"
        assert "component_section" in result


class TestPhase06SuccessCriteria:
    """Tests for Phase 6 ROADMAP success criteria."""

    @pytest.mark.asyncio
    async def test_STACK_01_configure_stack_regenerates_recipes(self, tmp_path: Path, mocker: Any) -> None:
        """STACK-01: Agent can call configure_stack and Justfile recipes regenerate with new stack config."""
        justfile = tmp_path / "Justfile"
        justfile.write_text("# Existing content\n")

        mocker.patch("vibraphone.tools.stack_tools.get_project_root", return_value=tmp_path)
        mocker.patch("vibraphone.tools.stack_tools.find_config_file", return_value=None)
        mocker.patch("vibraphone.tools.stack_tools.clear_config_cache")

        from vibraphone.tools.stack_tools import configure_stack

        # Configure with two components
        components = {
            "backend": {"language": "python", "root": "./src"},
            "frontend": {"language": "typescript", "root": "./web"},
        }
        result = await configure_stack.fn(components, preview=False)

        # STACK-01 verification:
        # 1. Status is configured
        assert result["status"] == "configured"

        # 2. Justfile contains component recipes
        justfile_content = justfile.read_text()
        assert "test-backend" in justfile_content
        assert "test-frontend" in justfile_content
        assert "lint-backend" in justfile_content
        assert "format-frontend" in justfile_content

        # 3. Aggregate recipes depend on component recipes
        assert "test *ARGS: test-backend test-frontend" in justfile_content

        # 4. Existing content preserved
        assert "# Existing content" in justfile_content
