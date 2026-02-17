"""Worktree lifecycle management MCP tools for vibraphone.

This module contains MCP tool implementations for worktree lifecycle management
including start_task, merge_task, cleanup_task, and recover_session.
"""

import asyncio
from datetime import datetime

from vibraphone.config import get_config, get_project_root
from vibraphone.server import mcp
from vibraphone.utils.errors import TaskError
from vibraphone.utils.session import SessionManager, SessionState
from vibraphone.utils.worktree_ops import (
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


@mcp.tool
async def cleanup_task(task_id: str) -> dict:
    """Remove worktree and delete branch after merge.

    Safety guards prevent cleanup if uncommitted changes exist or
    branch not merged into main.

    Args:
        task_id: Task identifier

    Returns:
        Dict with success status and next_steps, or error if guards fail
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

    worktree_path = state.worktree_path
    branch_name = state.branch_name

    # Safety check: uncommitted changes
    changes = await check_uncommitted_changes(worktree_path)
    if changes:
        return TaskError(
            error_type="UncommittedChanges",
            message="Uncommitted changes in worktree. Commit or stash before cleanup.",
            suggested_action=f"Files with changes: {', '.join(changes[:5])}",
        ).model_dump()

    # Safety check: branch merged into main
    if not await check_branch_merged(branch_name, project_root):
        return TaskError(
            error_type="BranchNotMerged",
            message="Task branch not merged. Run merge_task first.",
            suggested_action="Run merge_task to rebase onto main",
        ).model_dump()

    # Remove worktree
    await remove_worktree(worktree_path, project_root)

    # Delete branch (ignore failure - might already be gone)
    delete = await asyncio.create_subprocess_exec(
        "git",
        "branch",
        "-d",
        branch_name,
        cwd=project_root,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await delete.communicate()

    # Clear session state
    session.clear()

    return {
        "success": True,
        "next_steps": [
            "Worktree removed and branch deleted",
            "Task is complete - mark it complete with complete_task",
        ],
    }


@mcp.tool
async def recover_session() -> dict:
    """Check for stale session and return state.

    Returns session info if active session exists, or message if none.
    Use this after server startup to resume interrupted work.

    Returns:
        Dict with session info, message, and next_steps if session found,
        or session=None with message if no session or stale session detected.
    """
    project_root = get_project_root()
    session = SessionManager(project_root)
    state = session.load()

    if not state:
        return {
            "session": None,
            "message": "No active session found",
        }

    # Check if worktree still exists
    if not state.worktree_path.exists():
        return {
            "session": None,
            "message": f"Stale session for task {state.task_id} - worktree no longer exists",
            "suggested_action": "Run cleanup_task to clear session, or start_task to begin fresh",
        }

    # Valid session found
    return {
        "session": {
            "task_id": state.task_id,
            "worktree_path": str(state.worktree_path),
            "branch_name": state.branch_name,
            "started_at": state.started_at.isoformat(),
        },
        "message": f"Session found for task {state.task_id}",
        "next_steps": [
            f"Continue work: cd {state.worktree_path}",
            f"Or clean up: cleanup_task {state.task_id}",
        ],
    }
