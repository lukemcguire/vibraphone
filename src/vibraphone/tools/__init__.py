"""Tools package for vibraphone MCP server.

This package contains MCP tool implementations.

All tool modules are imported here to ensure their @mcp.tool decorators
execute during server startup, registering the tools with FastMCP.
"""

# Import all tool modules to register their MCP tools
# The imports are for side effects (decorator registration)
# Use relative imports to avoid circular import issues
# Re-export commonly used items for convenience
from vibraphone.tools.task_tools import (
    TaskError,
    abandon_task,
    complete_task,
    get_task_context,
    health_check,
    list_tasks,
    next_ready,
)

from . import (
    bridge_tools,
    quality_gate_tools,
    scaffold_tools,
    stack_tools,
    task_tools,
    worktree_tools,
)

# Silence ruff about unused imports - they're for side effects
_ = (
    bridge_tools,
    quality_gate_tools,
    scaffold_tools,
    stack_tools,
    task_tools,
    worktree_tools,
)

__all__ = [
    "TaskError",
    "abandon_task",
    "bridge_tools",
    "complete_task",
    "get_task_context",
    "health_check",
    "list_tasks",
    "next_ready",
    "quality_gate_tools",
    "scaffold_tools",
    "stack_tools",
    "worktree_tools",
]
