"""LLM code reviewer using instructor library for structured output.

Uses OpenRouter (OpenAI-compatible API) with instructor for Pydantic-validated
structured output from LLM code reviews.
"""

import os
from typing import Literal

from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class ReviewIssue(BaseModel):
    """A single issue found during code review."""

    severity: Literal["error", "warning"]
    file: str
    line: int | None
    message: str
    suggestion: str | None


class ReviewResult(BaseModel):
    """Result of a code review."""

    issues: list[ReviewIssue]
    summary: str


class MissingAPIKeyError(Exception):
    """Raised when REVIEWER_API_KEY is not set."""

    def __init__(self) -> None:
        super().__init__(
            "REVIEWER_API_KEY environment variable not set.\n"
            "Setup instructions:\n"
            "1. Get an API key from https://openrouter.ai/keys\n"
            "2. Set REVIEWER_API_KEY in your environment or .env file:\n"
            "   export REVIEWER_API_KEY=your-key-here\n"
            "   or add to .env: REVIEWER_API_KEY=your-key-here"
        )


class CodeReviewer:
    """LLM-powered code reviewer using instructor + OpenRouter."""

    def __init__(self, model: str = "anthropic/claude-3-sonnet") -> None:
        """Initialize the code reviewer.

        Args:
            model: Model to use for review (default: claude-3-sonnet).

        Raises:
            MissingAPIKeyError: If REVIEWER_API_KEY is not set.
        """
        api_key = os.environ.get("REVIEWER_API_KEY")
        if not api_key:
            raise MissingAPIKeyError()

        self.model = model
        self._client = None

    def _get_client(self):
        """Get or create the instructor-patched OpenAI client.

        Lazy import to avoid errors if instructor not installed.
        """
        if self._client is None:
            try:
                import instructor
                from openai import OpenAI
            except ImportError as e:
                raise ImportError(
                    "instructor and openai packages required for code review.\n"
                    "Install with: uv add instructor python-dotenv"
                ) from e

            # OpenRouter uses OpenAI SDK with custom base_url
            self._client = instructor.patch(
                OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=os.environ.get("REVIEWER_API_KEY"),
                ),
            )
        return self._client

    def review(self, diff_content: str, previous_issues: list[dict] | None = None) -> ReviewResult:
        """Send diff to LLM for review, return structured result.

        Args:
            diff_content: The git diff content to review.
            previous_issues: Previously identified issues to re-check.

        Returns:
            ReviewResult with issues and summary.
        """
        client = self._get_client()

        system_prompt = "You are a code reviewer. Analyze the diff for issues."
        if previous_issues:
            system_prompt += f"\n\nPreviously identified issues to re-check: {previous_issues}"

        return client.chat.completions.create(
            model=self.model,
            response_model=ReviewResult,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Review these changes:\n\n{diff_content}"},
            ],
            max_retries=2,
        )
