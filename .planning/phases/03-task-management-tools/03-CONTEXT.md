# Phase 3: Task Management Tools - Context

**Gathered:** 2026-02-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Agent calls MCP tools to manage tasks via beads_rust (list, query, complete, abandon, get context). This phase wraps existing `br` CLI commands as MCP tools. Task creation by agents is out of scope — tasks come from plan files or direct user manipulation.

</domain>

<decisions>
## Implementation Decisions

### Filters

- list_tasks supports filtering by status and plan
- Status values defined by beads_rust (ready, in_progress, completed, blocked)
- No filtering by phase or other metadata for v1

### Context Bundle

- get_task_context returns: task details, mermaid diagrams (from architecture.md), recent commits on task branch
- Requires active worktree — includes branch-specific context (commits, diffs)
- Look at existing `beads_tools.py` for reference implementation

### Error Handling

- Structured errors with: error type, message, and suggested action
- Example: "CannotCompleteBlockedTask" with message and suggestion to check dependencies

### next_ready Selection

- Uses critical path / PageRank approach from beads_viewer
- Returns task that is most blocking or on critical path
- Reference: beads_viewer README "Ready-made Blurb" section for algorithm details

### complete_task

- Records: status change, timestamp, optional notes
- Notes added at completion time

### abandon_task

- Requires reason for audit trail
- Resets task status to ready
- Notes captured with reason

### Dependency Graph

- list_tasks returns full dependency graph
- Agent can understand task relationships, parallel work opportunities, critical path
- No need for separate graph query

### Task Operations

- One task at a time — no batch operations
- No task editing — tasks are immutable once created
- Agents cannot create tasks — only work with existing tasks from plans

### Concurrency

- Task claiming prevents conflicts
- Once a task is claimed by an agent, not available to others
- Check existing implementation for claiming mechanism

### Ordering

- list_tasks ordered by priority (from beads_rust)

### Notes Field

- Notes can be added at complete and abandon operations
- Not editable separately

### Claude's Discretion

- Empty list/no ready task response format
- Task status values (verify with beads_rust)
- Metadata fields (created_at, updated_at, etc.)
- Exact task shape/fields in output
- Exact claiming mechanism implementation

</decisions>

<specifics>
## Specific Ideas

- **Primary approach:** Migrate existing `beads_tools.py` from vibraphone-template — working, tested code already exists
- **Critical path logic:** See beads_viewer for PageRank, critical paths, cycles, parallel tracks computation
- **Key references:**
  - beads_rust: https://github.com/Dicklesworthstone/beads_rust
  - br AGENTS.md: https://github.com/Dicklesworthstone/beads_rust/blob/main/AGENTS.md
  - beads_viewer: https://github.com/Dicklesworthstone/beads_viewer

</specifics>

<deferred>
## Deferred Ideas

- Task creation by agents — out of scope (user adds tasks directly or via plan import)
- Task editing — tasks are immutable
- Batch operations — one-at-a-time is sufficient for v1
- Phase-level filtering — not needed yet

</deferred>

---

*Phase: 03-task-management-tools*
*Context gathered: 2026-02-16*
