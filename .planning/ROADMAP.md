# Roadmap: Vibraphone

## Overview

Vibraphone is being extracted from a template repository into a standalone installable Python package. The migration moves ~4000 lines of working MCP server code into a proper package structure with src layout, adds new scaffolding tools for project initialization, and ensures all existing functionality (task management via beads_rust, git worktree isolation, quality gate enforcement, LLM code review, circuit breakers) survives the migration intact. The journey progresses from foundational packaging to tool migration to new scaffolding features to final testing and documentation.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Package Foundation** - Package installable with server entry point
- [ ] **Phase 2: Configuration & Core Utilities** - Config loading and shared utilities work
- [ ] **Phase 3: Task Management Tools** - Agent can manage tasks via beads_rust
- [x] **Phase 4: Worktree & Session Tools** - Agent works in isolated branches with session recovery (completed 2026-02-17)
- [x] **Phase 5: Quality Gate Tools** - All quality gates enforce review-before-commit (completed 2026-02-17)
- [ ] **Phase 6: Bridge & Stack Tools** - Agent integrates with GSD and configures stack
- [ ] **Phase 7: Scaffolding & Templates** - Agent scaffolds vibraphone into any project
- [x] **Phase 8: Quality Gate Worktree Integration** - Quality gates operate in active worktree (gap closure) (completed 2026-02-17)
- [ ] **Phase 9: Testing & Documentation** - Package tested and documented for users

## Phase Details

### Phase 1: Package Foundation
**Goal**: Package is installable and server starts
**Depends on**: Nothing (first phase)
**Requirements**: PKG-01, PKG-02, PKG-03, PKG-04, PKG-05, PKG-06
**Success Criteria** (what must be TRUE):
  1. User can install vibraphone via `uv tool install vibraphone` from local path
  2. User can install vibraphone via `pip install -e .` for development
  3. Running `vibraphone` command starts FastMCP server on stdio transport
  4. Server starts without vibraphone.yaml and does not crash or emit errors
  5. Source code is organized in src/vibraphone/ layout with proper package structure
**Plans**: 3 plans

Plans:
- [ ] 01-PLAN.md — Create src/vibraphone package structure and configure pyproject.toml
- [ ] 02-PLAN.md — Create FastMCP server entry point with lazy config loading stub
- [ ] 03-PLAN.md — Create tests and verify both installation methods

### Phase 2: Configuration & Core Utilities
**Goal**: Config loading and shared utilities work
**Depends on**: Phase 1
**Requirements**: CFG-01, CFG-02, CFG-03, CFG-04, CFG-05
**Success Criteria** (what must be TRUE):
  1. Server discovers vibraphone.yaml by walking up from any subdirectory
  2. Invalid vibraphone.yaml causes server to fail with clear error message showing which field is wrong
  3. Server runs with missing vibraphone.yaml using all default values
  4. Worktree base path reads from vibraphone.yaml worktrees_path field (defaults to ~/.vibraphone/worktrees/)
  5. Existing vibraphone.yaml from template projects loads without modification
**Plans**: 3 plans

Plans:
- [ ] 02-01-PLAN.md — Implement config discovery with directory walking and boundaries
- [ ] 02-02-PLAN.md — Implement Pydantic config model with validation and error messages
- [ ] 02-03-PLAN.md — Integration tests and Phase 2 success criteria verification

### Phase 3: Task Management Tools
**Goal**: Agent can manage tasks via beads_rust
**Depends on**: Phase 2
**Requirements**: TASK-01, TASK-02, TASK-03, TASK-04, TASK-05, TASK-06
**Success Criteria** (what must be TRUE):
  1. Agent can call list_tasks and see all tasks with status filtering working
  2. Agent can call next_ready and receive the next unblocked task
  3. Agent can call complete_task and immediately see newly unblocked dependent tasks
  4. Agent can call abandon_task and task status resets to ready
  5. Agent can call get_task_context and receive focused context bundle for a task
**Plans**: 5 plans

Plans:
- [ ] 03-01-PLAN.md — Create async CLI runner and structured error model infrastructure
- [ ] 03-02-PLAN.md — Implement list_tasks, next_ready, health_check query tools
- [ ] 03-03-PLAN.md — Implement complete_task, abandon_task mutation tools
- [ ] 03-04-PLAN.md — Implement get_task_context and register tools in server
- [ ] 03-05-PLAN.md — Create unit tests and Phase 3 success criteria verification

### Phase 4: Worktree & Session Tools
**Goal**: Agent works in isolated branches with session recovery
**Depends on**: Phase 3
**Requirements**: WKTREE-01, WKTREE-02, WKTREE-03, WKTREE-04, SESS-01, SESS-02, SESS-03
**Success Criteria** (what must be TRUE):
  1. Agent can call start_task and new worktree appears at configured path with task branch
  2. Agent can call merge_task and task branch merges into main via rebase
  3. Agent can call cleanup_task and worktree directory is removed with branch deleted
  4. Server startup automatically calls session recovery when vibraphone.yaml exists
  5. Session state persists to .vibraphone/session.json after every session operation
**Plans**: 4 plans

Plans:
- [ ] 04-01-PLAN.md — Create session state persistence layer (SessionState model, SessionManager class)
- [ ] 04-02-PLAN.md — Create worktree utility functions for git operations with safety guards
- [ ] 04-03-PLAN.md — Create MCP tools for worktree lifecycle management
- [ ] 04-04-PLAN.md — Add server startup integration and comprehensive unit tests

### Phase 5: Quality Gate Tools
**Goal**: All quality gates enforce review-before-commit
**Depends on**: Phase 4
**Requirements**: QUAL-01, QUAL-02, QUAL-03, QUAL-04, QUAL-05, QUAL-06
**Success Criteria** (what must be TRUE):
  1. Agent can call run_tests and circuit breaker blocks after max failures
  2. Agent can call run_lint and linter output returns
  3. Agent can call request_code_review and LLM review completes with approval/rejection
  4. Agent cannot call attempt_commit successfully without prior approved review
  5. Circuit breaker escalates to human after configured max_attempts exceeded
**Plans**: 5 plans

Plans:
- [ ] 05-01-PLAN.md — Create quality gate foundation (command_runner, circuit_breaker, quality_state)
- [ ] 05-02-PLAN.md — Extend config and create code_reviewer with instructor + OpenRouter
- [ ] 05-03-PLAN.md — Implement all 5 quality gate MCP tools (run_tests, run_lint, run_format, request_code_review, attempt_commit)
- [ ] 05-04-PLAN.md — Create unit tests for utility modules (command_runner, circuit_breaker, quality_state, code_reviewer)
- [ ] 05-05-PLAN.md — Create integration tests for quality gate tools and Phase 5 success criteria verification

### Phase 6: Bridge & Stack Tools
**Goal**: Agent integrates with GSD and configures stack
**Depends on**: Phase 5
**Requirements**: BRDG-01, STACK-01
**Success Criteria** (what must be TRUE):
  1. Agent can call import_gsd_plan and GSD plan converts to beads tasks with dependencies
  2. Agent can call configure_stack and Justfile recipes regenerate with new stack config
**Plans**: 4 plans

Plans:
- [ ] 06-01-PLAN.md — Create plan_parser utilities and extend config with STACK_DEFAULTS
- [ ] 06-02-PLAN.md — Implement import_gsd_plan MCP tool with explicit dependency wiring
- [ ] 06-03-PLAN.md — Implement configure_stack MCP tool with section-based Justfile update
- [ ] 06-04-PLAN.md — Create unit tests and Phase 6 success criteria verification

### Phase 7: Scaffolding & Templates
**Goal**: Agent scaffolds vibraphone into any project
**Depends on**: Phase 6
**Requirements**: NEW-01, NEW-02, NEW-03, NEW-04, NEW-05, NEW-06, NEW-07, NEW-08, NEW-09, TMPL-01, TMPL-02, TMPL-03
**Success Criteria** (what must be TRUE):
  1. Agent can call init_project in empty directory and all files generate correctly
  2. Agent can call init_project in existing project and it does not overwrite files without confirmation
  3. Generated vibraphone.yaml contains project-specific values (not template placeholders)
  4. Generated governance docs match existing template formats exactly
  5. Agent can call check_prerequisites and receive install commands for any missing dependencies
  6. Template files are bundled in the Python wheel and accessible via importlib.resources
**Plans**: 5 plans

Plans:
- [ ] 07-01-PLAN.md — Create bundled templates directory and configure pyproject.toml for wheel inclusion
- [ ] 07-02-PLAN.md — Implement check_prerequisites utility and MCP tool
- [ ] 07-03-PLAN.md — Create template_loader utility for importlib.resources access
- [ ] 07-04-PLAN.md — Implement init_project MCP tool with auto-detection and conflict handling
- [ ] 07-05-PLAN.md — Create unit tests and Phase 7 success criteria verification

### Phase 8: Quality Gate Worktree Integration
**Goal**: Quality gates operate in the active worktree when a session exists
**Depends on**: Phase 7
**Requirements**: QUAL-06 (worktree context)
**Gap Closure**: Closes INT-001 (quality gates ignore worktree context), Flow 2 (task execution flow)
**Success Criteria** (what must be TRUE):
  1. Agent calls start_task and then run_tests runs tests IN the worktree
  2. Agent calls request_code_review and it stages files from the worktree
  3. Agent calls attempt_commit and it commits TO the worktree branch
  4. Quality gates work correctly when no session exists (fallback to project root)
  5. E2E task execution flow works from import to cleanup
**Plans**: 1 plan

Plans:
- [ ] 08-01-PLAN.md — Integrate session awareness into quality gate tools

### Phase 9: Testing & Documentation
**Goal**: Package tested and documented for users
**Depends on**: Phase 8
**Requirements**: TEST-01, TEST-02, TEST-03, DOC-01, DOC-02, DOC-03
**Gap Closure**: Fixes test_phase5_success.py regression from Phase 8
**Success Criteria** (what must be TRUE):
  1. Unit tests run with mocked subprocesses and all pass
  2. Integration tests run with real git/br and key workflows pass
  3. Installed wheel contains all template files verified by test
  4. README explains installation and quickstart clearly
  5. Tool API reference documents all MCP tools with parameters and return values
**Plans**: 5 plans

Plans:
- [ ] 09-01-PLAN.md — Fix test_phase5_success.py mock patches for get_execution_context
- [ ] 09-02-PLAN.md — Complete unit test coverage with mocked subprocesses
- [ ] 09-03-PLAN.md — Create integration tests and wheel template verification
- [ ] 09-04-PLAN.md — Write README with installation and quickstart guide
- [ ] 09-05-PLAN.md — Write tool API reference and architecture documentation

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Package Foundation | 0/3 | Not started | - |
| 2. Configuration & Core Utilities | 0/3 | Not started | - |
| 3. Task Management Tools | 0/5 | Not started | - |
| 4. Worktree & Session Tools | 0/4 | Complete    | 2026-02-17 |
| 5. Quality Gate Tools | 0/5 | Complete    | 2026-02-17 |
| 6. Bridge & Stack Tools | 0/4 | Not started | - |
| 7. Scaffolding & Templates | 0/5 | Not started | - |
| 8. Quality Gate Worktree Integration | 0/1 | Complete    | 2026-02-17 |
| 9. Testing & Documentation | 0/5 | Not started | - |
