# Research Summary: Vibraphone

**Domain:** Python MCP server extraction and packaging
**Researched:** 2026-02-16
**Overall confidence:** MEDIUM

## Executive Summary

Vibraphone is an existing MCP server (~4000 lines Python) being extracted from a template repository into a standalone installable package. The migration is primarily a packaging and architecture refactor — the core functionality already works.

The standard Python packaging stack (pyproject.toml with PEP 621, src layout, hatchling build backend) fits well. The main technical risks are path handling (hardcoded relative paths must become configurable), template bundling (non-Python files must be explicitly included in the wheel), and subprocess environment isolation (external CLIs must be on system PATH, not venv PATH).

The feature landscape is well-defined: table stakes are proper packaging, server lifecycle, config discovery, and documentation. The differentiators — quality gate enforcement, worktree isolation, LLM code review, circuit breakers — already exist in the codebase and just need to survive the migration intact.

Architecture follows standard Python package patterns: src/vibraphone/ layout with clear separation between server core, tool modules, utilities, and bundled templates. The build order is straightforward: package structure first, then server+config, then utilities, then tools, then scaffolding.

## Key Findings

**Stack:** pyproject.toml (PEP 621) + hatchling + src/vibraphone/ layout + FastMCP + importlib.resources for template bundling. Ruff/pytest already configured.
**Architecture:** Entry point → FastMCP server → tool modules → utilities → bundled templates. Config flows from vibraphone.yaml discovery. External CLIs called via async subprocess.
**Critical pitfall:** Hardcoded relative paths (./worktrees/, ./docs/) will silently break after extraction. Every path must derive from config or project root discovery.

## Implications for Roadmap

Based on research, suggested phase structure:

1. **Package Foundation** — src layout, pyproject.toml, entry point, basic server starts
   - Addresses: installability, entry point, server lifecycle
   - Avoids: Discovering packaging issues late (Pitfall 2, 5)

2. **Config & Utilities** — Config loading from vibraphone.yaml, path resolution, br_client, session management
   - Addresses: Foundation for all tools, path handling
   - Avoids: Hardcoded path breakage (Pitfall 1, 4)

3. **Tool Migration** — Move existing tools to new package structure, adapt imports and paths
   - Addresses: Bulk of existing functionality (beads, worktree, quality, review, session, bridge, stack)
   - Avoids: Import breakage (Pitfall 9), async issues (Pitfall 7)

4. **Scaffolding & New Tools** — init_project, check_prerequisites, template bundling
   - Addresses: New functionality for standalone package
   - Avoids: File conflicts (Pitfall 6), package data missing (Pitfall 2)

5. **Testing & Documentation** — Unit tests, integration tests, README, quickstart, tool reference
   - Addresses: Quality assurance, user onboarding
   - Avoids: Subprocess PATH issues caught late (Pitfall 3)

**Phase ordering rationale:**
- Package must be installable before anything else can be tested
- Config/utilities are shared by all tools — must exist before tool migration
- Tools are the bulk of the work but relatively mechanical (copy + adapt paths/imports)
- Scaffolding depends on package structure being finalized
- Tests and docs validate everything and should come last

**Research flags for phases:**
- Phase 1: Needs FastMCP entry point pattern verification (MEDIUM confidence)
- Phase 3: Session recovery has known bug — may need debugging during migration
- Phase 4: init_project file merging strategy needs careful design

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Standard Python packaging, well-established patterns |
| Features | MEDIUM | Clear scope from migration plan; MCP ecosystem survey incomplete |
| Architecture | HIGH | src layout + FastMCP decorator pattern well-understood |
| Pitfalls | HIGH | Path handling and packaging pitfalls are well-documented patterns |

## Gaps to Address

- FastMCP current API and entry point pattern (verify with official docs before Phase 1)
- uv tool install specific requirements (test early)
- Cross-platform worktree behavior (test on macOS if possible)
- LLM API client choice for code review tool (httpx vs openai SDK)
