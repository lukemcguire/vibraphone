"""Reusable mock helpers for vibraphone tests.

This module provides factory functions for creating mock objects
commonly needed in tests, reducing boilerplate across test files.
"""

from datetime import UTC, datetime
from pathlib import Path
from tempfile import gettempdir
from typing import Any, Literal
from unittest.mock import MagicMock

from vibraphone.utils.quality_state import QualityGateState
from vibraphone.utils.session import SessionState


def create_mock_session(
    task_id: str = "test-task",
    worktree_path: Path | None = None,
    branch_name: str = "feat/test",
) -> SessionState:
    """Create a mock SessionState for testing.

    Args:
        task_id: Task identifier.
        worktree_path: Path to worktree (created as temp if None).
        branch_name: Git branch name.

    Returns:
        SessionState instance suitable for testing.
    """
    if worktree_path is None:
        # Caller should provide actual path; this is fallback
        worktree_path = Path(gettempdir()) / "test-worktree"

    return SessionState(
        task_id=task_id,
        worktree_path=worktree_path,
        branch_name=branch_name,
        started_at=datetime.now(UTC),
    )


def create_mock_quality_state(
    task_id: str = "default",
    test_attempts: int = 0,
    lint_attempts: int = 0,
    review_attempts: int = 0,
    last_review_status: Literal["APPROVED", "REJECTED", "ESCALATED"] | None = None,
    last_review_diff_hash: str | None = None,
) -> QualityGateState:
    """Create a mock QualityGateState for testing.

    Args:
        task_id: Task identifier.
        test_attempts: Number of test attempts.
        lint_attempts: Number of lint attempts.
        review_attempts: Number of review attempts.
        last_review_status: Last review status (APPROVED, REJECTED, ESCALATED).
        last_review_diff_hash: Hash of last reviewed diff.

    Returns:
        QualityGateState instance suitable for testing.
    """
    return QualityGateState(
        task_id=task_id,
        test_attempts=test_attempts,
        lint_attempts=lint_attempts,
        review_attempts=review_attempts,
        last_review_status=last_review_status,
        last_review_diff_hash=last_review_diff_hash,
    )


def create_mock_config(
    max_test_attempts: int = 3,
    max_lint_attempts: int = 3,
    max_format_attempts: int = 3,
    max_review_attempts: int = 5,
    review_model: str = "test-model",
) -> MagicMock:
    """Create a mock config object for quality gate tests.

    Args:
        max_test_attempts: Circuit breaker max for tests.
        max_lint_attempts: Circuit breaker max for lint.
        max_format_attempts: Circuit breaker max for format.
        max_review_attempts: Circuit breaker max for review.
        review_model: Model name for code review.

    Returns:
        MagicMock with config structure expected by quality gates.
    """
    config: Any = MagicMock()
    config.circuit_breakers.tests.max_attempts = max_test_attempts
    config.circuit_breakers.lint.max_attempts = max_lint_attempts
    config.circuit_breakers.format.max_attempts = max_format_attempts
    config.circuit_breakers.review.max_attempts = max_review_attempts
    config.review.model = review_model
    return config
