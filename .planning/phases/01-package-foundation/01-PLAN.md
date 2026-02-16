---
phase: 01-package-foundation
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - pyproject.toml
  - src/vibraphone/__init__.py
  - src/vibraphone/tools/__init__.py
  - src/vibraphone/utils/__init__.py
autonomous: true
requirements:
  - PKG-05
  - PKG-06

must_haves:
  truths:
    - "Source code is organized under src/vibraphone/ directory"
    - "pyproject.toml has no flat-layout hatch config"
    - "All core dependencies are declared in pyproject.toml"
    - "Package version is accessible via vibraphone.__version__"
  artifacts:
    - path: "src/vibraphone/__init__.py"
      provides: "Package initialization and version"
      contains: "__version__"
    - path: "pyproject.toml"
      provides: "Package metadata and dependencies"
      contains: "fastmcp"
      contains: "pyyaml"
    - path: "src/vibraphone/tools/__init__.py"
      provides: "Tools package placeholder"
    - path: "src/vibraphone/utils/__init__.py"
      provides: "Utils package placeholder"
  key_links:
    - from: "pyproject.toml"
      to: "src/vibraphone/"
      via: "Hatchling auto-discovery"
      pattern: "build-backend.*hatchling"
---

<objective>
Create the foundational package structure with src layout and configure pyproject.toml for installable package.

Purpose: Establish proper Python package structure following src layout convention, enabling both uv tool install and pip install -e. This is the foundation all subsequent phases build upon.

Output: Working package structure with proper metadata, dependencies declared, and Hatchling configured for auto-discovery.
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
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create src/vibraphone package structure</name>
  <files>
    - src/vibraphone/__init__.py
    - src/vibraphone/tools/__init__.py
    - src/vibraphone/utils/__init__.py
  </files>
  <action>
    Create the src layout package structure:

    1. Create `src/vibraphone/__init__.py` with:
       - `__version__ = "0.1.0"` constant
       - Docstring explaining vibraphone is an MCP server

    2. Create `src/vibraphone/tools/__init__.py` as empty file (placeholder for Phase 3+)

    3. Create `src/vibraphone/utils/__init__.py` as empty file (placeholder for Phase 2+)

    This follows the locked decision from CONTEXT.md to mirror existing structure (server.py, config.py, tools/, utils/) under src/vibraphone/.
  </action>
  <verify>
    ```bash
    # Verify directory structure exists
    test -f src/vibraphone/__init__.py && echo "OK: __init__.py"
    test -f src/vibraphone/tools/__init__.py && echo "OK: tools/__init__.py"
    test -f src/vibraphone/utils/__init__.py && echo "OK: utils/__init__.py"

    # Verify version is accessible (after pip install -e .)
    python -c "import vibraphone; assert vibraphone.__version__ == '0.1.0'"
    ```
  </verify>
  <done>
    - src/vibraphone/ directory structure exists with __init__.py, tools/, utils/
    - `vibraphone.__version__` returns "0.1.0"
    - tools/ and utils/ packages are importable (even if empty)
  </done>
</task>

<task type="auto">
  <name>Task 2: Update pyproject.toml for src layout and dependencies</name>
  <files>
    - pyproject.toml
  </files>
  <action>
    Update pyproject.toml to support src layout and declare all dependencies:

    1. **Remove flat-layout hatch config** (critical for PKG-05):
       Delete the entire `[tool.hatch.build.targets.wheel]` section with `packages = ["config.py", "server.py", "tools", "utils"]`
       Hatchling auto-discovers src/vibraphone/ when no explicit config exists.

    2. **Add core dependencies** (PKG-06):
       ```toml
       dependencies = [
           "fastmcp>=2.0",
           "pyyaml>=6.0",
       ]
       ```

    3. **Add dev dependencies** in `[project.optional-dependencies]`:
       ```toml
       [project.optional-dependencies]
       dev = [
           "pytest>=8.0",
           "pytest-asyncio>=0.23",
           "pytest-xdist>=3.0",
           "pytest-mock>=3.12",
       ]
       ```

    4. **Add entry point** for vibraphone command (PKG-01, PKG-03):
       ```toml
       [project.scripts]
       vibraphone = "vibraphone.server:main"
       ```

    5. **Add project metadata** (license, authors, URLs):
       ```toml
       license = {text = "MIT"}
       authors = [
           {name = "Luke McGuire", email = "luke@example.com"}
       ]
       [project.urls]
       Homepage = "https://github.com/lukemcguire/vibraphone"
       Repository = "https://github.com/lukemcguire/vibraphone"
       ```

    6. **Update pytest config** to remove flat-layout pythonpath:
       Change `pythonpath = ["."]` to use importlib mode instead:
       ```toml
       [tool.pytest.ini_options]
       testpaths = ["tests"]
       asyncio_mode = "auto"
       addopts = "--import-mode=importlib"
       ```

    Preserve all existing ruff and ty configuration as-is.
  </action>
  <verify>
    ```bash
    # Verify no flat-layout hatch config exists
    ! grep -q "packages = \[\"config.py\"" pyproject.toml && echo "OK: No flat layout config"

    # Verify dependencies are declared
    grep -q "fastmcp" pyproject.toml && echo "OK: fastmcp dependency"
    grep -q "pyyaml" pyproject.toml && echo "OK: pyyaml dependency"

    # Verify entry point exists
    grep -q "vibraphone = \"vibraphone.server:main\"" pyproject.toml && echo "OK: Entry point"

    # Verify dev dependencies
    grep -q "pytest" pyproject.toml && echo "OK: pytest in dev deps"
    ```
  </verify>
  <done>
    - pyproject.toml has no flat-layout [tool.hatch.build.targets.wheel] config
    - Core dependencies (fastmcp, pyyaml) are declared
    - Dev dependencies (pytest, pytest-asyncio, pytest-xdist) are in [project.optional-dependencies]
    - Entry point `vibraphone = "vibraphone.server:main"` is registered
    - All existing ruff/ty configuration preserved
  </done>
</task>

<task type="auto">
  <name>Task 3: Verify package is pip-installable</name>
  <files>
    - (none - verification task)
  </files>
  <action>
    Verify the package structure works with pip editable install:

    1. Install in editable mode:
       ```bash
       uv pip install -e ".[dev]"
       ```

    2. Verify imports work:
       ```bash
       python -c "import vibraphone; print(vibraphone.__version__)"
       python -c "from vibraphone.tools import *"
       python -c "from vibraphone.utils import *"
       ```

    3. Verify entry point is registered (but will fail since server.py doesn't exist yet):
       ```bash
       python -c "from vibraphone.server import main" 2>&1 | grep -v "No module named" || echo "Expected: server.py not created yet"
       ```

    Note: Full end-to-end verification (uv tool install, server startup) happens in Plan 03 after server.py is created.
  </action>
  <verify>
    ```bash
    # Verify editable install succeeded
    uv pip show vibraphone | grep -q "editable" && echo "OK: Editable install"

    # Verify package imports correctly
    python -c "import vibraphone; assert vibraphone.__version__ == '0.1.0'" && echo "OK: Version accessible"

    # Verify package location is src/vibraphone
    python -c "import vibraphone; print(vibraphone.__file__)" | grep -q "src/vibraphone" && echo "OK: Src layout"
    ```
  </verify>
  <done>
    - `pip install -e .` succeeds without errors
    - `import vibraphone` works and returns correct version
    - Package imports from src/vibraphone/ (not flat layout)
    - Dev dependencies (pytest) are available
  </done>
</task>

</tasks>

<verification>
After all tasks complete:
1. Run `uv pip install -e ".[dev]"` - must succeed
2. Run `python -c "import vibraphone; print(vibraphone.__version__)"` - must print "0.1.0"
3. Verify no flat-layout config remains in pyproject.toml
4. Verify entry point is registered (check pyproject.toml)
</verification>

<success_criteria>
- PKG-05: Source code organized in src/vibraphone/ layout - DONE
- PKG-06: All Python dependencies declared in pyproject.toml - DONE
- Package is pip-installable in editable mode
- Entry point registered (server.py created in next plan)
</success_criteria>

<output>
After completion, create `.planning/phases/01-package-foundation/01-01-SUMMARY.md`
</output>
