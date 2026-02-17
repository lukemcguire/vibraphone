"""Unit tests for worktree MCP tools.

Tests worktree_tools.py MCP tool implementations with mocked operations.
Uses pytest-mock for mocking session and worktree operations.
"""

from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from vibraphone.utils.session import SessionState
from vibraphone.utils.worktree_ops import RebaseError, WorktreeError


class TestStartTask:
    """Tests for start_task MCP tool."""

    @pytest.mark.asyncio
    async def test_start_task_success(self, mocker: Any, tmp_path: Path) -> None:
        """Mock create_worktree, verify session saved, verify next_steps."""
        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir()

        mock_create = mocker.patch(
            "vibraphone.tools.worktree_tools.create_worktree",
            new_callable=AsyncMock,
            return_value=worktree_path,
        )

        mock_session_class = mocker.patch("vibraphone.tools.worktree_tools.SessionManager")
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_get_config = mocker.patch("vibraphone.tools.worktree_tools.get_config")
        mock_get_config.return_value.worktrees_path = tmp_path / "wt"

        mock_get_root = mocker.patch("vibraphone.tools.worktree_tools.get_project_root")
        mock_get_root.return_value = tmp_path

        from vibraphone.tools.worktree_tools import start_task

        result = await start_task.fn("bd-test")

        # Verify create_worktree was called
        assert mock_create.called
        # Verify session was saved
        assert mock_session.save.called
        # Verify result structure
        assert result["branch_name"] == "feat/bd-test"
        assert "worktree_path" in result
        assert "next_steps" in result
        assert len(result["next_steps"]) == 3

    @pytest.mark.asyncio
    async def test_start_task_worktree_error(self, mocker: Any, tmp_path: Path) -> None:
        """Mock create_worktree raises WorktreeError, verify propagated."""
        mock_create = mocker.patch(
            "vibraphone.tools.worktree_tools.create_worktree",
            new_callable=AsyncMock,
            side_effect=WorktreeError(
                error_type="BranchAlreadyExists",
                message="Branch feat/bd-test already exists",
                suggested_action="Cleanup first",
            ),
        )

        mocker.patch("vibraphone.tools.worktree_tools.get_config")
        mocker.patch("vibraphone.tools.worktree_tools.get_project_root", return_value=tmp_path)

        from vibraphone.tools.worktree_tools import start_task

        with pytest.raises(WorktreeError) as exc_info:
            await start_task.fn("bd-test")

        assert exc_info.value.error_type == "BranchAlreadyExists"
        assert mock_create.called


class TestMergeTask:
    """Tests for merge_task MCP tool."""

    @pytest.mark.asyncio
    async def test_merge_task_success(self, mocker: Any, tmp_path: Path) -> None:
        """Mock session.load returns state, mock rebase_onto_main succeeds."""
        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir()

        mock_state = SessionState(
            task_id="bd-test",
            worktree_path=worktree_path,
            branch_name="feat/bd-test",
            started_at=datetime.now(),
        )

        mock_session_class = mocker.patch("vibraphone.tools.worktree_tools.SessionManager")
        mock_session = MagicMock()
        mock_session.load.return_value = mock_state
        mock_session_class.return_value = mock_session

        mock_rebase = mocker.patch(
            "vibraphone.tools.worktree_tools.rebase_onto_main",
            new_callable=AsyncMock,
            return_value={"success": True, "branch": "feat/bd-test"},
        )

        mocker.patch("vibraphone.tools.worktree_tools.get_project_root", return_value=tmp_path)

        from vibraphone.tools.worktree_tools import merge_task

        result = await merge_task.fn("bd-test")

        assert result["success"] is True
        assert result["branch"] == "feat/bd-test"
        assert "next_steps" in result
        assert mock_rebase.called

    @pytest.mark.asyncio
    async def test_merge_task_no_session(self, mocker: Any, tmp_path: Path) -> None:
        """Mock session.load returns None, verify error response."""
        mock_session_class = mocker.patch("vibraphone.tools.worktree_tools.SessionManager")
        mock_session = MagicMock()
        mock_session.load.return_value = None
        mock_session_class.return_value = mock_session

        mocker.patch("vibraphone.tools.worktree_tools.get_project_root", return_value=tmp_path)

        from vibraphone.tools.worktree_tools import merge_task

        result = await merge_task.fn("bd-test")

        assert "error_type" in result
        assert result["error_type"] == "NoActiveSession"

    @pytest.mark.asyncio
    async def test_merge_task_wrong_task(self, mocker: Any, tmp_path: Path) -> None:
        """Mock session with different task_id, verify error."""
        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir()

        mock_state = SessionState(
            task_id="bd-other",  # Different task
            worktree_path=worktree_path,
            branch_name="feat/bd-other",
            started_at=datetime.now(),
        )

        mock_session_class = mocker.patch("vibraphone.tools.worktree_tools.SessionManager")
        mock_session = MagicMock()
        mock_session.load.return_value = mock_state
        mock_session_class.return_value = mock_session

        mocker.patch("vibraphone.tools.worktree_tools.get_project_root", return_value=tmp_path)

        from vibraphone.tools.worktree_tools import merge_task

        result = await merge_task.fn("bd-test")

        assert "error_type" in result
        assert result["error_type"] == "NoActiveSession"

    @pytest.mark.asyncio
    async def test_merge_task_conflict(self, mocker: Any, tmp_path: Path) -> None:
        """Mock rebase_onto_main raises RebaseError, verify error response with files."""
        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir()

        mock_state = SessionState(
            task_id="bd-test",
            worktree_path=worktree_path,
            branch_name="feat/bd-test",
            started_at=datetime.now(),
        )

        mock_session_class = mocker.patch("vibraphone.tools.worktree_tools.SessionManager")
        mock_session = MagicMock()
        mock_session.load.return_value = mock_state
        mock_session_class.return_value = mock_session

        mock_rebase = mocker.patch(
            "vibraphone.tools.worktree_tools.rebase_onto_main",
            new_callable=AsyncMock,
            side_effect=RebaseError(
                message="Rebase conflicts detected in 2 file(s)",
                suggested_action="Resolve conflicts manually",
                conflicted_files=["src/main.py", "src/utils.py"],
            ),
        )

        mocker.patch("vibraphone.tools.worktree_tools.get_project_root", return_value=tmp_path)

        from vibraphone.tools.worktree_tools import merge_task

        result = await merge_task.fn("bd-test")

        assert "error_type" in result
        assert result["error_type"] == "RebaseConflict"
        assert "conflicted_files" in result
        assert "src/main.py" in result["conflicted_files"]
        assert mock_rebase.called


class TestCleanupTask:
    """Tests for cleanup_task MCP tool."""

    @pytest.mark.asyncio
    async def test_cleanup_task_success(self, mocker: Any, tmp_path: Path) -> None:
        """Mock all safety checks pass, verify worktree removed, branch deleted, session cleared."""
        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir()

        mock_state = SessionState(
            task_id="bd-test",
            worktree_path=worktree_path,
            branch_name="feat/bd-test",
            started_at=datetime.now(),
        )

        mock_session_class = mocker.patch("vibraphone.tools.worktree_tools.SessionManager")
        mock_session = MagicMock()
        mock_session.load.return_value = mock_state
        mock_session_class.return_value = mock_session

        mocker.patch(
            "vibraphone.tools.worktree_tools.check_uncommitted_changes",
            new_callable=AsyncMock,
            return_value=[],
        )

        mocker.patch(
            "vibraphone.tools.worktree_tools.check_branch_merged",
            new_callable=AsyncMock,
            return_value=True,
        )

        mock_remove = mocker.patch(
            "vibraphone.tools.worktree_tools.remove_worktree",
            new_callable=AsyncMock,
        )

        # Mock asyncio.create_subprocess_exec for branch deletion
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))
        mocker.patch("asyncio.create_subprocess_exec", return_value=mock_proc)

        mocker.patch("vibraphone.tools.worktree_tools.get_project_root", return_value=tmp_path)

        from vibraphone.tools.worktree_tools import cleanup_task

        result = await cleanup_task.fn("bd-test")

        assert result["success"] is True
        assert "next_steps" in result
        assert mock_remove.called
        assert mock_session.clear.called

    @pytest.mark.asyncio
    async def test_cleanup_task_no_session(self, mocker: Any, tmp_path: Path) -> None:
        """Verify error response when no session."""
        mock_session_class = mocker.patch("vibraphone.tools.worktree_tools.SessionManager")
        mock_session = MagicMock()
        mock_session.load.return_value = None
        mock_session_class.return_value = mock_session

        mocker.patch("vibraphone.tools.worktree_tools.get_project_root", return_value=tmp_path)

        from vibraphone.tools.worktree_tools import cleanup_task

        result = await cleanup_task.fn("bd-test")

        assert "error_type" in result
        assert result["error_type"] == "NoActiveSession"

    @pytest.mark.asyncio
    async def test_cleanup_task_uncommitted(self, mocker: Any, tmp_path: Path) -> None:
        """Mock check_uncommitted_changes returns files, verify error."""
        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir()

        mock_state = SessionState(
            task_id="bd-test",
            worktree_path=worktree_path,
            branch_name="feat/bd-test",
            started_at=datetime.now(),
        )

        mock_session_class = mocker.patch("vibraphone.tools.worktree_tools.SessionManager")
        mock_session = MagicMock()
        mock_session.load.return_value = mock_state
        mock_session_class.return_value = mock_session

        mocker.patch(
            "vibraphone.tools.worktree_tools.check_uncommitted_changes",
            new_callable=AsyncMock,
            return_value=["src/main.py", "src/utils.py"],
        )

        mocker.patch("vibraphone.tools.worktree_tools.get_project_root", return_value=tmp_path)

        from vibraphone.tools.worktree_tools import cleanup_task

        result = await cleanup_task.fn("bd-test")

        assert "error_type" in result
        assert result["error_type"] == "UncommittedChanges"

    @pytest.mark.asyncio
    async def test_cleanup_task_not_merged(self, mocker: Any, tmp_path: Path) -> None:
        """Mock check_branch_merged returns False, verify error."""
        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir()

        mock_state = SessionState(
            task_id="bd-test",
            worktree_path=worktree_path,
            branch_name="feat/bd-test",
            started_at=datetime.now(),
        )

        mock_session_class = mocker.patch("vibraphone.tools.worktree_tools.SessionManager")
        mock_session = MagicMock()
        mock_session.load.return_value = mock_state
        mock_session_class.return_value = mock_session

        mocker.patch(
            "vibraphone.tools.worktree_tools.check_uncommitted_changes",
            new_callable=AsyncMock,
            return_value=[],
        )

        mocker.patch(
            "vibraphone.tools.worktree_tools.check_branch_merged",
            new_callable=AsyncMock,
            return_value=False,
        )

        mocker.patch("vibraphone.tools.worktree_tools.get_project_root", return_value=tmp_path)

        from vibraphone.tools.worktree_tools import cleanup_task

        result = await cleanup_task.fn("bd-test")

        assert "error_type" in result
        assert result["error_type"] == "BranchNotMerged"


class TestRecoverSession:
    """Tests for recover_session MCP tool."""

    @pytest.mark.asyncio
    async def test_recover_session_no_session(self, mocker: Any, tmp_path: Path) -> None:
        """Mock session.load returns None, verify 'No active session'."""
        mock_session_class = mocker.patch("vibraphone.tools.worktree_tools.SessionManager")
        mock_session = MagicMock()
        mock_session.load.return_value = None
        mock_session_class.return_value = mock_session

        mocker.patch("vibraphone.tools.worktree_tools.get_project_root", return_value=tmp_path)

        from vibraphone.tools.worktree_tools import recover_session

        result = await recover_session.fn()

        assert result["session"] is None
        assert "No active session" in result["message"]

    @pytest.mark.asyncio
    async def test_recover_session_valid(self, mocker: Any, tmp_path: Path) -> None:
        """Mock session.load returns state, mock path.exists True, verify session returned."""
        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir()

        mock_state = SessionState(
            task_id="bd-test",
            worktree_path=worktree_path,
            branch_name="feat/bd-test",
            started_at=datetime(2026, 2, 16, 12, 0, 0),
        )

        mock_session_class = mocker.patch("vibraphone.tools.worktree_tools.SessionManager")
        mock_session = MagicMock()
        mock_session.load.return_value = mock_state
        mock_session_class.return_value = mock_session

        mocker.patch("vibraphone.tools.worktree_tools.get_project_root", return_value=tmp_path)

        from vibraphone.tools.worktree_tools import recover_session

        result = await recover_session.fn()

        assert result["session"] is not None
        assert result["session"]["task_id"] == "bd-test"
        assert result["session"]["branch_name"] == "feat/bd-test"
        assert "message" in result
        assert "next_steps" in result

    @pytest.mark.asyncio
    async def test_recover_session_stale(self, mocker: Any, tmp_path: Path) -> None:
        """Mock session exists but worktree_path doesn't exist, verify stale message."""
        # Path that doesn't exist
        nonexistent_path = tmp_path / "nonexistent_worktree"

        mock_state = SessionState(
            task_id="bd-test",
            worktree_path=nonexistent_path,
            branch_name="feat/bd-test",
            started_at=datetime.now(),
        )

        mock_session_class = mocker.patch("vibraphone.tools.worktree_tools.SessionManager")
        mock_session = MagicMock()
        mock_session.load.return_value = mock_state
        mock_session_class.return_value = mock_session

        mocker.patch("vibraphone.tools.worktree_tools.get_project_root", return_value=tmp_path)

        from vibraphone.tools.worktree_tools import recover_session

        result = await recover_session.fn()

        assert result["session"] is None
        assert "Stale session" in result["message"]
        assert "suggested_action" in result
