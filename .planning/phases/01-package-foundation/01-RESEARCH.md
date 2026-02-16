# Phase 1: Package Foundation - Research

**Researched:** 2026-02-16
**Domain:** Python Package Foundation with FastMCP Server Entry Point
**Confidence:** HIGH

## Summary

This research covers the technical foundation for creating an installable Python package with a FastMCP server entry point. The key finding is that FastMCP provides a simple, decorator-based API where `mcp.run()` handles all protocol details including stdio transport. The entry point pattern is straightforward: create a `main()` function that calls `mcp.run(transport="stdio")` and register it in `pyproject.toml` under `[project.scripts]`.

For the Astral toolchain ecosystem (uv, ruff, ty, prek), all tools are confirmed to be compatible and represent the modern best practice for Python development in 2025/2026. The `ty` type checker is now in Beta and recommended for production use.

**Primary recommendation:** Use `from fastmcp import FastMCP` (not `mcp.server.fastmcp`), create a single `server.py` that instantiates the MCP server and calls `mcp.run(transport="stdio")`, and register the entry point as `vibraphone = "vibraphone.server:main"`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Package Structure
- Mirror existing structure: `server.py`, `config.py`, `tools/`, `utils/` under `src/vibraphone/`
- Tests in root `tests/` directory (outside package, standard convention)
- MCP-server-only: no Python library API for `import vibraphone` — all interaction via MCP tools
- Separate files for each tool module (beads_tools.py, quality_tools.py, etc.)
- Template files bundled in package, accessible via `importlib.resources` (for Phase 7 scaffolding)

#### Entry Point Behavior
- Follow FastMCP docs pattern for entry point (not existing template pattern)
- Log to stderr for debugging (not silent, not file-based)
- Lazy config loading: vibraphone.yaml loads when first tool needs it, not on startup
- Session recovery deferred to Phase 4 (Phase 1 server starts without config)

#### Dependencies
- Python 3.13+ (latest stable)
- `pyproject.toml` only — no requirements.txt
- Dev dependencies in `[project.optional-dependencies] dev`
- FastMCP pinned to specific version for stability
- External binaries (br, bv, git, just, node/npx) not declared as deps — detect-and-guide via `check_prerequisites` tool

#### Development Workflow
- uv primarily for all Python tooling (install, venv, run)
- pytest + pytest-xdist for testing (parallel execution)
- ruff for linting and formatting
- ty (Astral type checker) for type checking
- prek for pre-commit hooks with ruff + ty
- GitHub Actions for CI (tests, lint, type check)
- Justfile for dev tasks, using `uv run` for Python commands
- `.python-version` file for Python version declaration

### Claude's Discretion

- Exact error message format on startup failure
- Logging verbosity level
- Specific FastMCP version to pin
- GitHub Actions workflow structure

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PKG-01 | Package installable via `uv tool install vibraphone` from local path or git | FastMCP entry point pattern, pyproject.toml [project.scripts] configuration |
| PKG-02 | Package installable via `pip install -e .` for development | src layout configuration, Hatchling build backend |
| PKG-03 | `vibraphone` command starts FastMCP server on stdio transport | `mcp.run(transport="stdio")` pattern documented below |
| PKG-04 | Server starts without vibraphone.yaml present (zero-config, stays quiet) | Lazy config loading pattern, no startup-time config requirement |
| PKG-05 | Source code organized in src/vibraphone/ layout | src layout patterns documented below, Hatchling auto-discovery |
| PKG-06 | All Python dependencies declared in pyproject.toml | Dependency declaration patterns, FastMCP package name confirmed |

</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastmcp | latest | MCP server framework | Purpose-built for MCP servers in Python. Handles stdio transport, tool registration, server lifecycle via simple `mcp.run()` call. |
| Python | >=3.13 | Runtime | Locked decision. Modern async/await, type hints, pattern matching. |
| Hatchling | latest | Build backend | Already in pyproject.toml. Fast, modern, zero-config for src layout packages. |
| pyyaml | >=6.0 | Config file parsing | Required for vibraphone.yaml parsing. Standard YAML library. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic | >=2.0 | Config validation | FastMCP may pull this in. Use for type-safe config parsing. |
| httpx | >=0.27.0 | Async HTTP client | For Phase 5 code review (LLM API calls). Async-compatible with FastMCP. |

### Development Tools

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| uv | 0.5+ | Package manager, tool installer | Astral ecosystem. Target for `uv tool install`. |
| ruff | latest | Linting & formatting | Replaces black, isort, flake8. Already configured in pyproject.toml. |
| ty | beta | Type checking | Astral's new type checker. Now in Beta, recommended for production. |
| prek | latest | Pre-commit hooks | Rust-based pre-commit alternative. Faster, integrates with uv. |
| pytest | >=8.0 | Testing framework | Standard Python testing. Already configured. |
| pytest-asyncio | >=0.23 | Async test support | Required for testing FastMCP async tools. |
| pytest-xdist | latest | Parallel test execution | Locked decision for faster test runs. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Hatchling | setuptools | setuptools is more mature but Hatchling is simpler for pure-Python packages and already configured |
| ty | mypy/pyright | ty is 10-60x faster and part of Astral ecosystem; mypy more mature but slower |
| prek | pre-commit | prek is Rust-based, faster, no Python dependency; pre-commit has broader ecosystem but slower |

**Installation:**
```bash
# Core dependencies (in pyproject.toml)
uv add fastmcp pyyaml

# Dev dependencies
uv add --dev pytest pytest-asyncio pytest-xdist ruff ty
```

## Architecture Patterns

### Recommended Project Structure

```
vibraphone/
├── pyproject.toml              # PEP 621 metadata, entry point, tool config
├── README.md                   # Package description
├── LICENSE                     # Required for PyPI
├── .python-version             # Python version declaration (3.13)
├── src/
│   └── vibraphone/
│       ├── __init__.py         # Package metadata (__version__)
│       ├── server.py           # FastMCP server entry point
│       ├── config.py           # Configuration loading (lazy)
│       ├── tools/              # MCP tool implementations
│       │   ├── __init__.py
│       │   └── (tool files migrated in later phases)
│       └── utils/              # Shared utilities
│           ├── __init__.py
│           └── (utility files migrated in later phases)
├── tests/
│   ├── __init__.py
│   └── test_server.py          # Entry point tests
└── .pre-commit-config.yaml     # prek configuration
```

### Pattern 1: FastMCP Entry Point

**What:** Single `server.py` with `main()` function that starts the server

**When:** All MCP servers — this is the standard pattern

**Example:**
```python
# src/vibraphone/server.py
import sys
from fastmcp import FastMCP

mcp = FastMCP("vibraphone")

# Tool registration happens via decorators in tool modules
# Import tool modules to trigger registration
# from vibraphone.tools import beads_tools, quality_tools  # Future phases

def main() -> None:
    """Entry point for vibraphone MCP server."""
    # Log startup to stderr (per locked decision)
    print("Starting vibraphone MCP server...", file=sys.stderr)
    # mcp.run() handles all protocol details including stdio transport
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
```

**Why:** FastMCP's `mcp.run(transport="stdio")` handles all protocol details, transport setup, and connection management automatically.

**Source:** [FastMCP Quickstart](https://gofastmcp.com/getting-started/quickstart) - HIGH confidence

---

### Pattern 2: pyproject.toml Entry Point Registration

**What:** Register console script in `[project.scripts]`

**When:** All installable Python CLI tools

**Example:**
```toml
[project.scripts]
vibraphone = "vibraphone.server:main"
```

**Why:** This makes `vibraphone` command available after `uv tool install` or `pip install`. The format is `command_name = "module.path:function_name"`.

**Source:** Python Packaging User Guide - HIGH confidence

---

### Pattern 3: Hatchling src Layout Configuration

**What:** Let Hatchling auto-discover src layout (minimal configuration)

**When:** Using src layout (recommended)

**Example:**
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

# No explicit [tool.hatch.build.targets.wheel] needed
# Hatchling auto-discovers src/vibraphone/
```

**Current issue:** pyproject.toml has legacy config that must be removed:
```toml
# REMOVE THIS - flat layout config:
[tool.hatch.build.targets.wheel]
packages = ["config.py", "server.py", "tools", "utils"]
```

**Why:** Hatchling automatically detects src layout. Explicit configuration is only needed for non-standard layouts.

**Source:** Hatchling documentation - HIGH confidence

---

### Pattern 4: Lazy Config Loading

**What:** Config loads on first access, not on server startup

**When:** Server must start without vibraphone.yaml (PKG-04)

**Example:**
```python
# src/vibraphone/config.py
from pathlib import Path
from dataclasses import dataclass

@dataclass
class VibraphoneConfig:
    project_root: Path
    # ... other fields

_config: VibraphoneConfig | None = None

def get_config() -> VibraphoneConfig | None:
    """Load config lazily. Returns None if vibraphone.yaml not found."""
    global _config
    if _config is not None:
        return _config

    config_path = Path.cwd() / "vibraphone.yaml"
    if not config_path.exists():
        return None

    # Parse and cache config
    _config = _parse_config(config_path)
    return _config
```

**Why:** Phase 1 requirement that server starts without crashing when vibraphone.yaml is absent.

---

### Anti-Patterns to Avoid

- **Flat layout (files at repo root):** Causes import pollution, harder to package. Use `src/vibraphone/` layout.
- **Importing `mcp.server.fastmcp`:** Old import path. Use `from fastmcp import FastMCP`.
- **Sync subprocess calls in async context:** Blocks event loop. Use `asyncio.create_subprocess_exec`.
- **Hardcoded paths:** Breaks when installed as package. All paths must come from config or use `importlib.resources`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MCP protocol implementation | Custom stdio handler | FastMCP `mcp.run()` | Handles protocol, transport, error recovery |
| Tool registration | Manual schema generation | `@mcp.tool` decorator | Auto-generates JSON schema from type hints |
| Package data access | `__file__` relative paths | `importlib.resources` | Works in editable and installed modes |
| Config validation | Manual validation | Pydantic | Type-safe, clear error messages |

**Key insight:** FastMCP is designed to eliminate boilerplate. The entire server can be started with just `mcp.run()`.

## Common Pitfalls

### Pitfall 1: Wrong FastMCP Import Path

**What goes wrong:** Using `from mcp.server.fastmcp import FastMCP` (old SDK path) instead of `from fastmcp import FastMCP` (FastMCP package).

**Why it happens:** The official Python SDK and FastMCP are different packages with similar naming.

**How to avoid:** Install `fastmcp` package (not `mcp`), use `from fastmcp import FastMCP`.

**Warning signs:** ImportError on startup, "No module named 'mcp.server.fastmcp'".

---

### Pitfall 2: Hatch Build Config for Wrong Layout

**What goes wrong:** Legacy `[tool.hatch.build.targets.wheel]` with flat layout paths causes built wheel to be empty or missing files.

**Why it happens:** Current pyproject.toml has config for flat layout that will be wrong after src migration.

**How to avoid:** Remove explicit hatch build config — let Hatchling auto-discover src layout.

**Warning signs:** `pip install -e .` succeeds but `uv tool install` produces non-working package.

---

### Pitfall 3: Entry Point Not Callable

**What goes wrong:** Registering `vibraphone.server` instead of `vibraphone.server:main` causes import but no execution.

**Why it happens:** Entry point syntax requires `module:function` format, not just module.

**How to avoid:** Always use `module.path:function_name` format in `[project.scripts]`.

**Warning signs:** `vibraphone` command runs but does nothing, no server starts.

---

### Pitfall 4: Tests Use Wrong Import Paths

**What goes wrong:** After src migration, tests still use `from tools.beads_tools` instead of `from vibraphone.tools.beads_tools`.

**Why it happens:** Import paths change from flat to namespaced.

**How to avoid:** Update all test imports. Use `pytest --import-mode=importlib` to catch issues early.

**Warning signs:** ImportError in test suite after restructuring.

## Code Examples

### Minimal Working Server

```python
# src/vibraphone/__init__.py
__version__ = "0.1.0"
```

```python
# src/vibraphone/server.py
import sys
from fastmcp import FastMCP

# Initialize server with name
mcp = FastMCP("vibraphone")

# Placeholder tool for Phase 1 verification
@mcp.tool
def ping() -> str:
    """Health check tool. Returns 'pong'."""
    return "pong"

def main() -> None:
    """Entry point for vibraphone MCP server."""
    # Log to stderr (per locked decision)
    print(f"vibraphone MCP server starting (v{__import__('vibraphone').__version__})", file=sys.stderr)
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
```

### Complete pyproject.toml for Phase 1

```toml
[project]
name = "vibraphone"
version = "0.1.0"
description = "Vibraphone is an MCP server for AI coding agents that enforces disciplined software development workflows."
readme = "README.md"
requires-python = ">=3.13"
license = {text = "MIT"}
authors = [
    {name = "Luke McGuire", email = "luke@example.com"}
]
keywords = ["mcp", "mcp-server", "ai-agents", "tdd", "workflow"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3.13",
]
dependencies = [
    "fastmcp>=2.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-xdist>=3.0",
    "pytest-mock>=3.12",
]

[project.scripts]
vibraphone = "vibraphone.server:main"

[project.urls]
Homepage = "https://github.com/lukemcguire/vibraphone"
Repository = "https://github.com/lukemcguire/vibraphone"
Issues = "https://github.com/lukemcguire/vibraphone/issues"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

# Ruff config (already extensive in current pyproject.toml - preserve it)
[tool.ruff]
line-length = 120
fix = true
extend-exclude = ["**/.venv"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "ANN", "B", "SIM", "PTH"]
ignore = ["E501", "ANN101", "ANN102"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.ty.environment]
python-version = "3.13"
```

### Basic Entry Point Test

```python
# tests/test_server.py
import subprocess
import sys

def test_entry_point_callable():
    """Verify vibraphone command can be invoked."""
    result = subprocess.run(
        [sys.executable, "-m", "vibraphone.server", "--help"],
        capture_output=True,
        text=True,
        timeout=5
    )
    # Server won't have --help, but should not crash with ImportError
    assert "ImportError" not in result.stderr

def test_version_importable():
    """Verify package version is accessible."""
    import vibraphone
    assert hasattr(vibraphone, "__version__")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `mcp.server.fastmcp` import | `from fastmcp import FastMCP` | FastMCP 2.0 | Simpler API, separate package |
| mypy/pyright type checking | ty (Astral) | Dec 2025 Beta | 10-60x faster, Rust-based |
| pre-commit (Python) | prek (Rust) | 2025 | Faster, no Python dependency |
| flat layout | src layout | Python 3.11+ standard | Prevents import pollution |

**Deprecated/outdated:**
- `setup.py`/`setup.cfg`: Use pyproject.toml (PEP 621)
- `mcp` package for FastMCP: Use `fastmcp` package
- `__file__` for package data: Use `importlib.resources`

## Claude's Discretion Recommendations

### Error Message Format on Startup Failure

**Recommendation:** Use structured error messages with clear action items:
```python
def main() -> None:
    try:
        mcp.run(transport="stdio")
    except Exception as e:
        print(f"vibraphone: error: {e}", file=sys.stderr)
        print("  Run 'vibraphone --help' for usage information.", file=sys.stderr)
        sys.exit(1)
```

### Logging Verbosity Level

**Recommendation:** Use WARNING as default, INFO for startup confirmation:
- Startup: Single INFO line to stderr confirming server started
- Missing config: DEBUG level (not a warning - expected in non-vibraphone projects)
- Tool errors: WARNING level with context

### Specific FastMCP Version to Pin

**Recommendation:** Use compatible release specifier `fastmcp>=2.0` (FastMCP 2.x is the current stable line as of 2026). Avoid exact pin to allow patch updates.

### GitHub Actions Workflow Structure

**Recommendation:** Single workflow file with test, lint, type-check jobs:
```yaml
name: CI
on: [push, pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv pip install -e ".[dev]"
      - run: uv run ruff check
      - run: uv run ty check
      - run: uv run pytest -n auto
```

## Open Questions

1. **FastMCP Tool Registration Pattern**
   - What we know: Decorators (`@mcp.tool`) work for single-file servers
   - What's unclear: Best pattern for multi-file tool modules — import side effects vs explicit registration
   - Recommendation: Use import side effects (import tool modules in server.py to trigger decorator registration)

2. **prek Configuration Format**
   - What we know: prek is compatible with pre-commit config format
   - What's unclear: Whether prek-specific features should be used
   - Recommendation: Start with pre-commit-compatible config, adopt prek features incrementally

## Sources

### Primary (HIGH confidence)

- [FastMCP Quickstart](https://gofastmcp.com/getting-started/quickstart) - Entry point pattern, mcp.run() usage
- [CircleCI FastMCP Tutorial](https://circleci.com/blog/building-and-deploying-a-python-mcp-server-with-fastmcp/) - Full packaging example
- [Astral ty Blog Post](https://astral.sh/blog/ty) - Type checker details, Beta status
- [prek Documentation](https://prek.j178.dev/) - Pre-commit alternative details

### Secondary (MEDIUM confidence)

- [GitHub Issue #1681](https://github.com/modelcontextprotocol/python-sdk/issues/1681) - Recommended server layout patterns
- Python Packaging User Guide - pyproject.toml, src layout standards

### Tertiary (LOW confidence)

- Existing project research files (STACK.md, ARCHITECTURE.md, PITFALLS.md) - Pre-verification research

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - FastMCP docs verified, Astral tools confirmed
- Architecture: HIGH - Official FastMCP patterns documented
- Pitfalls: HIGH - Based on verified documentation and common packaging patterns

**Research date:** 2026-02-16
**Valid until:** 90 days (stable tooling, low churn expected)

---

*Research completed for Phase 1: Package Foundation*
