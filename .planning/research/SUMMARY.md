# Project Research Summary

**Project:** Vibraphone MCP Server - v0.1.1 "Slash Commands" Milestone
**Domain:** Claude Code slash commands / MCP tool invocation
**Researched:** 2026-02-18
**Confidence:** HIGH

## Executive Summary

Vibraphone is a Python MCP server that enforces disciplined development workflows
via Claude Code. The v0.1.1 milestone focuses on making vibraphone tools reliably
invocable via `/v` slash commands, eliminating the serialization guessing game
that currently plagues complex parameter passing.

Research confirms that Claude Code slash commands are the correct mechanism (not
Agent Skills as previously attempted). Commands install to `~/.claude/commands/v.md`
as a single file that handles all `/v` subcommands via `$ARGUMENTS` parsing. The
critical finding is that ALL arguments arrive as strings - there is no native
dict/list passing. This requires either: (1) designing commands to take simple
primitive args and construct dicts inside the command body, or (2) using
AskUserQuestion for complex multi-field input.

The stringification pitfall is the primary risk. MCP tools expecting `dict`
params receive stringified JSON when commands pass complex arguments. The
solution is a multi-layer defense: clear v.md conventions, defensive parsing
in tools, and helpful error messages when type mismatches occur.

## Key Findings

### Recommended Stack (Slash Commands)

Single command file approach with subcommand routing via `$ARGUMENTS`.

**Core technologies:**
- **Slash Commands** (`~/.claude/commands/v.md`): User-invoked `/v` commands
- **Python 3.13+ / shutil**: Bundle and install command file via `vibraphone-cli`
- **importlib.resources**: Access bundled command from installed wheel

**Key stack changes from current:**
- Move from `skills/v/SKILL.md` (wrong) to `commands/v.md` (correct)
- Rename CLI subcommand from `skill install` to `setup-commands`
- Update pyproject.toml artifacts from `skills/` to `commands/`

### Expected Features

**Must have (table stakes) for v0.1.1:**
- `/v init` - Initialize vibraphone in project
- `/v configure-stack` - Configure component stack (simple args)
- `/v import-plan` - Import GSD phase into tasks (phase number as arg)
- `/v list|next|start|test|lint|format|commit|merge|complete` - Core workflow
- `/v status|health|recover|cleanup` - Session management
- `vibraphone setup-commands` CLI to install `/v` commands
- Clear MCP tool calling convention documented in v.md

**Should have (differentiators):**
- Argument hints in frontmatter (`argument-hint: <command> [args...]`)
- Defensive parsing in tools for dict parameters
- Helpful error messages when stringification detected

**Defer (v2+):**
- AskUserQuestion interactive flows for complex input
- Multi-stage command workflows
- Subagent spawning for parallel operations

### Architecture Approach

Single command file pattern with `$ARGUMENTS` subcommand routing.

**Major components:**
1. **`src/vibraphone/commands/v.md`**: Bundled command file with all `/v` docs
2. **`cli.py`**: `setup-commands` subcommand copies v.md to `~/.claude/commands/`
3. **MCP Tools**: No changes required - commands are pure documentation

**Key patterns:**
- Command body contains instructions for parsing `$ARGUMENTS`
- MCP tool calling convention clearly documented (objects, not strings)
- Cleanup of old `~/.claude/skills/v/` during install for migration

### Critical Pitfalls

1. **Dict/List Parameter Stringification** - Claude passes JSON as string, not
   object. Prevent with: convention docs + defensive parsing + helpful errors.
2. **Skill vs Command Confusion** - Skills are model-invoked, commands are
   user-invoked. Use `~/.claude/commands/` not `~/.claude/skills/`.
3. **MCP Tool Name Mismatch** - v.md tool names must match actual `@mcp.tool()`
   function names. Audit before release.
4. **Missing Restart After Install** - Users must restart Claude Code for
   commands to take effect. Document in install output.

## Implications for Roadmap

Based on research, suggested 3-phase structure:

### Phase 1: Command Infrastructure

**Rationale:** Establish correct installation mechanism before adding command
docs. Clean up existing incorrect skills/ installation.

**Delivers:** Working `/v` command infrastructure, CLI install command

**Addresses:** SLASH-05 (setup-commands CLI), SLASH-06 (cleanup)

**Tasks:**
- Create `src/vibraphone/commands/` directory
- Create `v.md` from existing `skills/v/SKILL.md` content
- Update `cli.py`: rename to `setup-commands`, change target path
- Update `pyproject.toml`: change artifacts from skills/ to commands/
- Remove obsolete `src/vibraphone/skills/` directory

**Avoids:** Pitfall 2 (skill vs command confusion)

### Phase 2: Command Documentation

**Rationale:** Document all `/v` commands with correct MCP tool calling
convention to prevent stringification bugs.

**Delivers:** Complete `/v` command reference in v.md

**Addresses:** SLASH-01, SLASH-02, SLASH-03 (documentation part)

**Tasks:**
- Document all core workflow commands (list, next, start, test, lint, format,
  review, commit, merge, cleanup, complete, recover, status, health)
- Document dict-heavy commands (init, configure-stack, import-plan) with
  explicit parameter handling guidance
- Add MCP Tool Calling Convention section with WRONG/RIGHT examples
- Add argument hints to frontmatter

**Avoids:** Pitfall 1 (stringification), Pitfall 3 (tool name mismatch)

### Phase 3: Tool Hardening

**Rationale:** Add defensive measures in MCP tools to catch and helpfully
report stringification issues.

**Delivers:** Robust tools that handle edge cases gracefully

**Addresses:** SLASH-03 (stringification fix)

**Tasks:**
- Add defensive parsing helper `_parse_maybe_json()` for dict params
- Add helpful error messages when string detected instead of dict
- Audit all tool names match v.md documentation
- Test with complex dict parameters

**Avoids:** Pitfall 1 (stringification) - second layer of defense

### Phase Ordering Rationale

- **Phase 1 first:** Cannot test commands without correct installation mechanism
- **Phase 2 second:** Commands must be documented before hardening makes sense
- **Phase 3 last:** Defensive parsing is backup, not primary solution

### Research Flags

Phases likely needing deeper research during planning:
- **None identified** - Research is comprehensive, official docs verified

Phases with standard patterns (skip research-phase):
- **Phase 1:** File copy, directory creation - standard Python patterns
- **Phase 2:** Documentation writing - clear requirements from FEATURES.md
- **Phase 3:** Defensive parsing - standard JSON handling patterns

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Verified against official Anthropic slash command docs |
| Features | HIGH | Clear requirements from SLASH-* items, GSD patterns analyzed |
| Architecture | HIGH | Single command file pattern well-documented |
| Pitfalls | HIGH | Stringification root cause identified, multi-layer defense designed |

**Overall confidence:** HIGH

### Gaps to Address

No significant gaps identified. Research covered:
- Official Anthropic documentation for slash commands and skills
- Existing vibraphone codebase (cli.py, server.py, skills/v/SKILL.md)
- GSD command patterns for argument handling examples
- FastMCP tool registration patterns

## Sources

### Primary (HIGH confidence)
- [Anthropic Docs - Slash Commands](https://docs.anthropic.com/en/docs/claude-code/slash-commands)
- [Anthropic Docs - Agent Skills](https://docs.anthropic.com/en/docs/claude-code/skills)
- Existing `src/vibraphone/cli.py` - source code analysis
- Existing `src/vibraphone/skills/v/SKILL.md` - current command documentation

### Secondary (MEDIUM confidence)
- GSD command implementations: `~/.claude/commands/gsd/*.md`
- FastMCP decorator patterns (training data + codebase verification)

### Tertiary (LOW confidence)
- None required - all findings verified against primary sources

---
*Research completed: 2026-02-18*
*Ready for roadmap: yes*
