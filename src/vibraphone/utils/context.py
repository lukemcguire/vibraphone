"""Execution context resolution for session-aware command execution.

Provides helpers to determine the correct execution directory based on
whether an active session exists. This bridges session state to quality
gate execution.

When a session exists with a valid worktree, quality gates execute
in the worktree. Otherwise, they fall back to project root.
"""

from pathlib import Path

from vibraphone.config import get_project_root
from vibraphone.utils.session import SessionManager, SessionState


def get_execution_context() -> tuple[Path, SessionState | None]:
    """Get the execution context for quality gate commands.

    Determines whether commands should run in a worktree or project root
    based on the existence and validity of the current session.

    Returns:
        Tuple of (execution_directory, session_state).
        - execution_directory: Path to worktree if session exists and is valid,
          otherwise Path to project root.
        - session_state: SessionState if session exists, None otherwise.
    """
    project_root = get_project_root()
    manager = SessionManager(project_root)
    state = manager.load()

    # If no session, return project root
    if state is None:
        return (project_root, None)

    # If session exists but worktree doesn't exist, fall back to project root
    if not state.worktree_path.exists():
        return (project_root, None)

    # Session exists and worktree is valid
    return (state.worktree_path, state)


def get_effective_task_id(session: SessionState | None) -> str:
    """Get the effective task ID from session or default.

    Args:
        session: SessionState if available, None otherwise.

    Returns:
        Task ID from session if available, "default" otherwise.
    """
    if session is None:
        return "default"
    return session.task_id
