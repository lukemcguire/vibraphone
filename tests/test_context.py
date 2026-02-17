"""Unit tests for context helper module.

Tests vibraphone.utils.context with mocked SessionManager.
Verifies execution context resolution for session-aware command execution.
"""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from vibraphone.utils.session import SessionState


class TestGetExecutionContext:
    """Tests for get_execution_context helper function."""

    def test_returns_project_root_when_no_session(self, mocker: Any, tmp_path: Path) -> None:
        """When SessionManager.load() returns None, returns project root."""
        from vibraphone.utils.context import get_execution_context

        # Mock get_project_root to return tmp_path
        mocker.patch("vibraphone.utils.context.get_project_root", return_value=tmp_path)

        # Mock SessionManager.load to return None (no session)
        mock_manager = MagicMock()
        mock_manager.load.return_value = None
        mocker.patch("vibraphone.utils.context.SessionManager", return_value=mock_manager)

        exec_dir, session = get_execution_context()

        assert exec_dir == tmp_path
        assert session is None

    def test_returns_project_root_when_worktree_missing(
        self, mocker: Any, tmp_path: Path
    ) -> None:
        """When session exists but worktree path doesn't exist, falls back."""
        from vibraphone.utils.context import get_execution_context

        # Mock get_project_root
        mocker.patch("vibraphone.utils.context.get_project_root", return_value=tmp_path)

        # Create a mock session with non-existent worktree
        mock_session = MagicMock(spec=SessionState)
        mock_session.worktree_path = tmp_path / "nonexistent" / "worktree"
        # The path doesn't exist, so should fall back

        mock_manager = MagicMock()
        mock_manager.load.return_value = mock_session
        mocker.patch("vibraphone.utils.context.SessionManager", return_value=mock_manager)

        exec_dir, session = get_execution_context()

        assert exec_dir == tmp_path
        assert session is None

    def test_returns_worktree_when_session_exists(
        self, mocker: Any, tmp_path: Path
    ) -> None:
        """When session exists with valid worktree, returns worktree path."""
        from vibraphone.utils.context import get_execution_context
        from datetime import datetime

        # Mock get_project_root
        mocker.patch("vibraphone.utils.context.get_project_root", return_value=tmp_path)

        # Create a valid worktree path
        worktree_path = tmp_path / "worktrees" / "task-001"
        worktree_path.mkdir(parents=True)

        # Create a real SessionState
        session = SessionState(
            task_id="001",
            worktree_path=worktree_path,
            branch_name="feat/001-test",
            started_at=datetime.now(),
        )

        mock_manager = MagicMock()
        mock_manager.load.return_value = session
        mocker.patch("vibraphone.utils.context.SessionManager", return_value=mock_manager)

        exec_dir, returned_session = get_execution_context()

        assert exec_dir == worktree_path
        assert returned_session is session
        assert returned_session.task_id == "001"

    def test_uses_project_root_from_config(
        self, mocker: Any, tmp_path: Path
    ) -> None:
        """SessionManager is initialized with project root from config."""
        from vibraphone.utils.context import get_execution_context

        # Mock get_project_root to return specific path
        project_root = tmp_path / "my-project"
        project_root.mkdir()
        mocker.patch("vibraphone.utils.context.get_project_root", return_value=project_root)

        # Mock SessionManager constructor to track call
        mock_manager_class = mocker.patch("vibraphone.utils.context.SessionManager")
        mock_manager = MagicMock()
        mock_manager.load.return_value = None
        mock_manager_class.return_value = mock_manager

        get_execution_context()

        # Verify SessionManager was initialized with project_root
        mock_manager_class.assert_called_once_with(project_root)


class TestGetEffectiveTaskId:
    """Tests for get_effective_task_id helper function."""

    def test_returns_task_id_from_session(self, mocker: Any) -> None:
        """When session exists, returns session's task_id."""
        from vibraphone.utils.context import get_effective_task_id

        mock_session = MagicMock(spec=SessionState)
        mock_session.task_id = "001"

        result = get_effective_task_id(mock_session)

        assert result == "001"

    def test_returns_default_when_no_session(self, mocker: Any) -> None:
        """When session is None, returns 'default'."""
        from vibraphone.utils.context import get_effective_task_id

        result = get_effective_task_id(None)

        assert result == "default"

    def test_returns_various_task_ids(self, mocker: Any) -> None:
        """Returns whatever task_id is in the session."""
        from vibraphone.utils.context import get_effective_task_id

        for task_id in ["001", "002", "abc-123", "feature-xyz"]:
            mock_session = MagicMock(spec=SessionState)
            mock_session.task_id = task_id

            result = get_effective_task_id(mock_session)

            assert result == task_id
