"""Configuration loading for vibraphone.

Config is loaded lazily on first access, not on server startup.
This allows the server to start without vibraphone.yaml present.
"""

import sys
from difflib import get_close_matches
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

# Default worktree path (CFG-04)
DEFAULT_WORKTREES_PATH = Path.home() / ".vibraphone" / "worktrees"

# Known top-level fields for typo detection
KNOWN_TOP_LEVEL_FIELDS = {
    "project",
    "components",
    "quality_gate",
    "worktree",
    "worktrees_path",
    "circuit_breakers",
    "review",
    "beads",
    "stitch",
}

# difflib cutoff for typo suggestions
TYPO_SUGGESTION_CUTOFF = 0.6

# Stack defaults for different languages (used by configure_stack tool)
STACK_DEFAULTS: dict[str, dict[str, str]] = {
    "python": {
        "test_command": "uv run pytest --tb=short",
        "lint_command": "uv run ruff check . && uv run ruff format --check .",
        "format_command": "uv run ruff check --fix . && uv run ruff format .",
    },
    "typescript": {
        "test_command": "npx vitest run",
        "lint_command": "npx eslint .",
        "format_command": "npx eslint --fix . && npx prettier --write .",
    },
    "go": {
        "test_command": "go test ./...",
        "lint_command": "golangci-lint run",
        "format_command": "gofmt -w .",
    },
    "rust": {
        "test_command": "cargo test",
        "lint_command": "cargo clippy -- -D warnings",
        "format_command": "cargo fmt",
    },
    "ruby": {
        "test_command": "bundle exec rspec",
        "lint_command": "bundle exec rubocop",
        "format_command": "bundle exec rubocop -a",
    },
    "java": {
        "test_command": "./gradlew test",
        "lint_command": "./gradlew checkstyleMain",
        "format_command": "./gradlew spotlessApply",
    },
}


class ProjectConfig(BaseModel):
    """Project identification."""

    name: str = "unnamed-project"
    version: str = "0.1.0"


class WorktreeConfig(BaseModel):
    """Worktree settings."""

    base_branch: str = "main"
    prefix: str = "feat/"
    auto_cleanup: bool = False


class CircuitBreakerToolConfig(BaseModel):
    """Circuit breaker settings for a single tool."""

    max_attempts: int | None = None  # None = no circuit breaker


class CircuitBreakersConfig(BaseModel):
    """Circuit breaker settings per tool."""

    tests: CircuitBreakerToolConfig = Field(default_factory=lambda: CircuitBreakerToolConfig(max_attempts=5))
    lint: CircuitBreakerToolConfig = Field(default_factory=lambda: CircuitBreakerToolConfig(max_attempts=None))
    review: CircuitBreakerToolConfig = Field(default_factory=lambda: CircuitBreakerToolConfig(max_attempts=3))


class QualityGateCommandsConfig(BaseModel):
    """Command overrides for quality gate tools."""

    test: str = "just test"
    lint: str = "just lint"
    format: str = "just format"
    check: str = "just check"


class QualityGateConfig(BaseModel):
    """Quality gate settings."""

    require_tests: bool = True
    require_lint: bool = True
    require_review: bool = True
    review_severity_threshold: str = "error"
    max_test_attempts: int = Field(default=10, ge=1)
    max_review_attempts: int = Field(default=5, ge=1)
    commands: QualityGateCommandsConfig = Field(default_factory=QualityGateCommandsConfig)


class ReviewConfig(BaseModel):
    """LLM code review settings."""

    model: str = "anthropic/claude-3-sonnet"


class ComponentConfig(BaseModel):
    """Configuration for a single project component."""

    language: str = "python"
    root: str = "./"
    test_command: str | None = None
    lint_command: str | None = None
    format_command: str | None = None
    coverage_threshold: int = 80


class StitchConfig(BaseModel):
    """Stitch MCP integration settings."""

    enabled: bool = False
    project_id: str | None = None


class BeadsConfig(BaseModel):
    """Beads task management settings."""

    database_path: str = ".beads/beads.db"


class VibraphoneConfig(BaseModel):
    """Full vibraphone.yaml configuration.

    Compatible with existing vibraphone-template format.
    All fields have sensible defaults.
    Unknown fields trigger warnings but don't fail loading.
    """

    model_config = ConfigDict(extra="allow")

    project: ProjectConfig = Field(default_factory=ProjectConfig)
    worktree: WorktreeConfig = Field(default_factory=WorktreeConfig)
    quality_gate: QualityGateConfig = Field(default_factory=QualityGateConfig)
    circuit_breakers: CircuitBreakersConfig = Field(default_factory=CircuitBreakersConfig)
    review: ReviewConfig = Field(default_factory=ReviewConfig)

    # Component configuration (for configure_stack tool)
    components: dict[str, ComponentConfig] = Field(default_factory=dict)
    stitch: StitchConfig = Field(default_factory=StitchConfig)
    beads: BeadsConfig = Field(default_factory=BeadsConfig)

    # The key configurable path (CFG-04)
    worktrees_path: Path = Field(default=DEFAULT_WORKTREES_PATH)

    @field_validator(
        "project",
        "worktree",
        "quality_gate",
        "circuit_breakers",
        "review",
        "components",
        "stitch",
        "beads",
        mode="before",
    )
    @classmethod
    def handle_none_sections(cls, v: Any) -> Any:  # noqa: ANN401
        """Convert None to empty dict for optional sections."""
        if v is None:
            return {}
        return v

    @field_validator("worktrees_path", mode="before")
    @classmethod
    def expand_tilde(cls, v: Any) -> Path:  # noqa: ANN401
        """Expand ~ in worktrees_path."""
        if isinstance(v, str):
            return Path(v).expanduser()
        if isinstance(v, Path):
            return v.expanduser()
        return v


def find_config_file() -> Path | None:
    """Walk up directories to find vibraphone.yaml.

    Search stops at:
    - First vibraphone.yaml found
    - .git directory (project root boundary)
    - $HOME directory (fallback boundary)

    Follows symlinks via Path.resolve().

    Returns:
        Path to vibraphone.yaml or None if not found.
    """
    current = Path.cwd().resolve()
    home = Path.home().resolve()

    while True:
        # Check for config file first
        config_path = current / "vibraphone.yaml"
        if config_path.is_file():
            return config_path

        # Check for .git directory (project root)
        if (current / ".git").exists():
            return None

        # Check if we've reached home
        if current == home:
            return None

        # Move up
        parent = current.parent
        if parent == current:
            # Filesystem root
            return None
        current = parent


def check_for_typos(unknown_fields: set[str]) -> list[str]:
    """Check unknown fields and generate warnings.

    Generates warnings for all unknown fields, with typo suggestions
    when a close match is found.
    """
    warnings = []
    for unknown in unknown_fields:
        matches = get_close_matches(unknown, KNOWN_TOP_LEVEL_FIELDS, n=1, cutoff=TYPO_SUGGESTION_CUTOFF)
        if matches:
            warnings.append(f"Unknown field '{unknown}'. Did you mean '{matches[0]}'?")
        else:
            warnings.append(f"Unknown field '{unknown}'.")
    return warnings


def format_validation_error(error: ValidationError, config_path: Path) -> str:
    """Format Pydantic validation error with helpful context."""
    lines = [f"Config validation failed in {config_path}:\n"]

    for err in error.errors():
        field_path = ".".join(str(p) for p in err["loc"])
        msg = err["msg"]
        error_type = err["type"]

        lines.append(f"  {field_path}: {msg}")

        # Add contextual suggestions per CONTEXT.md
        if error_type == "string_type":
            lines.append("    Did you mean to quote the value?")
        elif error_type == "int_parsing":
            lines.append("    Expected an integer.")

    return "\n".join(lines)


def load_yaml_with_errors(config_path: Path) -> dict:
    """Load YAML file with helpful error messages on failure."""
    try:
        content = config_path.read_text(encoding="utf-8")
        result = yaml.safe_load(content)
    except yaml.YAMLError as e:
        print(f"YAML syntax error in {config_path}:", file=sys.stderr)
        print(f"  {e}", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(f"Cannot read {config_path}: permission denied", file=sys.stderr)
        sys.exit(1)
    except UnicodeDecodeError as e:
        print(f"Cannot read {config_path}: encoding error - {e}", file=sys.stderr)
        sys.exit(1)
    else:
        return result if result is not None else {}


# Module-level cache
_config: VibraphoneConfig | None = None
_config_path: Path | None = None


def get_config() -> VibraphoneConfig:
    """Load config lazily.

    Returns:
        VibraphoneConfig with defaults if no file found, or validated config.
        Exits with error message if config is invalid.
    """
    global _config, _config_path

    if _config is not None:
        return _config

    config_path = find_config_file()
    if config_path is None:
        # No config file - use all defaults (CFG-03)
        _config = VibraphoneConfig()
        return _config

    _config_path = config_path

    try:
        raw_config = load_yaml_with_errors(config_path)
        _config = VibraphoneConfig.model_validate(raw_config)
    except ValidationError as e:
        print(format_validation_error(e, config_path), file=sys.stderr)
        sys.exit(1)
    else:
        # Check for unknown fields (CFG-05 compatibility + typo detection)
        unknown_fields = set(raw_config.keys()) - KNOWN_TOP_LEVEL_FIELDS
        if unknown_fields:
            warnings = check_for_typos(unknown_fields)
            for warning in warnings:
                print(f"Warning: {warning}", file=sys.stderr)

        return _config


def clear_config_cache() -> None:
    """Clear the cached config. Useful for testing."""
    global _config, _config_path
    _config = None
    _config_path = None


def get_project_root() -> Path:
    """Get project root directory.

    Returns the directory containing vibraphone.yaml or the current working
    directory if no config file is found.

    Returns:
        Path to project root directory.
    """
    config_path = find_config_file()
    if config_path is not None:
        return config_path.parent
    return Path.cwd()


def get_component_commands(component_name: str) -> dict[str, str]:
    """Get commands for a component, falling back to STACK_DEFAULTS by language.

    Args:
        component_name: Name of the component to look up

    Returns:
        Dict with test, lint, format commands for the component
    """
    config = get_config()
    comp = config.components.get(component_name, ComponentConfig())
    defaults = STACK_DEFAULTS.get(comp.language, {})
    return {
        "test": comp.test_command or defaults.get("test_command", "echo 'no test command'"),
        "lint": comp.lint_command or defaults.get("lint_command", "echo 'no lint command'"),
        "format": comp.format_command or defaults.get("format_command", "echo 'no format command'"),
    }
