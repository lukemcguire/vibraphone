"""Session state persistence for tracking active worktrees.

Provides SessionState model and SessionManager for persisting session data
to .vibraphone/session.json with atomic file operations.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel


class SessionState(BaseModel):
    """Session state for tracking active worktree.

    Attributes:
        task_id: Current task ID (matches br output format)
        worktree_path: Path to worktree directory
        branch_name: Branch name (e.g., feat/001-setup-auth)
        started_at: When session started
    """

    task_id: str
    worktree_path: Path
    branch_name: str
    started_at: datetime

    def to_json_string(self) -> str:
        """Serialize session state to JSON string.

        Handles Path and datetime serialization for JSON compatibility.

        Returns:
            JSON string representation of session state.
        """
        data = {
            "task_id": self.task_id,
            "worktree_path": str(self.worktree_path),
            "branch_name": self.branch_name,
            "started_at": self.started_at.isoformat(),
        }
        return json.dumps(data, indent=2)


class SessionManager:
    """Manager for session state persistence.

    Provides atomic file operations for session state using temp file + rename pattern.
    Session file stored at .vibraphone/session.json relative to project root.
    """

    def __init__(self, project_root: Path) -> None:
        """Initialize SessionManager with project root.

        Args:
            project_root: Path to project root directory.
        """
        self.project_root = project_root
        self.session_file = project_root / ".vibraphone" / "session.json"

    def load(self) -> SessionState | None:
        """Load session state from JSON file.

        Returns:
            SessionState if file exists and is valid, None if file doesn't exist.

        Raises:
            json.JSONDecodeError: If session file contains invalid JSON.
            ValidationError: If session data doesn't match SessionState schema.
        """
        if not self.session_file.exists():
            return None

        content = self.session_file.read_text(encoding="utf-8")
        data = json.loads(content)
        return SessionState(**data)

    def save(self, state: SessionState) -> None:
        """Atomically save session state to JSON file.

        Uses temp file + rename pattern for atomic writes on POSIX systems.
        Creates parent directory if needed.

        Args:
            state: SessionState to persist.
        """
        # Ensure parent directory exists
        self.session_file.parent.mkdir(parents=True, exist_ok=True)

        # Write to temp file in same directory for atomic rename
        with tempfile.NamedTemporaryFile(
            mode="w",
            dir=self.session_file.parent,
            delete=False,
            encoding="utf-8",
        ) as temp_file:
            temp_file.write(state.to_json_string())
            temp_name = temp_file.name

        # Atomic rename (POSIX guarantees atomicity)
        Path(temp_name).rename(self.session_file)

    def clear(self) -> None:
        """Delete session file if it exists."""
        if self.session_file.exists():
            self.session_file.unlink()


def get_session_manager() -> SessionManager:
    """Get SessionManager for current project.

    Uses config file location to determine project root, falling back to
    current working directory if no config found.

    Returns:
        SessionManager instance for current project.
    """
    from vibraphone.config import find_config_file

    config_path = find_config_file()
    project_root = config_path.parent if config_path is not None else Path.cwd()

    return SessionManager(project_root)
