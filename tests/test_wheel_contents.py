"""Wheel content verification tests.

Tests that the built wheel contains all required template files.
Uses build-and-extract approach per CONTEXT.md decision.
"""

import subprocess
import zipfile
from pathlib import Path
import tempfile
import pytest


class TestWheelTemplateContents:
    """Verify wheel contains all template files."""

    @pytest.fixture
    def built_wheel(self, tmp_path: Path) -> Path:
        """Build wheel and return path to wheel file."""
        # Build wheel using uv
        result = subprocess.run(
            ["uv", "build", "--wheel"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Build failed: {result.stderr}"

        # Find the wheel file
        dist_dir = Path(__file__).parent.parent / "dist"
        wheels = list(dist_dir.glob("*.whl"))
        assert len(wheels) == 1, f"Expected 1 wheel, found {len(wheels)}"
        return wheels[0]

    def test_wheel_contains_templates_directory(self, built_wheel: Path) -> None:
        """Wheel contains vibraphone/templates/ directory."""
        with zipfile.ZipFile(built_wheel, "r") as whl:
            names = whl.namelist()
            template_files = [n for n in names if "templates/" in n]
            assert len(template_files) > 0, "No templates found in wheel"

    def test_wheel_contains_vibraphone_yaml_template(self, built_wheel: Path) -> None:
        """Wheel contains vibraphone.yaml.j2 template."""
        with zipfile.ZipFile(built_wheel, "r") as whl:
            names = whl.namelist()
            assert any("vibraphone.yaml" in n for n in names), "vibraphone.yaml.j2 not found"

    def test_wheel_contains_agent_templates(self, built_wheel: Path) -> None:
        """Wheel contains AGENTS.md and CLAUDE.md templates."""
        with zipfile.ZipFile(built_wheel, "r") as whl:
            names = whl.namelist()
            assert any("AGENTS.md" in n for n in names), "AGENTS.md not found"
            assert any("CLAUDE.md" in n for n in names), "CLAUDE.md not found"

    def test_wheel_contains_docs_templates(self, built_wheel: Path) -> None:
        """Wheel contains docs/ templates (ARCHITECTURE.md, etc.)."""
        with zipfile.ZipFile(built_wheel, "r") as whl:
            names = whl.namelist()
            assert any("docs/ARCHITECTURE.md" in n for n in names), "docs/ARCHITECTURE.md not found"


class TestWheelInstallability:
    """Verify wheel can be installed and imported."""

    def test_template_loader_finds_templates(self) -> None:
        """Template loader can find templates after installation."""
        from vibraphone.utils.template_loader import get_all_template_paths

        paths = get_all_template_paths()
        assert len(paths) > 0, "No template paths found"

        # Check for expected templates
        path_strs = [str(p) for p in paths]
        assert any("vibraphone.yaml" in p for p in path_strs), "vibraphone.yaml.j2 not in paths"

    def test_template_loader_loads_content(self) -> None:
        """Template loader can load template content."""
        from vibraphone.utils.template_loader import load_template

        content = load_template("vibraphone.yaml.j2")
        assert "worktrees_path" in content, "vibraphone.yaml.j2 missing expected content"

    def test_template_loader_loads_tree(self) -> None:
        """Template loader can load tree of templates."""
        from vibraphone.utils.template_loader import load_template_tree

        docs = load_template_tree("docs")
        assert len(docs) > 0, "No docs templates found"
        assert any("ARCHITECTURE" in k for k in docs), "ARCHITECTURE.md not in docs tree"
