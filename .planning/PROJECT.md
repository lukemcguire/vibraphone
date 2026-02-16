# Vibraphone

## What This Is

Vibraphone is a standalone, installable MCP server for AI coding agents that enforces disciplined software development workflows. It provides tools for task management (via beads_rust), git worktree isolation, TDD enforcement, LLM-powered code review, and circuit breakers. Agents interact with it exclusively through MCP tools — there is no standalone CLI beyond the server entry point.

## Core Value

Every code change goes through the quality gate (tests, lint, review) before it can be committed — enforced by tooling, not by prompting.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Extract existing MCP server (~4000 lines) from vibraphone-template into installable Python package
- [ ] Package installable via `uv tool install vibraphone`
- [ ] `vibraphone` command starts FastMCP server
- [ ] All existing tools function after migration (beads, worktree, quality gate, review, session, bridge, stack)
- [ ] Worktree location configurable via vibraphone.yaml (default: `~/.vibraphone/worktrees/`)
- [ ] `init_project` tool scaffolds vibraphone into existing projects (vibraphone.yaml, AGENTS.md, CLAUDE.md, Justfile recipes, .planning/vibraphone/ governance docs, .mcp.json registration)
- [ ] `check_prerequisites` tool detects br, bv, node/npx, git, just and reports missing deps with install commands
- [ ] `configure_stack` becomes reconfigure tool (init_project handles first-time setup)
- [ ] Session recovery runs automatically on MCP server startup when vibraphone.yaml detected
- [ ] Scaffolded governance files match existing templates (CONSTITUTION.md, ARCHITECTURE.md, GLOSSARY.md, DECISIONS.md, prompts/reviewer.md, specs/_TEMPLATE.md)
- [ ] Unit tests with mocks for tool logic
- [ ] Integration tests with real git/br for tool flows
- [ ] Documentation: README, quickstart guide, tool API reference, architecture docs

### Out of Scope

- PyPI publishing — v1 installs from git or local path
- Standalone CLI commands beyond the MCP server entry point — all interaction through agents
- Full `triage` / `plan_parallel` implementation — keep as stubs that degrade gracefully without bv
- User-level config (`~/.config/vibraphone/`) — project-level vibraphone.yaml is sufficient for v1
- Session recovery bug fix — known issue, debug post-migration
- CI/CD pipeline — defer to post-v1

## Context

The existing implementation lives in `vibraphone-template/.mcp/servers/vibraphone/` as an embedded MCP server within a project template repo. The template approach creates friction: users can't install vibraphone into existing projects, updates require manual merging, and the template conflates the tool with the project it manages.

The codebase is structured as:
- `server.py` — FastMCP server entry point
- `config.py` — Configuration loading from vibraphone.yaml
- `tools/` — Tool modules: beads_tools, bridge_tools, quality_tools, review_tools, session_tools, stack_tools, worktree_tools
- `utils/` — Shared utilities: br_client (beads_rust CLI wrapper), session (session state management)
- `tests/` — Unit tests for circuit breakers, review tools, session recovery, stitch integration

The server shells out to `br` (beads_rust) for task management and calls GSD via `npx` for planning integration. LLM-powered code review uses a configurable model and a reviewer prompt template checked against a project CONSTITUTION.md.

Key external dependencies: FastMCP, beads_rust (br CLI), git, just, node/npx (for GSD).

## Constraints

- **Package format**: Python package with `src/vibraphone/` layout, distributed via uv
- **Interface**: MCP-only — no CLI subcommands, single `vibraphone` entry point starts the server
- **Compatibility**: Must work with existing vibraphone.yaml format from template projects
- **Dependencies**: br and bv are external binaries — detect-and-guide, not bundle
- **Scaffolding**: `init_project` generates files into user's project, not into the package itself

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Extract to standalone package (not template) | Templates can't be installed into existing projects, can't be updated cleanly | — Pending |
| MCP-only interface (no CLI) | All interaction through coding agents; single entry point simplifies distribution | — Pending |
| Worktree default `~/.vibraphone/worktrees/` | Global location outside project dir reduces agent confusion from seeing worktree files | — Pending |
| Project-level config only (vibraphone.yaml) | Simplicity for v1; user-level defaults deferred | — Pending |
| Detect-and-guide for br/bv | Bundling Rust binaries adds complexity; `check_prerequisites` tells users how to install | — Pending |
| Governance files in `.planning/vibraphone/` | Keeps vibraphone scaffolding separate from GSD planning docs | — Pending |

---
*Last updated: 2026-02-16 after initialization*
