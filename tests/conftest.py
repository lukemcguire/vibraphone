"""Shared pytest fixtures for vibraphone tests.

This module provides common fixtures that can be used across all test files.
Fixtures are automatically discovered by pytest.
"""

import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from unittest.mock import MagicMock

# Get full path to git executable (avoids S607 partial path warning)
GIT = shutil.which("git") or "git"


@pytest.fixture
def tmp_git_repo(tmp_path: Path) -> Path:
    """Create a real git repository for integration tests.

    Creates a minimal git repository with a single initial commit.
    Useful for testing git-dependent functionality.

    Args:
        tmp_path: Pytest's built-in temporary path fixture.

    Returns:
        Path to the created git repository.
    """
    repo = tmp_path / "test_repo"
    repo.mkdir()

    subprocess.run([GIT, "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run([GIT, "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True)
    subprocess.run([GIT, "config", "user.name", "Test"], cwd=repo, check=True, capture_output=True)

    # Create initial commit
    (repo / "README.md").write_text("# Test Repo\n")
    subprocess.run([GIT, "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run([GIT, "commit", "-m", "init"], cwd=repo, check=True, capture_output=True)

    return repo


@pytest.fixture
def mock_execution_context(tmp_path: Path, mocker: "MagicMock"):
    """Standard mock for get_execution_context returning proper tuple.

    Use this fixture in quality gate tool tests to mock the execution context.
    Returns a function that can be called with optional session parameter.

    Args:
        tmp_path: Pytest's built-in temporary path fixture.
        mocker: pytest-mock's mocker fixture.

    Returns:
        A factory function that creates a mock context.
        Call with optional session parameter:
            mock_context = mock_execution_context()
            mock_context(session=some_session)
    """
    from vibraphone.utils.session import SessionState

    def _mock_context(session: SessionState | None = None) -> "MagicMock":
        mock = mocker.patch("vibraphone.tools.quality_gate_tools.get_execution_context")
        mock.return_value = (tmp_path, session)
        return mock

    return _mock_context
