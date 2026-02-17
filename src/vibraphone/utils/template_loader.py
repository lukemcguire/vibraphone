"""Template loading utilities using importlib.resources.

Templates are bundled in the vibraphone.templates package and accessed
via importlib.resources for compatibility with pip installed wheels.
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import Any

from jinja2 import Environment, select_autoescape


def get_template_package() -> resources.abc.Traversable:
    """Get the vibraphone.templates package as a Traversable.

    Returns:
        Traversable representing the templates package root.
    """
    return resources.files("vibraphone.templates")


def load_template(template_name: str) -> str:
    """Load a template file from the vibraphone.templates package.

    Uses importlib.resources for compatibility with zip installs and wheels.

    Args:
        template_name: Relative path within templates/ (e.g., "vibraphone.yaml.j2")

    Returns:
        Template content as string.

    Raises:
        FileNotFoundError: If template doesn't exist.
    """
    template_files = get_template_package()
    template_path = template_files / template_name

    if not template_path.is_file():
        msg = f"Template not found: {template_name}"
        raise FileNotFoundError(msg)

    return template_path.read_text(encoding="utf-8")


def load_template_tree(subdir: str) -> dict[str, str]:
    """Load all templates from a subdirectory.

    Args:
        subdir: Subdirectory within templates/ (e.g., "docs")

    Returns:
        Dict mapping relative path to content for each file in the tree.
    """
    template_files = get_template_package()
    target = template_files / subdir

    templates: dict[str, str] = {}
    for item in target.rglob("*"):
        if item.is_file():
            rel_path = item.relative_to(target)
            templates[str(rel_path)] = item.read_text(encoding="utf-8")

    return templates


def render_template(template_content: str, variables: dict[str, Any]) -> str:
    """Render a Jinja2 template with the given variables.

    Args:
        template_content: Raw template string with Jinja2 syntax.
        variables: Dict of variable names to values.

    Returns:
        Rendered template string.
    """
    env = Environment(
        autoescape=select_autoescape(default=False),
        keep_trailing_newline=True,
    )
    template = env.from_string(template_content)
    return template.render(**variables)


def get_all_template_paths() -> list[str]:
    """Get list of all template file paths in the package.

    Returns:
        List of relative paths within templates/ directory.
    """
    template_files = get_template_package()
    paths: list[str] = []

    for item in template_files.rglob("*"):
        if item.is_file() and "__pycache__" not in str(item):
            # Get path relative to templates package
            rel = item.relative_to(template_files)
            rel_str = str(rel)
            # Exclude __init__.py (package marker, not a template)
            if rel_str != "__init__.py":
                paths.append(rel_str)

    return paths
