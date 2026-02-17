"""Vibraphone MCP server entry point."""

import sys

from fastmcp import FastMCP

# Initialize server with name
mcp = FastMCP("vibraphone")

# Import tools to register them with the mcp instance
# The tools use @mcp.tool decorator which registers on import
import vibraphone.tools.task_tools  # noqa: E402, F401


@mcp.tool
def ping() -> str:
    """Health check tool. Returns 'pong'.

    Use this to verify the MCP server is responsive.
    """
    return "pong"


def main() -> None:
    """Entry point for vibraphone MCP server.

    Starts the FastMCP server on stdio transport. The server handles
    all MCP protocol details including tool registration and request routing.

    Logs startup to stderr per design decision (not silent, not file-based).
    """
    # Log startup to stderr (per locked decision in CONTEXT.md)
    print("vibraphone MCP server starting (v0.1.0)", file=sys.stderr)
    # mcp.run() handles all protocol details including stdio transport
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
