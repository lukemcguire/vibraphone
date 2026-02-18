# Phase 10: Command Infrastructure - Research

**Researched:** 2026-02-18
**Domain:** Slash command installation and migration
**Confidence:** HIGH

## Summary

Phase 10 establishes the `/v` slash command installation mechanism by migrating
from the deprecated skills-based approach to Claude Code's native commands
directory. The research confirms a straightforward implementation: create a
bundled `v.md` command file, add a `setup-commands` CLI subcommand, and remove
obsolete artifacts.

**Primary recommendation:** Implement minimal, focused changes - a single CLI
command that copies one bundled markdown file to the correct location.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Installation UX

- Minimal output on success: single line with destination path
- Always show restart reminder: "Restart Claude Code for commands to take
  effect"
- Silent overwrite if v.md already exists (no confirmation needed)
- No version info in output (keep it minimal)

#### Migration Handling

- No migration code needed - this is a one-time personal cleanup
- Old `~/.claude/skills/v/` directory: user will manually delete
- Old `vibraphone skill install` CLI: remove entirely, no compatibility alias
- No README or placeholder in skills directory

#### Error Handling

- Auto-create `~/.claude/commands/` if missing (no error)
- Permission errors: clear error message with path and suggestion
- Missing bundled v.md: clear error indicating corrupt install
- Exit codes: simple (0 = success, 1 = any failure)

#### Verification Approach

- No CLI verify flag needed
- setup-commands verifies by checking file exists and is non-empty
- No manual verification steps suggested to user
- Unit tests for: CLI command, file copy, error cases

#### Claude's Discretion

- Exact wording of error messages
- Exact wording of success message
- Test file organization

### Deferred Ideas (OUT OF SCOPE)

None - discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SLASH-01 | User can invoke core workflow tools via /v commands | v.md documents all workflow commands (list, next, start, test, lint, format, review, commit, merge, cleanup, complete, recover, status, health) |
| SLASH-02 | User can invoke dict-heavy tools via /v commands with proper parameter handling | v.md includes dict parameter handling convention and examples for init, configure-stack, import-plan |
| SLASH-03 | Stringification bug is investigated, root cause identified, and fixed or documented | v.md contains explicit MCP Tool Calling Convention section explaining dict/list parameter handling |
| SLASH-05 | User can run `vibraphone setup-commands` to install /v commands to ~/.claude/commands/v.md | cli.py implementation pattern documented below |
| SLASH-06 | Existing artifacts (skills/v/, vibraphone-cli skill install) are cleaned up or repurposed | Migration handling documented - user manually deletes old skills/v/, remove skill subcommand from CLI |

Note: SLASH-04 (documentation) is addressed in Phase 11, not this phase.
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| importlib.resources | stdlib | Access bundled command file from package | Python standard, works with wheels |
| argparse | stdlib | CLI argument parsing | Already in use in cli.py |
| pathlib | stdlib | Path manipulation | Standard, cross-platform |
| shutil | stdlib | File copy operations | Standard, handles metadata |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| sys | stdlib | Exit codes, stderr | For all error handling |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| argparse | click/typer | argparse already in use, no need for additional dependency |
| shutil.copy2 | Path.read_text/write_text | copy2 preserves metadata, slightly cleaner |

**Installation:** No additional packages needed - all standard library.

## Architecture Patterns

### Recommended Project Structure

```
src/vibraphone/
+-- commands/                    # NEW: Bundled slash commands
|   +-- __init__.py              # Package marker (empty)
|   +-- v.md                     # The /v slash command
+-- skills/                      # REMOVE: Obsolete location
|   +-- __init__.py
|   +-- v/
|       +-- SKILL.md
+-- templates/                   # EXISTING: Jinja2 templates (unchanged)
+-- cli.py                       # MODIFY: Add setup-commands, remove skill
+-- server.py                    # MODIFY: Update check message
```

### Pattern 1: Single Command File with Subcommands

**What:** One `v.md` file that Claude Code reads to understand `/v` routing.

**When to use:** When commands share context and are tightly coupled.

**Trade-offs:**
- Pros: Simpler installation (1 file), shared documentation, single source of
  truth
- Cons: Larger single file, all-or-nothing updates

**Implementation:**

Claude Code automatically provides `$ARGUMENTS` containing everything after
`/v`. The v.md file instructs Claude how to parse and route:

```text
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

### Pattern 3: CLI Installation Command

**What:** User runs `vibraphone setup-commands` to install slash commands.

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
    bundled_path = get_bundled_command_path()
    if bundled_path is None:
        print("Error: Bundled command file not found.", file=sys.stderr)
        print("This indicates a corrupt installation.", file=sys.stderr)
        return 1

    # Auto-create destination directory
    COMMAND_DEST_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Copy file (silent overwrite per CONTEXT.md decision)
    try:
        shutil.copy2(bundled_path, COMMAND_DEST_PATH)
    except PermissionError:
        print(f"Error: Permission denied writing to {COMMAND_DEST_PATH}", file=sys.stderr)
        print("Check file permissions and try again.", file=sys.stderr)
        return 1

    print(f"Installed to {COMMAND_DEST_PATH}")
    print("Restart Claude Code for commands to take effect.")
    return 0
```

### Anti-Patterns to Avoid

- **Installing to skills/ directory:** Skills are for extended capabilities,
  not slash commands. Use `~/.claude/commands/`
- **Creating v/ directory with individual files:** Creates `/init`, `/list`
  commands, not `/v init`, `/v list`. Use single `v.md`
- **Dynamic command generation:** Fragile and unnecessary. Bundle static v.md

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Resource access | Custom path resolution | importlib.resources | Handles wheels, editable installs, zip installs |
| CLI parsing | Manual argument handling | argparse | Already integrated, battle-tested |
| File copying | read_text/write_text | shutil.copy2 | Preserves metadata, atomic on same filesystem |

**Key insight:** This phase is intentionally minimal. The complexity is in the
v.md documentation file, not the installation code.

## Common Pitfalls

### Pitfall 1: Wrong Installation Directory

**What goes wrong:** Installing to `~/.claude/skills/v/` instead of
`~/.claude/commands/v.md`.

**Why it happens:** Historical confusion between "skills" and "commands".

**How to avoid:** Use `~/.claude/commands/v.md` as the target path.

**Warning signs:** `/v` command not recognized after installation.

### Pitfall 2: Forgetting Development Fallback

**What goes wrong:** `importlib.resources` works for installed packages but
fails during development with `pip install -e .`.

**Why it happens:** Different path resolution in editable mode.

**How to avoid:** Include fallback to `Path(__file__).parent / "commands" / "v.md"`.

**Warning signs:** FileNotFoundError when running CLI in development.

### Pitfall 3: Not Creating Parent Directory

**What goes wrong:** Copy fails because `~/.claude/commands/` doesn't exist.

**Why it happens:** Fresh Claude Code installation may not have this directory.

**How to avoid:** Always call `parent.mkdir(parents=True, exist_ok=True)`.

**Warning signs:** FileNotFoundError or PermissionError on copy.

## Code Examples

Verified patterns from existing codebase:

### CLI Command Pattern (from existing cli.py)

```python
def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for vibraphone CLI."""
    parser = argparse.ArgumentParser(
        prog="vibraphone-cli",
        description="Vibraphone CLI utilities",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # setup-commands subcommand (NEW)
    setup_parser = subparsers.add_parser(
        "setup-commands",
        help="Install /v slash commands to ~/.claude/commands/",
    )
    setup_parser.set_defaults(func=cmd_setup_commands)

    return parser


def main() -> int:
    """Main entry point for vibraphone CLI."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    if hasattr(args, "func"):
        return args.func(args)

    parser.print_help()
    return 0
```

### Resource Loading Pattern (from existing template_loader.py)

```python
def get_bundled_command_path() -> Path | None:
    """Get the path to the bundled v.md command file.

    Returns:
        Path to the bundled command file, or None if not found.
    """
    # Try importlib.resources first (works for installed packages)
    try:
        from importlib.resources import files

        command_file = files("vibraphone.commands").joinpath("v.md")
        if command_file.is_file():
            return Path(str(command_file))
    except (ImportError, TypeError):
        pass

    # Fallback: check relative to this file (development mode)
    dev_path = Path(__file__).parent / "commands" / "v.md"
    if dev_path.is_file():
        return dev_path

    return None
```

### Command File Format (v.md frontmatter)

```markdown
---
name: v
description: Vibraphone slash commands for MCP tool orchestration
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
...
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| skills/ directory | commands/ directory | 2026-02 | Proper slash command support |
| SKILL.md format | v.md with $ARGUMENTS | 2026-02 | Single file handles subcommands |
| vibraphone skill install | vibraphone setup-commands | 2026-02 | Clearer command naming |

**Deprecated/outdated:**
- `~/.claude/skills/v/` directory: Use `~/.claude/commands/v.md` instead
- `vibraphone skill install`: Use `vibraphone setup-commands` instead

## Open Questions

None. All questions resolved by CONTEXT.md decisions and architecture research.

## Sources

### Primary (HIGH confidence)

- Existing `/home/luke/workspace/github.com/lukemcguire/vibraphone/.planning/research/ARCHITECTURE.md`
  - Slash command architecture section researched 2026-02-18
- Existing `/home/luke/.claude/commands/` structure
  - Verified command file format in user's own setup
- Existing `/home/luke/workspace/github.com/lukemcguire/vibraphone/src/vibraphone/cli.py`
  - Current CLI implementation pattern
- Existing `/home/luke/workspace/github.com/lukemcguire/vibraphone/src/vibraphone/utils/template_loader.py`
  - importlib.resources usage pattern

### Secondary (MEDIUM confidence)

- Existing `/home/luke/workspace/github.com/lukemcguire/vibraphone/src/vibraphone/skills/v/SKILL.md`
  - Content to migrate to commands/v.md

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All standard library, patterns already in codebase
- Architecture: HIGH - Documented in existing ARCHITECTURE.md
- Pitfalls: HIGH - Known issues from previous implementation attempts

**Research date:** 2026-02-18
**Valid until:** 30 days (stable Python patterns, Claude Code slash commands stable)
