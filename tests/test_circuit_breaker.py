"""Unit tests for circuit_breaker module.

Tests CircuitBreaker trip detection and escalation response format.
"""

from vibraphone.utils.circuit_breaker import CircuitBreaker


class TestCircuitBreaker:
    """Tests for CircuitBreaker class."""

    def test_check_returns_none_when_not_tripped(self) -> None:
        """CircuitBreaker.check returns None when attempts below threshold."""
        breaker = CircuitBreaker(5, "tests")

        result = breaker.check(3)

        assert result is None

    def test_check_returns_escalation_when_tripped(self) -> None:
        """CircuitBreaker.check returns escalation dict when threshold reached."""
        breaker = CircuitBreaker(5, "tests")

        result = breaker.check(5)

        assert result is not None
        assert result["status"] == "ESCALATED"
        assert result["error_type"] == "CircuitBreakerTripped"

    def test_check_returns_escalation_when_exceeded(self) -> None:
        """CircuitBreaker.check returns escalation when threshold exceeded."""
        breaker = CircuitBreaker(5, "tests")

        result = breaker.check(6)

        assert result is not None
        assert result["status"] == "ESCALATED"

    def test_none_max_attempts_never_trips(self) -> None:
        """CircuitBreaker with None max_attempts never trips."""
        breaker = CircuitBreaker(None, "lint")

        result = breaker.check(100)

        assert result is None

    def test_escalation_response_format(self) -> None:
        """Escalation response contains all required fields."""
        breaker = CircuitBreaker(5, "tests")

        result = breaker.check(5)

        assert result is not None
        assert "status" in result
        assert "error_type" in result
        assert "message" in result
        assert "human_actions" in result
        assert "next_steps" in result

    def test_escalation_includes_all_human_actions(self) -> None:
        """Escalation response includes 3 human action options."""
        breaker = CircuitBreaker(5, "tests")

        result = breaker.check(5)

        assert result is not None
        assert len(result["human_actions"]) == 3
        assert "Reset circuit breaker" in result["human_actions"][0]
        assert "Abandon task" in result["human_actions"][1]
        assert "Provide guidance" in result["human_actions"][2]

    def test_is_tripped_method_false(self) -> None:
        """is_tripped returns False when below threshold."""
        breaker = CircuitBreaker(5, "tests")

        assert breaker.is_tripped(3) is False

    def test_is_tripped_method_true(self) -> None:
        """is_tripped returns True when at threshold."""
        breaker = CircuitBreaker(5, "tests")

        assert breaker.is_tripped(5) is True
        assert breaker.is_tripped(6) is True

    def test_is_tripped_none_max_attempts(self) -> None:
        """is_tripped returns False when max_attempts is None."""
        breaker = CircuitBreaker(None, "tests")

        assert breaker.is_tripped(100) is False

    def test_escalation_message_includes_counts(self) -> None:
        """Escalation message includes attempt counts."""
        breaker = CircuitBreaker(5, "tests")

        result = breaker.check(5)

        assert result is not None
        assert "5" in result["message"]
        assert "max: 5" in result["message"]

    def test_escalation_message_includes_tool_name(self) -> None:
        """Escalation message includes tool name."""
        breaker = CircuitBreaker(5, "my-lint-tool")

        result = breaker.check(5)

        assert result is not None
        assert "my-lint-tool" in result["message"]

    def test_escalation_response_static_method(self) -> None:
        """escalation_response works as static method."""
        result = CircuitBreaker.escalation_response("review", 3, 3)

        assert result["status"] == "ESCALATED"
        assert result["error_type"] == "CircuitBreakerTripped"
        assert "review" in result["message"]

    def test_check_zero_attempts(self) -> None:
        """check returns None for zero attempts."""
        breaker = CircuitBreaker(5, "tests")

        result = breaker.check(0)

        assert result is None

    def test_check_one_below_threshold(self) -> None:
        """check returns None when one below threshold."""
        breaker = CircuitBreaker(5, "tests")

        result = breaker.check(4)

        assert result is None
