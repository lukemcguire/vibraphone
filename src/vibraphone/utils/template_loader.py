"""Template loading utilities using importlib.resources.

Templates are bundled in the vibraphone.templates package and accessed
via importlib.resources for compatibility with pip installed wheels.
"""

from __future__ import annotations

from importlib import resources
from typing import TYPE_CHECKING, Any

from jinja2 import Environment, select_autoescape

if TYPE_CHECKING:
    from collections.abc import Iterator


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


def _iter_files_recursive(traversable: resources.abc.Traversable) -> Iterator[resources.abc.Traversable]:
    """Recursively iterate over all files in a Traversable.

    Args:
        traversable: The directory to iterate over.

    Yields:
        Each file found in the tree.
    """
    for item in traversable.iterdir():
        if item.is_file():
            yield item
        elif item.is_dir():
            yield from _iter_files_recursive(item)


def load_template_tree(subdir: str) -> dict[str, str]:
    """Load all templates from a subdirectory.

    Args:
        subdir: Subdirectory within templates/ (e.g., "docs")

    Returns:
        Dict mapping relative path to content for each file in the tree.
    """
    template_files = get_template_package()
    target = template_files / subdir
    target_str = str(target)

    templates: dict[str, str] = {}
    for item in _iter_files_recursive(target):
        # Compute relative path by removing target prefix
        item_str = str(item)
        rel_path = item_str[len(target_str) + 1 :]  # +1 for the path separator
        templates[rel_path] = item.read_text(encoding="utf-8")

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
    template_files_str = str(template_files)
    paths: list[str] = []

    for item in _iter_files_recursive(template_files):
        item_str = str(item)
        if "__pycache__" not in item_str:
            # Compute relative path by removing template_files prefix
            rel_str = item_str[len(template_files_str) + 1 :]  # +1 for the path separator
            # Exclude __init__.py (package marker, not a template)
            if rel_str != "__init__.py":
                paths.append(rel_str)

    return paths
