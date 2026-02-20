"""Unit tests for auto_detect module.

Tests the project metadata auto-detection utilities for init_project scaffolding.
"""

from pathlib import Path


class TestDetectLanguage:
    """Tests for detect_language function."""

    def test_detect_language_python(self, tmp_path: Path) -> None:
        """pyproject.toml present returns 'python'."""
        from vibraphone.utils.auto_detect import detect_language

        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        result = detect_language(tmp_path)

        assert result == "python"

    def test_detect_language_typescript(self, tmp_path: Path) -> None:
        """package.json present returns 'typescript'."""
        from vibraphone.utils.auto_detect import detect_language

        (tmp_path / "package.json").write_text('{"name": "test"}')

        result = detect_language(tmp_path)

        assert result == "typescript"

    def test_detect_language_go(self, tmp_path: Path) -> None:
        """go.mod present returns 'go'."""
        from vibraphone.utils.auto_detect import detect_language

        (tmp_path / "go.mod").write_text("module example.com/test\n")

        result = detect_language(tmp_path)

        assert result == "go"

    def test_detect_language_rust(self, tmp_path: Path) -> None:
        """Cargo.toml present returns 'rust'."""
        from vibraphone.utils.auto_detect import detect_language

        (tmp_path / "Cargo.toml").write_text("[package]\nname = 'test'\n")

        result = detect_language(tmp_path)

        assert result == "rust"

    def test_detect_language_defaults_to_python(self, tmp_path: Path) -> None:
        """No indicators returns 'python'."""
        from vibraphone.utils.auto_detect import detect_language

        result = detect_language(tmp_path)

        assert result == "python"

    def test_detect_language_setup_py(self, tmp_path: Path) -> None:
        """setup.py also indicates Python."""
        from vibraphone.utils.auto_detect import detect_language

        (tmp_path / "setup.py").write_text("from setuptools import setup\n")

        result = detect_language(tmp_path)

        assert result == "python"

    def test_detect_language_ruby(self, tmp_path: Path) -> None:
        """Gemfile indicates Ruby."""
        from vibraphone.utils.auto_detect import detect_language

        (tmp_path / "Gemfile").write_text('source "https://rubygems.org"\n')

        result = detect_language(tmp_path)

        assert result == "ruby"

    def test_detect_language_java_gradle(self, tmp_path: Path) -> None:
        """build.gradle indicates Java."""
        from vibraphone.utils.auto_detect import detect_language

        (tmp_path / "build.gradle").write_text("plugins { id('java') }\n")

        result = detect_language(tmp_path)

        assert result == "java"


class TestDetectGitRemote:
    """Tests for detect_git_remote function."""

    def test_detect_git_remote_returns_url(self, tmp_path: Path) -> None:
        """.git/config with url returns url."""
        from vibraphone.utils.auto_detect import detect_git_remote

        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        config = git_dir / "config"
        config.write_text("""
[core]
    repositoryformatversion = 0
[remote "origin"]
    url = https://github.com/user/repo.git
    fetch = +refs/heads/*:refs/remotes/origin/*
""")

        result = detect_git_remote(tmp_path)

        assert result == "https://github.com/user/repo.git"

    def test_detect_git_remote_returns_none_no_git(self, tmp_path: Path) -> None:
        """No .git returns None."""
        from vibraphone.utils.auto_detect import detect_git_remote

        result = detect_git_remote(tmp_path)

        assert result is None

    def test_detect_git_remote_returns_none_no_remote(self, tmp_path: Path) -> None:
        """.git/config without remote url returns None."""
        from vibraphone.utils.auto_detect import detect_git_remote

        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        config = git_dir / "config"
        config.write_text("[core]\n    repositoryformatversion = 0\n")

        result = detect_git_remote(tmp_path)

        assert result is None

    def test_detect_git_remote_ssh_url(self, tmp_path: Path) -> None:
        """SSH URLs are detected."""
        from vibraphone.utils.auto_detect import detect_git_remote

        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        config = git_dir / "config"
        config.write_text('[remote "origin"]\n    url = git@github.com:user/repo.git\n')

        result = detect_git_remote(tmp_path)

        assert result == "git@github.com:user/repo.git"


class TestDetectTestFramework:
    """Tests for detect_test_framework function."""

    def test_detect_test_framework_pytest(self, tmp_path: Path) -> None:
        """pyproject.toml with pytest returns 'pytest'."""
        from vibraphone.utils.auto_detect import detect_test_framework

        (tmp_path / "pyproject.toml").write_text("""
[project]
dependencies = ["pytest"]
""")

        result = detect_test_framework(tmp_path, "python")

        assert result == "pytest"

    def test_detect_test_framework_pytest_ini(self, tmp_path: Path) -> None:
        """pytest.ini returns 'pytest'."""
        from vibraphone.utils.auto_detect import detect_test_framework

        (tmp_path / "pytest.ini").write_text("[pytest]\n")

        result = detect_test_framework(tmp_path, "python")

        assert result == "pytest"

    def test_detect_test_framework_vitest(self, tmp_path: Path) -> None:
        """vitest.config.ts returns 'vitest'."""
        from vibraphone.utils.auto_detect import detect_test_framework

        (tmp_path / "vitest.config.ts").write_text("export default {}")

        result = detect_test_framework(tmp_path, "typescript")

        assert result == "vitest"

    def test_detect_test_framework_jest(self, tmp_path: Path) -> None:
        """jest.config.js returns 'jest'."""
        from vibraphone.utils.auto_detect import detect_test_framework

        (tmp_path / "jest.config.js").write_text("module.exports = {}")

        result = detect_test_framework(tmp_path, "typescript")

        assert result == "jest"

    def test_detect_test_framework_go_test(self, tmp_path: Path) -> None:
        """Go projects return 'go test'."""
        from vibraphone.utils.auto_detect import detect_test_framework

        result = detect_test_framework(tmp_path, "go")

        assert result == "go test"

    def test_detect_test_framework_cargo_test(self, tmp_path: Path) -> None:
        """Rust projects return 'cargo test'."""
        from vibraphone.utils.auto_detect import detect_test_framework

        result = detect_test_framework(tmp_path, "rust")

        assert result == "cargo test"

    def test_detect_test_framework_unknown(self, tmp_path: Path) -> None:
        """Unknown language/config returns 'unknown'."""
        from vibraphone.utils.auto_detect import detect_test_framework

        result = detect_test_framework(tmp_path, "python")

        assert result == "unknown"


class TestDetectCIPlatform:
    """Tests for detect_ci_platform function."""

    def test_detect_ci_platform_github_actions(self, tmp_path: Path) -> None:
        """.github/workflows returns 'github-actions'."""
        from vibraphone.utils.auto_detect import detect_ci_platform

        workflows = tmp_path / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "ci.yml").write_text("name: CI\n")

        result = detect_ci_platform(tmp_path)

        assert result == "github-actions"

    def test_detect_ci_platform_gitlab(self, tmp_path: Path) -> None:
        """.gitlab-ci.yml returns 'gitlab-ci'."""
        from vibraphone.utils.auto_detect import detect_ci_platform

        (tmp_path / ".gitlab-ci.yml").write_text("stages:\n  - test\n")

        result = detect_ci_platform(tmp_path)

        assert result == "gitlab-ci"

    def test_detect_ci_platform_circleci(self, tmp_path: Path) -> None:
        """.circleci returns 'circleci'."""
        from vibraphone.utils.auto_detect import detect_ci_platform

        circleci = tmp_path / ".circleci"
        circleci.mkdir()
        (circleci / "config.yml").write_text("version: 2.1\n")

        result = detect_ci_platform(tmp_path)

        assert result == "circleci"

    def test_detect_ci_platform_none(self, tmp_path: Path) -> None:
        """No CI config returns None."""
        from vibraphone.utils.auto_detect import detect_ci_platform

        result = detect_ci_platform(tmp_path)

        assert result is None


class TestDetectProjectMetadata:
    """Tests for detect_project_metadata function."""

    def test_detect_project_metadata_combines_all(self, tmp_path: Path) -> None:
        """Returns dict with all keys."""
        from vibraphone.utils.auto_detect import detect_project_metadata

        # Set up a Python project with git and CI
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
        (tmp_path / "pytest.ini").write_text("[pytest]\n")

        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        config = git_dir / "config"
        config.write_text('[remote "origin"]\n    url = https://github.com/user/repo.git\n')

        workflows = tmp_path / ".github" / "workflows"
        workflows.mkdir(parents=True)

        result = detect_project_metadata(tmp_path)

        assert result["project_name"] == tmp_path.name
        assert result["git_remote"] == "https://github.com/user/repo.git"
        assert result["language"] == "python"
        assert result["test_framework"] == "pytest"
        assert result["ci_platform"] == "github-actions"
        assert result["worktrees_path"] == "~/.vibraphone/worktrees"

    def test_detect_project_metadata_project_name_from_dir(self, tmp_path: Path) -> None:
        """Project name comes from directory name."""
        from vibraphone.utils.auto_detect import detect_project_metadata

        result = detect_project_metadata(tmp_path)

        assert result["project_name"] == tmp_path.name

    def test_detect_project_metadata_defaults(self, tmp_path: Path) -> None:
        """Default values when nothing detected."""
        from vibraphone.utils.auto_detect import detect_project_metadata

        result = detect_project_metadata(tmp_path)

        assert result["language"] == "python"  # Default
        assert result["git_remote"] is None
        assert result["ci_platform"] is None
        assert result["worktrees_path"] == "~/.vibraphone/worktrees"


class TestPriorityOrder:
    """Tests for language detection priority."""

    def test_pyproject_takes_priority_over_requirements(self, tmp_path: Path) -> None:
        """pyproject.toml takes priority over requirements.txt."""
        from vibraphone.utils.auto_detect import detect_language

        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
        (tmp_path / "requirements.txt").write_text("requests\n")

        result = detect_language(tmp_path)

        assert result == "python"

    def test_pyproject_before_setup_py(self, tmp_path: Path) -> None:
        """pyproject.toml is checked before setup.py."""
        from vibraphone.utils.auto_detect import detect_language

        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n')
        (tmp_path / "setup.py").write_text("from setuptools import setup\n")

        result = detect_language(tmp_path)

        assert result == "python"
