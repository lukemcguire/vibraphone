"""Unit tests for worktree operations.

Tests worktree_ops.py functions with mocked git commands.
Uses pytest-mock for async subprocess mocking.
"""

# ruff: noqa: SLF001, S603
# SLF001: Private member access needed for mocking
# S603: Subprocess calls are mocked, not actual

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from vibraphone.utils.worktree_ops import (
    RebaseError,
    WorktreeError,
    check_branch_merged,
    check_uncommitted_changes,
    create_worktree,
    rebase_onto_main,
    remove_worktree,
)


class TestWorktreeError:
    """Tests for WorktreeError model."""

    def test_worktree_error_model(self) -> None:
        """Create and serialize WorktreeError."""
        error = WorktreeError(
            error_type="BranchAlreadyExists",
            message="Branch feat/test already exists",
            suggested_action="Run cleanup_task first",
        )

        data = error.model_dump()
        assert data["error_type"] == "BranchAlreadyExists"
        assert "already exists" in data["message"]
        assert data["suggested_action"] == "Run cleanup_task first"


class TestRebaseError:
    """Tests for RebaseError model."""

    def test_rebase_error_model(self) -> None:
        """Create and serialize RebaseError."""
        error = RebaseError(
            message="Rebase conflicts detected in 2 file(s)",
            suggested_action="Resolve conflicts manually",
            conflicted_files=["src/main.py", "src/utils.py"],
        )

        data = error.model_dump()
        assert data["error_type"] == "RebaseConflict"
        assert "2 file(s)" in data["message"]
        assert len(data["conflicted_files"]) == 2

    def test_rebase_error_with_conflicted_files(self) -> None:
        """RebaseError includes file list."""
        error = RebaseError(
            message="Conflicts in 3 files",
            suggested_action="Resolve",
            conflicted_files=["a.py", "b.py", "c.py"],
        )

        assert error.conflicted_files == ["a.py", "b.py", "c.py"]


class TestCreateWorktree:
    """Tests for create_worktree function."""

    @pytest.mark.asyncio
    async def test_create_worktree_success(self, mocker: Any, tmp_path: Path) -> None:
        """Mock git branch --list (empty), git worktree add returns 0."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))

        mocker.patch("asyncio.create_subprocess_exec", return_value=mock_proc)

        worktrees_path = tmp_path / "worktrees"
        repo_path = tmp_path / "repo"
        repo_path.mkdir()

        result = await create_worktree("bd-test", worktrees_path, repo_path, "repo")

        # Path should be worktrees_path / repo_name / task_id
        expected = worktrees_path / "repo" / "bd-test"
        assert result == expected

    @pytest.mark.asyncio
    async def test_create_worktree_branch_exists(self, mocker: Any, tmp_path: Path) -> None:
        """Mock git branch --list returns branch name, expect WorktreeError."""
        # First call: branch --list returns branch name (exists)
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"feat/bd-test\n", b""))

        mocker.patch("asyncio.create_subprocess_exec", return_value=mock_proc)

        worktrees_path = tmp_path / "worktrees"
        repo_path = tmp_path / "repo"
        repo_path.mkdir()

        with pytest.raises(WorktreeError) as exc_info:
            await create_worktree("bd-test", worktrees_path, repo_path, "repo")

        assert exc_info.value.error_type == "BranchAlreadyExists"

    @pytest.mark.asyncio
    async def test_create_worktree_creation_fails(self, mocker: Any, tmp_path: Path) -> None:
        """Mock git worktree add returns non-zero, expect WorktreeError."""
        mock_proc = MagicMock()

        # First call: branch check (empty)
        # Second call: worktree add (fails)
        call_count = [0]

        async def mock_communicate() -> tuple[bytes, bytes]:
            call_count[0] += 1
            if call_count[0] == 1:
                return (b"", b"")  # branch --list empty
            else:
                mock_proc.returncode = 1
                return (b"", b"fatal: worktree creation failed\n")

        mock_proc.communicate = mock_communicate
        mock_proc.returncode = 0  # First call succeeds

        mocker.patch("asyncio.create_subprocess_exec", return_value=mock_proc)

        worktrees_path = tmp_path / "worktrees"
        repo_path = tmp_path / "repo"
        repo_path.mkdir()

        with pytest.raises(WorktreeError) as exc_info:
            await create_worktree("bd-test", worktrees_path, repo_path, "repo")

        assert exc_info.value.error_type == "WorktreeCreationFailed"

    @pytest.mark.asyncio
    async def test_create_worktree_expands_tilde(self, mocker: Any, tmp_path: Path) -> None:
        """Verify worktrees_path.expanduser() called."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))

        mock_subprocess = mocker.patch("asyncio.create_subprocess_exec", return_value=mock_proc)

        # Use tilde path
        worktrees_path = Path("~/.vibraphone/worktrees")
        repo_path = tmp_path / "repo"
        repo_path.mkdir()

        result = await create_worktree("bd-test", worktrees_path, repo_path, "repo")

        # Verify the path was expanded in the subprocess call
        # The worktree add command should have expanded path
        assert "~" not in str(result)
        # Verify subprocess was called
        assert mock_subprocess.called


class TestRebaseOntoMain:
    """Tests for rebase_onto_main function."""

    @pytest.mark.asyncio
    async def test_rebase_success(self, mocker: Any, tmp_path: Path) -> None:
        """Mock git fetch, git rebase returns 0."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))

        mocker.patch("asyncio.create_subprocess_exec", return_value=mock_proc)

        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir()

        result = await rebase_onto_main(worktree_path, "feat/bd-test")

        assert result["success"] is True
        assert result["branch"] == "feat/bd-test"

    @pytest.mark.asyncio
    async def test_rebase_conflict(self, mocker: Any, tmp_path: Path) -> None:
        """Mock git rebase fails, git diff returns files, git rebase --abort called."""
        call_count = [0]

        def create_mock_proc(*args: str, **kwargs: str) -> MagicMock:
            mock_proc = MagicMock()

            async def mock_communicate() -> tuple[bytes, bytes]:
                call_count[0] += 1
                if call_count[0] == 1:
                    # git fetch
                    return (b"", b"")
                elif call_count[0] == 2:
                    # git rebase (fails)
                    mock_proc.returncode = 1
                    return (b"", b"CONFLICT\n")
                elif call_count[0] == 3:
                    # git diff --name-only --diff-filter=U
                    return (b"src/main.py\nsrc/utils.py\n", b"")
                else:
                    # git rebase --abort
                    return (b"", b"")

            mock_proc.communicate = mock_communicate
            mock_proc.returncode = 0
            return mock_proc

        mocker.patch("asyncio.create_subprocess_exec", side_effect=create_mock_proc)

        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir()

        with pytest.raises(RebaseError) as exc_info:
            await rebase_onto_main(worktree_path, "feat/bd-test")

        error = exc_info.value
        assert error.error_type == "RebaseConflict"
        assert len(error.conflicted_files) == 2
        assert "src/main.py" in error.conflicted_files

    @pytest.mark.asyncio
    async def test_rebase_aborts_on_failure(self, mocker: Any, tmp_path: Path) -> None:
        """Verify git rebase --abort called before raising."""
        subprocess_calls: list[tuple[str, ...]] = []

        async def mock_create_subprocess(*args: str, **kwargs: str) -> MagicMock:
            subprocess_calls.append(args)
            mock_proc = MagicMock()
            mock_proc.returncode = 0 if "--abort" in args else 1
            mock_proc.communicate = AsyncMock(
                return_value=(b"file.py\n" if "diff" in args else b"", b"")
            )
            return mock_proc

        mocker.patch("asyncio.create_subprocess_exec", side_effect=mock_create_subprocess)

        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir()

        with pytest.raises(RebaseError):
            await rebase_onto_main(worktree_path, "feat/bd-test")

        # Verify abort was called
        abort_called = any("--abort" in call for call in subprocess_calls)
        assert abort_called, "git rebase --abort should be called on failure"


class TestSafetyChecks:
    """Tests for safety check functions."""

    @pytest.mark.asyncio
    async def test_check_uncommitted_changes_clean(self, mocker: Any, tmp_path: Path) -> None:
        """Mock git status --porcelain returns empty."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))

        mocker.patch("asyncio.create_subprocess_exec", return_value=mock_proc)

        result = await check_uncommitted_changes(tmp_path)

        assert result == []

    @pytest.mark.asyncio
    async def test_check_uncommitted_changes_dirty(self, mocker: Any, tmp_path: Path) -> None:
        """Mock returns ' M file.txt', returns ['file.txt']."""
        # Git status --porcelain format: XY PATH where X and Y are status codes
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        # Real format: " M file.txt" (space, M, space, filename)
        mock_proc.communicate = AsyncMock(return_value=(b" M file.txt\nA  new_file.py\n", b""))

        mocker.patch("asyncio.create_subprocess_exec", return_value=mock_proc)

        result = await check_uncommitted_changes(tmp_path)

        assert len(result) == 2
        assert "file.txt" in result
        assert "new_file.py" in result

    @pytest.mark.asyncio
    async def test_check_branch_merged_true(self, mocker: Any, tmp_path: Path) -> None:
        """Mock git branch --merged returns branch name."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"feat/bd-test\n", b""))

        mocker.patch("asyncio.create_subprocess_exec", return_value=mock_proc)

        result = await check_branch_merged("feat/bd-test", tmp_path)

        assert result is True

    @pytest.mark.asyncio
    async def test_check_branch_merged_false(self, mocker: Any, tmp_path: Path) -> None:
        """Mock returns empty."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))

        mocker.patch("asyncio.create_subprocess_exec", return_value=mock_proc)

        result = await check_branch_merged("feat/bd-test", tmp_path)

        assert result is False


class TestRemoveWorktree:
    """Tests for remove_worktree function."""

    @pytest.mark.asyncio
    async def test_remove_worktree_success(self, mocker: Any, tmp_path: Path) -> None:
        """Mock git worktree remove returns 0."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))

        mocker.patch("asyncio.create_subprocess_exec", return_value=mock_proc)

        worktree_path = tmp_path / "worktree"
        repo_path = tmp_path / "repo"

        # Should not raise
        await remove_worktree(worktree_path, repo_path)

    @pytest.mark.asyncio
    async def test_remove_worktree_fails(self, mocker: Any, tmp_path: Path) -> None:
        """Mock git worktree remove fails, expect WorktreeError."""
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.communicate = AsyncMock(return_value=(b"", b"fatal: worktree in use\n"))

        mocker.patch("asyncio.create_subprocess_exec", return_value=mock_proc)

        worktree_path = tmp_path / "worktree"
        repo_path = tmp_path / "repo"

        with pytest.raises(WorktreeError) as exc_info:
            await remove_worktree(worktree_path, repo_path)

        assert exc_info.value.error_type == "WorktreeRemovalFailed"
