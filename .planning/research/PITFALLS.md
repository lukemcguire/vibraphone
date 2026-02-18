# Pitfalls Research

**Domain:** Claude Code slash commands / MCP tool invocation
**Researched:** 2026-02-18
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Dict/List Parameter Stringification

**What goes wrong:**
When a slash command instructs Claude to call an MCP tool with dict or list
parameters, Claude may serialize the dict/list to a JSON string instead of
passing it as a native object. The MCP tool receives `values: "{\"lang\":
\"go\"}"` instead of `values: {"lang": "go"}`.

**Why it happens:**
Claude Code's tool calling abstraction layer treats all string values
literally. When the SKILL.md documentation shows JSON examples in code
blocks, Claude may interpret this as "pass a string containing JSON" rather
than "pass a JSON object." This is exacerbated when:

- Examples use JSON syntax in markdown without clear "native object" cues
- The model sees `{"key": "value"}` and treats the entire thing as a string
literal
- Previous conversation context shows serialized JSON patterns

**Consequences:**
- MCP tools expecting `dict[str, Any]` receive `str`, causing TypeErrors
- Tool fails to access `data["key"]` because `data` is a string
- Subtle bugs where `isinstance(param, dict)` checks silently fail
- Workarounds like `json.loads()` inside tools become necessary (brittle)

**How to avoid:**

1. **Explicit convention documentation** in SKILL.md (current approach):
```markdown
When calling vibraphone MCP tools, **dict and list parameters must be passed
as JSON objects/arrays, NOT as JSON strings**.

| WRONG                          | RIGHT                        |
| ------------------------------ | ---------------------------- |
| `values: "{\"lang\": \"go\"}"` | `values: {"lang": "go"}`     |
| `files: "[\"a.py\", \"b.py\"]"`| `files: ["a.py", "b.py"]`    |
```

2. **Use schema-compatible type hints** in tool definitions:
```python
@mcp.tool
async def configure_stack(
    components: dict[str, dict[str, Any]],  # NOT str | dict
    ...
) -> dict[str, Any]:
```

3. **Add defensive parsing** in tools (backup, not primary solution):
```python
def _ensure_dict(value: dict | str) -> dict:
    if isinstance(value, str):
        return json.loads(value)
    return value
```

**Warning signs:**
- Tool calls failing with "string indices must be integers"
- `TypeError: string indices must be integers, not str`
- Logs showing parameters arriving as `"{"key": ...}"` with extra quotes
- SKILL.md examples being copy-pasted literally as strings

**Phase to address:**
Phase 1 (Slash Command Implementation) - Document convention in SKILL.md;
Phase 2 (Tool Hardening) - Add defensive parsing as fallback

---

### Pitfall 2: Skill Not Auto-Discovered

**What goes wrong:**
User installs skill via `vibraphone skill install` but `/v` commands are not
recognized. Claude Code does not invoke the skill even when the description
matches the user's request.

**Why it happens:**
Skills have strict discovery requirements that are easy to violate:
- YAML frontmatter syntax errors (tabs instead of spaces, missing `---`)
- Description field too vague or missing trigger keywords
- Skill directory in wrong location (`~/.claude/skills/v/` not
  `~/.claude/skills/vibraphone/`)
- SKILL.md file not named exactly `SKILL.md` (case-sensitive)

**Consequences:**
- Skill silently fails to load
- User frustration - "I installed it but it doesn't work"
- Debugging requires restarting Claude Code to see load errors

**How to avoid:**

1. **Validate YAML frontmatter** during skill install:
```python
def validate_skill_md(path: Path) -> list[str]:
    errors = []
    content = path.read_text()
    if not content.startswith("---\n"):
        errors.append("Missing opening ---")
    # ... validate name, description fields
    return errors
```

2. **Include specific trigger keywords** in description:
```yaml
description: |
  Vibraphone slash commands for MCP tool orchestration. Use when the user
  invokes /v commands like "/v init", "/v list", "/v next", "/v start"...
```

3. **Test skill discovery** after install:
```bash
vibraphone skill install
claude  # Then ask: "What Skills are available?"
```

**Warning signs:**
- `/v` command not appearing in tab completion
- Claude doesn't respond to skill-related queries
- `claude --debug` shows skill loading errors

**Phase to address:**
Phase 1 (Slash Command Implementation) - Validate SKILL.md during install

---

### Pitfall 3: MCP Tool Name Mismatch

**What goes wrong:**
SKILL.md instructs Claude to call `vibraphone_init_project` but the actual
registered tool name is `init_project` (FastMCP strips package prefix by
default) or vice versa.

**Why it happens:**
FastMCP's `@mcp.tool` decorator registers tools with the function name, not
a namespaced path. The documentation may assume a prefix that doesn't exist,
or the tool may have been renamed during refactoring.

**Consequences:**
- "Tool not found" errors
- Claude attempts to call non-existent tools
- User sees cryptic MCP protocol errors

**How to avoid:**

1. **Verify actual tool names** by listing registered tools:
```python
# In server startup or test
for tool in mcp.list_tools():
    print(f"Registered: {tool.name}")
```

2. **Use consistent naming** between SKILL.md and actual tools:
```markdown
**MCP Tool**: `init_project`  # Match actual @mcp.tool function name
```

3. **Document the mapping** explicitly if namespacing is needed:
```markdown
**MCP Tool Name Mapping:**
- SKILL.md: `vibraphone_init_project`
- Actual: `init_project` (via mcp__vibraphone__init_project)
```

**Warning signs:**
- Tool calls returning "unknown tool" errors
- Claude asking for clarification about which tool to use
- Inconsistency between docs and behavior

**Phase to address:**
Phase 1 (Slash Command Implementation) - Audit SKILL.md tool names against
actual registrations

---

## Moderate Pitfalls

### Pitfall 4: Missing Skill Restart After Update

**What goes wrong:**
User updates SKILL.md (e.g., fixes documentation) but changes don't take
effect. Old behavior persists.

**Why it happens:**
Claude Code loads skills once at startup. Changes to SKILL.md require
restarting Claude Code to take effect.

**Prevention:**
- Document this in skill install output: "Restart Claude Code if it's already
  running"
- Add a `/v reload` hint in documentation (though this isn't a real command)

---

### Pitfall 5: Argument Parsing Ambiguity

**What goes wrong:**
User runs `/v commit feat: add feature` but the message is parsed incorrectly.
Flags like `--language go` may be confused with positional arguments.

**Why it happens:**
Skills receive `$ARGUMENTS` as a single string. Claude must parse this
according to the skill's instructions, which may be ambiguous.

**Prevention:**
- Use explicit argument hints in SKILL.md frontmatter:
```yaml
argument-hint: <task_id> [--notes NOTES]
```
- Show clear examples in SKILL.md for each command variant

---

### Pitfall 6: Skill Conflicts With User Commands

**What goes wrong:**
User has a personal `/v` command in `~/.claude/commands/v.md` that conflicts
with the vibraphone skill.

**Why it happens:**
Slash commands and skills have separate namespaces but share the invocation
syntax. A `/v` command shadows the skill's `/v` trigger.

**Prevention:**
- Document that `/v` is reserved for vibraphone
- Consider alternative naming if conflicts are common
- Check for existing commands during install (warn, don't clobber)

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip defensive parsing | Faster implementation | Stringification bugs in production | Never for dict params |
| Omit argument hints | Less documentation | User confusion, parsing errors | Never for complex commands |
| Hardcode tool names | Quick copy-paste | Breaks on refactors | Never - always verify |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| FastMCP tool registration | Assuming namespaced names | Use exact function name from @mcp.tool |
| Claude Code skill loading | Using tabs in YAML frontmatter | Use spaces only (YAML spec) |
| MCP protocol | Passing dicts as JSON strings | Pass as native objects |
| Skill discovery | Vague description field | Include specific trigger keywords |

## "Looks Done But Isn't" Checklist

- [ ] **SKILL.md validation:** YAML frontmatter parsed without errors? Verify
      with `cat SKILL.md | head -n 10`
- [ ] **Tool name audit:** SKILL.md tool names match actual @mcp.tool
      registrations? Run verification script.
- [ ] **Parameter convention:** Dict/list examples show objects, not strings?
      Check all JSON examples in SKILL.md.
- [ ] **Skill discovery:** Skill appears in "What Skills are available?" query?
      Test after install.
- [ ] **Restart reminder:** User told to restart Claude Code after install?
      Check install output.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Parameter stringification | MEDIUM | Add defensive parsing in tool, update SKILL.md convention |
| Skill not discovered | LOW | Fix YAML syntax, restart Claude Code |
| Tool name mismatch | LOW | Update SKILL.md to match actual names |
| Missing restart | LOW | Restart Claude Code |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Parameter stringification | Phase 1 (SKILL.md convention) | Test with complex dict params |
| Skill not discovered | Phase 1 (validate on install) | Run skill discovery test |
| Tool name mismatch | Phase 1 (audit tool names) | Compare SKILL.md to mcp.list_tools() |
| Missing restart | Phase 1 (install message) | User can restart independently |
| Argument parsing | Phase 1 (argument-hint frontmatter) | Test edge cases |
| Skill conflicts | Phase 1 (check existing commands) | Warn during install |

## Root Cause Analysis: Parameter Stringification

The parameter stringification issue has multiple contributing factors:

### 1. Model Interpretation Ambiguity
Claude interprets JSON-like text in two ways:
- As a **literal string**: `"{"key": "value"}"` (the characters `{`, `"`, etc.)
- As a **JSON object**: `{"key": "value"}` (a structured value)

When SKILL.md shows:
```markdown
Call with:
```json
{"values": {"lang": "go"}}
```
```

Claude may read this as "pass a string that looks like JSON" rather than
"pass a JSON object."

### 2. MCP Protocol Layer
The MCP protocol serializes tool call parameters to JSON for transport. When
Claude passes `{"values": "{\"lang\": \"go\"}"}`, the protocol correctly
transmits a string value. The receiving tool gets a string, not a dict.

### 3. No Type Enforcement at Boundary
MCP tool definitions use Python type hints, but these are documentation-only
at the protocol level. The protocol doesn't reject mismatched types - it just
passes what it receives.

### Why SKILL.md Convention Helps (But Doesn't Fully Solve)

The current SKILL.md convention:
```markdown
| WRONG                          | RIGHT                        |
| ------------------------------ | ---------------------------- |
| `values: "{\"lang\": \"go\"}"` | `values: {"lang": "go"}`     |
```

This helps by:
- Making the distinction explicit
- Showing the wrong pattern for comparison

But it doesn't fully solve because:
- Claude still interprets markdown examples as text
- The model's "mental model" of JSON vs string is context-dependent
- Different Claude versions may interpret differently

### Recommended Multi-Layer Defense

1. **SKILL.md layer**: Clear convention documentation (current approach)
2. **Tool layer**: Defensive parsing for dict params
   ```python
   def _parse_maybe_json(value: dict | str | None) -> dict | None:
       if value is None:
           return None
       if isinstance(value, str):
           try:
               return json.loads(value)
           except json.JSONDecodeError:
               return {"raw": value}  # Fallback
       return value
   ```
3. **Error messages layer**: When type mismatch detected, return helpful error
   ```python
   if isinstance(components, str):
       return {
           "status": "error",
           "error": "components must be an object, not a string. Pass {...} not \"...\"",
           "hint": "See SKILL.md 'MCP Tool Calling Convention' section"
       }
   ```

## Sources

- [Claude Code Skills Documentation](https://docs.anthropic.com/en/docs/claude-code/skills)
  (HIGH confidence - official docs)
- [Claude Code Slash Commands Documentation](https://docs.anthropic.com/en/docs/claude-code/slash-commands)
  (HIGH confidence - official docs)
- [Claude Code MCP Documentation](https://docs.anthropic.com/en/docs/claude-code/mcp)
  (HIGH confidence - official docs)
- Project SKILL.md at `/home/luke/workspace/github.com/lukemcguire/vibraphone/src/vibraphone/skills/v/SKILL.md`
  (HIGH confidence - project source)
- FastMCP decorator patterns (MEDIUM confidence - training data + codebase
  verification)

---
*Pitfalls research for: Claude Code slash commands / MCP tool invocation*
*Researched: 2026-02-18*
