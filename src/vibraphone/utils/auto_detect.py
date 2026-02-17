"""Project metadata auto-detection for init_project scaffolding."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def detect_git_remote(project_root: Path) -> str | None:
    """Extract remote URL from git config.

    Args:
        project_root: Path to project root directory.

    Returns:
        Git remote URL or None if not found.
    """
    git_config = project_root / ".git" / "config"
    if not git_config.exists():
        return None

    content = git_config.read_text(encoding="utf-8")
    match = re.search(r'url\s*=\s*(.+)', content)
    if match:
        return match.group(1).strip()
    return None


def detect_language(project_root: Path) -> str:
    """Detect primary language from project files.

    Args:
        project_root: Path to project root directory.

    Returns:
        Detected language name, defaults to "python".
    """
    indicators = [
        ("pyproject.toml", "python"),
        ("setup.py", "python"),
        ("requirements.txt", "python"),
        ("package.json", "typescript"),
        ("Cargo.toml", "rust"),
        ("go.mod", "go"),
        ("Gemfile", "ruby"),
        ("build.gradle", "java"),
        ("pom.xml", "java"),
    ]
    for filename, language in indicators:
        if (project_root / filename).exists():
            return language
    return "python"  # Default


def detect_test_framework(project_root: Path, language: str) -> str:
    """Detect test framework from project structure.

    Args:
        project_root: Path to project root directory.
        language: Detected or specified language.

    Returns:
        Test framework name or "unknown".
    """
    if language == "python":
        if (project_root / "pyproject.toml").exists():
            content = (project_root / "pyproject.toml").read_text(encoding="utf-8")
            if "pytest" in content:
                return "pytest"
        if (project_root / "pytest.ini").exists():
            return "pytest"
    elif language == "typescript":
        if (project_root / "vitest.config.ts").exists():
            return "vitest"
        if (project_root / "jest.config.js").exists():
            return "jest"
    elif language == "go":
        return "go test"
    elif language == "rust":
        return "cargo test"
    return "unknown"


def detect_ci_platform(project_root: Path) -> str | None:
    """Detect CI platform from project structure.

    Args:
        project_root: Path to project root directory.

    Returns:
        CI platform name or None if not detected.
    """
    if (project_root / ".github" / "workflows").exists():
        return "github-actions"
    if (project_root / ".gitlab-ci.yml").exists():
        return "gitlab-ci"
    if (project_root / ".circleci").exists():
        return "circleci"
    return None


def detect_project_metadata(project_root: Path) -> dict[str, Any]:
    """Detect all project metadata from existing files.

    Args:
        project_root: Path to project root directory.

    Returns:
        Dict with detected values: project_name, git_remote, language,
        test_framework, ci_platform, worktrees_path.
    """
    language = detect_language(project_root)
    return {
        "project_name": project_root.name,
        "git_remote": detect_git_remote(project_root),
        "language": language,
        "test_framework": detect_test_framework(project_root, language),
        "ci_platform": detect_ci_platform(project_root),
        "worktrees_path": "~/.vibraphone/worktrees",
    }
