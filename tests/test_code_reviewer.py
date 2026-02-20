"""Unit tests for code_reviewer module.

Tests ReviewIssue, ReviewResult models and CodeReviewer with mocked LLM client.
"""

from typing import Literal, cast
from unittest.mock import MagicMock

import pytest

from vibraphone.utils.code_reviewer import (
    CodeReviewer,
    MissingAPIKeyError,
    ReviewIssue,
    ReviewResult,
)


class TestReviewIssue:
    """Tests for ReviewIssue model."""

    def test_review_issue_model(self) -> None:
        """ReviewIssue creates with all fields."""
        issue = ReviewIssue(
            severity="error",
            file="src/main.py",
            line=10,
            message="Unused import",
            suggestion="Remove unused import",
        )

        assert issue.severity == "error"
        assert issue.file == "src/main.py"
        assert issue.line == 10
        assert issue.message == "Unused import"
        assert issue.suggestion == "Remove unused import"

    def test_review_issue_optional_fields(self) -> None:
        """ReviewIssue with None optional fields."""
        issue = ReviewIssue(
            severity="warning",
            file="src/utils.py",
            line=None,
            message="Missing docstring",
            suggestion=None,
        )

        assert issue.line is None
        assert issue.suggestion is None

    def test_review_issue_severity_values(self) -> None:
        """ReviewIssue accepts error and warning severity."""
        for severity in cast("list[Literal['error', 'warning']]", ["error", "warning"]):
            issue = ReviewIssue(
                severity=severity,
                file="test.py",
                line=1,
                message="test",
                suggestion=None,
            )
            assert issue.severity == severity


class TestReviewResult:
    """Tests for ReviewResult model."""

    def test_review_result_model(self) -> None:
        """ReviewResult creates with issues list and summary."""
        issues = [
            ReviewIssue(severity="error", file="a.py", line=1, message="err", suggestion=None),
            ReviewIssue(severity="warning", file="b.py", line=2, message="warn", suggestion=None),
        ]
        result = ReviewResult(issues=issues, summary="Found 2 issues")

        assert len(result.issues) == 2
        assert result.summary == "Found 2 issues"

    def test_review_result_empty_issues(self) -> None:
        """ReviewResult can have empty issues list."""
        result = ReviewResult(issues=[], summary="No issues found")

        assert result.issues == []
        assert result.summary == "No issues found"


class TestCodeReviewer:
    """Tests for CodeReviewer class."""

    def test_code_reviewer_init(self, monkeypatch) -> None:
        """CodeReviewer initializes with model name."""
        monkeypatch.setenv("REVIEWER_API_KEY", "test-key")

        reviewer = CodeReviewer(model="anthropic/claude-3-sonnet")

        assert reviewer.model == "anthropic/claude-3-sonnet"

    def test_code_reviewer_missing_api_key(self, monkeypatch) -> None:
        """Clear error when REVIEWER_API_KEY not set."""
        monkeypatch.delenv("REVIEWER_API_KEY", raising=False)

        with pytest.raises(MissingAPIKeyError) as exc_info:
            CodeReviewer()

        assert "REVIEWER_API_KEY" in str(exc_info.value)
        assert "openrouter.ai" in str(exc_info.value)

    def test_code_reviewer_review_returns_result(self, monkeypatch, mocker) -> None:
        """Mock instructor client, verify ReviewResult returned."""
        monkeypatch.setenv("REVIEWER_API_KEY", "test-key")

        # Create mock result
        mock_result = ReviewResult(
            issues=[],
            summary="No issues found",
        )

        # Mock instructor.patch and client
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_result

        mock_instructor = MagicMock()
        mock_instructor.patch.return_value = mock_client

        mocker.patch.dict(
            "sys.modules",
            {
                "instructor": mock_instructor,
            },
        )
        mock_openai = MagicMock()
        mocker.patch.dict(
            "sys.modules",
            {
                "openai": mock_openai,
            },
        )

        reviewer = CodeReviewer()

        # Mock _get_client to return our mock
        reviewer._client = mock_client

        result = reviewer.review("diff content here")

        assert isinstance(result, ReviewResult)
        assert result.summary == "No issues found"

    def test_code_reviewer_includes_previous_issues(self, monkeypatch, mocker) -> None:
        """Previous issues passed to prompt."""
        monkeypatch.setenv("REVIEWER_API_KEY", "test-key")

        # Create mock result
        mock_result = ReviewResult(
            issues=[],
            summary="No issues found",
        )

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_result

        reviewer = CodeReviewer()
        reviewer._client = mock_client

        previous_issues = [{"file": "test.py", "message": "old issue"}]
        reviewer.review("diff content", previous_issues=previous_issues)

        # Verify the call was made
        assert mock_client.chat.completions.create.called
        call_kwargs = mock_client.chat.completions.create.call_args

        # Check that previous issues were passed in messages
        messages = call_kwargs[1]["messages"]
        system_message = messages[0]["content"]
        assert "Previously identified issues" in system_message

    def test_code_reviewer_review_without_previous_issues(self, monkeypatch, mocker) -> None:
        """Review works without previous issues."""
        monkeypatch.setenv("REVIEWER_API_KEY", "test-key")

        mock_result = ReviewResult(
            issues=[],
            summary="No issues found",
        )

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_result

        reviewer = CodeReviewer()
        reviewer._client = mock_client

        result = reviewer.review("diff content")

        assert isinstance(result, ReviewResult)
        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs[1]["messages"]
        system_message = messages[0]["content"]
        # Should NOT have previous issues section
        assert "Previously identified issues" not in system_message

    def test_missing_api_key_error_message(self) -> None:
        """MissingAPIKeyError provides setup instructions."""
        error = MissingAPIKeyError()

        assert "REVIEWER_API_KEY" in str(error)
        assert "https://openrouter.ai/keys" in str(error)
        assert "export REVIEWER_API_KEY" in str(error)

    def test_code_reviewer_default_model(self, monkeypatch) -> None:
        """CodeReviewer uses default model when not specified."""
        monkeypatch.setenv("REVIEWER_API_KEY", "test-key")

        reviewer = CodeReviewer()

        assert reviewer.model == "anthropic/claude-3-sonnet"

    def test_code_reviewer_lazy_client_init(self, monkeypatch) -> None:
        """CodeReviewer initializes client lazily."""
        monkeypatch.setenv("REVIEWER_API_KEY", "test-key")

        reviewer = CodeReviewer()

        # Client should not be initialized yet
        assert reviewer._client is None

    def test_code_reviewer_with_issues_result(self, monkeypatch, mocker) -> None:
        """Review returns result with issues."""
        monkeypatch.setenv("REVIEWER_API_KEY", "test-key")

        issues = [
            ReviewIssue(
                severity="error",
                file="src/main.py",
                line=10,
                message="Undefined variable",
                suggestion="Define the variable before use",
            ),
        ]
        mock_result = ReviewResult(
            issues=issues,
            summary="Found 1 error",
        )

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_result

        reviewer = CodeReviewer()
        reviewer._client = mock_client

        result = reviewer.review("diff with issues")

        assert len(result.issues) == 1
        assert result.issues[0].severity == "error"
        assert result.issues[0].file == "src/main.py"
