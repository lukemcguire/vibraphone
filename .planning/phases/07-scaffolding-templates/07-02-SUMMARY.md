---
phase: 07-scaffolding-templates
plan: 02
subsystem: scaffolding
tags: [prerequisites, platform-detection, mcp-tool]

# Dependency graph
requires: []
provides:
  - Prerequisite detection utility (check_prerequisites)
  - Platform-aware install commands for br, bv, git, just, node
  - MCP tool for dependency checking
affects: [init_project, scaffolding]

# Tech tracking
tech-stack:
  added: []
  patterns: [stdlib-only detection, dataclass output format]

key-files:
  created:
    - src/vibraphone/utils/prerequisites.py
    - src/vibraphone/tools/scaffold_tools.py
  modified:
    - src/vibraphone/server.py

key-decisions:
  - "Core dependencies (br, bv, git) distinguished from optional (just, node) in missing_core field"
  - "Platform detection via platform.system() returning Darwin/Linux/Windows"

patterns-established:
  - "Prerequisite dataclass for structured tool status"
  - "INSTALL_COMMANDS dict mapping tool -> platform -> install command"

requirements-completed: [NEW-08, NEW-09]

# Metrics
duration: 2min
completed: 2026-02-17
---

# Phase 07 Plan 02: Prerequisites Utility Summary

**Prerequisite detection utility with platform-aware install commands, exposed via check_prerequisites MCP tool**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-17T09:26:25Z
- **Completed:** 2026-02-17T09:28:32Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Created prerequisites.py utility detecting br, bv, git, just, node
- Platform-aware install commands (Darwin: brew, Linux: apt/brew, Windows: scoop)
- Returns structured list AND ready-to-run shell script for missing tools
- Distinguishes core dependencies (br, bv, git) from optional (just, node)
- Registered check_prerequisites as MCP tool

## Task Commits

Each task was committed atomically:

1. **Task 1: Create prerequisites utility module** - `b905577` (feat)
2. **Task 2: Create scaffold_tools.py with check_prerequisites MCP tool** - `2eef8fb` (feat)

## Files Created/Modified
- `src/vibraphone/utils/prerequisites.py` - Prerequisite detection utility with check_prerequisites() and INSTALL_COMMANDS
- `src/vibraphone/tools/scaffold_tools.py` - MCP tool wrapper exposing check_prerequisites
- `src/vibraphone/server.py` - Added scaffold_tools import for tool registration

## Decisions Made
- Core dependencies (br, bv, git) tracked separately in missing_core field for quick validation
- Shell script includes all missing tools with comments for platform alternatives
- Used stdlib only (platform, shutil, dataclasses) - no new dependencies

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Prerequisites detection ready for init_project to auto-check on scaffold
- Platform detection pattern established for future tools

---
*Phase: 07-scaffolding-templates*
*Completed: 2026-02-17*

## Self-Check: PASSED
- All claimed files exist
- All claimed commits found
