"""Git worktree operations with safety guards.

Provides async functions for worktree lifecycle management including
creation, rebase, cleanup, and safety checks with structured error handling.
"""

import asyncio
from pathlib import Path

from pydantic import BaseModel


class WorktreeError(BaseModel):
    """Structured error response for worktree operations.

    Provides consistent error format for worktree tools with
    actionable guidance for users. Follows TaskError pattern from task_tools.py.
    """

    error_type: str  # e.g., "BranchAlreadyExists", "UncommittedChanges"
    message: str  # Human-readable error message
    suggested_action: str  # What to do next


class RebaseError(BaseModel):
    """Structured error response for rebase conflicts.

    Extends WorktreeError pattern with conflict-specific details
    including the list of files with conflicts.
    """

    error_type: str = "RebaseConflict"
    message: str  # Includes conflict count
    suggested_action: str  # How to resolve
    conflicted_files: list[str]  # List of files with conflicts


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
