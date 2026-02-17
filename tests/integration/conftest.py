"""Integration test fixtures with real git operations."""

import pytest
import subprocess
from pathlib import Path


@pytest.fixture
def real_git_repo(tmp_path: Path) -> Path:
    """Create a real git repository with initial commit.

    This fixture creates actual git state - use for integration tests only.
    """
    repo = tmp_path / "integration_repo"
    repo.mkdir()

    # Initialize git
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)

    # Create initial commit on main
    (repo / "README.md").write_text("# Integration Test Repo\n")
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo, check=True, capture_output=True)

    return repo


@pytest.fixture
def git_repo_with_config(real_git_repo: Path) -> Path:
    """Git repo with vibraphone.yaml configured."""
    config_content = """worktrees_path: ~/.vibraphone/worktrees/

circuit_breakers:
  tests:
    max_attempts: 3
  lint:
    max_attempts: 3
  format:
    max_attempts: 3
  review:
    max_attempts: 5

review:
  model: openai/gpt-4o-mini

quality_gate:
  commands:
    test: pytest
    lint: ruff check
    format: ruff format
    check: ruff check
"""
    (real_git_repo / "vibraphone.yaml").write_text(config_content)
    return real_git_repo


@pytest.fixture
def git_repo_with_plan(git_repo_with_config: Path) -> Path:
    """Git repo with sample GSD plan for import testing."""
    # Create .planning directory structure
    planning_dir = git_repo_with_config / ".planning"
    planning_dir.mkdir()

    # Create a minimal GSD plan
    plan_content = """---
phase: test-phase
plan: 01
type: execute
---

<objective>
Test task for integration testing.
</objective>

<tasks>

<task type="auto">
  <name>Task 1: Test task</name>
  <files>test.txt</files>
  <action>Create a test file</action>
  <verify>test.txt exists</verify>
  <done>File created</done>
</task>

</tasks>
"""
    (planning_dir / "TEST-PLAN.md").write_text(plan_content)
    return git_repo_with_config
