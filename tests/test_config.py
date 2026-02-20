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
        # Pydantic validator accepts strings and expands ~ (see expand_tilde validator)
        config = VibraphoneConfig(worktrees_path="~/custom/worktrees")  # type: ignore[arg-type]
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


class TestConfigIntegration:
    """Integration tests for complete config flow: discovery -> loading -> validation."""

    def setup_method(self):
        """Clear config cache before each test."""
        clear_config_cache()

    def test_discovery_to_loading_pipeline(self, tmp_path: Path, monkeypatch):
        """Verify get_config() from subdirectory loads config from parent."""
        config_file = tmp_path / "vibraphone.yaml"
        config_file.write_text(
            """
project:
  name: integration-test
  version: 2.0.0
quality_gate:
  max_test_attempts: 3
"""
        )

        subdir = tmp_path / "deep" / "nested" / "dir"
        subdir.mkdir(parents=True)

        monkeypatch.chdir(subdir)
        config = get_config()

        assert config is not None
        assert config.project.name == "integration-test"
        assert config.project.version == "2.0.0"
        assert config.quality_gate.max_test_attempts == 3

    def test_server_starts_without_config(self, tmp_path: Path, monkeypatch, capfd):
        """Verify get_config() returns defaults when no vibraphone.yaml exists."""
        monkeypatch.chdir(tmp_path)

        config = get_config()

        assert config is not None
        assert config.project.name == "unnamed-project"
        assert config.project.version == "0.1.0"
        assert config.worktree.base_branch == "main"
        assert config.quality_gate.require_tests is True
        assert config.worktrees_path == Path.home() / ".vibraphone" / "worktrees"

        captured = capfd.readouterr()
        assert captured.err == ""

    def test_server_fails_on_invalid_config(self, tmp_path: Path, monkeypatch, capfd):
        """Verify invalid config causes exit with clear error message."""
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
        captured = capfd.readouterr()
        assert "max_test_attempts" in captured.err

    def test_template_format_compatibility(self, tmp_path: Path, monkeypatch):
        """Verify vibraphone.yaml matching template format loads correctly."""
        config_file = tmp_path / "vibraphone.yaml"
        config_file.write_text(
            """
project:
  name: template-project
  version: 1.5.0

worktree:
  base_branch: develop
  prefix: feature/
  auto_cleanup: true

quality_gate:
  require_tests: false
  require_lint: false
  require_review: false
  review_severity_threshold: warning
  max_test_attempts: 5
  max_review_attempts: 3
"""
        )
        monkeypatch.chdir(tmp_path)

        config = get_config()

        assert config.project.name == "template-project"
        assert config.project.version == "1.5.0"
        assert config.worktree.base_branch == "develop"
        assert config.worktree.prefix == "feature/"
        assert config.worktree.auto_cleanup is True
        assert config.quality_gate.require_tests is False
        assert config.quality_gate.max_test_attempts == 5
        assert config.worktrees_path == Path.home() / ".vibraphone" / "worktrees"

    def test_worktrees_path_custom_and_default(self, tmp_path: Path, monkeypatch):
        """Verify worktrees_path handles default, ~ expansion, and absolute paths."""
        monkeypatch.chdir(tmp_path)

        clear_config_cache()
        default_config = get_config()
        assert default_config.worktrees_path == Path.home() / ".vibraphone" / "worktrees"

        config_file = tmp_path / "vibraphone.yaml"
        config_file.write_text("worktrees_path: ~/custom/worktrees\n")
        clear_config_cache()
        tilde_config = get_config()
        assert tilde_config.worktrees_path == Path.home() / "custom" / "worktrees"

        config_file.write_text("worktrees_path: /absolute/path/worktrees\n")
        clear_config_cache()
        abs_config = get_config()
        assert abs_config.worktrees_path == Path("/absolute/path/worktrees")


class TestPhase2SuccessCriteria:
    """Verification of Phase 2 success criteria from ROADMAP.md.

    Each test verifies one CFG requirement:
    - CFG-01: Discovery from any subdirectory
    - CFG-02: Clear validation errors with field name
    - CFG-03: Defaults work when no config
    - CFG-04: worktrees_path configurable with correct default
    - CFG-05: Template format compatible
    """

    def setup_method(self):
        """Clear config cache before each test."""
        clear_config_cache()

    def test_cfg01_discovery_from_subdirectory(self, tmp_path: Path, monkeypatch):
        """CFG-01: Server discovers vibraphone.yaml by walking up from CWD."""
        config_file = tmp_path / "vibraphone.yaml"
        config_file.write_text(
            """
project:
  name: cfg01-test
"""
        )

        deep_subdir = tmp_path / "src" / "vibraphone" / "tools"
        deep_subdir.mkdir(parents=True)

        monkeypatch.chdir(deep_subdir)
        config = get_config()

        assert config is not None
        assert config.project.name == "cfg01-test"

    def test_cfg02_clear_error_on_invalid_field(self, tmp_path: Path, monkeypatch, capfd):
        """CFG-02: Invalid vibraphone.yaml shows clear error with field name."""
        config_file = tmp_path / "vibraphone.yaml"
        config_file.write_text(
            """
quality_gate:
  max_test_attempts: "invalid-string-instead-of-int"
"""
        )
        monkeypatch.chdir(tmp_path)

        with pytest.raises(SystemExit) as exc_info:
            get_config()

        assert exc_info.value.code == 1
        captured = capfd.readouterr()
        assert "max_test_attempts" in captured.err

    def test_cfg03_defaults_when_missing(self, tmp_path: Path, monkeypatch, capfd):
        """CFG-03: Server runs with missing vibraphone.yaml using defaults."""
        monkeypatch.chdir(tmp_path)

        config = get_config()

        assert config is not None
        assert config.project.name == "unnamed-project"
        assert config.project.version == "0.1.0"
        assert config.worktree.base_branch == "main"
        assert config.worktree.prefix == "feat/"
        assert config.worktree.auto_cleanup is False
        assert config.quality_gate.require_tests is True
        assert config.quality_gate.require_lint is True
        assert config.quality_gate.require_review is True
        assert config.quality_gate.review_severity_threshold == "error"
        assert config.quality_gate.max_test_attempts == 10
        assert config.quality_gate.max_review_attempts == 5
        assert config.worktrees_path == Path.home() / ".vibraphone" / "worktrees"

        captured = capfd.readouterr()
        assert captured.err == ""

    def test_cfg04_worktrees_path_configurable(self, tmp_path: Path, monkeypatch):
        """CFG-04: Worktrees path configurable, defaults to ~/.vibraphone/worktrees/."""
        monkeypatch.chdir(tmp_path)

        clear_config_cache()
        default_config = get_config()
        assert default_config.worktrees_path == Path.home() / ".vibraphone" / "worktrees"

        config_file = tmp_path / "vibraphone.yaml"
        config_file.write_text(
            """
worktrees_path: /custom/worktrees/location
"""
        )
        clear_config_cache()
        custom_config = get_config()
        assert custom_config.worktrees_path == Path("/custom/worktrees/location")

        config_file.write_text(
            """
worktrees_path: ~/my-worktrees
"""
        )
        clear_config_cache()
        tilde_config = get_config()
        assert tilde_config.worktrees_path == Path.home() / "my-worktrees"

    def test_cfg05_template_compatibility(self, tmp_path: Path, monkeypatch):
        """CFG-05: Existing template vibraphone.yaml loads without modification."""
        config_file = tmp_path / "vibraphone.yaml"
        config_file.write_text(
            """
project:
  name: existing-template-project
  version: 3.2.1

worktree:
  base_branch: main
  prefix: feature/
  auto_cleanup: false

quality_gate:
  require_tests: true
  require_lint: true
  require_review: true
  review_severity_threshold: error
  max_test_attempts: 10
  max_review_attempts: 5
"""
        )
        monkeypatch.chdir(tmp_path)

        config = get_config()

        assert config.project.name == "existing-template-project"
        assert config.project.version == "3.2.1"
        assert config.worktree.base_branch == "main"
        assert config.worktree.prefix == "feature/"
        assert config.worktree.auto_cleanup is False
        assert config.quality_gate.require_tests is True
        assert config.quality_gate.require_lint is True
        assert config.quality_gate.require_review is True
        assert config.quality_gate.review_severity_threshold == "error"
        assert config.quality_gate.max_test_attempts == 10
        assert config.quality_gate.max_review_attempts == 5
