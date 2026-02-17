# Phase 9: Testing & Documentation - Context

**Gathered:** 2026-02-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Prepare vibraphone for users through comprehensive testing and clear documentation. Includes fixing the test_phase5_success.py regression from Phase 8, completing unit test coverage, creating integration tests, writing user-facing README and tool documentation, and verifying wheel contents. Scope is testing infrastructure and user-facing docs only — no new features.

</domain>

<decisions>
## Implementation Decisions

### Test Strategy

**Mock depth: Selective mocking**
- Unit tests mock external tools (git, br, bv) but use real filesystem and Python APIs
- Integration tests use real git repos in temp directories
- Full mocking hides integration bugs; selective gives best of both worlds

**Integration coverage: Both per-tool and E2E**
- Per-tool tests verify each tool works in isolation with real git
- E2E tests verify complete workflows (start_task → work → commit → cleanup)
- Catches interaction bugs that per-tool tests miss

**Must-pass workflows: Critical paths only**
- start_task → code_review → commit flow
- import_gsd_plan flow
- init_project flow
- These are the essential paths that must work with real git/br for phase success

**test_phase5_success.py regression: Fix and expand**
- Fix the mock patches for get_execution_context
- Add worktree-specific integration tests alongside the fix

**CI approach: Fast feedback**
- Unit tests run on every push
- Integration tests run on main branch only
- Fast feedback loop for developers

**Test data: Shared fixtures**
- tests/fixtures/ contains sample GSD plans, git repos, config files
- Reduces duplication across test files

**Wheel verification: Both approaches**
- Build-and-extract test verifies template files exist in wheel
- Install-and-run test verifies init_project works from installed wheel

**Coverage gate: High coverage (90%+)**
- Vibraphone is a developer tool — high bar justified
- Enforce on new code, not necessarily legacy

### README Focus

**Primary reader: New users**
- Developers installing vibraphone into their projects
- Practical, task-focused documentation

**Quickstart: Full workflow (5 min)**
- Install, init, start_task through commit
- Complete mini workflow that shows the value prop

**Examples: Workflow examples**
- 2-3 complete workflows showing tools working together
- Realistic usage patterns, not just per-tool snippets

**Tone: Opinionated guide**
- Explains why vibraphone exists, what problems it solves
- Not just reference material — shows how to think about the tool

**Structure: Problem-first**
- Problem → Solution → Quickstart → Examples → Config
- Story-driven, draws reader in

**Config docs: Brief in README**
- Brief description of vibraphone.yaml fields
- Link to full reference for details

**Badges: Extended**
- PyPI version, Python versions, license
- CI status, coverage, code quality

**Visual: One diagram**
- Workflow diagram or architecture diagram
- Helps comprehension without overcomplicating

**Review step: Run through /crafting-effective-readmes skill after drafting**

### API Docs Approach

**Structure: Per-category files**
- task-tools.md, quality-tools.md, worktree-tools.md, etc.
- Modular, easy to find relevant tools

**Per-tool content: Examples + API**
- Description, parameters, return value
- Usage examples and common patterns
- More helpful than raw API spec

**Parameter docs: Examples + field list**
- Field list with types (human-readable)
- No full JSON schemas inline (redundant with MCP protocol)

**Source: Hybrid**
- Auto-generate API reference from docstrings via mkdocstrings
- Hand-write examples, guides, architecture in markdown

**Error docs: Full error reference**
- Dedicated error reference with all TaskError/WorktreeError types
- Common errors and resolutions per tool

**Location: docs/ directory**
- All docs in docs/ directory
- Keep README clean

**Scope: Full docs suite**
- API reference (auto-generated)
- Architecture doc (design decisions, data flow)
- Contributing guide (for future contributors)

**Format: Hybrid MkDocs**
- MkDocs + mkdocstrings plugin
- API reference rendered from docstrings
- Guides, examples, architecture in separate markdown files
- Local preview, search, navigation

### Test Organization

**File layout: Mirror src structure**
- tests/ mirrors src/vibraphone/ structure
- Each module gets a test file

**Naming: Match existing patterns**
- Follow existing test naming conventions in codebase
- Consistency over introducing new patterns

**Class organization: Classes by feature**
- Group related tests in classes (TestConfigDiscovery, TestConfigValidation)
- Better organization than flat functions

**Shared code: Both conftest.py and helpers/**
- conftest.py for pytest fixtures at each level
- tests/helpers/ for reusable test utilities

**Success tests: Per-phase files**
- test_phase<N>_success.py per phase
- Keeps phase verification isolated

**Integration tests: Separate directory**
- tests/integration/ directory
- Clear separation from unit tests

**Fixtures: Both static files and factories**
- Static files for complex data (sample repos, GSD plans)
- Factory functions for simple cases (temp configs, mock sessions)

**Dependencies: Extended pytest suite**
- pytest, pytest-asyncio (core)
- pytest-cov (coverage)
- pytest-xdist (parallel execution)
- pytest-timeout (prevent hanging tests)

</decisions>

<specifics>
## Specific Ideas

- Review README with `/crafting-effective-readmes` skill after drafting
- Consider including workflow diagram showing tool interaction
- Point agents at MCP `tools/list` endpoint or export schemas to `schemas/` directory if schema consumption needed

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 09-testing-documentation*
*Context gathered: 2026-02-17*
