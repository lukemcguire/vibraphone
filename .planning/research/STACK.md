# Technology Stack

**Project:** Vibraphone MCP Server
**Researched:** 2026-02-18 (updated with slash commands research)
**Confidence:** HIGH (verified against official Anthropic documentation)

## Executive Summary

For a Python MCP server distributed via `uv tool install`, the standard 2025/2026 stack centers on:
- **pyproject.toml** (PEP 621) for all metadata
- **Hatchling** or **setuptools** for build backend
- **src/vibraphone/** layout for package structure
- **[project.scripts]** for CLI entry points
- **FastMCP** for MCP protocol implementation
- **Ruff** for linting/formatting (replacing black, flake8, isort)
- **pytest** for testing

For slash commands, the project uses **Agent Skills** (SKILL.md format) installed via `vibraphone-cli skill install` to `~/.claude/skills/v/`.

---

## Slash Commands / Skills Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Agent Skills | Claude Code 1.0+ | Model-invoked capabilities packaged as SKILL.md | Official mechanism for packaging slash commands; Claude autonomously discovers and invokes based on description |
| SKILL.md format | YAML frontmatter + Markdown | Skill definition file | Standard format for Claude Code skills; supports frontmatter for metadata and Markdown for instructions |
| Python 3.13+ | 3.13 | Package bundling and CLI | Already used by vibraphone; shutil/importlib.resources for bundling |
| importlib.resources | stdlib | Access bundled skill files from wheel | Clean access to package data without path hacks; works for both dev and installed packages |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| shutil | stdlib | Copy skill directories during installation | In CLI `skill install` command to copy bundled skill to ~/.claude/skills/ |
| argparse | stdlib | CLI argument parsing | Already used in vibraphone-cli for subcommands |
| pathlib | stdlib | Path manipulation | Cross-platform path handling for skill locations |

### Installation Locations

| Location | Type | Purpose |
|----------|------|---------|
| `~/.claude/skills/v/` | Personal Skill | User-level skill installation (current approach) |
| `.claude/skills/v/` | Project Skill | Team-shared skills (checked into git) |
| `src/vibraphone/skills/v/` | Bundled Skill | Packaged within vibraphone wheel for distribution |

## How Claude Code Discovers and Loads Skills

### Discovery Process

1. **Automatic Discovery**: Claude Code automatically discovers skills from three sources at startup:
   - Personal Skills: `~/.claude/skills/*/SKILL.md`
   - Project Skills: `.claude/skills/*/SKILL.md`
   - Plugin Skills: Bundled with installed plugins

2. **Invocation Model**: Skills are **model-invoked** (not user-invoked like slash commands):
   - Claude autonomously decides when to use a skill based on:
     - User request context
     - Skill's `description` field (critical for discovery)
   - User does NOT type `/skill-name` to invoke

3. **Contrast with Slash Commands**:
   - Slash commands: User types `/command-name` explicitly
   - Skills: Claude activates automatically when description matches context

### SKILL.md File Format

```markdown
---
name: skill-name
description: Brief description of what this skill does and when to use it.
allowed-tools: Read, Grep, Glob  # Optional: restrict available tools
---

# Skill Title

Instructions for Claude in Markdown format.

## Examples
...
```

**Frontmatter Fields:**

| Field | Required | Max Length | Format |
|-------|----------|------------|--------|
| `name` | Yes | 64 chars | lowercase, numbers, hyphens only |
| `description` | Yes | 1024 chars | Include both what and when |
| `allowed-tools` | No | - | Comma-separated tool names |

### Current Vibraphone Implementation

The project already has a working skill implementation:

1. **Bundled Location**: `src/vibraphone/skills/v/SKILL.md`
2. **Installation CLI**: `vibraphone-cli skill install`
3. **Target Location**: `~/.claude/skills/v/`

The existing `SKILL.md` documents all `/v` commands as MCP tool invocations, with:
- Command syntax and flags
- MCP tool mappings
- JSON parameter examples
- Error handling guidance

## Integration with Python Package Bundling

### Current Approach (Working)

```python
# src/vibraphone/cli.py
SKILL_DEST_PATH = Path.home() / ".claude" / "skills" / "v"

def get_bundled_skill_path() -> Path | None:
    # Try importlib.resources first (works for installed packages)
    try:
        from importlib.resources import files
        skill_dir = files("vibraphone.skills").joinpath("v")
        if skill_dir.is_dir():
            return Path(str(skill_dir))
    except (ImportError, TypeError):
        pass

    # Fallback: check relative to this file (development mode)
    dev_path = Path(__file__).parent / "skills" / "v"
    if dev_path.is_dir():
        return dev_path
    return None

def cmd_skill_install() -> int:
    bundled_path = get_bundled_skill_path()
    if SKILL_DEST_PATH.exists():
        shutil.rmtree(SKILL_DEST_PATH)
    SKILL_DEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(bundled_path, SKILL_DEST_PATH)
    return 0
```

### pyproject.toml Configuration

```toml
[tool.hatch.build.targets.wheel]
# Include skills directory in wheel for importlib.resources access
artifacts = ["src/vibraphone/skills/"]
```

## Alternatives Considered for Slash Commands

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Skills (SKILL.md) | Slash commands (.md in .claude/commands/) | Use slash commands when you want explicit user invocation via `/command`. Use skills for automatic model-driven activation. |
| Personal skill (~/.claude/skills/) | Project skill (.claude/skills/) | Use project skills when team needs identical behavior. Use personal for individual customization. |
| CLI install command | Manual file copy | CLI is better for versioned releases; manual for rapid iteration. |

## What NOT to Use for Slash Commands

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Symlinks for skill installation | May break on Windows; Claude Code expects real directories | shutil.copytree for portable installation |
| JSON or YAML config files for skill definition | Claude Code requires SKILL.md format | SKILL.md with YAML frontmatter |
| MCP prompts as slash commands | Only works when MCP server is connected; skills work independently | Bundle as skill for always-available commands |
| Absolute paths in SKILL.md | Breaks portability across machines | Use relative paths or document that users must adjust |

## Key Design Decisions for Vibraphone

### Skill vs Slash Command

**Decision: Use Agent Skills (SKILL.md)**

Rationale:
1. The `/v` commands are already documented as model-invoked patterns
2. Skills provide better discoverability through description matching
3. Single file (SKILL.md) contains all command documentation
4. Users install once via `vibraphone-cli skill install`

### Installation Command Name

**Decision: Keep `vibraphone-cli skill install`**

The existing CLI already uses "skill" terminology which aligns with Claude Code's official naming.

### File Structure

```
vibraphone/
  src/vibraphone/
    skills/
      v/
        SKILL.md          # All /v command documentation
    cli.py                # skill install/status commands
    server.py             # MCP server (existing)
```

---

## Recommended Stack (General MCP Server)

### Build System & Packaging

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| pyproject.toml (PEP 621) | - | Single source of truth for project metadata | Standard since Python 3.11+. Replaces setup.py, setup.cfg. All modern tools read this. |
| Hatchling | latest | Build backend | Already in current pyproject.toml. Fast, modern, zero-config for simple packages. |
| uv | 0.5+ | Package manager & tool installer | HIGH confidence. Fast Rust-based pip replacement. Native `uv tool install` support is the deployment target. |

### Core Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| FastMCP | 2.0+ | MCP protocol server implementation | Purpose-built for MCP servers in Python. Handles stdio transport, tool registration, server lifecycle. |
| Python | >=3.13 | Runtime | Already specified in pyproject.toml. Modern async/await, type hints, pattern matching. |

### Project Structure

| Component | Path | Purpose | Why |
|-----------|------|---------|-----|
| Source layout | src/vibraphone/ | Package code | Import isolation, prevents accidental imports of local files during development. Recommended by PyPA. |
| Entry point | [project.scripts] | CLI command registration | Standard for `uv tool install`. Maps `vibraphone` command to server entry point. |
| Tests | tests/ | Test suite | Standard pytest discovery location. |
| Configuration | pyproject.toml | All config centralized | Ruff, pytest, coverage all configured here. |

### Development Tools

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Ruff | 0.15+ | Linting & formatting | 10-100x faster than flake8/black. Replaces: black, isort, flake8 + plugins. Already configured extensively in pyproject.toml. |
| pytest | 8.0+ | Testing framework | Standard Python test framework. Already configured. |
| pytest-cov | latest | Coverage reporting | Standard coverage tool for pytest. |
| ty | 0.0.17+ | Type checking | Fast Rust-based type checker. Configured as `[tool.ty.environment]` in pyproject.toml. |

### Runtime Dependencies

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| FastMCP | 2.0+ | MCP server framework | Required. Core dependency. |
| pyyaml | 6.0+ | Parse vibraphone.yaml | Required. Config file is YAML. |
| pydantic | 2.0+ | Config validation | Required. Type-safe config parsing. |
| python-dotenv | 1.0+ | Environment variable loading | Required. API key management. |
| instructor | 1.0+ | Structured LLM outputs | Required. Code review LLM calls. |
| defusedxml | 0.7+ | Secure XML parsing | Required. Security for XML handling. |

### External CLI Dependencies (not in PyPI)

Vibraphone shells out to external tools. These are **not** Python dependencies.

| Tool | Install Method | Detection Strategy |
|------|----------------|-------------------|
| br (beads_rust) | `cargo install beads_rust` | `check_prerequisites` tool detects, guides install |
| bv (beads_rust) | `cargo install beads_rust` | Optional. Graceful degradation if missing. |
| git | System package manager | Assume present (universal developer tool) |
| just | System package manager or cargo | `check_prerequisites` detects |
| node/npx | System package manager | For GSD integration. `check_prerequisites` detects |

**Architecture decision:** Detect-and-guide, not bundle. Vibraphone reports missing tools via `check_prerequisites` and provides install commands. Does NOT bundle binaries or auto-install.

---

## Package Structure

```
vibraphone/
  pyproject.toml              # PEP 621 metadata, dependencies, tool config
  README.md                   # PyPI description
  LICENSE                     # Required for PyPI
  src/
    vibraphone/
      __init__.py             # Package entry, version
      server.py               # FastMCP server entry point
      cli.py                  # vibraphone-cli skill install/status
      config.py               # vibraphone.yaml parsing
      tools/                  # MCP tools (start_task, etc.)
        __init__.py
        task_tools.py
        worktree_tools.py
        quality_gate_tools.py
        scaffold_tools.py
        stack_tools.py
        bridge_tools.py
      utils/                  # Shared utilities
        __init__.py
        cli_runner.py
        command_runner.py
        context.py
        errors.py
        plan_parser.py
        prerequisites.py
        quality_state.py
        session.py
        template_loader.py
        worktree_ops.py
        auto_detect.py
        circuit_breaker.py
        code_reviewer.py
      templates/              # Files for init_project to generate
        __init__.py
      skills/                 # Bundled Claude Code skill
        __init__.py
        v/
          SKILL.md            # All /v command documentation
  tests/
    unit/                     # Unit tests with mocks
    integration/              # Integration tests with real git/br
```

---

## pyproject.toml Configuration (Current)

```toml
[project]
name = "vibraphone"
version = "0.1.0"
description = "Vibraphone is an MCP server for AI coding agents that enforces disciplined software development workflows."
readme = "README.md"
requires-python = ">=3.13"
license = {text = "MIT"}
authors = [
    {name = "Luke McGuire", email = "luke@example.com"}
]
dependencies = [
    "defusedxml>=0.7.1",
    "fastmcp>=2.0",
    "instructor>=1.0",
    "pydantic>=2.0",
    "python-dotenv>=1.0",
    "pyyaml>=6.0",
]

[project.scripts]
vibraphone = "vibraphone.server:main"
vibraphone-cli = "vibraphone.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
# Include templates and skills directories in wheel for importlib.resources access
artifacts = ["src/vibraphone/templates/", "src/vibraphone/skills/"]
```

---

## Installation Workflows

### Developer Installation (Editable)

```bash
# Clone repo
git clone https://github.com/lukemcguire/vibraphone.git
cd vibraphone

# Install with uv
uv pip install -e ".[dev]"

# Run tests
uv run pytest

# Start server manually
vibraphone

# Install skill
vibraphone-cli skill install
```

### End-User Installation (uv tool install)

```bash
# Install as isolated tool
uv tool install vibraphone

# Register with Claude Code MCP
claude mcp add vibraphone -- vibraphone

# Install slash commands
vibraphone-cli skill install

# Tool now available in Claude Code
# Skill activated automatically based on description matching
```

---

## Anti-Patterns to Avoid

### 1. Symlinks for skill installation
**Why avoid:** May break on Windows; Claude Code expects real directories
**Instead:** shutil.copytree for portable installation

### 2. Flat Layout (files at repo root)
**Why avoid:** Import pollution, accidental test imports, harder to package
**Instead:** src/vibraphone/ layout. Already implemented.

### 3. setup.py/setup.cfg
**Why avoid:** Deprecated. pyproject.toml (PEP 621) is the standard
**Instead:** All metadata in pyproject.toml. Already implemented.

### 4. Hardcoded Paths
**Why avoid:** Breaks when installed as package vs local dev
**Instead:** Use `importlib.resources` for package data. Already implemented in cli.py.

### 5. Synchronous HTTP Client (requests)
**Why avoid:** FastMCP is async. Blocking calls in async context cause issues
**Instead:** httpx (async HTTP client) if needed for external APIs.

### 6. Auto-Installation of External Tools
**Why avoid:** Security risk, sudo requirements, user environment violations
**Instead:** Detect + report missing tools. User installs via cargo/npm/apt.

---

## Confidence Assessment

| Area | Level | Reason |
|------|-------|--------|
| pyproject.toml (PEP 621) | HIGH | Standard since Python 3.11+, well-documented |
| src/ layout | HIGH | PyPA recommendation, industry standard |
| Ruff for linting | HIGH | Current in project, widely adopted |
| pytest framework | HIGH | Industry standard |
| FastMCP | HIGH | Verified version 2.0+ in dependencies |
| Agent Skills (SKILL.md) | HIGH | Verified against official Anthropic docs |
| skill install via CLI | HIGH | Already implemented and working |
| uv tool install | HIGH | Standard uv workflow |

**Overall confidence: HIGH**

---

## Sources

**Verified against official documentation:**
- [Anthropic Docs - Slash Commands](https://docs.anthropic.com/en/docs/claude-code/slash-commands) - Command file format, frontmatter fields, argument handling
- [Anthropic Docs - Agent Skills](https://docs.anthropic.com/en/docs/claude-code/skills) - SKILL.md format, discovery process, invocation model
- [Anthropic Docs - Tutorials](https://docs.anthropic.com/en/docs/claude-code/tutorials) - Create custom slash commands tutorial
- [Anthropic Docs - Memory](https://docs.anthropic.com/en/docs/claude-code/memory) - CLAUDE.md locations and hierarchy
- Existing vibraphone codebase - Current skill implementation pattern
- Python packaging PEPs (621, 517, 518) - Established standards

---

*Stack research for: Vibraphone MCP Server with Claude Code slash commands*
*Researched: 2026-02-18*
