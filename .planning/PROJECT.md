# Vibraphone

## What This Is

Vibraphone is a standalone, installable MCP server for AI coding agents that enforces
disciplined software development workflows. It provides 18 MCP tools for task management
(via beads_rust), git worktree isolation, quality gate enforcement with circuit breakers,
LLM-powered code review, and project scaffolding.

## Core Value

Every code change goes through the quality gate (tests, lint, review) before it can be
committed — enforced by tooling, not by prompting.

## Requirements

### Validated

- ✓ Extract MCP server into installable Python package — v0.1.0
- ✓ Package installable via `uv tool install vibraphone` — v0.1.0
- ✓ `vibraphone` command starts FastMCP server — v0.1.0
- ✓ All tools function: task, worktree, quality gate, review, session, bridge, stack,
  scaffold — v0.1.0
- ✓ Worktree location configurable via vibraphone.yaml — v0.1.0
- ✓ `init_project` scaffolds vibraphone into existing projects — v0.1.0
- ✓ `check_prerequisites` detects dependencies with install commands — v0.1.0
- ✓ Session recovery runs on server startup — v0.1.0
- ✓ 413 tests (394 unit + 12 integration + 7 wheel) — v0.1.0
- ✓ Documentation: README, API reference, architecture docs — v0.1.0

### Active

### Slash Commands

- [ ] SLASH-01: Add /v commands for core workflow tools
- [ ] SLASH-02: Add /v commands for dict-heavy tools (init, configure-stack, import-plan)
- [ ] SLASH-03: Investigate stringification bug — root cause and fix
- [ ] SLASH-04: Documentation update for /v commands
- [ ] SLASH-05: `vibraphone setup-commands` CLI to install slash commands
- [ ] SLASH-06: Clean up existing artifacts (skills/v/, vibraphone-cli)

### Out of Scope

- PyPI publishing — v0.1.0 installs from git or local path
- Standalone CLI commands beyond MCP server entry point — all interaction through agents
- Full `triage` / `plan_parallel` implementation — stubs degrade gracefully without bv
- User-level config (`~/.config/vibraphone/`) — project-level vibraphone.yaml is sufficient
- CI/CD pipeline — defer to future

## Context

**Shipped v0.1.0** with 4,388 lines of Python across 18 MCP tools.

**Package structure:**

- `src/vibraphone/server.py` — FastMCP server entry point
- `src/vibraphone/config.py` — Configuration with Pydantic validation
- `src/vibraphone/tools/` — 6 tool modules (task, worktree, quality_gate, bridge, stack,
  scaffold)
- `src/vibraphone/utils/` — 9 utility modules
- `src/vibraphone/templates/` — 11 bundled Jinja2 templates for scaffolding
- `src/vibraphone/skills/v/` — Existing SKILL.md (to be cleaned up)
- `tests/` — 27 test files with 413 tests

**Key external dependencies:** FastMCP, beads_rust (br CLI), git, just, node/npx (for GSD),
instructor + OpenRouter (for LLM review).

## Current Milestone: v0.1.1 Slash Commands

**Goal:** Agents invoke vibraphone tools reliably via /v commands — no more serialization
guessing.

**Target features:**

- Slash commands for all workflow tools (core + dict-heavy)
- `vibraphone setup-commands` CLI installer
- Stringification bug investigation and fix
- Clean migration from existing skill-based approach

## Constraints

- **Package format**: Python package with `src/vibraphone/` layout, distributed via uv
- **Interface**: MCP-only — no CLI subcommands, single `vibraphone` entry point starts the
  server (exception: `setup-commands` for slash command installation)
- **Compatibility**: Works with existing vibraphone.yaml format from template projects
- **Dependencies**: br and bv are external binaries — detect-and-guide, not bundle
- **Scaffolding**: `init_project` generates files into user's project, not into the package
  itself

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Extract to standalone package (not template) | Templates can't be installed into existing projects, can't be updated cleanly | ✓ Good — clean `uv tool install` workflow |
| MCP-only interface (no CLI) | All interaction through coding agents; single entry point simplifies distribution | ✓ Good — 18 tools registered via decorators |
| Worktree default ~/.vibraphone/worktrees/ | Global location outside project dir reduces agent confusion | ✓ Good — configurable via vibraphone.yaml |
| Project-level config only (vibraphone.yaml) | Simplicity for v1; user-level defaults deferred | ✓ Good — works out of box |
| Detect-and-guide for br/bv | Bundling Rust binaries adds complexity | ✓ Good — `check_prerequisites` provides install commands |
| Review-before-commit enforcement | Quality gates block commits without approved review | ✓ Good — enforced by `attempt_commit` |
| Session-aware quality gates | Quality gates execute in worktree context when session active | ✓ Good — Phase 8 integration complete |
| Template bundling via hatchling artifacts | Templates must work after `pip install` | ✓ Good — verified by wheel content tests |
| Slash commands via `vibraphone setup-commands` | Explicit installation, bundled in package, global availability | — Pending |

---
*Last updated: 2026-02-18 after v0.1.1 milestone started*
