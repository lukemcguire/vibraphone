---
phase: 07-scaffolding-templates
plan: 01
subsystem: templates
tags: [scaffolding, templates, bundling, hatchling]
dependencies:
  requires: []
  provides: [bundled-templates]
  affects: [init_project, check_prerequisites]
tech_stack:
  added: []
  patterns: [jinja2-templates, importlib.resources, hatchling-artifacts]
key_files:
  created:
    - src/vibraphone/templates/__init__.py
    - src/vibraphone/templates/vibraphone.yaml.j2
    - src/vibraphone/templates/AGENTS.md
    - src/vibraphone/templates/CLAUDE.md
    - src/vibraphone/templates/gitignore_append.txt
    - src/vibraphone/templates/docs/ARCHITECTURE.md
    - src/vibraphone/templates/docs/GLOSSARY.md
    - src/vibraphone/templates/docs/DECISIONS.md.j2
    - src/vibraphone/templates/docs/CONSTITUTION.md.j2
    - src/vibraphone/templates/docs/prompts/reviewer.md
    - src/vibraphone/templates/docs/specs/_TEMPLATE.md
  modified:
    - pyproject.toml
decisions:
  - Use Jinja2 templates with {{ project_name }}, {{ language }}, {{ worktrees_path }} variables
  - Include language-specific conditional blocks in CONSTITUTION.md.j2 for python, typescript, go, rust, ruby, java
  - Use hatchling artifacts config rather than shared-data for template bundling
metrics:
  duration: 5 min
  tasks: 2
  files: 12
  completed_date: 2026-02-17
---

# Phase 7 Plan 1: Template Bundling Summary

Bundled scaffolding templates in Python wheel via hatchling artifacts configuration. Templates are now accessible via importlib.resources after pip install.

## One-Liner

Template directory with Jinja2 templates for vibraphone.yaml, CONSTITUTION.md, and governance docs bundled in wheel for importlib.resources access.

## Tasks Completed

### Task 1: Create templates directory structure

Created `src/vibraphone/templates/` with all scaffolding templates:
- `vibraphone.yaml.j2` - Jinja2 template with {{ project_name }}, {{ worktrees_path }}, {{ components }} variables
- `AGENTS.md` - Static agent behavioral contract (copied from vibraphone-template)
- `CLAUDE.md` - Claude-specific instructions with project context placeholder
- `gitignore_append.txt` - Vibraphone-specific entries (.vibraphone/, .beads/, worktrees/)
- `docs/CONSTITUTION.md.j2` - Language-specific coding rules with conditionals for 6 languages
- `docs/DECISIONS.md.j2` - Initial ADR template with {{ project_name }} variable
- `docs/ARCHITECTURE.md` - Architecture documentation placeholder
- `docs/GLOSSARY.md` - Domain terminology (copied from vibraphone-template)
- `docs/prompts/reviewer.md` - Code review prompt template
- `docs/specs/_TEMPLATE.md` - Feature spec template

**Commit:** 5f78536

### Task 2: Configure pyproject.toml for template bundling

Added `[tool.hatch.build.targets.wheel]` section with `artifacts = ["src/vibraphone/templates/"]` to bundle templates in the wheel. This ensures templates are accessible via importlib.resources.files() after pip install.

**Commit:** 9d3c5bc

## Deviations from Plan

None - plan executed exactly as written.

## Key Files

| File | Purpose |
|------|---------|
| `src/vibraphone/templates/vibraphone.yaml.j2` | Main config template with project-specific variables |
| `src/vibraphone/templates/docs/CONSTITUTION.md.j2` | Language-specific coding rules with conditional blocks |
| `pyproject.toml` | Hatchling artifacts configuration for wheel bundling |

## Verification

- [x] Template directory structure matches RESEARCH.md recommended structure
- [x] All template files present and readable
- [x] Jinja2 templates contain correct variable placeholders ({{ project_name }}, {{ language }})
- [x] pyproject.toml has artifacts config for templates
- [x] CONSTITUTION.md.j2 has language-specific conditionals for python, typescript, go, rust, ruby, java

## Next Steps

The templates are ready for use by:
1. `init_project` MCP tool (07-02) - will render templates with auto-detected/project-specific values
2. `template_loader.py` utility (07-02) - will use importlib.resources to access bundled templates

## Self-Check: PASSED

- All 11 template files created and verified
- pyproject.toml artifacts config verified
- Both commits (5f78536, 9d3c5bc) verified
- SUMMARY.md created
