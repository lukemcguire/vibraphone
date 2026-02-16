# Technology Stack

**Project:** Vibraphone MCP Server
**Researched:** 2026-02-16
**Confidence:** MEDIUM (verification limited - no web access for current docs)

## Executive Summary

For a Python MCP server distributed via `uv tool install`, the standard 2025/2026 stack centers on:
- **pyproject.toml** (PEP 621) for all metadata
- **Hatchling** or **setuptools** for build backend
- **src/vibraphone/** layout for package structure
- **[project.scripts]** for CLI entry points
- **FastMCP** for MCP protocol implementation
- **Ruff** for linting/formatting (replacing black, flake8, isort)
- **pytest** for testing

The stack prioritizes modern Python packaging standards (PEP 621, PEP 517/518), developer experience via uv tooling, and minimal dependency bloat.

---

## Recommended Stack

### Build System & Packaging

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| pyproject.toml (PEP 621) | - | Single source of truth for project metadata | Standard since Python 3.11+. Replaces setup.py, setup.cfg. All modern tools read this. |
| Hatchling | latest | Build backend | MEDIUM confidence. Fast, modern, zero-config for simple packages. Already in current pyproject.toml. Alternative: setuptools (more mature, wider adoption). |
| uv | 0.5+ | Package manager & tool installer | HIGH confidence. Fast Rust-based pip replacement. Native `uv tool install` support is the deployment target. |

**Rationale for Hatchling:** Current pyproject.toml uses it. Hatchling is simpler than setuptools for pure-Python packages with straightforward builds. However, **setuptools has wider ecosystem adoption** if compatibility is critical.

**Flag for validation:** Verify Hatchling vs setuptools for MCP server context. FastMCP documentation may have recommendations.

### Core Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| FastMCP | latest | MCP protocol server implementation | HIGH confidence. Purpose-built for MCP servers in Python. Handles stdio transport, tool registration, server lifecycle. |
| Python | >=3.13 | Runtime | HIGH confidence. Already specified in pyproject.toml. Modern async/await, type hints, pattern matching. |

**Note:** Current pyproject.toml shows `requires-python = ">=3.13"` but `dependencies = []`. FastMCP **must** be added to dependencies.

### Project Structure

| Component | Path | Purpose | Why |
|-----------|------|---------|-----|
| Source layout | src/vibraphone/ | Package code | HIGH confidence. Import isolation, prevents accidental imports of local files during development. Recommended by PyPA. |
| Entry point | [project.scripts] | CLI command registration | HIGH confidence. Standard for `uv tool install`. Maps `vibraphone` command to server entry point. |
| Tests | tests/ | Test suite | HIGH confidence. Standard pytest discovery location. |
| Configuration | pyproject.toml | All config centralized | HIGH confidence. Ruff, pytest, coverage all configured here. |

### Development Tools

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Ruff | latest | Linting & formatting | HIGH confidence. 10-100x faster than flake8/black. Replaces: black, isort, flake8 + plugins. Already configured extensively in pyproject.toml. |
| pytest | latest | Testing framework | HIGH confidence. Standard Python test framework. Already configured. |
| pytest-cov | latest | Coverage reporting | MEDIUM confidence. Standard coverage tool for pytest. |
| mypy or pyright | latest | Type checking | MEDIUM confidence. pyproject.toml has `[tool.ty.environment]` (unclear what "ty" is - may need clarification). Recommend pyright (faster) or mypy (more mature). |

**Current state:** pyproject.toml has extensive Ruff configuration (50+ rules enabled). This is good - keep it.

**Flag for validation:** `[tool.ty.environment]` in current pyproject.toml is unclear. Verify what "ty" is. Standard options: mypy, pyright, or Pyre.

### Runtime Dependencies (to be added)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| FastMCP | latest | MCP server framework | Required. Core dependency. |
| pyyaml | latest | Parse vibraphone.yaml | Required. Config file is YAML. |
| httpx | latest | HTTP client for LLM APIs | Required. Code review calls OpenAI-compatible APIs. Use httpx (async) not requests (sync). |
| pydantic | v2 | Config validation | Recommended. Type-safe config parsing. FastMCP may already pull this in. |

**Note:** Current `dependencies = []` is incorrect. These must be added.

### External CLI Dependencies (not in PyPI)

Vibraphone shells out to external tools. These are **not** Python dependencies.

| Tool | Install Method | Detection Strategy |
|------|----------------|-------------------|
| br (beads_rust) | `cargo install beads_rust` | `check_prerequisites` tool detects, guides install |
| bv (beads_rust) | `cargo install beads_rust` | Optional. Graceful degradation if missing. |
| git | System package manager | Assume present (universal developer tool) |
| just | System package manager or cargo | `check_prerequisites` detects |
| node/npx | System package manager | For GSD integration. `check_prerequisites` detects |

**Architecture decision:** Detect-and-guide, not bundle. Vibraphone reports missing tools via `check_prerequisites` and provides install commands. Does NOT bundle binaries or auto-install.

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Build backend | Hatchling | setuptools | Setuptools is more mature and widely adopted, but Hatchling is simpler for pure-Python. MEDIUM confidence - may prefer setuptools for stability. |
| Build backend | Hatchling | Poetry | Poetry is a full workflow tool (combines pip + venv + build). Vibraphone targets uv ecosystem. Poetry's build backend (poetry-core) adds complexity. |
| Linter/formatter | Ruff | black + flake8 + isort | Ruff consolidates 3+ tools into one, 10-100x faster. Already configured in project. |
| HTTP client | httpx | requests | httpx supports async (FastMCP is async). requests is sync-only. |
| Type checker | pyright/mypy | None | Type checking is valuable for 4000 line codebase. Current config unclear (tool.ty). |
| Config format | YAML (vibraphone.yaml) | TOML | YAML is already chosen. TOML is more Pythonic but YAML is more human-friendly for nested structures. |

---

## Package Structure

```
vibraphone/
├── pyproject.toml              # PEP 621 metadata, dependencies, tool config
├── README.md                   # PyPI description
├── LICENSE                     # Required for PyPI
├── src/
│   └── vibraphone/
│       ├── __init__.py         # Package entry, version
│       ├── server.py           # FastMCP server entry point
│       ├── tools/              # MCP tools (start_task, etc.)
│       ├── utils/              # Shared utilities
│       └── templates/          # Files for init_project to generate
├── tests/
│   ├── unit/                   # Unit tests with mocks
│   └── integration/            # Integration tests with real git/br
└── .python-version             # Python version for tooling
```

**Current issue:** pyproject.toml has:
```toml
[tool.hatch.build.targets.wheel]
packages = ["config.py", "server.py", "tools", "utils"]
```

This is **flat layout** (files at repo root). Need to migrate to **src/vibraphone/** layout.

**Migration required:**
1. Create `src/vibraphone/` directory
2. Move `config.py`, `server.py`, `tools/`, `utils/` into it
3. Update `[tool.hatch.build.targets.wheel]` to `packages = ["src/vibraphone"]` OR remove (Hatchling auto-discovers src/ layout)
4. Add `[project.scripts]` entry point

---

## pyproject.toml Configuration

### Required Additions

```toml
[project]
name = "vibraphone"
version = "0.1.0"
description = "MCP server for AI coding agents that enforces disciplined software development workflows"
readme = "README.md"
requires-python = ">=3.13"
license = {text = "MIT"}  # or appropriate license
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
keywords = ["mcp", "mcp-server", "ai-agents", "tdd", "workflow"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3.13",
]

dependencies = [
    "fastmcp>=0.1.0",      # Version TBD - check FastMCP releases
    "pyyaml>=6.0",
    "httpx>=0.27.0",
    "pydantic>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=4.1",
    "pytest-asyncio>=0.23",  # FastMCP is async
    "ruff>=0.2",
]

[project.scripts]
vibraphone = "vibraphone.server:main"  # Entry point for `uv tool install vibraphone`

[project.urls]
Homepage = "https://github.com/yourusername/vibraphone"
Documentation = "https://github.com/yourusername/vibraphone#readme"
Repository = "https://github.com/yourusername/vibraphone"
Issues = "https://github.com/yourusername/vibraphone/issues"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

# Remove [tool.hatch.build.targets.wheel] if using src/ layout
# Hatchling auto-discovers src/vibraphone/
```

### Entry Point Implementation

In `src/vibraphone/server.py`:

```python
def main() -> None:
    """Entry point for vibraphone MCP server."""
    # FastMCP server startup logic
    # This is what runs when user executes `vibraphone` command
    pass

if __name__ == "__main__":
    main()
```

---

## Installation Workflows

### Developer Installation (Editable)

```bash
# Clone repo
git clone https://github.com/yourusername/vibraphone.git
cd vibraphone

# Install with uv
uv pip install -e ".[dev]"

# Or traditional pip
pip install -e ".[dev]"

# Run tests
uv run pytest

# Start server manually
vibraphone
```

### End-User Installation (uv tool install)

```bash
# Install as isolated tool
uv tool install vibraphone

# Register with Claude Code MCP
claude mcp add vibraphone -- vibraphone

# Tool now available in Claude Code
# Agent calls init_project, start_task, etc.
```

### Publishing to PyPI

```bash
# Build distribution
uv build

# Upload to PyPI (requires account + token)
uv publish
```

**Note:** `uv build` and `uv publish` are MEDIUM confidence. Verify uv has these commands (may be `python -m build` + `twine upload` if uv doesn't provide).

---

## Dependency Version Strategy

| Dependency Type | Pin Strategy | Rationale |
|-----------------|-------------|-----------|
| Python | `>=3.13` | Minimum version. Allows newer. User controls runtime. |
| Direct deps | Minimum + caret (`>=X.Y`) | Allow patch updates. Avoid breaking changes. |
| Dev deps | Minimum + caret (`>=X.Y`) | Flexibility for developers. |
| Lockfile | Yes (uv.lock or requirements.txt) | Reproducible dev environments. |

**For FastMCP:** Check if FastMCP has API stability guarantees. If pre-1.0, may need tighter pinning (`>=0.1,<0.2`).

---

## Testing Stack

### Test Organization

```
tests/
├── unit/
│   ├── test_config.py          # Config parsing, validation
│   ├── test_tools.py           # Tool logic with mocks
│   └── test_utils.py           # Utility functions
├── integration/
│   ├── test_task_workflow.py   # Full workflow: start → complete
│   ├── test_git_ops.py         # Real git operations
│   └── test_br_ops.py          # Real beads_rust operations
└── conftest.py                 # Shared fixtures
```

### Test Dependencies

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=4.1",
    "pytest-asyncio>=0.23",       # FastMCP tools are async
    "pytest-mock>=3.12",          # Mock external processes
    "pytest-timeout>=2.2",        # Prevent hanging tests
]
```

### Test Execution

```bash
# All tests
uv run pytest

# Unit tests only (fast)
uv run pytest tests/unit

# Integration tests (slower, requires git/br)
uv run pytest tests/integration

# Coverage report
uv run pytest --cov=src/vibraphone --cov-report=html
```

---

## Anti-Patterns to Avoid

### 1. Bundling External Binaries
**Why avoid:** Increases package size, platform-specific nightmares, security concerns.
**Instead:** Detect-and-guide via `check_prerequisites`. Users install br/bv/git/just via their system package managers.

### 2. Flat Layout (files at repo root)
**Why avoid:** Import pollution, accidental test imports, harder to package.
**Instead:** src/vibraphone/ layout. Already recommended by PyPA.

### 3. setup.py/setup.cfg
**Why avoid:** Deprecated. pyproject.toml (PEP 621) is the standard since Python 3.11+.
**Instead:** All metadata in pyproject.toml.

### 4. Hardcoded Paths
**Why avoid:** Breaks when installed as package vs local dev.
**Instead:** Use `importlib.resources` for package data, vibraphone.yaml for user-configurable paths.

### 5. Synchronous HTTP Client (requests)
**Why avoid:** FastMCP is async. Blocking calls in async context cause issues.
**Instead:** httpx (async HTTP client).

### 6. Auto-Installation of External Tools
**Why avoid:** Security risk, sudo requirements, user environment violations.
**Instead:** Detect + report missing tools. User installs via cargo/npm/apt.

---

## Configuration Management

### vibraphone.yaml (per-project, user-created)

```yaml
# User's project configuration
worktree_location: ../vibraphone-worktrees  # Configurable
components:
  - name: server
    path: src/server
quality_gates:
  - tests_pass
  - lint_clean
  - review_approved
llm:
  base_url: https://api.openai.com/v1
  model: gpt-4
  api_key_env: OPENAI_API_KEY
```

**Location:** Project root (where user calls `init_project`).
**Parsing:** pyyaml + pydantic for validation.
**Discovery:** On MCP server startup, check for vibraphone.yaml in cwd. If present, load config. If absent, stay quiet (not a vibraphone project).

### Package Defaults (embedded in vibraphone package)

Store default templates in `src/vibraphone/templates/`:
- CONSTITUTION.md
- ARCHITECTURE.md
- AGENTS.md
- CLAUDE.md
- etc.

`init_project` tool copies these into user's `.planning/vibraphone/`.

**Access templates:** Use `importlib.resources` or `importlib.metadata.files()` to read package data at runtime.

---

## CI/CD Considerations

### GitHub Actions Workflow (example)

```yaml
name: Test & Lint
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - run: uv pip install -e ".[dev]"
      - run: uv run pytest --cov
      - run: uv run ruff check

  publish:
    if: startsWith(github.ref, 'refs/tags/')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - run: uv build
      - run: uv publish
    env:
      UV_PUBLISH_TOKEN: ${{ secrets.PYPI_TOKEN }}
```

**Note:** `uv build` and `uv publish` syntax is MEDIUM confidence. Verify uv documentation.

---

## Migration Checklist

From current state (flat layout, no dependencies) to production-ready package:

- [ ] Create src/vibraphone/ directory structure
- [ ] Move config.py, server.py, tools/, utils/ into src/vibraphone/
- [ ] Add `__init__.py` files (make it a package)
- [ ] Update pyproject.toml:
  - [ ] Add dependencies (fastmcp, pyyaml, httpx, pydantic)
  - [ ] Add dev dependencies (pytest-asyncio, pytest-mock)
  - [ ] Add [project.scripts] entry point
  - [ ] Add license, authors, URLs
  - [ ] Remove/fix [tool.hatch.build.targets.wheel]
- [ ] Clarify [tool.ty.environment] (what is "ty"? Use mypy or pyright)
- [ ] Create templates/ directory in package for init_project
- [ ] Implement server.py main() entry point
- [ ] Update tests for new import paths (vibraphone.tools.X not tools.X)
- [ ] Add importlib.resources for template access
- [ ] Test `uv pip install -e .`
- [ ] Test `vibraphone` command starts server
- [ ] Test `uv tool install .` (local install)
- [ ] Write README.md for PyPI
- [ ] Add LICENSE file
- [ ] Verify FastMCP version compatibility

---

## Open Questions & Validation Needed

| Question | Confidence | Action |
|----------|------------|--------|
| FastMCP latest version & API stability | LOW | Check FastMCP docs/releases. May need version pinning if pre-1.0. |
| Hatchling vs setuptools for MCP context | MEDIUM | Verify FastMCP examples. May prefer setuptools for ecosystem consistency. |
| [tool.ty.environment] in pyproject.toml | LOW | What is "ty"? Replace with mypy or pyright config. |
| uv build/publish commands | MEDIUM | Verify uv documentation. May need python -m build + twine. |
| FastMCP async requirements | MEDIUM | Verify if FastMCP tools must be async. Affects pytest-asyncio necessity. |
| Minimum Python version (3.13 vs 3.11+) | MEDIUM | 3.13 is very recent. Consider 3.11+ for wider adoption unless 3.13 features required. |

---

## Confidence Assessment

| Area | Level | Reason |
|------|-------|--------|
| pyproject.toml (PEP 621) | HIGH | Standard since Python 3.11+, well-documented |
| src/ layout | HIGH | PyPA recommendation, industry standard |
| Ruff for linting | HIGH | Current in project, widely adopted |
| pytest framework | HIGH | Industry standard |
| httpx for async HTTP | HIGH | Standard async HTTP client |
| FastMCP specifics | LOW | Cannot verify current API, version, conventions |
| Hatchling vs setuptools | MEDIUM | Both valid, need FastMCP context |
| uv tool install details | MEDIUM | uv is newer, need current docs |
| [tool.ty] config | LOW | Unknown tool, needs investigation |

**Overall confidence: MEDIUM** - Core Python packaging practices are solid, but FastMCP-specific details and uv tooling details need verification with current documentation.

---

## Sources

**Verified:**
- Existing pyproject.toml (read from project)
- migration-plan.md (read from project)
- Python packaging PEPs (621, 517, 518) - established standards

**Needs verification (no web access):**
- FastMCP current version, API, examples
- uv tool install specifics (uv is newer tool, <2 years old)
- Hatchling vs setuptools for MCP servers
- [tool.ty.environment] purpose
- Current Python version adoption (3.13 vs 3.11)

**Research limitations:** Unable to access Context7, official documentation, or web search. Recommendations based on established Python packaging standards (high confidence) and FastMCP/uv understanding from training data (low-medium confidence, flagged for validation).
