# Phase 11: Command Documentation - Context

**Gathered:** 2026-02-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Document all `/v` slash commands in v.md with correct MCP tool calling convention.
Covers core workflow commands (list, next, start, test, lint, format, review,
commit, merge, cleanup, complete, recover, status, health) and dict-heavy commands
(init, configure-stack, import-plan). Adding new commands or changing MCP tool
behavior is out of scope.

</domain>

<decisions>
## Implementation Decisions

### Command Organization

- **4 workflow stage groups:**
  1. Start Work (list, next, start)
  2. Run Quality (test, lint, format, review)
  3. Commit & Merge (commit, merge, cleanup, complete)
  4. Session Management (status, health, recover)
- Each section has a brief intro paragraph, then commands as H3 headings
- Clean, scannable structure

### Example Depth

- **Full coverage** for each command: typical scenarios + edge cases + common
  mistakes
- Comprehensive documentation that teaches, not just references
- Examples should help users understand both what works and what doesn't

### Parameter Guidance

- **Dual approach:** Inline examples for dict-heavy commands + general reference
  section explaining dict parameter handling patterns
- Dict-heavy commands (init, configure-stack, import-plan) get special attention
- Users can copy-paste and modify examples directly

### Error Documentation

- **Dual approach:** Dedicated troubleshooting section for common errors + inline
  command-specific errors where relevant
- Troubleshooting section covers:
  - Quality gate failures (test/lint failures, how to resolve)
  - Worktree issues (merge conflicts, uncommitted changes)
- Command-specific errors documented with their respective commands

### Claude's Discretion

- Quick reference table at document start (yes/no, format)
- Example format (plain code blocks, commented, or input/output pairs)
- Number of examples per command (fixed or variable by complexity)
- Whether examples include error cases
- Stringification pitfall documentation approach (WRONG/RIGHT examples vs text)
- Whether to include MCP tool function names for auditability
- Error documentation format (structured vs FAQ style)

</decisions>

<specifics>
## Specific Ideas

- "Full coverage" documentation - user wants comprehensive reference that
  teaches, not just lists commands
- Dual approaches favored (inline + reference section) for parameters and errors
- 4-group workflow organization mirrors how users actually work through tasks

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope.

</deferred>

---

*Phase: 11-command-documentation*
*Context gathered: 2026-02-19*
