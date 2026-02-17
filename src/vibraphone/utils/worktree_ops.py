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
