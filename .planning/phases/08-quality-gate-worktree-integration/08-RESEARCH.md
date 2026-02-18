# Phase 8: Quality Gate Worktree Integration - Research

**Researched:** 2026-02-17
**Domain:** Session-aware quality gate command execution in git worktrees
**Confidence:** HIGH

## Summary

Phase 8 requires integrating session awareness into quality gate tools so they operate in the active worktree when a session exists. The current implementation has a clean separation: quality gate tools call `get_project_root()` to determine where to run commands, while session state is managed separately via `SessionManager`. The integration requires creating a helper function that resolves the execution context (worktree path if session exists, project root otherwise) and modifying all quality gate tools to use this context.

**Primary recommendation:** Create a `get_execution_context()` helper function that checks for an active session and returns the appropriate working directory. Modify all quality gate tools to use this context instead of hardcoded `get_project_root()`.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| QUAL-06 | Quality gates operate in worktree context when session exists | Session tracking via SessionManager.load() returns worktree_path; quality gate tools use configurable cwd parameter |

## Architecture Patterns

### Current Architecture (Gap Identified)

The quality gate tools currently have this pattern:

```python
# quality_gate_tools.py - Current implementation
@mcp.tool
async def run_tests(component: str | None = None) -> dict:
    project_root = get_project_root()  # Always returns project root
    # ...
    returncode, stdout, stderr = await run_command(command, cwd=project_root)
```

The session is tracked independently:

```python
# session.py - Session tracking
class SessionState(BaseModel):
    task_id: str
    worktree_path: Path  # This is the missing link
    branch_name: str
    started_at: datetime
```

### Recommended Integration Pattern

**Pattern 1: Execution Context Helper**

Create a utility function that resolves the execution context:

```python
# utils/context.py (NEW FILE)
from pathlib import Path
from vibraphone.config import get_project_root
from vibraphone.utils.session import SessionManager, SessionState

def get_execution_context() -> tuple[Path, SessionState | None]:
    """Get execution context for quality gate commands.

    Returns:
        Tuple of (working_directory, session_state).
        working_directory is worktree_path if session exists, else project_root.
        session_state is None if no active session.
    """
    project_root = get_project_root()
    session = SessionManager(project_root)
    state = session.load()

    if state and state.worktree_path.exists():
        return (state.worktree_path, state)

    return (project_root, None)
```

**Pattern 2: Quality Gate Tool Modification**

Each quality gate tool needs to replace `get_project_root()` with the context-aware version:

```python
# quality_gate_tools.py - Modified implementation
from vibraphone.utils.context import get_execution_context

@mcp.tool
async def run_tests(component: str | None = None) -> dict:
    config = get_config()
    exec_dir, session = get_execution_context()  # Context-aware
    task_id = session.task_id if session else "default"
    state_manager = get_quality_state_manager(task_id)
    # ...
    returncode, stdout, stderr = await run_command(command, cwd=exec_dir)
```

### Files Requiring Modification

| File | Changes Required |
|------|-----------------|
| `quality_gate_tools.py` | Import `get_execution_context`, replace `get_project_root()` calls |
| `run_tests` | Use exec context for cwd, derive task_id from session |
| `run_lint` | Use exec context for cwd |
| `run_format` | Use exec context for cwd |
| `request_code_review` | Use exec context for staging, derive task_id from session |
| `attempt_commit` | Use exec context for commit, derive task_id from session |
| NEW: `utils/context.py` | Create execution context helper |

### Fallback Behavior

When no session exists:
1. `get_execution_context()` returns `(project_root, None)`
2. Quality gates use `task_id="default"` for state management
3. All git operations run in project root
4. Behavior is identical to current implementation

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Session lookup | New session query function | `SessionManager(project_root).load()` | Already exists, atomic reads |
| Project root resolution | Custom path walking | `get_project_root()` from config.py | Already handles config discovery |
| Worktree existence check | Custom path validation | `state.worktree_path.exists()` | Simple stdlib check |

## Common Pitfalls

### Pitfall 1: Forgetting to Update task_id in State Manager
**What goes wrong:** When a session exists, quality state should use the session's task_id, not "default". Otherwise state persists across different task contexts.
**Why it happens:** Current code hardcodes `task_id="default"` in `get_quality_state_manager()`.
**How to avoid:** Extract `task_id` from session state when available.

### Pitfall 2: Git Commands Running in Wrong Directory
**What goes wrong:** Tests run in project root instead of worktree, or commits go to wrong branch.
**Why it happens:** Forgetting to pass the `cwd` parameter to `run_command()` or git subprocess calls.
**How to avoid:** Every git command MUST use the execution context directory, including helper functions like `get_unstaged_files()`, `stage_files()`, `get_staged_diff()`, `run_git_commit()`.

### Pitfall 3: State File Location Mismatch
**What goes wrong:** Quality state file written to wrong `.vibraphone/tasks/{task_id}/` directory.
**Why it happens:** `get_quality_state_manager()` uses `get_project_root()` internally.
**How to avoid:** `QualityStateManager` should continue to use project root for state storage (this is correct behavior - state is shared across worktrees, only execution happens in worktree).

### Pitfall 4: Stale Session References
**What goes wrong:** Session file exists but worktree was manually deleted, causing commands to fail.
**Why it happens:** Session file not cleaned up when worktree is removed externally.
**How to avoid:** Check `state.worktree_path.exists()` before using worktree path. If worktree doesn't exist, fall back to project root.

## Code Examples

### Execution Context Helper

```python
# src/vibraphone/utils/context.py
"""Execution context resolution for session-aware command execution."""

from pathlib import Path

from vibraphone.config import get_project_root
from vibraphone.utils.session import SessionManager, SessionState


def get_execution_context() -> tuple[Path, SessionState | None]:
    """Resolve execution context for quality gate commands.

    When an active session exists with a valid worktree, returns the
    worktree path as the execution directory. Otherwise falls back to
    project root.

    Returns:
        Tuple of (working_directory, session_state).
        - working_directory: Path to execute commands in
        - session_state: SessionState if session exists and worktree valid, else None
    """
    project_root = get_project_root()
    session = SessionManager(project_root)
    state = session.load()

    if state and state.worktree_path.exists():
        return (state.worktree_path, state)

    return (project_root, None)


def get_effective_task_id(session: SessionState | None) -> str:
    """Get effective task_id for state management.

    Args:
        session: Session state from get_execution_context(), or None

    Returns:
        Task ID from session if available, otherwise "default"
    """
    return session.task_id if session else "default"
```

### Modified run_tests Example

```python
# quality_gate_tools.py - Modified run_tests
from vibraphone.utils.context import get_execution_context, get_effective_task_id

@mcp.tool
async def run_tests(component: str | None = None) -> dict:
    """Run tests with circuit breaker protection."""
    config = get_config()
    exec_dir, session = get_execution_context()
    task_id = get_effective_task_id(session)
    state_manager = get_quality_state_manager(task_id)

    # Load state for attempt tracking
    state = state_manager.load()
    if state is None:
        state = QualityGateState(task_id=task_id)

    # Check circuit breaker before running
    breaker = CircuitBreaker(
        max_attempts=config.circuit_breakers.tests.max_attempts,
        tool_name="run_tests",
    )
    escalation = breaker.check(state.test_attempts)
    if escalation:
        return escalation

    # Get command and execute IN THE WORKTREE
    command = get_command("test", component)
    start_time = datetime.now(UTC)

    returncode, stdout, stderr = await run_command(command, cwd=exec_dir)
    # ... rest of function
```

### Modified request_code_review Example

```python
# quality_gate_tools.py - Modified request_code_review
@mcp.tool
async def request_code_review(task_id_override: str | None = None, files: list[str] | None = None) -> dict:
    """Request LLM code review of staged changes."""
    config = get_config()
    exec_dir, session = get_execution_context()

    # Use override if provided, else session task_id, else "default"
    if task_id_override:
        task_id = task_id_override
    else:
        task_id = get_effective_task_id(session)

    state_manager = get_quality_state_manager(task_id)
    # ...

    # Prepare files for review IN THE WORKTREE
    blocked_files, diff_content, error = await prepare_files_for_review(files, exec_dir)
    # ... rest of function
```

### Modified attempt_commit Example

```python
# quality_gate_tools.py - Modified attempt_commit
@mcp.tool
async def attempt_commit(task_id_override: str | None = None, message: str = "") -> dict:
    """Attempt to commit changes. Requires approved code review."""
    exec_dir, session = get_execution_context()

    # Use override if provided, else session task_id, else "default"
    if task_id_override:
        task_id = task_id_override
    else:
        task_id = get_effective_task_id(session)

    state_manager = get_quality_state_manager(task_id)
    # ...

    # All git operations use exec_dir
    returncode, current_diff, stderr = await get_staged_diff(exec_dir)
    # ...
    returncode, stdout, stderr = await run_git_commit(message, cwd=exec_dir)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded project root | Session-aware execution context | Phase 8 | Quality gates work in isolated worktrees |

**Deprecated/outdated:**
- Direct `get_project_root()` calls in quality gate tools (replaced by `get_execution_context()`)

## Integration Points

### How Session Tracking Works

1. `start_task` creates worktree at `{worktrees_path}/{repo-name}/{task_id}/`
2. `start_task` saves `SessionState` with `worktree_path`, `branch_name`, `task_id`
3. Session persists to `.vibraphone/session.json`
4. `cleanup_task` clears session after merge

### How Quality Gates Should Adapt

1. Check for active session via `get_execution_context()`
2. If session exists with valid worktree:
   - Execute all commands in worktree directory
   - Use session's `task_id` for state management
3. If no session or invalid worktree:
   - Execute in project root (current behavior)
   - Use "default" task_id for state management

### E2E Flow (Success Criterion 5)

```
1. import_gsd_plan -> Creates tasks in beads
2. start_task("001") -> Creates worktree, saves session
3. run_tests() -> Detects session, runs in worktree
4. [Make changes in worktree]
5. request_code_review() -> Stages from worktree, reviews
6. attempt_commit() -> Commits to worktree branch
7. merge_task("001") -> Rebases onto main
8. cleanup_task("001") -> Removes worktree, clears session
```

## Open Questions

1. **Should task_id parameter be optional or removed from request_code_review?**
   - Current: `request_code_review(task_id: str, ...)` requires explicit task_id
   - Option A: Keep required for backward compatibility
   - Option B: Make optional, derive from session
   - Recommendation: Make optional with override, derive from session when not provided

2. **Should task_id parameter be optional in attempt_commit?**
   - Same as above - recommend optional with session-derived default

3. **What happens if session.task_id differs from explicit task_id_override?**
   - Recommendation: Override takes precedence (explicit is intentional)

## Sources

### Primary (HIGH confidence)
- `/home/luke/workspace/github.com/lukemcguire/vibraphone/src/vibraphone/tools/quality_gate_tools.py` - Current quality gate implementation
- `/home/luke/workspace/github.com/lukemcguire/vibraphone/src/vibraphone/utils/session.py` - Session state management
- `/home/luke/workspace/github.com/lukemcguire/vibraphone/src/vibraphone/tools/worktree_tools.py` - Worktree lifecycle tools
- `/home/luke/workspace/github.com/lukemcguire/vibraphone/src/vibraphone/utils/command_runner.py` - Command execution with cwd parameter

### Secondary (MEDIUM confidence)
- `/home/luke/workspace/github.com/lukemcguire/vibraphone/.planning/REQUIREMENTS.md` - Requirements definitions
- `/home/luke/workspace/github.com/lukemcguire/vibraphone/.planning/ROADMAP.md` - Phase definitions and success criteria
- `/home/luke/workspace/github.com/lukemcguire/vibraphone/.planning/STATE.md` - Prior decisions

## Metadata

**Confidence breakdown:**
- Architecture patterns: HIGH - Code is well-structured with clear extension points
- Integration approach: HIGH - SessionManager already provides needed data
- Pitfalls: HIGH - Based on actual code analysis

**Research date:** 2026-02-17
**Valid until:** N/A (internal codebase research, not time-sensitive)
