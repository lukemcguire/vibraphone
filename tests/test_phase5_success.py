"""Success criteria tests for Phase 5 Quality Gate Tools.

Tests verify all ROADMAP requirements for Phase 5:
- QUAL-01: Agent can run tests with circuit breaker
- QUAL-02: Agent can run linter
- QUAL-03: Agent can run formatter
- QUAL-04: Agent can request LLM-powered code review with staging
- QUAL-05: Agent can commit only after approved review
- QUAL-06: Circuit breakers escalate after configurable max attempts

Each test is named by requirement ID for ROADMAP traceability.
"""

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from vibraphone.utils.circuit_breaker import CircuitBreaker
from vibraphone.utils.quality_state import QualityGateState


class TestPhase5SuccessCriteria:
    """Verify all Phase 5 requirements from ROADMAP.md."""

    @pytest.mark.asyncio
    async def test_QUAL_01_run_tests_with_circuit_breaker(
        self, mocker: Any, tmp_path: Path
    ) -> None:
        """QUAL-01: Verify run_tests tool exists and circuit_breaker.check is called.

        The run_tests tool should:
        1. Exist as an MCP tool callable via .fn()
        2. Use CircuitBreaker.check() on failure
        3. Return escalation response when circuit breaker trips
        """
        # Import tool
        from vibraphone.tools.quality_gate_tools import run_tests

        # Verify tool exists (has fn attribute for direct call)
        assert hasattr(run_tests, "fn")

        # Setup mocks
        mocker.patch("vibraphone.tools.quality_gate_tools.get_project_root", return_value=tmp_path)
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_command",
            new_callable=AsyncMock,
            return_value=(1, "", "test failed"),
        )

        mock_config = MagicMock()
        mock_config.circuit_breakers.tests.max_attempts = 3
        mocker.patch("vibraphone.tools.quality_gate_tools.get_config", return_value=mock_config)

        mock_state_manager_class = mocker.patch(
            "vibraphone.tools.quality_gate_tools.get_quality_state_manager"
        )
        mock_state_manager = MagicMock()
        # Start with 2 attempts, will increment to 3 on failure
        mock_state_manager.load.return_value = QualityGateState(
            task_id="default", test_attempts=2
        )
        mock_state_manager_class.return_value = mock_state_manager

        # Run tool
        result = await run_tests.fn()

        # Verify circuit breaker escalation response
        assert result["status"] == "ESCALATED"
        assert result["error_type"] == "CircuitBreakerTripped"
        assert "human_actions" in result

    @pytest.mark.asyncio
    async def test_QUAL_02_run_lint(self, mocker: Any, tmp_path: Path) -> None:
        """QUAL-02: Verify run_lint tool exists and returns structured output.

        The run_lint tool should:
        1. Exist as an MCP tool callable via .fn()
        2. Return structured output with status, output, duration_ms, timestamp
        """
        from vibraphone.tools.quality_gate_tools import run_lint

        # Verify tool exists
        assert hasattr(run_lint, "fn")

        # Setup mocks
        mocker.patch("vibraphone.tools.quality_gate_tools.get_project_root", return_value=tmp_path)
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_command",
            new_callable=AsyncMock,
            return_value=(0, "lint passed", ""),
        )

        # Run tool
        result = await run_lint.fn()

        # Verify structured output
        assert result["status"] == "pass"
        assert "output" in result
        assert "duration_ms" in result
        assert "timestamp" in result
        assert "next_steps" in result

    @pytest.mark.asyncio
    async def test_QUAL_03_run_format(self, mocker: Any, tmp_path: Path) -> None:
        """QUAL-03: Verify run_format tool exists and returns structured output.

        The run_format tool should:
        1. Exist as an MCP tool callable via .fn()
        2. Return structured output with status, output, duration_ms, timestamp
        """
        from vibraphone.tools.quality_gate_tools import run_format

        # Verify tool exists
        assert hasattr(run_format, "fn")

        # Setup mocks
        mocker.patch("vibraphone.tools.quality_gate_tools.get_project_root", return_value=tmp_path)
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_command",
            new_callable=AsyncMock,
            return_value=(0, "formatted", ""),
        )

        # Run tool
        result = await run_format.fn()

        # Verify structured output
        assert result["status"] == "pass"
        assert "output" in result
        assert "duration_ms" in result
        assert "timestamp" in result
        assert "next_steps" in result

    @pytest.mark.asyncio
    async def test_QUAL_04_request_code_review(self, mocker: Any, tmp_path: Path) -> None:
        """QUAL-04: Verify request_code_review tool with staging and blocking.

        The request_code_review tool should:
        1. Exist as an MCP tool callable via .fn()
        2. Block dangerous files (.env, credentials, etc.)
        3. Return APPROVED when only warnings present
        4. Return REJECTED when errors present
        """
        from vibraphone.tools.quality_gate_tools import is_dangerous_file, request_code_review

        # Verify tool exists
        assert hasattr(request_code_review, "fn")

        # Verify dangerous files blocked
        assert is_dangerous_file(".env") is True
        assert is_dangerous_file("secrets.yaml") is True
        assert is_dangerous_file("id_rsa") is True

        # Setup mocks for APPROVED case
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
            return_value=(["config/.env"], "diff content", None),
        )

        # Mock review with warnings only (APPROVED)
        mock_issue = MagicMock()
        mock_issue.model_dump.return_value = {"severity": "warning", "message": "Minor"}
        mock_result = MagicMock()
        mock_result.issues = [mock_issue]
        mock_result.summary = "OK"

        mock_reviewer_class = mocker.patch("vibraphone.tools.quality_gate_tools.CodeReviewer")
        mock_reviewer = MagicMock()
        mock_reviewer.review.return_value = mock_result
        mock_reviewer_class.return_value = mock_reviewer

        result = await request_code_review.fn("test-task")

        # APPROVED with warnings about blocked file
        assert result["status"] == "APPROVED"
        assert "warnings" in result
        assert ".env" in result["warnings"][0]

    @pytest.mark.asyncio
    async def test_QUAL_05_attempt_commit_requires_review(
        self, mocker: Any, tmp_path: Path
    ) -> None:
        """QUAL-05: Verify attempt_commit enforces review-before-commit workflow.

        The attempt_commit tool should:
        1. Fail without APPROVED status
        2. Fail when diff hash mismatch (sneaky changes)
        3. Succeed with APPROVED + matching hash
        """
        from vibraphone.tools.quality_gate_tools import attempt_commit

        # Verify tool exists
        assert hasattr(attempt_commit, "fn")

        # Setup mocks
        mocker.patch("vibraphone.tools.quality_gate_tools.get_project_root", return_value=tmp_path)

        # Test 1: No approved review
        mock_state_manager_class = mocker.patch(
            "vibraphone.tools.quality_gate_tools.get_quality_state_manager"
        )
        mock_state_manager = MagicMock()
        mock_state_manager.load.return_value = None
        mock_state_manager_class.return_value = mock_state_manager

        result = await attempt_commit.fn("test-task", "msg")
        assert result["status"] == "error"
        assert "No approved review" in result["message"]

        # Test 2: Diff hash mismatch
        mock_state_manager.load.return_value = QualityGateState(
            task_id="test-task",
            last_review_status="APPROVED",
            last_review_diff_hash="old-hash",
        )

        mocker.patch(
            "vibraphone.tools.quality_gate_tools.get_staged_diff",
            new_callable=AsyncMock,
            return_value=(0, "different content", ""),
        )

        result = await attempt_commit.fn("test-task", "msg")
        assert result["status"] == "error"
        assert "differ from reviewed" in result["message"]

        # Test 3: Success with matching hash
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.hash_diff",
            return_value="old-hash",
        )
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_command",
            new_callable=AsyncMock,
            return_value=(0, "", ""),
        )
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.get_command",
            return_value="just check",
        )
        mocker.patch(
            "vibraphone.tools.quality_gate_tools.run_git_commit",
            new_callable=AsyncMock,
            return_value=(0, "[main abc123] msg", ""),
        )

        result = await attempt_commit.fn("test-task", "msg")
        assert result["status"] == "committed"

    @pytest.mark.asyncio
    async def test_QUAL_06_circuit_breaker_escalation(self, mocker: Any) -> None:
        """QUAL-06: Verify circuit breaker escalation response format.

        Circuit breaker escalation should:
        1. Return status ESCALATED
        2. Include human_actions list with options
        3. Use config-driven thresholds
        """
        # Test with config-driven max_attempts
        breaker = CircuitBreaker(max_attempts=3, tool_name="run_tests")

        # Not tripped at 2 attempts
        result = breaker.check(2)
        assert result is None

        # Tripped at 3 attempts
        result = breaker.check(3)
        assert result is not None
        assert result["status"] == "ESCALATED"
        assert result["error_type"] == "CircuitBreakerTripped"
        assert "human_actions" in result
        assert len(result["human_actions"]) >= 1

        # Verify config-driven - None means disabled
        breaker_disabled = CircuitBreaker(max_attempts=None, tool_name="run_tests")
        result = breaker_disabled.check(100)
        assert result is None

    @pytest.mark.asyncio
    async def test_QUAL_06_circuit_breaker_human_actions(self) -> None:
        """QUAL-06: Verify circuit breaker provides human action options."""
        breaker = CircuitBreaker(max_attempts=3, tool_name="run_tests")

        result = breaker.check(3)

        assert result is not None
        assert "human_actions" in result
        # Should have meaningful human actions
        actions = result["human_actions"]
        assert len(actions) >= 1
        # Check that actions provide useful guidance
        all_actions_text = " ".join(actions)
        assert "reset" in all_actions_text.lower() or "abandon" in all_actions_text.lower()

    @pytest.mark.asyncio
    async def test_QUAL_06_circuit_breaker_in_tools(self, mocker: Any, tmp_path: Path) -> None:
        """QUAL-06: Verify circuit breakers work in actual tools."""
        from vibraphone.tools.quality_gate_tools import run_tests

        mocker.patch("vibraphone.tools.quality_gate_tools.get_project_root", return_value=tmp_path)

        # Config with low threshold
        mock_config = MagicMock()
        mock_config.circuit_breakers.tests.max_attempts = 2
        mocker.patch("vibraphone.tools.quality_gate_tools.get_config", return_value=mock_config)

        # State at threshold
        mock_state_manager_class = mocker.patch(
            "vibraphone.tools.quality_gate_tools.get_quality_state_manager"
        )
        mock_state_manager = MagicMock()
        mock_state_manager.load.return_value = QualityGateState(
            task_id="default", test_attempts=2
        )
        mock_state_manager_class.return_value = mock_state_manager

        # Run - should escalate immediately (attempts already at threshold)
        result = await run_tests.fn()

        assert result["status"] == "ESCALATED"
        assert "max" in result["message"].lower()
