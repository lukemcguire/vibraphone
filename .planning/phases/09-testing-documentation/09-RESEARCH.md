# Phase 9: Testing & Documentation - Research

**Researched:** 2026-02-17
**Domain:** pytest testing, MkDocs documentation, mkdocstrings API reference
**Confidence:** HIGH

## Summary

This phase focuses on preparing vibraphone for users through comprehensive testing and clear documentation. The codebase already has established testing patterns using pytest with pytest-asyncio and pytest-mock. Phase 8 introduced `get_execution_context()` which returns a tuple `(Path, SessionState | None)` — this broke test_phase5_success.py and needs fixing. For documentation, MkDocs with mkdocstrings provides hybrid documentation where API reference is auto-generated from Google-style docstrings while guides remain hand-written markdown.

**Primary recommendation:** Follow existing test patterns (class-based, mocker patches, `.fn` attribute for FastMCP tools). Use mkdocstrings `::: module.function` syntax for API docs. Fix regression by mocking `get_execution_context` to return proper tuple.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Test Strategy
- **Mock depth: Selective mocking** — Unit tests mock external tools (git, br, bv) but use real filesystem and Python APIs. Integration tests use real git repos in temp directories.
- **Integration coverage: Both per-tool and E2E** — Per-tool tests verify each tool in isolation with real git. E2E tests verify complete workflows (start_task -> work -> commit -> cleanup).
- **Must-pass workflows: Critical paths only** — start_task -> code_review -> commit flow, import_gsd_plan flow, init_project flow.
- **test_phase5_success.py regression: Fix and expand** — Fix mock patches for get_execution_context. Add worktree-specific integration tests alongside the fix.
- **CI approach: Fast feedback** — Unit tests run on every push. Integration tests run on main branch only.
- **Test data: Shared fixtures** — tests/fixtures/ contains sample GSD plans, git repos, config files.
- **Wheel verification: Both approaches** — Build-and-extract test verifies template files exist. Install-and-run test verifies init_project works from installed wheel.
- **Coverage gate: High coverage (90%+)** — Vibraphone is a developer tool, high bar justified.

#### README Focus
- **Primary reader: New users** — Developers installing vibraphone into their projects.
- **Quickstart: Full workflow (5 min)** — Install, init, start_task through commit.
- **Examples: Workflow examples** — 2-3 complete workflows showing tools working together.
- **Tone: Opinionated guide** — Explains why vibraphone exists, what problems it solves.
- **Structure: Problem-first** — Problem -> Solution -> Quickstart -> Examples -> Config.
- **Config docs: Brief in README** — Brief description of vibraphone.yaml fields, link to full reference.
- **Badges: Extended** — PyPI version, Python versions, license, CI status, coverage, code quality.
- **Visual: One diagram** — Workflow diagram or architecture diagram.
- **Review step: Run through /crafting-effective-readmes skill after drafting.**

#### API Docs Approach
- **Structure: Per-category files** — task-tools.md, quality-tools.md, worktree-tools.md, etc.
- **Per-tool content: Examples + API** — Description, parameters, return value, usage examples.
- **Parameter docs: Examples + field list** — Field list with types, no full JSON schemas inline.
- **Source: Hybrid** — Auto-generate API reference from docstrings via mkdocstrings. Hand-write examples, guides, architecture in markdown.
- **Error docs: Full error reference** — Dedicated error reference with all TaskError/WorktreeError types.
- **Location: docs/ directory** — All docs in docs/, keep README clean.
- **Scope: Full docs suite** — API reference (auto-generated), Architecture doc, Contributing guide.
- **Format: Hybrid MkDocs** — MkDocs + mkdocstrings plugin.

#### Test Organization
- **File layout: Mirror src structure** — tests/ mirrors src/vibraphone/ structure.
- **Naming: Match existing patterns** — Follow existing test naming conventions.
- **Class organization: Classes by feature** — Group related tests in classes (TestConfigDiscovery, TestConfigValidation).
- **Shared code: Both conftest.py and helpers/** — conftest.py for pytest fixtures at each level, tests/helpers/ for reusable test utilities.
- **Success tests: Per-phase files** — test_phase<N>_success.py per phase.
- **Integration tests: Separate directory** — tests/integration/ directory.
- **Fixtures: Both static files and factories** — Static files for complex data, factory functions for simple cases.
- **Dependencies: Extended pytest suite** — pytest, pytest-asyncio, pytest-cov, pytest-xdist, pytest-timeout.

### Claude's Discretion
(No discretion areas specified - all decisions locked)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TEST-01 | Unit tests run with mocked subprocesses and all pass | pytest-mock pattern with `mocker.patch()`, selective mocking strategy (mock git/br/bv, use real filesystem) |
| TEST-02 | Integration tests run with real git/br and key workflows pass | Integration tests in tests/integration/, use real git repos in temp directories, critical path workflows |
| TEST-03 | Installed wheel contains all template files verified by test | pytest-cov for coverage gate, build-and-extract and install-and-run verification patterns |
| DOC-01 | README explains installation and quickstart clearly | Problem-first structure, 5-min quickstart workflow, /crafting-effective-readmes skill |
| DOC-02 | Tool API reference documents all MCP tools with parameters and return values | mkdocstrings with Google-style docstrings, per-category files (task-tools.md, quality-tools.md) |
| DOC-03 | Architecture documentation | MkDocs with mkdocstrings, docs/ directory structure |

</phase_requirements>

## Standard Stack

### Core Testing
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | >=8.0 | Test framework | Already in pyproject.toml, industry standard |
| pytest-asyncio | >=0.23 | Async test support | Required for all MCP tools which are async |
| pytest-mock | >=3.12 | Mocking utilities | Mocker fixture provides cleaner API than unittest.mock |
| pytest-cov | (add) | Coverage reporting | Required for 90%+ coverage gate |
| pytest-timeout | (add) | Prevent hanging tests | Prevents async tests from hanging forever |

### Core Documentation
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| mkdocs | (add) | Static site generator | Better than Sphinx for Python docs |
| mkdocstrings | (add) | Auto-generate API docs from docstrings | Supports Google-style, integrates with MkDocs |
| mkdocs-material | (add) | Material theme for MkDocs | Best-in-class theme, search included |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest-xdist | >=3.0 | Parallel test execution | Already configured, use for faster test runs |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| mkdocstrings | pdoc | pdoc is simpler but mkdocstrings integrates with MkDocs for hybrid docs |
| MkDocs | Sphinx | Sphinx is more powerful but MkDocs is simpler and better for hybrid approach |

**Installation:**
```bash
uv add --group dev pytest-cov pytest-timeout mkdocs mkdocstrings mkdocs-material
```

## Architecture Patterns

### Recommended Test Structure
```
tests/
├── conftest.py              # Root-level fixtures (get_execution_context mock, tmp_git_repo)
├── fixtures/                # Static test data (sample GSD plans, config files)
│   ├── sample_plan.md
│   └── minimal_config.yaml
├── helpers/                 # Reusable test utilities
│   ├── git_helpers.py       # Functions to create test repos
│   └── mock_helpers.py      # Common mock configurations
├── integration/             # Integration tests (real git/br)
│   ├── conftest.py          # Integration-specific fixtures
│   ├── test_worktree_e2e.py # Full worktree workflows
│   └── test_quality_e2e.py  # Quality gate workflows
├── test_phase4_success.py   # Phase 4 success criteria
├── test_phase5_success.py   # Phase 5 success criteria (FIX THIS)
└── unit/                    # Unit tests (mocked subprocesses)
    └── (mirror src structure)
```

### Pattern 1: FastMCP Tool Testing
**What:** Access FastMCP tools via `.fn` attribute for direct testing
**When to use:** All MCP tool tests
**Example:**
```python
# Source: tests/test_phase5_success.py (existing pattern)
from vibraphone.tools.quality_gate_tools import run_tests

# Verify tool exists (has fn attribute for direct call)
assert hasattr(run_tests, "fn")

# Call tool directly
result = await run_tests.fn()

# Assert on result structure
assert result["status"] in ["pass", "fail", "ESCALATED"]
```

### Pattern 2: Mocking get_execution_context
**What:** Mock get_execution_context to return proper tuple for Phase 8 compatibility
**When to use:** All quality gate tool tests after Phase 8
**Example:**
```python
# Source: src/vibraphone/utils/context.py (actual signature)
# get_execution_context() -> tuple[Path, SessionState | None]

# Correct mock pattern
mock_context = mocker.patch("vibraphone.tools.quality_gate_tools.get_execution_context")
mock_context.return_value = (tmp_path, None)  # Returns tuple, not Path alone
```

### Pattern 3: Selective Mocking
**What:** Mock external CLI tools, use real filesystem
**When to use:** Unit tests
**Example:**
```python
# Source: tests/test_task_tools.py (existing pattern)
# Mock external CLI calls
mocker.patch(
    "vibraphone.tools.task_tools.run_cli",
    new_callable=AsyncMock,
    return_value=(0, "task-1\nReady\n", ""),
)

# Use real tmp_path fixture for filesystem operations
result = await tool.fn(tmp_path)
assert (tmp_path / "some_file").exists()  # Real filesystem check
```

### Pattern 4: mkdocstrings API Reference
**What:** Auto-generate API docs from Google-style docstrings
**When to use:** docs/tools/*.md files
**Example:**
```markdown
# Source: mkdocstrings documentation pattern
## Task Tools

::: vibraphone.tools.task_tools.list_tasks
    options:
      show_source: false
      docstring_style: google

::: vibraphone.tools.task_tools.next_ready
```

### Anti-Patterns to Avoid
- **Mocking get_execution_context to return only Path:** Must return `tuple[Path, SessionState | None]` after Phase 8
- **Calling tools via mcp.call_tool() in tests:** Use `.fn` attribute directly for cleaner tests
- **Full integration tests for every path:** Only critical paths need E2E, use unit tests for edge cases
- **Flat test functions:** Use class-based organization for related tests

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Test fixtures | Custom setup/teardown | pytest fixtures + conftest.py | Better isolation, automatic cleanup |
| Mock objects | Manual mock classes | pytest-mock `mocker` fixture | Cleaner syntax, auto-reset |
| Coverage reporting | Manual coverage tracking | pytest-cov plugin | Industry standard, CI integration |
| API documentation | Manual doc sync | mkdocstrings | Auto-generated from docstrings, stays in sync |
| Test timeouts | Per-test timeout logic | pytest-timeout decorator | Prevents CI hangs |

**Key insight:** The codebase already has established patterns. Match them rather than introducing new approaches.

## Common Pitfalls

### Pitfall 1: get_execution_context Tuple Return
**What goes wrong:** Phase 8 changed `get_execution_context()` to return `tuple[Path, SessionState | None]` instead of just `Path`. Tests that mock this function and return only a `Path` will fail with unpacking errors.
**Why it happens:** Phase 8 added session awareness without updating all test mocks.
**How to avoid:** Always mock as `mock.return_value = (path, None)` or `mock.return_value = (path, session_state)`.
**Warning signs:** `TypeError: cannot unpack non-iterable MagicMock object` or `ValueError: not enough values to unpack`

### Pitfall 2: Forgetting .fn for FastMCP Tools
**What goes wrong:** Calling `run_tests()` directly fails because decorated tools are FunctionTool objects, not functions.
**Why it happens:** FastMCP wraps functions in FunctionTool objects.
**How to avoid:** Always use `tool.fn()` for direct testing, or check `hasattr(tool, "fn")`.
**Warning signs:** `TypeError: 'FunctionTool' object is not callable`

### Pitfall 3: Integration Test CI Timeouts
**What goes wrong:** Running integration tests on every push slows CI significantly.
**Why it happens:** Real git operations are slow.
**How to avoid:** Run integration tests only on main branch (CI config), use unit tests for PR validation.
**Warning signs:** CI taking >10 minutes

### Pitfall 4: mkdocstrings Not Finding Modules
**What goes wrong:** `::: vibraphone.tools.task_tools` produces "module not found" error.
**Why it happens:** mkdocstrings needs proper Python path configuration.
**How to avoid:** Configure mkdocs.yml with proper watch paths, run `mkdocs serve` from project root.
**Warning signs:** "Module 'vibraphone' not found" in docs build

## Code Examples

Verified patterns from official sources:

### Unit Test with Selective Mocking
```python
# Source: tests/test_phase5_success.py (existing pattern)
@pytest.mark.asyncio
async def test_QUAL_01_run_tests_with_circuit_breaker(
    mocker: Any, tmp_path: Path
) -> None:
    """QUAL-01: Verify run_tests tool exists and circuit_breaker.check is called."""
    from vibraphone.tools.quality_gate_tools import run_tests

    # Verify tool exists
    assert hasattr(run_tests, "fn")

    # Mock external dependencies
    mocker.patch("vibraphone.tools.quality_gate_tools.get_project_root", return_value=tmp_path)
    mocker.patch(
        "vibraphone.tools.quality_gate_tools.run_command",
        new_callable=AsyncMock,
        return_value=(1, "", "test failed"),
    )

    # Mock state manager
    mock_state_manager_class = mocker.patch(
        "vibraphone.tools.quality_gate_tools.get_quality_state_manager"
    )
    mock_state_manager = MagicMock()
    mock_state_manager.load.return_value = QualityGateState(task_id="default", test_attempts=2)
    mock_state_manager_class.return_value = mock_state_manager

    # Run tool
    result = await run_tests.fn()

    # Verify response
    assert result["status"] == "ESCALATED"
```

### mkdocstrings Configuration
```yaml
# Source: mkdocstrings documentation (mkdocs.yml)
site_name: Vibraphone
theme:
  name: material

nav:
  - Home: index.md
  - Tools:
      - Task Tools: tools/task-tools.md
      - Quality Tools: tools/quality-tools.md
      - Worktree Tools: tools/worktree-tools.md

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          options:
            docstring_style: google
            show_source: false
```

### mkdocstrings API Page
```markdown
# Source: mkdocstrings documentation pattern (docs/tools/quality-tools.md)
# Quality Gate Tools

Tools for enforcing quality gates before commits.

## run_tests

::: vibraphone.tools.quality_gate_tools.run_tests
    options:
      docstring_style: google

## request_code_review

::: vibraphone.tools.quality_gate_tools.request_code_review
    options:
      docstring_style: google
```

### conftest.py for Integration Tests
```python
# Source: pytest fixtures documentation (tests/conftest.py)
import pytest
from pathlib import Path
import subprocess

@pytest.fixture
def tmp_git_repo(tmp_path: Path) -> Path:
    """Create a real git repository for integration tests."""
    repo = tmp_path / "test_repo"
    repo.mkdir()

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True, capture_output=True)

    # Create initial commit
    (repo / "README.md").write_text("# Test Repo")
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True, capture_output=True)

    return repo

@pytest.fixture
def mock_execution_context(tmp_path: Path, mocker):
    """Standard mock for get_execution_context returning proper tuple."""
    from vibraphone.utils.session import SessionState
    from datetime import datetime

    mock = mocker.patch("vibraphone.utils.context.get_execution_context")
    mock.return_value = (tmp_path, None)
    return mock
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Sphinx for all Python docs | MkDocs + mkdocstrings | Recent years | Simpler setup, better for hybrid docs |
| unittest.mock directly | pytest-mock `mocker` fixture | pytest best practice | Cleaner code, auto-reset |
| Flat test functions | Class-based test organization | Existing codebase pattern | Better organization |

**Deprecated/outdated:**
- `nose` test framework: Use pytest instead
- Manual mock patches without cleanup: Use pytest-mock for automatic cleanup

## Open Questions

1. **pytest-timeout configuration**
   - What we know: pytest-timeout exists and prevents hanging tests
   - What's unclear: Optimal timeout value for integration tests with real git
   - Recommendation: Start with 60s default, configure per-test with `@pytest.mark.timeout(120)` for slow integration tests

2. **mkdocs-material theme licensing**
   - What we know: mkdocs-material has MIT license for basic features
   - What's unclear: Whether advanced features (social cards, blog) require Insiders license
   - Recommendation: Use free tier features only; Insiders features are not needed for API docs

## Sources

### Primary (HIGH confidence)
- `/home/luke/workspace/github.com/lukemcguire/vibraphone/pyproject.toml` - Existing pytest configuration, dependencies
- `/home/luke/workspace/github.com/lukemcguire/vibraphone/tests/test_phase5_success.py` - Existing test patterns
- `/home/luke/workspace/github.com/lukemcguire/vibraphone/tests/test_phase4_success.py` - Phase success test pattern
- `/home/luke/workspace/github.com/lukemcguire/vibraphone/src/vibraphone/utils/context.py` - get_execution_context signature
- `/home/luke/workspace/github.com/lukemcguire/vibraphone/src/vibraphone/tools/quality_gate_tools.py` - MCP tool implementations with docstrings

### Secondary (MEDIUM confidence)
- mkdocstrings documentation (mkdocstrings.github.io) - Plugin configuration, ::: syntax
- pytest fixtures documentation (docs.pytest.org) - Fixture patterns, conftest.py

### Tertiary (LOW confidence)
- None - All findings verified against primary or secondary sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Based on existing pyproject.toml and established patterns
- Architecture: HIGH - Based on existing test files and source code
- Pitfalls: HIGH - Based on actual code analysis (get_execution_context signature change)
- Documentation: MEDIUM - Based on mkdocstrings official docs, not yet verified in project

**Research date:** 2026-02-17
**Valid until:** 30 days (stable tools and patterns)
