"""Tests for vibraphone server entry point."""

import subprocess
import sys


def test_version_importable():
    """Verify package version is accessible."""
    import vibraphone

    assert hasattr(vibraphone, "__version__")
    assert vibraphone.__version__ == "0.1.0"


def test_server_module_importable():
    """Verify server module can be imported."""
    from vibraphone import server

    assert hasattr(server, "main")
    assert hasattr(server, "mcp")
    assert callable(server.main)


def test_ping_tool_registered():
    """Verify ping tool is registered with MCP.

    Note: FastMCP @mcp.tool decorator wraps functions in FunctionTool objects,
    so we verify registration via mcp._tool_manager rather than direct call.
    """
    from vibraphone.server import mcp

    # Verify ping tool is registered
    assert "ping" in mcp._tool_manager._tools


def test_mcp_instance_configured():
    """Verify MCP instance is properly configured."""
    from vibraphone.server import mcp

    assert mcp.name == "vibraphone"


def test_entry_point_module_runnable():
    """Verify server module can be run as entry point.

    The server will block waiting for stdin, so we just verify
    it doesn't crash on import and has the expected structure.
    """
    result = subprocess.run(
        [sys.executable, "-c", "from vibraphone.server import main; print('OK')"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert "OK" in result.stdout
    assert "ImportError" not in result.stderr
    assert "ModuleNotFoundError" not in result.stderr
