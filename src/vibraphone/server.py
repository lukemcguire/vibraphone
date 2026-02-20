"""Vibraphone MCP server entry point."""

import sys

from vibraphone.config import find_config_file
from vibraphone.mcp_instance import mcp

# Import tools to register them with the mcp instance
# The tools use @mcp.tool decorator which registers on import
# These are intentionally imported for side effects only
from vibraphone.tools import (
    bridge_tools,
    quality_gate_tools,
    scaffold_tools,
    stack_tools,
    task_tools,
    worktree_tools,
)

# Re-export mcp for backward compatibility
__all__ = ["main", "mcp", "ping"]

# Silence ruff about unused imports - they're for side effects
_ = (
    bridge_tools,
    quality_gate_tools,
    scaffold_tools,
    stack_tools,
    task_tools,
    worktree_tools,
)


@mcp.tool
def ping() -> str:
    """Health check tool. Returns 'pong'.

    Use this to verify the MCP server is responsive.
    """
    return "pong"


def check_stale_session() -> None:
    """Check for stale session on startup (log only, no auto-resume).

    Per SESS-01: Session recovery runs automatically on server startup
    when vibraphone.yaml is detected. Logs message if stale session found.
    """
    config_path = find_config_file()
    if not config_path:
        return  # Not a vibraphone project

    project_root = config_path.parent
    from vibraphone.utils.session import SessionManager

    session = SessionManager(project_root)
    state = session.load()

    if state:
        print(
            f"Session found: task {state.task_id} in worktree {state.worktree_path}. Call recover_session to continue.",
            file=sys.stderr,
        )


def main() -> None:
    """Entry point for vibraphone MCP server.

    Starts the FastMCP server on stdio transport. The server handles
    all MCP protocol details including tool registration and request routing.

    Logs startup to stderr per design decision (not silent, not file-based).
    """
    # Log startup to stderr (per locked decision in CONTEXT.md)
    print("vibraphone MCP server starting (v0.1.0)", file=sys.stderr)

    # Check for stale session on startup (SESS-01)
    check_stale_session()

    # mcp.run() handles all protocol details including stdio transport
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
