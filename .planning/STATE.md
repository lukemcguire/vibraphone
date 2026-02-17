# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-16)

**Core value:** Every code change goes through the quality gate (tests, lint, review) before it can be committed — enforced by tooling, not by prompting.
**Current focus:** Phase 5 - Quality Gate Tools

## Current Position

Phase: 5 of 8 (Quality Gate Tools)
Current Plan: 2 of 5 in current phase
Total Plans in Phase: 5
Status: Config extensions and code reviewer complete - circuit_breakers, review.model, CodeReviewer
Last activity: 2026-02-17 — Completed 05-02 Configuration Extensions

Progress: [████████░░] 80%

## Performance Metrics

**Velocity:**
- Total plans completed: 15
- Average duration: 2.9 min
- Total execution time: 0.73 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-package-foundation | 3 | 3 | 2.7 min |
| 02-configuration-core-utilities | 3 | 3 | 3.7 min |
| 03-task-management-tools | 5 | 8 | 1.6 min |
| 04-worktree-session-tools | 4 | 4 | 2.3 min |

**Recent Trend:**
- Last 5 plans: 2.8 min
- Trend: Steady

*Updated after each plan completion*

| Phase 04 P01 | 1min | 3 tasks | 1 file |
| Phase 04 P02 | 3min | 5 tasks | 1 file |
| Phase 04 P03 | 3min | 5 tasks | 2 files |
| Phase 04 P04 | 15min | 5 tasks | 9 files |
| Phase 05 P01 | 4min | 3 tasks | 3 files |
| Phase 05 P02 | 3min | 2 tasks | 2 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Extract to standalone package (not template) — Templates can't be installed into existing projects, can't be updated cleanly
- MCP-only interface (no CLI) — All interaction through coding agents; single entry point simplifies distribution
- Worktree default ~/.vibraphone/worktrees/ — Global location outside project dir reduces agent confusion
- Project-level config only (vibraphone.yaml) — Simplicity for v1; user-level defaults deferred
- Detect-and-guide for br/bv — Bundling Rust binaries adds complexity; check_prerequisites tells users how to install
- Governance files in .planning/vibraphone/ — Keeps vibraphone scaffolding separate from GSD planning docs
- Use Hatchling auto-discovery for src layout (01-01) — No explicit wheel config needed for src layout
- Use importlib mode for pytest (01-01) — Works with src layout without flat pythonpath
- FastMCP tools are FunctionTool objects (01-02) — Verify via mcp._tool_manager, not direct call
- Entry point via uv pip install -e . (01-02) — Available at .venv/bin/vibraphone, not global PATH
- Subprocess test pattern for entry point (01-03) — Verifies module runnable without blocking on stdin
- Config cache clearing in test setup (01-03) — Ensures test isolation
- Config discovery checks for vibraphone.yaml BEFORE .git boundary (02-01) — Ensures config at project root is found
- Symlink following via Path.resolve() for config discovery (02-01) — Standard Python behavior
- Pydantic BaseModel with ConfigDict(extra='allow') for template compatibility (02-02) — Allows unknown fields with warnings
- Unknown field warnings with typo suggestions via difflib.get_close_matches (02-02) — Helpful error messages
- [Phase 02]: Success criteria tests named by requirement ID for ROADMAP traceability
- [Phase 03-01]: asyncio.create_subprocess_exec for non-blocking CLI execution (not subprocess.run)
- [Phase 03-02]: Query tools use run_cli pattern with br/bv JSON output
- [Phase 03-03]: complete_task checks blocked status before closing, abandon_task requires reason
- [Phase 03-04]: get_task_context extracts mermaid from architecture.md, uses subprocess for git log
- [Phase 03-05]: Access FastMCP tool functions via .fn attribute for unit testing
- [Phase 04-01]: Session file at .vibraphone/session.json (runtime state separate from governance docs)
- [Phase 04-01]: Atomic writes via tempfile.NamedTemporaryFile + Path.rename for POSIX guarantee
- [Phase 04-01]: SessionManager.load() returns None for missing files (not exception)
- [Phase 04-02]: WorktreeError/RebaseError follow TaskError pattern (error_type, message, suggested_action)
- [Phase 04-02]: Always abort rebase before raising RebaseError to restore clean git state
- [Phase 04-02]: Git operations via asyncio.create_subprocess_exec in worktree_ops.py
- [Phase 04]: TaskError reused for consistent error format across worktree tools
- [Phase 04]: Session not cleared after merge_task - cleanup_task handles complete cleanup
- [Phase 04]: Branch deletion failure ignored in cleanup_task - might already be gone
- [Phase 04-04]: TaskError moved to utils/errors.py to break circular imports
- [Phase 04-04]: get_project_root moved to config.py from task_tools.py
- [Phase 04-04]: WorktreeError/RebaseError extend Exception (not BaseModel) for proper exception handling
- [Phase 05-01]: command_runner returns raw (returncode, stdout, stderr) tuple - tools parse output themselves
- [Phase 05-01]: Circuit breaker check() returns None when disabled or not tripped
- [Phase 05-01]: Per-task state files at .vibraphone/tasks/{task_id}/state.json for task isolation
- [Phase 05-02]: CircuitBreakerToolConfig.max_attempts uses Optional[int] (None = disabled)
- [Phase 05-02]: CodeReviewer uses lazy client initialization to avoid import errors
- [Phase 05-02]: MissingAPIKeyError provides setup instructions in error message

### Pending Todos

None yet.

### Blockers/Concerns

- **Phase 1**: ~~FastMCP entry point pattern needs verification~~ — Resolved: use FastMCP docs pattern
- **Phase 3**: Session recovery has known bug — may need debugging during migration
- **Phase 7**: init_project file merging strategy needs careful design to avoid overwriting user files

## Session Continuity

Last session: 2026-02-17 — Completed 05-02 Configuration Extensions
Stopped at: Phase 5 Plan 2 complete, continuing with Plan 3
Resume file: .planning/phases/05-quality-gate-tools/05-CONTEXT.md
