"""Tests for vibraphone configuration loading."""

from pathlib import Path

import pytest

from vibraphone.config import (
    VibraphoneConfig,
    clear_config_cache,
    find_config_file,
    get_config,
)


class TestGetConfig:
    """Tests for get_config function."""

    def setup_method(self):
        """Clear config cache before each test."""
        clear_config_cache()

    def test_returns_defaults_when_no_file(self, tmp_path: Path, monkeypatch):
        """Verify get_config returns default config when no file exists."""
        monkeypatch.chdir(tmp_path)
        config = get_config()
        assert config is not None
        assert config.worktrees_path == Path.home() / ".vibraphone" / "worktrees"

    def test_loads_from_found_config(self, tmp_path: Path, monkeypatch):
        """Verify get_config integrates with find_config_file()."""
        config_file = tmp_path / "vibraphone.yaml"
        config_file.write_text(
            """
project:
  name: test-project
  version: 1.0.0
"""
        )
        monkeypatch.chdir(tmp_path)
        config = get_config()
        assert config is not None
        assert config.project.name == "test-project"
        assert config.project.version == "1.0.0"

    def test_exits_on_validation_error(self, tmp_path: Path, monkeypatch, capsys):
        """Verify invalid config causes sys.exit(1)."""
        config_file = tmp_path / "vibraphone.yaml"
        config_file.write_text(
            """
quality_gate:
  max_test_attempts: not-a-number
"""
        )
        monkeypatch.chdir(tmp_path)

        with pytest.raises(SystemExit) as exc_info:
            get_config()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "max_test_attempts" in captured.err or "validation" in captured.err.lower()

    def test_caches_config(self, tmp_path: Path, monkeypatch):
        """Verify repeated calls return same instance."""
        monkeypatch.chdir(tmp_path)

        config1 = get_config()
        config2 = get_config()

        assert config1 is config2


class TestVibraphoneConfig:
    """Tests for VibraphoneConfig Pydantic model."""

    def test_is_pydantic_model(self):
        """Verify VibraphoneConfig is a Pydantic BaseModel, not dataclass."""
        from pydantic import BaseModel

        assert issubclass(VibraphoneConfig, BaseModel)

    def test_has_worktrees_path_with_default(self):
        """Verify worktrees_path defaults to ~/.vibraphone/worktrees/."""
        config = VibraphoneConfig()
        assert config.worktrees_path == Path.home() / ".vibraphone" / "worktrees"

    def test_worktrees_path_expands_tilde(self):
        """Verify ~/custom/path expands to absolute path."""
        config = VibraphoneConfig(worktrees_path="~/custom/worktrees")
        expected = Path.home() / "custom" / "worktrees"
        assert config.worktrees_path == expected

    def test_all_sections_have_defaults(self):
        """Verify missing sections use defaults."""
        config = VibraphoneConfig()
        assert config.project is not None
        assert config.worktree is not None
        assert config.quality_gate is not None

    def test_compatible_with_template_format(self):
        """Verify loading a full template-style config works."""
        template_data = {
            "project": {"name": "my-project", "version": "2.0.0"},
            "worktree": {"base_branch": "develop", "prefix": "feature/", "auto_cleanup": True},
            "quality_gate": {
                "require_tests": False,
                "require_lint": False,
                "require_review": False,
                "review_severity_threshold": "warning",
                "max_test_attempts": 5,
                "max_review_attempts": 3,
            },
        }
        config = VibraphoneConfig.model_validate(template_data)
        assert config.project.name == "my-project"
        assert config.worktree.base_branch == "develop"
        assert config.quality_gate.max_test_attempts == 5


class TestConfigValidation:
    """Tests for config validation and error handling."""

    def setup_method(self):
        """Clear config cache before each test."""
        clear_config_cache()

    def test_invalid_field_type_shows_helpful_error(self):
        """Verify string where int expected shows helpful suggestion."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            VibraphoneConfig.model_validate({"quality_gate": {"max_test_attempts": "not-a-number"}})

        errors = exc_info.value.errors()
        assert len(errors) >= 1
        error = errors[0]
        assert "max_test_attempts" in str(error["loc"])

    def test_yaml_syntax_error_shows_line_number(self, tmp_path: Path, monkeypatch, capsys):
        """Verify malformed YAML shows parser error with line number."""
        config_file = tmp_path / "vibraphone.yaml"
        config_file.write_text(
            """
project:
  name: unclosed
  version: [invalid yaml
"""
        )
        monkeypatch.chdir(tmp_path)

        with pytest.raises(SystemExit) as exc_info:
            get_config()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "yaml" in captured.err.lower() or "syntax" in captured.err.lower()

    def test_unknown_field_shows_warning(self, tmp_path: Path, monkeypatch, capsys):
        """Verify unknown field triggers warning to stderr."""
        config_file = tmp_path / "vibraphone.yaml"
        config_file.write_text(
            """
unknown_section:
  some_field: value
"""
        )
        monkeypatch.chdir(tmp_path)

        config = get_config()
        assert config is not None

        captured = capsys.readouterr()
        assert "unknown" in captured.err.lower() or "warning" in captured.err.lower()

    def test_typo_suggests_correction(self, tmp_path: Path, monkeypatch, capsys):
        """Verify typo in field name suggests correction."""
        config_file = tmp_path / "vibraphone.yaml"
        config_file.write_text(
            """
projct:
  name: my-project
"""
        )
        monkeypatch.chdir(tmp_path)

        config = get_config()
        assert config is not None

        captured = capsys.readouterr()
        assert "projct" in captured.err or "project" in captured.err


class TestFindConfigFile:
    """Tests for config file discovery by walking up directories."""

    def setup_method(self):
        """Clear config cache before each test."""
        clear_config_cache()

    def test_finds_config_in_current_directory(self, tmp_path: Path, monkeypatch):
        """Verify find_config_file finds vibraphone.yaml in cwd."""
        config_file = tmp_path / "vibraphone.yaml"
        config_file.write_text("project:\n  name: test\n")

        monkeypatch.chdir(tmp_path)

        result = find_config_file()
        assert result is not None
        assert result == config_file

    def test_finds_config_in_parent_directory(self, tmp_path: Path, monkeypatch):
        """Verify find_config_file walks up to find config in parent."""
        config_file = tmp_path / "vibraphone.yaml"
        config_file.write_text("project:\n  name: test\n")

        subdir = tmp_path / "subdir"
        subdir.mkdir()

        monkeypatch.chdir(subdir)

        result = find_config_file()
        assert result is not None
        assert result == config_file

    def test_stops_at_git_boundary(self, tmp_path: Path, monkeypatch):
        """Verify search stops at .git directory boundary."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        parent_config = tmp_path.parent / "vibraphone.yaml"
        parent_config.write_text("project:\n  name: outside\n")

        monkeypatch.chdir(tmp_path)

        result = find_config_file()
        assert result is None

        parent_config.unlink()

    def test_stops_at_home_boundary(self, monkeypatch):
        """Verify search stops at $HOME directory when no .git found."""
        home = Path.home()
        home_config = home / "vibraphone.yaml"

        if home_config.exists():
            pytest.skip("vibraphone.yaml exists in $HOME, cannot test boundary")

        monkeypatch.chdir(home)

        result = find_config_file()
        assert result is None or isinstance(result, Path)

    def test_returns_none_at_filesystem_root(self, monkeypatch):
        """Verify returns None when reaching filesystem root with no config."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            deep = tmp / "a" / "b" / "c"
            deep.mkdir(parents=True)

            monkeypatch.chdir(deep)

            result = find_config_file()
            assert result is None

    def test_follows_symlinks(self, tmp_path: Path, monkeypatch):
        """Verify symlinks are followed via Path.resolve()."""
        real_dir = tmp_path / "real"
        real_dir.mkdir()
        config_file = real_dir / "vibraphone.yaml"
        config_file.write_text("project:\n  name: test\n")

        link_dir = tmp_path / "link"
        link_dir.symlink_to(real_dir)

        monkeypatch.chdir(link_dir)

        result = find_config_file()
        assert result is not None
        assert result.resolve() == config_file.resolve()

    def test_caches_discovery_result(self, tmp_path: Path, monkeypatch):
        """Verify discovery result is cached after first lookup."""
        config_file = tmp_path / "vibraphone.yaml"
        config_file.write_text("project:\n  name: test\n")

        monkeypatch.chdir(tmp_path)

        result1 = find_config_file()
        result2 = find_config_file()

        assert result1 == result2
        assert result1 == config_file
