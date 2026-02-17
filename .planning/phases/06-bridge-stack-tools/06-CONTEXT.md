# Phase 6: Bridge & Stack Tools - Context

**Gathered:** 2026-02-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Integration layer connecting GSD planning to beads_rust task management and Justfile build configuration. Two tools:
1. **import_gsd_plan** — Parse GSD PLAN.md files and create beads issues with dependencies
2. **configure_stack** — Generate Justfile recipes and vibraphone.yaml from component definitions

This is a migration from `/home/luke/workspace/github.com/lukemcguire/vibraphone-template/.mcp/servers/vibraphone/tools/bridge_tools.py` and `stack_tools.py`.

</domain>

<decisions>
## Implementation Decisions

### Import Behavior

- **Idempotency**: Skip if `plan:<id>` label already exists in beads — write-once model
- **Plan updates**: If tasks need changes after import, edit beads directly (complete_task, abandon_task, manual edit)
- **Re-import purpose**: Error recovery only (e.g., API failed mid-import), not plan evolution
- **No tasks in plan**: Warn and skip that plan, continue with others
- **Multi-plan import**: Import all plans in a phase at once (current behavior)

### Dependency Mapping

- **Intra-plan deps**: Explicit only via optional `<blocked_by>` XML field inside `<task>` elements
  - No implicit sequential deps (tasks are parallel by default)
  - If ordering needed, plan author adds `<blocked_by>task-name</blocked_by>`
- **Inter-plan deps**: First task of dependent plan blocked by last task of dependency plan
  - Uses GSD frontmatter `depends_on: ["01-01"]` as currently
  - Convention: last task in a plan represents "plan complete"
- **Missing deps**: Not a concern — all plans imported together, references resolve
- **Cycles**: Let beads_rust reject invalid deps (no cycle detection in vibraphone)

### Stack Scope

- **Generated from components**: Quality gate recipes (test, lint, format per component)
- **Static (base template from init_project)**: Worktree ops, Beads helpers, Setup/debug recipes
- **configure_stack behavior**: Section update only — insert/update component recipes, don't regenerate full Justfile
- **STACK_DEFAULTS languages**: python, typescript, go (current) + add rust, ruby, java
- **Stitch integration**: Keep Stitch support — will be used after migration

### Safety & Recovery

- **Two-phase flow**: `preview=True` by default (returns proposals), `preview=False` to write
- **Validation**: Fail-fast — validate all plan files before creating any beads tasks
- **Rollback**: No automatic rollback on partial failure
  - Report what succeeded/failed clearly
  - Rely on idempotency for recovery (re-import skips existing)
- **Error handling**: Clear error messages with suggested actions

### Claude's Discretion

- Exact format of `<blocked_by>` XML field (single task ref vs list)
- How to structure base Justfile template for init_project
- Exact validation checks for plan structure
- Error message wording and format

</decisions>

<specifics>
## Specific Ideas

- **Migration source**: `/home/luke/workspace/github.com/lukemcguire/vibraphone-template/.mcp/servers/vibraphone/tools/bridge_tools.py` and `stack_tools.py`
- **GSD plan format**: YAML frontmatter + XML `<tasks>` blocks with `<task>`, `<title>`, `<description>`, `<labels>`, `<type>` elements
- **Beads labels**: Use `plan:<id>` (e.g., `plan:02-01`) for idempotency tracking
- **Justfile structure**: `[private]` per-component recipes, aggregate recipes for test/lint/format

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 06-bridge-stack-tools*
*Context gathered: 2026-02-16*
