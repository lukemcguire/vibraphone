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

Run tests in the current worktree context. Uses the test_command from
vibraphone.yaml for the specified component.

- `--component`: Component name to test (optional, defaults to all)

**MCP Tool**: `vibraphone_run_tests`

| Parameter | Type   | Default | Required |
| --------- | ------ | ------- | -------- |
| component | string | null    | No       |

**Typical usage (all components):**

User runs: `/v test`

Claude calls:
```json
{}
```

**Specific component:**

User runs: `/v test --component server`

Claude calls:
```json
{"component": "server"}
```

**Success response:**

- Status: PASSED
- Test count and pass rate

**Failure response:**

- Status: FAILED
- Failure details with file/line
- Suggested fixes

**Edge case - Circuit breaker triggered:**

After max_test_attempts exceeded:
- Status: ESCALATED
- Message: "Test failures persist after N attempts"
- Suggested action: Manual intervention required

### `/v lint [--component NAME]`

Run linter in the current worktree context. Uses the lint_command from
vibraphone.yaml.

- `--component`: Component name to lint (optional, defaults to all)

**MCP Tool**: `vibraphone_run_lint`

| Parameter | Type   | Default | Required |
| --------- | ------ | ------- | -------- |
| component | string | null    | No       |

**Typical usage:**

User runs: `/v lint`

Claude calls:
```json
{}
```

**Success response:**

- Status: PASSED
- No lint errors found

**Failure response:**

- Status: FAILED
- Violation list with file/line/rule
- Many violations are auto-fixable

**Common workflow:**

```text
/v lint          # See violations
# Fix or auto-fix issues
/v lint          # Re-run until PASSED
```

### `/v format [--component NAME]`

Run formatter in the current worktree context. Uses the format_command from
vibraphone.yaml.

- `--component`: Component name to format (optional, defaults to all)

**MCP Tool**: `vibraphone_run_format`

| Parameter | Type   | Default | Required |
| --------- | ------ | ------- | -------- |
| component | string | null    | No       |

**Typical usage:**

User runs: `/v format`

Claude calls:
```json
{}
```

**Response includes:**

- Status: PASSED (formatting applied)
- Files modified count

**Note:** Formatters typically modify files in place. The quality gate checks
that the formatter ran successfully, not that files were unchanged.

### `/v review [--files FILE1,FILE2,...]`

Request LLM-powered code review. Uses instructor + OpenRouter to analyze code
changes and provide feedback.

- `--files`: Comma-separated list of files to review (optional)

**MCP Tool**: `vibraphone_request_code_review`

| Parameter | Type          | Default | Required |
| --------- | ------------- | ------- | -------- |
| task_id   | string        | null    | No       |
| files     | array[string] | null    | No       |

**Typical usage (all changed files):**

User runs: `/v review`

Claude calls:
```json
{}
```

**Specific files:**

User runs: `/v review --files src/main.py,src/utils.py`

Claude calls:
```json
{
  "files": ["src/main.py", "src/utils.py"]
}
```

**Common mistake - WRONG array format:**

```json
// WRONG - files is a string
{"files": "src/main.py,src/utils.py"}
```

```json
// RIGHT - files is an array
{"files": ["src/main.py", "src/utils.py"]}
```

**Success response:**

- Status: APPROVED
- Review summary
- No blocking issues

**Rejection response:**

- Status: REJECTED
- Issues list with severity and location
- Suggested fixes

**Edge case - Missing API key:**

Error: `MissingAPIKeyError`
Message: "REVIEWER_API_KEY not set"
Suggested action: "Set REVIEWER_API_KEY in environment or .env file"

**Edge case - Circuit breaker:**

After max_review_attempts exceeded:
- Status: ESCALATED
- Message: "Review not approved after N attempts"
- Suggested action: Manual review required

## Commit & Merge

Commands for committing and integrating completed work. These handle
the git workflow: committing with quality gate enforcement, merging
to main, and cleaning up worktrees.

### `/v commit <message>`

Attempt to commit changes. Enforces quality gate: requires passing
tests, lint, and approved review before committing.

- `<message>`: Commit message (required)

**MCP Tool**: `vibraphone_attempt_commit`

| Parameter | Type   | Default | Required |
| --------- | ------ | ------- | -------- |
| task_id   | string | null    | No       |
| message   | string | ""      | No       |

**Typical usage:**

User runs: `/v commit "feat: add user authentication"`

Claude calls:
```json
{
  "message": "feat: add user authentication"
}
```

**Success response:**

- Status: COMMITTED
- Commit hash
- Branch name

**Quality gate enforcement:**

The tool runs quality checks before committing:

1. Run tests - if fail, return TESTS_FAILED
2. Run lint - if fail, return LINT_FAILED
3. Check for approved review - if none, return REVIEW_REQUIRED

**Edge case - Quality gate failure:**

Status: TESTS_FAILED
Message: "Tests must pass before commit"
Suggested action: "Run /v test to see failures, fix, and retry"

**Edge case - No approved review:**

Status: REVIEW_REQUIRED
Message: "Code review required before commit"
Suggested action: "Run /v review and address feedback"

**Common mistake - Empty message:**

```text
# WRONG - No commit message
/v commit

# RIGHT - Always provide a meaningful message
/v commit "feat: add user authentication"
```

### `/v merge <task_id>`

Merge task branch into main. Rebases onto main first, then fast-forward
merges.

- `<task_id>`: Task ID (required, e.g., bd-abc123)

**MCP Tool**: `vibraphone_merge_task`

| Parameter | Type   | Default | Required |
| --------- | ------ | ------- | -------- |
| task_id   | string | -       | Yes      |

**Typical usage:**

User runs: `/v merge bd-abc123`

Claude calls:
```json
{"task_id": "bd-abc123"}
```

**Success response:**

- Status: MERGED
- Merged commit hash
- Target branch (main)

**Edge case - Uncommitted changes:**

Error: `UncommittedChanges`
Message: "Worktree has uncommitted changes"
Suggested action: "Commit or stash changes first"
Files: List of modified files

**Edge case - Rebase conflict:**

Error: `RebaseConflict`
Message: "Rebase conflicts with main"
Suggested action: "Manually resolve conflicts"
Conflicted files: List of files with conflicts

**Conflict resolution workflow:**

```text
1. cd ~/.vibraphone/worktrees/bd-abc123/
2. # Edit conflicted files
3. git add <resolved-files>
4. git rebase --continue
5. /v merge bd-abc123
```

### `/v cleanup <task_id>`

Remove worktree and delete task branch. Run after merge to clean up
isolated development environment.

- `<task_id>`: Task ID (required, e.g., bd-abc123)

**MCP Tool**: `vibraphone_cleanup_task`

| Parameter | Type   | Default | Required |
| --------- | ------ | ------- | -------- |
| task_id   | string | -       | Yes      |

**Typical usage:**

User runs: `/v cleanup bd-abc123`

Claude calls:
```json
{"task_id": "bd-abc123"}
```

**Success response:**

- Status: CLEANED_UP
- Removed worktree path
- Deleted branch name

**Edge case - Branch not merged:**

Error: `BranchNotMerged`
Message: "Task branch not merged into main"
Suggested action: "Run /v merge first"

**Edge case - Uncommitted changes:**

Error: `UncommittedChanges`
Message: "Worktree has uncommitted changes"
Suggested action: "Commit or stash changes, or use --force"

### `/v complete <task_id> [--notes NOTES]`

Mark task as completed in Beads. Updates task status and records
completion notes.

- `<task_id>`: Task ID (required, e.g., bd-abc123)
- `--notes`: Optional completion notes

**MCP Tool**: `vibraphone_complete_task`

| Parameter | Type   | Default | Required |
| --------- | ------ | ------- | -------- |
| task_id   | string | -       | Yes      |
| notes     | string | null    | No       |

**Typical usage:**

User runs: `/v complete bd-abc123`

Claude calls:
```json
{"task_id": "bd-abc123"}
```

**With completion notes:**

User runs: `/v complete bd-abc123 --notes "Feature shipped to production"`

Claude calls:
```json
{
  "task_id": "bd-abc123",
  "notes": "Feature shipped to production"
}
```

**Edge case - Blocked task:**

Error: `CannotCompleteBlockedTask`
Message: "Task has incomplete dependencies"
Suggested action: Lists blocking tasks

**Typical completion workflow:**

```text
/v commit "feat: complete feature"
/v merge bd-abc123
/v cleanup bd-abc123
/v complete bd-abc123
```

Or use the shortcut: `/v finish bd-abc123 "feat: complete feature"`

## Session Management

Commands for checking project state and recovering from interruptions.
Use these when you need to understand current status or resume after
a break.

### `/v status`

Show current session and project state. Displays active task, worktree
location, and recent activity.

**MCP Tool**: `vibraphone_recover_session`

No parameters required.

**Typical usage:**

User runs: `/v status`

Claude calls:
```json
{}
```

**Response includes:**

- Session status (active/inactive)
- Current task ID and title
- Worktree path
- Branch name
- Uncommitted changes count

**Edge case - No active session:**

Status: NO_SESSION
Message: "No active session found"
Suggested actions:
- Start a task with `/v start <task_id>`
- Recover a previous session with `/v recover`

### `/v health`

Show project health metrics. Analyzes task completion rates, quality
gate success rates, and overall project status.

**MCP Tool**: `vibraphone_health_check`

No parameters required.

**Typical usage:**

User runs: `/v health`

Claude calls:
```json
{}
```

**Response includes:**

- Total tasks count
- Completed/In Progress/Ready/Blocked breakdown
- Quality gate success rate
- Average tasks per day (if history available)
- Any warnings or recommendations

### `/v recover`

Resume an interrupted session. Finds the most recent incomplete
session and restores context.

**MCP Tool**: `vibraphone_recover_session`

No parameters required.

**Typical usage:**

User runs: `/v recover`

Claude calls:
```json
{}
```

**Response includes:**

- Recovered session ID
- Task ID and title
- Worktree path
- Last known state
- Suggested next action

**Edge case - No session to recover:**

Status: NO_SESSION
Message: "No incomplete session found"
Suggested action: "Start a new task with `/v start` or `/v next`"

**When to use:**

- After Claude Code restart
- After system crash or timeout
- When continuing work after a break

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
