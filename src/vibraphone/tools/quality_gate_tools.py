"""Quality gate MCP tools for vibraphone.

This module contains MCP tool implementations for quality gate enforcement:
run_tests, run_lint, run_format, request_code_review, and attempt_commit.

These tools enforce the review-before-commit workflow with circuit breaker
protection and state-based approval tracking.
"""

import asyncio
import hashlib
import re
from datetime import UTC, datetime
from pathlib import Path

from vibraphone.config import get_config
from vibraphone.server import mcp
from vibraphone.utils.circuit_breaker import CircuitBreaker
from vibraphone.utils.code_reviewer import CodeReviewer, MissingAPIKeyError
from vibraphone.utils.command_runner import get_command, run_command
from vibraphone.utils.context import get_effective_task_id, get_execution_context
from vibraphone.utils.quality_state import (
    QualityGateState,
    get_quality_state_manager,
)

# Patterns for dangerous files that should never be staged
DANGEROUS_PATTERNS = [
    r"\.env$",  # .env files
    r"\.env\.",  # .env.local, .env.production, etc.
    r"\.pem$",  # Certificate files
    r"\.key$",  # Private key files
    r"credentials\.json$",  # Credentials files
    r"secrets?\.json$",  # Secrets files
    r"secrets?\.yaml$",  # Secrets YAML files
    r"secrets?\.yml$",  # Secrets YAML files
    r"private",  # Private files (any extension)
    r"id_rsa",  # SSH private keys
    r"id_ed25519$",  # Ed25519 private keys
    r"\.p12$",  # PKCS12 certificates
    r"\.pfx$",  # PFX certificates
]


def is_dangerous_file(file_path: str) -> bool:
    """Check if a file matches dangerous file patterns.

    Args:
        file_path: File path to check.

    Returns:
        True if the file matches a dangerous pattern.
    """
    filename = Path(file_path).name.lower()
    return any(re.search(pattern, filename, re.IGNORECASE) for pattern in DANGEROUS_PATTERNS)


async def get_unstaged_files(cwd: Path) -> list[str]:
    """Get list of unstaged files from git status.

    Args:
        cwd: Working directory for git command.

    Returns:
        List of file paths that are modified but not staged.
    """
    process = await asyncio.create_subprocess_exec(
        "git",
        "status",
        "--porcelain",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )
    stdout_bytes, _ = await process.communicate()
    stdout = stdout_bytes.decode("utf-8", errors="replace")

    # Parse porcelain output: XY filename
    # X = staged status, Y = unstaged status
    # We want files that have unstaged changes (Y != ' ' and not '??' for untracked)
    # or files that are untracked
    files = []
    for line in stdout.strip().split("\n"):
        if not line:
            continue
        # Porcelain format: XY PATH or XY ORIG_PATH -> PATH
        xy = line[:2]
        path_part = line[3:]

        # Handle renamed files
        if " -> " in path_part:
            path_part = path_part.split(" -> ")[1]

        # Include files that have unstaged changes or are untracked
        # Y column: 'M' = modified, 'D' = deleted, 'A' = added
        # '??' = untracked
        if xy == "??" or xy[1] in "MDA":
            files.append(path_part)

    return files


async def stage_files(files: list[str], cwd: Path) -> tuple[int, str, str]:
    """Stage specified files via git add.

    Args:
        files: List of file paths to stage.
        cwd: Working directory for git command.

    Returns:
        Tuple of (returncode, stdout, stderr).
    """
    if not files:
        return (0, "", "")

    process = await asyncio.create_subprocess_exec(
        "git",
        "add",
        *files,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )
    stdout_bytes, stderr_bytes = await process.communicate()
    stdout = stdout_bytes.decode("utf-8", errors="replace")
    stderr = stderr_bytes.decode("utf-8", errors="replace")

    return (process.returncode or 0, stdout, stderr)


async def get_staged_diff(cwd: Path) -> tuple[int, str, str]:
    """Get the staged diff content.

    Args:
        cwd: Working directory for git command.

    Returns:
        Tuple of (returncode, stdout, stderr).
    """
    process = await asyncio.create_subprocess_exec(
        "git",
        "diff",
        "--staged",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )
    stdout_bytes, stderr_bytes = await process.communicate()
    stdout = stdout_bytes.decode("utf-8", errors="replace")
    stderr = stderr_bytes.decode("utf-8", errors="replace")

    return (process.returncode or 0, stdout, stderr)


def hash_diff(diff_content: str) -> str:
    """Generate SHA-256 hash of diff content.

    Args:
        diff_content: The diff string to hash.

    Returns:
        Hexadecimal hash string.
    """
    return hashlib.sha256(diff_content.encode("utf-8")).hexdigest()


def filter_dangerous_files(files: list[str]) -> tuple[list[str], list[str]]:
    """Split files into safe and dangerous file lists.

    Args:
        files: List of file paths to filter.

    Returns:
        Tuple of (safe_files, blocked_files).
    """
    safe_files = []
    blocked_files = []
    for f in files:
        if is_dangerous_file(f):
            blocked_files.append(f)
        else:
            safe_files.append(f)
    return safe_files, blocked_files


def run_llm_review(
    diff_content: str,
    previous_issues: list[dict] | None,
    model: str,
) -> tuple[list[dict], str] | dict:
    """Run LLM code review and return issues and summary.

    Args:
        diff_content: The git diff to review.
        previous_issues: Issues from previous review to re-check.
        model: The LLM model to use.

    Returns:
        Tuple of (issues_data, summary) on success, or error dict on failure.
    """
    try:
        reviewer = CodeReviewer(model=model)
        result = reviewer.review(diff_content, previous_issues)
    except MissingAPIKeyError:
        return {
            "status": "error",
            "error_type": "MissingAPIKeyError",
            "message": "REVIEWER_API_KEY environment variable not set.",
            "human_actions": [
                "Get API key from https://openrouter.ai/keys",
                "Set REVIEWER_API_KEY in environment or .env file",
            ],
            "next_steps": ["Set up API key and retry."],
        }
    except ImportError as e:
        return {
            "status": "error",
            "error_type": "ImportError",
            "message": str(e),
            "next_steps": ["Install required packages: uv add instructor python-dotenv"],
        }

    issues_data = [issue.model_dump() for issue in result.issues]
    return issues_data, result.summary


def build_review_response(
    review_status: str,
    issues_data: list[dict],
    summary: str,
    attempt: int,
    blocked_files: list[str],
) -> dict:
    """Build the response dict for a code review.

    Args:
        review_status: APPROVED, REJECTED, or ESCALATED.
        issues_data: List of issue dicts from review.
        summary: Review summary text.
        attempt: Current attempt number.
        blocked_files: List of blocked dangerous files.

    Returns:
        Response dict with status, issues, summary, warnings, next_steps.
    """
    response = {
        "status": review_status,
        "issues": issues_data,
        "summary": summary,
        "attempt": attempt,
        "next_steps": [],
    }

    if blocked_files:
        response["warnings"] = [f"Blocked dangerous file: {f}" for f in blocked_files]

    if review_status == "APPROVED":
        response["next_steps"] = ["Review approved. Ready for attempt_commit."]
    else:
        response["next_steps"] = [
            "Fix the identified issues.",
            "Run request_code_review again for re-review.",
        ]

    return response


async def prepare_files_for_review(
    files: list[str] | None,
    project_root: Path,
) -> tuple[list[str], list[str], dict | None]:
    """Prepare files for review by staging safe files.

    Args:
        files: Optional list of files to stage. If None, uses all unstaged.
        project_root: Project root directory.

    Returns:
        Tuple of (blocked_files, diff_hash, error_dict).
        If error_dict is not None, staging or diff fetch failed.
    """
    # Get unstaged files
    unstaged_files = await get_unstaged_files(project_root)

    # Filter to requested files if specified
    if files is not None:
        unstaged_files = [f for f in unstaged_files if f in files]

    # Filter out dangerous files
    safe_files, blocked_files = filter_dangerous_files(unstaged_files)

    # Stage safe files
    if safe_files:
        returncode, _stdout, stderr = await stage_files(safe_files, project_root)
        if returncode != 0:
            return (
                [],
                "",
                {
                    "status": "error",
                    "message": f"Failed to stage files: {stderr}",
                    "next_steps": ["Check git status and resolve staging issues."],
                },
            )

    # Get staged diff
    returncode, diff_content, stderr = await get_staged_diff(project_root)
    if returncode != 0:
        return (
            [],
            "",
            {
                "status": "error",
                "message": f"Failed to get staged diff: {stderr}",
                "next_steps": ["Check git status and resolve issues."],
            },
        )

    return blocked_files, diff_content, None


async def run_git_commit(message: str, cwd: Path) -> tuple[int, str, str]:
    """Execute git commit with the given message.

    Args:
        message: Commit message.
        cwd: Working directory for git command.

    Returns:
        Tuple of (returncode, stdout, stderr).
    """
    process = await asyncio.create_subprocess_exec(
        "git",
        "commit",
        "-m",
        message,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )
    stdout_bytes, stderr_bytes = await process.communicate()
    stdout = stdout_bytes.decode("utf-8", errors="replace")
    stderr = stderr_bytes.decode("utf-8", errors="replace")

    return (process.returncode or 0, stdout, stderr)


@mcp.tool
async def run_tests(component: str | None = None) -> dict:
    """Run tests with circuit breaker protection.

    Executes the configured test command and returns structured output.
    Circuit breaker prevents runaway test loops by tracking failures.

    Args:
        component: Optional component name (e.g., "server" -> "just test-server").

    Returns:
        Dict with status, output, duration_ms, timestamp, attempt, next_steps.
        status is "pass" or "fail". Circuit breaker can return "ESCALATED".
    """
    config = get_config()
    exec_dir, session = get_execution_context()
    state_manager = get_quality_state_manager(get_effective_task_id(session))

    # Load state for attempt tracking
    state = state_manager.load()
    if state is None:
        state = QualityGateState(task_id=get_effective_task_id(session))

    # Check circuit breaker before running
    breaker = CircuitBreaker(
        max_attempts=config.circuit_breakers.tests.max_attempts,
        tool_name="run_tests",
    )
    escalation = breaker.check(state.test_attempts)
    if escalation:
        return escalation

    # Get command and execute
    command = get_command("test", component)
    start_time = datetime.now(UTC)

    returncode, stdout, stderr = await run_command(command, cwd=exec_dir)

    end_time = datetime.now(UTC)
    duration_ms = int((end_time - start_time).total_seconds() * 1000)

    output = stdout + ("\n--- STDERR ---\n" + stderr if stderr else "")
    passed = returncode == 0

    # Update state
    if passed:
        state.test_attempts = 0
    else:
        state.test_attempts += 1

        # Check circuit breaker after failure
        escalation = breaker.check(state.test_attempts)
        if escalation:
            state_manager.save(state)
            return escalation

    state_manager.save(state)

    return {
        "status": "pass" if passed else "fail",
        "output": output,
        "duration_ms": duration_ms,
        "timestamp": start_time.isoformat(),
        "attempt": state.test_attempts,
        "next_steps": (["Tests passed. Ready for next step."] if passed else ["Fix failing tests and run again."]),
    }


@mcp.tool
async def run_lint(component: str | None = None) -> dict:
    """Run linter and return output.

    Executes the configured lint command. Lint typically has no circuit breaker
    since failures are usually quick fixes rather than deep problems.

    Args:
        component: Optional component name (e.g., "server" -> "just lint-server").

    Returns:
        Dict with status, output, duration_ms, timestamp, attempt, next_steps.
        status is "pass" (returncode 0) or "fail" (non-zero).
    """
    exec_dir, _session = get_execution_context()

    # Get command and execute
    command = get_command("lint", component)
    start_time = datetime.now(UTC)

    returncode, stdout, stderr = await run_command(command, cwd=exec_dir)

    end_time = datetime.now(UTC)
    duration_ms = int((end_time - start_time).total_seconds() * 1000)

    output = stdout + ("\n--- STDERR ---\n" + stderr if stderr else "")
    passed = returncode == 0

    return {
        "status": "pass" if passed else "fail",
        "output": output,
        "duration_ms": duration_ms,
        "timestamp": start_time.isoformat(),
        "attempt": 0,  # No circuit breaker for lint
        "next_steps": (["Lint passed. Ready for next step."] if passed else ["Fix lint errors and run again."]),
    }


@mcp.tool
async def run_format(component: str | None = None) -> dict:
    """Run formatter (auto-fix mode).

    Executes the configured format command. Formatters typically modify files
    in place, so the output shows what changed.

    Args:
        component: Optional component name (e.g., "server" -> "just format-server").

    Returns:
        Dict with status, output, duration_ms, timestamp, attempt, next_steps.
        status is "pass" (returncode 0) or "fail" (non-zero).
    """
    exec_dir, _session = get_execution_context()

    # Get command and execute
    command = get_command("format", component)
    start_time = datetime.now(UTC)

    returncode, stdout, stderr = await run_command(command, cwd=exec_dir)

    end_time = datetime.now(UTC)
    duration_ms = int((end_time - start_time).total_seconds() * 1000)

    output = stdout + ("\n--- STDERR ---\n" + stderr if stderr else "")
    passed = returncode == 0

    return {
        "status": "pass" if passed else "fail",
        "output": output,
        "duration_ms": duration_ms,
        "timestamp": start_time.isoformat(),
        "attempt": 0,  # No circuit breaker for format
        "next_steps": (
            ["Format passed. Ready for next step."] if passed else ["Format failed. Check output for errors."]
        ),
    }


@mcp.tool
async def request_code_review(task_id: str | None = None, files: list[str] | None = None) -> dict:
    """Request LLM code review of staged changes.

    This tool handles staging internally. It stages unstaged files (optional filter),
    blocks dangerous files, gets the diff, and sends it to an LLM for review.

    Args:
        task_id: Task ID for state tracking. If None, derives from active session.
        files: Optional list of files to stage. If None, stages all unstaged changes.

    Returns:
        Dict with status (APPROVED/REJECTED/ESCALATED), issues, summary,
        warnings (blocked dangerous files), attempt, next_steps.
    """
    config = get_config()
    exec_dir, session = get_execution_context()
    effective_task_id = task_id if task_id else get_effective_task_id(session)
    state_manager = get_quality_state_manager(effective_task_id)

    # Load state
    state = state_manager.load()
    if state is None:
        state = QualityGateState(task_id=effective_task_id)

    # Check circuit breaker before running
    breaker = CircuitBreaker(
        max_attempts=config.circuit_breakers.review.max_attempts,
        tool_name="request_code_review",
    )
    escalation = breaker.check(state.review_attempts)
    if escalation:
        return escalation

    # Prepare files for review
    blocked_files, diff_content, error = await prepare_files_for_review(files, exec_dir)
    if error:
        return error

    # Check if there's anything to review
    if not diff_content.strip():
        return {
            "status": "APPROVED",
            "issues": [],
            "summary": "No staged changes to review.",
            "warnings": blocked_files,
            "attempt": state.review_attempts,
            "next_steps": ["No changes to commit."],
        }

    # Hash the diff for later verification
    diff_hash = hash_diff(diff_content)

    # Prepare previous issues for context
    previous_issues = state.last_review_issues if state.last_review_issues else None

    # Run LLM review
    review_result = run_llm_review(diff_content, previous_issues, config.review.model)
    if isinstance(review_result, dict):
        return review_result  # Error case

    issues_data, summary = review_result

    # Determine status based on severity
    has_errors = any(issue.get("severity") == "error" for issue in issues_data)

    if has_errors:
        review_status = "REJECTED"
        state.review_attempts += 1
    else:
        review_status = "APPROVED"
        state.review_attempts = 0  # Reset on approval

    # Update state
    state.last_review_status = review_status
    state.last_review_diff_hash = diff_hash
    state.last_review_issues = issues_data

    # Check circuit breaker after rejection
    if review_status == "REJECTED":
        escalation = breaker.check(state.review_attempts)
        if escalation:
            state_manager.save(state)
            return escalation

    state_manager.save(state)

    # Build and return response
    return build_review_response(review_status, issues_data, summary, state.review_attempts, blocked_files)


@mcp.tool
async def attempt_commit(task_id: str | None = None, message: str = "") -> dict:
    """Attempt to commit changes. Requires approved code review.

    Enforces the review-before-commit workflow:
    1. Review must be APPROVED
    2. Staged diff hash must match reviewed diff (no sneaking in changes)
    3. Quality gate check must pass

    All conditions must be met before executing git commit.

    Args:
        task_id: Task ID for state verification. If None, derives from active session.
        message: Commit message.

    Returns:
        Dict with status ("committed" or "error"), message (commit hash or error),
        and next_steps.
    """
    exec_dir, session = get_execution_context()
    effective_task_id = task_id if task_id else get_effective_task_id(session)
    state_manager = get_quality_state_manager(effective_task_id)

    # Load state
    state = state_manager.load()

    # Check 1: State exists and has approved review
    if state is None or state.last_review_status != "APPROVED":
        return {
            "status": "error",
            "message": "No approved review found. Run request_code_review first.",
            "next_steps": ["Run request_code_review to get approval."],
        }

    # Check 2: Staged diff matches reviewed diff
    returncode, current_diff, stderr = await get_staged_diff(exec_dir)
    if returncode != 0:
        return {
            "status": "error",
            "message": f"Failed to get staged diff: {stderr}",
            "next_steps": ["Check git status and resolve issues."],
        }

    current_hash = hash_diff(current_diff)
    if current_hash != state.last_review_diff_hash:
        return {
            "status": "error",
            "message": "Staged changes differ from reviewed changes. Re-review required.",
            "next_steps": ["Run request_code_review again."],
        }

    # Check 3: Quality gate passes
    check_command = get_command("check")
    returncode, stdout, stderr = await run_command(check_command, cwd=exec_dir)

    if returncode != 0:
        output = stdout + ("\n--- STDERR ---\n" + stderr if stderr else "")
        return {
            "status": "error",
            "message": f"Quality gate check failed:\n{output}",
            "next_steps": [
                "Fix the quality gate failures.",
                "Re-run request_code_review after fixes.",
            ],
        }

    # All checks passed - execute commit
    returncode, stdout, stderr = await run_git_commit(message, cwd=exec_dir)

    if returncode != 0:
        output = stdout + ("\n--- STDERR ---\n" + stderr if stderr else "")
        return {
            "status": "error",
            "message": f"Git commit failed:\n{output}",
            "next_steps": ["Check git status and resolve issues."],
        }

    # Extract commit hash from output
    # git commit output typically includes the hash on a line like:
    # [main abc1234] commit message
    commit_hash = ""
    for line in stdout.split("\n"):
        if line.startswith("["):
            # Extract hash between branch name and ]
            parts = line.split()
            if len(parts) >= 2:
                commit_hash = parts[1].rstrip("]")
                break

    return {
        "status": "committed",
        "message": f"Commit {commit_hash}" if commit_hash else "Commit successful",
        "commit_hash": commit_hash,
        "next_steps": [
            "Commit successful.",
            "Continue with next task or push when ready.",
        ],
    }
