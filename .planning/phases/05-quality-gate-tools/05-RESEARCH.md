# Phase 5: Quality Gate Tools - Research

**Researched:** 2026-02-16
**Domain:** Quality gate enforcement tools with circuit breakers and LLM-powered code review
**Confidence:** HIGH

## Summary

Phase 5 implements five MCP tools that enforce quality gates before code can be committed: `run_tests`, `run_lint`, `run_format`, `request_code_review`, and `attempt_commit`. The key innovations are:

1. **Circuit breakers** that block agents after configurable failed attempts, with escalation to humans
2. **Per-task state persistence** that tracks review status and enables multi-agent scenarios
3. **Structured LLM code review** using the `instructor` library with Pydantic-validated output via OpenRouter

The implementation leverages existing patterns from the codebase (FastMCP tools, TaskError model, async subprocess execution via `asyncio.create_subprocess_exec`, atomic file writes via `tempfile.NamedTemporaryFile`).

**Primary recommendation:** Build on existing patterns. Use `instructor.from_provider()` for OpenRouter integration with Pydantic models. Store per-task quality gate state in `.vibraphone/tasks/{task_id}/state.json` using the atomic write pattern from `SessionManager`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Circuit Breaker Behavior

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

#### Review Approval State

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

#### Structured Review Output

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

#### Tool Output Format

- **Format:** Structured JSON dicts (current approach)
- **Standard fields:**
  - `status`: pass/fail/APPROVED/REJECTED/ESCALATED/committed
  - `output` or `issues`: Tool-specific result data
  - `next_steps`: List of suggested actions for the agent
  - `attempt`: Current attempt count (for tools with circuit breakers)
  - `warnings`: Any non-blocking warnings (e.g., blocked sensitive files)
- **Add timing info:** `duration_ms` and `timestamp` fields

#### Command Discovery

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
- **Component support:** `run_tests(component="server")` -> `just test-server`

#### attempt_commit Enforcement

- **Precondition 1:** Review must be APPROVED
- **Precondition 2:** Staged diff hash must match reviewed diff (no sneaking in changes)
- **Precondition 3:** `just check` (or configured command) must pass
- **All pass:** Execute `git commit -m "{message}"`

### Claude's Discretion

- Exact error message wording
- Logging/audit detail level
- Retry behavior for transient failures (network, API)

### Deferred Ideas (OUT OF SCOPE)

- User-level config defaults at ~/.config/vibraphone/ - Phase 8 or v2
- Multi-agent coordination features (task locking) - v2

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| QUAL-01 | Agent can run tests with circuit breaker (run_tests) | Async subprocess execution pattern, circuit breaker state management, command discovery from config |
| QUAL-02 | Agent can run linter (run_lint) | Same async subprocess pattern, optional circuit breaker via config |
| QUAL-03 | Agent can run formatter (run_format) | Same async subprocess pattern, auto-fix mode handling |
| QUAL-04 | Agent can request LLM-powered code review with staging (request_code_review) | instructor library with OpenRouter, git diff hashing, dangerous file blocking, Pydantic models |
| QUAL-05 | Agent can commit only after approved review (attempt_commit) | Review state validation, diff hash verification, git commit execution |
| QUAL-06 | Circuit breakers escalate after configurable max attempts | Per-tool counter state, escalation response format, config schema |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastmcp | >=2.0 | MCP tool framework | Already in use, provides @mcp.tool decorator |
| pydantic | >=2.0 | Data validation and models | Already in use, TaskError pattern, ReviewIssue/ReviewResult models |
| instructor | >=1.0 | Structured LLM output with validation | Industry standard (3M+ downloads/month), seamless Pydantic integration |
| python-dotenv | >=1.0 | Load environment variables from .env | 12-factor app pattern, loads REVIEWER_API_KEY |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| openai | >=1.0 | OpenAI-compatible client for OpenRouter | Instructor wraps this for structured output |
| hashlib | (stdlib) | SHA-256 diff hashing | Verifying staged changes match reviewed changes |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| instructor | Direct OpenAI client with response_format | instructor provides automatic retries, validation, and cleaner API |
| OpenRouter | Direct Anthropic/OpenAI API | OpenRouter provides unified access to multiple models with one API key |
| python-dotenv | os.environ only | dotenv enables .env files for local development |

**Installation:**
```bash
uv add instructor python-dotenv
# or
pip install instructor python-dotenv
```

## Architecture Patterns

### Recommended Project Structure
```
src/vibraphone/
├── tools/
│   ├── quality_gate_tools.py    # NEW: run_tests, run_lint, run_format, request_code_review, attempt_commit
│   ├── task_tools.py            # EXISTING: list_tasks, complete_task, etc.
│   └── worktree_tools.py        # EXISTING: start_task, merge_task, cleanup_task
├── utils/
│   ├── circuit_breaker.py       # NEW: CircuitBreaker class with per-tool counters
│   ├── quality_state.py         # NEW: QualityState model and manager
│   ├── code_reviewer.py         # NEW: Instructor-based LLM reviewer
│   ├── command_runner.py        # NEW: Command discovery and execution
│   ├── cli_runner.py            # EXISTING: br/bv CLI execution
│   ├── errors.py                # EXISTING: TaskError model
│   └── session.py               # EXISTING: SessionState model
└── config.py                    # EXTEND: Add circuit_breakers and quality_gate.commands
```

### Pattern 1: Async Subprocess Execution
**What:** Non-blocking command execution using `asyncio.create_subprocess_exec`
**When to use:** All CLI commands (tests, lint, format, git operations)
**Example:**
```python
# Source: Existing cli_runner.py and worktree_ops.py patterns
import asyncio

async def run_command(command: str, *args: str, cwd: Path | None = None) -> tuple[int, str, str]:
    """Run command asynchronously, return (returncode, stdout, stderr)."""
    process = await asyncio.create_subprocess_exec(
        command,
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )
    stdout_bytes, stderr_bytes = await process.communicate()
    return (
        process.returncode or 0,
        stdout_bytes.decode("utf-8", errors="replace"),
        stderr_bytes.decode("utf-8", errors="replace"),
    )
```

### Pattern 2: Instructor with OpenRouter
**What:** Structured LLM output using instructor library with Pydantic validation
**When to use:** Code review in request_code_review
**Example:**
```python
# Source: https://python.useinstructor.com/
import instructor
from pydantic import BaseModel
from typing import Literal

class ReviewIssue(BaseModel):
    severity: Literal["error", "warning"]
    file: str
    line: int | None
    message: str
    suggestion: str | None

class ReviewResult(BaseModel):
    issues: list[ReviewIssue]
    summary: str

# OpenRouter uses OpenAI-compatible API
# baseURL: https://openrouter.ai/api/v1
# Authorization: Bearer $OPENROUTER_API_KEY
client = instructor.from_provider(
    "openrouter/anthropic/claude-3-sonnet",  # configurable model
    api_key=os.getenv("REVIEWER_API_KEY"),
)

result: ReviewResult = client.create(
    response_model=ReviewResult,
    messages=[
        {"role": "system", "content": "Review the following code changes..."},
        {"role": "user", "content": diff_content},
    ],
    max_retries=2,  # Auto-retry on validation failure
)
```

### Pattern 3: Per-Task State Persistence
**What:** Atomic file writes for per-task quality gate state
**When to use:** Storing review status, circuit breaker counters, diff hashes
**Example:**
```python
# Source: Existing session.py pattern
import json
import tempfile
from pathlib import Path
from pydantic import BaseModel

class QualityGateState(BaseModel):
    task_id: str
    last_review_status: str | None = None  # APPROVED/REJECTED/ESCALATED
    last_review_diff_hash: str | None = None  # SHA-256
    last_review_issues: list[dict] = []
    review_attempts: int = 0
    test_attempts: int = 0
    lint_attempts: int = 0

class QualityStateManager:
    def __init__(self, project_root: Path, task_id: str):
        self.state_file = project_root / ".vibraphone" / "tasks" / task_id / "state.json"

    def load(self) -> QualityGateState | None:
        if not self.state_file.exists():
            return None
        data = json.loads(self.state_file.read_text())
        return QualityGateState(**data)

    def save(self, state: QualityGateState) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        # Atomic write via temp file + rename
        with tempfile.NamedTemporaryFile(
            mode="w",
            dir=self.state_file.parent,
            delete=False,
            encoding="utf-8",
        ) as temp_file:
            temp_file.write(state.model_dump_json(indent=2))
            temp_name = temp_file.name
        Path(temp_name).rename(self.state_file)
```

### Pattern 4: Circuit Breaker with Escalation
**What:** Counter-based failure tracking with escalation to human
**When to use:** run_tests, request_code_review (configurable for all tools)
**Example:**
```python
# Source: CONTEXT.md locked decision
class CircuitBreaker:
    def __init__(self, max_attempts: int | None, tool_name: str):
        self.max_attempts = max_attempts
        self.tool_name = tool_name

    def check(self, current_attempts: int) -> dict | None:
        """Return escalation response if tripped, None otherwise."""
        if self.max_attempts is None:
            return None  # No circuit breaker configured
        if current_attempts >= self.max_attempts:
            return {
                "status": "ESCALATED",
                "error_type": "CircuitBreakerTripped",
                "message": f"{self.tool_name} failed {current_attempts} times (max: {self.max_attempts})",
                "human_actions": [
                    "Reset circuit breaker and let agent continue",
                    "Abandon task and start over",
                    "Provide guidance then reset breaker",
                ],
                "next_steps": ["Await human decision"],
            }
        return None

    def should_reset_on_success(self) -> bool:
        """Counter resets on success (one passing test clears the counter)."""
        return True
```

### Anti-Patterns to Avoid
- **Blocking subprocess calls:** Never use `subprocess.run()` - use `asyncio.create_subprocess_exec`
- **Direct agent git add access:** All staging happens through request_code_review, not exposed to agent
- **Global circuit breaker state:** Each tool (tests, lint, review) has independent counters
- **Missing dangerous file blocking:** Always filter .env, .pem, .key, credentials.json before staging

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Structured LLM output | Custom JSON parsing with validation | instructor library | Automatic retries, Pydantic validation, clean API |
| Environment variable loading | Manual .env parsing | python-dotenv | Handles edge cases, variable expansion, comments |
| Atomic file writes | Custom rename logic | tempfile.NamedTemporaryFile + Path.rename | POSIX atomicity guarantees |
| Process execution | subprocess.run (blocking) | asyncio.create_subprocess_exec | Non-blocking, matches existing patterns |
| Diff hashing | Custom hash implementation | hashlib.sha256 | Standard, reliable, matches git's approach |

**Key insight:** The instructor library handles the complexity of structured output extraction including validation failures, retries, and provider-specific quirks. Building this manually would require handling many edge cases.

## Common Pitfalls

### Pitfall 1: Circuit Breaker State Race Conditions
**What goes wrong:** Multiple tool calls increment counters incorrectly
**Why it happens:** Non-atomic read-modify-write operations on state file
**How to avoid:** Load state once at start of tool execution, save at end. The atomic write pattern prevents corruption.
**Warning signs:** Counter values don't match actual attempts

### Pitfall 2: Stale Review After Code Changes
**What goes wrong:** Agent modifies code after review but before commit, bypassing review
**Why it happens:** No verification that staged diff matches reviewed diff
**How to avoid:** Store SHA-256 hash of reviewed diff in state, verify hash matches before attempt_commit
**Warning signs:** attempt_commit succeeds with unreviewed changes

### Pitfall 3: Missing Dangerous File Detection
**What goes wrong:** Sensitive files like .env get staged and reviewed, leaking secrets
**Why it happens:** Not filtering files before staging
**How to avoid:** Block staging of files matching patterns: `.env*`, `*.pem`, `*.key`, `*credentials*`, `*secret*`
**Warning signs:** Review output contains sensitive file content

### Pitfall 4: Command Discovery Failure
**What goes wrong:** Tool fails because `just test` doesn't exist
**Why it happens:** Project uses pytest directly, not justfile
**How to avoid:** Check vibraphone.yaml for command override first, then fall back to justfile defaults
**Warning signs:** "command not found: just" errors

### Pitfall 5: Instructor/OpenRouter API Errors
**What goes wrong:** Code review fails due to network issues or API limits
**Why it happens:** Transient failures not handled gracefully
**How to avoid:** Claude's discretion: Implement retry with exponential backoff for transient failures. Return clear error for non-transient (auth, rate limit).
**Warning signs:** Random review failures, inconsistent behavior

## Code Examples

Verified patterns from official sources:

### Instructor with OpenRouter Integration
```python
# Source: https://python.useinstructor.com/ and https://openrouter.ai/docs
import os
import instructor
from openai import OpenAI
from pydantic import BaseModel
from typing import Literal
from dotenv import load_dotenv

load_dotenv()  # Load REVIEWER_API_KEY from .env

class ReviewIssue(BaseModel):
    severity: Literal["error", "warning"]
    file: str
    line: int | None
    message: str
    suggestion: str | None

class ReviewResult(BaseModel):
    issues: list[ReviewIssue]
    summary: str

# OpenRouter uses OpenAI SDK with custom base_url
client = instructor.patch(
    OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ.get("REVIEWER_API_KEY"),
    ),
)

def review_code(diff_content: str, previous_issues: list[dict] | None = None) -> ReviewResult:
    system_prompt = "You are a code reviewer. Analyze the diff for issues."
    if previous_issues:
        system_prompt += f"\n\nPreviously identified issues to re-check: {previous_issues}"

    return client.chat.completions.create(
        model="anthropic/claude-3-sonnet",  # Configurable in vibraphone.yaml
        response_model=ReviewResult,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Review these changes:\n\n{diff_content}"},
        ],
        max_retries=2,
    )
```

### SHA-256 Diff Hashing
```python
# Source: Standard library pattern
import hashlib

def hash_diff(diff_content: str) -> str:
    """Generate SHA-256 hash of diff content for integrity verification."""
    return hashlib.sha256(diff_content.encode("utf-8")).hexdigest()
```

### Dangerous File Detection
```python
# Source: CONTEXT.md locked decision
import re
from pathlib import Path

DANGEROUS_PATTERNS = [
    r"\.env",           # .env, .env.local, .env.production
    r"\.pem$",          # Certificate files
    r"\.key$",          # Key files
    r"credentials",     # credentials.json, aws-credentials
    r"secrets?",        # secrets.yaml, secret.json
    r"private",         # private.key, private.pem
]

def is_dangerous_file(file_path: Path) -> bool:
    """Check if file matches dangerous patterns."""
    file_str = str(file_path).lower()
    return any(re.search(pattern, file_str) for pattern in DANGEROUS_PATTERNS)

def filter_safe_files(files: list[Path]) -> tuple[list[Path], list[Path]]:
    """Split files into safe and dangerous lists."""
    safe, dangerous = [], []
    for f in files:
        (dangerous if is_dangerous_file(f) else safe).append(f)
    return safe, dangerous
```

### Command Discovery with Override
```python
# Source: CONTEXT.md locked decision
from pathlib import Path

# Default commands
DEFAULT_COMMANDS = {
    "test": "just test",
    "lint": "just lint",
    "format": "just format",
    "check": "just check",
}

def get_command(
    command_type: str,
    config: dict,
    component: str | None = None,
) -> str:
    """Get command from config override or default.

    Args:
        command_type: One of "test", "lint", "format", "check"
        config: Parsed vibraphone.yaml config dict
        component: Optional component name (e.g., "server" -> "test-server")

    Returns:
        Command string to execute
    """
    # Check config override first
    quality_gate = config.get("quality_gate", {})
    commands = quality_gate.get("commands", {})
    command = commands.get(command_type, DEFAULT_COMMANDS.get(command_type, f"just {command_type}"))

    # Handle component suffix for justfile recipes
    if component and command.startswith("just "):
        recipe = command[5:]  # Remove "just "
        command = f"just {recipe}-{component}"

    return command
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Custom JSON parsing for LLM output | instructor library with Pydantic | 2024 | Validation, retries, type safety |
| Global circuit breaker | Per-tool independent counters | Phase 5 design | Granular control, config flexibility |
| SQLite for state | Per-task JSON files | Phase 5 design | Simpler, no DB dependencies, task isolation |
| Hardcoded commands | Config override + justfile defaults | Phase 5 design | Project flexibility |

**Deprecated/outdated:**
- subprocess.run (blocking): Use asyncio.create_subprocess_exec for non-blocking execution
- Global state files: Use per-task state for multi-agent scenarios

## Open Questions

1. **Component Discovery for Justfile Recipes**
   - What we know: Config supports component override (e.g., `test-server`)
   - What's unclear: How to discover available components from justfile
   - Recommendation: Don't auto-discover; rely on config or explicit component parameter

2. **Review Prompt Template Location**
   - What we know: Review prompt needs to include diff and previous issues
   - What's unclear: Should prompt template be configurable or hardcoded
   - Recommendation: Start with hardcoded prompt; make configurable in v2 if needed

3. **Circuit Breaker Reset UI**
   - What we know: Human can reset circuit breaker via escalation response
   - What's unclear: Whether to expose reset_circuit_breaker tool or handle via config
   - Recommendation: Claude's discretion - tool-based reset is cleaner for agent interaction

## Sources

### Primary (HIGH confidence)
- https://python.useinstructor.com/ - Instructor library documentation (Pydantic integration, OpenAI compatibility, retries)
- https://openrouter.ai/docs - OpenRouter API documentation (OpenAI-compatible, base_url, authentication)
- https://pypi.org/project/python-dotenv/ - python-dotenv documentation (load_dotenv, .env file format)

### Secondary (MEDIUM confidence)
- Existing codebase patterns: `cli_runner.py`, `session.py`, `worktree_ops.py`, `config.py`
- CONTEXT.md locked decisions for implementation requirements

### Tertiary (LOW confidence)
- None - all critical information verified with official sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - instructor and python-dotenv are well-documented, existing patterns are proven
- Architecture: HIGH - patterns derived from existing codebase and locked decisions
- Pitfalls: HIGH - based on locked requirements and common implementation issues

**Research date:** 2026-02-16
**Valid until:** 30 days (instructor library stable, patterns are foundational)
