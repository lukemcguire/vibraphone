"""Unit tests for vibraphone task management tools.

Uses pytest-mock to mock CLI calls (br/bv) for testing without actual installations.

Note: FastMCP @mcp.tool decorator wraps functions in FunctionTool objects.
To test the underlying logic, we access the original function via the .fn attribute.
"""

from unittest.mock import AsyncMock

import pytest


class TestListTasks:
    """Tests for list_tasks MCP tool."""

    @pytest.mark.asyncio
    async def test_list_tasks_no_filter(self, mocker):
        """Verify list_tasks returns all tasks without filters."""
        mock_result = {
            "issues": [{"id": "bd-1", "title": "Task 1"}, {"id": "bd-2", "title": "Task 2"}],
            "dependency_graph": {"bd-1": ["bd-2"]},
        }
        mocker.patch("vibraphone.tools.task_tools.run_cli", new_callable=AsyncMock, return_value=mock_result)

        from vibraphone.tools.task_tools import list_tasks

        # Access underlying function via .fn attribute (FunctionTool wrapper)
        result = await list_tasks.fn()

        assert result["total"] == 2
        assert len(result["tasks"]) == 2
        assert result["tasks"][0]["id"] == "bd-1"
        assert "dependency_graph" in result

    @pytest.mark.asyncio
    async def test_list_tasks_with_status_filter(self, mocker):
        """Verify list_tasks passes status filter to CLI."""
        mock_result = {
            "issues": [{"id": "bd-1", "status": "ready"}],
            "dependency_graph": {},
        }
        mock_run_cli = mocker.patch("vibraphone.tools.task_tools.run_cli", new_callable=AsyncMock, return_value=mock_result)

        from vibraphone.tools.task_tools import list_tasks

        result = await list_tasks.fn(status="ready")

        assert result["total"] == 1
        assert result["tasks"][0]["status"] == "ready"
        # Verify status filter was passed to CLI
        call_args = mock_run_cli.call_args
        assert "--status" in call_args[0]
        assert "ready" in call_args[0]

    @pytest.mark.asyncio
    async def test_list_tasks_with_plan_filter(self, mocker):
        """Verify list_tasks passes plan filter to CLI."""
        mock_result = {
            "issues": [{"id": "bd-1", "plan": "03-01"}],
            "dependency_graph": {},
        }
        mock_run_cli = mocker.patch("vibraphone.tools.task_tools.run_cli", new_callable=AsyncMock, return_value=mock_result)

        from vibraphone.tools.task_tools import list_tasks

        result = await list_tasks.fn(plan="03-01")

        assert result["total"] == 1
        # Verify plan filter was passed to CLI
        call_args = mock_run_cli.call_args
        assert "--plan" in call_args[0]
        assert "03-01" in call_args[0]

    @pytest.mark.asyncio
    async def test_list_tasks_empty_results(self, mocker):
        """Verify list_tasks handles empty results gracefully."""
        mock_result = {"issues": [], "dependency_graph": {}}
        mocker.patch("vibraphone.tools.task_tools.run_cli", new_callable=AsyncMock, return_value=mock_result)

        from vibraphone.tools.task_tools import list_tasks

        result = await list_tasks.fn()

        assert result["total"] == 0
        assert result["tasks"] == []
        assert result["dependency_graph"] == {}


class TestNextReady:
    """Tests for next_ready MCP tool."""

    @pytest.mark.asyncio
    async def test_next_ready_returns_task(self, mocker):
        """Verify next_ready returns highest priority unblocked task."""
        mock_result = {
            "task": {"id": "bd-1", "title": "Critical task"},
            "reason": "critical path",
            "claim_command": "br claim bd-1",
        }
        mocker.patch("vibraphone.tools.task_tools.run_cli", new_callable=AsyncMock, return_value=mock_result)

        from vibraphone.tools.task_tools import next_ready

        result = await next_ready.fn()

        assert result["task"] is not None
        assert result["task"]["id"] == "bd-1"
        assert result["reason"] == "critical path"
        assert result["claim_command"] == "br claim bd-1"

    @pytest.mark.asyncio
    async def test_next_ready_no_ready_tasks(self, mocker):
        """Verify next_ready returns message when no tasks ready."""
        mock_result = {"task": None}
        mocker.patch("vibraphone.tools.task_tools.run_cli", new_callable=AsyncMock, return_value=mock_result)

        from vibraphone.tools.task_tools import next_ready

        result = await next_ready.fn()

        assert result["task"] is None
        assert "message" in result
        assert "No ready tasks" in result["message"]


class TestHealthCheck:
    """Tests for health_check MCP tool."""

    @pytest.mark.asyncio
    async def test_health_check_returns_metrics(self, mocker):
        """Verify health_check returns graph metrics structure."""
        mock_result = {
            "status": "computed",
            "data_hash": "abc123",
            "as_of": "2026-02-16T12:00:00Z",
            "pagerank": {"top": [{"id": "bd-1", "score": 0.5}]},
            "betweenness": {"top": [{"id": "bd-2", "score": 0.3}]},
            "critical_path": ["bd-1", "bd-2", "bd-3"],
            "cycles": [],
            "project_health": {"status": "healthy"},
        }
        mocker.patch("vibraphone.tools.task_tools.run_cli", new_callable=AsyncMock, return_value=mock_result)

        from vibraphone.tools.task_tools import health_check

        result = await health_check.fn()

        assert result["status"] == "computed"
        assert result["data_hash"] == "abc123"
        assert result["as_of"] == "2026-02-16T12:00:00Z"
        assert "metrics" in result
        assert result["metrics"]["pagerank_top"][0]["id"] == "bd-1"
        assert result["metrics"]["critical_path"] == ["bd-1", "bd-2", "bd-3"]
        assert result["metrics"]["cycles"] == []


class TestCompleteTask:
    """Tests for complete_task MCP tool."""

    @pytest.mark.asyncio
    async def test_complete_task_success_with_unblocked(self, mocker):
        """Verify complete_task returns task and unblocked list on success."""
        # First call: show task (not blocked)
        # Second call: close task
        mock_show = {"id": "bd-1", "status": "in_progress"}
        mock_close = {"issue": {"id": "bd-1", "status": "completed"}, "unblocked": ["bd-2", "bd-3"], "closed_at": "2026-02-16T12:00:00Z"}

        mock_run_cli = mocker.patch("vibraphone.tools.task_tools.run_cli", new_callable=AsyncMock)
        mock_run_cli.side_effect = [mock_show, mock_close]

        from vibraphone.tools.task_tools import complete_task

        result = await complete_task.fn("bd-1")

        assert result["task"]["status"] == "completed"
        assert "bd-2" in result["unblocked"]
        assert "bd-3" in result["unblocked"]
        assert result["completed_at"] == "2026-02-16T12:00:00Z"

    @pytest.mark.asyncio
    async def test_complete_task_blocked_returns_error(self, mocker):
        """Verify complete_task returns TaskError for blocked tasks."""
        mock_show = {"id": "bd-1", "status": "blocked"}
        mocker.patch("vibraphone.tools.task_tools.run_cli", new_callable=AsyncMock, return_value=mock_show)

        from vibraphone.tools.task_tools import complete_task

        result = await complete_task.fn("bd-1")

        assert "error_type" in result
        assert result["error_type"] == "CannotCompleteBlockedTask"
        assert "message" in result
        assert "suggested_action" in result

    @pytest.mark.asyncio
    async def test_complete_task_with_notes(self, mocker):
        """Verify complete_task passes notes to CLI."""
        mock_show = {"id": "bd-1", "status": "ready"}
        mock_close = {"issue": {"id": "bd-1", "status": "completed"}, "unblocked": [], "closed_at": "2026-02-16T12:00:00Z"}

        mock_run_cli = mocker.patch("vibraphone.tools.task_tools.run_cli", new_callable=AsyncMock)
        mock_run_cli.side_effect = [mock_show, mock_close]

        from vibraphone.tools.task_tools import complete_task

        result = await complete_task.fn("bd-1", notes="Implemented feature X")

        assert result["task"]["status"] == "completed"
        # Verify notes were passed
        close_call_args = mock_run_cli.call_args_list[1]
        assert "--notes" in close_call_args[0]
        assert "Implemented feature X" in close_call_args[0]


class TestAbandonTask:
    """Tests for abandon_task MCP tool."""

    @pytest.mark.asyncio
    async def test_abandon_task_success_with_reason(self, mocker):
        """Verify abandon_task resets status and records reason."""
        mock_result = {"issue": {"id": "bd-1", "status": "ready"}, "updated_at": "2026-02-16T12:00:00Z"}
        mock_run_cli = mocker.patch("vibraphone.tools.task_tools.run_cli", new_callable=AsyncMock, return_value=mock_result)

        from vibraphone.tools.task_tools import abandon_task

        result = await abandon_task.fn("bd-1", "Blocked by dependency")

        assert result["task"]["status"] == "ready"
        assert result["reason"] == "Blocked by dependency"
        assert result["abandoned_at"] == "2026-02-16T12:00:00Z"

        # Verify reason was passed in notes
        call_args = mock_run_cli.call_args
        assert "--notes" in call_args[0]
        assert "Abandoned: Blocked by dependency" in call_args[0]

    @pytest.mark.asyncio
    async def test_abandon_task_requires_reason(self, mocker):
        """Verify abandon_task requires reason parameter."""
        # This test verifies the function signature requires reason
        # The actual TypeError would be caught at call time
        from vibraphone.tools.task_tools import abandon_task

        # Function signature should require reason parameter
        # Access underlying function's signature
        import inspect

        sig = inspect.signature(abandon_task.fn)
        params = sig.parameters
        assert "reason" in params
        # reason should not have a default
        assert params["reason"].default == inspect.Parameter.empty


class TestGetTaskContext:
    """Tests for get_task_context MCP tool."""

    @pytest.mark.asyncio
    async def test_get_task_context_with_mermaid(self, mocker, tmp_path):
        """Verify get_task_context extracts mermaid diagrams."""
        mock_task = {"id": "bd-1", "title": "Task", "branch": "feat/bd-1"}
        mock_commits = []  # Empty commits for simplicity

        # Mock run_cli for task fetch
        mock_run_cli = mocker.patch("vibraphone.tools.task_tools.run_cli", new_callable=AsyncMock)
        mock_run_cli.return_value = mock_task

        # Mock get_branch_commits to return empty
        mocker.patch("vibraphone.tools.task_tools.get_branch_commits", new_callable=AsyncMock, return_value=mock_commits)

        # Create mock architecture.md
        arch_dir = tmp_path / "docs"
        arch_dir.mkdir()
        arch_file = arch_dir / "architecture.md"
        arch_file.write_text("```mermaid\ngraph TD\n  A --> B\n```\n")

        mocker.patch("vibraphone.tools.task_tools.get_project_root", return_value=tmp_path)

        from vibraphone.tools.task_tools import get_task_context

        result = await get_task_context.fn("bd-1")

        assert result["task"]["id"] == "bd-1"
        assert len(result["architecture_diagrams"]) == 1
        assert "graph TD" in result["architecture_diagrams"][0]

    @pytest.mark.asyncio
    async def test_get_task_context_without_architecture_md(self, mocker, tmp_path):
        """Verify get_task_context handles missing architecture.md."""
        mock_task = {"id": "bd-1", "title": "Task", "branch": "feat/bd-1"}

        mocker.patch("vibraphone.tools.task_tools.run_cli", new_callable=AsyncMock, return_value=mock_task)
        mocker.patch("vibraphone.tools.task_tools.get_branch_commits", new_callable=AsyncMock, return_value=[])

        # No architecture.md file
        mocker.patch("vibraphone.tools.task_tools.get_project_root", return_value=tmp_path)

        from vibraphone.tools.task_tools import get_task_context

        result = await get_task_context.fn("bd-1")

        assert result["task"]["id"] == "bd-1"
        assert result["architecture_diagrams"] == []
        assert result["recent_commits"] == []

    @pytest.mark.asyncio
    async def test_get_task_context_with_branch_commits(self, mocker, tmp_path):
        """Verify get_task_context includes recent commits when branch exists."""
        mock_task = {"id": "bd-1", "title": "Task", "branch": "feat/bd-1"}
        mock_commits = [{"hash": "abc123", "subject": "Initial commit", "date": "2026-02-16"}]

        mocker.patch("vibraphone.tools.task_tools.run_cli", new_callable=AsyncMock, return_value=mock_task)
        mocker.patch("vibraphone.tools.task_tools.get_branch_commits", new_callable=AsyncMock, return_value=mock_commits)
        mocker.patch("vibraphone.tools.task_tools.get_project_root", return_value=tmp_path)

        from vibraphone.tools.task_tools import get_task_context

        result = await get_task_context.fn("bd-1")

        assert len(result["recent_commits"]) == 1
        assert result["recent_commits"][0]["hash"] == "abc123"


class TestPhase3SuccessCriteria:
    """Verify all TASK requirements from ROADMAP.md."""

    @pytest.mark.asyncio
    async def test_task_01_list_tasks_with_status_filter(self, mocker):
        """TASK-01: Agent can list tasks with optional status filter."""
        mock_result = {"issues": [{"id": "bd-1", "status": "ready"}], "dependency_graph": {}}
        mocker.patch("vibraphone.tools.task_tools.run_cli", new_callable=AsyncMock, return_value=mock_result)

        from vibraphone.tools.task_tools import list_tasks

        result = await list_tasks.fn(status="ready")

        assert "tasks" in result
        assert "dependency_graph" in result
        assert result["total"] >= 0

    @pytest.mark.asyncio
    async def test_task_02_next_ready_returns_task(self, mocker):
        """TASK-02: Agent can get next unblocked task."""
        mock_result = {"task": {"id": "bd-1", "title": "Critical task"}, "reason": "critical path"}
        mocker.patch("vibraphone.tools.task_tools.run_cli", new_callable=AsyncMock, return_value=mock_result)

        from vibraphone.tools.task_tools import next_ready

        result = await next_ready.fn()

        assert result["task"] is not None
        assert "reason" in result

    @pytest.mark.asyncio
    async def test_task_03_complete_task_shows_unblocked(self, mocker):
        """TASK-03: Agent can mark task complete and see unblocked tasks."""
        # First call: show task (not blocked)
        # Second call: close task
        mock_show = {"id": "bd-1", "status": "in_progress"}
        mock_close = {"issue": {"id": "bd-1", "status": "completed"}, "unblocked": ["bd-2"]}

        mock_run_cli = mocker.patch("vibraphone.tools.task_tools.run_cli", new_callable=AsyncMock)
        mock_run_cli.side_effect = [mock_show, mock_close]

        from vibraphone.tools.task_tools import complete_task

        result = await complete_task.fn("bd-1")

        assert result["task"]["status"] == "completed"
        assert "bd-2" in result["unblocked"]

    @pytest.mark.asyncio
    async def test_task_04_abandon_task_resets_status(self, mocker):
        """TASK-04: Agent can abandon task and status resets to ready."""
        mock_result = {"issue": {"id": "bd-1", "status": "ready"}, "updated_at": "2026-02-16"}
        mocker.patch("vibraphone.tools.task_tools.run_cli", new_callable=AsyncMock, return_value=mock_result)

        from vibraphone.tools.task_tools import abandon_task

        result = await abandon_task.fn("bd-1", "Blocked by dependency")

        assert result["task"]["status"] == "ready"
        assert result["reason"] == "Blocked by dependency"

    @pytest.mark.asyncio
    async def test_task_05_health_check_returns_metrics(self, mocker):
        """TASK-05: Agent can run health check on beads state."""
        mock_result = {
            "status": "computed",
            "data_hash": "abc123",
            "as_of": "2026-02-16",
            "pagerank": {"top": [{"id": "bd-1", "score": 0.5}]},
            "betweenness": {},
            "critical_path": ["bd-1", "bd-2"],
            "cycles": [],
            "project_health": {},
        }
        mocker.patch("vibraphone.tools.task_tools.run_cli", new_callable=AsyncMock, return_value=mock_result)

        from vibraphone.tools.task_tools import health_check

        result = await health_check.fn()

        assert result["status"] == "computed"
        assert "metrics" in result

    @pytest.mark.asyncio
    async def test_task_06_get_task_context_returns_bundle(self, mocker, tmp_path):
        """TASK-06: Agent can load focused context bundle for a task."""
        mock_task = {"id": "bd-1", "title": "Task", "branch": "feat/bd-1"}
        mock_commits = []

        mocker.patch("vibraphone.tools.task_tools.run_cli", new_callable=AsyncMock, return_value=mock_task)
        mocker.patch("vibraphone.tools.task_tools.get_branch_commits", new_callable=AsyncMock, return_value=mock_commits)

        # Create mock architecture.md
        arch_dir = tmp_path / "docs"
        arch_dir.mkdir()
        arch_file = arch_dir / "architecture.md"
        arch_file.write_text("```mermaid\ngraph TD\n  A --> B\n```\n")

        mocker.patch("vibraphone.tools.task_tools.get_project_root", return_value=tmp_path)

        from vibraphone.tools.task_tools import get_task_context

        result = await get_task_context.fn("bd-1")

        assert result["task"]["id"] == "bd-1"
        assert len(result["architecture_diagrams"]) == 1
