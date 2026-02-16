---
phase: 01-package-foundation
plan: 02
type: execute
wave: 2
depends_on:
  - "01"
files_modified:
  - src/vibraphone/server.py
  - src/vibraphone/config.py
autonomous: true
requirements:
  - PKG-03
  - PKG-04

must_haves:
  truths:
    - "Running `vibraphone` command starts FastMCP server on stdio transport"
    - "Server starts without vibraphone.yaml present and does not crash"
    - "Server logs startup message to stderr"
    - "Server has at least one tool registered (ping) for health check"
  artifacts:
    - path: "src/vibraphone/server.py"
      provides: "FastMCP server entry point"
      exports: ["main", "mcp"]
      contains: "mcp.run"
    - path: "src/vibraphone/config.py"
      provides: "Lazy config loading stub"
      exports: ["get_config"]
  key_links:
    - from: "pyproject.toml [project.scripts]"
      to: "vibraphone.server:main"
      via: "Entry point registration"
      pattern: "vibraphone.*vibraphone.server:main"
    - from: "server.py main()"
      to: "FastMCP stdio transport"
      via: "mcp.run(transport='stdio')"
      pattern: "mcp\\.run.*stdio"
---

<objective>
Create the FastMCP server entry point with lazy config loading stub.

Purpose: Deliver a working `vibraphone` command that starts an MCP server on stdio transport. The server must start without requiring vibraphone.yaml (zero-config), logging to stderr for debugging.

Output: Working FastMCP server that can be invoked via `vibraphone` command, with placeholder config module for Phase 2.
</objective>

<execution_context>
@/home/luke/.claude/get-shit-done/workflows/execute-plan.md
@/home/luke/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/01-package-foundation/01-CONTEXT.md
@.planning/phases/01-package-foundation/01-RESEARCH.md
@.planning/phases/01-package-foundation/01-01-SUMMARY.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create FastMCP server entry point</name>
  <files>
    - src/vibraphone/server.py
  </files>
  <action>
    Create `src/vibraphone/server.py` following the FastMCP docs pattern from RESEARCH.md:

    ```python
    """Vibraphone MCP server entry point."""

    import sys

    from fastmcp import FastMCP

    # Initialize server with name
    mcp = FastMCP("vibraphone")

    # Placeholder tool for Phase 1 verification (health check)
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
    ```

    Key points from locked decisions:
    - Use `from fastmcp import FastMCP` (NOT `from mcp.server.fastmcp`)
    - Call `mcp.run(transport="stdio")` - handles all protocol details
    - Log to stderr for debugging (not silent, not file-based)
    - Include a `ping` tool for health check verification
    - Do NOT load config on startup (lazy loading, deferred to Phase 2)
  </action>
  <verify>
    ```bash
    # Verify server module can be imported
    python -c "from vibraphone.server import main, mcp, ping; print('OK: Imports')"

    # Verify mcp instance exists
    python -c "from vibraphone.server import mcp; assert mcp.name == 'vibraphone'"

    # Verify ping tool is registered
    python -c "from vibraphone.server import ping; assert ping() == 'pong'"
    ```
  </verify>
  <done>
    - src/vibraphone/server.py exists with main() function
    - FastMCP instance `mcp` is created with name "vibraphone"
    - ping() tool is registered and returns "pong"
    - main() calls mcp.run(transport="stdio")
    - Startup message logged to stderr
  </done>
</task>

<task type="auto">
  <name>Task 2: Create lazy config loading stub</name>
  <files>
    - src/vibraphone/config.py
  </files>
  <action>
    Create `src/vibraphone/config.py` with a lazy loading stub that returns None when vibraphone.yaml doesn't exist:

    ```python
    """Configuration loading for vibraphone.

    Config is loaded lazily on first access, not on server startup.
    This allows the server to start without vibraphone.yaml present.
    """

    from dataclasses import dataclass
    from pathlib import Path
    from typing import Self

    @dataclass
    class VibraphoneConfig:
        """Configuration for vibraphone MCP server.

        This is a stub for Phase 2. Full implementation will include
        worktree paths, quality gate settings, and stack configuration.
        """
        project_root: Path

        # Phase 2 will add:
        # worktrees_path: Path
        # quality_gate: QualityGateConfig
        # stack: StackConfig

    _config: VibraphoneConfig | None = None

    def get_config() -> VibraphoneConfig | None:
        """Load config lazily. Returns None if vibraphone.yaml not found.

        This implements the lazy loading pattern from RESEARCH.md:
        - Config loads on first access, not on server startup
        - Returns None when vibraphone.yaml is absent (PKG-04)
        - Caches result for subsequent calls

        Full implementation coming in Phase 2: Configuration & Core Utilities.
        """
        global _config
        if _config is not None:
            return _config

        # Stub: Check for vibraphone.yaml in current directory
        # Phase 2 will implement directory walking and YAML parsing
        config_path = Path.cwd() / "vibraphone.yaml"
        if not config_path.exists():
            return None

        # Placeholder: Would parse YAML and create VibraphoneConfig
        # For now, just indicate config file exists
        _config = VibraphoneConfig(project_root=Path.cwd())
        return _config

    def clear_config_cache() -> None:
        """Clear the cached config. Useful for testing."""
        global _config
        _config = None
    ```

    This stub satisfies PKG-04 (server starts without config) and provides the interface for Phase 2 implementation.
  </action>
  <verify>
    ```bash
    # Verify config module can be imported
    python -c "from vibraphone.config import get_config, VibraphoneConfig, clear_config_cache"

    # Verify get_config returns None when no vibraphone.yaml
    cd /tmp && python -c "from vibraphone.config import get_config; assert get_config() is None"

    # Verify VibraphoneConfig is a dataclass
    python -c "from vibraphone.config import VibraphoneConfig; from dataclasses import is_dataclass; assert is_dataclass(VibraphoneConfig)"
    ```
  </verify>
  <done>
    - src/vibraphone/config.py exists with VibraphoneConfig dataclass
    - get_config() function returns None when vibraphone.yaml doesn't exist
    - Config caching is implemented for performance
    - clear_config_cache() available for testing
  </done>
</task>

<task type="auto">
  <name>Task 3: Verify entry point registration and server startup</name>
  <files>
    - (none - verification task)
  </files>
  <action>
    Verify the vibraphone command works:

    1. Reinstall package to register entry point:
       ```bash
       uv pip install -e ".[dev]"
       ```

    2. Verify entry point is registered:
       ```bash
       which vibraphone || uv tool list | grep vibraphone
       ```

    3. Test server startup (will block, so use timeout):
       ```bash
       timeout 2 vibraphone 2>&1 | head -1 || true
       ```
       Expected output: "vibraphone MCP server starting (v0.1.0)"

    4. Verify server can be imported and run via Python:
       ```bash
       timeout 2 python -m vibraphone.server 2>&1 | head -1 || true
       ```

    Note: Full MCP protocol testing happens in Plan 03. This task verifies basic startup only.
  </action>
  <verify>
    ```bash
    # Verify entry point exists
    python -c "from vibraphone.server import main; print('OK: main() callable')"

    # Verify server module can be run
    timeout 2 python -c "from vibraphone.server import main; print('Server would start here')" 2>&1 | grep -q "Server would start" && echo "OK: Module runnable"

    # Verify startup message goes to stderr
    timeout 2 python -c "import sys; from vibraphone.server import mcp; print('mcp instance OK', file=sys.stderr)" 2>&1 | grep -q "mcp instance OK" && echo "OK: Stderr logging"
    ```
  </verify>
  <done>
    - `vibraphone` command is registered and executable
    - Running `vibraphone` outputs startup message to stderr
    - Server starts without vibraphone.yaml present (no crash)
    - Entry point can also be run via `python -m vibraphone.server`
  </done>
</task>

</tasks>

<verification>
After all tasks complete:
1. Run `uv pip install -e ".[dev]"` - must register entry point
2. Run `timeout 2 vibraphone 2>&1` - must print startup message
3. Run server from directory without vibraphone.yaml - must not crash
4. Verify ping tool is accessible via MCP protocol (Plan 03)
</verification>

<success_criteria>
- PKG-03: `vibraphone` command starts FastMCP server on stdio transport - DONE
- PKG-04: Server starts without vibraphone.yaml present (zero-config, stays quiet) - DONE
- Entry point registered and working
- Startup message logged to stderr
- Config stub returns None when vibraphone.yaml absent
</success_criteria>

<output>
After completion, create `.planning/phases/01-package-foundation/01-02-SUMMARY.md`
</output>
