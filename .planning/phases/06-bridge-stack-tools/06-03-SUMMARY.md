---
phase: 06-bridge-stack-tools
plan: 03
subsystem: stack-configuration
tags: [justfile, vibraphone-yaml, mcp-tool, stack-config]

# Dependency graph
requires:
  - phase: 06-01
    provides: STACK_DEFAULTS config with 6 language defaults
provides:
  - configure_stack MCP tool for generating per-component Justfile recipes
  - Section-based Justfile update preserving manual customizations
  - vibraphone.yaml components section update
  - Optional Stitch integration via stitch_project_id parameter
affects: [phase-07-init-project]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Section-based Justfile update with markers (# === COMPONENT RECIPES ===)"
    - "Two-phase preview flow (preview=True default)"
    - "Config cache clearing after write via clear_config_cache()"

key-files:
  created:
    - src/vibraphone/tools/stack_tools.py
  modified:
    - src/vibraphone/server.py

key-decisions:
  - "Section-based Justfile update (not full regeneration) to preserve manual customizations"
  - "Two-phase preview flow with preview=True as default for agent review before write"
  - "Per-component recipes marked [private] to avoid cluttering just --list"

patterns-established:
  - "MCP tool pattern: @mcp.tool decorator, async function, dict return with status/next_steps"
  - "Section markers for idempotent file updates: _COMPONENT_RECIPES_START/_END"

requirements-completed: [STACK-01]

# Metrics
duration: 2min
completed: 2026-02-17
---

# Phase 6 Plan 3: Stack Configuration Tool Summary

**configure_stack MCP tool that generates per-component Justfile recipes and updates vibraphone.yaml with section-based updates preserving manual customizations**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-17T08:17:26Z
- **Completed:** 2026-02-17T08:19:47Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Created configure_stack MCP tool with section-based Justfile update
- Two-phase preview flow (preview=True default) for agent review before write
- vibraphone.yaml components section update preserving other sections
- Optional Stitch integration via stitch_project_id parameter
- Config cache clearing after write for immediate reload

## Task Commits

Each task was committed atomically:

1. **Task 1: Create stack_tools.py with configure_stack** - `9b43306` (feat)
2. **Task 2: Register stack_tools in server** - `b727a09` (feat)

**Plan metadata:** pending (docs: complete plan)

## Files Created/Modified

- `src/vibraphone/tools/stack_tools.py` - configure_stack MCP tool with Justfile recipe generation
- `src/vibraphone/server.py` - Added stack_tools import for auto-registration

## Decisions Made

- Used section-based Justfile update with markers (`# === COMPONENT RECIPES ===`) to preserve manual customizations outside the component section
- Per-component recipes marked `[private]` to keep `just --list` clean
- Helper functions extracted for testability: `_render_component_recipes`, `_render_component_section`, `_update_justfile_section`, `_render_vibraphone_yaml`, `_update_env_var`, `_sync_mcp_config`

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- configure_stack tool ready for use by init_project in Phase 7
- Section-based update pattern established for future file generation tools
- STACK_DEFAULTS integration tested and working

---
*Phase: 06-bridge-stack-tools*
*Completed: 2026-02-17*
