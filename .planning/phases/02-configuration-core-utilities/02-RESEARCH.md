# Phase 2: Configuration & Core Utilities - Research

**Researched:** 2026-02-16
**Domain:** Python Configuration Discovery, Loading, and Validation
**Confidence:** HIGH

## Summary

This research covers the technical patterns for implementing configuration discovery, loading, and validation for vibraphone. The key finding is that PyYAML's `safe_load()` combined with Pydantic validation provides the most robust solution for config handling, with built-in support for helpful error messages and type coercion. For directory walking to find config files, pathlib's `.parent` iteration is the standard Python pattern, with `.git` directory detection providing a reliable project root boundary.

The `difflib.get_close_matches()` function from Python's standard library provides a built-in solution for typo detection with a configurable similarity threshold (default 0.6), matching the CONTEXT.md requirement for near-miss field name suggestions.

**Primary recommendation:** Use PyYAML `safe_load()` for parsing, Pydantic `BaseModel` with `extra='allow'` for validation (warns on unknown fields instead of rejecting), and `difflib.get_close_matches()` for typo suggestions. Implement directory walking using pathlib's `.parent` chain with `.git` and `$HOME` as boundaries.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Error Message Depth
- Validation errors show: field name + problem + suggestion (e.g., "worktrees_path: must be a string, got 123. Did you mean to quote the path?")
- YAML syntax errors expose parser detail (line number, parse error from library)
- Server fails fast with exit(1) on invalid config at startup
- Multiple problems reported together, not just first error
- Config file exists but unreadable (permissions, encoding) → fail with error
- Output to stderr only (no log file for v1)
- Warnings allowed for non-fatal issues, server can still start
- Warning vs error threshold at Claude's discretion

#### Discovery Edge Cases
- First vibraphone.yaml wins, stop searching immediately
- Search boundary: stop at .git directory (project root)
- If no .git found, fallback to $HOME as boundary
- Discovery happens once at startup, result is cached
- Symlink handling at Claude's discretion (will follow symlinks by default)

#### Unknown Field Handling
- Unknown fields in config → warn but continue
- Near-miss typo detection: warn with suggestion for fields that look like typos of known names

### Claude's Discretion

- Which scenarios warrant warnings vs errors
- Symlink handling approach (default: follow symlinks)
- Exact typo detection algorithm (Levenshtein distance threshold)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CFG-01 | Server discovers vibraphone.yaml by walking up from CWD | pathlib parent iteration pattern, .git and $HOME boundary detection |
| CFG-02 | Config validates on load with clear error messages for invalid fields | Pydantic validation with custom error messages, PyYAML error parsing |
| CFG-03 | All config fields have sensible defaults | Pydantic `Field(default=...)` and `model_config = ConfigDict(extra='allow')` |
| CFG-04 | Worktree base path configurable via vibraphone.yaml (default: ~/.vibraphone/worktrees/) | Path expansion with `Path.expanduser()`, Pydantic field defaults |
| CFG-05 | Existing vibraphone.yaml format from template projects is compatible | Pydantic flexible schema with optional fields, nested model support |

</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pyyaml | >=6.0 | YAML file parsing | Already in dependencies. Standard library for YAML in Python. Use `safe_load()` for security. |
| pydantic | >=2.0 | Config validation | Type-safe parsing, automatic error messages, coercion. FastMCP may pull this in already. |
| pathlib | stdlib | Path handling | Python standard. Use for all file path operations. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| difflib | stdlib | Typo detection | `get_close_matches()` for suggesting similar field names on unknown keys |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pydantic validation | Manual dict validation | Manual validation requires more code, harder to maintain, less helpful errors |
| difflib | Levenshtein package | difflib is stdlib (no dependency), 0.6 cutoff works well for typos |
| pathlib.parent walking | os.path recursion | pathlib is more readable, Python 3.13+ standard |

**Installation:**
```bash
# Already in pyproject.toml
# pyyaml>=6.0 is present
# pydantic may be pulled in by fastmcp
```

## Architecture Patterns

### Recommended Project Structure

```
src/vibraphone/
├── config.py              # Config loading, validation, caching
├── server.py              # Entry point (imports config)
└── utils/
    └── discovery.py       # Config file discovery (walk up directories)
```

### Pattern 1: Directory Walking for Config Discovery

**What:** Walk up from CWD to find `vibraphone.yaml`, stopping at `.git` or `$HOME`

**When:** All config loading (happens once, cached)

**Example:**
```python
# Source: Standard pathlib pattern
from pathlib import Path
import os

def find_config_file() -> Path | None:
    """Walk up directories to find vibraphone.yaml.

    Search stops at:
    - First vibraphone.yaml found
    - .git directory (project root boundary)
    - $HOME directory (fallback boundary)

    Returns:
        Path to vibraphone.yaml or None if not found.
    """
    current = Path.cwd().resolve()

    # Get boundary paths
    home = Path.home().resolve()

    while True:
        # Check for config file first (before checking boundary)
        config_path = current / "vibraphone.yaml"
        if config_path.is_file():
            return config_path

        # Check for .git directory (project root boundary)
        if (current / ".git").exists():
            # Stop at project root, no config found
            return None

        # Check if we've reached home directory
        if current == home:
            return None

        # Move up one directory
        parent = current.parent
        if parent == current:
            # Reached filesystem root
            return None
        current = parent
```

**Why:** This pattern is deterministic, handles nested projects correctly, and has clear boundary conditions.

---

### Pattern 2: Pydantic Config Model with Defaults

**What:** Use Pydantic `BaseModel` with field defaults and `extra='allow'` for unknown field tolerance

**When:** All config parsing

**Example:**
```python
# Source: Pydantic docs - https://docs.pydantic.dev/latest/concepts/models/
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Any

class ProjectConfig(BaseModel):
    """Project identification from vibraphone.yaml."""
    name: str = "unnamed-project"
    version: str = "0.1.0"

class WorktreeConfig(BaseModel):
    """Worktree settings with defaults."""
    base_branch: str = "main"
    prefix: str = "feat/"
    auto_cleanup: bool = False

class QualityGateConfig(BaseModel):
    """Quality gate settings with defaults."""
    require_tests: bool = True
    require_lint: bool = True
    require_review: bool = True
    review_severity_threshold: str = "error"
    max_test_attempts: int = Field(default=10, ge=1)
    max_review_attempts: int = Field(default=5, ge=1)

class VibraphoneConfig(BaseModel):
    """Full vibraphone.yaml configuration.

    Compatible with existing vibraphone-template format.
    All fields have sensible defaults.
    Unknown fields are allowed (will warn but not fail).
    """
    model_config = ConfigDict(extra='allow')  # Allow unknown fields

    project: ProjectConfig = Field(default_factory=ProjectConfig)
    worktree: WorktreeConfig = Field(default_factory=WorktreeConfig)
    quality_gate: QualityGateConfig = Field(default_factory=QualityGateConfig)

    # The key configurable path (CFG-04)
    # Note: The template uses 'worktree.base_branch', not 'worktrees_path'
    # We may need to support both for compatibility

    @field_validator('project', 'worktree', 'quality_gate', mode='before')
    @classmethod
    def handle_none_sections(cls, v: Any) -> Any:
        """Handle missing sections by converting None to empty dict."""
        if v is None:
            return {}
        return v
```

**Why:** Pydantic provides type coercion, validation, and automatic error messages. `extra='allow'` lets us warn on unknown fields instead of failing.

---

### Pattern 3: Error Message Formatting

**What:** Format Pydantic and YAML errors with helpful context and suggestions

**When:** Any config parsing error

**Example:**
```python
# Source: Pydantic error handling docs - https://docs.pydantic.dev/latest/errors/errors/
import sys
from pathlib import Path
from difflib import get_close_matches
from pydantic import ValidationError
import yaml

# Known field names for typo detection
KNOWN_TOP_LEVEL_FIELDS = {'project', 'components', 'quality_gate', 'worktree', 'review', 'beads', 'stitch'}
SUGGESTION_CUTOFF = 0.6  # difflib default

def format_validation_error(error: ValidationError, config_path: Path) -> str:
    """Format Pydantic validation error with helpful context."""
    lines = [f"Config validation failed in {config_path}:\n"]

    for err in error.errors():
        field_path = '.'.join(str(p) for p in err['loc'])
        msg = err['msg']
        error_type = err['type']

        # Build helpful error message
        lines.append(f"  {field_path}: {msg}")

        # Add suggestions for type errors
        if error_type == 'string_type':
            lines.append(f"    Did you mean to quote the value?")
        elif error_type == 'int_parsing':
            lines.append(f"    Expected an integer, got a different type.")

    return '\n'.join(lines)

def check_for_typos(unknown_fields: set[str]) -> list[str]:
    """Check unknown fields for potential typos against known field names."""
    warnings = []
    for unknown in unknown_fields:
        matches = get_close_matches(unknown, KNOWN_TOP_LEVEL_FIELDS, n=1, cutoff=SUGGESTION_CUTOFF)
        if matches:
            warnings.append(f"  Unknown field '{unknown}'. Did you mean '{matches[0]}'?")
    return warnings

def load_yaml_with_errors(config_path: Path) -> dict:
    """Load YAML file with helpful error messages."""
    try:
        content = config_path.read_text()
        return yaml.safe_load(content)
    except yaml.YAMLError as e:
        # YAML syntax errors - expose parser detail (line number, problem)
        print(f"YAML syntax error in {config_path}:", file=sys.stderr)
        print(f"  {e}", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(f"Cannot read {config_path}: permission denied", file=sys.stderr)
        sys.exit(1)
    except UnicodeDecodeError as e:
        print(f"Cannot read {config_path}: encoding error - {e}", file=sys.stderr)
        sys.exit(1)
```

**Why:** Users get actionable errors immediately. Pydantic provides the structure, we add contextual suggestions.

---

### Pattern 4: Cached Config Loading

**What:** Load config once on first access, cache result for subsequent calls

**When:** All config access (already implemented in Phase 1 stub)

**Example:**
```python
# Source: Existing config.py pattern from Phase 1
from pathlib import Path
from pydantic import ValidationError
import sys

_config: VibraphoneConfig | None = None
_config_path: Path | None = None

def get_config() -> VibraphoneConfig | None:
    """Load config lazily. Returns None if vibraphone.yaml not found.

    Implements:
    - Lazy loading (not on server startup)
    - Caching (single load per process)
    - Default values when file missing
    """
    global _config, _config_path

    if _config is not None:
        return _config

    config_path = find_config_file()
    if config_path is None:
        # No config file - use all defaults (PKG-04)
        _config = VibraphoneConfig()
        return _config

    _config_path = config_path

    try:
        raw_config = load_yaml_with_errors(config_path)
        _config = VibraphoneConfig.model_validate(raw_config)

        # Check for unknown fields and warn
        unknown_fields = set(raw_config.keys()) - KNOWN_TOP_LEVEL_FIELDS
        if unknown_fields:
            warnings = check_for_typos(unknown_fields)
            for warning in warnings:
                print(f"Warning: {warning}", file=sys.stderr)

        return _config

    except ValidationError as e:
        print(format_validation_error(e, config_path), file=sys.stderr)
        sys.exit(1)

def clear_config_cache() -> None:
    """Clear the cached config. Useful for testing."""
    global _config, _config_path
    _config = None
    _config_path = None
```

**Why:** Matches Phase 1 pattern, supports testing, caches discovery result.

---

### Anti-Patterns to Avoid

- **Using `yaml.load()` instead of `yaml.safe_load()`:** Security vulnerability - allows arbitrary code execution. Always use `safe_load()`.
- **Failing silently on malformed config:** Users need to know what went wrong. Always report errors with context.
- **Hardcoding paths like `~/.vibraphone/worktrees`:** Use `Path.home()` for ~ expansion, make paths configurable.
- **Rejecting unknown fields with `extra='forbid'`:** Breaks forward compatibility. Use `extra='allow'` and warn.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML parsing | Custom parser | PyYAML `safe_load()` | Handles edge cases, security, line numbers |
| Config validation | Manual type checking | Pydantic `BaseModel` | Type coercion, error messages, nested models |
| Typo detection | Levenshtein implementation | `difflib.get_close_matches()` | stdlib, proven algorithm, configurable cutoff |
| Path expansion | String manipulation | `Path.expanduser()` | Handles ~, environment variables correctly |
| Directory walking | os.path recursion | pathlib `.parent` chain | More readable, handles edge cases |

**Key insight:** The standard library and Pydantic cover all config handling needs. Custom solutions add complexity without benefit.

## Common Pitfalls

### Pitfall 1: Not Handling YAML Encoding Issues

**What goes wrong:** Config files with non-UTF8 encoding cause cryptic errors.

**Why it happens:** PyYAML defaults to system encoding, some editors save in different encodings.

**How to avoid:** Always specify UTF-8 when reading, catch `UnicodeDecodeError` with helpful message.

**Warning signs:** "UnicodeDecodeError: 'utf-8' codec can't decode"

---

### Pitfall 2: Forgetting to Expand ~ in Paths

**What goes wrong:** `~/.vibraphone/worktrees` is treated as literal path, not home directory.

**Why it happens:** YAML doesn't expand shell variables, Python strings don't either.

**How to avoid:** Use `Path.expanduser()` on all path fields after loading.

**Warning signs:** "No such file or directory: '~/...'" errors

---

### Pitfall 3: Config Discovery Goes to Filesystem Root

**What goes wrong:** Walking up directories without boundary goes all the way to `/`, finding wrong config or taking forever.

**Why it happens:** Missing boundary conditions in the walk loop.

**How to avoid:** Always check for `.git` directory and `$HOME` as boundaries, handle filesystem root case.

**Warning signs:** Config loading takes unexpectedly long, finds config in unexpected location.

---

### Pitfall 4: Not Handling Missing Optional Sections

**What goes wrong:** Pydantic fails validation when a nested section like `project:` exists but is empty or None.

**Why it happens:** YAML parses empty section as `None`, not empty dict.

**How to avoid:** Use `mode='before'` validators to convert `None` to `{}` for nested models.

**Warning signs:** "Input should be a valid dictionary" errors for sections that should be optional.

## Code Examples

### Complete Config Module

```python
# src/vibraphone/config.py
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
    "project", "components", "quality_gate", "worktree", "review", "beads", "stitch"
}

# difflib cutoff for typo suggestions (0.6 is default, works well)
TYPO_SUGGESTION_CUTOFF = 0.6


class ProjectConfig(BaseModel):
    """Project identification."""

    name: str = "unnamed-project"
    version: str = "0.1.0"


class WorktreeConfig(BaseModel):
    """Worktree settings."""

    base_branch: str = "main"
    prefix: str = "feat/"
    auto_cleanup: bool = False


class QualityGateConfig(BaseModel):
    """Quality gate settings."""

    require_tests: bool = True
    require_lint: bool = True
    require_review: bool = True
    review_severity_threshold: str = "error"
    max_test_attempts: int = Field(default=10, ge=1)
    max_review_attempts: int = Field(default=5, ge=1)


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

    @field_validator("project", "worktree", "quality_gate", mode="before")
    @classmethod
    def handle_none_sections(cls, v: Any) -> Any:
        """Convert None to empty dict for optional sections."""
        if v is None:
            return {}
        return v


def find_config_file() -> Path | None:
    """Walk up directories to find vibraphone.yaml.

    Search stops at:
    - First vibraphone.yaml found
    - .git directory (project root boundary)
    - $HOME directory (fallback boundary)

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
    """Check unknown fields for potential typos."""
    warnings = []
    for unknown in unknown_fields:
        matches = get_close_matches(
            unknown, KNOWN_TOP_LEVEL_FIELDS, n=1, cutoff=TYPO_SUGGESTION_CUTOFF
        )
        if matches:
            warnings.append(
                f"Unknown field '{unknown}'. Did you mean '{matches[0]}'?"
            )
    return warnings


def format_validation_error(error: ValidationError, config_path: Path) -> str:
    """Format Pydantic validation error with helpful context."""
    lines = [f"Config validation failed in {config_path}:\n"]

    for err in error.errors():
        field_path = ".".join(str(p) for p in err["loc"])
        msg = err["msg"]
        error_type = err["type"]

        lines.append(f"  {field_path}: {msg}")

        # Add contextual suggestions
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
        return result if result is not None else {}
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
        # No config file - use all defaults
        _config = VibraphoneConfig()
        return _config

    _config_path = config_path

    try:
        raw_config = load_yaml_with_errors(config_path)
        _config = VibraphoneConfig.model_validate(raw_config)

        # Check for unknown fields
        unknown_fields = set(raw_config.keys()) - KNOWN_TOP_LEVEL_FIELDS
        if unknown_fields:
            warnings = check_for_typos(unknown_fields)
            for warning in warnings:
                print(f"Warning: {warning}", file=sys.stderr)

        return _config

    except ValidationError as e:
        print(format_validation_error(e, config_path), file=sys.stderr)
        sys.exit(1)


def clear_config_cache() -> None:
    """Clear the cached config. Useful for testing."""
    global _config, _config_path
    _config = None
    _config_path = None
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `yaml.load()` | `yaml.safe_load()` | PyYAML 5.1+ (2019) | Security: prevents arbitrary code execution |
| Manual validation | Pydantic BaseModel | Pydantic 2.0 (2023) | Type safety, automatic coercion, better errors |
| os.path for paths | pathlib | Python 3.4+ | Readable, object-oriented path handling |
| `extra='forbid'` | `extra='allow'` with warnings | Pydantic 2.0+ | Forward compatibility with new config fields |

**Deprecated/outdated:**
- `yaml.load()` without Loader: Security vulnerability, removed in PyYAML 6.0
- `setup.cfg` for config: Use pyproject.toml (PEP 621)
- Custom config formats (INI, JSON): YAML is standard for hierarchical config

## Claude's Discretion Recommendations

### Warning vs Error Threshold

**Recommendation:** Use warnings for:
- Unknown fields (with typo suggestion if applicable)
- Deprecated field names (future feature)
- Optional fields with invalid values that have defaults

Use errors for:
- Required fields missing
- Type mismatches that cannot be coerced
- Constraint violations (e.g., `max_test_attempts < 1`)
- YAML syntax errors
- File permission/read errors

### Symlink Handling

**Recommendation:** Follow symlinks by default using `Path.resolve()`. This is the standard Python behavior and what users expect. If a symlink points outside the project, the `.git` boundary check will still work correctly.

### Typo Detection Algorithm

**Recommendation:** Use `difflib.get_close_matches()` with:
- `n=1` (return only the best match)
- `cutoff=0.6` (default, works well for single-word typos)

This matches 1-2 character edits in words up to about 8 characters, which covers most typos without false positives.

## Open Questions

1. **Template Compatibility - worktrees_path vs worktree.base_branch**
   - What we know: The template uses `worktree.base_branch` for git branch, but CFG-04 mentions `worktrees_path` field
   - What's unclear: Whether we need a separate `worktrees_path` field or derive it from existing config
   - Recommendation: Add optional `worktrees_path` field at root level (default: `~/.vibraphone/worktrees/`), keep template's `worktree.base_branch` for branch configuration

2. **Components Section Handling**
   - What we know: Template has `components.app` with language-specific settings
   - What's unclear: Whether Phase 2 needs to validate components or just ignore them
   - Recommendation: Add to `KNOWN_TOP_LEVEL_FIELDS` but don't validate in v1. Future phase will handle stack configuration.

## Sources

### Primary (HIGH confidence)

- [Pydantic Validation Errors](https://docs.pydantic.dev/latest/errors/validation_errors/) - Error types, formatting, custom messages
- [Pydantic Error Handling](https://docs.pydantic.dev/latest/errors/errors/) - ValidationError structure, error customization
- [PyYAML Documentation](https://pyyaml.org/wiki/PyYAMLDocumentation) - safe_load, YAMLError handling
- [Python difflib](https://docs.python.org/3/library/difflib.html) - get_close_matches API, cutoff parameter

### Secondary (MEDIUM confidence)

- [Python pathlib](https://docs.python.org/3/library/pathlib.html) - Path operations, parent iteration
- FreeCodeCamp YAML in Python guide - safe_load best practices
- Real Python pathlib tutorial - Path manipulation patterns

### Tertiary (LOW confidence)

- Stack Overflow discussions on config file discovery patterns
- Reddit discussions on Pydantic config validation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - PyYAML, Pydantic, pathlib are all mature, well-documented libraries
- Architecture: HIGH - Patterns verified against official docs and existing template
- Pitfalls: HIGH - Based on documented error types and common issues

**Research date:** 2026-02-16
**Valid until:** 90 days (stable libraries, low churn expected)

---

*Research completed for Phase 2: Configuration & Core Utilities*
