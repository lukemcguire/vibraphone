# Error Reference

Vibraphone uses structured error responses for consistent handling.

## Error Response Format

All errors follow this structure:

```python
{
    "status": "error",
    "error_type": "ErrorTypeName",
    "message": "Human-readable error message",
    "suggested_action": "What to do next"
}
```

## Error Types

### TaskError

Base error for task-related operations.

| error_type | When Raised |
|------------|-------------|
| `TaskNotFound` | Task ID doesn't exist in beads |
| `TaskBlocked` | Cannot complete blocked task |
| `CliError` | br/bv command failed |
| `CannotCompleteBlockedTask` | Task has incomplete dependencies |
| `NoActiveSession` | No session for task ID |

### WorktreeError

Errors for worktree operations.

| error_type | When Raised |
|------------|-------------|
| `WorktreeExists` | Worktree already exists for task |
| `WorktreeNotFound` | No worktree for task ID |
| `UncommittedChanges` | Cannot proceed with uncommitted changes |
| `BranchNotMerged` | Task branch not merged into main |

### RebaseError

Errors during rebase operations.

| error_type | When Raised |
|------------|-------------|
| `RebaseConflict` | Merge conflicts during rebase |
| `RebaseFailed` | Generic rebase failure |

### CircuitBreakerTripped

When quality gate exceeds max attempts.

```python
{
    "status": "ESCALATED",
    "error_type": "CircuitBreakerTripped",
    "message": "Tests failed 3 times (max: 3)",
    "human_actions": [
        "Run tests locally to diagnose failure",
        "Fix the failing tests and reset: cleanup_task",
        "Abandon this approach: abandon_task"
    ]
}
```

### MissingAPIKeyError

When code review API key is not configured.

```python
{
    "status": "error",
    "error_type": "MissingAPIKeyError",
    "message": "REVIEWER_API_KEY environment variable not set.",
    "human_actions": [
        "Get API key from https://openrouter.ai/keys",
        "Set REVIEWER_API_KEY in environment or .env file"
    ]
}
```

## Handling Errors

Agents should:

1. Check `error_type` for categorization
2. Read `message` for specifics
3. Follow `suggested_action` or `human_actions`
