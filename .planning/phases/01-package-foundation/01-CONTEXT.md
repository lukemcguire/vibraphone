# Phase 1: Package Foundation - Context

**Gathered:** 2026-02-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Package is installable and server starts. This phase delivers the foundational Python package structure with proper src layout, installable via uv/pip, with a working FastMCP server entry point. All existing functionality (tools, config, utilities) is preserved but organized as a proper package.

</domain>

<decisions>
## Implementation Decisions

### Package Structure
- Mirror existing structure: `server.py`, `config.py`, `tools/`, `utils/` under `src/vibraphone/`
- Tests in root `tests/` directory (outside package, standard convention)
- MCP-server-only: no Python library API for `import vibraphone` — all interaction via MCP tools
- Separate files for each tool module (beads_tools.py, quality_tools.py, etc.)
- Template files bundled in package, accessible via `importlib.resources` (for Phase 7 scaffolding)

### Entry Point Behavior
- Follow FastMCP docs pattern for entry point (not existing template pattern)
- Log to stderr for debugging (not silent, not file-based)
- Lazy config loading: vibraphone.yaml loads when first tool needs it, not on startup
- Session recovery deferred to Phase 4 (Phase 1 server starts without config)
- Claude's Discretion: error handling on startup failure

### Dependencies
- Python 3.13+ (latest stable)
- `pyproject.toml` only — no requirements.txt
- Dev dependencies in `[project.optional-dependencies] dev`
- FastMCP pinned to specific version for stability
- External binaries (br, bv, git, just, node/npx) not declared as deps — detect-and-guide via `check_prerequisites` tool

### Development Workflow
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

</decisions>

<specifics>
## Specific Ideas

- "MCP-server-only doesn't preclude scaffolding, slash-commands, etc." — all tools work via MCP, no Python import API needed
- Keep toolchain consistent with Astral ecosystem (uv, ruff, ty)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-package-foundation*
*Context gathered: 2026-02-16*
