# Architecture

Vibraphone is an MCP (Model Context Protocol) server that provides tools for AI coding agents.

## System Overview

```
+-------------------------------------------------------------+
|                     MCP Client (Claude)                      |
|                    (calls vibraphone tools)                  |
+---------------------------+---------------------------------+
                            | stdio transport
                            v
+-------------------------------------------------------------+
|                   Vibraphone MCP Server                      |
+-----------------------------+-------------------------------+
|  Task Tools     |  Quality Gates  |  Worktree Tools         |
|  (list_tasks,   |  (run_tests,    |  (start_task,           |
|   next_ready,   |   run_lint,     |   merge_task,           |
|   complete...)  |   review...)    |   cleanup...)           |
+--------+--------+--------+--------+--------+----------------+
         |                 |                 |
         v                 v                 v
+----------------+ +----------------+ +------------------------+
| beads_rust CLI | | git / pytest   | | git worktree           |
| (br, bv)       | | ruff / LLM     | | .vibraphone/session    |
+----------------+ +----------------+ +------------------------+
```

## Key Components

### Configuration (config.py)

- Discovers `vibraphone.yaml` by walking up from current directory
- Validates configuration with Pydantic
- Returns sensible defaults when config missing

### Session Management (utils/session.py)

- Tracks active worktree and task
- Persists to `.vibraphone/session.json`
- Enables session recovery on server restart

### Quality Gates (tools/quality_gate_tools.py)

- Execute test/lint/format commands
- Circuit breakers for repeated failures
- LLM-powered code review via instructor + OpenRouter
- Review-before-commit enforcement

### Worktree Isolation (utils/worktree_ops.py)

- Creates isolated git worktrees per task
- Manages branch lifecycle (create, rebase, delete)
- Safety guards for uncommitted changes

## Data Flow

1. Agent calls `start_task` -> worktree created, session saved
2. Agent works in worktree, calls quality gates
3. Agent calls `request_code_review` -> LLM reviews diff
4. Agent calls `attempt_commit` -> commit only if APPROVED
5. Agent calls `merge_task` -> rebase onto main
6. Agent calls `cleanup_task` -> worktree removed

## File Locations

| Path | Purpose |
|------|---------|
| `vibraphone.yaml` | Project configuration |
| `.vibraphone/session.json` | Active session state |
| `.vibraphone/tasks/{id}/state.json` | Per-task quality gate state |
| `~/.vibraphone/worktrees/` | Worktree storage |

## Tool Categories

### Task Tools

Interface with beads_rust CLI to manage task lifecycle:
- List and query tasks with filters
- Get next unblocked task via critical path analysis
- Complete or abandon tasks
- Load context bundles for focused work

### Quality Gate Tools

Enforce quality before commits:
- Run tests with circuit breaker protection
- Run linter and formatter
- Request LLM code review (APPROVED/REJECTED)
- Attempt commit (requires approved review)

### Worktree Tools

Manage isolated worktrees per task:
- Create worktree with feature branch
- Rebase onto main for integration
- Clean up worktree and branch after merge
- Recover interrupted sessions

### Scaffold Tools

Initialize vibraphone in new projects:
- Check for required dependencies (br, bv, git)
- Generate configuration files from templates
- Handle file conflicts with unified diffs

### Bridge Tools

Import external planning into beads:
- Import GSD PLAN.md files as beads tasks
- Configure per-component test/lint commands
