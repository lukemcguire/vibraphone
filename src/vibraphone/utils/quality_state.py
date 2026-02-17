"""Per-task quality gate state persistence.

Provides QualityGateState model and QualityStateManager for persisting
per-task state to .vibraphone/tasks/{task_id}/state.json with atomic writes.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Literal

from pydantic import BaseModel


class QualityGateState(BaseModel):
    """State for tracking quality gate progress on a task.

    Stores review status, diff hash for preventing sneaked changes,
    review issues for re-review comparison, and attempt counters.

    Attributes:
        task_id: Task identifier (e.g., "001", "002").
        last_review_status: APPROVED, REJECTED, ESCALATED, or None.
        last_review_diff_hash: SHA-256 hash of last reviewed staged diff.
        last_review_issues: List of issues from last review for comparison.
        review_attempts: Counter for circuit breaker (reset on approval).
        test_attempts: Counter for circuit breaker (reset on pass).
        lint_attempts: Counter for circuit breaker (reset on pass).
    """

    task_id: str
    last_review_status: Literal["APPROVED", "REJECTED", "ESCALATED"] | None = None
    last_review_diff_hash: str | None = None
    last_review_issues: list[dict] = []
    review_attempts: int = 0
    test_attempts: int = 0
    lint_attempts: int = 0

    def custom_dump_json(self) -> str:
        """Serialize state to JSON string with pretty formatting.

        Returns:
            JSON string representation with indent=2.
        """
        data = {
            "task_id": self.task_id,
            "last_review_status": self.last_review_status,
            "last_review_diff_hash": self.last_review_diff_hash,
            "last_review_issues": self.last_review_issues,
            "review_attempts": self.review_attempts,
            "test_attempts": self.test_attempts,
            "lint_attempts": self.lint_attempts,
        }
        return json.dumps(data, indent=2)


class QualityStateManager:
    """Manager for per-task quality gate state persistence.

    Provides atomic file operations for state using temp file + rename pattern.
    State stored at .vibraphone/tasks/{task_id}/state.json.
    """

    def __init__(self, project_root: Path, task_id: str) -> None:
        """Initialize QualityStateManager.

        Args:
            project_root: Path to project root directory.
            task_id: Task identifier for state file.
        """
        self.project_root = project_root
        self.task_id = task_id
        self.state_file = project_root / ".vibraphone" / "tasks" / task_id / "state.json"

    def load(self) -> QualityGateState | None:
        """Load state from JSON file.

        Returns:
            QualityGateState if file exists and is valid, None if file doesn't exist.

        Raises:
            json.JSONDecodeError: If state file contains invalid JSON.
            ValidationError: If state data doesn't match QualityGateState schema.
        """
        if not self.state_file.exists():
            return None

        content = self.state_file.read_text(encoding="utf-8")
        data = json.loads(content)
        return QualityGateState(**data)

    def save(self, state: QualityGateState) -> None:
        """Atomically save state to JSON file.

        Uses temp file + rename pattern for atomic writes on POSIX systems.
        Creates parent directory if needed.

        Args:
            state: QualityGateState to persist.
        """
        # Ensure parent directory exists
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # Write to temp file in same directory for atomic rename
        with tempfile.NamedTemporaryFile(
            mode="w",
            dir=self.state_file.parent,
            delete=False,
            encoding="utf-8",
        ) as temp_file:
            temp_file.write(state.custom_dump_json())
            temp_name = temp_file.name

        # Atomic rename (POSIX guarantees atomicity)
        Path(temp_name).rename(self.state_file)

    def clear(self) -> None:
        """Delete state file if it exists.

        Called when task closes to clean up state.
        """
        if self.state_file.exists():
            self.state_file.unlink()
            # Also try to clean up empty parent directories
            try:
                self.state_file.parent.rmdir()
                (self.state_file.parent.parent).rmdir()  # tasks/
            except OSError:
                # Directories not empty or don't exist, that's fine
                pass


def get_quality_state_manager(task_id: str) -> QualityStateManager:
    """Get QualityStateManager for a specific task.

    Uses config file location to determine project root, falling back to
    current working directory if no config found.

    Args:
        task_id: Task identifier for state file.

    Returns:
        QualityStateManager instance for the specified task.
    """
    from vibraphone.config import get_project_root

    project_root = get_project_root()
    return QualityStateManager(project_root, task_id)
