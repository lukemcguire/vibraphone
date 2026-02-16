# Domain Pitfalls

**Domain:** Python MCP server extraction / packaging
**Researched:** 2026-02-16

## Critical Pitfalls

Mistakes that cause rewrites or major issues.

### Pitfall 1: Hardcoded Relative Paths Survive Migration

**What goes wrong:** Existing code uses `./worktrees/`, `./docs/`, `./.vibraphone/` relative to the template project root. After extraction to an installed package, these paths resolve relative to the user's CWD — which is unpredictable (could be worktree dir, home dir, etc.).
**Why it happens:** Path assumptions are invisible until the server runs from a different location than where it was developed.
**Consequences:** Tools create files in wrong locations. Worktrees appear in random directories. Config files not found. Silent data loss if session.json written to wrong path.
**Prevention:** Audit every `Path(".")` and `os.path.join` in the codebase. Replace with config-derived paths. All paths must flow from either (a) vibraphone.yaml location (project root) or (b) `~/.vibraphone/` (global state). Add integration test that runs tools from a different CWD than project root.
**Detection:** grep for `"./`, `Path(".")`, `os.getcwd()` in source files.

### Pitfall 2: Package Data Not Included in Distribution

**What goes wrong:** Template files (AGENTS.md, CONSTITUTION.md, reviewer.md, etc.) exist in the source tree but aren't included in the built wheel. `init_project` fails with FileNotFoundError in production.
**Why it happens:** Python packaging requires explicit inclusion of non-Python files. `pyproject.toml` needs `[tool.hatch.build.targets.wheel]` or equivalent configuration to include template directories.
**Consequences:** `init_project` works in development (`pip install -e .`) but fails after `uv tool install` from built package.
**Prevention:** Use `importlib.resources` (not `__file__`-relative paths) to access bundled templates. Add a test that installs the built wheel in a clean venv and verifies all templates are accessible. Configure package data explicitly in pyproject.toml.
**Detection:** Build wheel, install in clean venv, call `init_project` — if it fails, package data config is wrong.

### Pitfall 3: Subprocess Calls Assume PATH Environment

**What goes wrong:** `subprocess.run(["br", ...])` works on developer machine where `br` is in PATH. After `uv tool install`, the server runs in an isolated environment where PATH may not include cargo bin, node_modules/.bin, etc.
**Why it happens:** `uv tool install` creates isolated environments. External CLIs (br, git, just, npx) must be on the system PATH, not the venv PATH.
**Consequences:** All tools that shell out fail silently or with cryptic "command not found" errors. User thinks vibraphone is broken.
**Prevention:** `check_prerequisites` should run on first tool call (not just when explicitly called). Each subprocess call should catch `FileNotFoundError` and return a helpful message naming the missing binary and install command. Never swallow subprocess errors.
**Detection:** Install vibraphone in a minimal environment without br/git/just and verify error messages are clear.

## Moderate Pitfalls

### Pitfall 4: Config Discovery Breaks in Worktrees

**What goes wrong:** vibraphone.yaml lives in project root. When agent is working in a worktree (`~/.vibraphone/worktrees/task-123/`), the CWD is the worktree — not the project root. Config discovery walks up the directory tree and fails (worktree parent is `~/.vibraphone/worktrees/`, not the project).
**Prevention:** Store project root in session state when `start_task` creates the worktree. Tools read project root from session, not from CWD. Alternatively, git worktrees share `.git` — use `git rev-parse --show-toplevel` on the main worktree to find project root.

### Pitfall 5: Entry Point Function Signature Wrong for FastMCP

**What goes wrong:** `[project.scripts] vibraphone = "vibraphone.server:main"` requires `main()` to be a synchronous entry point that starts the async server. FastMCP's startup may need specific invocation patterns (e.g., `mcp.run()` with stdio transport).
**Prevention:** Verify the exact FastMCP entry point pattern before migrating. Test that `vibraphone` command starts the server and responds to MCP protocol on stdio. Test early — this is the foundation everything else depends on.

### Pitfall 6: Template Files Conflict with Existing User Files

**What goes wrong:** `init_project` generates AGENTS.md, CLAUDE.md, Justfile, .gitignore entries. User already has these files. Overwriting loses their customizations. Skipping loses vibraphone setup.
**Prevention:** For each generated file, check if it exists first. For AGENTS.md/CLAUDE.md: fail if they exist and offer merge guidance. For Justfile: append recipes (don't overwrite). For .gitignore: append entries only if not already present. For .mcp.json: merge the server entry into existing config. Never silently overwrite.

### Pitfall 7: Async Context Issues in Tool Handlers

**What goes wrong:** FastMCP tool handlers are async. Subprocess calls (br, git, just) are blocking. Using `subprocess.run()` inside async handlers blocks the event loop, making the server unresponsive during long operations (test suites, code review).
**Prevention:** Use `asyncio.create_subprocess_exec` or run blocking calls via `asyncio.to_thread(subprocess.run, ...)`. The existing codebase may already handle this — verify during migration.

## Minor Pitfalls

### Pitfall 8: Version Pinning Too Tight or Too Loose

**What goes wrong:** Pinning `fastmcp==1.2.3` breaks when users have a different version. Using `fastmcp>=1.0` allows breaking changes.
**Prevention:** Use compatible release pins: `fastmcp~=1.2` (allows 1.2.x patches, blocks 1.3). Pin major+minor, allow patch.

### Pitfall 9: Test Imports Break After Restructuring

**What goes wrong:** Tests import `from tools.beads_tools import ...` — after moving to `src/vibraphone/tools/`, all imports change to `from vibraphone.tools.beads_tools import ...`. Easy to miss some.
**Prevention:** Migrate tests alongside source. Run full test suite after restructuring. Use `pytest --import-mode=importlib` to catch import issues early.

### Pitfall 10: Session State Format Incompatibility

**What goes wrong:** Existing `.vibraphone/session.json` format from template may not match what the standalone package expects. Users migrating from template get corrupt session state.
**Prevention:** Version the session format. Add a migration check on startup that upgrades old formats or warns about incompatibility.

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Package restructuring | Paths break (Pitfall 1), imports break (Pitfall 9) | Audit all paths, run tests from different CWD |
| Entry point setup | FastMCP invocation wrong (Pitfall 5) | Verify pattern early, test stdio transport |
| Template bundling | Package data missing (Pitfall 2) | Use importlib.resources, test from installed wheel |
| Tool migration | Subprocess PATH issues (Pitfall 3), async blocking (Pitfall 7) | Wrap all subprocess calls, use async subprocess |
| init_project | File conflicts (Pitfall 6) | Check-before-write, merge strategy per file type |
| Config system | Worktree discovery (Pitfall 4) | Store project root in session state |

## Sources

- Python Packaging User Guide (packaging.python.org)
- importlib.resources documentation (docs.python.org)
- Common Python packaging mistakes (training data, MEDIUM confidence)
- MCP server patterns (training data, LOW confidence — needs verification)
