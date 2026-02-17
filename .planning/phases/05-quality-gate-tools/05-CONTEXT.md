# Phase 5: Quality Gate Tools - Context

**Gathered:** 2026-02-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement MCP tools that enforce quality gates before code can be committed: run_tests, run_lint, run_format, request_code_review, and attempt_commit. Circuit breakers prevent runaway loops. Review state blocks premature commits. All tools integrate with session state for crash recovery.

Scope: Quality gate enforcement tools only. Task management, worktree operations, and scaffolding are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Circuit Breaker Behavior

- **When tripped:** Block the agent entirely (not just the tool)
- **Escalation to human:** Return summary with context (failures + recent agent actions)
- **Human actions available:** All three options:
  1. Reset circuit breaker and let agent continue
  2. Abandon task and start over
  3. Provide guidance then reset breaker
- **Counter reset:** Reset on success (one passing test clears the counter)
- **Thresholds:** Default 5 for tests, 3 for review - configurable per-project
- **Scope:** Per-tool independent counters (tests, lint, review each have their own)
- **Config structure:** Nested per-tool config:
  ```yaml
  circuit_breakers:
    tests:
      max_attempts: 5
    lint:
      max_attempts: null  # no circuit breaker for lint
    review:
      max_attempts: 3
  ```

### Review Approval State

- **Review scope:** Staged changes only - tool handles staging internally
- **Dangerous files blocked:** .env, .pem, .key, credentials.json, etc. cannot be staged
- **Review outcomes:**
  - Comments have severity: "error" or "warning"
  - Any errors = REJECTED
  - Warnings only or clean = APPROVED
  - Max attempts exceeded = ESCALATED
- **State storage:** Per-task state files at `.vibraphone/tasks/{task_id}/state.json`
  - Enables multi-agent scenarios (each task isolated)
  - State cleaned up when task closes
- **State fields:**
  - `last_review_status`: APPROVED/REJECTED/ESCALATED
  - `last_review_diff_hash`: SHA-256 of staged diff
  - `last_review_issues`: List of issues for re-review comparison
  - `review_attempts`: Counter for circuit breaker
  - `test_attempts`: Counter for circuit breaker
- **Previous issues:** Passed to subsequent reviews to ensure nothing is missed

### Structured Review Output

- **Library:** Use `instructor` for Pydantic-validated structured output
- **Provider:** OpenRouter (OpenAI-compatible API)
- **Model selection:** Default to Claude Sonnet, configurable in vibraphone.yaml
- **API key:** Environment variable `REVIEWER_API_KEY`, loaded via python-dotenv
- **Output model:**
  ```python
  class ReviewIssue(BaseModel):
      severity: Literal["error", "warning"]
      file: str
      line: int | None
      message: str
      suggestion: str | None

  class ReviewResult(BaseModel):
      issues: list[ReviewIssue]
      summary: str
  ```

### Tool Output Format

- **Format:** Structured JSON dicts (current approach)
- **Standard fields:**
  - `status`: pass/fail/APPROVED/REJECTED/ESCALATED/committed
  - `output` or `issues`: Tool-specific result data
  - `next_steps`: List of suggested actions for the agent
  - `attempt`: Current attempt count (for tools with circuit breakers)
  - `warnings`: Any non-blocking warnings (e.g., blocked sensitive files)
- **Add timing info:** `duration_ms` and `timestamp` fields

### Command Discovery

- **Approach:** Justfile recipes + vibraphone.yaml override
- **Default commands:**
  - `just test` for run_tests
  - `just lint` for run_lint
  - `just format` for run_format
  - `just check` for attempt_commit quality gate
- **Config override:**
  ```yaml
  quality_gate:
    commands:
      test: "pytest"           # override default "just test"
      lint: "ruff check ."     # override default "just lint"
      format: "ruff format ."  # override default "just format"
      check: "just check"      # quality gate check
  ```
- **Component support:** `run_tests(component="server")` → `just test-server`

### attempt_commit Enforcement

- **Precondition 1:** Review must be APPROVED
- **Precondition 2:** Staged diff hash must match reviewed diff (no sneaking in changes)
- **Precondition 3:** `just check` (or configured command) must pass
- **All pass:** Execute `git commit -m "{message}"`

### Claude's Discretion

- Exact error message wording
- Logging/audit detail level
- Retry behavior for transient failures (network, API)

</decisions>

<specifics>
## Specific Ideas

- "Fat Tools, Skinny Prompts" philosophy - tools handle complexity, not agents
- Agent should not have direct `git add` access - vibraphone controls staging
- Per-task state files solve multi-agent scenarios without SQLite complexity
- instructor library provides clean Pydantic integration with OpenRouter

</specifics>

<deferred>
## Deferred Ideas

- User-level config defaults at ~/.config/vibraphone/ - Phase 8 or v2
- Multi-agent coordination features (task locking) - v2

</deferred>

---

*Phase: 05-quality-gate-tools*
*Context gathered: 2026-02-17*
