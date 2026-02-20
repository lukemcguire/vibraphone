# Phase 12: Tool Hardening - Research

**Researched:** 2026-02-19
**Domain:** Defensive type checking for MCP tool parameters
**Confidence:** HIGH

## Summary

This phase adds defensive parsing checks to three MCP tools that receive dict/list
parameters which Claude sometimes passes as JSON strings instead of native objects.
The solution is inline type checking at the start of each affected tool function,
returning an educational error message with WRONG/RIGHT examples that mirror the
v.md documentation format.

**Primary recommendation:** Add inline `isinstance(param, str)` checks at the start
of `init_project`, `configure_stack`, and `request_code_review` functions. When a
string is detected, return a dict with `error_type: "ParameterStringified"` and a
table-formatted error message with examples.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Error, not auto-parse**: When a dict parameter is received as a JSON string,
  the tool returns an error with examples -- it does NOT silently parse
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
  - `init_project` -> `values` parameter
  - `configure_stack` -> `components` parameter
  - `request_code_review` -> `files` parameter
- **Implementation**: Inline checks at the top of each tool function
  (no decorator or shared utility needed for just 3 tools)

### Testing strategy

- **Unit tests in existing files**: Add tests to the existing tool test files
  (not a new dedicated test file)
- **Test cases per hardened parameter**:
  - Valid JSON string -> returns error with WRONG/RIGHT examples
  - Invalid JSON string -> returns error (graceful, not crash)
  - Correct dict -> success (normal operation)
  - Null/None value -> success (parameter is optional)
- **Verify error format**: Tests should assert error message contains
  "WRONG" and "RIGHT" text

### Claude's Discretion

- Exact error message wording (within the format constraints above)
- Truncation of long received values in error messages
- Whether to include parameter name in error or infer from context

### Deferred Ideas (OUT OF SCOPE)

- Auto-parse with warning (decided against -- prefer explicit errors)
- Decorator-based approach (deferred -- over-engineering for 3 tools)
- Hardening all dict/list params (deferred -- focus on known problematic ones)
- Integration tests with simulated Claude behavior (deferred -- unit tests
  sufficient for this phase)

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SLASH-03 | Stringification bug is investigated, root cause identified, and fixed or documented | Defensive parsing adds the "fix" layer -- when Claude passes a stringified value, tools now provide educational error messages that guide agents to correct behavior |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.11+ | Runtime | Project uses modern Python features |
| FastMCP | (existing) | MCP framework | All tools use @mcp.tool decorator |
| Pydantic | (existing) | Data validation | TaskError model uses Pydantic |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| json | stdlib | JSON parsing | Detecting if string is valid JSON |
| typing | stdlib | Type hints | `dict[str, Any]`, `list[str]`, etc. |

**No new installation required** - all dependencies are already in the project.

## Architecture Patterns

### Recommended Implementation Structure

```text
src/vibraphone/tools/
├── scaffold_tools.py    # Add check for `values` param
├── stack_tools.py       # Add check for `components` param
└── quality_gate_tools.py # Add check for `files` param

tests/
├── test_scaffold_tools.py  # Add defensive parsing tests
├── test_stack_tools.py     # Add defensive parsing tests
└── test_quality_gate_tools.py # Add defensive parsing tests
```

### Pattern: Inline Type Guard with Educational Error

**What:** At the start of each tool function, check if the problematic parameter
is a string. If so, return an error dict with table-formatted guidance.

**When to use:** For dict/list parameters that Claude may stringify.

**Example:**

```python
# At the top of init_project function
@mcp.tool
async def init_project(
    project_path: str | None = None,
    values: dict[str, Any] | None = None,
    *,
    preview: bool = True,
) -> dict[str, Any]:
    # Defensive check for stringified values parameter
    if values is not None and isinstance(values, str):
        return _build_stringification_error(
            param_name="values",
            received=values,
            example_wrong='values: "{\\"language\\": \\"go\\"}"',
            example_right='values: {"language": "go"}',
        )
    # ... rest of function

def _build_stringification_error(
    param_name: str,
    received: str,
    example_wrong: str,
    example_right: str,
) -> dict[str, Any]:
    """Build educational error for stringified parameter.

    Mirrors the WRONG/RIGHT table format from v.md documentation.
    """
    # Truncate long values for readability
    display_value = received if len(received) <= 100 else received[:97] + "..."

    return {
        "status": "error",
        "error_type": "ParameterStringified",
        "message": f"""Parameter `{param_name}` received as a JSON string
instead of a native object.

| WRONG                          | RIGHT                        |
| ------------------------------ | ---------------------------- |
| `{example_wrong}` | `{example_right}` |

Remove the quotes around the object.""",
        "received": display_value,
        "next_steps": [
            f"Pass `{param_name}` as a native object, not a JSON string.",
            "MCP protocol handles JSON serialization automatically.",
        ],
    }
```

**Source:** Derived from v.md MCP Tool Calling Convention section (lines 15-27).

### Anti-Patterns to Avoid

- **Silent auto-parsing:** Do not parse the JSON string and continue. This
  hides the bug and prevents agents from learning correct MCP usage.
- **Generic error messages:** Do not return "Invalid parameter type" without
  examples. The educational value is in showing exactly what was wrong and
  how to fix it.
- **Crashing on invalid JSON:** If the string is not valid JSON, return a
  graceful error rather than raising an exception.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Error response format | Custom dict structure | Follow TaskError pattern | Consistency with existing error handling |
| JSON validation | Custom try/except | `json.loads()` with catch | Standard library handles edge cases |

**Key insight:** For just 3 tools, inline checks are simpler than a shared
decorator. A decorator would add complexity (signature inspection, parameter
name mapping) for minimal reuse benefit.

## Common Pitfalls

### Pitfall 1: Checking for None Before isinstance

**What goes wrong:** `isinstance(None, str)` returns False, but the parameter
may be legitimately None (optional parameter).

**Why it happens:** Forgetting that None is a valid value for optional params.

**How to avoid:** Check `param is not None and isinstance(param, str)`.

**Warning signs:** Tool returns stringification error when parameter omitted.

### Pitfall 2: Not Truncating Long Values

**What goes wrong:** Error message includes a 10KB JSON string, making the
response unreadable.

**Why it happens:** Large objects get stringified and included verbatim.

**How to avoid:** Truncate received value in error message to ~100 chars.

**Warning signs:** Error responses that span multiple screens.

### Pitfall 3: Inconsistent Error Format

**What goes wrong:** Each tool returns slightly different error structure,
confusing agents.

**Why it happens:** Ad-hoc error construction without shared helper.

**How to avoid:** Use a shared helper function `_build_stringification_error()`
that all three tools call.

**Warning signs:** Tests pass for one tool but fail for others due to format
differences.

## Code Examples

Verified patterns from the codebase:

### Existing Error Pattern (TaskError)

```python
# Source: src/vibraphone/utils/errors.py
from pydantic import BaseModel

class TaskError(BaseModel):
    """Structured error response for task management tools."""
    error_type: str
    message: str
    suggested_action: str

# Usage in bridge_tools.py
return TaskError(
    error_type="NoComponentsConfigured",
    message="No components configured in vibraphone.yaml",
    suggested_action="Configure components in vibraphone.yaml before importing plans",
).model_dump()
```

### v.md WRONG/RIGHT Table Format

```markdown
# Source: src/vibraphone/commands/v.md lines 20-24
| WRONG                          | RIGHT                        |
| ------------------------------ | ---------------------------- |
| `values: "{\"lang\": \"go\"}"` | `values: {"lang": "go"}`     |
| `files: "[\"a.py\", \"b.py\"]"`| `files: ["a.py", "b.py"]`    |
| `components: "{...}"`          | `components: {...}`          |
```

### Tool Function Signature Pattern

```python
# Source: src/vibraphone/tools/scaffold_tools.py lines 138-144
@mcp.tool
async def init_project(
    project_path: str | None = None,
    values: dict[str, Any] | None = None,
    *,
    preview: bool = True,
) -> dict[str, Any]:
```

```python
# Source: src/vibraphone/tools/stack_tools.py lines 219-225
@mcp.tool
async def configure_stack(
    components: dict[str, dict[str, Any]],
    stitch_project_id: str | None = None,
    *,
    preview: bool = True,
) -> dict[str, Any]:
```

```python
# Source: src/vibraphone/tools/quality_gate_tools.py lines 494-495
@mcp.tool
async def request_code_review(task_id: str | None = None,
                              files: list[str] | None = None) -> dict:
```

### Existing Test Pattern (pytest-mock)

```python
# Source: tests/test_scaffold_tools.py lines 53-90
class TestInitProjectPreview:
    @pytest.mark.asyncio
    async def test_init_project_preview_returns_detected_values(
        self, mocker: Any, tmp_path: Path
    ) -> None:
        """preview=True returns status='preview'."""
        mocker.patch("vibraphone.tools.scaffold_tools.check_prereqs", ...)
        mocker.patch("vibraphone.tools.scaffold_tools.detect_project_metadata", ...)

        from vibraphone.tools.scaffold_tools import init_project

        result = await init_project.fn(str(tmp_path), preview=True)

        assert result["status"] == "preview"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Accept any parameter type | Type hints on tool params | Phase 6+ | Better documentation |
| Crash on bad input | TaskError pattern | Phase 5+ | Graceful error handling |
| No stringification awareness | Defensive parsing (this phase) | Phase 12 | Educational error messages |

**Deprecated/outdated:**
- Returning raw Python exceptions as strings: Use structured TaskError or
  error dicts with `error_type` field.

## Open Questions

1. **Helper function location**
   - What we know: Three tools need the same defensive check
   - What's unclear: Should helper live in utils/errors.py or in each tool file
   - Recommendation: For just 3 tools, duplicate the helper in each file
     (simpler than cross-file imports). If more tools need hardening later,
     extract to utils/defensive_parsing.py.

2. **Error message exact wording**
   - What we know: Must include WRONG/RIGHT table format
   - What's unclear: Exact wording around the table
   - Recommendation: Keep it minimal - just the table and one-line fix
     instruction. Agents can infer from examples.

## Sources

### Primary (HIGH confidence)

- Codebase examination (2026-02-19):
  - `src/vibraphone/tools/scaffold_tools.py` - init_project implementation
  - `src/vibraphone/tools/stack_tools.py` - configure_stack implementation
  - `src/vibraphone/tools/quality_gate_tools.py` - request_code_review implementation
  - `src/vibraphone/utils/errors.py` - TaskError pattern
  - `src/vibraphone/commands/v.md` - WRONG/RIGHT table format documentation

- Test file examination:
  - `tests/test_scaffold_tools.py` - test patterns for scaffold tools
  - `tests/test_stack_tools.py` - test patterns for stack tools
  - `tests/test_quality_gate_tools.py` - test patterns for quality gate tools

### Secondary (MEDIUM confidence)

- STATE.md decisions section confirms multi-layer defense approach chosen
- CONTEXT.md locked decisions provide exact implementation constraints

### Tertiary (LOW confidence)

- None - all findings verified against codebase

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH - All libraries already in use, no new dependencies
- Architecture: HIGH - Pattern is simple inline check, follows existing
  TaskError conventions
- Pitfalls: HIGH - Derived from understanding of Python isinstance behavior
  and the specific MCP context

**Research date:** 2026-02-19
**Valid until:** 30 days - defensive patterns are stable
