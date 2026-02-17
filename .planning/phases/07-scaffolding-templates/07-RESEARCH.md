# Phase 7: Scaffolding & Templates - Research

**Researched:** 2026-02-17
**Domain:** Project scaffolding via MCP tools with bundled templates using importlib.resources
**Confidence:** HIGH

## Summary

Phase 7 implements two MCP tools for scaffolding vibraphone into new or existing projects:

1. **init_project** — Generates vibraphone.yaml, AGENTS.md, CLAUDE.md, .planning/vibraphone/ governance docs, appends to Justfile and .gitignore. Uses auto-detection for project metadata (git remote, language, test framework) with user review before writing. Handles conflicts per-file with user confirmation.

2. **check_prerequisites** — Detects external dependencies (br, bv, git, just, node/npx) and reports install commands per-platform (macOS brew, Linux apt/brew, Windows scoop). Returns both structured list and ready-to-run shell script.

Templates are bundled in the Python wheel via importlib.resources and hatchling artifacts configuration. The implementation follows existing patterns: FastMCP @mcp.tool decorators, Pydantic models, two-phase preview/apply flow, TaskError for structured errors.

**Primary recommendation:** Create a `templates/` directory in the vibraphone package with Jinja2 templates for all files. Use importlib.resources.files() for template access. Implement auto-detection functions for project metadata. Follow the conflict handling flow from CONTEXT.md (per-file prompts, show diff, binary yes/no).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Conflict Handling

- **Prompt per file via agent** — tool returns conflict info, agent conveys to user, user decides
- **Binary options only** — Yes/No per file (no "skip all" or "yes to all")
- **Always show diff** — before asking to overwrite
- **Non-conflicting files** — write immediately while waiting for conflict resolution
- **No rollback needed** — each file decision is independent

#### Init Experience

- **Progress steps show results** — `Checking prerequisites... OK br, OK bv`
- **Celebratory success message** — ASCII art + congratulations + docs link
- **Fail fast on errors** — stop immediately, show clear error, suggest fix
- **Plain text output** — human-readable, no JSON structure needed for agent parsing

#### Prerequisites Reporting

- **Platform-aware install commands** — macOS (brew), Linux (apt/brew), Windows (scoop)
- **Core dependencies only** — br, bv, git (essential for vibraphone to function)
- **Output in both formats** — structured list `{tool, installed, install_command}` + ready-to-run shell script
- **Auto-check on init_project call** — warns if missing, also available on demand via check_prerequisites tool

#### Template Variables

- **Full scan auto-detection** — git remote URL, directory name, language, test framework, CI platform from existing files
- **Partial prompts fallback** — only prompt for values that couldn't be detected
- **Review first** — show all detected values, let user edit before writing files
- **Essentials only** — project name, worktrees_path, stack config (author, repo URL, CI prefs inferred)

### Claude's Discretion

- Exact ASCII art design for celebratory message
- Progress step phrasing/wording
- Which files constitute "governance docs" (follow existing template structure)
- Error message tone and detail level

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| NEW-01 | Agent can scaffold vibraphone into existing project via init_project | Two-phase preview/apply pattern, conflict detection, auto-detection for project metadata |
| NEW-02 | init_project generates vibraphone.yaml from template with project-specific values | Jinja2 templates, STACK_DEFAULTS, auto-detected project values |
| NEW-03 | init_project generates AGENTS.md and CLAUDE.md | Static templates from vibraphone-template repo |
| NEW-04 | init_project generates .planning/vibraphone/ governance docs | Static templates (CONSTITUTION.md, ARCHITECTURE.md, GLOSSARY.md, DECISIONS.md, prompts/reviewer.md, specs/_TEMPLATE.md) |
| NEW-05 | init_project appends Justfile recipes | Section-based append with markers |
| NEW-06 | init_project appends .gitignore entries | Append-only for .vibraphone/ and worktrees |
| NEW-07 | init_project does not overwrite existing files without explicit confirmation | Conflict detection, diff display, per-file yes/no prompts |
| NEW-08 | Agent can check for missing external dependencies via check_prerequisites | shutil.which() for detection, platform module for OS, install command mapping |
| NEW-09 | check_prerequisites detects br, bv, git, just, node/npx and reports install commands | Per-platform install commands (brew, apt, scoop) |

| TMPL-01 | Scaffolding template files bundled inside the Python package | hatchling artifacts config, src/vibraphone/templates/ directory |
| TMPL-02 | Templates accessed via importlib.resources | importlib.resources.files() with Traversable API |
| TMPL-03 | Templates match existing governance file formats from vibraphone-template | Direct copy from vibraphone-template repo with Jinja2 variable substitution |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastmcp | >=2.0 | MCP tool framework | Already in use, provides @mcp.tool decorator |
| pydantic | >=2.0 | Data validation and models | Already in use, TaskError pattern, config models |
| jinja2 | >=3.0 | Template rendering | Standard for Python templating, already a dependency |
| importlib.resources | (stdlib) | Access bundled package resources | Python 3.9+ standard, works with zip installs |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| shutil (stdlib) | - | which() for binary detection | check_prerequisites |
| platform (stdlib) | - | OS detection | Platform-specific install commands |
| pathlib (stdlib) | - | Path operations | All file handling |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| importlib.resources | pkg_resources | pkg_resources is deprecated, slower, doesn't work well with zip apps |
| Jinja2 templates | string.Template | Jinja2 provides conditionals, loops, includes for complex templates |
| shutil.which() | distutils.spawn.find_executable | distutils deprecated in Python 3.12 |

**Installation:**
```bash
# No new dependencies required - all are stdlib or already in pyproject.toml
# jinja2 is already pulled in by instructor dependency
```

## Architecture Patterns

### Recommended Project Structure
```
src/vibraphone/
├── templates/                     # NEW: Bundled template files
│   ├── vibraphone.yaml.j2        # Jinja2 template for config
│   ├── AGENTS.md                 # Static agent instructions
│   ├── CLAUDE.md                 # Static claude instructions
│   ├── gitignore_append.txt      # Entries to append to .gitignore
│   └── docs/                     # Governance doc templates
│       ├── CONSTITUTION.md
│       ├── ARCHITECTURE.md
│       ├── GLOSSARY.md
│       ├── DECISIONS.md
│       ├── prompts/
│       │   └── reviewer.md
│       └── specs/
│           └── _TEMPLATE.md
├── tools/
│   ├── scaffold_tools.py         # NEW: init_project, check_prerequisites
│   ├── bridge_tools.py           # EXISTING
│   ├── stack_tools.py            # EXISTING
│   └── ...
├── utils/
│   ├── template_loader.py        # NEW: importlib.resources wrapper
│   └── ...
└── config.py                     # EXTEND: Add VibraphoneTemplateConfig
```

### Pattern 1: Template Loading with importlib.resources
**What:** Load templates from bundled package resources
**When to use:** All template access in scaffold_tools.py
**Example:**
```python
# Source: Python 3.9+ docs - https://docs.python.org/3/library/importlib.resources.html
from importlib import resources
from pathlib import Path

def load_template(template_name: str) -> str:
    """Load a template file from the vibraphone.templates package.

    Uses importlib.resources for compatibility with zip installs.
    """
    template_files = resources.files("vibraphone.templates")
    template_path = template_files / template_name
    return template_path.read_text(encoding="utf-8")

def load_template_tree(target_dir: Path) -> dict[str, str]:
    """Load all templates from a subdirectory.

    Returns dict of relative_path -> content.
    """
    template_files = resources.files("vibraphone.templates")
    target = template_files / target_dir

    templates = {}
    for item in target.rglob("*"):
        if item.is_file():
            rel_path = item.relative_to(target)
            templates[str(rel_path)] = item.read_text(encoding="utf-8")
    return templates
```

### Pattern 2: Project Auto-Detection
**What:** Detect project metadata from existing files
**When to use:** init_project before template rendering
**Example:**
```python
# Source: Pattern from vibraphone-template structure analysis
import re
from pathlib import Path

def detect_git_remote(project_root: Path) -> str | None:
    """Extract remote URL from git config."""
    git_config = project_root / ".git" / "config"
    if not git_config.exists():
        return None

    content = git_config.read_text(encoding="utf-8")
    match = re.search(r'url\s*=\s*(.+)', content)
    if match:
        return match.group(1).strip()
    return None

def detect_language(project_root: Path) -> str:
    """Detect primary language from project files."""
    indicators = [
        ("pyproject.toml", "python"),
        ("setup.py", "python"),
        ("requirements.txt", "python"),
        ("package.json", "typescript"),
        ("Cargo.toml", "rust"),
        ("go.mod", "go"),
        ("Gemfile", "ruby"),
        ("build.gradle", "java"),
        ("pom.xml", "java"),
    ]
    for filename, language in indicators:
        if (project_root / filename).exists():
            return language
    return "python"  # Default

def detect_test_framework(project_root: Path, language: str) -> str:
    """Detect test framework from project structure."""
    if language == "python":
        if (project_root / "pyproject.toml").exists():
            content = (project_root / "pyproject.toml").read_text()
            if "pytest" in content:
                return "pytest"
        if (project_root / "pytest.ini").exists():
            return "pytest"
    elif language == "typescript":
        if (project_root / "vitest.config.ts").exists():
            return "vitest"
        if (project_root / "jest.config.js").exists():
            return "jest"
    return "unknown"

def detect_ci_platform(project_root: Path) -> str | None:
    """Detect CI platform from project structure."""
    if (project_root / ".github" / "workflows").exists():
        return "github-actions"
    if (project_root / ".gitlab-ci.yml").exists():
        return "gitlab-ci"
    if (project_root / ".circleci").exists():
        return "circleci"
    return None
```

### Pattern 3: Conflict Detection and Resolution
**What:** Check for existing files and handle conflicts per CONTEXT.md
**When to use:** init_project before writing each file
**Example:**
```python
# Source: CONTEXT.md conflict handling decisions
from pathlib import Path
from difflib import unified_diff

class ConflictInfo:
    """Information about a file conflict for agent to present to user."""
    def __init__(self, path: Path, existing: str, proposed: str):
        self.path = path
        self.existing = existing
        self.proposed = proposed
        self.diff = self._generate_diff()

    def _generate_diff(self) -> str:
        """Generate unified diff for agent to show user."""
        existing_lines = self.existing.splitlines(keepends=True)
        proposed_lines = self.proposed.splitlines(keepends=True)
        return "".join(unified_diff(
            existing_lines,
            proposed_lines,
            fromfile=f"{self.path} (existing)",
            tofile=f"{self.path} (proposed)",
        ))

async def init_project(
    project_path: Path,
    *,
    preview: bool = True,
    values: dict | None = None,
) -> dict:
    """Scaffold vibraphone into a project.

    Two-phase flow:
    - preview=True: returns detected values, proposed files, any conflicts
    - preview=False: writes non-conflicting files, returns conflicts for resolution

    Conflict handling:
    - Non-conflicting files written immediately
    - Conflicting files returned with diff for user decision
    - Each file decision is independent (no rollback needed)
    """
    # Auto-detect values
    detected = {
        "project_name": project_path.name,
        "git_remote": detect_git_remote(project_path),
        "language": detect_language(project_path),
        "test_framework": detect_test_framework(project_path, detect_language(project_path)),
        "ci_platform": detect_ci_platform(project_path),
    }

    # Merge with user-provided values
    final_values = {**detected, **(values or {})}

    # Check prerequisites first
    prereqs = check_prerequisites()
    missing_core = [p for p in prereqs["prerequisites"] if p["tool"] in ("br", "bv", "git") and not p["installed"]]
    if missing_core:
        return TaskError(
            error_type="MissingPrerequisites",
            message=f"Missing required tools: {', '.join(p['tool'] for p in missing_core)}",
            suggested_action=prereqs["shell_script"],
        )

    # Generate proposed files
    proposed_files = _render_templates(final_values)

    # Check for conflicts
    conflicts = []
    non_conflicting = {}

    for rel_path, content in proposed_files.items():
        full_path = project_path / rel_path
        if full_path.exists():
            existing = full_path.read_text(encoding="utf-8")
            if existing.strip() != content.strip():
                conflicts.append(ConflictInfo(full_path, existing, content))
        else:
            non_conflicting[rel_path] = content

    if preview:
        return {
            "status": "preview",
            "detected_values": detected,
            "final_values": final_values,
            "files_to_create": list(proposed_files.keys()),
            "conflicts": [{"path": str(c.path), "diff": c.diff} for c in conflicts],
            "prerequisites": prereqs,
            "next_steps": [
                "1. Review detected values and edit if needed",
                "2. Review conflicts and decide: overwrite (yes) or skip (no)",
                "3. Call init_project(..., preview=False, values=final_values) to proceed",
            ],
        }

    # Write non-conflicting files
    for rel_path, content in non_conflicting.items():
        full_path = project_path / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")

    return {
        "status": "partial" if conflicts else "complete",
        "files_written": list(non_conflicting.keys()),
        "conflicts": [{"path": str(c.path), "diff": c.diff} for c in conflicts],
        "next_steps": [
            "1. For each conflict, decide: overwrite (yes) or skip (no)",
            f"2. Call resolve_conflict(path, overwrite=True/False) for each",
        ] if conflicts else [
            "1. Project scaffolded successfully!",
            "2. Run 'just bootstrap' to initialize beads",
            "3. Run '/gsd:new-project' to start planning",
        ],
    }
```

### Pattern 4: Prerequisites Checking
**What:** Detect installed tools and provide install commands
**When to use:** init_project auto-check, standalone check_prerequisites tool
**Example:**
```python
# Source: CONTEXT.md prerequisites decisions
import platform
import shutil
from dataclasses import dataclass

@dataclass
class Prerequisite:
    tool: str
    installed: bool
    install_command: str

# Per-platform install commands
INSTALL_COMMANDS = {
    "br": {
        "Darwin": "brew install beads-rust  # or: cargo install beads_rust",
        "Linux": "cargo install beads_rust  # or build from source",
        "Windows": "cargo install beads_rust  # requires Rust toolchain",
    },
    "bv": {
        "Darwin": "brew install beads-viewer  # or: cargo install beads_viewer",
        "Linux": "cargo install beads_viewer",
        "Windows": "cargo install beads_viewer",
    },
    "git": {
        "Darwin": "brew install git",
        "Linux": "sudo apt install git  # or: brew install git",
        "Windows": "scoop install git",
    },
    "just": {
        "Darwin": "brew install just",
        "Linux": "sudo apt install just  # or: brew install just",
        "Windows": "scoop install just",
    },
    "node": {
        "Darwin": "brew install node",
        "Linux": "sudo apt install nodejs npm  # or: brew install node",
        "Windows": "scoop install nodejs",
    },
}

def check_prerequisites() -> dict:
    """Check for required external dependencies.

    Returns both structured list and ready-to-run shell script.
    Core dependencies: br, bv, git (essential for vibraphone to function).
    """
    system = platform.system()  # Darwin, Linux, Windows

    results = []
    install_commands = []

    for tool in ["br", "bv", "git", "just", "node"]:
        path = shutil.which(tool)
        installed = path is not None

        install_cmd = INSTALL_COMMANDS.get(tool, {}).get(system, f"# Install {tool} for your platform")
        results.append(Prerequisite(
            tool=tool,
            installed=installed,
            install_command=install_cmd if not installed else "",
        ))

        if not installed:
            install_commands.append(install_cmd)

    # Build shell script for missing tools
    shell_script = "#!/bin/bash\n# Install missing prerequisites\n\n"
    shell_script += "\n".join(install_commands) if install_commands else "# All prerequisites installed!"

    return {
        "platform": system,
        "prerequisites": [r.__dict__ for r in results],
        "all_installed": all(r.installed for r in results),
        "shell_script": shell_script,
        "missing_core": [r.tool for r in results if r.tool in ("br", "bv", "git") and not r.installed],
    }
```

### Pattern 5: Progress Output for Init Experience
**What:** Human-readable progress output per CONTEXT.md
**When to use:** init_project execution phase
**Example:**
```python
# Source: CONTEXT.md init experience decisions
import sys

def _progress(message: str, status: str = "OK") -> None:
    """Print progress step with status indicator."""
    # Status indicators
    indicators = {
        "OK": "\u2713",    # checkmark
        "FAIL": "\u2717",  # x mark
        "SKIP": "\u2192",  # arrow
    }
    indicator = indicators.get(status, status)
    print(f"{message}... {indicator}", file=sys.stderr)

def _celebration_message(project_name: str) -> str:
    """Generate celebratory success message with ASCII art."""
    return f"""
\u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510
\u2502  Vibraphone initialized!                    \u2502
\u2502                                            \u2502
\u2502  Project: {project_name:<30} \u2502
\u2502                                            \u2502
\u2502  Next steps:                                \u2502
\u2502  1. Run 'just bootstrap'                     \u2502
\u2502  2. Run '/gsd:new-project' to plan          \u2502
\u2502  3. Use MCP tools to execute tasks          \u2502
\u2502                                            \u2502
\u2502  Docs: https://github.com/lukemcguire/      \u2502
\u2502       vibraphone#readme                     \u2502
\u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518
"""
```

### Anti-Patterns to Avoid
- **Overwriting without confirmation:** Always check if file exists and show diff
- **Silent failures on missing prerequisites:** Fail fast with clear error
- **Full file regeneration for append targets:** Use append for .gitignore, section markers for Justfile
- **Ignoring partial template state:** Track which files were written for conflict resolution
- **Platform assumptions:** Always detect OS and provide appropriate install commands

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Template loading | __file__-relative paths | importlib.resources | Works with zip installs, namespace packages |
| Binary detection | Custom PATH parsing | shutil.which() | Handles PATH, symlinks, Windows PATHEXT |
| OS detection | sys.platform parsing | platform.system() | Returns consistent Darwin/Linux/Windows |
| File diffs | Manual comparison | difflib.unified_diff | Standard format, handles encoding |
| Template rendering | string.format() | Jinja2 | Conditionals, loops, includes |

**Key insight:** The vibraphone-template repo provides the template source material. The task is packaging those templates with importlib.resources and adding variable substitution for project-specific values.

## Common Pitfalls

### Pitfall 1: Template Files Not Included in Wheel
**What goes wrong:** Templates directory exists in source but not in installed wheel
**Why it happens:** hatchling only includes Python files by default
**How to avoid:** Add `artifacts = ["templates/"]` to `[tool.hatch.build.targets.wheel]` in pyproject.toml
**Warning signs:** FileNotFoundError when loading templates after pip install

### Pitfall 2: Missing Jinja2 Dependency
**What goes wrong:** ImportError when rendering templates
**Why it happens:** jinja2 is pulled in by instructor but may not be explicit
**How to avoid:** Add `jinja2>=3.0` to dependencies in pyproject.toml
**Warning signs:** ImportError for jinja2

### Pitfall 3: Incorrect Conflict Diff Format
**What goes wrong:** Diffs are unreadable or don't show actual changes
**Why it happens:** Not using unified_diff correctly, missing newlines
**How to avoid:** Use `keepends=True` when splitting, include fromfile/tofile headers
**Warning signs:** User confusion about what changed

### Pitfall 4: Platform Detection Edge Cases
**What goes wrong:** Wrong install commands shown for WSL or unusual setups
**Why it happens:** platform.system() returns "Linux" for WSL
**How to avoid:** Document WSL as Linux, consider WSL detection for better UX (optional)
**Warning signs:** Windows users on WSL get apt commands (which actually work)

### Pitfall 5: Partial Write Failure
**What goes wrong:** Some files written, then error occurs, inconsistent state
**Why it happens:** Error during iteration, disk full, permissions
**How to avoid:** Write non-conflicting files first, return clear status with files_written list
**Warning signs:** User reports missing files after init_project

## Code Examples

### pyproject.toml Updates for Template Bundling
```toml
# Add to existing pyproject.toml

[tool.hatch.build.targets.wheel]
# Include templates directory in wheel
artifacts = ["src/vibraphone/templates/"]

# Or use shared-data for data_files approach (less recommended)
# [tool.hatch.build.targets.wheel.shared-data]
# "templates" = "src/vibraphone/templates"
```

### Template File Structure
```
src/vibraphone/templates/
├── vibraphone.yaml.j2         # Jinja2 with {{ project_name }}, {{ language }}, etc.
├── AGENTS.md                  # Static - copy from vibraphone-template
├── CLAUDE.md                  # Static - copy from vibraphone-template
├── gitignore_append.txt       # Just the vibraphone-specific entries
└── docs/
    ├── CONSTITUTION.md.j2     # Jinja2 with language-specific rules
    ├── ARCHITECTURE.md        # Static template (empty placeholder)
    ├── GLOSSARY.md            # Static - copy from vibraphone-template
    ├── DECISIONS.md.j2        # Jinja2 with initial ADR
    ├── prompts/
    │   └── reviewer.md        # Static - copy from vibraphone-template
    └── specs/
        └── _TEMPLATE.md       # Static - copy from vibraphone-template
```

### vibraphone.yaml.j2 Template
```yaml
# Generated by vibraphone init_project
# https://github.com/lukemcguire/vibraphone

project:
  name: {{ project_name }}
  version: 0.1.0

components:
{% if component_name %}
  {{ component_name }}:
    language: {{ language }}
    root: {{ component_root | default("./") }}
    test_command: {{ test_command }}
    lint_command: {{ lint_command }}
    format_command: {{ format_command }}
    coverage_threshold: 80
{% endif %}

quality_gate:
  require_tests: true
  require_lint: true
  require_review: true
  review_severity_threshold: error
  max_test_attempts: 10
  max_review_attempts: 5

worktree:
  base_branch: main
  prefix: feat/
  auto_cleanup: false

review:
  model: {{ review_model | default("anthropic/claude-3-sonnet") }}
  prompt_file: ./docs/prompts/reviewer.md
  constitution_file: ./docs/CONSTITUTION.md

beads:
  use_bv: false
  auto_sync: true

stitch:
  enabled: false
  project_id: ${STITCH_PROJECT_ID}
```

### CONSTITUTION.md.j2 Template (Language-Specific Rules)
```markdown
# CONSTITUTION.md — Project Law

The immutable rules the code reviewer checks against. Each rule has a
machine-readable ID that the reviewer references in its JSON output.

---

## Naming Conventions

### `snake-case-files`

All file names use snake_case{% if language == "go" %}, following Go convention. No camelCase, PascalCase, or kebab-case in file names{% elif language == "python" %}, following PEP 8. No camelCase or kebab-case in file names{% else %}{% endif %}.

{% if language == "python" %}
### `descriptive-names`

Variables, functions, and types must have descriptive names. No single-letter variables except loop counters (`i`, `j`, `k`). Use snake_case for functions/variables, PascalCase for classes.
{% elif language == "go" %}
### `descriptive-names`

Variables, functions, and types must have descriptive names. No single-letter variables except loop counters (`i`, `j`, `k`) and receiver names. Exported names use PascalCase, unexported use camelCase, per Go convention.
{% elif language == "typescript" %}
### `descriptive-names`

Variables, functions, and types must have descriptive names. No single-letter variables except loop counters (`i`, `j`, `k`). Use camelCase for functions/variables, PascalCase for classes/types/interfaces.
{% endif %}

---

## Architectural Boundaries

### `single-responsibility`

Each module, function, or class should have a single responsibility. If a function does two things, split it.

{% if language == "python" %}
### `no-circular-imports`

Python modules must not form import cycles. Structure packages so dependencies flow in one direction.
{% elif language == "go" %}
### `no-circular-imports`

Go packages must not form import cycles. Structure packages so dependencies flow in one direction.
{% endif %}

---

## Forbidden Patterns

### `no-hardcoded-secrets`

No secrets, API keys, passwords, or tokens hardcoded in source files. All secrets must come from environment variables.

{% if language == "go" %}
### `no-naked-goroutines`

Goroutines must have proper error handling and lifecycle management. Use `errgroup`, context cancellation, or similar patterns. No fire-and-forget goroutines without recovery.

### `no-init-functions`

Avoid `init()` functions. Use explicit initialization so dependencies and side effects are visible at the call site.

### `no-panic-in-library-code`

Library packages must not call `panic()`. Return errors and let the caller decide how to handle them. `main` and test code may panic.
{% endif %}

---

## Required Patterns

{% if language == "python" %}
### `require-type-hints`

All public functions must have type hints for parameters and return values.

### `require-docstrings`

All public modules, classes, and functions must have docstrings following Google style.
{% elif language == "go" %}
### `require-error-wrapping`

Wrap errors with context using `fmt.Errorf("context: %w", err)`. Do not discard or swallow errors silently.

### `require-doc-comments`

All exported functions, types, and package declarations must have doc comments following Go convention (`// FunctionName does...`).

### `require-error-handling`

All external calls (HTTP, file I/O, subprocess) must have explicit error handling. No ignored error return values.
{% elif language == "typescript" %}
### `require-return-types`

All public functions must have explicit return type annotations.

### `require-jsdoc`

All exported functions and classes must have JSDoc comments.
{% endif %}

---

## Test Requirements

### `require-tests-for-public-functions`

Every exported function must have at least one test.

### `require-test-before-code`

Follow TDD: write a failing test before writing the implementation.

### `no-skipped-tests`

{% if language == "python" %}
No `@pytest.skip()` or `pytest.mark.skip` in committed test files without an accompanying issue ID explaining why.
{% elif language == "go" %}
No `t.Skip()` in committed test files without an accompanying issue ID explaining why.
{% elif language == "typescript" %}
No `.skip()` or `.only()` on test cases without an accompanying issue ID explaining why.
{% endif %}

---

## Security Checklist

### `no-secrets-in-code`

No secrets, credentials, or API keys in source code. Use `.env` and environment variables.

---

## Diagram Requirements

### `require-diagram-update`

New packages, services, or significant architectural changes must include updated Mermaid diagrams in `docs/ARCHITECTURE.md`.

### `diagram-matches-code`

Mermaid diagrams in ARCHITECTURE.md must accurately reflect the current codebase. Stale diagrams are treated as warnings.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Static templates in repo | Bundled in wheel via importlib.resources | Phase 7 design | Works with pip install, no external files needed |
| Manual project setup | init_project tool with auto-detection | Phase 7 design | Consistent setup, fewer errors |
| Generic error messages | Platform-aware install commands | Phase 7 design | Users get actionable commands |
| Full file overwrite | Per-file conflict prompts with diffs | Phase 7 design | Safer, user always sees changes |

**Deprecated/outdated:**
- __file__-relative paths for templates: Use importlib.resources for wheel compatibility
- Generic "install X" messages: Provide platform-specific commands

## Open Questions

1. **Constitution Language Rules**
   - What we know: CONSTITUTION.md should have language-specific rules
   - What's unclear: How many languages to support initially
   - Recommendation: Start with python, typescript, go (matching STACK_DEFAULTS). Add rust, ruby, java templates as needed.

2. **ASCII Art Design**
   - What we know: CONTEXT.md asks for celebratory ASCII art
   - What's unclear: Exact design
   - Recommendation: Use simple box drawing characters as shown in Pattern 5. Keep it readable across terminals.

3. **Justfile Append vs Section Update**
   - What we know: configure_stack uses section markers
   - What's unclear: Should init_project append or use section markers
   - Recommendation: Append for init_project (file may not exist), section update for configure_stack (file exists with content).

4. **Worktrees Path Default**
   - What we know: Default is ~/.vibraphone/worktrees
   - What's unclear: Should init_project prompt for custom path
   - Recommendation: Use default, let user edit vibraphone.yaml if they want custom path. Don't add to prompt flow.

## Sources

### Primary (HIGH confidence)
- `/home/luke/workspace/github.com/lukemcguire/vibraphone-template/` - Template source files to bundle
- `https://docs.python.org/3/library/importlib.resources.html` - Official importlib.resources API
- `https://hatch.pypa.io/latest/config/build/` - Hatchling build configuration for artifacts
- `src/vibraphone/tools/stack_tools.py` - Existing template rendering pattern with Jinja2

### Secondary (MEDIUM confidence)
- `src/vibraphone/config.py` - Existing STACK_DEFAULTS, config structure
- `src/vibraphone/utils/cli_runner.py` - Async subprocess pattern
- `src/vibraphone/tools/bridge_tools.py` - Two-phase preview/apply pattern

### Tertiary (LOW confidence)
- None - all critical information from verified codebase and official docs

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - importlib.resources well-documented, Jinja2 already used
- Architecture: HIGH - template structure from vibraphone-template, patterns from existing tools
- Pitfalls: HIGH - common packaging issues documented in hatchling docs

**Research date:** 2026-02-17
**Valid until:** 30 days (Python stdlib stable, hatchling patterns stable)
