"""Success criteria tests for Phase 4 Worktree & Session Tools.

Tests verify all ROADMAP requirements for Phase 4:
- WKTREE-01: start_task creates worktree at configured path
- WKTREE-02: merge_task rebases onto main
- WKTREE-03: cleanup_task removes worktree with guards
- WKTREE-04: configurable worktrees_path from config
- SESS-01: server startup checks for stale session
- SESS-02: recover_session returns session state
- SESS-03: session persists to .vibraphone/session.json

Each test is named by requirement ID for ROADMAP traceability.
"""

from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from vibraphone.utils.session import SessionManager, SessionState


class TestPhase4SuccessCriteria:
    """Verify all Phase 4 requirements from ROADMAP.md."""

    @pytest.mark.asyncio
    async def test_WKTREE_01_start_task(self, mocker: Any, tmp_path: Path) -> None:
        """WKTREE-01: Verify start_task creates worktree at configured path.

        The worktree should be created at {worktrees_path}/{repo-name}/{task-id}/
        with branch name feat/{task-id} from main.
        """
        worktrees_path = tmp_path / "custom_worktrees"
        worktree_path = worktrees_path / "myrepo" / "bd-test"
        worktree_path.mkdir(parents=True)

        mock_create = mocker.patch(
            "vibraphone.tools.worktree_tools.create_worktree",
            new_callable=AsyncMock,
            return_value=worktree_path,
        )

        mock_session_class = mocker.patch("vibraphone.tools.worktree_tools.SessionManager")
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock config to return custom worktrees_path
        mock_config = MagicMock()
        mock_config.worktrees_path = worktrees_path
        mocker.patch("vibraphone.tools.worktree_tools.get_config", return_value=mock_config)

        mocker.patch(
            "vibraphone.tools.worktree_tools.get_project_root",
            return_value=tmp_path / "myrepo",
        )

        from vibraphone.tools.worktree_tools import start_task

        result = await start_task.fn("bd-test")

        # Verify path uses config.worktrees_path
        assert mock_create.called
        call_kwargs = mock_create.call_args
        assert call_kwargs[1]["worktrees_path"] == worktrees_path

        # Verify branch_name is feat/{task-id}
        assert result["branch_name"] == "feat/bd-test"

    @pytest.mark.asyncio
    async def test_WKTREE_02_merge_task(self, mocker: Any, tmp_path: Path) -> None:
        """WKTREE-02: Verify merge_task rebases onto main.

        The merge should use rebase onto origin/main pattern.
        On conflict, should return file list.
        """
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

        # Mock rebase_onto_main to verify origin/main pattern
        mock_rebase = mocker.patch(
            "vibraphone.tools.worktree_tools.rebase_onto_main",
            new_callable=AsyncMock,
            return_value={"success": True, "branch": "feat/bd-test"},
        )

        mocker.patch("vibraphone.tools.worktree_tools.get_project_root", return_value=tmp_path)

        from vibraphone.tools.worktree_tools import merge_task

        result = await merge_task.fn("bd-test")

        # Verify rebase_onto_main was called
        assert mock_rebase.called
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_WKTREE_02_merge_task_conflict(self, mocker: Any, tmp_path: Path) -> None:
        """WKTREE-02: Verify merge_task handles conflicts with file list."""
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

        from vibraphone.utils.worktree_ops import RebaseError

        _mock_rebase = mocker.patch(
            "vibraphone.tools.worktree_tools.rebase_onto_main",
            new_callable=AsyncMock,
            side_effect=RebaseError(
                message="Rebase conflicts in 2 file(s)",
                suggested_action="Resolve conflicts",
                conflicted_files=["src/main.py", "src/utils.py"],
            ),
        )

        mocker.patch("vibraphone.tools.worktree_tools.get_project_root", return_value=tmp_path)

        from vibraphone.tools.worktree_tools import merge_task

        result = await merge_task.fn("bd-test")

        # Verify conflict handling returns file list
        assert result["error_type"] == "RebaseConflict"
        assert "conflicted_files" in result
        assert len(result["conflicted_files"]) == 2
        assert "src/main.py" in result["conflicted_files"]

    @pytest.mark.asyncio
    async def test_WKTREE_03_cleanup_task(self, mocker: Any, tmp_path: Path) -> None:
        """WKTREE-03: Verify cleanup removes worktree with guards.

        Safety checks should be called before removal:
        - check_uncommitted_changes
        - check_branch_merged
        """
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

        mock_uncommitted = mocker.patch(
            "vibraphone.tools.worktree_tools.check_uncommitted_changes",
            new_callable=AsyncMock,
            return_value=[],
        )

        mock_merged = mocker.patch(
            "vibraphone.tools.worktree_tools.check_branch_merged",
            new_callable=AsyncMock,
            return_value=True,
        )

        mock_remove = mocker.patch(
            "vibraphone.tools.worktree_tools.remove_worktree",
            new_callable=AsyncMock,
        )

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))
        mocker.patch("asyncio.create_subprocess_exec", return_value=mock_proc)

        mocker.patch("vibraphone.tools.worktree_tools.get_project_root", return_value=tmp_path)

        from vibraphone.tools.worktree_tools import cleanup_task

        result = await cleanup_task.fn("bd-test")

        # Verify safety checks called before removal
        assert mock_uncommitted.called
        assert mock_merged.called
        assert mock_remove.called
        assert mock_session.clear.called
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_WKTREE_04_configurable_path(self, mocker: Any, tmp_path: Path) -> None:
        """WKTREE-04: Verify worktrees_path from config used.

        The config.worktrees_path should be passed to create_worktree.
        """
        custom_path = tmp_path / "custom_location"
        worktree_path = custom_path / "myrepo" / "bd-test"
        worktree_path.mkdir(parents=True)

        mock_create = mocker.patch(
            "vibraphone.tools.worktree_tools.create_worktree",
            new_callable=AsyncMock,
            return_value=worktree_path,
        )

        mock_session_class = mocker.patch("vibraphone.tools.worktree_tools.SessionManager")
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock config returning custom path
        mock_config = MagicMock()
        mock_config.worktrees_path = custom_path
        mocker.patch("vibraphone.tools.worktree_tools.get_config", return_value=mock_config)

        mocker.patch(
            "vibraphone.tools.worktree_tools.get_project_root",
            return_value=tmp_path / "myrepo",
        )

        from vibraphone.tools.worktree_tools import start_task

        await start_task.fn("bd-test")

        # Verify custom path was passed to create_worktree
        assert mock_create.called
        assert mock_create.call_args[1]["worktrees_path"] == custom_path

    @pytest.mark.asyncio
    async def test_SESS_01_startup_detection(self, mocker: Any, tmp_path: Path) -> None:
        """SESS-01: Verify server startup checks for stale session.

        When vibraphone.yaml is detected, check_stale_session should be called
        and log a message if a session is found.
        """
        # Mock find_config_file to return a path
        mocker.patch(
            "vibraphone.server.find_config_file",
            return_value=tmp_path / "vibraphone.yaml",
        )

        # Mock session to have a state
        mock_state = SessionState(
            task_id="bd-test",
            worktree_path=tmp_path / "worktree",
            branch_name="feat/bd-test",
            started_at=datetime(2026, 2, 16, 12, 0, 0),
        )

        # SessionManager is imported locally in check_stale_session, so patch there
        mock_session_class = mocker.patch("vibraphone.utils.session.SessionManager")
        mock_session = MagicMock()
        mock_session.load.return_value = mock_state
        mock_session_class.return_value = mock_session

        # Capture stderr
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            from vibraphone.server import check_stale_session

            check_stale_session()

            # Verify message logged to stderr
            output = mock_stderr.getvalue()
            assert "Session found" in output
            assert "bd-test" in output
            assert "recover_session" in output

    @pytest.mark.asyncio
    async def test_SESS_02_recover_session(self, mocker: Any, tmp_path: Path) -> None:
        """SESS-02: Verify recover_session returns session state.

        When session exists, should return session dict.
        When no session, should return None.
        """
        # Test with no session
        mock_session_class = mocker.patch("vibraphone.tools.worktree_tools.SessionManager")
        mock_session = MagicMock()
        mock_session.load.return_value = None
        mock_session_class.return_value = mock_session

        mocker.patch("vibraphone.tools.worktree_tools.get_project_root", return_value=tmp_path)

        from vibraphone.tools.worktree_tools import recover_session

        result = await recover_session.fn()
        assert result["session"] is None

        # Test with valid session
        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir()

        mock_state = SessionState(
            task_id="bd-test",
            worktree_path=worktree_path,
            branch_name="feat/bd-test",
            started_at=datetime(2026, 2, 16, 12, 0, 0),
        )

        mock_session.load.return_value = mock_state

        result = await recover_session.fn()

        assert result["session"] is not None
        assert result["session"]["task_id"] == "bd-test"
        assert result["session"]["branch_name"] == "feat/bd-test"

    @pytest.mark.asyncio
    async def test_SESS_03_session_persistence(self, tmp_path: Path) -> None:
        """SESS-03: Verify session persists to .vibraphone/session.json.

        Session should be saved to and loaded from the correct path.
        """
        session = SessionManager(tmp_path)

        # Create session
        state = SessionState(
            task_id="bd-test",
            worktree_path=tmp_path / "worktree",
            branch_name="feat/bd-test",
            started_at=datetime(2026, 2, 16, 12, 0, 0),
        )

        # Save session
        session.save(state)

        # Verify file exists at correct path
        session_file = tmp_path / ".vibraphone" / "session.json"
        assert session_file.exists()

        # Load session
        loaded = session.load()

        # Verify all fields present
        assert loaded is not None
        assert loaded.task_id == "bd-test"
        assert loaded.branch_name == "feat/bd-test"
        assert loaded.worktree_path == tmp_path / "worktree"
        assert loaded.started_at.year == 2026
