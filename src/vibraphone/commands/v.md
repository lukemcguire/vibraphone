---
name: v
description:
  Vibraphone slash commands for MCP tool orchestration. Use when the user
  invokes /v commands or asks about vibraphone task management.
argument-hint: <command> [args...] -- init|list|next|start|test|commit|...
allowed-tools:
  - mcp__vibraphone
---

# Vibraphone Slash Commands

User-friendly slash commands for vibraphone MCP tools.

## MCP Tool Calling Convention

When calling vibraphone MCP tools, **dict and list parameters must be passed as
JSON objects/arrays, NOT as JSON strings**.

| WRONG                          | RIGHT                        |
| ------------------------------ | ---------------------------- |
| `values: "{\"lang\": \"go\"}"` | `values: {"lang": "go"}`     |
| `files: "[\"a.py\", \"b.py\"]"`| `files: ["a.py", "b.py"]`    |
| `components: "{...}"`          | `components: {...}`          |

The MCP protocol handles JSON serialization automatically. Never manually
serialize dicts/lists to strings.

## Quick Reference

| Command | Purpose | MCP Tool |
| ------- | ------- | -------- |
| /v init | Initialize vibraphone in project | vibraphone_init_project |
| /v check-prereqs | Check dependencies | vibraphone_check_prerequisites |
| /v configure-stack | Configure test/lint/format | vibraphone_configure_stack |
| /v import-plan | Import GSD plans to Beads | vibraphone_import_gsd_plan |
| /v list | List tasks from Beads | vibraphone_list_tasks |
| /v next | Get next ready task | vibraphone_next_ready |
| /v start <id> | Start task in worktree | vibraphone_start_task |
| /v test | Run tests | vibraphone_run_tests |
| /v lint | Run linter | vibraphone_run_lint |
| /v format | Run formatter | vibraphone_run_format |
| /v review | Request code review | vibraphone_request_code_review |
| /v commit <msg> | Attempt commit | vibraphone_attempt_commit |
| /v merge <id> | Merge task branch | vibraphone_merge_task |
| /v cleanup <id> | Remove worktree/branch | vibraphone_cleanup_task |
| /v complete <id> | Mark task done | vibraphone_complete_task |
| /v status | Show session state | vibraphone_recover_session |
| /v health | Show health metrics | vibraphone_health_check |
| /v recover | Resume session | vibraphone_recover_session |
| /v cycle | Run quality suite | (multiple) |
| /v finish | Complete workflow | (multiple) |

## Start Work

Commands for discovering and starting tasks. These are your entry points
into the workflow - use them to see what's available and begin working
on a task.

### `/v init [--language LANG] [--name NAME] [--apply]`

Initialize vibraphone in the current project. Creates vibraphone.yaml
and supporting configuration files.

- `--language` / `-l`: Programming language (python, go, rust, node)
- `--name` / `-n`: Project name (defaults to directory name)
- `--apply`: Skip preview and write files immediately

**MCP Tool**: `vibraphone_init_project`

| Parameter    | Type    | Default | Required |
| ------------ | ------- | ------- | -------- |
| project_path | string  | null    | No       |
| values       | object  | null    | No       |
| preview      | boolean | true    | No       |

**Typical usage (preview first):**

User runs: `/v init`

Claude calls:
```json
{"preview": true}
```

Claude shows preview, asks to confirm, then calls:
```json
{"preview": false}
```

**With language and name:**

User runs: `/v init --language go --name myapp --apply`

Claude calls:
```json
{
  "preview": false,
  "values": {
    "language": "go",
    "project_name": "myapp"
  }
}
```

**Common mistake - WRONG stringification:**

```json
// WRONG - values is a string, not an object
{"values": "{\"language\": \"go\"}"}
```

```json
// RIGHT - values is a native object
{"values": {"language": "go"}}
```

**Flow**:

1. If no `--apply`: Call with `preview: true`, show preview, ask to confirm
2. With `--apply` or after confirmation: Call with `preview: false`

### `/v check-prereqs`

Check for required dependencies (br, bv, git, just, node/npx).

**MCP Tool**: `vibraphone_check_prerequisites`

No parameters required.

### `/v configure-stack [--stitch PROJECT_ID]`

Configure test/lint/format commands for project components. Generates
or updates the components section in vibraphone.yaml.

- `--stitch`: Enable Stitch MCP integration with project ID

**MCP Tool**: `vibraphone_configure_stack`

| Parameter         | Type    | Default | Required |
| ----------------- | ------- | ------- | -------- |
| components        | object  | -       | Yes      |
| stitch_project_id | string  | null    | No       |
| preview           | boolean | true    | No       |

**Typical usage (single Python component):**

User runs: `/v configure-stack`

Claude understands project and calls:
```json
{
  "components": {
    "server": {
      "language": "python",
      "root": "./src",
      "test_command": "pytest",
      "lint_command": "ruff check .",
      "format_command": "ruff format ."
    }
  },
  "preview": true
}
```

**Multiple components (monorepo):**

```json
{
  "components": {
    "backend": {
      "language": "python",
      "root": "./backend",
      "test_command": "pytest",
      "lint_command": "ruff check .",
      "format_command": "ruff format ."
    },
    "frontend": {
      "language": "node",
      "root": "./frontend",
      "test_command": "npm test",
      "lint_command": "npm run lint",
      "format_command": "npm run format"
    }
  },
  "preview": true
}
```

**With Stitch integration:**

```json
{
  "components": {"server": {...}},
  "stitch_project_id": "proj_abc123",
  "preview": false
}
```

**Common mistake - WRONG stringification:**

```json
// WRONG - components is a string
{"components": "{\"server\": {...}}"}
```

```json
// RIGHT - components is a native object
{"components": {"server": {...}}}
```

**Flow**:

1. Understand project structure (languages, test frameworks)
2. Call with `preview: true`
3. Show proposed config, ask to confirm
4. Call with `preview: false`

### `/v import-plan <phase>`

Import GSD phase plans into Beads tasks. Reads PLAN.md files from
.planning/phases/ directory and creates corresponding Beads tasks.

- `<phase>`: Phase number (required, e.g., 6 or 06)

**MCP Tool**: `vibraphone_import_gsd_plan`

| Parameter    | Type    | Default | Required |
| ------------ | ------- | ------- | -------- |
| phase_number | integer | -       | Yes      |
| preview      | boolean | true    | No       |

**Typical usage (preview first):**

User runs: `/v import-plan 6`

Claude calls:
```json
{
  "phase_number": 6,
  "preview": true
}
```

Claude shows what would be imported, asks to confirm.

**With apply (skip preview):**

User runs: `/v import-plan 6 --apply`

Claude calls:
```json
{
  "phase_number": 6,
  "preview": false
}
```

**Edge case - Phase with no plans:**

Error: `NoPlanFilesFound`
Message: "No PLAN.md files found in phase directory"
Suggested action: "Create PLAN.md files first"

**Common mistake - WRONG parameter type:**

```json
// WRONG - phase_number is a string
{"phase_number": "6", "preview": true}
```

```json
// RIGHT - phase_number is an integer
{"phase_number": 6, "preview": true}
```

**Flow**:

1. Call with `preview: true`
2. Show what would be imported (tasks, dependencies)
3. Ask to confirm
4. Call with `preview: false`

### `/v list [--status STATUS] [--plan PLAN]`

List tasks from Beads. Shows task ID, title, status, and plan assignment.

- `--status`: Filter by status (ready, in_progress, completed, blocked)
- `--plan`: Filter by plan ID (e.g., "06-02")

**MCP Tool**: `vibraphone_list_tasks`

| Parameter | Type   | Default | Required |
| --------- | ------ | ------- | -------- |
| status    | string | null    | No       |
| plan      | string | null    | No       |

**Typical usage (all tasks):**

User runs: `/v list`

Claude calls:
```json
{}
```

**Filter by status:**

User runs: `/v list --status ready`

Claude calls:
```json
{"status": "ready"}
```

**Filter by plan:**

User runs: `/v list --plan 06-02`

Claude calls:
```json
{"plan": "06-02"}
```

**Combine filters:**

User runs: `/v list --status in_progress --plan 06`

Claude calls:
```json
{
  "status": "in_progress",
  "plan": "06"
}
```

**Edge case - No tasks found:**

Returns empty list with message "No tasks found matching criteria"

### `/v next`

Get the next ready task using critical path analysis. Considers dependencies,
priorities, and blocking relationships.

**MCP Tool**: `vibraphone_next_ready`

No parameters required.

**Typical usage:**

User runs: `/v next`

Claude calls:
```json
{}
```

**Response includes:**

- Task ID (e.g., "bd-abc123")
- Title and description
- Why this task was selected (dependencies met, high priority, etc.)
- Suggested next action

**Edge case - No ready tasks:**

Response: "No ready tasks found"
Suggested actions:
- Check if blocked tasks have unresolved dependencies
- Complete in-progress tasks first
- Import new plans with `/v import-plan`

### `/v start <task_id>`

Start a task in an isolated git worktree. Creates a branch, sets up the
worktree, and begins a session.

- `<task_id>`: Task ID from Beads (required, e.g., bd-abc123)

**MCP Tool**: `vibraphone_start_task`

| Parameter | Type   | Default | Required |
| --------- | ------ | ------- | -------- |
| task_id   | string | -       | Yes      |

**Typical usage:**

User runs: `/v start bd-abc123`

Claude calls:
```json
{"task_id": "bd-abc123"}
```

**Response includes:**

- Worktree path (e.g., ~/.vibraphone/worktrees/bd-abc123/)
- Branch name
- Session ID

**Edge case - Task already in progress:**

Error: `BranchAlreadyExists`
Message: "Branch 'task/bd-abc123' already exists"
Suggested action: "Task may already be in progress. Check existing worktrees
with `git worktree list`"

**Edge case - Blocked task:**

Error: `CannotStartBlockedTask`
Message: "Task has incomplete dependencies"
Suggested action: Lists blocking tasks to complete first

**Common mistake - Wrong ID format:**

```text
# WRONG - Using numeric ID
/v start 123

# RIGHT - Use full task ID from /v list output
/v start bd-abc123
```

## Run Quality

Commands for running quality gates. These enforce the core value of
vibraphone: every code change goes through tests, lint, format, and
review before it can be committed.

### `/v test [--component NAME]`

Run tests.

- `--component`: Component name to test (optional)

**MCP Tool**: `vibraphone_run_tests`

| Parameter | Type   | Default | Required |
| --------- | ------ | ------- | -------- |
| component | string | null    | No       |

**Default call** (no options):

```json
{}
```

### `/v lint [--component NAME]`

Run linter.

- `--component`: Component name to lint (optional)

**MCP Tool**: `vibraphone_run_lint`

| Parameter | Type   | Default | Required |
| --------- | ------ | ------- | -------- |
| component | string | null    | No       |

**Default call** (no options):

```json
{}
```

### `/v format [--component NAME]`

Run formatter.

- `--component`: Component name to format (optional)

**MCP Tool**: `vibraphone_run_format`

| Parameter | Type   | Default | Required |
| --------- | ------ | ------- | -------- |
| component | string | null    | No       |

**Default call** (no options):

```json
{}
```

### `/v review [--files FILE1,FILE2,...]`

Request code review.

- `--files`: Comma-separated list of files (optional)

**MCP Tool**: `vibraphone_request_code_review`

| Parameter | Type          | Default | Required |
| --------- | ------------- | ------- | -------- |
| task_id   | string        | null    | No       |
| files     | array[string] | null    | No       |

**Default call** (no options):

```json
{}
```

**With files**:

```json
{
  "files": ["src/main.py", "src/utils.py"]
}
```

## Commit & Merge

Commands for committing and integrating completed work. These handle
the git workflow: committing with quality gate enforcement, merging
to main, and cleaning up worktrees.

### `/v commit <message>`

Attempt to commit changes.

- `<message>`: Commit message (required)

**MCP Tool**: `vibraphone_attempt_commit`

| Parameter | Type   | Default | Required |
| --------- | ------ | ------- | -------- |
| task_id   | string | null    | No       |
| message   | string | ""      | No       |

**Call**:

```json
{
  "message": "feat: add user authentication"
}
```

### `/v merge <task_id>`

Merge task branch into main.

- `<task_id>`: Task ID (required, e.g., bd-abc123)

**MCP Tool**: `vibraphone_merge_task`

| Parameter | Type   | Default | Required |
| --------- | ------ | ------- | -------- |
| task_id   | string | -       | Yes      |

**Call**:

```json
{
  "task_id": "bd-abc123"
}
```

### `/v cleanup <task_id>`

Remove worktree and delete branch.

- `<task_id>`: Task ID (required, e.g., bd-abc123)

**MCP Tool**: `vibraphone_cleanup_task`

| Parameter | Type   | Default | Required |
| --------- | ------ | ------- | -------- |
| task_id   | string | -       | Yes      |

**Call**:

```json
{
  "task_id": "bd-abc123"
}
```

### `/v complete <task_id> [--notes NOTES]`

Mark task as completed.

- `<task_id>`: Task ID (required, e.g., bd-abc123)
- `--notes`: Optional completion notes

**MCP Tool**: `vibraphone_complete_task`

| Parameter | Type   | Default | Required |
| --------- | ------ | ------- | -------- |
| task_id   | string | -       | Yes      |
| notes     | string | null    | No       |

**Call**:

```json
{
  "task_id": "bd-abc123"
}
```

**With notes**:

```json
{
  "task_id": "bd-abc123",
  "notes": "Completed feature X"
}
```

## Session Management

Commands for checking project state and recovering from interruptions.
Use these when you need to understand current status or resume after
a break.

### `/v recover`

Resume interrupted session.

**MCP Tool**: `vibraphone_recover_session`

No parameters required.

### `/v status`

Show current session/project state.

**MCP Tool**: `vibraphone_recover_session`

No parameters required.

### `/v health`

Show project health metrics.

**MCP Tool**: `vibraphone_health_check`

No parameters required.

## Troubleshooting

[Will be populated by Plan 11-03]

## Workflow Shortcuts

### `/v cycle`

Run test -> lint -> format -> review in sequence.

**MCP Tools called in order**:

1. `vibraphone_run_tests` with `{}`
2. `vibraphone_run_lint` with `{}`
3. `vibraphone_run_format` with `{}`
4. `vibraphone_request_code_review` with `{}`

**Flow**:

1. Run tests, if pass continue
2. Run lint, if pass continue
3. Run format, if pass continue
4. Request code review
5. Report final status

### `/v finish <task_id> <message>`

Complete workflow: commit -> merge -> cleanup -> complete.

- `<task_id>`: Task ID (required, e.g., bd-abc123)
- `<message>`: Commit message (required)

**MCP Tools called in order**:

1. `vibraphone_attempt_commit` with `{"task_id": "...", "message": "..."}`
2. `vibraphone_merge_task` with `{"task_id": "..."}`
3. `vibraphone_cleanup_task` with `{"task_id": "..."}`
4. `vibraphone_complete_task` with `{"task_id": "..."}`

**Flow**:

1. Attempt commit, if success continue
2. Merge task branch
3. Cleanup worktree
4. Mark task complete
5. Report final status

## Argument Parsing

1. **Flags with values**: `--language go` -> extract `go`
2. **Short flags**: `-l go` -> same as `--language go`
3. **Positional args**: `/v start bd-abc123` -> task_id = "bd-abc123"
4. **Boolean flags**: `--apply` -> true if present
5. **Comma-separated**: `--files a.py,b.py` -> `["a.py", "b.py"]`

## Error Handling

When a tool returns an error:

1. Show the error message clearly
2. Show `next_steps` if available
3. Offer to help resolve the issue

## Context Detection

Vibraphone tools auto-find `vibraphone.yaml` by walking up from CWD. Users
don't need to specify the project root.

If no `vibraphone.yaml` found:

- Project commands (list, start, etc.) will error
- Global commands (check-prereqs, init) still work
