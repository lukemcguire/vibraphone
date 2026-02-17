"""Shared error models for vibraphone tools.

Provides structured error responses with actionable guidance for users.
"""

from pydantic import BaseModel


class TaskError(BaseModel):
    """Structured error response for task management tools.

    Provides consistent error format with actionable guidance for users.
    Used by task_tools and worktree_tools.
    """

    error_type: str  # e.g., "CannotCompleteBlockedTask", "NoActiveSession"
    message: str  # Human-readable error message
    suggested_action: str  # What to do next
