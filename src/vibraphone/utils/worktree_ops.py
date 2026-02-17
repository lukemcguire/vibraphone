"""Git worktree operations with safety guards.

Provides async functions for worktree lifecycle management including
creation, rebase, cleanup, and safety checks with structured error handling.
"""

import asyncio
from pathlib import Path


class WorktreeError(Exception):
    """Structured error response for worktree operations.

    Provides consistent error format for worktree tools with
    actionable guidance for users. Follows TaskError pattern from task_tools.py
    but extends Exception so it can be raised and caught.
    """

    error_type: str  # e.g., "BranchAlreadyExists", "UncommittedChanges"
    message: str  # Human-readable error message
    suggested_action: str  # What to do next

    def __init__(
        self,
        error_type: str,
        message: str,
        suggested_action: str,
    ) -> None:
        self.error_type = error_type
        self.message = message
        self.suggested_action = suggested_action
        super().__init__(message)

    def model_dump(self) -> dict:
        """Serialize error to dict for MCP response."""
        return {
            "error_type": self.error_type,
            "message": self.message,
            "suggested_action": self.suggested_action,
        }


class RebaseError(Exception):
    """Structured error response for rebase conflicts.

    Extends WorktreeError pattern with conflict-specific details
    including the list of files with conflicts.
    """

    error_type: str = "RebaseConflict"
    message: str  # Includes conflict count
    suggested_action: str  # How to resolve
    conflicted_files: list[str]  # List of files with conflicts

    def __init__(
        self,
        message: str,
        suggested_action: str,
        conflicted_files: list[str],
        error_type: str = "RebaseConflict",
    ) -> None:
        self.error_type = error_type
        self.message = message
        self.suggested_action = suggested_action
        self.conflicted_files = conflicted_files
        super().__init__(message)

    def model_dump(self) -> dict:
        """Serialize error to dict for MCP response."""
        return {
            "error_type": self.error_type,
            "message": self.message,
            "suggested_action": self.suggested_action,
            "conflicted_files": self.conflicted_files,
        }


async def create_worktree(
    task_id: str,
    worktrees_path: Path,
    project_root: Path,
    repo_name: str,
) -> Path:
    """Create git worktree for task with new branch from main.

    Creates worktree at {worktrees_path}/{repo_name}/{task_id}/
    with branch feat/{task_id} from main.

    Args:
        task_id: Task identifier (from br output)
        worktrees_path: Base path for worktrees (from config)
        project_root: Main repository root
        repo_name: Repository directory name

    Returns:
        Path to created worktree

    Raises:
        WorktreeError: If branch exists or creation fails
    """
    # Expand tilde in worktrees_path
    worktrees_path = worktrees_path.expanduser()

    # Build worktree path and branch name
    worktree_path = worktrees_path / repo_name / task_id
    branch_name = f"feat/{task_id}"

    # Create parent directories
    worktree_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if branch already exists (collision handling)
    check = await asyncio.create_subprocess_exec(
        "git",
        "branch",
        "--list",
        branch_name,
        cwd=project_root,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await check.communicate()

    if stdout.decode().strip():
        raise WorktreeError(
            error_type="BranchAlreadyExists",
            message=f"Branch {branch_name} already exists - task may already be in progress",
            suggested_action="Check existing worktrees with 'git worktree list' or cleanup previous attempt",
        )

    # Create worktree with new branch from main
    process = await asyncio.create_subprocess_exec(
        "git",
        "worktree",
        "add",
        "-b",
        branch_name,
        str(worktree_path),
        "main",
        cwd=project_root,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()

    if process.returncode != 0:
        raise WorktreeError(
            error_type="WorktreeCreationFailed",
            message=f"Failed to create worktree: {stderr.decode().strip()}",
            suggested_action="Check disk space and permissions",
        )

    return worktree_path


async def rebase_onto_main(worktree_path: Path, branch_name: str) -> dict:
    """Rebase task branch onto main with conflict detection and abort.

    Fetches latest main, then rebases current branch onto origin/main.
    On conflict, aborts rebase and returns detailed conflict information.

    Args:
        worktree_path: Path to task worktree
        branch_name: Branch being rebased

    Returns:
        Dict with success status and branch name

    Raises:
        RebaseError: If rebase fails with conflicts (includes conflicted_files)
    """
    # Fetch latest main (ignore returncode - might be offline)
    fetch = await asyncio.create_subprocess_exec(
        "git",
        "fetch",
        "origin",
        "main",
        cwd=worktree_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await fetch.communicate()

    # Attempt rebase onto origin/main
    process = await asyncio.create_subprocess_exec(
        "git",
        "rebase",
        "origin/main",
        cwd=worktree_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _stdout, _stderr = await process.communicate()

    if process.returncode == 0:
        return {"success": True, "branch": branch_name}

    # On conflict: get conflicted files, abort rebase, raise error
    diff_process = await asyncio.create_subprocess_exec(
        "git",
        "diff",
        "--name-only",
        "--diff-filter=U",
        cwd=worktree_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await diff_process.communicate()
    conflicted_files = [f for f in stdout.decode().strip().split("\n") if f]

    # CRITICAL: Abort rebase to restore clean state
    abort = await asyncio.create_subprocess_exec(
        "git",
        "rebase",
        "--abort",
        cwd=worktree_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await abort.communicate()

    raise RebaseError(
        error_type="RebaseConflict",
        message=f"Rebase conflicts detected in {len(conflicted_files)} file(s)",
        suggested_action="Resolve conflicts manually, then retry merge_task",
        conflicted_files=conflicted_files,
    )


async def check_uncommitted_changes(worktree_path: Path) -> list[str]:
    """Check for uncommitted changes in worktree.

    Runs git status --porcelain and parses output to get list of
    changed files. Each line in output is "XY filename" format.

    Args:
        worktree_path: Path to the worktree to check

    Returns:
        List of changed filenames (empty if clean)
    """
    process = await asyncio.create_subprocess_exec(
        "git",
        "status",
        "--porcelain",
        cwd=worktree_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await process.communicate()

    # Split by newline, strip trailing whitespace only, filter empty lines
    lines = stdout.decode().rstrip("\n").split("\n")
    # Each line is "XY filename" - extract filename starting at position 3
    return [line[3:] for line in lines if line]


async def check_branch_merged(branch_name: str, project_root: Path) -> bool:
    """Check if branch is merged into main.

    Runs git branch --merged main --list to check if the branch
    appears in the list of branches merged into main.

    Args:
        branch_name: Name of the branch to check
        project_root: Main repository root

    Returns:
        True if branch is merged into main, False otherwise
    """
    process = await asyncio.create_subprocess_exec(
        "git",
        "branch",
        "--merged",
        "main",
        "--list",
        branch_name,
        cwd=project_root,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await process.communicate()

    return bool(stdout.decode().strip())


async def remove_worktree(worktree_path: Path, project_root: Path) -> None:
    """Remove git worktree.

    Removes the worktree directory from the repository. This function
    should be called after safety checks pass in cleanup_task.

    Note: Branch deletion is separate (done in cleanup_task MCP tool).

    Args:
        worktree_path: Path to the worktree to remove
        project_root: Main repository root

    Raises:
        WorktreeError: If worktree removal fails
    """
    process = await asyncio.create_subprocess_exec(
        "git",
        "worktree",
        "remove",
        str(worktree_path),
        cwd=project_root,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()

    if process.returncode != 0:
        raise WorktreeError(
            error_type="WorktreeRemovalFailed",
            message=f"Failed to remove worktree: {stderr.decode().strip()}",
            suggested_action="Check if worktree directory is in use",
        )
