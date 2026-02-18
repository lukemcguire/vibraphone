# Architecture Patterns: Python MCP Server Package

**Domain:** Python MCP server (standalone package)
**Researched:** 2026-02-16 (updated 2026-02-18 for slash commands)
**Confidence:** HIGH (slash commands), MEDIUM (general MCP patterns)

---

# Slash Command Architecture (Added 2026-02-18)

## Overview

This section documents the architecture for bundling and installing slash commands
(`/v` commands) in the vibraphone package.

## System Overview

```
+-------------------------------------------------------------+
|                    Claude Code Runtime                       |
+-------------------------------------------------------------+
|  +-------------+  +-------------+  +---------------------+  |
|  | ~/.claude/  |  | ~/.claude/  |  | MCP Server Process  |  |
|  | skills/     |  | commands/   |  | (vibraphone)        |  |
|  | (obsolete)  |  | v.md        |  |                     |  |
|  +-------------+  +-------------+  +---------------------+  |
|                          |                   |               |
+--------------------------+-------------------+---------------+
                           |                   |
                           v                   v
+-------------------------------------------------------------+
|                     Vibraphone Package                      |
+-------------------------------------------------------------+
|  +-------------+  +-------------+  +---------------------+  |
|  | commands/   |  | templates/  |  | MCP Tools           |  |
|  | v.md        |  | (Jinja2)    |  | (FastMCP)           |  |
|  +-------------+  +-------------+  +---------------------+  |
|                                                             |
|  cli.py: setup-commands → copies v.md to ~/.claude/commands/|
+-------------------------------------------------------------+
```

## Current vs Target State

### Current State (Problem)

1. **Mixed terminology**: "skills" vs "commands" confusion
2. **Wrong installation target**: Installing to `~/.claude/skills/v/`
   instead of `~/.claude/commands/v.md`
3. **Single monolithic SKILL.md**: All commands in one file, not in
   individual .md files (this is actually fine for /v subcommand pattern)
4. **Incomplete bundling**: skills/ in artifacts but targeting wrong location

### Target State (Solution)

Per Claude Code documentation (HIGH confidence - official docs):

- **Commands** are what users invoke with `/v`
- **Location**: `~/.claude/commands/v.md` for user-level `/v` command
- **Format**: Single `v.md` file that accepts `$ARGUMENTS` for subcommands

**Key insight**: A file at `~/.claude/commands/v.md` creates `/v` command.
The file's `$ARGUMENTS` placeholder captures everything after `/v`.

## Recommended Project Structure

```
src/vibraphone/
+-- commands/                    # Bundled slash commands
|   +-- __init__.py              # Package marker (empty)
|   +-- v.md                     # The /v slash command
+-- skills/                      # REMOVE: Obsolete location
|   +-- __init__.py
|   +-- v/
|       +-- SKILL.md
+-- templates/                   # EXISTING: Jinja2 templates
|   +-- __init__.py
|   +-- vibraphone.yaml.j2
|   +-- ...
+-- cli.py                       # MODIFY: Change install target
+-- server.py
+-- ...
```

### Structure Rationale

- **commands/**: Matches Claude Code's terminology and expected location
- **v.md**: Single file containing all /v subcommands (simpler than 25+
  individual files)
- **Remove skills/**: Was incorrect terminology; skills are for extended
  capabilities, not slash commands

## Command File Format

### v.md Structure

```markdown
---
name: v
description: Vibraphone workflow commands for MCP tool orchestration
argument-hint: <command> [args...] -- init|list|next|start|test|commit|...
allowed-tools:
  - mcp__vibraphone
---

## MCP Tool Calling Convention

When calling vibraphone MCP tools, **dict and list parameters must be passed as
JSON objects/arrays, NOT as JSON strings**.

| WRONG                          | RIGHT                        |
| ------------------------------ | ---------------------------- |
| `values: "{\"lang\": \"go\"}"` | `values: {"lang": "go"}`     |

## Commands

### /v init [--language LANG] [--name NAME] [--apply]

Initialize vibraphone in the current project.
...

### /v list [--status STATUS] [--plan PLAN]

List tasks from Beads.
...

## Argument Parsing

1. Extract subcommand from $ARGUMENTS (first word)
2. Parse flags: `--flag value` or `-f value`
3. Map to MCP tool call
4. Handle response and display to user
```

### Key Frontmatter Fields

| Field | Purpose | Example |
|-------|---------|---------|
| `name` | Command name (derived from filename) | `v` |
| `description` | Shown in /help | `Vibraphone workflow commands` |
| `argument-hint` | Shown during autocomplete | `<command> [args...]` |
| `allowed-tools` | Tools this command can use | `mcp__vibraphone` |

## Architectural Patterns

### Pattern 1: Single Command with Subcommands

**What:** One `/v` command that parses `$ARGUMENTS` for subcommand routing.

**When to use:** When commands share context and are tightly coupled.

**Trade-offs:**
- Pros: Simpler installation (1 file), shared documentation
- Cons: Larger single file, all-or-nothing updates

**Implementation:**

Claude Code automatically provides `$ARGUMENTS` containing everything after
`/v`. The v.md file instructs Claude how to parse and route:

```
User: /v init --language python
$ARGUMENTS = "init --language python"

Claude parses v.md and calls:
mcp__vibraphone__init_project({"values": {"language": "python"}})
```

### Pattern 2: Resource Bundling with Hatchling

**What:** Use `artifacts` in pyproject.toml to bundle non-Python files.

**Current pyproject.toml:**

```toml
[tool.hatch.build.targets.wheel]
artifacts = ["src/vibraphone/templates/", "src/vibraphone/skills/"]
```

**Updated configuration:**

```toml
[tool.hatch.build.targets.wheel]
artifacts = ["src/vibraphone/templates/", "src/vibraphone/commands/"]
```

### Pattern 3: CLI Installation Flow

**What:** User runs `vibraphone-cli setup-commands` to install slash commands.

**Implementation:**

```python
COMMAND_NAME = "v"
COMMAND_DEST_PATH = Path.home() / ".claude" / "commands" / f"{COMMAND_NAME}.md"

def get_bundled_command_path() -> Path | None:
    """Get path to bundled command file."""
    try:
        from importlib.resources import files

        command_file = files("vibraphone.commands").joinpath(f"{COMMAND_NAME}.md")
        if command_file.is_file():
            return Path(str(command_file))
    except (ImportError, TypeError):
        pass

    # Development fallback
    dev_path = Path(__file__).parent / "commands" / f"{COMMAND_NAME}.md"
    if dev_path.is_file():
        return dev_path

    return None

def cmd_setup_commands() -> int:
    """Install slash commands to ~/.claude/commands/."""
    # Clean up old skill installation if present
    old_skill_dir = Path.home() / ".claude" / "skills" / "v"
    if old_skill_dir.exists():
        shutil.rmtree(old_skill_dir)
        print(f"Removed old installation at {old_skill_dir}")

    bundled_path = get_bundled_command_path()
    if bundled_path is None:
        print("Error: Bundled command not found.", file=sys.stderr)
        return 1

    COMMAND_DEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(bundled_path, COMMAND_DEST_PATH)

    print(f"Commands installed to {COMMAND_DEST_PATH}")
    print("\nYou can now use /v commands in Claude Code:")
    print("  /v init --language python")
    print("\nRestart Claude Code if it's already running.")
    return 0
```

## Data Flow

### Installation Flow

```
User runs: vibraphone-cli setup-commands
         |
         v
+------------------------+
| get_bundled_command()  |
| (importlib.resources)  |
+------------------------+
         |
         v
+------------------------+
| Clean up old ~/.claude/|
| skills/v/ if present   |
+------------------------+
         |
         v
+------------------------+
| Copy to ~/.claude/     |
| commands/v.md          |
+------------------------+
         |
         v
+------------------------+
| User restarts Claude   |
| Code                   |
+------------------------+
         |
         v
+------------------------+
| /v commands available  |
+------------------------+
```

### Command Execution Flow

```
User types: /v init --language python
         |
         v
+------------------------+
| Claude Code reads      |
| ~/.claude/commands/v.md|
+------------------------+
         |
         v
+------------------------+
| Injects $ARGUMENTS:    |
| "init --language python"|
+------------------------+
         |
         v
+------------------------+
| Claude parses v.md     |
| instructions           |
+------------------------+
         |
         v
+------------------------+
| Calls MCP tool:        |
| vibraphone_init_project|
+------------------------+
         |
         v
+------------------------+
| MCP server processes   |
| and returns result     |
+------------------------+
```

## Integration Points

### With Existing Package

| Point | Current | Change Required |
|-------|---------|-----------------|
| `cli.py` | `skill install` subcommand | Rename to `setup-commands` |
| Installation target | `~/.claude/skills/v/` | `~/.claude/commands/v.md` |
| `pyproject.toml` | artifacts includes `skills/` | Change to `commands/` |
| `server.py` | Checks `check_skill_installed()` | Update to `check_commands_installed()` |

### With MCP Tools

Slash commands are **pure documentation** - they tell Claude which MCP tools
to call. No code changes to MCP tools required.

| Command | MCP Tool |
|---------|----------|
| `/v init` | `vibraphone_init_project` |
| `/v list` | `vibraphone_list_tasks` |
| `/v start <id>` | `vibraphone_start_task` |
| `/v test` | `vibraphone_run_tests` |
| `/v commit <msg>` | `vibraphone_attempt_commit` |
| `/v finish <id> <msg>` | Multi-step: commit, merge, cleanup, complete |

## Anti-Patterns

### Anti-Pattern 1: Installing to skills/ Directory

**What people do:** Install command files to `~/.claude/skills/`

**Why it's wrong:** Skills are for extended capabilities (long-running knowledge),
not slash commands (one-shot prompts).

**Do this instead:** Install to `~/.claude/commands/`

### Anti-Pattern 2: Creating /v/ Directory with Individual Files

**What people do:** Create `~/.claude/commands/v/init.md`, `v/list.md`, etc.

**Why it's wrong:** This creates `/init`, `/list` commands, NOT `/v init`,
`/v list`. Subdirectories are for organization only.

**Do this instead:** Single `v.md` that handles subcommands via `$ARGUMENTS`

### Anti-Pattern 3: Dynamic Command Generation

**What people do:** Generate .md files at install time based on MCP tool
discovery.

**Why it's wrong:** Fragile, breaks offline, unnecessary complexity.

**Do this instead:** Static v.md bundled with package, updated with releases

## Build Order

1. **Create `src/vibraphone/commands/` directory**
2. **Create `commands/__init__.py`** (empty package marker)
3. **Create `commands/v.md`** from existing `skills/v/SKILL.md`
   - Update YAML frontmatter to command format
   - Keep command documentation identical
4. **Update `cli.py`**:
   - Rename `skill install` to `setup-commands` (or add alias)
   - Change destination to `~/.claude/commands/v.md`
   - Update `get_bundled_command_path()` to use `vibraphone.commands`
   - Add cleanup for old `~/.claude/skills/v/` directory
5. **Update `pyproject.toml`**:
   - Change `artifacts` from `skills/` to `commands/`
6. **Update `server.py`**:
   - Rename `check_skill_installed()` to `check_commands_installed()`
   - Update path check to `~/.claude/commands/v.md`
7. **Remove `src/vibraphone/skills/` directory** (obsolete)

## Migration for Existing Users

For users who installed to `~/.claude/skills/v/`:

```python
def cmd_setup_commands() -> int:
    # Clean up old installation if present
    old_skill_dir = Path.home() / ".claude" / "skills" / "v"
    if old_skill_dir.exists():
        shutil.rmtree(old_skill_dir)
        print(f"Removed old installation at {old_skill_dir}")

    # Install new command...
```

## Sources

- [Claude Code Slash Commands Documentation](https://docs.anthropic.com/en/docs/claude-code/slash-commands) - HIGH confidence
- Existing `src/vibraphone/cli.py` - source code analysis
- Existing `src/vibraphone/server.py` - source code analysis
- Existing `src/vibraphone/utils/template_loader.py` - resource loading pattern

---

# Original Architecture Research (2026-02-16)

Below is the original architecture research for the general Python MCP server
package structure.

---

## Recommended Architecture

### Package Layout (src layout)

```
vibraphone/
+-- pyproject.toml                    # PEP 621 metadata, build config, entry point
+-- README.md
+-- LICENSE
+-- .python-version                   # Python version pinning
+-- src/
|   +-- vibraphone/
|       +-- __init__.py               # Package metadata (__version__, __all__)
|       +-- __main__.py               # Entry point: python -m vibraphone
|       +-- server.py                 # FastMCP server definition
|       +-- config.py                 # Configuration loading (vibraphone.yaml)
|       +-- tools/                    # MCP tool implementations
|       |   +-- __init__.py
|       |   +-- beads_tools.py        # Task management (br integration)
|       |   +-- bridge_tools.py       # GSD integration (npx delegation)
|       |   +-- quality_tools.py      # Lint/test/format runners
|       |   +-- review_tools.py       # LLM-powered code review
|       |   +-- session_tools.py      # Session state management
|       |   +-- stack_tools.py        # Stack configuration
|       |   +-- worktree_tools.py     # Git worktree isolation
|       +-- utils/                    # Shared utilities
|       |   +-- __init__.py
|       |   +-- br_client.py          # beads_rust CLI wrapper
|       |   +-- session.py            # Session state persistence
|       +-- templates/                # Bundled scaffolding files
|       |   +-- vibraphone.yaml       # Project genome template
|       |   +-- AGENTS.md             # Agent behavioral contract
|       |   +-- CLAUDE.md             # Claude Code entrypoint
|       |   +-- justfile_recipes.just # Justfile recipes to append
|       |   +-- governance/           # .planning/vibraphone/ files
|       |       +-- CONSTITUTION.md
|       |       +-- ARCHITECTURE.md
|       |       +-- GLOSSARY.md
|       |       +-- DECISIONS.md
|       |       +-- prompts/
|       |       |   +-- reviewer.md
|       |       +-- specs/
|       |           +-- _TEMPLATE.md
+-- tests/
|   +-- __init__.py
|   +-- unit/                         # Unit tests with mocks
|   |   +-- test_config.py
|   |   +-- test_beads_tools.py
|   |   +-- test_review_tools.py
|   |   +-- ...
|   +-- integration/                  # Integration tests (real git/br)
|       +-- test_worktree_flow.py
|       +-- test_session_recovery.py
|       +-- test_init_project.py
+-- docs/                             # Documentation (defer to later phase)
    +-- quickstart.md
    +-- tools/                        # API reference per tool
    +-- architecture.md
```

### Why src layout?

**Rationale:**
- Prevents accidental imports from development directory (forces testing
  against installed package)
- Clean separation between package code and project metadata
- Standard practice in modern Python packaging (PEP 517/518/621)
- Hatchling (build backend) expects src layout by default

**Source:** Python Packaging Guide (training data, HIGH confidence for
packaging patterns)

---

## Component Boundaries

### Layer 1: Entry Point

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `__main__.py` | CLI entry point (`python -m vibraphone`) | -> `server.py` |
| `pyproject.toml [project.scripts]` | Console script entry point (`vibraphone` command) | -> `__main__.py` or `server.py` |

**Implementation:**
```toml
[project.scripts]
vibraphone = "vibraphone.server:main"
```

**Data flow:** User runs `vibraphone` -> setuptools/hatch invokes
`server.main()` -> FastMCP server starts

---

### Layer 2: Server Core

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `server.py` | FastMCP server definition, tool registration, startup hook (session recovery) | -> `tools/*`, `config.py` |
| `config.py` | Load vibraphone.yaml, provide config to tools | <- All tool modules |

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

**Source:** FastMCP patterns from training data (MEDIUM confidence, official
docs unavailable)

---

### Layer 3: Tool Modules

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `beads_tools.py` | Task lifecycle (start_task, complete_task, etc.) | -> `utils/br_client.py` |
| `bridge_tools.py` | GSD integration (import_gsd_plan) | -> shell (npx) |
| `quality_tools.py` | run_tests, run_lint, run_format | -> shell (pytest, ruff) |
| `review_tools.py` | request_code_review (LLM-powered) | -> config (reviewer prompt), LLM API |
| `session_tools.py` | Session state CRUD, recovery | -> `utils/session.py` |
| `stack_tools.py` | configure_stack, init_project (scaffolding) | -> `templates/` (bundled files) |
| `worktree_tools.py` | Git worktree management | -> shell (git) |

**Tool registration pattern:**
```python
# tools/beads_tools.py
from vibraphone.server import mcp

@mcp.tool()
async def start_task(name: str, description: str) -> str:
    """Start a new task in a dedicated git worktree."""
    # Implementation
```

**Data flow:** MCP client (Claude Code) -> FastMCP server -> tool function ->
external process (br/git) -> response

---

### Layer 4: Utilities

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `utils/br_client.py` | beads_rust CLI wrapper (subprocess calls) | <- `beads_tools.py` |
| `utils/session.py` | Session state persistence (.vibraphone/session.json) | <- `session_tools.py`, `server.py` |

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
| `templates/` | Scaffolding file content for init_project | <- `stack_tools.init_project()` |

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
6. If found + stale session exists -> auto-recover
7. FastMCP server starts stdio transport
8. Claude Code connects via MCP protocol
```

### Tool Invocation Flow

```
1. Claude Code sends MCP tool call -> vibraphone server
2. FastMCP routes to @mcp.tool() decorated function
3. Tool function loads config (if needed)
4. Tool calls utility (e.g., br_client, shell command)
5. Utility returns result
6. Tool formats response
7. FastMCP sends MCP response -> Claude Code
```

### Init Project Flow (Scaffolding)

```
1. Agent calls init_project tool
2. Tool checks: vibraphone.yaml already exists? -> error
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

**Source:** FastMCP SDK patterns (MEDIUM confidence, training data + limited
web access)

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

**Why:** Testable (mock config), explicit dependencies, supports multiple
projects

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

**Why:** Non-blocking I/O (FastMCP is async), timeout support, clean
cancellation

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

**Why:** Works in editable mode (`pip install -e .`) and installed mode,
PEP 302 compliant

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

**What:** All modules at top level (`vibraphone/beads_tools.py`,
`vibraphone/quality_tools.py`)

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

**Instead:** Define server in one place, import tool modules after server
creation:
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
- Main bottleneck: external process calls (br, git) -- already async,
  non-blocking

---

## Build Order Dependencies

### Phase 1: Package Structure (no external dependencies)

1. Create `src/vibraphone/` layout
2. Add `pyproject.toml` with entry point
3. Implement `__main__.py` (minimal: just print version)
4. Verify: `uv pip install -e . && vibraphone` runs

**Rationale:** Establishes installability early, unblocks parallel work on
components

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

**Rationale:** Tools depend on utilities, can be developed in parallel with
server

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

**Rationale:** Worktree -> beads creates foundation for task workflow; others
can proceed in parallel

---

### Phase 5: Templates + Scaffolding (depends on Phase 1)

1. Create `src/vibraphone/templates/` directory
2. Add all scaffolding files (AGENTS.md, CONSTITUTION.md, etc.)
3. Implement template loading (importlib.resources)
4. Implement `init_project` tool (depends on template loading)
5. Integration test: init_project in empty directory

**Rationale:** Templates needed for stack_tools.init_project; can be done in
parallel with tool migration

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

1. **FastMCP server lifecycle hooks** -- Is `@mcp.on_startup()` the correct
   decorator? Does FastMCP support shutdown hooks?
2. **FastMCP tool schema generation** -- Does FastMCP auto-generate schema from
   type hints, or manual JSON schema required?
3. **MCP stdio transport** -- Does FastMCP handle stdio transport automatically,
   or needs explicit configuration?
4. **importlib.resources in Python 3.13** -- `files()` API confirmed stable?
   (HIGH confidence for 3.9+, but verify 3.13 specifics)

### Areas for phase-specific research:

- **Session recovery implementation** -- Current template has known bugs; needs
  debugging during migration
- **LLM API integration for code review** -- Which client library? Direct HTTP
  calls? Async patterns?
- **Justfile recipe merging** -- How to append recipes without breaking
  existing syntax?

---

## Sources

**Confidence Assessment:**

| Topic | Confidence | Source |
|-------|------------|--------|
| Python src layout | HIGH | PEP 517/518/621, Python Packaging Guide (training data) |
| Console script entry points | HIGH | setuptools documentation (training data) |
| importlib.resources | HIGH | Python standard library docs (training data) |
| asyncio subprocess | HIGH | Python standard library docs (training data) |
| Claude Code slash commands | HIGH | Official Anthropic documentation (2026-02-18) |
| FastMCP patterns | MEDIUM | Training data on FastMCP SDK (official docs unavailable during research) |
| MCP protocol | MEDIUM | Limited web access to modelcontextprotocol.io |
| Build order | MEDIUM | Inferred from dependency graph + experience |

**Note:** Web search tools were unavailable during original research.
Slash command research (2026-02-18) used official Anthropic documentation.

**Recommendation:** Verify FastMCP-specific patterns (decorators, lifecycle
hooks, schema generation) with official documentation or examples before
implementation.
