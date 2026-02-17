"""Circuit breaker for quality gate failure tracking with escalation.

Prevents runaway agent loops by tracking failures per tool and
returning escalation responses when thresholds are exceeded.
"""

from __future__ import annotations


class CircuitBreaker:
    """Circuit breaker for per-tool failure tracking with escalation.

    When tripped, blocks the agent entirely and returns escalation response
    with human action options. Independent counters per tool (tests, lint, review).

    Attributes:
        max_attempts: Maximum allowed attempts before tripping. None means no limit.
        tool_name: Name of the tool (for escalation messages).
    """

    def __init__(self, max_attempts: int | None, tool_name: str) -> None:
        """Initialize circuit breaker.

        Args:
            max_attempts: Maximum attempts before tripping. None disables breaker.
            tool_name: Name of the tool for escalation messages.
        """
        self.max_attempts = max_attempts
        self.tool_name = tool_name

    def check(self, current_attempts: int) -> dict | None:
        """Check if circuit breaker is tripped.

        Args:
            current_attempts: Current number of failed attempts.

        Returns:
            Escalation response dict if tripped, None otherwise.
            None is also returned if max_attempts is None (breaker disabled).
        """
        if self.max_attempts is None:
            return None

        if self.is_tripped(current_attempts):
            return self.escalation_response(self.tool_name, current_attempts, self.max_attempts)

        return None

    def is_tripped(self, current_attempts: int) -> bool:
        """Check if circuit breaker threshold is exceeded.

        Args:
            current_attempts: Current number of failed attempts.

        Returns:
            True if threshold exceeded, False otherwise.
        """
        if self.max_attempts is None:
            return False

        return current_attempts >= self.max_attempts

    @staticmethod
    def escalation_response(
        tool_name: str,
        attempts: int,
        max_attempts: int,
    ) -> dict:
        """Generate escalation response with human action options.

        Args:
            tool_name: Name of the tool that tripped.
            attempts: Number of attempts made.
            max_attempts: Configured maximum attempts.

        Returns:
            Escalation dict with status, error details, and human actions.
        """
        return {
            "status": "ESCALATED",
            "error_type": "CircuitBreakerTripped",
            "message": f"{tool_name} failed {attempts} times (max: {max_attempts})",
            "human_actions": [
                "Reset circuit breaker and let agent continue",
                "Abandon task and start over",
                "Provide guidance then reset breaker",
            ],
            "next_steps": ["Await human decision"],
        }
