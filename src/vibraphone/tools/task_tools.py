"""Task management MCP tools for vibraphone.

This module contains MCP tool implementations for task management operations
with br/bv CLIs. Tools follow the error handling pattern from CONTEXT.md.
"""

from pathlib import Path

from pydantic import BaseModel

from vibraphone.server import mcp
from vibraphone.utils.cli_runner import run_cli


class TaskError(BaseModel):
    """Structured error response per CONTEXT.md locked decision.

    Provides consistent error format for task management tools with
    actionable guidance for users.
    """

    error_type: str  # e.g., "CannotCompleteBlockedTask"
    message: str  # Human-readable error message
    suggested_action: str  # What to do next


def get_project_root() -> Path:
    """Get project root directory for CLI commands.

    Returns the directory containing vibraphone.yaml or the current working
    directory if no config file is found.
    """
    from vibraphone.config import find_config_file

    config_path = find_config_file()
    if config_path is not None:
        return config_path.parent
    return Path.cwd()


@mcp.tool
async def list_tasks(status: str | None = None, plan: str | None = None) -> dict:
    """List tasks with optional filters.

    Args:
        status: Filter by status (ready, in_progress, completed, blocked)
        plan: Filter by plan/phase identifier

    Returns:
        Dict with tasks list, dependency graph, and total count.
        Tasks ordered by priority from beads_rust.
    """
    args = ["list", "--json"]

    if status is not None:
        args.extend(["--status", status])

    if plan is not None:
        args.extend(["--plan", plan])

    result = await run_cli("br", *args, cwd=get_project_root())

    tasks = result.get("issues", [])
    return {
        "tasks": tasks,
        "dependency_graph": result.get("dependency_graph", {}),
        "total": len(tasks),
    }


@mcp.tool
async def next_ready() -> dict:
    """Get the next unblocked task using critical path analysis.

    Uses PageRank/critical path algorithm from beads_viewer to identify
    the task that is most blocking or on the critical path.

    Returns:
        Dict with recommended task and claim command, or empty if none ready.
        Includes 'reason' explaining why this task was selected.
    """
    result = await run_cli("bv", "--robot-next", cwd=get_project_root())

    if not result.get("task"):
        return {"task": None, "message": "No ready tasks available"}

    return {
        "task": result["task"],
        "claim_command": result.get("claim_command"),
        "reason": result.get("reason", "critical path prioritization"),
    }


@mcp.tool
async def health_check() -> dict:
    """Check the health of the beads state.

    Returns graph metrics including PageRank, betweenness, critical path,
    cycle detection, and project health indicators.

    Returns:
        Dict with status, data_hash, as_of timestamp, and metrics dict.
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
