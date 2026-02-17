# Phase 6: Bridge & Stack Tools - Research

**Researched:** 2026-02-16
**Domain:** Integration layer connecting GSD planning to beads_rust task management and Justfile build configuration
**Confidence:** HIGH

## Summary

Phase 6 implements two MCP tools that bridge the vibraphone MCP server to external systems:

1. **import_gsd_plan** — Parses GSD PLAN.md files (YAML frontmatter + XML `<tasks>` blocks) and creates beads issues with dependencies. This is a migration from the existing `bridge_tools.py` in vibraphone-template with key modifications to dependency handling per user decisions.

2. **configure_stack** — Generates Justfile recipes and vibraphone.yaml from component definitions. This is a migration from `stack_tools.py` with support for section-based updates rather than full file regeneration.

The implementation leverages existing patterns from the codebase: FastMCP @mcp.tool decorators, Pydantic models, async subprocess execution via `asyncio.create_subprocess_exec` (via `cli_runner.py`), two-phase preview pattern, and TaskError for structured errors.

**Primary recommendation:** Migrate the existing implementation from vibraphone-template with modifications per CONTEXT.md decisions. Add `defusedxml` dependency for safe XML parsing. Extend the existing `config.py` to support component definitions and STACK_DEFAULTS for additional languages (rust, ruby, java).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Import Behavior

- **Idempotency**: Skip if `plan:<id>` label already exists in beads — write-once model
- **Plan updates**: If tasks need changes after import, edit beads directly (complete_task, abandon_task, manual edit)
- **Re-import purpose**: Error recovery only (e.g., API failed mid-import), not plan evolution
- **No tasks in plan**: Warn and skip that plan, continue with others
- **Multi-plan import**: Import all plans in a phase at once (current behavior)

#### Dependency Mapping

- **Intra-plan deps**: Explicit only via optional `<blocked_by>` XML field inside `<task>` elements
  - No implicit sequential deps (tasks are parallel by default)
  - If ordering needed, plan author adds `<blocked_by>task-name</blocked_by>`
- **Inter-plan deps**: First task of dependent plan blocked by last task of dependency plan
  - Uses GSD frontmatter `depends_on: ["01-01"]` as currently
  - Convention: last task in a plan represents "plan complete"
- **Missing deps**: Not a concern — all plans imported together, references resolve
- **Cycles**: Let beads_rust reject invalid deps (no cycle detection in vibraphone)

#### Stack Scope

- **Generated from components**: Quality gate recipes (test, lint, format per component)
- **Static (base template from init_project)**: Worktree ops, Beads helpers, Setup/debug recipes
- **configure_stack behavior**: Section update only — insert/update component recipes, don't regenerate full Justfile
- **STACK_DEFAULTS languages**: python, typescript, go (current) + add rust, ruby, java
- **Stitch integration**: Keep Stitch support — will be used after migration

#### Safety & Recovery

- **Two-phase flow**: `preview=True` by default (returns proposals), `preview=False` to write
- **Validation**: Fail-fast — validate all plan files before creating any beads tasks
- **Rollback**: No automatic rollback on partial failure
  - Report what succeeded/failed clearly
  - Rely on idempotency for recovery (re-import skips existing)
- **Error handling**: Clear error messages with suggested actions

### Claude's Discretion

- Exact format of `<blocked_by>` XML field (single task ref vs list)
- How to structure base Justfile template for init_project
- Exact validation checks for plan structure
- Error message wording and format

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| BRDG-01 | Agent can import GSD plan as beads tasks with dependencies (import_gsd_plan) | XML parsing with defusedxml, YAML frontmatter extraction, br CLI integration via cli_runner.py, idempotency via label checking, dependency wiring pattern |
| STACK-01 | Agent can reconfigure stack components and regenerate Justfile recipes (configure_stack) | Justfile template rendering, vibraphone.yaml section update, STACK_DEFAULTS per language, two-phase preview pattern |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastmcp | >=2.0 | MCP tool framework | Already in use, provides @mcp.tool decorator |
| pydantic | >=2.0 | Data validation and models | Already in use, TaskError pattern, config models |
| pyyaml | >=6.0 | YAML parsing for frontmatter | Already in use, config loading |
| defusedxml | >=0.7.1 | Safe XML parsing for GSD task blocks | Security-focused, prevents XXE attacks, already used in template |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| re (stdlib) | - | Regex for frontmatter/task extraction | Parsing PLAN.md files |
| asyncio (stdlib) | - | Async subprocess execution | All br CLI calls via cli_runner.py |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| defusedxml | xml.etree.ElementTree | defusedxml prevents XXE attacks, safer for untrusted input |
| Custom XML parsing | BeautifulSoup | Overkill for simple task blocks, adds dependency |
| Full Justfile regeneration | Section-based update | Section update preserves manual customizations (locked decision) |

**Installation:**
```bash
uv add defusedxml
```

## Architecture Patterns

### Recommended Project Structure
```
src/vibraphone/
├── tools/
│   ├── bridge_tools.py       # NEW: import_gsd_plan tool
│   ├── stack_tools.py        # NEW: configure_stack tool
│   ├── task_tools.py         # EXISTING: br CLI integration
│   ├── quality_gate_tools.py # EXISTING: quality enforcement
│   └── worktree_tools.py     # EXISTING: worktree ops
├── utils/
│   ├── cli_runner.py         # EXISTING: async br/bv execution
│   ├── errors.py             # EXISTING: TaskError model
│   ├── session.py            # EXISTING: session persistence
│   └── plan_parser.py        # NEW: GSD plan parsing utilities
└── config.py                 # EXTEND: Add component config, STACK_DEFAULTS
```

### Pattern 1: GSD Plan Parsing
**What:** Extract YAML frontmatter and XML task blocks from PLAN.md files
**When to use:** import_gsd_plan parsing phase
**Example:**
```python
# Source: Existing bridge_tools.py pattern
import re
import yaml
from defusedxml.ElementTree import fromstring as parse_xml

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_TASKS_RE = re.compile(r"<tasks>(.*?)</tasks>", re.DOTALL)

def _extract_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from between --- fences."""
    match = _FRONTMATTER_RE.match(content)
    if not match:
        return {}
    return yaml.safe_load(match.group(1)) or {}

def _extract_tasks_from_xml(body: str) -> list[dict]:
    """Find <tasks>...</tasks> block and parse each <task> element."""
    match = _TASKS_RE.search(body)
    if not match:
        return []

    # Sanitize XML content (escape bare & and < not part of known tags)
    inner = _sanitize_xml_content(match.group(1))
    xml_str = f"<tasks>{inner}</tasks>"
    root = parse_xml(xml_str)

    tasks = []
    for task_el in root.findall("task"):
        task_data = {}
        for child in task_el:
            task_data[child.tag] = (child.text or "").strip()
        tasks.append(task_data)
    return tasks
```

### Pattern 2: Beads CLI Integration
**What:** Use existing cli_runner.py for br commands
**When to use:** Creating tasks, checking labels, adding dependencies
**Example:**
```python
# Source: Existing cli_runner.py and task_tools.py patterns
from vibraphone.utils.cli_runner import run_cli

async def _create_beads_task(plan_id: str, task_idx: int, task_data: dict) -> str:
    """Create a single Beads issue from a parsed task element."""
    title_text = task_data.get("title", f"Task {task_idx + 1}")
    title = f"[{plan_id}] {title_text}"
    description = task_data.get("description", "")
    labels = task_data.get("labels", f"plan:{plan_id}")
    type_ = task_data.get("type", "task")

    # Build br create arguments
    args = ["create", title, "--json"]
    if description:
        args.extend(["--description", description])
    if type_:
        args.extend(["--type", type_])
    if labels:
        args.extend(["--labels", labels])

    result = await run_cli("br", *args, cwd=get_project_root())
    return str(result.get("id", ""))

async def _existing_plan_ids() -> set[str]:
    """Return plan IDs that already have Beads tasks (for idempotency)."""
    result = await run_cli("br", "list", "--json", cwd=get_project_root())
    items = result.get("items", [])
    ids = set()
    for item in items:
        for label in item.get("labels", []):
            if isinstance(label, str) and label.startswith("plan:"):
                ids.add(label.removeprefix("plan:"))
    return ids
```

### Pattern 3: Dependency Wiring
**What:** Wire up intra-plan and inter-plan dependencies
**When to use:** After all tasks created, before sync
**Example:**
```python
# Source: Existing bridge_tools.py pattern (modified per CONTEXT.md)
async def _setup_plan_dependencies(
    plan_tasks: dict[str, list[str]],  # plan_id -> list of beads issue IDs
    plan_deps: dict[str, list[str]],   # plan_id -> list of depends_on plan IDs
    task_blocked_by: dict[str, str],   # task_name -> blocker_task_name (from XML)
) -> list[dict]:
    """Wire up intra-plan and inter-plan dependencies.

    Per CONTEXT.md:
    - Intra-plan: explicit only via <blocked_by> XML field
    - Inter-plan: first task of dependent blocked by last task of dependency
    """
    deps_created = []

    for plan_id, task_ids in plan_tasks.items():
        # Intra-plan deps: only if <blocked_by> specified
        # This is Claude's discretion - format: single task name reference
        for i, task_id in enumerate(task_ids):
            task_name = task_names_by_id.get(task_id)
            if task_name in task_blocked_by:
                blocker_name = task_blocked_by[task_name]
                blocker_id = task_ids_by_name.get(blocker_name)
                if blocker_id:
                    await run_cli("br", "dep", "add", task_id, blocker_id,
                                  "--type", "blocks", cwd=get_project_root())
                    deps_created.append({
                        "blocked": task_id, "blocker": blocker_id,
                        "type": "intra-plan"
                    })

        # Inter-plan deps: first task blocked by last task of each dep plan
        if plan_id in plan_deps and task_ids:
            first_task = task_ids[0]
            for dep_plan_id in plan_deps[plan_id]:
                dep_task_ids = plan_tasks.get(dep_plan_id, [])
                if dep_task_ids:
                    last_dep_task = dep_task_ids[-1]
                    await run_cli("br", "dep", "add", first_task, last_dep_task,
                                  "--type", "blocks", cwd=get_project_root())
                    deps_created.append({
                        "blocked": first_task, "blocker": last_dep_task,
                        "type": "inter-plan"
                    })

    return deps_created
```

### Pattern 4: Two-Phase Preview Pattern
**What:** Return proposals on preview=True, write on preview=False
**When to use:** Both import_gsd_plan and configure_stack
**Example:**
```python
# Source: Existing configure_stack pattern from stack_tools.py
async def configure_stack(
    components: dict[str, dict[str, Any]],
    *,
    preview: bool = True,
) -> dict:
    """Generate per-component Justfile recipes and vibraphone.yaml config.

    Two-phase flow:
    - preview=True: returns proposed file contents for agent to present to user
    - preview=False: writes files, reloads config, returns confirmation
    """
    justfile_content = _render_justfile(components)
    yaml_content = _render_vibraphone_yaml(components, existing_config)

    if preview:
        return {
            "status": "preview",
            "justfile": justfile_content,
            "vibraphone_yaml": yaml_content,
            "next_steps": [
                "1. Review the proposed changes",
                "2. Call configure_stack(..., preview=False) to apply",
            ],
        }

    # Write files
    justfile_path.write_text(justfile_content)
    yaml_path.write_text(yaml_content)
    reload_config()

    return {
        "status": "configured",
        "justfile_path": str(justfile_path),
        "vibraphone_yaml_path": str(yaml_path),
        "components": list(components.keys()),
    }
```

### Pattern 5: Justfile Section Rendering
**What:** Render per-component recipes for insertion into Justfile
**When to use:** configure_stack when generating quality gate recipes
**Example:**
```python
# Source: Existing stack_tools.py pattern
STACK_DEFAULTS: dict[str, dict[str, str]] = {
    "python": {
        "test_command": "uv run pytest --tb=short",
        "lint_command": "uv run ruff check . && uv run ruff format --check .",
        "format_command": "uv run ruff check --fix . && uv run ruff format .",
    },
    "typescript": {
        "test_command": "npx vitest run",
        "lint_command": "npx eslint .",
        "format_command": "npx eslint --fix . && npx prettier --write .",
    },
    "go": {
        "test_command": "go test ./...",
        "lint_command": "golangci-lint run",
        "format_command": "gofmt -w .",
    },
    # NEW per CONTEXT.md:
    "rust": {
        "test_command": "cargo test",
        "lint_command": "cargo clippy -- -D warnings",
        "format_command": "cargo fmt",
    },
    "ruby": {
        "test_command": "bundle exec rspec",
        "lint_command": "bundle exec rubocop",
        "format_command": "bundle exec rubocop -a",
    },
    "java": {
        "test_command": "./gradlew test",
        "lint_command": "./gradlew checkstyleMain",
        "format_command": "./gradlew spotlessApply",
    },
}

def _render_component_recipes(name: str, root: str, commands: dict[str, str]) -> str:
    """Render per-component Justfile recipes (marked [private])."""
    lines = []

    lines.append(f"# Run {name} tests")
    lines.append("[private]")
    lines.append(f"test-{name} *ARGS:")
    lines.append(f"    cd {root} && {commands['test_command']} {{ARGS}}")
    lines.append("")

    lines.append(f"# Run {name} linter")
    lines.append("[private]")
    lines.append(f"lint-{name}:")
    lines.append(f"    cd {root} && {commands['lint_command']}")
    lines.append("")

    lines.append(f"# Run {name} formatter")
    lines.append("[private]")
    lines.append(f"format-{name}:")
    lines.append(f"    cd {root} && {commands['format_command']}")

    return "\n".join(lines)
```

### Anti-Patterns to Avoid
- **Implicit sequential dependencies:** Don't assume task N+1 depends on task N — use explicit `<blocked_by>` only
- **Full Justfile regeneration:** Use section update to preserve manual customizations
- **Missing idempotency check:** Always check for existing `plan:<id>` labels before creating tasks
- **Blocking subprocess calls:** Never use `subprocess.run()` — use existing `run_cli` via cli_runner.py
- **Cycle detection in vibraphone:** Let beads_rust handle cycle detection — don't duplicate

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| XML parsing | xml.etree.ElementTree directly | defusedxml.ElementTree | Prevents XXE attacks on untrusted plan files |
| br CLI execution | subprocess.run (blocking) | cli_runner.run_cli | Async, consistent error handling, JSON parsing |
| Error responses | Plain dicts with error strings | TaskError model | Consistent structure with error_type, message, suggested_action |
| YAML parsing | Custom YAML parser | pyyaml.safe_load | Standard, handles edge cases |
| Config reload | Manual file read + parse | reload_config() | Ensures singleton cache is updated |

**Key insight:** The existing codebase provides all the infrastructure needed (cli_runner, TaskError, config management). The migration is primarily adapting the template's bridge_tools.py and stack_tools.py to use these existing patterns.

## Common Pitfalls

### Pitfall 1: Missing defusedxml Dependency
**What goes wrong:** XML parsing fails with ImportError
**Why it happens:** defusedxml not in pyproject.toml dependencies
**How to avoid:** Add `defusedxml>=0.7.1` to dependencies before implementing
**Warning signs:** ImportError when importing bridge_tools

### Pitfall 2: Implicit Sequential Dependencies
**What goes wrong:** Tasks are incorrectly blocked by preceding task
**Why it happens:** Old code assumed sequential execution (task N+1 blocked by task N)
**How to avoid:** Remove implicit sequential logic — only use explicit `<blocked_by>` for intra-plan deps
**Warning signs:** Tasks blocked that shouldn't be, parallel tasks running sequentially

### Pitfall 3: Plan Import Creates Duplicates
**What goes wrong:** Running import_gsd_plan twice creates duplicate tasks
**Why it happens:** Not checking for existing `plan:<id>` labels before creating
**How to avoid:** Call `_existing_plan_ids()` at start, skip plans with existing labels
**Warning signs:** Duplicate tasks with same plan ID prefix

### Pitfall 4: Justfile Section Update Destroys Customizations
**What goes wrong:** Manual additions to Justfile are lost after configure_stack
**Why it happens:** Full file regeneration instead of section update
**How to avoid:** Use marker comments (e.g., `# BEGIN COMPONENT RECIPES`) for section replacement
**Warning signs:** User reports lost custom recipes after running configure_stack

### Pitfall 5: Missing Validation Before Creation
**What goes wrong:** Half of plans imported before invalid plan detected, partial state left
**Why it happens:** Creating tasks while iterating instead of validate-then-create
**How to avoid:** Two-pass: validate all plan files first, then create all tasks
**Warning signs:** Inconsistent state after import failure

## Code Examples

Verified patterns from migration source and existing codebase:

### GSD Plan File Format
```markdown
---
phase: 05-quality-gate-tools
plan: 01
type: execute
wave: 1
depends_on: ["04-01"]
---

<objective>
Create the foundational utilities...
</objective>

<tasks>

<task type="auto">
  <name>Task 1: Create command_runner.py</name>
  <files>src/vibraphone/utils/command_runner.py</files>
  <action>
  Create async command runner...
  </action>
  <verify>python -c "from vibraphone.utils.command_runner import run_command"</verify>
  <done>run_command function exists</done>
</task>

<task type="auto">
  <name>Task 2: Create circuit_breaker.py</name>
  <files>src/vibraphone/utils/circuit_breaker.py</files>
  <blocked_by>Task 1: Create command_runner.py</blocked_by>  <!-- OPTIONAL -->
  <action>
  Create CircuitBreaker class...
  </action>
</task>

</tasks>
```

### import_gsd_plan Tool Implementation
```python
# Source: Migration from bridge_tools.py with CONTEXT.md modifications
from pathlib import Path
from vibraphone.config import get_project_root
from vibraphone.utils.cli_runner import run_cli

_PLAN_FILE_RE = re.compile(r"^(\d+-\d+)-PLAN\.md$")

async def import_gsd_plan(phase_number: int, *, preview: bool = True) -> dict:
    """Import all GSD PLAN.md files for a phase into Beads tasks.

    Two-phase flow:
    - preview=True: returns what would be imported without creating tasks
    - preview=False: creates tasks, wires dependencies, syncs

    Idempotent: plans with existing `plan:<id>` labels are skipped.
    """
    phase_dir = _resolve_phase_dir(phase_number)
    if phase_dir is None:
        return {"error": f"Phase directory not found for phase {phase_number}"}

    # Discover plan files
    plan_files = [
        (match.group(1), path)
        for path in sorted(phase_dir.iterdir())
        if (match := _PLAN_FILE_RE.match(path.name))
    ]

    if not plan_files:
        return {"error": f"No PLAN.md files found in {phase_dir}"}

    # Idempotency check
    existing = await _existing_plan_ids()
    skipped = [pid for pid, _ in plan_files if pid in existing]
    plan_files = [(pid, p) for pid, p in plan_files if pid not in existing]

    if not plan_files:
        return {
            "already_imported": True,
            "skipped_plans": skipped,
            "message": f"All plans for phase {phase_number} already imported.",
        }

    if preview:
        # Return preview of what would be imported
        preview_data = []
        for plan_id, plan_path in plan_files:
            content = plan_path.read_text()
            frontmatter = _extract_frontmatter(content)
            tasks = _extract_tasks_from_xml(content)
            preview_data.append({
                "plan_id": plan_id,
                "depends_on": frontmatter.get("depends_on", []),
                "task_count": len(tasks),
                "task_titles": [t.get("title", f"Task {i}") for i, t in enumerate(tasks)],
            })
        return {
            "status": "preview",
            "plans": preview_data,
            "skipped_plans": skipped,
            "next_steps": [
                "1. Review the plans to be imported",
                "2. Call import_gsd_plan(phase_number, preview=False) to create tasks",
            ],
        }

    # Validate all plans first (fail-fast)
    for plan_id, plan_path in plan_files:
        content = plan_path.read_text()
        tasks = _extract_tasks_from_xml(content)
        if not tasks:
            return {
                "error": f"Plan {plan_id} has no tasks",
                "suggested_action": "Add <tasks> block to the plan or remove the file",
            }

    # Create tasks
    plan_tasks, plan_deps, tasks_created, task_blocked_by = await _parse_and_create_tasks(plan_files)

    # Wire dependencies
    dependencies = await _setup_plan_dependencies(plan_tasks, plan_deps, task_blocked_by)

    # Sync
    await run_cli("br", "sync", "--flush-only", cwd=get_project_root())

    return {
        "tasks_created": tasks_created,
        "dependencies": dependencies,
        "skipped_plans": skipped,
        "next_steps": ["1. next_ready() to get the first task to work on"],
    }
```

### configure_stack Tool Implementation
```python
# Source: Migration from stack_tools.py
import yaml
from vibraphone.config import get_project_root, get_config, clear_config_cache

async def configure_stack(
    components: dict[str, dict[str, Any]],
    *,
    preview: bool = True,
    stitch_project_id: str | None = None,
) -> dict:
    """Generate per-component Justfile recipes and vibraphone.yaml config.

    Two-phase flow:
    - preview=True: returns proposed file contents
    - preview=False: writes files, reloads config
    """
    project_root = get_project_root()

    # Read existing config
    config_path = project_root / "vibraphone.yaml"
    existing_config = {}
    if config_path.exists():
        with config_path.open() as f:
            existing_config = yaml.safe_load(f) or {}

    justfile_content = _render_justfile(components)
    yaml_content = _render_vibraphone_yaml(components, existing_config)

    if preview:
        result = {
            "status": "preview",
            "justfile": justfile_content,
            "vibraphone_yaml": yaml_content,
            "components": list(components.keys()),
            "next_steps": [
                "1. Review the proposed Justfile and vibraphone.yaml",
                "2. Call configure_stack(..., preview=False) to apply",
            ],
        }
        if stitch_project_id:
            result["stitch_note"] = f"Will enable stitch with project ID {stitch_project_id}"
        return result

    # Write files
    justfile_path = project_root / "Justfile"
    justfile_path.write_text(justfile_content)

    yaml_path = project_root / "vibraphone.yaml"
    yaml_path.write_text(yaml_content)

    # Handle stitch if provided
    if stitch_project_id:
        _update_env_var("STITCH_PROJECT_ID", stitch_project_id, project_root)

    # Reload config singleton
    clear_config_cache()

    return {
        "status": "configured",
        "justfile_path": str(justfile_path),
        "vibraphone_yaml_path": str(yaml_path),
        "components": list(components.keys()),
        "next_steps": ["1. import_gsd_plan(phase_number) to import phase tasks"],
    }
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Implicit sequential deps | Explicit `<blocked_by>` only | Phase 6 design | Tasks parallel by default, clearer intent |
| Full Justfile regeneration | Section update | Phase 6 design | Preserves manual customizations |
| subprocess.run (blocking) | asyncio.create_subprocess_exec | Phase 3 design | Non-blocking, consistent with codebase |
| 3 language defaults | 6 language defaults (rust, ruby, java added) | Phase 6 design | Broader project support |

**Deprecated/outdated:**
- Implicit task ordering: Use explicit `<blocked_by>` XML element for dependencies
- Global cycle detection: Let beads_rust handle this at the dependency level

## Open Questions

1. **`<blocked_by>` Format**
   - What we know: CONTEXT.md says optional `<blocked_by>` inside `<task>` elements
   - What's unclear: Single task ref vs. comma-separated list
   - Recommendation: Start with single task ref (simpler, covers most cases). List support can be added later if needed.

2. **Justfile Section Markers**
   - What we know: Section update preferred over full regeneration
   - What's unclear: Exact marker format for identifying component recipe sections
   - Recommendation: Use `# === COMPONENT RECIPES ===` and `# === END COMPONENT RECIPES ===` markers

3. **Validation Granularity**
   - What we know: Fail-fast validation before any task creation
   - What's unclear: What specific validations to perform
   - Recommendation: Minimum: (1) file is valid YAML/XML, (2) has at least one task, (3) `<blocked_by>` references existing task name in same plan

## Sources

### Primary (HIGH confidence)
- `/home/luke/workspace/github.com/lukemcguire/vibraphone-template/.mcp/servers/vibraphone/tools/bridge_tools.py` - Existing implementation to migrate
- `/home/luke/workspace/github.com/lukemcguire/vibraphone-template/.mcp/servers/vibraphone/tools/stack_tools.py` - Existing implementation to migrate
- `src/vibraphone/utils/cli_runner.py` - Async subprocess execution pattern
- `src/vibraphone/tools/task_tools.py` - br CLI integration pattern

### Secondary (MEDIUM confidence)
- `.planning/phases/05-quality-gate-tools/05-RESEARCH.md` - Similar research format reference
- `src/vibraphone/utils/session.py` - State persistence pattern reference
- `src/vibraphone/config.py` - Config loading pattern

### Tertiary (LOW confidence)
- None - all critical information from verified codebase sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - defusedxml well-documented, existing patterns proven
- Architecture: HIGH - migration from working code with known patterns
- Pitfalls: HIGH - based on CONTEXT.md decisions and existing implementation issues

**Research date:** 2026-02-16
**Valid until:** 30 days (patterns are stable, migration source is version-controlled)
