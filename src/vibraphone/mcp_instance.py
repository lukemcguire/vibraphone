"""MCP server instance for vibraphone.

This module provides the FastMCP instance that tools register with.
Separated from server.py to avoid circular imports when tools import the mcp instance.
"""

from fastmcp import FastMCP

# Initialize server with name
mcp = FastMCP("vibraphone")
