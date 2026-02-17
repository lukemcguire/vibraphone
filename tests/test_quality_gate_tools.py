"""Unit tests for quality_gate_tools MCP tools.

Tests quality_gate_tools.py MCP tool implementations with mocked dependencies.
Uses pytest-mock for mocking run_command, CircuitBreaker, and CodeReviewer.
"""

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from vibraphone.utils.quality_state import QualityGateState


class TestRunTests:
    """Tests for run_tests MCP tool."""

    @pytest.mark.asyncio
    async def test_run_tests_pass(self, mocker: Any, tmp_path: Path) -> None:
        """Mock run_command returns 0, status is 'pass'."""
        mock_run_command = mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_command",
            new_callable=AsyncMock,
            return_value=(0, "all tests passed", ""),
        )

        mocker.patch("vibraphone.tools.quality_gate_tools.get_project_root", return_value=tmp_path)

        # Mock config
        mock_config = MagicMock()
        mock_config.circuit_breakers.tests.max_attempts = 5
        mocker.patch("vibraphone.tools.quality_gate_tools.get_config", return_value=mock_config)

        # Mock state manager
        mock_state_manager_class = mocker.patch(
            "vibraphone.tools.quality_gate_tools.get_quality_state_manager"
        )
        mock_state_manager = MagicMock()
        mock_state_manager.load.return_value = QualityGateState(task_id="default")
        mock_state_manager_class.return_value = mock_state_manager

        from vibraphone.tools.quality_gate_tools import run_tests

        result = await run_tests.fn()

        assert result["status"] == "pass"
        assert "output" in result
        assert mock_run_command.called

    @pytest.mark.asyncio
    async def test_run_tests_fail(self, mocker: Any, tmp_path: Path) -> None:
        """Mock run_command returns 1, status is 'fail'."""
        mock_run_command = mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_command",
            new_callable=AsyncMock,
            return_value=(1, "", "test failed"),
        )

        mocker.patch("vibraphone.tools.quality_gate_tools.get_project_root", return_value=tmp_path)

        mock_config = MagicMock()
        mock_config.circuit_breakers.tests.max_attempts = 5
        mocker.patch("vibraphone.tools.quality_gate_tools.get_config", return_value=mock_config)

        mock_state_manager_class = mocker.patch(
            "vibraphone.tools.quality_gate_tools.get_quality_state_manager"
        )
        mock_state_manager = MagicMock()
        mock_state_manager.load.return_value = QualityGateState(task_id="default")
        mock_state_manager_class.return_value = mock_state_manager

        from vibraphone.tools.quality_gate_tools import run_tests

        result = await run_tests.fn()

        assert result["status"] == "fail"
        assert mock_run_command.called

    @pytest.mark.asyncio
    async def test_run_tests_with_component(self, mocker: Any, tmp_path: Path) -> None:
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
        mocker.patch("vibraphone.tools.quality_gate_tools.get_project_root", return_value=tmp_path)

        mock_config = MagicMock()
        mock_config.circuit_breakers.tests.max_attempts = 5
        mocker.patch("vibraphone.tools.quality_gate_tools.get_config", return_value=mock_config)

        mock_state_manager_class = mocker.patch(
            "vibraphone.tools.quality_gate_tools.get_quality_state_manager"
        )
        mock_state_manager = MagicMock()
        mock_state_manager.load.return_value = QualityGateState(task_id="default")
        mock_state_manager_class.return_value = mock_state_manager

        from vibraphone.tools.quality_gate_tools import run_tests

        await run_tests.fn(component="server")

        mock_get_command.assert_called_once_with("test", "server")

    @pytest.mark.asyncio
    async def test_run_tests_circuit_breaker_tripped(self, mocker: Any, tmp_path: Path) -> None:
        """High attempt count triggers escalation."""
        mocker.patch("vibraphone.tools.quality_gate_tools.get_project_root", return_value=tmp_path)

        mock_config = MagicMock()
        mock_config.circuit_breakers.tests.max_attempts = 3
        mocker.patch("vibraphone.tools.quality_gate_tools.get_config", return_value=mock_config)

        # State with high attempt count (already at max)
        mock_state_manager_class = mocker.patch(
            "vibraphone.tools.quality_gate_tools.get_quality_state_manager"
        )
        mock_state_manager = MagicMock()
        mock_state_manager.load.return_value = QualityGateState(
            task_id="default", test_attempts=3
        )
        mock_state_manager_class.return_value = mock_state_manager

        from vibraphone.tools.quality_gate_tools import run_tests

        result = await run_tests.fn()

        assert result["status"] == "ESCALATED"
        assert result["error_type"] == "CircuitBreakerTripped"


class TestRunLint:
    """Tests for run_lint MCP tool."""

    @pytest.mark.asyncio
    async def test_run_lint_pass(self, mocker: Any, tmp_path: Path) -> None:
        """Mock run_command returns 0."""
        mock_run_command = mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_command",
            new_callable=AsyncMock,
            return_value=(0, "lint passed", ""),
        )

        mocker.patch("vibraphone.tools.quality_gate_tools.get_project_root", return_value=tmp_path)

        from vibraphone.tools.quality_gate_tools import run_lint

        result = await run_lint.fn()

        assert result["status"] == "pass"
        assert mock_run_command.called

    @pytest.mark.asyncio
    async def test_run_lint_fail(self, mocker: Any, tmp_path: Path) -> None:
        """Mock run_command returns 1."""
        mock_run_command = mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_command",
            new_callable=AsyncMock,
            return_value=(1, "", "lint errors found"),
        )

        mocker.patch("vibraphone.tools.quality_gate_tools.get_project_root", return_value=tmp_path)

        from vibraphone.tools.quality_gate_tools import run_lint

        result = await run_lint.fn()

        assert result["status"] == "fail"
        assert mock_run_command.called


class TestRunFormat:
    """Tests for run_format MCP tool."""

    @pytest.mark.asyncio
    async def test_run_format_success(self, mocker: Any, tmp_path: Path) -> None:
        """Mock run_command returns 0."""
        mock_run_command = mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_command",
            new_callable=AsyncMock,
            return_value=(0, "formatted", ""),
        )

        mocker.patch("vibraphone.tools.quality_gate_tools.get_project_root", return_value=tmp_path)

        from vibraphone.tools.quality_gate_tools import run_format

        result = await run_format.fn()

        assert result["status"] == "pass"
        assert mock_run_command.called


class TestRequestCodeReview:
    """Tests for request_code_review MCP tool."""

    @pytest.mark.asyncio
    async def test_request_code_review_approved(self, mocker: Any, tmp_path: Path) -> None:
        """Mock reviewer returns only warnings."""
        mocker.patch("vibraphone.tools.quality_gate_tools.get_project_root", return_value=tmp_path)

        mock_config = MagicMock()
        mock_config.circuit_breakers.review.max_attempts = 5
        mock_config.review.model = "test-model"
        mocker.patch("vibraphone.tools.quality_gate_tools.get_config", return_value=mock_config)

        # Mock state manager
        mock_state_manager_class = mocker.patch(
            "vibraphone.tools.quality_gate_tools.get_quality_state_manager"
        )
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
    async def test_request_code_review_rejected(self, mocker: Any, tmp_path: Path) -> None:
        """Mock reviewer returns errors."""
        mocker.patch("vibraphone.tools.quality_gate_tools.get_project_root", return_value=tmp_path)

        mock_config = MagicMock()
        mock_config.circuit_breakers.review.max_attempts = 5
        mock_config.review.model = "test-model"
        mocker.patch("vibraphone.tools.quality_gate_tools.get_config", return_value=mock_config)

        mock_state_manager_class = mocker.patch(
            "vibraphone.tools.quality_gate_tools.get_quality_state_manager"
        )
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
    async def test_request_code_review_blocks_dangerous_files(
        self, mocker: Any, tmp_path: Path
    ) -> None:
        """.env file not staged."""
        mocker.patch("vibraphone.tools.quality_gate_tools.get_project_root", return_value=tmp_path)

        mock_config = MagicMock()
        mock_config.circuit_breakers.review.max_attempts = 5
        mock_config.review.model = "test-model"
        mocker.patch("vibraphone.tools.quality_gate_tools.get_config", return_value=mock_config)

        mock_state_manager_class = mocker.patch(
            "vibraphone.tools.quality_gate_tools.get_quality_state_manager"
        )
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
    async def test_request_code_review_circuit_breaker(
        self, mocker: Any, tmp_path: Path
    ) -> None:
        """Escalation after max attempts."""
        mocker.patch("vibraphone.tools.quality_gate_tools.get_project_root", return_value=tmp_path)

        mock_config = MagicMock()
        mock_config.circuit_breakers.review.max_attempts = 3
        mock_config.review.model = "test-model"
        mocker.patch("vibraphone.tools.quality_gate_tools.get_config", return_value=mock_config)

        # State already at max attempts
        mock_state_manager_class = mocker.patch(
            "vibraphone.tools.quality_gate_tools.get_quality_state_manager"
        )
        mock_state_manager = MagicMock()
        mock_state_manager.load.return_value = QualityGateState(
            task_id="test-task", review_attempts=3
        )
        mock_state_manager_class.return_value = mock_state_manager

        from vibraphone.tools.quality_gate_tools import request_code_review

        result = await request_code_review.fn("test-task")

        assert result["status"] == "ESCALATED"
        assert result["error_type"] == "CircuitBreakerTripped"


class TestAttemptCommit:
    """Tests for attempt_commit MCP tool."""

    @pytest.mark.asyncio
    async def test_attempt_commit_no_review(self, mocker: Any, tmp_path: Path) -> None:
        """Fails without approved review."""
        mocker.patch("vibraphone.tools.quality_gate_tools.get_project_root", return_value=tmp_path)

        mock_state_manager_class = mocker.patch(
            "vibraphone.tools.quality_gate_tools.get_quality_state_manager"
        )
        mock_state_manager = MagicMock()
        mock_state_manager.load.return_value = None  # No state
        mock_state_manager_class.return_value = mock_state_manager

        from vibraphone.tools.quality_gate_tools import attempt_commit

        result = await attempt_commit.fn("test-task", "commit message")

        assert result["status"] == "error"
        assert "No approved review" in result["message"]

    @pytest.mark.asyncio
    async def test_attempt_commit_diff_mismatch(self, mocker: Any, tmp_path: Path) -> None:
        """Fails when diff hash changed."""
        mocker.patch("vibraphone.tools.quality_gate_tools.get_project_root", return_value=tmp_path)

        mock_state_manager_class = mocker.patch(
            "vibraphone.tools.quality_gate_tools.get_quality_state_manager"
        )
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
    async def test_attempt_commit_quality_check_fails(self, mocker: Any, tmp_path: Path) -> None:
        """Fails when just check fails."""
        mocker.patch("vibraphone.tools.quality_gate_tools.get_project_root", return_value=tmp_path)

        mock_state_manager_class = mocker.patch(
            "vibraphone.tools.quality_gate_tools.get_quality_state_manager"
        )
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
    async def test_attempt_commit_success(self, mocker: Any, tmp_path: Path) -> None:
        """All checks pass, commit executes."""
        mocker.patch("vibraphone.tools.quality_gate_tools.get_project_root", return_value=tmp_path)

        mock_state_manager_class = mocker.patch(
            "vibraphone.tools.quality_gate_tools.get_quality_state_manager"
        )
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
