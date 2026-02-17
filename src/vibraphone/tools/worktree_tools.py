"""Worktree lifecycle management MCP tools for vibraphone.

This module contains MCP tool implementations for worktree lifecycle management
including start_task, merge_task, cleanup_task, and recover_session.
"""

import asyncio
from datetime import datetime
from pathlib import Path

from vibraphone.config import get_config
from vibraphone.server import mcp
from vibraphone.tools.task_tools import TaskError, get_project_root
from vibraphone.utils.session import SessionManager, SessionState
from vibraphone.utils.worktree_ops import (
    WorktreeError,
    check_branch_merged,
    check_uncommitted_changes,
    create_worktree,
    rebase_onto_main,
    remove_worktree,
)


@mcp.tool
async def start_task(task_id: str) -> dict:
    """Start task in isolated git worktree.

    Creates worktree at {worktrees_path}/{repo-name}/{task-id}/
    with branch feat/{task-id} from main.

    Args:
        task_id: Task identifier (from br output, e.g., bd-abc123)

    Returns:
        Dict with worktree_path, branch_name, and next_steps per CONTEXT.md

    Raises:
        WorktreeError: If branch exists or creation fails (propagates to MCP)
    """
    config = get_config()
    project_root = get_project_root()
    repo_name = project_root.name

    # Create worktree with new branch from main
    worktree_path = await create_worktree(
        task_id=task_id,
        worktrees_path=config.worktrees_path,
        project_root=project_root,
        repo_name=repo_name,
    )

    branch_name = f"feat/{task_id}"

    # Save session state
    session = SessionManager(project_root)
    session.save(
        SessionState(
            task_id=task_id,
            worktree_path=worktree_path,
            branch_name=branch_name,
            started_at=datetime.now(),
        )
    )

    return {
        "worktree_path": str(worktree_path),
        "branch_name": branch_name,
        "next_steps": [
            f"Work in the worktree: cd {worktree_path}",
            "Make changes and commit them",
            "When done, call merge_task to integrate into main",
        ],
    }


@mcp.tool
async def merge_task(task_id: str) -> dict:
    """Rebase task branch into main.

    Args:
        task_id: Task identifier

    Returns:
        Dict with success status and next_steps, or error with conflict details
    """
    project_root = get_project_root()
    session = SessionManager(project_root)
    state = session.load()

    # Check for active session matching this task
    if not state or state.task_id != task_id:
        return TaskError(
            error_type="NoActiveSession",
            message=f"No active session for task {task_id}",
            suggested_action="Run start_task first",
        ).model_dump()

    branch_name = state.branch_name
    worktree_path = state.worktree_path

    # Attempt rebase - let RebaseError propagate (includes conflict info)
    try:
        await rebase_onto_main(worktree_path, branch_name)
    except Exception as e:
        # RebaseError and WorktreeError both have model_dump()
        if hasattr(e, "model_dump"):
            return e.model_dump()
        raise

    # Session is NOT cleared after merge - cleanup_task handles that
    return {
        "success": True,
        "branch": branch_name,
        "next_steps": [
            "Rebase successful",
            "Run cleanup_task to remove worktree and delete branch",
        ],
    }
