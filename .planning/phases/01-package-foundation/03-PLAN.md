---
phase: 01-package-foundation
plan: 03
type: execute
wave: 3
depends_on:
  - "02"
files_modified:
  - tests/__init__.py
  - tests/test_server.py
  - tests/test_config.py
autonomous: false
requirements:
  - PKG-01
  - PKG-02

must_haves:
  truths:
    - "User can install vibraphone via `uv tool install vibraphone` from local path"
    - "User can install vibraphone via `pip install -e .` for development"
    - "Tests verify entry point registration and server startup"
    - "Tests verify package structure is correct"
  artifacts:
    - path: "tests/__init__.py"
      provides: "Test package initialization"
    - path: "tests/test_server.py"
      provides: "Server entry point tests"
      exports: ["test_entry_point_callable", "test_version_importable", "test_ping_tool"]
    - path: "tests/test_config.py"
      provides: "Config loading tests"
      exports: ["test_get_config_returns_none_without_yaml"]
  key_links:
    - from: "tests/test_server.py"
      to: "vibraphone.server"
      via: "Import and execution"
      pattern: "from vibraphone.server"
    - from: "pytest"
      to: "tests/"
      via: "Test discovery"
      pattern: "testpaths.*tests"
---

<objective>
Create comprehensive tests and verify both installation methods work end-to-end.

Purpose: Ensure the package can be installed via both `uv tool install` and `pip install -e .`, with tests that verify the entry point, server startup, and package structure.

Output: Working test suite and human-verified installation success.
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
@.planning/phases/01-package-foundation/01-02-SUMMARY.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create test package structure and server tests</name>
  <files>
    - tests/__init__.py
    - tests/test_server.py
  </files>
  <action>
    Create test files to verify package functionality:

    1. Create `tests/__init__.py` as empty file

    2. Create `tests/test_server.py`:

    ```python
    """Tests for vibraphone server entry point."""

    import subprocess
    import sys

    import pytest


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
        """Verify ping tool is registered and works."""
        from vibraphone.server import ping

        result = ping()
        assert result == "pong"


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
    ```

    These tests verify:
    - Package version is accessible
    - Server module imports without error
    - ping tool is registered and functional
    - MCP instance is configured correctly
    - Entry point module is runnable
  </action>
  <verify>
    ```bash
    # Run the tests
    uv run pytest tests/test_server.py -v

    # All tests should pass
    uv run pytest tests/test_server.py --tb=short
    ```
  </verify>
  <done>
    - tests/__init__.py exists
    - tests/test_server.py exists with 5 test functions
    - All tests pass when running `uv run pytest tests/test_server.py`
  </done>
</task>

<task type="auto">
  <name>Task 2: Create config tests</name>
  <files>
    - tests/test_config.py
  </files>
  <action>
    Create `tests/test_config.py` to verify config loading behavior:

    ```python
    """Tests for vibraphone configuration loading."""

    import os
    from pathlib import Path

    import pytest

    from vibraphone.config import VibraphoneConfig, clear_config_cache, get_config


    class TestGetConfig:
        """Tests for get_config function."""

        def setup_method(self):
            """Clear config cache before each test."""
            clear_config_cache()

        def test_returns_none_when_no_config_file(self, tmp_path: Path, monkeypatch):
            """Verify get_config returns None when vibraphone.yaml doesn't exist."""
            monkeypatch.chdir(tmp_path)
            assert get_config() is None

        def test_returns_cached_config(self, tmp_path: Path, monkeypatch):
            """Verify config is cached after first load."""
            monkeypatch.chdir(tmp_path)

            # First call
            result1 = get_config()
            # Second call (should return same cached value)
            result2 = get_config()

            assert result1 is result2

        def test_clear_cache_allows_reload(self, tmp_path: Path, monkeypatch):
            """Verify clear_config_cache allows config to be reloaded."""
            monkeypatch.chdir(tmp_path)

            get_config()
            clear_config_cache()

            # After clear, should fetch again (still None for no file)
            result = get_config()
            assert result is None


    class TestVibraphoneConfig:
        """Tests for VibraphoneConfig dataclass."""

        def test_is_dataclass(self):
            """Verify VibraphoneConfig is a dataclass."""
            from dataclasses import is_dataclass

            assert is_dataclass(VibraphoneConfig)

        def test_has_project_root_field(self):
            """Verify VibraphoneConfig has project_root field."""
            config = VibraphoneConfig(project_root=Path("/tmp"))
            assert config.project_root == Path("/tmp")
    ```

    These tests verify:
    - get_config returns None when vibraphone.yaml doesn't exist
    - Config caching works correctly
    - Cache can be cleared for testing
    - VibraphoneConfig dataclass structure is correct
  </action>
  <verify>
    ```bash
    # Run the config tests
    uv run pytest tests/test_config.py -v

    # All tests should pass
    uv run pytest tests/test_config.py --tb=short
    ```
  </verify>
  <done>
    - tests/test_config.py exists with test classes
    - All config tests pass
    - Tests verify lazy loading behavior
  </done>
</task>

<task type="checkpoint:human-verify">
  <name>Task 3: Human verification of Phase 1 completion</name>
  <files>
    - (none - verification checkpoint)
  </files>
  <action>
    Human verifies complete Phase 1 implementation end-to-end.
  </action>
  <verify>
    Human runs verification commands and confirms success.
  </verify>
  <done>
    All Phase 1 success criteria verified by human.
  </done>
  <what-built>
    Complete Phase 1 package foundation:
    - src/vibraphone/ package structure with __init__.py, server.py, config.py, tools/, utils/
    - pyproject.toml configured for src layout with fastmcp and pyyaml dependencies
    - Entry point `vibraphone = "vibraphone.server:main"` registered
    - FastMCP server that starts on stdio transport
    - Lazy config loading stub that returns None when vibraphone.yaml absent
    - Test suite verifying all functionality
  </what-built>
  <how-to-verify>
    Run these commands in order to verify the complete Phase 1 implementation:

    **1. Verify editable install (PKG-02):**
    ```bash
    cd /home/luke/workspace/github.com/lukemcguire/vibraphone
    uv pip install -e ".[dev]"
    python -c "import vibraphone; print(f'Version: {vibraphone.__version__}')"
    ```
    Expected: "Version: 0.1.0"

    **2. Verify uv tool install (PKG-01):**
    ```bash
    uv tool install .
    which vibraphone
    ```
    Expected: Path to vibraphone executable

    **3. Verify server starts without config (PKG-04):**
    ```bash
    cd /tmp  # Directory without vibraphone.yaml
    timeout 2 vibraphone 2>&1 | head -1
    ```
    Expected: "vibraphone MCP server starting (v0.1.0)"

    **4. Run test suite:**
    ```bash
    cd /home/luke/workspace/github.com/lukemcguire/vibraphone
    uv run pytest -v
    ```
    Expected: All tests pass

    **5. Verify package structure (PKG-05):**
    ```bash
    ls -la src/vibraphone/
    ```
    Expected: __init__.py, server.py, config.py, tools/, utils/
  </how-to-verify>
  <resume-signal>
    Type "approved" if all verifications pass, or describe any issues found.
  </resume-signal>
</task>

</tasks>

<verification>
After all tasks complete:
1. `uv run pytest tests/` - all tests must pass
2. `uv pip install -e .` - must succeed
3. `uv tool install .` - must register vibraphone command
4. `vibraphone` command - must start server without vibraphone.yaml
</verification>

<success_criteria>
- PKG-01: Package installable via `uv tool install vibraphone` from local path - VERIFIED
- PKG-02: Package installable via `pip install -e .` for development - VERIFIED
- All tests pass
- Human verification confirms end-to-end installation works
</success_criteria>

<output>
After completion, create `.planning/phases/01-package-foundation/01-03-SUMMARY.md`
</output>
