# Phase 11: Command Documentation - Research

**Researched:** 2026-02-19
**Domain:** Technical documentation / MCP tool command reference
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Command Organization

- **4 workflow stage groups:**
  1. Start Work (list, next, start)
  2. Run Quality (test, lint, format, review)
  3. Commit & Merge (commit, merge, cleanup, complete)
  4. Session Management (status, health, recover)
- Each section has a brief intro paragraph, then commands as H3 headings
- Clean, scannable structure

#### Example Depth

- **Full coverage** for each command: typical scenarios + edge cases + common
  mistakes
- Comprehensive documentation that teaches, not just references
- Examples should help users understand both what works and what doesn't

#### Parameter Guidance

- **Dual approach:** Inline examples for dict-heavy commands + general reference
  section explaining dict parameter handling patterns
- Dict-heavy commands (init, configure-stack, import-plan) get special attention
- Users can copy-paste and modify examples directly

#### Error Documentation

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

### Deferred Ideas (OUT OF SCOPE)

None - discussion stayed within phase scope.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SLASH-01 | User can invoke core workflow tools via /v commands | Workflow commands documented with examples for list, next, start, test, lint, format, review, commit, merge, cleanup, complete, recover, status, health |
| SLASH-02 | User can invoke dict-heavy tools with proper parameter handling | Dict-heavy commands (init, configure-stack, import-plan) documented with inline JSON examples and reference section for dict patterns |
| SLASH-04 | Documentation includes /v command usage | Full v.md documentation with MCP tool calling convention section and WRONG/RIGHT table |

</phase_requirements>

## Summary

This phase documents vibraphone's `/v` slash commands in v.md for Claude Code
users. The documentation must be comprehensive enough to teach users how to
invoke MCP tools correctly, with special attention to the stringification
pitfall where dicts/lists get incorrectly serialized as JSON strings.

The current v.md already has good foundations: MCP Tool Calling Convention with
WRONG/RIGHT table, parameter tables, and basic JSON examples. The gap is "full
coverage" documentation that teaches typical scenarios, edge cases, and common
mistakes rather than just referencing commands.

**Primary recommendation:** Reorganize v.md into 4 workflow stage groups,
add a quick reference table at the start, expand each command with
typical/edge/error examples, and add a dedicated troubleshooting section.

## Standard Stack

### Core (Documentation Format)

| Element | Purpose | Why Standard |
|---------|---------|--------------|
| Markdown | Documentation format | Claude Code reads markdown natively |
| YAML frontmatter | Command metadata | Claude Code command discovery |
| JSON code blocks | MCP call examples | Copy-pasteable examples |
| WRONG/RIGHT tables | Anti-pattern documentation | Proven effective for stringification pitfall |

### Documentation Structure

| Section | Content | Purpose |
|---------|---------|---------|
| Quick Reference Table | Command -> Purpose mapping | Fast lookup |
| MCP Tool Calling Convention | WRONG/RIGHT table | Prevent stringification |
| Workflow Stage Groups | 4 groups with intro paragraphs | Mirror user workflow |
| Troubleshooting | Dedicated error resolution | Centralized error guidance |

**Installation:**

No installation needed - documentation is read directly by Claude Code.

## Architecture Patterns

### Recommended Document Structure

```text
---
name: v
description: ...
argument-hint: ...
allowed-tools: ...
---

# Vibraphone Slash Commands

[Brief intro paragraph]

## Quick Reference

[Table: Command | Purpose | MCP Tool]

## MCP Tool Calling Convention

[WRONG/RIGHT table - already exists]

## Start Work

[Intro paragraph about this workflow stage]

### /v list [options...]
[Full coverage examples]

### /v next
[Full coverage examples]

### /v start <task_id>
[Full coverage examples]

## Run Quality

[Intro paragraph about quality gates]

### /v test [options...]
[Full coverage examples]

...

## Commit & Merge

[Intro paragraph about commit workflow]

...

## Session Management

[Intro paragraph about session/recovery]

...

## Troubleshooting

[Common errors + resolutions]

## Argument Parsing

[Already exists]

## Error Handling

[Already exists]

## Context Detection

[Already exists]
```

### Pattern 1: Full Coverage Command Documentation

**What:** Each command gets 3 types of examples:
1. **Typical:** Happy path usage
2. **Edge cases:** Optional parameters, filtering, multi-component
3. **Common mistakes:** What NOT to do, with correction

**When to use:** All documented commands

**Example structure:**

```markdown
### /v start <task_id>

Start a task in an isolated git worktree.

**Typical usage:**

/v start bd-abc123

Claude calls: `vibraphone_start_task({"task_id": "bd-abc123"})`

**Edge cases:**

# Task already in progress (returns error)
/v start bd-abc123
-> error_type: "BranchAlreadyExists"
-> suggested_action: "Check existing worktrees..."

**Common mistakes:**

# WRONG: Using wrong ID format
/v start 123

# RIGHT: Use full task ID from br output
/v start bd-abc123
```

### Pattern 2: Dict-Heavy Command Documentation

**What:** Commands with complex dict parameters get expanded inline examples
showing the full JSON structure.

**When to use:** init, configure-stack, import-plan

**Example:**

```markdown
### /v configure-stack [--stitch PROJECT_ID]

**Basic single component:**

/v configure-stack

Claude calls:
```json
{
  "components": {
    "server": {
      "language": "python",
      "root": "./src",
      "test_command": "pytest",
      "lint_command": "ruff check .",
      "format_command": "ruff format ."
    }
  },
  "preview": true
}
```

**Multiple components:**

```json
{
  "components": {
    "backend": {...},
    "frontend": {
      "language": "node",
      "root": "./web",
      "test_command": "npm test",
      ...
    }
  }
}
```
```

### Anti-Patterns to Avoid

- **Wall of text:** Long paragraphs without examples - users skip these
- **Missing error context:** Only showing happy path - users get stuck on errors
- **Inconsistent formats:** Different example styles per command - confusing
- **Hidden tool names:** Not showing which MCP tool is called - harder to debug

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Quick reference table | Custom ASCII table | Markdown table with Command/Purpose/MCP columns | Rendered consistently |
| JSON examples | Escaped strings in text | Fenced code blocks with json language | Copy-pasteable, syntax highlighted |
| Error documentation | Scattered inline only | Dedicated troubleshooting section + inline | Centralized lookup + context |

**Key insight:** Documentation should be scannable first, detailed second. The
quick reference table and section headers allow users to find commands fast,
while the full coverage examples teach comprehensive usage.

## Common Pitfalls

### Pitfall 1: Dict Parameter Stringification

**What goes wrong:** Users (or Claude) pass dict parameters as JSON strings
instead of native objects: `values: "{\"lang\": \"go\"}"` instead of
`values: {"lang": "go"}`.

**Why it happens:** Claude Code's abstraction layer may serialize examples
literally. When documentation shows JSON in code blocks, it can be interpreted
as "pass this string" rather than "pass this object."

**How to avoid:**
1. WRONG/RIGHT table at document start (already exists)
2. Repeat convention inline for dict-heavy commands
3. Use clear language: "Claude calls:" not "Pass:"

**Warning signs:**
- Tool returns `TypeError: string indices must be integers`
- Logs show extra quotes around parameter values

### Pitfall 2: Missing Error Context

**What goes wrong:** Documentation only shows happy path. Users encounter
errors and have no guidance on resolution.

**Why it happens:** Happy path is easy to document; errors require knowing
all failure modes.

**How to avoid:**
1. For each command, list common error_type values
2. Document suggested_action from tool responses
3. Add troubleshooting section for cross-cutting errors

**Warning signs:**
- Users asking "what does this error mean?"
- Repeated questions about same failure modes

### Pitfall 3: Inconsistent Example Formats

**What goes wrong:** Commands use different example styles, making the
documentation feel disjointed and harder to learn.

**Why it happens:** Documentation written incrementally without style guide.

**How to avoid:**
1. Define consistent template for all commands
2. Use same "Typical / Edge / Mistake" structure
3. Same code block format and labeling

**Warning signs:**
- Some commands have many examples, others have few
- Format varies between JSON, text, and mixed

## Code Examples

### Error Types to Document (from tool source)

```text
# From task_tools.py
- CannotCompleteBlockedTask: Task has incomplete dependencies
- NoActiveSession: No session found for task

# From worktree_tools.py
- NoActiveSession: No active session for task
- UncommittedChanges: Files with uncommitted changes
- BranchNotMerged: Task branch not merged into main

# From worktree_ops.py
- BranchAlreadyExists: Branch already exists - task may be in progress
- WorktreeCreationFailed: Failed to create worktree
- RebaseConflict: Rebase conflicts with conflicted_files list
- WorktreeRemovalFailed: Failed to remove worktree

# From quality_gate_tools.py
- MissingAPIKeyError: REVIEWER_API_KEY not set
- ImportError: Missing packages (instructor, python-dotenv)
- Quality gate failures: test/lint/format return non-zero

# From scaffold_tools.py
- Missing prerequisites: br, bv, git, just, node/npx
- Project path does not exist

# From bridge_tools.py
- NoComponentsConfigured: No components in vibraphone.yaml
- PhaseDirectoryNotFound: Phase directory not found
- NoPlanFilesFound: No PLAN.md files in phase directory
- PlanHasNoTasks: Plan file has no tasks block
```

### Quick Reference Table Format

```markdown
## Quick Reference

| Command | Purpose | MCP Tool |
| ------- | ------- | -------- |
| /v init | Initialize vibraphone in project | vibraphone_init_project |
| /v list | List tasks from Beads | vibraphone_list_tasks |
| /v next | Get next ready task | vibraphone_next_ready |
| /v start <id> | Start task in worktree | vibraphone_start_task |
| /v test | Run tests | vibraphone_run_tests |
| /v lint | Run linter | vibraphone_run_lint |
| /v format | Run formatter | vibraphone_run_format |
| /v review | Request code review | vibraphone_request_code_review |
| /v commit <msg> | Attempt commit | vibraphone_attempt_commit |
| /v merge <id> | Merge task branch | vibraphone_merge_task |
| /v cleanup <id> | Remove worktree/branch | vibraphone_cleanup_task |
| /v complete <id> | Mark task done | vibraphone_complete_task |
| /v status | Show session state | vibraphone_recover_session |
| /v health | Show health metrics | vibraphone_health_check |
| /v recover | Resume session | vibraphone_recover_session |
| /v cycle | Run quality suite | (multiple) |
| /v finish | Complete workflow | (multiple) |
```

### Troubleshooting Section Format

```markdown
## Troubleshooting

### Quality Gate Failures

**Test failures:**

1. Run `/v test` to see failure output
2. Fix failing tests
3. Re-run `/v test` until pass
4. If stuck after max attempts, circuit breaker escalates

**Lint failures:**

1. Run `/v lint` to see violations
2. Fix lint errors (often auto-fixable)
3. Re-run `/v lint` until pass

**Review rejection:**

1. Review issues list in response
2. Fix identified problems
3. Run `/v review` again
4. If max attempts exceeded, tool returns ESCALATED

### Worktree Issues

**Merge conflicts:**

Error: `RebaseConflict` with `conflicted_files` list

Resolution:
1. `cd` to worktree path
2. Manually resolve conflicts in listed files
3. Stage resolved files: `git add <files>`
4. Re-run `/v merge <task_id>`

**Uncommitted changes:**

Error: `UncommittedChanges` with file list

Resolution:
1. `cd` to worktree path
2. Commit or stash changes
3. Re-run `/v cleanup <task_id>`

**Branch not merged:**

Error: `BranchNotMerged`

Resolution:
1. Run `/v merge <task_id>` first
2. Then run `/v cleanup <task_id>`
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Basic parameter tables | Full coverage examples | Phase 11 | Teaching vs referencing |
| Single error section | Dual: inline + troubleshooting | Phase 11 | Better error discovery |
| Flat command list | 4-group workflow organization | Phase 11 | Mirrors actual usage |

**Deprecated/outdated:**
- None for this phase (documentation only)

## Open Questions

1. **Should examples include MCP tool function names?**
   - What we know: README.md shows tool names, v.md shows tool names
   - What's unclear: Whether every example should show the exact MCP call
   - Recommendation: YES - include for auditability and debugging

2. **How many examples per command?**
   - What we know: CONTEXT.md says "full coverage" with typical + edge + mistakes
   - What's unclear: Exact count (varies by complexity)
   - Recommendation: Variable by complexity - simple commands get 1-2, dict-heavy
     get 3-5

3. **Should error examples show full JSON responses?**
   - What we know: Tools return structured errors with error_type, message,
     suggested_action
   - What's unclear: Whether to show full response or just key fields
   - Recommendation: Show key fields inline (error_type, suggested_action),
     full responses in troubleshooting section

## Sources

### Primary (HIGH confidence)

- `/home/luke/workspace/github.com/lukemcguire/vibraphone/src/vibraphone/commands/v.md` - Current command documentation
- `/home/luke/workspace/github.com/lukemcguire/vibraphone/src/vibraphone/tools/*.py` - Tool implementations and error types
- `/home/luke/workspace/github.com/lukemcguire/vibraphone/.planning/research/PITFALLS.md` - Stringification pitfall research
- `/home/luke/workspace/github.com/lukemcguire/vibraphone/README.md` - Existing documentation style

### Secondary (MEDIUM confidence)

- `/home/luke/workspace/github.com/lukemcguire/vibraphone/.planning/REQUIREMENTS.md` - Requirement IDs and traceability
- `/home/luke/workspace/github.com/lukemcguire/vibraphone/.planning/phases/11-command-documentation/11-CONTEXT.md` - User decisions

### Tertiary (LOW confidence)

- None - all sources are project files with HIGH confidence

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH - based on existing v.md and README patterns
- Architecture: HIGH - structure defined in CONTEXT.md decisions
- Pitfalls: HIGH - documented in PITFALLS.md with root cause analysis
- Error types: HIGH - extracted directly from tool source code

**Research date:** 2026-02-19
**Valid until:** 30 days (stable documentation patterns)

---

*Research for: Phase 11 Command Documentation*
*Researched: 2026-02-19*
