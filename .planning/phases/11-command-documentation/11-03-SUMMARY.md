---
phase: 11-command-documentation
plan: 03
subsystem: docs
tags: [documentation, slash-commands, troubleshooting]

# Dependency graph
requires:
  - phase: 11-02
    provides: Start Work and Run Quality command documentation
provides:
  - Full coverage documentation for Commit & Merge commands
  - Full coverage documentation for Session Management commands
  - Comprehensive Troubleshooting section
affects: [command-reference, user-guide]

# Tech tracking
tech-stack:
  added: []
  patterns: [full-coverage-documentation, dual-error-approach]

key-files:
  created: []
  modified:
    - src/vibraphone/commands/v.md

key-decisions:
  - "Troubleshooting section follows dual approach: inline command errors +
    centralized section for cross-cutting issues"
  - "Quality gate, worktree, and session issues grouped for discoverability"

patterns-established:
  - "Full coverage: typical usage, success response, edge cases, common
    mistakes"
  - "Troubleshooting structure: Quality Gate > Worktree > Session issues"

requirements-completed: [SLASH-01, SLASH-04]

# Metrics
duration: 15min
completed: 2026-02-20
---

# Phase 11 Plan 03: Commit, Merge, Session, Troubleshooting Documentation

**Full coverage documentation for Commit & Merge and Session Management
commands, plus comprehensive Troubleshooting section covering quality gate,
worktree, and session errors.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-02-20T00:31:27Z
- **Completed:** 2026-02-20T00:46:00Z
- **Tasks:** 3
- **Files modified:** 1

## Accomplishments

- Documented /v commit with quality gate enforcement details (tests, lint,
  review required)
- Documented /v merge with conflict resolution workflow
- Documented /v cleanup and /v complete with typical completion workflow
- Documented /v status, /v health, /v recover with response details and edge
  cases
- Added Troubleshooting section with Quality Gate Failures (test/lint/review/API
  key)
- Added Troubleshooting section with Worktree Issues (conflicts/uncommitted/
  branch)
- Added Troubleshooting section with Session Issues (no session/recovery)

## Task Commits

Each task was committed atomically:

1. **Task 1: Document Commit & Merge commands with full coverage** -
   `3c6ad9a` (docs)
2. **Task 2: Document Session Management commands with full coverage** -
   `459f104` (docs)
3. **Task 3: Add Troubleshooting section** - `a5d2c6e` (docs)

## Files Created/Modified

- `src/vibraphone/commands/v.md` - Added full coverage documentation for
  commit/merge/cleanup/complete/status/health/recover commands; added
  Troubleshooting section

## Decisions Made

- Troubleshooting section organized by error category (Quality Gate, Worktree,
  Session) for easy navigation
- Each error type includes resolution steps with specific commands
- Maintained dual approach: inline command errors + centralized troubleshooting

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all documentation tasks completed without issues.

## User Setup Required

None - documentation-only plan.

## Next Phase Readiness

- All workflow commands now have full coverage documentation
- Troubleshooting section provides centralized error resolution reference
- Ready for Plan 11-04 (remaining documentation tasks)

## Self-Check: PASSED

- FOUND: SUMMARY.md
- FOUND: v.md
- FOUND: 3c6ad9a (Task 1 commit)
- FOUND: 459f104 (Task 2 commit)
- FOUND: a5d2c6e (Task 3 commit)

---
*Phase: 11-command-documentation*
*Completed: 2026-02-20*
