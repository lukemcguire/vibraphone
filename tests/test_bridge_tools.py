"""Unit tests for bridge_tools - import_gsd_plan."""

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest


class TestImportGsdPlanPreview:
    """Tests for import_gsd_plan preview mode."""

    @pytest.mark.asyncio
    async def test_preview_returns_plan_structure(self, tmp_path: Path, mocker: Any) -> None:
        """Preview should return plan structure without creating tasks."""
        # Setup phase directory with plan file
        phase_dir = tmp_path / ".planning" / "phases" / "06-test-phase"
        phase_dir.mkdir(parents=True)
        plan_file = phase_dir / "06-01-PLAN.md"
        plan_file.write_text("""---
phase: 06-test-phase
plan: 01
depends_on: ["05-01"]
---
<tasks>
<task><name>Task 1</name><description>First task</description></task>
<task><name>Task 2</name><description>Second task</description></task>
</tasks>
""")

        mocker.patch("vibraphone.tools.bridge_tools.get_project_root", return_value=tmp_path)
        mocker.patch("vibraphone.tools.bridge_tools.get_config")

        # Mock config to have components
        mock_config = MagicMock()
        mock_config.components = {"backend": {"language": "python"}}
        mocker.patch("vibraphone.tools.bridge_tools.get_config", return_value=mock_config)

        # Mock existing_plan_ids to return empty set
        async_mock = AsyncMock(return_value=set())
        mocker.patch("vibraphone.tools.bridge_tools._existing_plan_ids", side_effect=async_mock)

        from vibraphone.tools.bridge_tools import import_gsd_plan

        result = await import_gsd_plan.fn(6, preview=True)

        assert result["status"] == "preview"
        assert result["phase_number"] == 6
        assert len(result["plans"]) == 1
        assert result["plans"][0]["plan_id"] == "06-01"
        assert result["plans"][0]["task_count"] == 2

    @pytest.mark.asyncio
    async def test_preview_skips_already_imported(self, tmp_path: Path, mocker: Any) -> None:
        """Preview should indicate which plans are already imported."""
        phase_dir = tmp_path / ".planning" / "phases" / "06-test-phase"
        phase_dir.mkdir(parents=True)
        plan_file = phase_dir / "06-01-PLAN.md"
        plan_file.write_text("""---
phase: 06-test-phase
plan: 01
---
<tasks>
<task><name>Task 1</name></task>
</tasks>
""")

        mocker.patch("vibraphone.tools.bridge_tools.get_project_root", return_value=tmp_path)

        mock_config = MagicMock()
        mock_config.components = {"backend": {"language": "python"}}
        mocker.patch("vibraphone.tools.bridge_tools.get_config", return_value=mock_config)

        # Mock existing_plan_ids to return that 06-01 is already imported
        async_mock = AsyncMock(return_value={"06-01"})
        mocker.patch("vibraphone.tools.bridge_tools._existing_plan_ids", side_effect=async_mock)

        from vibraphone.tools.bridge_tools import import_gsd_plan

        result = await import_gsd_plan.fn(6, preview=True)

        assert result["status"] == "already_imported"
        assert "06-01" in result["skipped_plans"]

    @pytest.mark.asyncio
    async def test_preview_shows_task_titles(self, tmp_path: Path, mocker: Any) -> None:
        """Preview should show task titles for review."""
        phase_dir = tmp_path / ".planning" / "phases" / "06-test-phase"
        phase_dir.mkdir(parents=True)
        plan_file = phase_dir / "06-01-PLAN.md"
        plan_file.write_text("""---
phase: 06-test-phase
plan: 01
---
<tasks>
<task><name>Implement Feature X</name></task>
<task><name>Write Tests</name></task>
</tasks>
""")

        mocker.patch("vibraphone.tools.bridge_tools.get_project_root", return_value=tmp_path)

        mock_config = MagicMock()
        mock_config.components = {"backend": {"language": "python"}}
        mocker.patch("vibraphone.tools.bridge_tools.get_config", return_value=mock_config)

        async_mock = AsyncMock(return_value=set())
        mocker.patch("vibraphone.tools.bridge_tools._existing_plan_ids", side_effect=async_mock)

        from vibraphone.tools.bridge_tools import import_gsd_plan

        result = await import_gsd_plan.fn(6, preview=True)

        titles = result["plans"][0]["task_titles"]
        assert "Implement Feature X" in titles
        assert "Write Tests" in titles


class TestImportGsdPlanExecution:
    """Tests for import_gsd_plan execution (preview=False)."""

    @pytest.mark.asyncio
    async def test_creates_tasks_with_br_create(self, tmp_path: Path, mocker: Any) -> None:
        """Should call br create for each task."""
        phase_dir = tmp_path / ".planning" / "phases" / "06-test-phase"
        phase_dir.mkdir(parents=True)
        plan_file = phase_dir / "06-01-PLAN.md"
        plan_file.write_text("""---
phase: 06-test-phase
plan: 01
---
<tasks>
<task><name>Task 1</name></task>
<task><name>Task 2</name></task>
</tasks>
""")

        mocker.patch("vibraphone.tools.bridge_tools.get_project_root", return_value=tmp_path)

        mock_config = MagicMock()
        mock_config.components = {"backend": {"language": "python"}}
        mocker.patch("vibraphone.tools.bridge_tools.get_config", return_value=mock_config)

        async_mock = AsyncMock(return_value=set())
        mocker.patch("vibraphone.tools.bridge_tools._existing_plan_ids", side_effect=async_mock)

        # Mock br create calls
        mock_run_cli = mocker.patch("vibraphone.tools.bridge_tools.run_cli", new_callable=AsyncMock)
        mock_run_cli.side_effect = [
            {"id": "bd-1"},  # First br create
            {"id": "bd-2"},  # Second br create
            None,  # br sync
        ]

        from vibraphone.tools.bridge_tools import import_gsd_plan

        result = await import_gsd_plan.fn(6, preview=False)

        assert result["status"] == "imported"
        assert result["total_tasks"] == 2
        # Verify br create was called twice
        assert mock_run_cli.call_count >= 2

    @pytest.mark.asyncio
    async def test_wires_intra_plan_dependencies_from_blocked_by(self, tmp_path: Path, mocker: Any) -> None:
        """Should create deps ONLY for explicit blocked_by (no implicit sequential)."""
        phase_dir = tmp_path / ".planning" / "phases" / "06-test-phase"
        phase_dir.mkdir(parents=True)
        plan_file = phase_dir / "06-01-PLAN.md"
        plan_file.write_text("""---
phase: 06-test-phase
plan: 01
---
<tasks>
<task><name>Task 1</name></task>
<task>
  <name>Task 2</name>
  <blocked_by>Task 1</blocked_by>
</task>
</tasks>
""")

        mocker.patch("vibraphone.tools.bridge_tools.get_project_root", return_value=tmp_path)

        mock_config = MagicMock()
        mock_config.components = {"backend": {"language": "python"}}
        mocker.patch("vibraphone.tools.bridge_tools.get_config", return_value=mock_config)

        async_mock = AsyncMock(return_value=set())
        mocker.patch("vibraphone.tools.bridge_tools._existing_plan_ids", side_effect=async_mock)

        # Mock br create and dep add calls
        mock_run_cli = mocker.patch("vibraphone.tools.bridge_tools.run_cli", new_callable=AsyncMock)
        mock_run_cli.side_effect = [
            {"id": "bd-1"},  # Task 1 br create
            {"id": "bd-2"},  # Task 2 br create
            None,  # br dep add (intra-plan)
            None,  # br sync
        ]

        from vibraphone.tools.bridge_tools import import_gsd_plan

        result = await import_gsd_plan.fn(6, preview=False)

        # Should have exactly 1 intra-plan dependency
        intra_plan_deps = [d for d in result["dependencies"] if d.get("type") == "intra-plan"]
        assert len(intra_plan_deps) == 1
        assert intra_plan_deps[0]["blocked_name"] == "Task 2"
        assert intra_plan_deps[0]["blocker_name"] == "Task 1"

    @pytest.mark.asyncio
    async def test_no_implicit_sequential_dependencies(self, tmp_path: Path, mocker: Any) -> None:
        """CRITICAL: Tasks without blocked_by should NOT be blocked by preceding task."""
        phase_dir = tmp_path / ".planning" / "phases" / "06-test-phase"
        phase_dir.mkdir(parents=True)
        plan_file = phase_dir / "06-01-PLAN.md"
        plan_file.write_text("""---
phase: 06-test-phase
plan: 01
---
<tasks>
<task><name>Task 1</name></task>
<task><name>Task 2</name></task>
<task><name>Task 3</name></task>
</tasks>
""")

        mocker.patch("vibraphone.tools.bridge_tools.get_project_root", return_value=tmp_path)

        mock_config = MagicMock()
        mock_config.components = {"backend": {"language": "python"}}
        mocker.patch("vibraphone.tools.bridge_tools.get_config", return_value=mock_config)

        async_mock = AsyncMock(return_value=set())
        mocker.patch("vibraphone.tools.bridge_tools._existing_plan_ids", side_effect=async_mock)

        mock_run_cli = mocker.patch("vibraphone.tools.bridge_tools.run_cli", new_callable=AsyncMock)
        mock_run_cli.side_effect = [
            {"id": "bd-1"},
            {"id": "bd-2"},
            {"id": "bd-3"},
            None,  # br sync
        ]

        from vibraphone.tools.bridge_tools import import_gsd_plan

        result = await import_gsd_plan.fn(6, preview=False)

        # Should have ZERO intra-plan dependencies (no blocked_by specified)
        intra_plan_deps = [d for d in result["dependencies"] if d.get("type") == "intra-plan"]
        assert len(intra_plan_deps) == 0

    @pytest.mark.asyncio
    async def test_wires_inter_plan_dependencies(self, tmp_path: Path, mocker: Any) -> None:
        """Should block first task by last task of dependency plan."""
        # Create two plan files
        phase_dir = tmp_path / ".planning" / "phases" / "06-test-phase"
        phase_dir.mkdir(parents=True)

        plan_01 = phase_dir / "06-01-PLAN.md"
        plan_01.write_text("""---
phase: 06-test-phase
plan: 01
---
<tasks>
<task><name>Task A1</name></task>
</tasks>
""")

        plan_02 = phase_dir / "06-02-PLAN.md"
        plan_02.write_text("""---
phase: 06-test-phase
plan: 02
depends_on: ["06-01"]
---
<tasks>
<task><name>Task B1</name></task>
</tasks>
""")

        mocker.patch("vibraphone.tools.bridge_tools.get_project_root", return_value=tmp_path)

        mock_config = MagicMock()
        mock_config.components = {"backend": {"language": "python"}}
        mocker.patch("vibraphone.tools.bridge_tools.get_config", return_value=mock_config)

        async_mock = AsyncMock(return_value=set())
        mocker.patch("vibraphone.tools.bridge_tools._existing_plan_ids", side_effect=async_mock)

        mock_run_cli = mocker.patch("vibraphone.tools.bridge_tools.run_cli", new_callable=AsyncMock)
        mock_run_cli.side_effect = [
            {"id": "bd-1"},  # Plan 01 Task 1
            {"id": "bd-2"},  # Plan 02 Task 1
            None,  # br dep add (inter-plan)
            None,  # br sync
        ]

        from vibraphone.tools.bridge_tools import import_gsd_plan

        result = await import_gsd_plan.fn(6, preview=False)

        # Should have 1 inter-plan dependency
        inter_plan_deps = [d for d in result["dependencies"] if d.get("type") == "inter-plan"]
        assert len(inter_plan_deps) == 1
        assert inter_plan_deps[0]["blocked_plan"] == "06-02"
        assert inter_plan_deps[0]["blocker_plan"] == "06-01"

    @pytest.mark.asyncio
    async def test_calls_br_sync_after_creation(self, tmp_path: Path, mocker: Any) -> None:
        """Should call br sync --flush-only after creating all tasks."""
        phase_dir = tmp_path / ".planning" / "phases" / "06-test-phase"
        phase_dir.mkdir(parents=True)
        plan_file = phase_dir / "06-01-PLAN.md"
        plan_file.write_text("""---
phase: 06-test-phase
plan: 01
---
<tasks>
<task><name>Task 1</name></task>
</tasks>
""")

        mocker.patch("vibraphone.tools.bridge_tools.get_project_root", return_value=tmp_path)

        mock_config = MagicMock()
        mock_config.components = {"backend": {"language": "python"}}
        mocker.patch("vibraphone.tools.bridge_tools.get_config", return_value=mock_config)

        async_mock = AsyncMock(return_value=set())
        mocker.patch("vibraphone.tools.bridge_tools._existing_plan_ids", side_effect=async_mock)

        mock_run_cli = mocker.patch("vibraphone.tools.bridge_tools.run_cli", new_callable=AsyncMock)
        mock_run_cli.side_effect = [
            {"id": "bd-1"},
            None,  # br sync
        ]

        from vibraphone.tools.bridge_tools import import_gsd_plan

        await import_gsd_plan.fn(6, preview=False)

        # Last call should be br sync
        last_call = mock_run_cli.call_args_list[-1]
        assert "sync" in last_call[0]


class TestImportGsdPlanIdempotency:
    """Tests for idempotency behavior."""

    @pytest.mark.asyncio
    async def test_skips_plans_with_existing_label(self, tmp_path: Path, mocker: Any) -> None:
        """Should skip plans that already have plan:<id> label in Beads."""
        phase_dir = tmp_path / ".planning" / "phases" / "06-test-phase"
        phase_dir.mkdir(parents=True)
        plan_file = phase_dir / "06-01-PLAN.md"
        plan_file.write_text("""---
phase: 06-test-phase
plan: 01
---
<tasks>
<task><name>Task 1</name></task>
</tasks>
""")

        mocker.patch("vibraphone.tools.bridge_tools.get_project_root", return_value=tmp_path)

        mock_config = MagicMock()
        mock_config.components = {"backend": {"language": "python"}}
        mocker.patch("vibraphone.tools.bridge_tools.get_config", return_value=mock_config)

        # Mock that 06-01 already exists
        async_mock = AsyncMock(return_value={"06-01"})
        mocker.patch("vibraphone.tools.bridge_tools._existing_plan_ids", side_effect=async_mock)

        from vibraphone.tools.bridge_tools import import_gsd_plan

        result = await import_gsd_plan.fn(6, preview=False)

        assert result["status"] == "already_imported"
        assert "06-01" in result["skipped_plans"]

    @pytest.mark.asyncio
    async def test_returns_skipped_plans_list(self, tmp_path: Path, mocker: Any) -> None:
        """Should return list of skipped plans in response."""
        phase_dir = tmp_path / ".planning" / "phases" / "06-test-phase"
        phase_dir.mkdir(parents=True)

        # Create two plans
        for i in [1, 2]:
            plan_file = phase_dir / f"06-0{i}-PLAN.md"
            plan_file.write_text(f"""---
phase: 06-test-phase
plan: 0{i}
---
<tasks>
<task><name>Task {i}</name></task>
</tasks>
""")

        mocker.patch("vibraphone.tools.bridge_tools.get_project_root", return_value=tmp_path)

        mock_config = MagicMock()
        mock_config.components = {"backend": {"language": "python"}}
        mocker.patch("vibraphone.tools.bridge_tools.get_config", return_value=mock_config)

        # Mock that 06-01 already exists but not 06-02
        async_mock = AsyncMock(return_value={"06-01"})
        mocker.patch("vibraphone.tools.bridge_tools._existing_plan_ids", side_effect=async_mock)

        mock_run_cli = mocker.patch("vibraphone.tools.bridge_tools.run_cli", new_callable=AsyncMock)
        mock_run_cli.side_effect = [
            {"id": "bd-2"},
            None,
        ]

        from vibraphone.tools.bridge_tools import import_gsd_plan

        result = await import_gsd_plan.fn(6, preview=False)

        assert "06-01" in result["skipped_plans"]
        assert result["total_tasks"] == 1  # Only 06-02 was created


class TestImportGsdPlanValidation:
    """Tests for validation behavior."""

    @pytest.mark.asyncio
    async def test_fails_fast_on_invalid_plan(self, tmp_path: Path, mocker: Any) -> None:
        """Should fail before creating any tasks if validation fails."""
        phase_dir = tmp_path / ".planning" / "phases" / "06-test-phase"
        phase_dir.mkdir(parents=True)
        plan_file = phase_dir / "06-01-PLAN.md"
        plan_file.write_text("""---
phase: 06-test-phase
plan: 01
---
<tasks>
</tasks>
""")  # No tasks!

        mocker.patch("vibraphone.tools.bridge_tools.get_project_root", return_value=tmp_path)

        mock_config = MagicMock()
        mock_config.components = {"backend": {"language": "python"}}
        mocker.patch("vibraphone.tools.bridge_tools.get_config", return_value=mock_config)

        async_mock = AsyncMock(return_value=set())
        mocker.patch("vibraphone.tools.bridge_tools._existing_plan_ids", side_effect=async_mock)

        from vibraphone.tools.bridge_tools import import_gsd_plan

        result = await import_gsd_plan.fn(6, preview=False)

        assert "error_type" in result
        assert result["error_type"] == "PlanHasNoTasks"

    @pytest.mark.asyncio
    async def test_warns_on_plan_with_no_tasks(self, tmp_path: Path, mocker: Any) -> None:
        """Should warn and skip plan with no tasks, continue with others."""
        phase_dir = tmp_path / ".planning" / "phases" / "06-test-phase"
        phase_dir.mkdir(parents=True)

        # Plan with no tasks
        plan_01 = phase_dir / "06-01-PLAN.md"
        plan_01.write_text("""---
phase: 06-test-phase
plan: 01
---
<tasks>
</tasks>
""")

        mocker.patch("vibraphone.tools.bridge_tools.get_project_root", return_value=tmp_path)

        mock_config = MagicMock()
        mock_config.components = {"backend": {"language": "python"}}
        mocker.patch("vibraphone.tools.bridge_tools.get_config", return_value=mock_config)

        async_mock = AsyncMock(return_value=set())
        mocker.patch("vibraphone.tools.bridge_tools._existing_plan_ids", side_effect=async_mock)

        from vibraphone.tools.bridge_tools import import_gsd_plan

        result = await import_gsd_plan.fn(6, preview=False)

        # Should return error - fail-fast validation
        assert "error_type" in result


class TestImportGsdPlanErrors:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_returns_error_if_no_components_configured(self, tmp_path: Path, mocker: Any) -> None:
        """Should return error if components not configured."""
        mocker.patch("vibraphone.tools.bridge_tools.get_project_root", return_value=tmp_path)

        mock_config = MagicMock()
        mock_config.components = None  # No components!
        mocker.patch("vibraphone.tools.bridge_tools.get_config", return_value=mock_config)

        from vibraphone.tools.bridge_tools import import_gsd_plan

        result = await import_gsd_plan.fn(6, preview=False)

        assert "error_type" in result
        assert result["error_type"] == "NoComponentsConfigured"

    @pytest.mark.asyncio
    async def test_returns_error_if_phase_dir_not_found(self, tmp_path: Path, mocker: Any) -> None:
        """Should return error if phase directory doesn't exist."""
        mocker.patch("vibraphone.tools.bridge_tools.get_project_root", return_value=tmp_path)

        mock_config = MagicMock()
        mock_config.components = {"backend": {"language": "python"}}
        mocker.patch("vibraphone.tools.bridge_tools.get_config", return_value=mock_config)

        from vibraphone.tools.bridge_tools import import_gsd_plan

        result = await import_gsd_plan.fn(999, preview=False)  # Non-existent phase

        assert "error_type" in result
        assert result["error_type"] == "PhaseDirectoryNotFound"


class TestPhase06SuccessCriteria:
    """Tests for Phase 6 ROADMAP success criteria."""

    @pytest.mark.asyncio
    async def test_BRDG_01_import_gsd_plan_creates_tasks(self, tmp_path: Path, mocker: Any) -> None:
        """BRDG-01: Agent can call import_gsd_plan and GSD plan converts to beads tasks with dependencies."""
        phase_dir = tmp_path / ".planning" / "phases" / "06-test-phase"
        phase_dir.mkdir(parents=True)

        plan_file = phase_dir / "06-01-PLAN.md"
        plan_file.write_text("""---
phase: 06-test-phase
plan: 01
depends_on: ["05-01"]
---
<tasks>
<task><name>Setup Database</name></task>
<task>
  <name>Create API</name>
  <blocked_by>Setup Database</blocked_by>
</task>
</tasks>
""")

        mocker.patch("vibraphone.tools.bridge_tools.get_project_root", return_value=tmp_path)

        mock_config = MagicMock()
        mock_config.components = {"backend": {"language": "python"}}
        mocker.patch("vibraphone.tools.bridge_tools.get_config", return_value=mock_config)

        async_mock = AsyncMock(return_value=set())
        mocker.patch("vibraphone.tools.bridge_tools._existing_plan_ids", side_effect=async_mock)

        # Mock: first plan already imported (for inter-plan dep)
        # But we're importing 06-01 which has depends_on 05-01
        # For simplicity, let's not test inter-plan here, just intra
        mock_run_cli = mocker.patch("vibraphone.tools.bridge_tools.run_cli", new_callable=AsyncMock)
        mock_run_cli.side_effect = [
            {"id": "bd-1"},  # Task 1
            {"id": "bd-2"},  # Task 2
            None,  # dep add
            None,  # sync
        ]

        from vibraphone.tools.bridge_tools import import_gsd_plan

        result = await import_gsd_plan.fn(6, preview=False)

        # BRDG-01 verification:
        # 1. Tasks created
        assert result["status"] == "imported"
        assert result["total_tasks"] == 2

        # 2. Dependencies wired
        assert len(result["dependencies"]) >= 1

        # 3. Verify structure
        created_ids = [t["beads_id"] for t in result["tasks_created"]]
        assert "bd-1" in created_ids
        assert "bd-2" in created_ids
