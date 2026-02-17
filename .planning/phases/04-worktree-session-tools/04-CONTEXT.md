# Phase 4: Worktree & Session Tools - Context

**Gathered:** 2026-02-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Agent manages isolated git worktrees for task work, with session state persistence and automatic recovery detection on server startup. The agent can start tasks in isolated branches, merge completed work back to main, clean up worktrees, and recover from interrupted sessions.

**Scope:**
- `start_task` — Create worktree + branch for a task
- `merge_task` — Rebase task branch into main
- `cleanup_task` — Remove worktree and delete branch
- Session state persistence to `.vibraphone/session.json`
- Stale session detection on server startup (log-only, no auto-resume)

**Out of scope:**
- Quality gate tools (Phase 5)
- GSD integration (Phase 6)
- Project scaffolding (Phase 7)

</domain>

<decisions>
## Implementation Decisions

### Worktree/Branch Naming

- **Branch prefix:** `feat/{task-id}` (e.g., `feat/001-setup-auth`)
- **Task ID format:** Match br output exactly — use whatever format br returns
- **Worktree path:** `~/.vibraphone/worktrees/{repo-name}/{task-id}/`
  - `{repo-name}` derived from repository directory name
  - Base path (`~/.vibraphone/worktrees/`) configurable in vibraphone.yaml
- **Branch collision handling:** Fail with error — if branch exists, task is already in progress
- **Merge target:** Always `main` (hardcoded)
- **Active worktree tracking:** Stored in `session.json` (task_id → worktree_path mapping)

### Merge Conflict Handling

- **Merge method:** Rebase onto main (not merge commit, not squash)
- **Conflict mode:** Fail with detailed report
  - Include list of conflicted files
  - Include conflict markers/sections where possible
- **After conflict:** Abort rebase, restore worktree to pre-merge state
  - Run `git rebase --abort` before returning error
  - Agent can then pull latest main, resolve conflicts, retry

### Session Recovery Flow

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

### Cleanup Safety Guards

- **Uncommitted changes:** Fail with error
  - Message: "Uncommitted changes in worktree. Commit or stash before cleanup."
- **Unmerged branch:** Fail if not merged into main
  - Message: "Task branch not merged. Run merge_task first."
- **Force option:** No force option — always enforce safety checks
- **Branch deletion:** Delete local branch after cleanup
  - Worktree removed, branch deleted, session state cleared

### Tool Result Format

- **Include `next_steps`** in all tool results to guide agents
- **No state summary** — agent has context, don't repeat
- **No files affected list** — agent is continuing work, not handing off

### Claude's Discretion

- Exact error message formatting
- Session JSON schema details (field names, types)
- Worktree creation command sequence (git worktree add specifics)

</decisions>

<specifics>
## Specific Ideas

- "Remember, this is primarily a migration" — refer to existing implementation in `vibraphone-template/.mcp/servers/vibraphone/` for patterns
- `next_steps` in results is an existing pattern — agents expect guidance on what to do next
- Session recovery has a known bug — may need debugging during migration (noted in STATE.md)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 04-worktree-session-tools*
*Context gathered: 2026-02-16*
