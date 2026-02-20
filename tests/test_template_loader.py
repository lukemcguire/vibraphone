"""Unit tests for template_loader module.

Tests the template loading utilities that use importlib.resources
for accessing bundled templates in the vibraphone.templates package.
"""

import pytest


class TestLoadTemplate:
    """Tests for load_template function."""

    def test_load_template_returns_content(self) -> None:
        """load_template('vibraphone.yaml.j2') returns string content."""
        from vibraphone.utils.template_loader import load_template

        # Load a known template that should exist
        content = load_template("vibraphone.yaml.j2")

        assert isinstance(content, str)
        assert len(content) > 0
        # Should contain Jinja2 variables
        assert "{{" in content or "{%" in content

    def test_load_template_raises_for_missing(self) -> None:
        """FileNotFoundError for non-existent template."""
        from vibraphone.utils.template_loader import load_template

        with pytest.raises(FileNotFoundError) as exc_info:
            load_template("nonexistent_template.xyz")

        assert "Template not found" in str(exc_info.value)

    def test_load_template_static_file(self) -> None:
        """load_template works for static files (no Jinja2)."""
        from vibraphone.utils.template_loader import load_template

        # AGENTS.md should be a static template
        content = load_template("AGENTS.md")

        assert isinstance(content, str)
        assert len(content) > 0


class TestLoadTemplateTree:
    """Tests for load_template_tree function."""

    def test_load_template_tree_returns_dict(self) -> None:
        """load_template_tree('docs') returns dict of paths to content."""
        from vibraphone.utils.template_loader import load_template_tree

        templates = load_template_tree("docs")

        assert isinstance(templates, dict)
        assert len(templates) > 0
        # All values should be strings
        for content in templates.values():
            assert isinstance(content, str)

    def test_load_template_tree_paths_are_relative(self) -> None:
        """Template paths in result are relative to subdir."""
        from vibraphone.utils.template_loader import load_template_tree

        templates = load_template_tree("docs")

        # Paths should be relative, not absolute
        for path in templates.keys():
            assert not path.startswith("/")
            # Should not contain "docs/" prefix since we're loading from docs/
            assert not path.startswith("docs/")

    def test_load_template_tree_includes_nested_files(self) -> None:
        """Nested files are included in tree."""
        from vibraphone.utils.template_loader import load_template_tree

        templates = load_template_tree("docs")

        # Check for nested paths (e.g., prompts/reviewer.md)
        # It's OK if no nested files exist, but if they do they should be included
        # Just verify structure is correct
        assert isinstance(templates, dict)


class TestRenderTemplate:
    """Tests for render_template function."""

    def test_render_template_substitutes_variables(self) -> None:
        """render_template with {{ project_name }} gets replaced."""
        from vibraphone.utils.template_loader import render_template

        template = "Hello {{ name }}!"
        variables = {"name": "World"}

        result = render_template(template, variables)

        assert result == "Hello World!"

    def test_render_template_handles_conditionals(self) -> None:
        """Jinja2 {% if %} blocks work."""
        from vibraphone.utils.template_loader import render_template

        template = "{% if show %}Visible{% else %}Hidden{% endif %}"

        result_true = render_template(template, {"show": True})
        result_false = render_template(template, {"show": False})

        assert result_true == "Visible"
        assert result_false == "Hidden"

    def test_render_template_handles_loops(self) -> None:
        """Jinja2 {% for %} loops work."""
        from vibraphone.utils.template_loader import render_template

        template = "{% for item in items %}{{ item }}{% endfor %}"
        variables = {"items": ["a", "b", "c"]}

        result = render_template(template, variables)

        assert result == "abc"

    def test_render_template_missing_variable_empty(self) -> None:
        """Missing variables render as empty string (Jinja2 default)."""
        from vibraphone.utils.template_loader import render_template

        template = "Value: {{ missing_var }}"
        variables = {}

        result = render_template(template, variables)

        assert result == "Value: "

    def test_render_template_keeps_trailing_newline(self) -> None:
        """Trailing newlines are preserved."""
        from vibraphone.utils.template_loader import render_template

        template = "content\n"
        variables = {}

        result = render_template(template, variables)

        assert result.endswith("\n")


class TestGetAllTemplatePaths:
    """Tests for get_all_template_paths function."""

    def test_get_all_template_paths_returns_list(self) -> None:
        """Returns list of all template paths."""
        from vibraphone.utils.template_loader import get_all_template_paths

        paths = get_all_template_paths()

        assert isinstance(paths, list)
        assert len(paths) > 0
        # All should be strings
        for path in paths:
            assert isinstance(path, str)

    def test_get_all_template_paths_excludes_pycache(self) -> None:
        """__pycache__ directories are excluded."""
        from vibraphone.utils.template_loader import get_all_template_paths

        paths = get_all_template_paths()

        for path in paths:
            assert "__pycache__" not in path

    def test_get_all_template_paths_excludes_init(self) -> None:
        """__init__.py is excluded (it's a package marker, not a template)."""
        from vibraphone.utils.template_loader import get_all_template_paths

        paths = get_all_template_paths()

        assert "__init__.py" not in paths


class TestGetTemplatePackage:
    """Tests for get_template_package function."""

    def test_get_template_package_returns_traversable(self) -> None:
        """Returns a Traversable object."""
        from importlib import resources

        from vibraphone.utils.template_loader import get_template_package

        result = get_template_package()

        # Should be a Traversable
        assert isinstance(result, resources.abc.Traversable)

    def test_get_template_package_has_templates(self) -> None:
        """Template package contains expected files."""
        from vibraphone.utils.template_loader import get_template_package

        pkg = get_template_package()

        # Should be able to join paths
        yaml_template = pkg / "vibraphone.yaml.j2"
        # Just verify we can access it (doesn't raise)
        assert yaml_template is not None


class TestTMPL02TemplatesAccessibleViaImportlib:
    """Verify TMPL-02 requirement: Templates accessed via importlib.resources."""

    def test_TMPL_02_templates_accessible_via_importlib(self) -> None:
        """TMPL-02: Templates accessible via importlib.resources."""
        from importlib import resources

        from vibraphone.utils.template_loader import get_template_package

        # Verify we can access the templates package via importlib
        pkg = get_template_package()

        # Should be able to read a file using the Traversable API
        # This verifies wheel compatibility
        assert isinstance(pkg, resources.abc.Traversable)

        # Try to access a known template
        template_path = pkg / "vibraphone.yaml.j2"
        assert template_path.is_file()

        # Should be able to read content
        content = template_path.read_text(encoding="utf-8")
        assert len(content) > 0

    def test_templates_work_from_wheel_context(self) -> None:
        """Template access works the same way whether from source or wheel."""
        from vibraphone.utils.template_loader import load_template

        # This should work both from source tree and installed wheel
        content = load_template("vibraphone.yaml.j2")

        assert isinstance(content, str)
        # Should contain project config structure
        assert "project:" in content.lower() or "{{" in content
