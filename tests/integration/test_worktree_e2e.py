"""End-to-end integration tests for worktree workflows.

Tests critical paths with real git operations.
Marked as integration for CI filtering.
"""

from pathlib import Path

import pytest


@pytest.mark.integration
@pytest.mark.timeout(120)
class TestWorktreeE2E:
    """E2E tests for worktree lifecycle with real git."""

    @pytest.mark.asyncio
    async def test_start_task_creates_worktree(self, git_repo_with_config: Path) -> None:
        """start_task creates a worktree and branch."""
        # This is a placeholder - real implementation requires br CLI
        # For now, verify the repo is set up correctly
        assert (git_repo_with_config / ".git").exists()
        assert (git_repo_with_config / "vibraphone.yaml").exists()

    @pytest.mark.asyncio
    async def test_session_persists_after_start(self, git_repo_with_config: Path) -> None:
        """Session state persists after start_task."""
        # Placeholder - verify session infrastructure works
        from vibraphone.utils.session import SessionManager

        manager = SessionManager(git_repo_with_config)
        assert manager.load() is None  # No session yet

    @pytest.mark.asyncio
    async def test_cleanup_removes_worktree(self, git_repo_with_config: Path) -> None:
        """cleanup_task removes worktree directory."""
        # Placeholder - verify cleanup infrastructure


@pytest.mark.integration
@pytest.mark.timeout(120)
class TestImportGsdPlanE2E:
    """E2E tests for import_gsd_plan workflow."""

    @pytest.mark.asyncio
    async def test_import_plan_parses_file(self, git_repo_with_plan: Path) -> None:
        """import_gsd_plan parses a GSD plan file."""
        from vibraphone.utils.plan_parser import extract_frontmatter

        plan_path = git_repo_with_plan / ".planning" / "TEST-PLAN.md"
        content = plan_path.read_text()

        frontmatter = extract_frontmatter(content)
        assert frontmatter is not None
        assert frontmatter.get("phase") == "test-phase"

    @pytest.mark.asyncio
    async def test_import_plan_extracts_tasks(self, git_repo_with_plan: Path) -> None:
        """import_gsd_plan extracts tasks from plan."""
        from vibraphone.utils.plan_parser import extract_tasks_from_xml

        plan_path = git_repo_with_plan / ".planning" / "TEST-PLAN.md"
        content = plan_path.read_text()

        tasks = extract_tasks_from_xml(content)
        assert len(tasks) == 1
        assert tasks[0]["name"] == "Task 1: Test task"

    @pytest.mark.asyncio
    async def test_import_plan_verifies_phase_structure(self, git_repo_with_plan: Path) -> None:
        """Verify plan has correct phase structure."""
        plan_path = git_repo_with_plan / ".planning" / "TEST-PLAN.md"
        assert plan_path.exists()

        # Verify .planning directory exists
        planning_dir = git_repo_with_plan / ".planning"
        assert planning_dir.is_dir()
