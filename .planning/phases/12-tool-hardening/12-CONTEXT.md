# Phase 12: Tool Hardening - Context

**Gathered:** 2026-02-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Add defensive parsing to MCP tools so they gracefully handle when Claude passes
dict/list arguments as JSON strings. Focus on known problematic tools only.
This is a hardening phase — no new features, just making existing tools more
resilient to the stringification bug.

</domain>

<decisions>
## Implementation Decisions

### Defensive parsing approach
- **Error, not auto-parse**: When a dict parameter is received as a JSON string,
  the tool returns an error with examples — it does NOT silently parse
- **Explicit over seamless**: Forces agents to learn the correct calling convention
  rather than hiding the underlying issue

### Error messaging
- **Table format from v.md**: Use the same WRONG vs RIGHT table format that
  agents see in the slash command documentation
- **Include received value**: Show exactly what was received (the JSON string)
- **Include correct example**: Show what the MCP call should look like
- **Suggest fix action**: Direct instruction like "Remove the quotes around
  the object"
- **No docs link**: Keep error message self-contained with examples

### Scope of hardening
- **Known problematic tools only**: Focus on the three dict-heavy tools
- **Parameters to harden**:
  - `init_project` → `values` parameter
  - `configure_stack` → `components` parameter
  - `request_code_review` → `files` parameter
- **Implementation**: Inline checks at the top of each tool function
  (no decorator or shared utility needed for just 3 tools)

### Testing strategy
- **Unit tests in existing files**: Add tests to the existing tool test files
  (not a new dedicated test file)
- **Test cases per hardened parameter**:
  - Valid JSON string → returns error with WRONG/RIGHT examples
  - Invalid JSON string → returns error (graceful, not crash)
  - Correct dict → success (normal operation)
  - Null/None value → success (parameter is optional)
- **Verify error format**: Tests should assert error message contains
  "WRONG" and "RIGHT" text

### Claude's Discretion
- Exact error message wording (within the format constraints above)
- Truncation of long received values in error messages
- Whether to include parameter name in error or infer from context

</decisions>

<specifics>
## Specific Ideas

- Error message should mirror the v.md "MCP Tool Calling Convention" section
  for consistency — agents already see that pattern in documentation
- The goal is education: agents should see the error, understand the fix,
  and not make the same mistake again

</specifics>

<deferred>
## Deferred Ideas

- Auto-parse with warning (decided against — prefer explicit errors)
- Decorator-based approach (deferred — over-engineering for 3 tools)
- Hardening all dict/list params (deferred — focus on known problematic ones)
- Integration tests with simulated Claude behavior (deferred — unit tests
  sufficient for this phase)

</deferred>

---

*Phase: 12-tool-hardening*
*Context gathered: 2026-02-19*
