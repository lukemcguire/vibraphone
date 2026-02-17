# Phase 4: Worktree & Session Tools - Research

**Researched:** 2026-02-16
**Domain:** Git worktree management and session state persistence for isolated task development
**Confidence:** HIGH

## Summary

This phase implements MCP tools for managing isolated git worktrees where agents can work on tasks without affecting the main branch. The tools enable starting tasks in isolated branches (start_task), merging completed work back to main via rebase (merge_task), and cleaning up worktrees after successful merges (cleanup_task). Additionally, session state persistence tracks active work across server restarts, with automatic stale session detection on startup.

The implementation builds on patterns established in Phase 3 (task_tools.py, cli_runner.py) and uses the configurable worktrees path from vibraphone.yaml. Git worktree operations are performed via asyncio subprocess calls to git commands, following the same async pattern used for br/bv CLIs.

**Primary recommendation:** Use `git worktree add -b <branch> <path> <start-point>` to create isolated worktrees, `git rebase --onto main` for merging, and `git worktree remove` with safety guards for cleanup. Store session state in `.vibraphone/session.json` with JSON schema matching existing Pydantic patterns.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Worktree/Branch Naming

- **Branch prefix:** `feat/{task-id}` (e.g., `feat/001-setup-auth`)
- **Task ID format:** Match br output exactly — use whatever format br returns
- **Worktree path:** `~/.vibraphone/worktrees/{repo-name}/{task-id}/`
  - `{repo-name}` derived from repository directory name
  - Base path (`~/.vibraphone/worktrees/`) configurable in vibraphone.yaml
- **Branch collision handling:** Fail with error — if branch exists, task is already in progress
- **Merge target:** Always `main` (hardcoded)
- **Active worktree tracking:** Stored in `session.json` (task_id → worktree_path mapping)

#### Merge Conflict Handling

- **Merge method:** Rebase onto main (not merge commit, not squash)
- **Conflict mode:** Fail with detailed report
  - Include list of conflicted files
  - Include conflict markers/sections where possible
- **After conflict:** Abort rebase, restore worktree to pre-merge state
  - Run `git rebase --abort` before returning error
  - Agent can then pull latest main, resolve conflicts, retry

#### Session Recovery Flow

- **Stale session handling:** Log only — do not auto-resume
  - Server logs: "Session found: task X in worktree Y. Call resume_session to continue."
  - Agent decides whether to resume or cleanup
- **Session file location:** `.vibraphone/session.json`
  - Runtime state separate from governance docs (`.planning/vibraphone/`)
- **Session data (extended):**
  - Current task ID
  - Worktree path
  - Start timestamp
  - Branch name
- **Update timing:** On state changes only (after start_task, merge_task, cleanup_task)
  - No periodic writes
  - No writes on every tool call

#### Cleanup Safety Guards

- **Uncommitted changes:** Fail with error
  - Message: "Uncommitted changes in worktree. Commit or stash before cleanup."
- **Unmerged branch:** Fail if not merged into main
  - Message: "Task branch not merged. Run merge_task first."
- **Force option:** No force option — always enforce safety checks
- **Branch deletion:** Delete local branch after cleanup
  - Worktree removed, branch deleted, session state cleared

#### Tool Result Format

- **Include `next_steps`** in all tool results to guide agents
- **No state summary** — agent has context, don't repeat
- **No files affected list** — agent is continuing work, not handing off

### Claude's Discretion

- Exact error message formatting
- Session JSON schema details (field names, types)
- Worktree creation command sequence (git worktree add specifics)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| WKTREE-01 | start_task — Create worktree + branch for a task | Use `git worktree add -b feat/{task-id} {path} main` to create worktree with new branch. Path from config: `{worktrees_path}/{repo-name}/{task-id}/`. |
| WKTREE-02 | merge_task — Rebase task branch into main | Use `git rebase --onto main main feat/{task-id}` in worktree. On conflict: `git rebase --abort`, report conflicted files. |
| WKTREE-03 | cleanup_task — Remove worktree and delete branch | Use `git worktree remove {path}` then `git branch -d feat/{task-id}`. Safety checks: no uncommitted changes, branch merged. |
| WKTREE-04 | Worktrees at configurable path | Use `worktrees_path` from VibraphoneConfig (default `~/.vibraphone/worktrees/`). Already implemented in config.py. |
| SESS-01 | Session recovery on startup when vibraphone.yaml detected | Check for session.json on server startup via FastMCP lifespan or early init. Log message if stale session found. |
| SESS-02 | recover_session tool to check for stale sessions | Read session.json, check if worktree exists and is valid. Return session state or "no session" message. |
| SESS-03 | Session state persisted in .vibraphone/session.json | Use Pydantic model for session data. Write atomically (write to temp, rename). Read on startup. |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastmcp | >=2.0 | MCP server framework | Already in use, provides `@mcp.tool()` decorator |
| pydantic | >=2.0 | Session model validation | Already in use for config and errors |
| asyncio.subprocess | stdlib | Git command execution | Non-blocking subprocess calls, matches Phase 3 pattern |
| pathlib.Path | stdlib | Path manipulation | Cross-platform, `.expanduser()` for tilde handling |

### External CLIs (Required)
| CLI | Purpose | When to Use |
|-----|---------|-------------|
| git worktree add | Create isolated worktree | start_task |
| git worktree remove | Remove worktree | cleanup_task |
| git worktree list | Check existing worktrees | Validation, recovery |
| git rebase | Merge task branch | merge_task |
| git branch -d | Delete merged branch | cleanup_task |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| git worktree | git clone | Worktree shares .git, faster, less disk space |
| git rebase | git merge --squash | Rebase maintains linear history, matches locked decision |
| asyncio.subprocess | subprocess.run | subprocess.run blocks event loop — never use in async |
| .vibraphone/session.json | .planning/vibraphone/session.json | Runtime state separate from governance docs per locked decision |

**Installation:**
```bash
# vibraphone already has dependencies
# Git is external dependency (assumed present)
# No additional PyPI packages needed for this phase
```

## Architecture Patterns

### Recommended Project Structure
```
src/vibraphone/
├── server.py           # FastMCP instance, startup hooks
├── config.py           # Config loading (existing)
├── tools/
│   ├── __init__.py     # Tool exports
│   ├── task_tools.py   # Task management (existing)
│   └── worktree_tools.py  # Worktree MCP tools (NEW)
└── utils/
    ├── __init__.py
    ├── cli_runner.py   # Async subprocess wrapper (existing)
    └── session.py      # Session state persistence (NEW)
```

### Pattern 1: Git Worktree Creation
**What:** Create isolated worktree with new branch from main
**When to use:** start_task tool
**Example:**
```python
# Source: Git documentation + CONTEXT.md locked decisions
import asyncio
from pathlib import Path

async def create_worktree(
    task_id: str,
    worktrees_path: Path,
    project_root: Path,
    repo_name: str,
) -> Path:
    """Create git worktree for task.

    Args:
        task_id: Task identifier (from br output)
        worktrees_path: Base path for worktrees (from config)
        project_root: Main repository root
        repo_name: Repository directory name

    Returns:
        Path to created worktree

    Raises:
        WorktreeError: If branch exists or creation fails
    """
    branch_name = f"feat/{task_id}"
    worktree_path = worktrees_path / repo_name / task_id

    # Ensure parent directory exists
    worktree_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if branch already exists
    check = await asyncio.create_subprocess_exec(
        "git", "branch", "--list", branch_name,
        cwd=project_root,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await check.communicate()

    if stdout.decode().strip():
        raise WorktreeError(
            error_type="BranchAlreadyExists",
            message=f"Branch {branch_name} already exists — task may already be in progress",
            suggested_action="Check existing worktrees with 'git worktree list' or cleanup previous attempt",
        )

    # Create worktree with new branch
    process = await asyncio.create_subprocess_exec(
        "git", "worktree", "add", "-b", branch_name,
        str(worktree_path), "main",
        cwd=project_root,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()

    if process.returncode != 0:
        raise WorktreeError(
            error_type="WorktreeCreationFailed",
            message=f"Failed to create worktree: {stderr.decode()}",
            suggested_action="Check disk space and permissions",
        )

    return worktree_path
```

### Pattern 2: Rebase with Conflict Handling
**What:** Rebase task branch onto main with conflict detection and abort
**When to use:** merge_task tool
**Example:**
```python
# Source: CONTEXT.md locked decisions + Git documentation
async def rebase_onto_main(
    worktree_path: Path,
    branch_name: str,
) -> dict:
    """Rebase task branch onto main.

    Args:
        worktree_path: Path to task worktree
        branch_name: Branch being rebased

    Returns:
        Dict with success status or conflict details

    Raises:
        RebaseError: If rebase fails (includes conflict info)
    """
    # Fetch latest main
    fetch = await asyncio.create_subprocess_exec(
        "git", "fetch", "origin", "main",
        cwd=worktree_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await fetch.communicate()

    # Attempt rebase
    process = await asyncio.create_subprocess_exec(
        "git", "rebase", "origin/main",
        cwd=worktree_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()

    if process.returncode != 0:
        # Get conflicted files
        diff_process = await asyncio.create_subprocess_exec(
            "git", "diff", "--name-only", "--diff-filter=U",
            cwd=worktree_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await diff_process.communicate()
        conflicted_files = stdout.decode().strip().split("\n")

        # Abort rebase to restore clean state
        abort = await asyncio.create_subprocess_exec(
            "git", "rebase", "--abort",
            cwd=worktree_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await abort.communicate()

        raise RebaseError(
            error_type="RebaseConflict",
            message=f"Rebase conflicts detected in {len(conflicted_files)} file(s)",
            suggested_action="Resolve conflicts manually, then retry merge_task",
            conflicted_files=conflicted_files,
        )

    return {"success": True, "branch": branch_name}
```

### Pattern 3: Session State Persistence
**What:** Pydantic model for session state with atomic file writes
**When to use:** Session management across all worktree tools
**Example:**
```python
# Source: Existing Pydantic patterns + CONTEXT.md session schema
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel
import json
import tempfile

class SessionState(BaseModel):
    """Session state persisted to .vibraphone/session.json."""

    task_id: str
    worktree_path: Path
    branch_name: str
    started_at: datetime

    # Allow Path serialization
    class Config:
        json_encoders = {
            Path: str,
            datetime: lambda v: v.isoformat(),
        }

    def model_dump_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps({
            "task_id": self.task_id,
            "worktree_path": str(self.worktree_path),
            "branch_name": self.branch_name,
            "started_at": self.started_at.isoformat(),
        })


class SessionManager:
    """Manages session state persistence."""

    def __init__(self, project_root: Path):
        self.session_file = project_root / ".vibraphone" / "session.json"

    def load(self) -> SessionState | None:
        """Load session state if exists."""
        if not self.session_file.exists():
            return None

        data = json.loads(self.session_file.read_text())
        return SessionState(**data)

    def save(self, state: SessionState) -> None:
        """Atomically save session state."""
        self.session_file.parent.mkdir(parents=True, exist_ok=True)

        # Write to temp file, then rename (atomic on POSIX)
        with tempfile.NamedTemporaryFile(
            mode="w",
            dir=self.session_file.parent,
            delete=False,
        ) as f:
            f.write(state.model_dump_json())
            temp_path = Path(f.name)

        temp_path.rename(self.session_file)

    def clear(self) -> None:
        """Clear session state."""
        if self.session_file.exists():
            self.session_file.unlink()
```

### Pattern 4: Safety Guard Checks
**What:** Pre-cleanup validation for uncommitted changes and merge status
**When to use:** cleanup_task tool
**Example:**
```python
# Source: CONTEXT.md locked decisions + Git documentation
async def check_uncommitted_changes(worktree_path: Path) -> list[str]:
    """Check for uncommitted changes in worktree.

    Returns list of changed files, empty if clean.
    """
    process = await asyncio.create_subprocess_exec(
        "git", "status", "--porcelain",
        cwd=worktree_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await process.communicate()

    lines = stdout.decode().strip().split("\n")
    return [line[3:] for line in lines if line]


async def check_branch_merged(branch_name: str, project_root: Path) -> bool:
    """Check if branch is merged into main."""
    process = await asyncio.create_subprocess_exec(
        "git", "branch", "--merged", "main", "--list", branch_name,
        cwd=project_root,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await process.communicate()

    return bool(stdout.decode().strip())
```

### Anti-Patterns to Avoid
- **Using subprocess.run()** — Blocks event loop, use asyncio.create_subprocess_exec
- **Not handling tilde in paths** — Use Path.expanduser() for worktrees_path
- **Forgetting to abort failed rebase** — Must run git rebase --abort before returning error
- **Deleting worktree without safety checks** — Always check uncommitted changes and merge status
- **Writing session.json non-atomically** — Use temp file + rename for crash safety
- **Auto-resuming sessions** — Per locked decision: log only, agent decides

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Git operations | Python git library | git CLI via subprocess | Git CLI is authoritative, no library API drift |
| Path handling | String concatenation | pathlib.Path | Cross-platform, handles edge cases |
| Tilde expansion | Manual ~ replacement | Path.expanduser() | Handles HOME, edge cases |
| JSON persistence | Custom serializer | Pydantic model_dump_json() | Type-safe, consistent with existing patterns |
| Atomic file writes | Direct open/write | tempfile + rename | Crash-safe on POSIX |

**Key insight:** Git CLI is the source of truth. Python git libraries add abstraction without benefit for our simple use case.

## Common Pitfalls

### Pitfall 1: Worktree Path Not Expanded
**What goes wrong:** `~/.vibraphone/worktrees/` passed to git without tilde expansion
**Why it happens:** Config stores string, git needs absolute path
**How to avoid:** Always call `Path.expanduser()` on worktrees_path
**Warning signs:** Git error "could not create directory"

### Pitfall 2: Rebase Leaves Worktree in Bad State
**What goes wrong:** Failed rebase leaves worktree in detached/conflict state
**Why it happens:** Not running git rebase --abort on failure
**How to avoid:** Always abort rebase in exception handler before returning error
**Warning signs:** Subsequent git operations fail with "rebase in progress"

### Pitfall 3: Deleting Active Worktree
**What goes wrong:** Cleanup deletes worktree while agent is still working
**Why it happens:** No check for uncommitted changes
**How to avoid:** Run `git status --porcelain` before `git worktree remove`
**Warning signs:** Lost work after cleanup

### Pitfall 4: Session.json Corruption
**What goes wrong:** Partial write leaves invalid JSON
**Why it happens:** Crash during write, no atomicity
**How to avoid:** Write to temp file, then rename (atomic on POSIX)
**Warning signs:** JSON parse errors on startup

### Pitfall 5: Branch Name Collision
**What goes wrong:** start_task creates branch that already exists
**Why it happens:** Previous task not cleaned up, or concurrent start
**How to avoid:** Check `git branch --list` before `git worktree add -b`
**Warning signs:** "fatal: a branch named 'feat/xxx' already exists"

## Code Examples

### start_task Implementation
```python
# Source: CONTEXT.md + existing patterns from task_tools.py
from vibraphone.server import mcp
from vibraphone.config import get_config

@mcp.tool
async def start_task(task_id: str) -> dict:
    """Start task in isolated git worktree.

    Creates worktree at {worktrees_path}/{repo-name}/{task-id}/
    with branch feat/{task-id} from main.

    Args:
        task_id: Task identifier (e.g., bd-abc123)

    Returns:
        Dict with worktree_path, branch_name, and next_steps

    Raises:
        WorktreeError: If branch exists or creation fails
    """
    config = get_config()
    project_root = get_project_root()
    repo_name = project_root.name

    worktree_path = await create_worktree(
        task_id=task_id,
        worktrees_path=config.worktrees_path,
        project_root=project_root,
        repo_name=repo_name,
    )

    branch_name = f"feat/{task_id}"

    # Save session state
    session = SessionManager(project_root)
    session.save(SessionState(
        task_id=task_id,
        worktree_path=worktree_path,
        branch_name=branch_name,
        started_at=datetime.now(),
    ))

    return {
        "worktree_path": str(worktree_path),
        "branch_name": branch_name,
        "next_steps": [
            f"Work in the worktree: cd {worktree_path}",
            "Make changes and commit them",
            "When done, call merge_task to integrate into main",
        ],
    }
```

### merge_task Implementation
```python
# Source: CONTEXT.md locked decisions
@mcp.tool
async def merge_task(task_id: str) -> dict:
    """Rebase task branch into main.

    Args:
        task_id: Task identifier

    Returns:
        Dict with success status and next_steps

    Raises:
        RebaseError: If conflicts detected (includes file list)
    """
    project_root = get_project_root()
    session = SessionManager(project_root)
    state = session.load()

    if not state or state.task_id != task_id:
        return WorktreeError(
            error_type="NoActiveSession",
            message=f"No active session for task {task_id}",
            suggested_action="Run start_task first",
        ).model_dump()

    branch_name = state.branch_name
    worktree_path = state.worktree_path

    try:
        await rebase_onto_main(worktree_path, branch_name)
    except RebaseError as e:
        return e.model_dump()

    return {
        "success": True,
        "branch": branch_name,
        "next_steps": [
            "Rebase successful",
            "Run cleanup_task to remove worktree and delete branch",
        ],
    }
```

### cleanup_task Implementation
```python
# Source: CONTEXT.md locked decisions
@mcp.tool
async def cleanup_task(task_id: str) -> dict:
    """Remove worktree and delete branch after merge.

    Args:
        task_id: Task identifier

    Returns:
        Dict with success status and next_steps

    Raises:
        WorktreeError: If uncommitted changes or branch not merged
    """
    project_root = get_project_root()
    session = SessionManager(project_root)
    state = session.load()

    if not state or state.task_id != task_id:
        return WorktreeError(
            error_type="NoActiveSession",
            message=f"No active session for task {task_id}",
            suggested_action="Run start_task first",
        ).model_dump()

    worktree_path = state.worktree_path
    branch_name = state.branch_name

    # Safety check: uncommitted changes
    changes = await check_uncommitted_changes(worktree_path)
    if changes:
        return WorktreeError(
            error_type="UncommittedChanges",
            message=f"Uncommitted changes in worktree. Commit or stash before cleanup.",
            suggested_action=f"Files with changes: {', '.join(changes[:5])}",
        ).model_dump()

    # Safety check: branch merged
    if not await check_branch_merged(branch_name, project_root):
        return WorktreeError(
            error_type="BranchNotMerged",
            message="Task branch not merged. Run merge_task first.",
            suggested_action="Run merge_task to rebase onto main",
        ).model_dump()

    # Remove worktree
    remove = await asyncio.create_subprocess_exec(
        "git", "worktree", "remove", str(worktree_path),
        cwd=project_root,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await remove.communicate()

    if remove.returncode != 0:
        return WorktreeError(
            error_type="WorktreeRemovalFailed",
            message=f"Failed to remove worktree: {stderr.decode()}",
            suggested_action="Check if worktree directory is in use",
        ).model_dump()

    # Delete branch
    delete = await asyncio.create_subprocess_exec(
        "git", "branch", "-d", branch_name,
        cwd=project_root,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await delete.communicate()

    # Clear session
    session.clear()

    return {
        "success": True,
        "next_steps": [
            "Worktree removed and branch deleted",
            "Task is complete — mark it complete with complete_task",
        ],
    }
```

### recover_session Implementation
```python
# Source: CONTEXT.md locked decisions
@mcp.tool
async def recover_session() -> dict:
    """Check for stale session and return state.

    Returns session info if active session exists, or message if none.
    Use this after server startup to resume interrupted work.
    """
    project_root = get_project_root()
    session = SessionManager(project_root)
    state = session.load()

    if not state:
        return {
            "session": None,
            "message": "No active session found",
        }

    # Check if worktree still exists
    if not state.worktree_path.exists():
        return {
            "session": None,
            "message": f"Stale session for task {state.task_id} — worktree no longer exists",
            "suggested_action": "Run cleanup_task to clear session, or start_task to begin fresh",
        }

    return {
        "session": {
            "task_id": state.task_id,
            "worktree_path": str(state.worktree_path),
            "branch_name": state.branch_name,
            "started_at": state.started_at.isoformat(),
        },
        "message": f"Session found for task {state.task_id}",
        "next_steps": [
            f"Continue work: cd {state.worktree_path}",
            "Or clean up: cleanup_task {state.task_id}",
        ],
    }
```

### Server Startup Hook
```python
# Source: FastMCP patterns + CONTEXT.md
# In server.py

def check_stale_session() -> None:
    """Check for stale session on startup (log only, no auto-resume)."""
    config_path = find_config_file()
    if not config_path:
        return  # Not a vibraphone project

    project_root = config_path.parent
    session = SessionManager(project_root)
    state = session.load()

    if state:
        print(
            f"Session found: task {state.task_id} in worktree {state.worktree_path}. "
            f"Call recover_session to continue.",
            file=sys.stderr,
        )


def main() -> None:
    """Entry point for vibraphone MCP server."""
    print("vibraphone MCP server starting (v0.1.0)", file=sys.stderr)

    # Check for stale session on startup
    check_stale_session()

    mcp.run(transport="stdio")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| In-project worktrees | External ~/.vibraphone/worktrees/ | Migration | Cleaner separation, less agent confusion |
| Merge commits | Rebase onto main | Locked decision | Linear history, cleaner git log |
| Auto-resume sessions | Log-only, agent decides | Locked decision | Safer recovery, agent has context |
| subprocess.run() | asyncio.create_subprocess_exec() | Phase 3 | Non-blocking, proper async |

**Deprecated/outdated:**
- `subprocess.run()` in async context: Always use asyncio subprocess
- `subprocess.Popen()` directly: Use asyncio.create_subprocess_exec

## Open Questions

1. **FastMCP Startup Hook Behavior**
   - What we know: FastMCP has lifespan events, but they may not trigger until client connects (per web research)
   - What's unclear: Exact timing of startup hooks vs server ready
   - Recommendation: Call check_stale_session() synchronously in main() before mcp.run() — simple and reliable

2. **Branch Name Sanitization**
   - What we know: Task IDs come from br output
   - What's unclear: Do we need to sanitize task IDs for branch names?
   - Recommendation: Assume br returns valid IDs. Add validation if issues arise.

3. **Worktree Path Length Limits**
   - What we know: Long paths can cause issues on some systems
   - What's unclear: Max safe path length
   - Recommendation: Use task_id as directory name (typically short). No action needed.

## Sources

### Primary (HIGH confidence)
- Git documentation (git-scm.com) — worktree commands, rebase, conflict handling
- Python asyncio documentation — create_subprocess_exec patterns
- Pydantic v2 documentation — BaseModel, model_dump patterns
- Project config.py — existing VibraphoneConfig with worktrees_path

### Secondary (MEDIUM confidence)
- Web search: Git worktree best practices 2025 — command syntax verified
- Web search: Git rebase conflict handling — abort patterns confirmed
- Web search: Python asyncio subprocess — best practices confirmed
- Phase 3 RESEARCH.md — established patterns for CLI wrapping

### Tertiary (LOW confidence)
- FastMCP lifecycle hooks — behavior unclear, using synchronous fallback

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — git CLI is stable, asyncio patterns established in Phase 3
- Architecture: HIGH — patterns follow existing task_tools.py structure
- Pitfalls: HIGH — git edge cases are well-documented

**Research date:** 2026-02-16
**Valid until:** 30 days (git CLI stable, asyncio patterns stable, Pydantic v2 stable)
