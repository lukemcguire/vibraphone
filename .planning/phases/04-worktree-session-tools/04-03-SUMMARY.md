---
phase: 04-worktree-session-tools
plan: 03
subsystem: worktree
tags: [git, worktree, mcp-tools, session-management, rebase]

# Dependency graph
requires:
  - phase: 04-01
    provides: SessionState and SessionManager for session persistence
  - phase: 04-02
    provides: create_worktree, rebase_onto_main, check_uncommitted_changes, check_branch_merged, remove_worktree
provides:
  - start_task MCP tool - creates worktree and branch for task
  - merge_task MCP tool - rebases task branch onto main
  - cleanup_task MCP tool - removes worktree with safety guards
  - recover_session MCP tool - checks for stale sessions
affects: [quality-gate, gsd-integration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - MCP tool registration via @mcp.tool decorator
    - Session state integration with worktree lifecycle
    - Safety guard pattern for destructive operations

key-files:
  created:
    - src/vibraphone/tools/worktree_tools.py
  modified:
    - src/vibraphone/server.py

key-decisions:
  - "TaskError reused for consistent error format across worktree tools"
  - "Session not cleared after merge_task - cleanup_task handles complete cleanup"
  - "Branch deletion failure ignored in cleanup_task - might already be gone"

patterns-established:
  - "MCP tools import existing utilities from utils/ and reuse error patterns"
  - "SessionManager integrated into worktree lifecycle for state tracking"
  - "Safety guards check preconditions before destructive operations"

requirements-completed: [WKTREE-01, WKTREE-02, WKTREE-03, SESS-02]

# Metrics
duration: 3min
completed: 2026-02-17
---

# Phase 04 Plan 03: Worktree Lifecycle MCP Tools Summary

**MCP tools for worktree lifecycle: start_task, merge_task, cleanup_task, and recover_session with safety guards and session state integration**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-17T02:57:30Z
- **Completed:** 2026-02-17T03:00:53Z
- **Tasks:** 5
- **Files modified:** 2

## Accomplishments
- start_task MCP tool creates worktree at configured path with feat/{task-id} branch
- merge_task MCP tool rebases onto main with conflict handling via RebaseError
- cleanup_task MCP tool removes worktree with safety guards for uncommitted changes and unmerged branches
- recover_session MCP tool checks for stale sessions and returns session state
- All 4 tools registered in MCP server and accessible to agents

## Task Commits

Each task was committed atomically:

1. **Task 1: Create worktree_tools.py with start_task** - `168c051` (feat)
2. **Task 2: Add merge_task tool** - `439a507` (feat)
3. **Task 3: Add cleanup_task tool** - `62e3763` (feat)
4. **Task 4: Add recover_session tool** - `8e191cd` (feat)
5. **Task 5: Register tools in server** - `d498f48` (feat)

## Files Created/Modified
- `src/vibraphone/tools/worktree_tools.py` - MCP tools for worktree lifecycle (236 lines)
- `src/vibraphone/server.py` - Added worktree_tools import for tool registration

## Decisions Made
- Reused TaskError from task_tools.py for consistent error format across all tools
- Session state NOT cleared after merge_task - cleanup_task handles complete cleanup workflow
- Branch deletion failure in cleanup_task ignored gracefully (branch might already be gone)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None - all imports and registrations worked on first attempt.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Worktree lifecycle tools complete, ready for quality gate integration (Phase 5)
- All 4 tools registered with MCP and functional

---
*Phase: 04-worktree-session-tools*
*Completed: 2026-02-17*

## Self-Check: PASSED

- worktree_tools.py: FOUND
- Task 1 commit (168c051): FOUND
- Task 2 commit (439a507): FOUND
- Task 3 commit (62e3763): FOUND
- Task 4 commit (8e191cd): FOUND
- Task 5 commit (d498f48): FOUND
