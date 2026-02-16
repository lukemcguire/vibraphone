# Architecture Patterns: Python MCP Server Package

**Domain:** Python MCP server (standalone package)
**Researched:** 2026-02-16
**Confidence:** MEDIUM (based on Python packaging standards + MCP SDK patterns from training data, web research tools unavailable)

## Recommended Architecture

### Package Layout (src layout)

```
vibraphone/
├── pyproject.toml                    # PEP 621 metadata, build config, entry point
├── README.md
├── LICENSE
├── .python-version                   # Python version pinning
├── src/
│   └── vibraphone/
│       ├── __init__.py               # Package metadata (__version__, __all__)
│       ├── __main__.py               # Entry point: python -m vibraphone
│       ├── server.py                 # FastMCP server definition
│       ├── config.py                 # Configuration loading (vibraphone.yaml)
│       ├── tools/                    # MCP tool implementations
│       │   ├── __init__.py
│       │   ├── beads_tools.py        # Task management (br integration)
│       │   ├── bridge_tools.py       # GSD integration (npx delegation)
│       │   ├── quality_tools.py      # Lint/test/format runners
│       │   ├── review_tools.py       # LLM-powered code review
│       │   ├── session_tools.py      # Session state management
│       │   ├── stack_tools.py        # Stack configuration
│       │   └── worktree_tools.py     # Git worktree isolation
│       ├── utils/                    # Shared utilities
│       │   ├── __init__.py
│       │   ├── br_client.py          # beads_rust CLI wrapper
│       │   └── session.py            # Session state persistence
│       └── templates/                # Bundled scaffolding files
│           ├── vibraphone.yaml       # Project genome template
│           ├── AGENTS.md             # Agent behavioral contract
│           ├── CLAUDE.md             # Claude Code entrypoint
│           ├── justfile_recipes.just # Justfile recipes to append
│           └── governance/           # .planning/vibraphone/ files
│               ├── CONSTITUTION.md
│               ├── ARCHITECTURE.md
│               ├── GLOSSARY.md
│               ├── DECISIONS.md
│               ├── prompts/
│               │   └── reviewer.md
│               └── specs/
│                   └── _TEMPLATE.md
├── tests/
│   ├── __init__.py
│   ├── unit/                         # Unit tests with mocks
│   │   ├── test_config.py
│   │   ├── test_beads_tools.py
│   │   ├── test_review_tools.py
│   │   └── ...
│   └── integration/                  # Integration tests (real git/br)
│       ├── test_worktree_flow.py
│       ├── test_session_recovery.py
│       └── test_init_project.py
└── docs/                             # Documentation (defer to later phase)
    ├── quickstart.md
    ├── tools/                        # API reference per tool
    └── architecture.md
```

### Why src layout?

**Rationale:**
- Prevents accidental imports from development directory (forces testing against installed package)
- Clean separation between package code and project metadata
- Standard practice in modern Python packaging (PEP 517/518/621)
- Hatchling (build backend) expects src layout by default

**Source:** Python Packaging Guide (training data, HIGH confidence for packaging patterns)

---

## Component Boundaries

### Layer 1: Entry Point

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `__main__.py` | CLI entry point (`python -m vibraphone`) | → `server.py` |
| `pyproject.toml [project.scripts]` | Console script entry point (`vibraphone` command) | → `__main__.py` or `server.py` |

**Implementation:**
```toml
[project.scripts]
vibraphone = "vibraphone.server:main"
```

**Data flow:** User runs `vibraphone` → setuptools/hatch invokes `server.main()` → FastMCP server starts

---

### Layer 2: Server Core

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `server.py` | FastMCP server definition, tool registration, startup hook (session recovery) | → `tools/*`, `config.py` |
| `config.py` | Load vibraphone.yaml, provide config to tools | ← All tool modules |

**Implementation pattern (FastMCP):**
```python
# server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("vibraphone")

# Auto-register tools via decorators
from vibraphone.tools import beads_tools, quality_tools, ...

@mcp.on_startup()
async def startup():
    """Auto-recover session if vibraphone.yaml exists."""
    config = load_config()
    if config and has_stale_session(config):
        await recover_session()

def main():
    mcp.run()
```

**Source:** FastMCP patterns from training data (MEDIUM confidence, official docs unavailable)

---

### Layer 3: Tool Modules

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `beads_tools.py` | Task lifecycle (start_task, complete_task, etc.) | → `utils/br_client.py` |
| `bridge_tools.py` | GSD integration (import_gsd_plan) | → shell (npx) |
| `quality_tools.py` | run_tests, run_lint, run_format | → shell (pytest, ruff) |
| `review_tools.py` | request_code_review (LLM-powered) | → config (reviewer prompt), LLM API |
| `session_tools.py` | Session state CRUD, recovery | → `utils/session.py` |
| `stack_tools.py` | configure_stack, init_project (scaffolding) | → `templates/` (bundled files) |
| `worktree_tools.py` | Git worktree management | → shell (git) |

**Tool registration pattern:**
```python
# tools/beads_tools.py
from vibraphone.server import mcp

@mcp.tool()
async def start_task(name: str, description: str) -> str:
    """Start a new task in a dedicated git worktree."""
    # Implementation
```

**Data flow:** MCP client (Claude Code) → FastMCP server → tool function → external process (br/git) → response

---

### Layer 4: Utilities

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `utils/br_client.py` | beads_rust CLI wrapper (subprocess calls) | ← `beads_tools.py` |
| `utils/session.py` | Session state persistence (.vibraphone/session.json) | ← `session_tools.py`, `server.py` |

**Implementation pattern:**
```python
# utils/br_client.py
class BeadsClient:
    def __init__(self, project_root: Path):
        self.project_root = project_root

    async def start_task(self, name: str) -> dict:
        """Call `br start` and parse output."""
        result = await asyncio.create_subprocess_exec(
            "br", "start", name,
            cwd=self.project_root,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        # Parse and return
```

---

### Layer 5: Templates (Bundled Static Files)

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `templates/` | Scaffolding file content for init_project | ← `stack_tools.init_project()` |

**Access pattern:**
```python
from importlib.resources import files

def get_template(name: str) -> str:
    """Load bundled template file."""
    return files("vibraphone.templates").joinpath(name).read_text()
```

**Why bundle templates in package:**
- init_project must generate files into user's project
- Templates need to version with the package
- importlib.resources handles installed vs editable mode transparently

**Source:** importlib.resources pattern (HIGH confidence, standard library)

---

## Data Flow

### Startup Flow

```
1. User runs: vibraphone
2. setuptools invokes: vibraphone.server:main()
3. main() creates FastMCP instance
4. FastMCP calls @mcp.on_startup() hooks
5. Startup hook checks for vibraphone.yaml
6. If found + stale session exists → auto-recover
7. FastMCP server starts stdio transport
8. Claude Code connects via MCP protocol
```

### Tool Invocation Flow

```
1. Claude Code sends MCP tool call → vibraphone server
2. FastMCP routes to @mcp.tool() decorated function
3. Tool function loads config (if needed)
4. Tool calls utility (e.g., br_client, shell command)
5. Utility returns result
6. Tool formats response
7. FastMCP sends MCP response → Claude Code
```

### Init Project Flow (Scaffolding)

```
1. Agent calls init_project tool
2. Tool checks: vibraphone.yaml already exists? → error
3. Tool loads templates from vibraphone.templates/
4. Tool writes files to user's project:
   - vibraphone.yaml (configured for project)
   - AGENTS.md, CLAUDE.md (root)
   - .planning/vibraphone/ governance files
   - Append recipes to Justfile (or create)
   - Update .mcp.json (add vibraphone server)
   - Update .gitignore (add .vibraphone/, worktrees)
5. Tool returns success message with next steps
```

### Session Recovery Flow

```
1. On startup: check for vibraphone.yaml
2. If exists: load session state from .vibraphone/session.json
3. If stale session (task active but no worktree):
   - Log warning
   - Call recover_session tool automatically
4. If no vibraphone.yaml: stay quiet (not a vibraphone project)
```

---

## Patterns to Follow

### Pattern 1: FastMCP Decorator-Based Tool Registration

**What:** Use `@mcp.tool()` decorator to register MCP tools

**When:** All tool implementations

**Example:**
```python
from vibraphone.server import mcp

@mcp.tool()
async def start_task(
    name: str,
    description: str,
    worktree_path: str | None = None
) -> str:
    """
    Start a new task in a dedicated git worktree.

    Args:
        name: Task identifier (branch name)
        description: Task description
        worktree_path: Override default worktree location

    Returns:
        Success message with worktree location
    """
    config = load_config()
    worktree_dir = worktree_path or config.worktree_location

    # Create worktree
    br_client = BeadsClient(config.project_root)
    await br_client.start_task(name)

    # Create git worktree
    await create_worktree(name, worktree_dir)

    return f"Task {name} started in {worktree_dir}/{name}"
```

**Why:** FastMCP auto-generates JSON schema from type hints, reducing boilerplate

**Source:** FastMCP SDK patterns (MEDIUM confidence, training data + limited web access)

---

### Pattern 2: Configuration as Dependency

**What:** Tools receive config via function call, not global state

**When:** Any tool needing project configuration

**Example:**
```python
# config.py
from pathlib import Path
from dataclasses import dataclass

@dataclass
class VibraphoneConfig:
    project_root: Path
    worktree_location: Path
    stack_id: str
    review_model: str

def load_config(project_root: Path | None = None) -> VibraphoneConfig | None:
    """Load vibraphone.yaml from project root."""
    root = project_root or Path.cwd()
    config_path = root / "vibraphone.yaml"

    if not config_path.exists():
        return None

    # Parse YAML and return config object
```

**Why:** Testable (mock config), explicit dependencies, supports multiple projects

---

### Pattern 3: Async Subprocess Calls

**What:** Use asyncio.create_subprocess_exec for all external commands

**When:** Calling br, git, npx, pytest, ruff

**Example:**
```python
async def run_command(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    """Run command and capture output."""
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode, stdout.decode(), stderr.decode()
```

**Why:** Non-blocking I/O (FastMCP is async), timeout support, clean cancellation

---

### Pattern 4: Template Access via importlib.resources

**What:** Load bundled templates using importlib.resources

**When:** init_project, any scaffolding operation

**Example:**
```python
from importlib.resources import files

def render_template(name: str, **kwargs) -> str:
    """Load template and substitute variables."""
    template_path = files("vibraphone.templates").joinpath(name)
    template = template_path.read_text()

    # Simple string substitution (or use jinja2 if needed)
    for key, value in kwargs.items():
        template = template.replace(f"{{{key}}}", value)

    return template
```

**Why:** Works in editable mode (`pip install -e .`) and installed mode, PEP 302 compliant

---

### Pattern 5: Graceful Degradation for External Dependencies

**What:** Detect missing dependencies (br, bv, just) and provide helpful errors

**When:** check_prerequisites, any tool requiring external binaries

**Example:**
```python
import shutil

def check_prerequisite(binary: str) -> dict[str, str | bool]:
    """Check if binary exists in PATH."""
    path = shutil.which(binary)

    install_commands = {
        "br": "cargo install beads_rust",
        "bv": "cargo install beads_rust --features vibraphone",
        "just": "cargo install just",
        "git": "Install from https://git-scm.com",
    }

    return {
        "binary": binary,
        "found": path is not None,
        "path": path or "Not found",
        "install_command": install_commands.get(binary, "Unknown"),
    }

@mcp.tool()
async def check_prerequisites() -> str:
    """Detect br, bv, node/npx, git, just and report status."""
    binaries = ["br", "bv", "just", "git", "node", "npx"]
    results = [check_prerequisite(b) for b in binaries]

    missing = [r for r in results if not r["found"]]

    if not missing:
        return "All prerequisites installed."

    return format_missing_deps(missing)
```

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Flat Package Structure

**What:** All modules at top level (`vibraphone/beads_tools.py`, `vibraphone/quality_tools.py`)

**Why bad:**
- Poor organization as codebase grows
- No clear separation between tools, utilities, templates
- Harder to navigate for contributors

**Instead:** Use subdirectories (`tools/`, `utils/`, `templates/`)

---

### Anti-Pattern 2: Global Server Instance Imported Everywhere

**What:**
```python
# server.py
mcp = FastMCP("vibraphone")

# beads_tools.py
from vibraphone.server import mcp  # Circular import risk
```

**Why bad:**
- Circular import risk (server imports tools, tools import server)
- Hard to test tools in isolation
- Tight coupling

**Instead:** Define server in one place, import tool modules after server creation:
```python
# server.py
mcp = FastMCP("vibraphone")

# Import tool modules to trigger decorator registration
from vibraphone.tools import (
    beads_tools,
    quality_tools,
    # ... all tools
)

def main():
    mcp.run()
```

**Note:** This requires careful ordering. Alternative: use explicit registration:
```python
# server.py
from vibraphone.tools.beads_tools import get_tools as get_beads_tools

mcp = FastMCP("vibraphone")

for tool_func in get_beads_tools():
    mcp.tool()(tool_func)
```

**Confidence:** MEDIUM (FastMCP-specific pattern, official guidance unavailable)

---

### Anti-Pattern 3: Hardcoded Paths

**What:**
```python
WORKTREE_DIR = Path.home() / ".vibraphone" / "worktrees"
```

**Why bad:**
- Not configurable per project
- Hard to test (always uses real filesystem location)
- Breaks when user wants custom location

**Instead:** Load from config:
```python
def get_worktree_dir(config: VibraphoneConfig) -> Path:
    return config.worktree_location

# In vibraphone.yaml:
# worktree_location: ~/.vibraphone/worktrees  # default
# worktree_location: /tmp/vibraphone-worktrees  # override
```

---

### Anti-Pattern 4: Synchronous Blocking Calls in Async Functions

**What:**
```python
@mcp.tool()
async def run_tests() -> str:
    result = subprocess.run(["pytest"], capture_output=True)  # BLOCKS event loop
    return result.stdout.decode()
```

**Why bad:**
- Blocks FastMCP's async event loop
- No cancellation support
- Other tool calls blocked while waiting

**Instead:** Use asyncio.create_subprocess_exec

---

### Anti-Pattern 5: Templates as Hardcoded Strings

**What:**
```python
AGENTS_MD = """
# Agent Behavioral Contract

## Core Principles
...
"""
```

**Why bad:**
- Unreadable in code
- Hard to edit (no syntax highlighting)
- Can't version independently

**Instead:** Bundle as files in `templates/`, load via importlib.resources

---

## Scalability Considerations

| Concern | At 100 users | At 10K users | At 1M users |
|---------|--------------|--------------|-------------|
| Package size | Templates ~50KB, acceptable | Same (static files don't grow) | Same |
| Startup time | <100ms (load config, check session) | Same (local file I/O) | Same |
| Concurrent sessions | N/A (single-user MCP server) | N/A | N/A |
| External dependency failures | Detect-and-guide (check_prerequisites) | Consider bundling br/bv binaries | Consider offering Docker image |

**Notes:**
- MCP servers are single-user, single-process (run locally per project)
- Scale concern is "number of installs" not "concurrent users"
- Main bottleneck: external process calls (br, git) — already async, non-blocking

---

## Build Order Dependencies

### Phase 1: Package Structure (no external dependencies)

1. Create `src/vibraphone/` layout
2. Add `pyproject.toml` with entry point
3. Implement `__main__.py` (minimal: just print version)
4. Verify: `uv pip install -e . && vibraphone` runs

**Rationale:** Establishes installability early, unblocks parallel work on components

---

### Phase 2: Core Server + Config (depends on Phase 1)

1. Implement `server.py` (FastMCP server definition)
2. Implement `config.py` (vibraphone.yaml loading)
3. Add startup hook (session recovery check)
4. Verify: Server starts, loads config, exits gracefully

**Rationale:** Server infrastructure required before tools can register

---

### Phase 3: Utilities (parallel with Phase 2)

1. Implement `utils/br_client.py`
2. Implement `utils/session.py`
3. Unit tests for utilities (mock subprocess calls)

**Rationale:** Tools depend on utilities, can be developed in parallel with server

---

### Phase 4: Tool Migration (depends on Phase 2 + 3)

1. Migrate existing tools one-by-one to new structure
2. Each tool: decorator registration, async subprocess, config loading
3. Unit tests per tool (mock br_client, session)
4. Integration tests per tool (real git/br)

**Order:**
1. `worktree_tools.py` (foundational, no external tool dependencies)
2. `beads_tools.py` (depends on worktree_tools, br_client)
3. `quality_tools.py` (independent)
4. `session_tools.py` (independent)
5. `review_tools.py` (independent, but complex LLM integration)
6. `bridge_tools.py` (depends on session understanding)
7. `stack_tools.py` (depends on templates from Phase 5)

**Rationale:** Worktree → beads creates foundation for task workflow; others can proceed in parallel

---

### Phase 5: Templates + Scaffolding (depends on Phase 1)

1. Create `src/vibraphone/templates/` directory
2. Add all scaffolding files (AGENTS.md, CONSTITUTION.md, etc.)
3. Implement template loading (importlib.resources)
4. Implement `init_project` tool (depends on template loading)
5. Integration test: init_project in empty directory

**Rationale:** Templates needed for stack_tools.init_project; can be done in parallel with tool migration

---

### Phase 6: Testing + Documentation (ongoing)

1. Unit tests for all components
2. Integration tests for workflows
3. Documentation: README, quickstart, tool API reference

**Rationale:** Continuous throughout other phases

---

## Configuration Schema

### vibraphone.yaml

```yaml
# Project identification
project_name: my-project
stack_id: python-fastapi  # or rust-cli, typescript-react, etc.

# Paths (all support ~ expansion and relative paths)
worktree_location: ~/.vibraphone/worktrees  # Default
planning_dir: .planning/vibraphone  # Default

# Quality gate configuration
quality:
  test_command: pytest
  lint_command: ruff check .
  format_command: ruff format .

# Code review configuration
review:
  model: claude-opus-4-6  # Or other LLM
  reviewer_prompt: .planning/vibraphone/prompts/reviewer.md
  constitution: .planning/vibraphone/CONSTITUTION.md

# External tools (for check_prerequisites)
tools:
  beads: br
  just: just
  git: git
  gsd: npx get-shit-done  # Optional
```

**Future expansion:**
- Circuit breaker thresholds
- Parallel execution settings (when bv is available)
- Custom tool aliases

---

## Open Questions / Research Flags

### LOW confidence areas (need verification with official docs):

1. **FastMCP server lifecycle hooks** — Is `@mcp.on_startup()` the correct decorator? Does FastMCP support shutdown hooks?
2. **FastMCP tool schema generation** — Does FastMCP auto-generate schema from type hints, or manual JSON schema required?
3. **MCP stdio transport** — Does FastMCP handle stdio transport automatically, or needs explicit configuration?
4. **importlib.resources in Python 3.13** — `files()` API confirmed stable? (HIGH confidence for 3.9+, but verify 3.13 specifics)

### Areas for phase-specific research:

- **Session recovery implementation** — Current template has known bugs; needs debugging during migration
- **LLM API integration for code review** — Which client library? Direct HTTP calls? Async patterns?
- **Justfile recipe merging** — How to append recipes without breaking existing syntax?

---

## Sources

**Confidence Assessment:**

| Topic | Confidence | Source |
|-------|------------|--------|
| Python src layout | HIGH | PEP 517/518/621, Python Packaging Guide (training data) |
| Console script entry points | HIGH | setuptools documentation (training data) |
| importlib.resources | HIGH | Python standard library docs (training data) |
| asyncio subprocess | HIGH | Python standard library docs (training data) |
| FastMCP patterns | MEDIUM | Training data on FastMCP SDK (official docs unavailable during research) |
| MCP protocol | MEDIUM | Limited web access to modelcontextprotocol.io |
| Build order | MEDIUM | Inferred from dependency graph + experience |

**Note:** Web search tools were unavailable during research. Recommendations are based on:
- Python packaging standards (HIGH confidence: PEP compliance)
- FastMCP SDK patterns from training data (MEDIUM confidence: may need verification)
- General MCP architecture understanding (MEDIUM confidence: limited official doc access)

**Recommendation:** Verify FastMCP-specific patterns (decorators, lifecycle hooks, schema generation) with official documentation or examples before implementation.
