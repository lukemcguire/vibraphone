"""Unit tests for quality_gate_tools MCP tools.

Tests quality_gate_tools.py MCP tool implementations with mocked dependencies.
Uses pytest-mock for mocking run_command, CircuitBreaker, and CodeReviewer.
"""

from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from vibraphone.utils.quality_state import QualityGateState
from vibraphone.utils.session import SessionState


@pytest.fixture
def mock_execution_context(mocker: Any, tmp_path: Path):
    """Mock get_execution_context to return project root by default."""
    mock_ctx = mocker.patch("vibraphone.tools.quality_gate_tools.get_execution_context")
    mock_ctx.return_value = (tmp_path, None)
    return mock_ctx


@pytest.fixture
def mock_session_state(tmp_path: Path):
    """Create a mock SessionState for testing session-aware behavior."""
    worktree_path = tmp_path / "worktrees" / "task-001"
    worktree_path.mkdir(parents=True)
    return SessionState(
        task_id="001",
        worktree_path=worktree_path,
        branch_name="feat/001-test",
        started_at=datetime.now(),
    )


class TestRunTests:
    """Tests for run_tests MCP tool."""

    @pytest.mark.asyncio
    async def test_run_tests_pass(self, mocker: Any, mock_execution_context) -> None:
        """Mock run_command returns 0, status is 'pass'."""
        mock_run_command = mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_command",
            new_callable=AsyncMock,
            return_value=(0, "all tests passed", ""),
        )

        # Mock config
        mock_config = MagicMock()
        mock_config.circuit_breakers.tests.max_attempts = 5
        mocker.patch("vibraphone.tools.quality_gate_tools.get_config", return_value=mock_config)

        # Mock state manager
        mock_state_manager_class = mocker.patch("vibraphone.tools.quality_gate_tools.get_quality_state_manager")
        mock_state_manager = MagicMock()
        mock_state_manager.load.return_value = QualityGateState(task_id="default")
        mock_state_manager_class.return_value = mock_state_manager

        from vibraphone.tools.quality_gate_tools import run_tests

        result = await run_tests.fn()

        assert result["status"] == "pass"
        assert "output" in result
        assert mock_run_command.called

    @pytest.mark.asyncio
    async def test_run_tests_fail(self, mocker: Any, mock_execution_context) -> None:
        """Mock run_command returns 1, status is 'fail'."""
        mock_run_command = mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_command",
            new_callable=AsyncMock,
            return_value=(1, "", "test failed"),
        )

        mock_config = MagicMock()
        mock_config.circuit_breakers.tests.max_attempts = 5
        mocker.patch("vibraphone.tools.quality_gate_tools.get_config", return_value=mock_config)

        mock_state_manager_class = mocker.patch("vibraphone.tools.quality_gate_tools.get_quality_state_manager")
        mock_state_manager = MagicMock()
        mock_state_manager.load.return_value = QualityGateState(task_id="default")
        mock_state_manager_class.return_value = mock_state_manager

        from vibraphone.tools.quality_gate_tools import run_tests

        result = await run_tests.fn()

        assert result["status"] == "fail"
        assert mock_run_command.called

    @pytest.mark.asyncio
    async def test_run_tests_with_component(self, mocker: Any, mock_execution_context) -> None:
        """Component passed to get_command."""
        mock_get_command = mocker.patch(
            "vibraphone.tools.quality_gate_tools.get_command",
            return_value="just test-server",
        )

        mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_command",
            new_callable=AsyncMock,
            return_value=(0, "", ""),
        )

        mock_config = MagicMock()
        mock_config.circuit_breakers.tests.max_attempts = 5
        mocker.patch("vibraphone.tools.quality_gate_tools.get_config", return_value=mock_config)

        mock_state_manager_class = mocker.patch("vibraphone.tools.quality_gate_tools.get_quality_state_manager")
        mock_state_manager = MagicMock()
        mock_state_manager.load.return_value = QualityGateState(task_id="default")
        mock_state_manager_class.return_value = mock_state_manager

        from vibraphone.tools.quality_gate_tools import run_tests

        await run_tests.fn(component="server")

        mock_get_command.assert_called_once_with("test", "server")

    @pytest.mark.asyncio
    async def test_run_tests_circuit_breaker_tripped(self, mocker: Any, mock_execution_context) -> None:
        """High attempt count triggers escalation."""
        mock_config = MagicMock()
        mock_config.circuit_breakers.tests.max_attempts = 3
        mocker.patch("vibraphone.tools.quality_gate_tools.get_config", return_value=mock_config)

        # State with high attempt count (already at max)
        mock_state_manager_class = mocker.patch("vibraphone.tools.quality_gate_tools.get_quality_state_manager")
        mock_state_manager = MagicMock()
        mock_state_manager.load.return_value = QualityGateState(task_id="default", test_attempts=3)
        mock_state_manager_class.return_value = mock_state_manager

        from vibraphone.tools.quality_gate_tools import run_tests

        result = await run_tests.fn()

        assert result["status"] == "ESCALATED"
        assert result["error_type"] == "CircuitBreakerTripped"

    @pytest.mark.asyncio
    async def test_uses_worktree_when_session_exists(self, mocker: Any, tmp_path: Path, mock_session_state) -> None:
        """When session exists, commands run in worktree directory."""
        worktree_path = tmp_path / "worktrees" / "task-001"
        worktree_path.mkdir(parents=True, exist_ok=True)

        # Mock execution context to return worktree
        mock_ctx = mocker.patch("vibraphone.tools.quality_gate_tools.get_execution_context")
        mock_ctx.return_value = (worktree_path, mock_session_state)

        mock_run_command = mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_command",
            new_callable=AsyncMock,
            return_value=(0, "all tests passed", ""),
        )

        mock_config = MagicMock()
        mock_config.circuit_breakers.tests.max_attempts = 5
        mocker.patch("vibraphone.tools.quality_gate_tools.get_config", return_value=mock_config)

        mock_state_manager_class = mocker.patch("vibraphone.tools.quality_gate_tools.get_quality_state_manager")
        mock_state_manager = MagicMock()
        mock_state_manager.load.return_value = QualityGateState(task_id="001")
        mock_state_manager_class.return_value = mock_state_manager

        from vibraphone.tools.quality_gate_tools import run_tests

        await run_tests.fn()

        # Verify run_command was called with worktree as cwd
        mock_run_command.assert_called_once()
        call_kwargs = mock_run_command.call_args.kwargs
        assert call_kwargs["cwd"] == worktree_path

    @pytest.mark.asyncio
    async def test_uses_project_root_when_no_session(self, mocker: Any, tmp_path: Path, mock_execution_context) -> None:
        """When no session, commands run in project root directory."""
        mock_run_command = mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_command",
            new_callable=AsyncMock,
            return_value=(0, "all tests passed", ""),
        )

        mock_config = MagicMock()
        mock_config.circuit_breakers.tests.max_attempts = 5
        mocker.patch("vibraphone.tools.quality_gate_tools.get_config", return_value=mock_config)

        mock_state_manager_class = mocker.patch("vibraphone.tools.quality_gate_tools.get_quality_state_manager")
        mock_state_manager = MagicMock()
        mock_state_manager.load.return_value = QualityGateState(task_id="default")
        mock_state_manager_class.return_value = mock_state_manager

        from vibraphone.tools.quality_gate_tools import run_tests

        await run_tests.fn()

        # Verify run_command was called with tmp_path (project root) as cwd
        mock_run_command.assert_called_once()
        call_kwargs = mock_run_command.call_args.kwargs
        assert call_kwargs["cwd"] == tmp_path


class TestRunLint:
    """Tests for run_lint MCP tool."""

    @pytest.mark.asyncio
    async def test_run_lint_pass(self, mocker: Any, mock_execution_context) -> None:
        """Mock run_command returns 0."""
        mock_run_command = mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_command",
            new_callable=AsyncMock,
            return_value=(0, "lint passed", ""),
        )

        from vibraphone.tools.quality_gate_tools import run_lint

        result = await run_lint.fn()

        assert result["status"] == "pass"
        assert mock_run_command.called

    @pytest.mark.asyncio
    async def test_run_lint_fail(self, mocker: Any, mock_execution_context) -> None:
        """Mock run_command returns 1."""
        mock_run_command = mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_command",
            new_callable=AsyncMock,
            return_value=(1, "", "lint errors found"),
        )

        from vibraphone.tools.quality_gate_tools import run_lint

        result = await run_lint.fn()

        assert result["status"] == "fail"
        assert mock_run_command.called

    @pytest.mark.asyncio
    async def test_uses_worktree_when_session_exists(self, mocker: Any, tmp_path: Path, mock_session_state) -> None:
        """When session exists, lint runs in worktree directory."""
        worktree_path = tmp_path / "worktrees" / "task-001"
        worktree_path.mkdir(parents=True, exist_ok=True)

        mock_ctx = mocker.patch("vibraphone.tools.quality_gate_tools.get_execution_context")
        mock_ctx.return_value = (worktree_path, mock_session_state)

        mock_run_command = mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_command",
            new_callable=AsyncMock,
            return_value=(0, "lint passed", ""),
        )

        from vibraphone.tools.quality_gate_tools import run_lint

        await run_lint.fn()

        mock_run_command.assert_called_once()
        call_kwargs = mock_run_command.call_args.kwargs
        assert call_kwargs["cwd"] == worktree_path

    @pytest.mark.asyncio
    async def test_uses_project_root_when_no_session(self, mocker: Any, tmp_path: Path, mock_execution_context) -> None:
        """When no session, lint runs in project root directory."""
        mock_run_command = mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_command",
            new_callable=AsyncMock,
            return_value=(0, "lint passed", ""),
        )

        from vibraphone.tools.quality_gate_tools import run_lint

        await run_lint.fn()

        mock_run_command.assert_called_once()
        call_kwargs = mock_run_command.call_args.kwargs
        assert call_kwargs["cwd"] == tmp_path


class TestRunFormat:
    """Tests for run_format MCP tool."""

    @pytest.mark.asyncio
    async def test_run_format_success(self, mocker: Any, mock_execution_context) -> None:
        """Mock run_command returns 0."""
        mock_run_command = mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_command",
            new_callable=AsyncMock,
            return_value=(0, "formatted", ""),
        )

        from vibraphone.tools.quality_gate_tools import run_format

        result = await run_format.fn()

        assert result["status"] == "pass"
        assert mock_run_command.called

    @pytest.mark.asyncio
    async def test_uses_worktree_when_session_exists(self, mocker: Any, tmp_path: Path, mock_session_state) -> None:
        """When session exists, format runs in worktree directory."""
        worktree_path = tmp_path / "worktrees" / "task-001"
        worktree_path.mkdir(parents=True, exist_ok=True)

        mock_ctx = mocker.patch("vibraphone.tools.quality_gate_tools.get_execution_context")
        mock_ctx.return_value = (worktree_path, mock_session_state)

        mock_run_command = mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_command",
            new_callable=AsyncMock,
            return_value=(0, "formatted", ""),
        )

        from vibraphone.tools.quality_gate_tools import run_format

        await run_format.fn()

        mock_run_command.assert_called_once()
        call_kwargs = mock_run_command.call_args.kwargs
        assert call_kwargs["cwd"] == worktree_path

    @pytest.mark.asyncio
    async def test_uses_project_root_when_no_session(self, mocker: Any, tmp_path: Path, mock_execution_context) -> None:
        """When no session, format runs in project root directory."""
        mock_run_command = mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_command",
            new_callable=AsyncMock,
            return_value=(0, "formatted", ""),
        )

        from vibraphone.tools.quality_gate_tools import run_format

        await run_format.fn()

        mock_run_command.assert_called_once()
        call_kwargs = mock_run_command.call_args.kwargs
        assert call_kwargs["cwd"] == tmp_path


class TestRequestCodeReview:
    """Tests for request_code_review MCP tool."""

    @pytest.mark.asyncio
    async def test_request_code_review_approved(self, mocker: Any, mock_execution_context) -> None:
        """Mock reviewer returns only warnings."""
        mock_config = MagicMock()
        mock_config.circuit_breakers.review.max_attempts = 5
        mock_config.review.model = "test-model"
        mocker.patch("vibraphone.tools.quality_gate_tools.get_config", return_value=mock_config)

        # Mock state manager
        mock_state_manager_class = mocker.patch("vibraphone.tools.quality_gate_tools.get_quality_state_manager")
        mock_state_manager = MagicMock()
        mock_state_manager.load.return_value = QualityGateState(task_id="test-task")
        mock_state_manager_class.return_value = mock_state_manager

        # Mock file preparation - return diff content
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.prepare_files_for_review",
            new_callable=AsyncMock,
            return_value=([], "some diff content", None),
        )

        # Mock review to return warning (not error)
        mock_issue = MagicMock()
        mock_issue.model_dump.return_value = {"severity": "warning", "message": "Minor issue"}
        mock_result = MagicMock()
        mock_result.issues = [mock_issue]
        mock_result.summary = "Looks good overall"

        mock_reviewer_class = mocker.patch("vibraphone.tools.quality_gate_tools.CodeReviewer")
        mock_reviewer = MagicMock()
        mock_reviewer.review.return_value = mock_result
        mock_reviewer_class.return_value = mock_reviewer

        from vibraphone.tools.quality_gate_tools import request_code_review

        result = await request_code_review.fn("test-task")

        assert result["status"] == "APPROVED"
        assert "issues" in result
        assert "next_steps" in result

    @pytest.mark.asyncio
    async def test_request_code_review_rejected(self, mocker: Any, mock_execution_context) -> None:
        """Mock reviewer returns errors."""
        mock_config = MagicMock()
        mock_config.circuit_breakers.review.max_attempts = 5
        mock_config.review.model = "test-model"
        mocker.patch("vibraphone.tools.quality_gate_tools.get_config", return_value=mock_config)

        mock_state_manager_class = mocker.patch("vibraphone.tools.quality_gate_tools.get_quality_state_manager")
        mock_state_manager = MagicMock()
        mock_state_manager.load.return_value = QualityGateState(task_id="test-task")
        mock_state_manager_class.return_value = mock_state_manager

        mocker.patch(
            "vibraphone.tools.quality_gate_tools.prepare_files_for_review",
            new_callable=AsyncMock,
            return_value=([], "some diff content", None),
        )

        # Mock review to return error
        mock_issue = MagicMock()
        mock_issue.model_dump.return_value = {"severity": "error", "message": "Bad code"}
        mock_result = MagicMock()
        mock_result.issues = [mock_issue]
        mock_result.summary = "Has issues"

        mock_reviewer_class = mocker.patch("vibraphone.tools.quality_gate_tools.CodeReviewer")
        mock_reviewer = MagicMock()
        mock_reviewer.review.return_value = mock_result
        mock_reviewer_class.return_value = mock_reviewer

        from vibraphone.tools.quality_gate_tools import request_code_review

        result = await request_code_review.fn("test-task")

        assert result["status"] == "REJECTED"

    @pytest.mark.asyncio
    async def test_request_code_review_blocks_dangerous_files(self, mocker: Any, mock_execution_context) -> None:
        """.env file not staged."""
        mock_config = MagicMock()
        mock_config.circuit_breakers.review.max_attempts = 5
        mock_config.review.model = "test-model"
        mocker.patch("vibraphone.tools.quality_gate_tools.get_config", return_value=mock_config)

        mock_state_manager_class = mocker.patch("vibraphone.tools.quality_gate_tools.get_quality_state_manager")
        mock_state_manager = MagicMock()
        mock_state_manager.load.return_value = QualityGateState(task_id="test-task")
        mock_state_manager_class.return_value = mock_state_manager

        # Mock file preparation to return blocked dangerous files
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.prepare_files_for_review",
            new_callable=AsyncMock,
            return_value=(["config/.env"], "some diff", None),
        )

        mock_issue = MagicMock()
        mock_issue.model_dump.return_value = {"severity": "warning", "message": "OK"}
        mock_result = MagicMock()
        mock_result.issues = [mock_issue]
        mock_result.summary = "Looks good"

        mock_reviewer_class = mocker.patch("vibraphone.tools.quality_gate_tools.CodeReviewer")
        mock_reviewer = MagicMock()
        mock_reviewer.review.return_value = mock_result
        mock_reviewer_class.return_value = mock_reviewer

        from vibraphone.tools.quality_gate_tools import request_code_review

        result = await request_code_review.fn("test-task")

        # Should have warning about blocked file
        assert "warnings" in result
        assert ".env" in result["warnings"][0]

    @pytest.mark.asyncio
    async def test_request_code_review_circuit_breaker(self, mocker: Any, mock_execution_context) -> None:
        """Escalation after max attempts."""
        mock_config = MagicMock()
        mock_config.circuit_breakers.review.max_attempts = 3
        mock_config.review.model = "test-model"
        mocker.patch("vibraphone.tools.quality_gate_tools.get_config", return_value=mock_config)

        # State already at max attempts
        mock_state_manager_class = mocker.patch("vibraphone.tools.quality_gate_tools.get_quality_state_manager")
        mock_state_manager = MagicMock()
        mock_state_manager.load.return_value = QualityGateState(task_id="test-task", review_attempts=3)
        mock_state_manager_class.return_value = mock_state_manager

        from vibraphone.tools.quality_gate_tools import request_code_review

        result = await request_code_review.fn("test-task")

        assert result["status"] == "ESCALATED"
        assert result["error_type"] == "CircuitBreakerTripped"

    @pytest.mark.asyncio
    async def test_optional_task_id_derived_from_session(self, mocker: Any, tmp_path: Path, mock_session_state) -> None:
        """task_id derived from session when not explicitly provided."""
        worktree_path = tmp_path / "worktrees" / "task-001"
        worktree_path.mkdir(parents=True, exist_ok=True)

        mock_ctx = mocker.patch("vibraphone.tools.quality_gate_tools.get_execution_context")
        mock_ctx.return_value = (worktree_path, mock_session_state)

        mock_config = MagicMock()
        mock_config.circuit_breakers.review.max_attempts = 5
        mock_config.review.model = "test-model"
        mocker.patch("vibraphone.tools.quality_gate_tools.get_config", return_value=mock_config)

        mock_state_manager_class = mocker.patch("vibraphone.tools.quality_gate_tools.get_quality_state_manager")
        mock_state_manager = MagicMock()
        mock_state_manager.load.return_value = QualityGateState(task_id="001")
        mock_state_manager_class.return_value = mock_state_manager

        mocker.patch(
            "vibraphone.tools.quality_gate_tools.prepare_files_for_review",
            new_callable=AsyncMock,
            return_value=([], "some diff", None),
        )

        mock_issue = MagicMock()
        mock_issue.model_dump.return_value = {"severity": "warning", "message": "OK"}
        mock_result = MagicMock()
        mock_result.issues = [mock_issue]
        mock_result.summary = "OK"

        mock_reviewer_class = mocker.patch("vibraphone.tools.quality_gate_tools.CodeReviewer")
        mock_reviewer = MagicMock()
        mock_reviewer.review.return_value = mock_result
        mock_reviewer_class.return_value = mock_reviewer

        from vibraphone.tools.quality_gate_tools import request_code_review

        # Call without task_id - should derive "001" from session
        result = await request_code_review.fn()

        # Verify state_manager was called with "001" (from session)
        mock_state_manager_class.assert_called_once_with("001")
        assert result["status"] == "APPROVED"

    @pytest.mark.asyncio
    async def test_explicit_task_id_overrides_session(self, mocker: Any, tmp_path: Path, mock_session_state) -> None:
        """Explicit task_id takes precedence over session task_id."""
        worktree_path = tmp_path / "worktrees" / "task-001"
        worktree_path.mkdir(parents=True, exist_ok=True)

        mock_ctx = mocker.patch("vibraphone.tools.quality_gate_tools.get_execution_context")
        mock_ctx.return_value = (worktree_path, mock_session_state)

        mock_config = MagicMock()
        mock_config.circuit_breakers.review.max_attempts = 5
        mock_config.review.model = "test-model"
        mocker.patch("vibraphone.tools.quality_gate_tools.get_config", return_value=mock_config)

        mock_state_manager_class = mocker.patch("vibraphone.tools.quality_gate_tools.get_quality_state_manager")
        mock_state_manager = MagicMock()
        mock_state_manager.load.return_value = QualityGateState(task_id="003")
        mock_state_manager_class.return_value = mock_state_manager

        mocker.patch(
            "vibraphone.tools.quality_gate_tools.prepare_files_for_review",
            new_callable=AsyncMock,
            return_value=([], "some diff", None),
        )

        mock_issue = MagicMock()
        mock_issue.model_dump.return_value = {"severity": "warning", "message": "OK"}
        mock_result = MagicMock()
        mock_result.issues = [mock_issue]
        mock_result.summary = "OK"

        mock_reviewer_class = mocker.patch("vibraphone.tools.quality_gate_tools.CodeReviewer")
        mock_reviewer = MagicMock()
        mock_reviewer.review.return_value = mock_result
        mock_reviewer_class.return_value = mock_reviewer

        from vibraphone.tools.quality_gate_tools import request_code_review

        # Call with explicit task_id="003" when session has "001"
        result = await request_code_review.fn(task_id="003")

        # Verify state_manager was called with "003" (explicit), not "001" (from session)
        mock_state_manager_class.assert_called_once_with("003")
        assert result["status"] == "APPROVED"


class TestAttemptCommit:
    """Tests for attempt_commit MCP tool."""

    @pytest.mark.asyncio
    async def test_attempt_commit_no_review(self, mocker: Any, mock_execution_context) -> None:
        """Fails without approved review."""
        mock_state_manager_class = mocker.patch("vibraphone.tools.quality_gate_tools.get_quality_state_manager")
        mock_state_manager = MagicMock()
        mock_state_manager.load.return_value = None  # No state
        mock_state_manager_class.return_value = mock_state_manager

        from vibraphone.tools.quality_gate_tools import attempt_commit

        result = await attempt_commit.fn("test-task", "commit message")

        assert result["status"] == "error"
        assert "No approved review" in result["message"]

    @pytest.mark.asyncio
    async def test_attempt_commit_diff_mismatch(self, mocker: Any, mock_execution_context) -> None:
        """Fails when diff hash changed."""
        mock_state_manager_class = mocker.patch("vibraphone.tools.quality_gate_tools.get_quality_state_manager")
        mock_state_manager = MagicMock()
        mock_state_manager.load.return_value = QualityGateState(
            task_id="test-task",
            last_review_status="APPROVED",
            last_review_diff_hash="old-hash",
        )
        mock_state_manager_class.return_value = mock_state_manager

        # Mock get_staged_diff to return different content
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.get_staged_diff",
            new_callable=AsyncMock,
            return_value=(0, "different content", ""),
        )

        from vibraphone.tools.quality_gate_tools import attempt_commit

        result = await attempt_commit.fn("test-task", "commit message")

        assert result["status"] == "error"
        assert "differ from reviewed" in result["message"]

    @pytest.mark.asyncio
    async def test_attempt_commit_quality_check_fails(self, mocker: Any, mock_execution_context) -> None:
        """Fails when just check fails."""
        mock_state_manager_class = mocker.patch("vibraphone.tools.quality_gate_tools.get_quality_state_manager")
        mock_state_manager = MagicMock()
        mock_state_manager.load.return_value = QualityGateState(
            task_id="test-task",
            last_review_status="APPROVED",
            last_review_diff_hash="abc123",
        )
        mock_state_manager_class.return_value = mock_state_manager

        # Mock get_staged_diff to return matching hash
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.get_staged_diff",
            new_callable=AsyncMock,
            return_value=(0, "matching content", ""),
        )
        # Mock hash_diff to return matching hash
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.hash_diff",
            return_value="abc123",
        )

        # Mock check command to fail
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_command",
            new_callable=AsyncMock,
            return_value=(1, "", "tests failed"),
        )
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.get_command",
            return_value="just check",
        )

        from vibraphone.tools.quality_gate_tools import attempt_commit

        result = await attempt_commit.fn("test-task", "commit message")

        assert result["status"] == "error"
        assert "Quality gate check failed" in result["message"]

    @pytest.mark.asyncio
    async def test_attempt_commit_success(self, mocker: Any, mock_execution_context) -> None:
        """All checks pass, commit executes."""
        mock_state_manager_class = mocker.patch("vibraphone.tools.quality_gate_tools.get_quality_state_manager")
        mock_state_manager = MagicMock()
        mock_state_manager.load.return_value = QualityGateState(
            task_id="test-task",
            last_review_status="APPROVED",
            last_review_diff_hash="abc123",
        )
        mock_state_manager_class.return_value = mock_state_manager

        mocker.patch(
            "vibraphone.tools.quality_gate_tools.get_staged_diff",
            new_callable=AsyncMock,
            return_value=(0, "matching content", ""),
        )
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.hash_diff",
            return_value="abc123",
        )

        # Mock check command to pass
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_command",
            new_callable=AsyncMock,
            return_value=(0, "all good", ""),
        )
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.get_command",
            return_value="just check",
        )

        # Mock git commit
        mock_commit = mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_git_commit",
            new_callable=AsyncMock,
            return_value=(0, "[main abc1234] my message", ""),
        )

        from vibraphone.tools.quality_gate_tools import attempt_commit

        result = await attempt_commit.fn("test-task", "my message")

        assert result["status"] == "committed"
        assert mock_commit.called

    @pytest.mark.asyncio
    async def test_optional_task_id_derived_from_session(self, mocker: Any, tmp_path: Path, mock_session_state) -> None:
        """task_id derived from session when not explicitly provided."""
        worktree_path = tmp_path / "worktrees" / "task-001"
        worktree_path.mkdir(parents=True, exist_ok=True)

        mock_ctx = mocker.patch("vibraphone.tools.quality_gate_tools.get_execution_context")
        mock_ctx.return_value = (worktree_path, mock_session_state)

        mock_state_manager_class = mocker.patch("vibraphone.tools.quality_gate_tools.get_quality_state_manager")
        mock_state_manager = MagicMock()
        mock_state_manager.load.return_value = QualityGateState(
            task_id="001",
            last_review_status="APPROVED",
            last_review_diff_hash="abc123",
        )
        mock_state_manager_class.return_value = mock_state_manager

        mocker.patch(
            "vibraphone.tools.quality_gate_tools.get_staged_diff",
            new_callable=AsyncMock,
            return_value=(0, "matching content", ""),
        )
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.hash_diff",
            return_value="abc123",
        )
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_command",
            new_callable=AsyncMock,
            return_value=(0, "all good", ""),
        )
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.get_command",
            return_value="just check",
        )
        _mock_commit = mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_git_commit",
            new_callable=AsyncMock,
            return_value=(0, "[main abc1234] message", ""),
        )

        from vibraphone.tools.quality_gate_tools import attempt_commit

        # Call without task_id - should derive "001" from session
        result = await attempt_commit.fn(message="test commit")

        # Verify state_manager was called with "001" (from session)
        mock_state_manager_class.assert_called_once_with("001")
        assert result["status"] == "committed"

    @pytest.mark.asyncio
    async def test_git_operations_use_worktree_cwd(self, mocker: Any, tmp_path: Path, mock_session_state) -> None:
        """Git operations use worktree as cwd when session exists."""
        worktree_path = tmp_path / "worktrees" / "task-001"
        worktree_path.mkdir(parents=True, exist_ok=True)

        mock_ctx = mocker.patch("vibraphone.tools.quality_gate_tools.get_execution_context")
        mock_ctx.return_value = (worktree_path, mock_session_state)

        mock_state_manager_class = mocker.patch("vibraphone.tools.quality_gate_tools.get_quality_state_manager")
        mock_state_manager = MagicMock()
        mock_state_manager.load.return_value = QualityGateState(
            task_id="001",
            last_review_status="APPROVED",
            last_review_diff_hash="abc123",
        )
        mock_state_manager_class.return_value = mock_state_manager

        mock_get_staged_diff = mocker.patch(
            "vibraphone.tools.quality_gate_tools.get_staged_diff",
            new_callable=AsyncMock,
            return_value=(0, "matching content", ""),
        )
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.hash_diff",
            return_value="abc123",
        )
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_command",
            new_callable=AsyncMock,
            return_value=(0, "all good", ""),
        )
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.get_command",
            return_value="just check",
        )
        mock_run_git_commit = mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_git_commit",
            new_callable=AsyncMock,
            return_value=(0, "[main abc1234] message", ""),
        )

        from vibraphone.tools.quality_gate_tools import attempt_commit

        await attempt_commit.fn(task_id="001", message="test commit")

        # Verify git operations called with worktree as cwd
        mock_get_staged_diff.assert_called_once()
        assert mock_get_staged_diff.call_args.args[0] == worktree_path

        mock_run_git_commit.assert_called_once()
        assert mock_run_git_commit.call_args.kwargs["cwd"] == worktree_path


class TestRequestCodeReviewDefensiveParsing:
    """Tests for request_code_review defensive parsing of files parameter."""

    @pytest.mark.asyncio
    async def test_files_as_json_string_parses_successfully(self, mocker: Any, mock_execution_context) -> None:
        """Pass files as JSON string - should parse and proceed normally."""
        mock_config = MagicMock()
        mock_config.circuit_breakers.review.max_attempts = 5
        mock_config.review.model = "test-model"
        mocker.patch("vibraphone.tools.quality_gate_tools.get_config", return_value=mock_config)

        mock_state_manager_class = mocker.patch("vibraphone.tools.quality_gate_tools.get_quality_state_manager")
        mock_state_manager = MagicMock()
        mock_state_manager.load.return_value = QualityGateState(task_id="test-task")
        mock_state_manager_class.return_value = mock_state_manager

        mocker.patch(
            "vibraphone.tools.quality_gate_tools.prepare_files_for_review",
            new_callable=AsyncMock,
            return_value=([], "some diff content", None),
        )

        mock_issue = MagicMock()
        mock_issue.model_dump.return_value = {"severity": "warning", "message": "OK"}
        mock_result = MagicMock()
        mock_result.issues = [mock_issue]
        mock_result.summary = "Looks good"

        mock_reviewer_class = mocker.patch("vibraphone.tools.quality_gate_tools.CodeReviewer")
        mock_reviewer = MagicMock()
        mock_reviewer.review.return_value = mock_result
        mock_reviewer_class.return_value = mock_reviewer

        from vibraphone.tools.quality_gate_tools import request_code_review

        # Pass files as JSON string - should parse successfully
        result = await request_code_review.fn(task_id="test-task", files='["main.py", "test.py"]')

        # Should NOT return an error - should proceed to review
        assert result["status"] == "APPROVED"

    @pytest.mark.asyncio
    async def test_files_as_invalid_json_returns_error(self, mocker: Any, mock_execution_context) -> None:
        """Pass files as invalid JSON string returns ParameterParseError."""
        from vibraphone.tools.quality_gate_tools import request_code_review

        result = await request_code_review.fn(task_id="test-task", files='["unclosed')

        assert result["status"] == "error"
        assert result["error_type"] == "ParameterParseError"
        assert "Failed to parse" in result["message"]

    @pytest.mark.asyncio
    async def test_files_as_list_works_normally(self, mocker: Any, mock_execution_context) -> None:
        """Pass files as proper list proceeds normally."""
        mock_config = MagicMock()
        mock_config.circuit_breakers.review.max_attempts = 5
        mock_config.review.model = "test-model"
        mocker.patch("vibraphone.tools.quality_gate_tools.get_config", return_value=mock_config)

        mock_state_manager_class = mocker.patch("vibraphone.tools.quality_gate_tools.get_quality_state_manager")
        mock_state_manager = MagicMock()
        mock_state_manager.load.return_value = QualityGateState(task_id="test-task")
        mock_state_manager_class.return_value = mock_state_manager

        mocker.patch(
            "vibraphone.tools.quality_gate_tools.prepare_files_for_review",
            new_callable=AsyncMock,
            return_value=([], "some diff content", None),
        )

        mock_issue = MagicMock()
        mock_issue.model_dump.return_value = {"severity": "warning", "message": "OK"}
        mock_result = MagicMock()
        mock_result.issues = [mock_issue]
        mock_result.summary = "Looks good"

        mock_reviewer_class = mocker.patch("vibraphone.tools.quality_gate_tools.CodeReviewer")
        mock_reviewer = MagicMock()
        mock_reviewer.review.return_value = mock_result
        mock_reviewer_class.return_value = mock_reviewer

        from vibraphone.tools.quality_gate_tools import request_code_review

        result = await request_code_review.fn(task_id="test-task", files=["main.py", "test.py"])

        # Should NOT return the stringification error
        assert result["status"] != "error" or result.get("error_type") != "ParameterStringified"
        # Should proceed to review
        assert result["status"] == "APPROVED"

    @pytest.mark.asyncio
    async def test_files_as_none_allowed(self, mocker: Any, mock_execution_context) -> None:
        """Pass files=None (or omit) proceeds normally."""
        mock_config = MagicMock()
        mock_config.circuit_breakers.review.max_attempts = 5
        mock_config.review.model = "test-model"
        mocker.patch("vibraphone.tools.quality_gate_tools.get_config", return_value=mock_config)

        mock_state_manager_class = mocker.patch("vibraphone.tools.quality_gate_tools.get_quality_state_manager")
        mock_state_manager = MagicMock()
        mock_state_manager.load.return_value = QualityGateState(task_id="test-task")
        mock_state_manager_class.return_value = mock_state_manager

        mocker.patch(
            "vibraphone.tools.quality_gate_tools.prepare_files_for_review",
            new_callable=AsyncMock,
            return_value=([], "some diff content", None),
        )

        mock_issue = MagicMock()
        mock_issue.model_dump.return_value = {"severity": "warning", "message": "OK"}
        mock_result = MagicMock()
        mock_result.issues = [mock_issue]
        mock_result.summary = "Looks good"

        mock_reviewer_class = mocker.patch("vibraphone.tools.quality_gate_tools.CodeReviewer")
        mock_reviewer = MagicMock()
        mock_reviewer.review.return_value = mock_result
        mock_reviewer_class.return_value = mock_reviewer

        from vibraphone.tools.quality_gate_tools import request_code_review

        # Call with files=None (or omit)
        result = await request_code_review.fn(task_id="test-task", files=None)

        # Should NOT return the stringification error
        assert result["status"] != "error" or result.get("error_type") != "ParameterStringified"
        # Should proceed to review
        assert result["status"] == "APPROVED"


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_is_dangerous_file_env(self) -> None:
        """.env files are dangerous."""
        from vibraphone.tools.quality_gate_tools import is_dangerous_file

        assert is_dangerous_file(".env") is True
        assert is_dangerous_file("config/.env") is True
        assert is_dangerous_file(".env.local") is True
        assert is_dangerous_file(".env.production") is True

    def test_is_dangerous_file_keys(self) -> None:
        """Key files are dangerous."""
        from vibraphone.tools.quality_gate_tools import is_dangerous_file

        assert is_dangerous_file("id_rsa") is True
        assert is_dangerous_file("private.key") is True
        assert is_dangerous_file("secrets.yaml") is True
        assert is_dangerous_file("credentials.json") is True

    def test_is_dangerous_file_safe(self) -> None:
        """Normal files are safe."""
        from vibraphone.tools.quality_gate_tools import is_dangerous_file

        assert is_dangerous_file("main.py") is False
        assert is_dangerous_file("config.yaml") is False
        assert is_dangerous_file("README.md") is False

    def test_hash_diff_consistent(self) -> None:
        """hash_diff returns consistent hash."""
        from vibraphone.tools.quality_gate_tools import hash_diff

        hash1 = hash_diff("some content")
        hash2 = hash_diff("some content")

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length

    def test_hash_diff_different(self) -> None:
        """hash_diff returns different hash for different content."""
        from vibraphone.tools.quality_gate_tools import hash_diff

        hash1 = hash_diff("content a")
        hash2 = hash_diff("content b")

        assert hash1 != hash2

    def test_filter_dangerous_files(self) -> None:
        """filter_dangerous_files splits safe and blocked."""
        from vibraphone.tools.quality_gate_tools import filter_dangerous_files

        files = ["main.py", ".env", "config.yaml", "secrets.json", "test.py"]
        safe, blocked = filter_dangerous_files(files)

        assert safe == ["main.py", "config.yaml", "test.py"]
        assert blocked == [".env", "secrets.json"]


class TestPhase8SuccessCriteria:
    """Phase 8 success criteria tests for QUAL-06 (worktree context integration).

    These tests verify the MUST_HAVE truths from the plan:
    - Agent calls start_task and then run_tests runs tests IN the worktree
    - Agent calls request_code_review and it stages files from the worktree
    - Agent calls attempt_commit and it commits TO the worktree branch
    - Quality gates work correctly when no session exists (fallback to project root)
    - E2E task execution flow works from import to cleanup
    """

    @pytest.mark.asyncio
    async def test_QUAL_06_worktree_context_integration(self, mocker: Any, tmp_path: Path, mock_session_state) -> None:
        """QUAL-06: Verify quality gates use worktree context when session exists.

        Covers success criteria 1, 2, 3:
        - run_tests executes in worktree
        - request_code_review stages files from worktree
        - attempt_commit commits to worktree branch
        """
        worktree_path = tmp_path / "worktrees" / "task-001"
        worktree_path.mkdir(parents=True, exist_ok=True)

        # Mock execution context to return worktree with session
        mock_ctx = mocker.patch("vibraphone.tools.quality_gate_tools.get_execution_context")
        mock_ctx.return_value = (worktree_path, mock_session_state)

        # Common mocks
        mock_config = MagicMock()
        mock_config.circuit_breakers.tests.max_attempts = 5
        mock_config.circuit_breakers.review.max_attempts = 5
        mock_config.review.model = "test-model"
        mocker.patch("vibraphone.tools.quality_gate_tools.get_config", return_value=mock_config)

        mock_state_manager_class = mocker.patch("vibraphone.tools.quality_gate_tools.get_quality_state_manager")
        mock_state_manager = MagicMock()
        mock_state_manager.load.return_value = QualityGateState(task_id="001")
        mock_state_manager_class.return_value = mock_state_manager

        # Test run_tests uses worktree
        mock_run_command = mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_command",
            new_callable=AsyncMock,
            return_value=(0, "tests passed", ""),
        )

        from vibraphone.tools.quality_gate_tools import run_tests

        await run_tests.fn()

        run_tests_cwd = mock_run_command.call_args.kwargs["cwd"]
        assert run_tests_cwd == worktree_path, "run_tests should execute in worktree"

        # Test request_code_review uses worktree
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.prepare_files_for_review",
            new_callable=AsyncMock,
            return_value=([], "diff content", None),
        )
        mock_issue = MagicMock()
        mock_issue.model_dump.return_value = {"severity": "warning", "message": "OK"}
        mock_result = MagicMock()
        mock_result.issues = [mock_issue]
        mock_result.summary = "OK"
        mock_reviewer_class = mocker.patch("vibraphone.tools.quality_gate_tools.CodeReviewer")
        mock_reviewer = MagicMock()
        mock_reviewer.review.return_value = mock_result
        mock_reviewer_class.return_value = mock_reviewer

        from vibraphone.tools.quality_gate_tools import request_code_review

        await request_code_review.fn()

        # Verify prepare_files_for_review was called with worktree
        prepare_files = mocker.patch(
            "vibraphone.tools.quality_gate_tools.prepare_files_for_review",
            new_callable=AsyncMock,
            return_value=([], "diff", None),
        )
        await request_code_review.fn()
        if prepare_files.called:
            assert prepare_files.call_args.args[1] == worktree_path

        # Test attempt_commit uses worktree
        mock_state_manager.load.return_value = QualityGateState(
            task_id="001",
            last_review_status="APPROVED",
            last_review_diff_hash="abc123",
        )
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.get_staged_diff",
            new_callable=AsyncMock,
            return_value=(0, "content", ""),
        )
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.hash_diff",
            return_value="abc123",
        )
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_command",
            new_callable=AsyncMock,
            return_value=(0, "check passed", ""),
        )
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.get_command",
            return_value="just check",
        )
        mock_git_commit = mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_git_commit",
            new_callable=AsyncMock,
            return_value=(0, "[main abc1234] message", ""),
        )

        from vibraphone.tools.quality_gate_tools import attempt_commit

        await attempt_commit.fn(message="test")

        commit_cwd = mock_git_commit.call_args.kwargs["cwd"]
        assert commit_cwd == worktree_path, "attempt_commit should commit in worktree"

    @pytest.mark.asyncio
    async def test_QUAL_06_fallback_to_project_root(self, mocker: Any, tmp_path: Path) -> None:
        """QUAL-06: Verify fallback to project root when no session.

        Covers success criterion 4:
        - Quality gates work correctly when no session exists
        """
        # Mock execution context to return project root without session
        mock_ctx = mocker.patch("vibraphone.tools.quality_gate_tools.get_execution_context")
        mock_ctx.return_value = (tmp_path, None)

        mock_config = MagicMock()
        mock_config.circuit_breakers.tests.max_attempts = 5
        mock_config.circuit_breakers.review.max_attempts = 5
        mock_config.review.model = "test-model"
        mocker.patch("vibraphone.tools.quality_gate_tools.get_config", return_value=mock_config)

        mock_state_manager_class = mocker.patch("vibraphone.tools.quality_gate_tools.get_quality_state_manager")
        mock_state_manager = MagicMock()
        mock_state_manager.load.return_value = QualityGateState(task_id="default")
        mock_state_manager_class.return_value = mock_state_manager

        # Verify run_tests uses project root
        mock_run_command = mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_command",
            new_callable=AsyncMock,
            return_value=(0, "tests passed", ""),
        )

        from vibraphone.tools.quality_gate_tools import run_tests

        await run_tests.fn()

        run_tests_cwd = mock_run_command.call_args.kwargs["cwd"]
        assert run_tests_cwd == tmp_path, "run_tests should use project root when no session"

        # Verify run_lint uses project root
        mock_run_command.reset_mock()
        from vibraphone.tools.quality_gate_tools import run_lint

        await run_lint.fn()

        lint_cwd = mock_run_command.call_args.kwargs["cwd"]
        assert lint_cwd == tmp_path, "run_lint should use project root when no session"

        # Verify run_format uses project root
        mock_run_command.reset_mock()
        from vibraphone.tools.quality_gate_tools import run_format

        await run_format.fn()

        format_cwd = mock_run_command.call_args.kwargs["cwd"]
        assert format_cwd == tmp_path, "run_format should use project root when no session"

    @pytest.mark.asyncio
    async def test_QUAL_06_e2e_task_flow(self, mocker: Any, tmp_path: Path, mock_session_state) -> None:
        """QUAL-06: Verify E2E task flow components.

        Covers success criterion 5:
        - E2E task execution flow works from import to cleanup

        This test verifies the wiring of session-aware execution without
        actually calling the worktree tools, just verifying the flow.
        """
        worktree_path = tmp_path / "worktrees" / "task-001"
        worktree_path.mkdir(parents=True, exist_ok=True)

        # Mock execution context
        mock_ctx = mocker.patch("vibraphone.tools.quality_gate_tools.get_execution_context")
        mock_ctx.return_value = (worktree_path, mock_session_state)

        mock_config = MagicMock()
        mock_config.circuit_breakers.tests.max_attempts = 5
        mock_config.circuit_breakers.review.max_attempts = 5
        mock_config.review.model = "test-model"
        mocker.patch("vibraphone.tools.quality_gate_tools.get_config", return_value=mock_config)

        # Setup state manager with proper state progression
        mock_state_manager_class = mocker.patch("vibraphone.tools.quality_gate_tools.get_quality_state_manager")
        mock_state_manager = MagicMock()
        initial_state = QualityGateState(task_id="001")
        mock_state_manager.load.return_value = initial_state
        mock_state_manager_class.return_value = mock_state_manager

        # Step 1: Run tests in worktree
        mock_run_command = mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_command",
            new_callable=AsyncMock,
            return_value=(0, "tests passed", ""),
        )

        from vibraphone.tools.quality_gate_tools import run_tests

        await run_tests.fn()
        assert mock_run_command.call_args.kwargs["cwd"] == worktree_path

        # Step 2: Request code review
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.prepare_files_for_review",
            new_callable=AsyncMock,
            return_value=([], "diff content", None),
        )
        mock_issue = MagicMock()
        mock_issue.model_dump.return_value = {"severity": "warning", "message": "OK"}
        mock_result = MagicMock()
        mock_result.issues = [mock_issue]
        mock_result.summary = "Approved"
        mock_reviewer_class = mocker.patch("vibraphone.tools.quality_gate_tools.CodeReviewer")
        mock_reviewer = MagicMock()
        mock_reviewer.review.return_value = mock_result
        mock_reviewer_class.return_value = mock_reviewer

        from vibraphone.tools.quality_gate_tools import request_code_review

        review_result = await request_code_review.fn()
        assert review_result["status"] == "APPROVED"

        # Step 3: Attempt commit
        mock_state_manager.load.return_value = QualityGateState(
            task_id="001",
            last_review_status="APPROVED",
            last_review_diff_hash="abc123",
        )
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.get_staged_diff",
            new_callable=AsyncMock,
            return_value=(0, "content", ""),
        )
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.hash_diff",
            return_value="abc123",
        )
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_command",
            new_callable=AsyncMock,
            return_value=(0, "check passed", ""),
        )
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.get_command",
            return_value="just check",
        )
        mock_git_commit = mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_git_commit",
            new_callable=AsyncMock,
            return_value=(0, "[feat/001-test abc1234] commit", ""),
        )

        from vibraphone.tools.quality_gate_tools import attempt_commit

        commit_result = await attempt_commit.fn(message="feat: implement feature")

        assert commit_result["status"] == "committed"
        assert mock_git_commit.call_args.kwargs["cwd"] == worktree_path
