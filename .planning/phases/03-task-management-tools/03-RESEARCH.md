# Phase 3: Task Management Tools - Research

**Researched:** 2026-02-16
**Domain:** MCP tools wrapping beads_rust (br) and beads_viewer (bv) CLIs for task management
**Confidence:** HIGH

## Summary

This phase implements MCP tools that wrap the `br` (beads_rust) and `bv` (beads_viewer) CLI commands for AI agent task management. The tools enable agents to list tasks, get the next ready task using critical path analysis, complete/abandon tasks, and retrieve task context bundles. The implementation pattern is straightforward: use Python's asyncio subprocess to call br/bv commands with `--json` or `--robot-*` flags, parse the JSON output, and return structured data through FastMCP.

**Primary recommendation:** Wrap br/bv CLI commands with JSON output mode. Use `--json` for br commands and `--robot-*` flags for bv commands. Never parse human-readable output - always use machine-parseable modes.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Filters:** list_tasks supports filtering by status and plan. Status values defined by beads_rust (ready, in_progress, completed, blocked). No filtering by phase or other metadata for v1.
- **Context Bundle:** get_task_context returns: task details, mermaid diagrams (from architecture.md), recent commits on task branch. Requires active worktree - includes branch-specific context (commits, diffs).
- **Error Handling:** Structured errors with: error type, message, and suggested action. Example: "CannotCompleteBlockedTask" with message and suggestion to check dependencies.
- **next_ready Selection:** Uses critical path / PageRank approach from beads_viewer. Returns task that is most blocking or on critical path.
- **complete_task:** Records status change, timestamp, optional notes. Notes added at completion time.
- **abandon_task:** Requires reason for audit trail. Resets task status to ready. Notes captured with reason.
- **Dependency Graph:** list_tasks returns full dependency graph. Agent can understand task relationships, parallel work opportunities, critical path. No need for separate graph query.
- **Task Operations:** One task at a time - no batch operations. No task editing - tasks are immutable once created. Agents cannot create tasks - only work with existing tasks from plans.
- **Concurrency:** Task claiming prevents conflicts. Once a task is claimed by an agent, not available to others.
- **Ordering:** list_tasks ordered by priority (from beads_rust).
- **Notes Field:** Notes can be added at complete and abandon operations. Not editable separately.

### Claude's Discretion

- Empty list/no ready task response format
- Task status values (verify with beads_rust)
- Metadata fields (created_at, updated_at, etc.)
- Exact task shape/fields in output
- Exact claiming mechanism implementation

### Deferred Ideas (OUT OF SCOPE)

- Task creation by agents - out of scope (user adds tasks directly or via plan import)
- Task editing - tasks are immutable
- Batch operations - one-at-a-time is sufficient for v1
- Phase-level filtering - not needed yet

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TASK-01 | list_tasks with optional status filter | Use `br list --status=<status> --json`. Supports status values: ready, in_progress, completed, blocked. |
| TASK-02 | next_ready (next unblocked task) | Use `bv --robot-next` for single top pick with critical path/PageRank prioritization. |
| TASK-03 | complete_task (mark complete, see unblocked) | Use `br close <id>` or `br update <id> --status=completed`. Returns updated state. |
| TASK-04 | abandon_task (reset status) | Use `br update <id> --status=ready` with notes. Requires reason per locked decision. |
| TASK-05 | health_check on beads state | Use `bv --robot-insights` for graph metrics, or check br database health. |
| TASK-06 | get_task_context (focused context bundle) | Use `br show <id> --json` + read architecture.md + git log for branch commits. |
| TASK-07 | add_task with dependencies | Use `br create` with dependency specification via `--blocks` or similar flag. |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastmcp | >=2.0 | MCP server framework | Already in use, provides `@mcp.tool()` decorator |
| pydantic | >=2.0 | Data validation/models | Already in use for config, natural fit for task models |
| asyncio.subprocess | stdlib | CLI command execution | Non-blocking subprocess calls to br/bv |

### External CLIs (Required)
| CLI | Purpose | When to Use |
|-----|---------|-------------|
| br (beads_rust) | Task CRUD operations | list_tasks, complete_task, abandon_task, add_task |
| bv (beads_viewer) | Graph analysis, prioritization | next_ready, health_check |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| br --json | Parse JSONL directly | JSONL parsing is error-prone, br --json provides stable schema |
| bv --robot-* | bv human output | Human output has ANSI codes, variable format - use robot modes |
| asyncio.subprocess | subprocess.run | subprocess.run is blocking - asyncio prevents server stalls |

**Installation:**
```bash
# vibraphone already has dependencies
# External CLIs must be installed separately:
# br: cargo install from beads_rust repo
# bv: cargo install from beads_viewer repo
```

## Architecture Patterns

### Recommended Project Structure
```
src/vibraphone/
├── server.py           # FastMCP instance, tool registration
├── config.py           # Config loading (existing)
├── tools/
│   ├── __init__.py     # Tool exports
│   └── task_tools.py   # Task management MCP tools (NEW)
└── utils/
    └── cli_runner.py   # Async subprocess wrapper for br/bv (NEW)
```

### Pattern 1: Async Subprocess Wrapper
**What:** Centralized async function to execute br/bv commands with JSON output
**When to use:** All task tools need to call external CLIs
**Example:**
```python
# Source: Standard asyncio pattern
import asyncio
import json
from pathlib import Path

async def run_cli(command: str, *args: str, cwd: Path | None = None) -> dict:
    """Run a CLI command and parse JSON output.

    Args:
        command: The CLI to run (br or bv)
        *args: Command arguments
        cwd: Working directory (defaults to project root)

    Returns:
        Parsed JSON output

    Raises:
        CliError: If command fails or returns non-JSON
    """
    cmd = [command, *args]
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise CliError(f"{command} failed: {stderr.decode()}")

    return json.loads(stdout.decode())
```

### Pattern 2: FastMCP Tool Registration
**What:** Use `@mcp.tool()` decorator to expose functions as MCP tools
**When to use:** Every tool function
**Example:**
```python
# Source: FastMCP documentation
from fastmcp import FastMCP

mcp = FastMCP("vibraphone")

@mcp.tool()
async def list_tasks(status: str | None = None) -> dict:
    """List tasks with optional status filter.

    Args:
        status: Filter by status (ready, in_progress, completed, blocked)

    Returns:
        Dict with tasks list and dependency graph
    """
    args = ["list", "--json"]
    if status:
        args.extend(["--status", status])

    result = await run_cli("br", *args)
    return {"tasks": result["issues"], "graph": result.get("dependency_graph", {})}
```

### Pattern 3: Structured Error Response
**What:** Return consistent error structure with type, message, and suggested action
**When to use:** When operations fail (blocked task, not found, etc.)
**Example:**
```python
# Source: CONTEXT.md locked decision
from pydantic import BaseModel

class TaskError(BaseModel):
    error_type: str
    message: str
    suggested_action: str

# Usage in tool:
@mcp.tool()
async def complete_task(task_id: str, notes: str | None = None) -> dict:
    # Check if task is blocked
    task = await get_task(task_id)
    if task.get("status") == "blocked":
        return TaskError(
            error_type="CannotCompleteBlockedTask",
            message=f"Task {task_id} is blocked by incomplete dependencies",
            suggested_action="Complete blocking tasks first or use abandon_task to reset"
        ).model_dump()
    # ... proceed with completion
```

### Anti-Patterns to Avoid
- **Parsing human-readable output:** br and bv have stable JSON modes - always use `--json` or `--robot-*`
- **Blocking subprocess calls:** Using `subprocess.run` blocks the entire server - always use asyncio
- **Direct JSONL manipulation:** br uses SQLite + JSONL internally - don't touch those files directly
- **Missing stderr handling:** Always capture and handle stderr for debugging

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Task CRUD | Custom SQLite/JSONL | br CLI commands | br handles all edge cases, locking, validation |
| Critical path analysis | PageRank implementation | bv --robot-next | bv has production-tested algorithms |
| Dependency graph traversal | Graph library code | bv --robot-insights | bv computes betweenness, HITS, k-core, cycles |
| Task claiming | Custom lock mechanism | br built-in claiming | Check existing implementation for claiming API |

**Key insight:** br and bv are mature CLIs with years of development. Wrapping them is simpler and more reliable than reimplementing their logic.

## Common Pitfalls

### Pitfall 1: Using Wrong Output Mode
**What goes wrong:** Parsing human-readable output fails when terminal width changes or ANSI codes appear
**Why it happens:** Developers try `br list` without `--json` and get colorized table output
**How to avoid:** Always use `--json` for br, `--robot-*` for bv
**Warning signs:** Output contains ANSI escape codes (`\x1b[...`), output format varies between runs

### Pitfall 2: Not Handling Missing CLIs
**What goes wrong:** Server crashes when br or bv not installed
**Why it happens:** CLIs are external dependencies not in pyproject.toml
**How to avoid:** Check CLI availability at startup, provide helpful error message
**Warning signs:** FileNotFoundError when calling run_cli()

### Pitfall 3: Blocking the Event Loop
**What goes wrong:** Server becomes unresponsive while waiting for br output
**Why it happens:** Using synchronous subprocess.run() instead of asyncio
**How to avoid:** Always use asyncio.create_subprocess_exec()
**Warning signs:** Server hangs during task operations

### Pitfall 4: Ignoring Working Directory
**What goes wrong:** br commands fail because they can't find beads.db
**Why it happens:** br expects to run from project root or directory with .beads/
**How to avoid:** Pass cwd parameter to run_cli(), default to project root from config
**Warning signs:** "database not found" errors from br

## Code Examples

### list_tasks Implementation
```python
# Source: br AGENTS.md + FastMCP pattern
@mcp.tool()
async def list_tasks(status: str | None = None, plan: str | None = None) -> dict:
    """List tasks with optional filters.

    Args:
        status: Filter by status (ready, in_progress, completed, blocked)
        plan: Filter by plan/phase identifier

    Returns:
        Dict with tasks, dependency graph, and metadata
    """
    args = ["list", "--json"]
    if status:
        args.extend(["--status", status])
    if plan:
        args.extend(["--plan", plan])

    result = await run_cli("br", *args, cwd=get_project_root())
    return {
        "tasks": result.get("issues", []),
        "dependency_graph": result.get("dependency_graph", {}),
        "total": len(result.get("issues", [])),
    }
```

### next_ready Implementation
```python
# Source: beads_viewer README --robot-next
@mcp.tool()
async def next_ready() -> dict:
    """Get the next unblocked task using critical path analysis.

    Uses PageRank/critical path algorithm from beads_viewer to identify
    the task that is most blocking or on the critical path.

    Returns:
        Dict with recommended task and claim command, or empty if none ready
    """
    result = await run_cli("bv", "--robot-next", cwd=get_project_root())

    if not result.get("task"):
        return {"task": None, "message": "No ready tasks available"}

    return {
        "task": result["task"],
        "claim_command": result.get("claim_command"),
        "reason": result.get("reason", "critical path prioritization"),
    }
```

### complete_task Implementation
```python
# Source: br AGENTS.md close command
@mcp.tool()
async def complete_task(task_id: str, notes: str | None = None) -> dict:
    """Mark a task as completed.

    Args:
        task_id: The task ID (e.g., bd-abc123)
        notes: Optional completion notes

    Returns:
        Updated task state and newly unblocked tasks
    """
    # Verify task exists and is not blocked
    task = await run_cli("br", "show", task_id, "--json", cwd=get_project_root())

    if task.get("status") == "blocked":
        return {
            "error": {
                "error_type": "CannotCompleteBlockedTask",
                "message": f"Task {task_id} is blocked by incomplete dependencies",
                "suggested_action": "Complete blocking tasks first",
            }
        }

    # Complete the task
    args = ["close", task_id]
    if notes:
        args.extend(["--notes", notes])

    result = await run_cli("br", *args, cwd=get_project_root())

    return {
        "task": result.get("issue"),
        "unblocked": result.get("unblocked", []),
        "completed_at": result.get("closed_at"),
    }
```

### abandon_task Implementation
```python
# Source: br AGENTS.md update command
@mcp.tool()
async def abandon_task(task_id: str, reason: str) -> dict:
    """Abandon a task and reset its status to ready.

    Args:
        task_id: The task ID (e.g., bd-abc123)
        reason: Required reason for audit trail

    Returns:
        Updated task state with reason recorded
    """
    # Reset status and capture reason
    args = ["update", task_id, "--status", "ready", "--notes", f"Abandoned: {reason}"]

    result = await run_cli("br", *args, cwd=get_project_root())

    return {
        "task": result.get("issue"),
        "abandoned_at": result.get("updated_at"),
        "reason": reason,
    }
```

### health_check Implementation
```python
# Source: beads_viewer README --robot-insights
@mcp.tool()
async def health_check() -> dict:
    """Check the health of the beads state.

    Returns graph metrics including PageRank, betweenness, critical path,
    cycle detection, and project health indicators.

    Returns:
        Dict with health metrics and any issues detected
    """
    result = await run_cli("bv", "--robot-insights", cwd=get_project_root())

    return {
        "status": result.get("status"),  # computed/approx/timeout/skipped
        "data_hash": result.get("data_hash"),
        "as_of": result.get("as_of"),
        "metrics": {
            "pagerank_top": result.get("pagerank", {}).get("top", []),
            "betweenness_top": result.get("betweenness", {}).get("top", []),
            "critical_path": result.get("critical_path", []),
            "cycles": result.get("cycles", []),
            "project_health": result.get("project_health", {}),
        },
    }
```

### get_task_context Implementation
```python
# Source: CONTEXT.md context bundle requirements
@mcp.tool()
async def get_task_context(task_id: str) -> dict:
    """Load focused context bundle for a task.

    Returns task details, mermaid diagrams from architecture.md,
    and recent commits on the task branch.

    Args:
        task_id: The task ID

    Returns:
        Dict with task details, architecture diagrams, and git context
    """
    # Get task details
    task = await run_cli("br", "show", task_id, "--json", cwd=get_project_root())

    # Read architecture.md for mermaid diagrams
    arch_path = get_project_root() / "docs" / "architecture.md"
    mermaid_diagrams = extract_mermaid_from_markdown(arch_path)

    # Get recent commits on task branch (if in worktree)
    branch_name = task.get("branch")
    commits = []
    if branch_name:
        commits = await get_branch_commits(branch_name, limit=5)

    return {
        "task": task,
        "architecture_diagrams": mermaid_diagrams,
        "recent_commits": commits,
    }
```

### add_task Implementation
```python
# Source: br AGENTS.md create command
@mcp.tool()
async def add_task(
    title: str,
    description: str | None = None,
    priority: str = "P2",
    dependencies: list[str] | None = None,
) -> dict:
    """Create a new task with optional dependencies.

    Args:
        title: Task title
        description: Optional task description
        priority: Priority level (P0-P4, default P2)
        dependencies: List of task IDs this task depends on

    Returns:
        Created task details
    """
    args = ["create", "--title", title, "--priority", priority]

    if description:
        args.extend(["--description", description])

    if dependencies:
        for dep_id in dependencies:
            args.extend(["--depends-on", dep_id])

    result = await run_cli("br", *args, cwd=get_project_root())

    return {
        "task": result.get("issue"),
        "created_at": result.get("created_at"),
    }
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Parse br human output | Use br --json | beads_rust 1.0 | Stable schema, no ANSI codes |
| Custom task prioritization | bv --robot-next | beads_viewer 2.0 | PageRank/critical path algorithms |
| Manual dependency tracking | br built-in deps | beads_rust 0.5 | Automatic blocked/ready states |
| Single analysis pass | Two-phase analysis | beads_viewer 2.1 | Instant metrics + async centralities |

**Deprecated/outdated:**
- bd CLI (Python beads): Replaced by br (beads_rust). Use br commands, not bd.

## Open Questions

1. **Task claiming mechanism**
   - What we know: CONTEXT.md mentions claiming prevents conflicts
   - What's unclear: Exact API - is it br claim or br update --claim?
   - Recommendation: Check beads_rust AGENTS.md for current claiming API

2. **Status values**
   - What we know: ready, in_progress, completed, blocked mentioned in CONTEXT.md
   - What's unclear: Are there other states (paused, cancelled)?
   - Recommendation: Run `br list --help` to see valid status values

3. **JSON schema stability**
   - What we know: --json provides stable output
   - What's unclear: Exact field names for each command's output
   - Recommendation: Run commands with --json and document actual schema

## Sources

### Primary (HIGH confidence)
- beads_rust AGENTS.md - https://github.com/Dicklesworthstone/beads_rust/blob/main/AGENTS.md - br command reference, JSON mode documentation
- beads_viewer README - https://github.com/Dicklesworthstone/beads_viewer - --robot-* flags, graph algorithms, two-phase analysis
- FastMCP documentation - https://github.com/jlowin/fastmcp - @mcp.tool() decorator, async patterns

### Secondary (MEDIUM confidence)
- Python asyncio subprocess docs - https://docs.python.org/3/library/asyncio-subprocess.html - create_subprocess_exec pattern
- Pydantic v2 docs - https://docs.pydantic.dev/ - BaseModel, model_dump, field validators

### Tertiary (LOW confidence)
- None - all core information verified from primary sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - FastMCP already in use, asyncio is stdlib, br/bv docs verified
- Architecture: HIGH - Patterns follow existing server.py structure and br/bv documented APIs
- Pitfalls: HIGH - Based on documented CLI behavior and common asyncio mistakes

**Research date:** 2026-02-16
**Valid until:** 30 days (br/bv APIs are stable, FastMCP 2.x is mature)
