"""Unit tests for session management.

Tests SessionState model and SessionManager with mocked file operations.
Uses tmp_path fixture for isolated testing.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from vibraphone.utils.session import SessionManager, SessionState


class TestSessionState:
    """Tests for SessionState model."""

    def test_session_state_creation(self, tmp_path: Path) -> None:
        """Create SessionState with all fields."""
        worktree_path = tmp_path / "worktree"
        state = SessionState(
            task_id="bd-test",
            worktree_path=worktree_path,
            branch_name="feat/bd-test",
            started_at=datetime(2026, 2, 16, 12, 0, 0),
        )

        assert state.task_id == "bd-test"
        assert state.worktree_path == worktree_path
        assert state.branch_name == "feat/bd-test"
        assert state.started_at == datetime(2026, 2, 16, 12, 0, 0)

    def test_session_state_json_serialization(self, tmp_path: Path) -> None:
        """model_dump_json returns valid JSON with Path as string."""
        import json

        worktree_path = tmp_path / "worktree"
        state = SessionState(
            task_id="bd-test",
            worktree_path=worktree_path,
            branch_name="feat/bd-test",
            started_at=datetime(2026, 2, 16, 12, 0, 0),
        )

        json_str = state.model_dump_json()

        # Should be valid JSON
        data = json.loads(json_str)
        assert data["task_id"] == "bd-test"
        assert data["worktree_path"] == str(worktree_path)
        assert data["branch_name"] == "feat/bd-test"
        assert "started_at" in data


class TestSessionManager:
    """Tests for SessionManager."""

    def test_load_no_session(self, tmp_path: Path) -> None:
        """Returns None when file doesn't exist."""
        session = SessionManager(tmp_path)
        result = session.load()

        assert result is None

    def test_save_creates_file(self, tmp_path: Path) -> None:
        """save() creates .vibraphone/session.json."""
        session = SessionManager(tmp_path)
        state = SessionState(
            task_id="bd-test",
            worktree_path=tmp_path / "worktree",
            branch_name="feat/bd-test",
            started_at=datetime.now(),
        )

        session.save(state)

        session_file = tmp_path / ".vibraphone" / "session.json"
        assert session_file.exists()

    def test_save_load_roundtrip(self, tmp_path: Path) -> None:
        """save then load returns same data."""
        session = SessionManager(tmp_path)
        original_state = SessionState(
            task_id="bd-test",
            worktree_path=tmp_path / "worktree",
            branch_name="feat/bd-test",
            started_at=datetime(2026, 2, 16, 12, 0, 0),
        )

        session.save(original_state)
        loaded_state = session.load()

        assert loaded_state is not None
        assert loaded_state.task_id == original_state.task_id
        assert loaded_state.worktree_path == original_state.worktree_path
        assert loaded_state.branch_name == original_state.branch_name

    def test_clear_removes_file(self, tmp_path: Path) -> None:
        """clear() removes session file."""
        session = SessionManager(tmp_path)
        state = SessionState(
            task_id="bd-test",
            worktree_path=tmp_path / "worktree",
            branch_name="feat/bd-test",
            started_at=datetime.now(),
        )

        session.save(state)
        session_file = tmp_path / ".vibraphone" / "session.json"
        assert session_file.exists()

        session.clear()

        assert not session_file.exists()

    def test_clear_no_file_is_safe(self, tmp_path: Path) -> None:
        """clear() is safe when no file exists."""
        session = SessionManager(tmp_path)

        # Should not raise
        session.clear()

    def test_atomic_write(self, tmp_path: Path) -> None:
        """Verify temp file + rename pattern is used."""
        session = SessionManager(tmp_path)
        state = SessionState(
            task_id="bd-test",
            worktree_path=tmp_path / "worktree",
            branch_name="feat/bd-test",
            started_at=datetime.now(),
        )

        # Track Path.rename calls
        with patch.object(Path, "rename") as mock_rename:
            session.save(state)

            # Verify rename was called (temp file -> final file)
            mock_rename.assert_called_once()
            # The target should be the session file
            rename_target = mock_rename.call_args[0][0]
            assert rename_target == tmp_path / ".vibraphone" / "session.json"

    def test_load_handles_json_decode_error(self, tmp_path: Path) -> None:
        """load() raises JSONDecodeError for invalid JSON."""
        import json

        session = SessionManager(tmp_path)
        session_file = tmp_path / ".vibraphone" / "session.json"
        session_file.parent.mkdir(parents=True, exist_ok=True)
        session_file.write_text("not valid json {")

        with pytest.raises(json.JSONDecodeError):
            session.load()

    def test_load_handles_missing_fields(self, tmp_path: Path) -> None:
        """load() raises ValidationError for missing required fields."""
        import json

        from pydantic import ValidationError

        session = SessionManager(tmp_path)
        session_file = tmp_path / ".vibraphone" / "session.json"
        session_file.parent.mkdir(parents=True, exist_ok=True)
        # Missing required fields
        session_file.write_text(json.dumps({"task_id": "bd-test"}))

        with pytest.raises(ValidationError):
            session.load()
