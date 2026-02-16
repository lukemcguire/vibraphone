# Vibraphone: Template to Standalone MCP Server Migration Plan

## Context

Vibraphone currently exists as a directory template (`vibraphone-template`) that
users clone to start projects. The MCP server, scaffolding files, test project,
and documentation all live in one repo. This creates friction: users can't
install vibraphone into an existing project, updates require manual merging, and
the template conflates the tool with the project it manages.

The goal is to extract vibraphone into a **standalone, installable Python
package** that users add to any project via `pip install vibraphone` +
`claude mcp add`. All interaction happens through MCP tools inside a coding
agent — no standalone CLI beyond the server entry point.

---

## Decisions Made

| Decision          | Choice                         | Rationale                                                                                                                        |
| ----------------- | ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------- |
| Distribution      | pip/uv package                 | MCP server is Python. User is most comfortable with Python/uv ecosystem.                                                         |
| Interface         | MCP-only (no CLI)              | All interaction through coding agent. Single entry point (`vibraphone`) starts FastMCP server.                                   |
| GSD integration   | Vibraphone wraps GSD           | Vibraphone is the primary tool. Calls GSD via `npx` internally for planning. Also works without GSD.                             |
| Beads dependency  | Bundle br + bv                 | Detect-and-guide: `check_prerequisites` tells users how to install if missing (`cargo install`).                                 |
| Scaffolding model | Generated into project         | `init_project` MCP tool generates vibraphone.yaml, AGENTS.md, CLAUDE.md, Justfile recipes, `.planning/vibraphone/` structure.    |
| Governance files  | All in `.planning/vibraphone/` | CONSTITUTION.md, ARCHITECTURE.md, GLOSSARY.md, DECISIONS.md, prompts/, specs/ — all live together under `.planning/vibraphone/`. |
| Worktree location | Configurable                   | Default location TBD, overridable via `vibraphone.yaml`. Worktrees outside project dir reduce agent confusion.                   |
| Session recovery  | Automatic on startup           | MCP server checks for `vibraphone.yaml` on startup. If found, checks for stale session. If no vibraphone.yaml, stays quiet.      |
| Testing           | Unit + integration             | Unit tests with mocks for logic. Integration tests with real git/br for tool flows.                                              |
| Documentation     | Full docs site                 | README, quickstart, detailed guides, API reference per tool, architecture docs.                                                  |
| Repo strategy     | New repo (`vibraphone`)        | vibraphone-template archived as reference. New repo is the active project.                                                       |
| Dog-fooding       | Phased                         | GSD for planning, manual migration for code restructuring, dog-food vibraphone for new features.                                 |

## Tool Changes

**New tools:**

| Tool                  | Purpose                                                                                                                                                                                                                                                                                           |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `init_project`        | Scaffolds vibraphone into existing project. Generates vibraphone.yaml, AGENTS.md, CLAUDE.md, Justfile recipes, `.planning/vibraphone/` directory with CONSTITUTION.md, ARCHITECTURE.md, GLOSSARY.md, DECISIONS.md, prompts/reviewer.md, specs/\_TEMPLATE.md. Registers MCP server in `.mcp.json`. |
| `check_prerequisites` | Detects br, bv, node/npx, git, just. Reports missing deps with install commands. Replaces bootstrap.sh.                                                                                                                                                                                           |

**Modified tools:**

| Tool              | Change                                                                                                      |
| ----------------- | ----------------------------------------------------------------------------------------------------------- |
| `configure_stack` | Becomes the "reconfigure" tool (init_project handles first-time setup).                                     |
| `start_task`      | Reads worktree path from vibraphone.yaml instead of hardcoded `./worktrees/`.                               |
| `recover_session` | Runs automatically on MCP server startup when vibraphone.yaml is detected. Also available as explicit tool. |

**Unchanged tools (migrate as-is):** `list_tasks`, `next_ready`,
`complete_task`, `abandon_task`, `health_check`, `get_task_context`, `add_task`,
`merge_task`, `cleanup_task`, `run_tests`, `run_lint`, `run_format`,
`request_code_review`, `attempt_commit`, `import_gsd_plan`

**Kept as future stubs:** `triage`, `plan_parallel` — require `bv` for
multi-agent parallel execution. Keep but gracefully degrade when bv not
installed. Full implementation deferred until multi-subagent workflows are
viable.

**Known bugs to fix post-migration:** Session recovery flow needs debugging (not
working reliably in current template).

---

## Execution Approach

### Phase A: Planning (GSD)

1. Create the new `vibraphone` repo
2. Run `/gsd:new-project` using the GSD prompt guidance below
3. GSD produces PROJECT.md, REQUIREMENTS.md, ROADMAP.md

### Phase B: Manual Migration

1. Restructure `.mcp/servers/vibraphone/` into a proper Python package
   (`src/vibraphone/`)
2. Add `pyproject.toml` with pip/uv distribution config and `[project.scripts]`
   entry point
3. Extract hardcoded paths into configuration (worktree location, .planning
   paths)
4. Move scaffolding templates into the package (for `init_project` to generate)
5. Get `vibraphone` command starting the MCP server from the installed package
6. Migrate existing tests, adapt for new package structure

### Phase C: New Features (Dog-food vibraphone)

1. Point Claude Code at the standalone vibraphone MCP server
2. Build `init_project` tool using vibraphone's own TDD loop
3. Build `check_prerequisites` tool
4. Make worktree location configurable
5. Add GSD wrapping (planning tools that delegate to npx)
6. Write documentation
7. Set up CI/CD for the package

---

## Files Generated by `init_project`

When an agent calls `init_project` in a user's project:

```plaintext
project-root/
├── vibraphone.yaml                          # Project genome (components, quality gates, etc.)
├── AGENTS.md                                # Agent behavioral contract
├── CLAUDE.md                                # Claude Code entrypoint → points to AGENTS.md
├── Justfile                                 # Recipes appended (or created if none exists)
├── .mcp.json                                # MCP server entry added (or created)
├── .planning/
│   └── vibraphone/
│       ├── CONSTITUTION.md                  # Project coding rules
│       ├── ARCHITECTURE.md                  # Mermaid diagrams
│       ├── GLOSSARY.md                      # Domain terms
│       ├── DECISIONS.md                     # ADRs
│       ├── prompts/
│       │   └── reviewer.md                  # Code review LLM prompt
│       └── specs/
│           └── _TEMPLATE.md                 # Manual spec template
├── .vibraphone/                             # Runtime state (gitignored)
└── .gitignore                               # Entries appended for .vibraphone/, worktrees
```

---

## Verification

After the migration is complete, verify:

1. **Install:** `pip install -e .` (or `uv pip install -e .`) succeeds
2. **Server starts:** `vibraphone` command starts FastMCP server without errors
3. **MCP registration:** `claude mcp add vibraphone -- vibraphone` works
4. **Init:** Agent calls `init_project` and correct files are generated
5. **Prerequisites:** Agent calls `check_prerequisites` and gets accurate report
6. **Full workflow:** `start_task` → `run_tests` → `run_lint` →
   `request_code_review` → `attempt_commit` → `merge_task` → `cleanup_task` →
   `complete_task` works end-to-end
7. **Tests pass:** `uv run pytest` passes all unit and integration tests
8. **No vibraphone.yaml = quiet:** MCP server starts in a non-vibraphone project
   without interfering
