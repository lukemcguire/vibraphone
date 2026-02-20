"""Unit tests for quality_state module.

Tests QualityGateState model and QualityStateManager with mocked file operations.
Uses tmp_path fixture for isolated testing.
"""

import json
from pathlib import Path
from typing import Literal, cast
from unittest.mock import patch

import pytest

from vibraphone.utils.quality_state import (
    QualityGateState,
    QualityStateManager,
    get_quality_state_manager,
)


class TestQualityGateState:
    """Tests for QualityGateState model."""

    def test_quality_gate_state_defaults(self) -> None:
        """New state has None values and 0 counters."""
        state = QualityGateState(task_id="001")

        assert state.task_id == "001"
        assert state.last_review_status is None
        assert state.last_review_diff_hash is None
        assert state.last_review_issues == []
        assert state.review_attempts == 0
        assert state.test_attempts == 0
        assert state.lint_attempts == 0

    def test_quality_gate_state_model_dump_json(self) -> None:
        """custom_dump_json returns valid JSON with all fields."""
        state = QualityGateState(
            task_id="001",
            last_review_status="APPROVED",
            last_review_diff_hash="abc123",
            last_review_issues=[{"file": "test.py", "message": "issue"}],
            review_attempts=2,
            test_attempts=3,
            lint_attempts=1,
        )

        json_str = state.custom_dump_json()

        # Should be valid JSON
        data = json.loads(json_str)
        assert data["task_id"] == "001"
        assert data["last_review_status"] == "APPROVED"
        assert data["last_review_diff_hash"] == "abc123"
        assert len(data["last_review_issues"]) == 1
        assert data["review_attempts"] == 2
        assert data["test_attempts"] == 3
        assert data["lint_attempts"] == 1

    def test_quality_gate_state_with_all_statuses(self) -> None:
        """State accepts APPROVED, REJECTED, ESCALATED status values."""
        for status in cast(
            "list[Literal['APPROVED', 'REJECTED', 'ESCALATED']]",
            ["APPROVED", "REJECTED", "ESCALATED"],
        ):
            state = QualityGateState(task_id="001", last_review_status=status)
            assert state.last_review_status == status


class TestQualityStateManager:
    """Tests for QualityStateManager."""

    def test_manager_load_returns_none_for_missing_file(self, tmp_path: Path) -> None:
        """load() returns None when file doesn't exist."""
        manager = QualityStateManager(tmp_path, "001")
        result = manager.load()

        assert result is None

    def test_manager_save_and_load(self, tmp_path: Path) -> None:
        """save then load returns same values."""
        manager = QualityStateManager(tmp_path, "001")
        original_state = QualityGateState(
            task_id="001",
            last_review_status="REJECTED",
            last_review_diff_hash="def456",
            last_review_issues=[{"file": "main.py", "message": "error"}],
            review_attempts=1,
            test_attempts=2,
            lint_attempts=0,
        )

        manager.save(original_state)
        loaded_state = manager.load()

        assert loaded_state is not None
        assert loaded_state.task_id == original_state.task_id
        assert loaded_state.last_review_status == original_state.last_review_status
        assert loaded_state.last_review_diff_hash == original_state.last_review_diff_hash
        assert loaded_state.last_review_issues == original_state.last_review_issues
        assert loaded_state.review_attempts == original_state.review_attempts
        assert loaded_state.test_attempts == original_state.test_attempts
        assert loaded_state.lint_attempts == original_state.lint_attempts

    def test_manager_atomic_write(self, tmp_path: Path) -> None:
        """Verify temp file + rename pattern is used."""
        manager = QualityStateManager(tmp_path, "001")
        state = QualityGateState(task_id="001")

        # Track Path.rename calls
        with patch.object(Path, "rename") as mock_rename:
            manager.save(state)

            # Verify rename was called (temp file -> final file)
            mock_rename.assert_called_once()
            # The target should be the state file
            rename_target = mock_rename.call_args[0][0]
            assert rename_target == tmp_path / ".vibraphone" / "tasks" / "001" / "state.json"

    def test_manager_clear(self, tmp_path: Path) -> None:
        """clear() deletes file."""
        manager = QualityStateManager(tmp_path, "001")
        state = QualityGateState(task_id="001")

        manager.save(state)
        state_file = tmp_path / ".vibraphone" / "tasks" / "001" / "state.json"
        assert state_file.exists()

        manager.clear()

        assert not state_file.exists()

    def test_manager_clear_no_file_is_safe(self, tmp_path: Path) -> None:
        """clear() is safe when no file exists."""
        manager = QualityStateManager(tmp_path, "001")

        # Should not raise
        manager.clear()

    def test_manager_creates_parent_directories(self, tmp_path: Path) -> None:
        """save() creates .vibraphone/tasks/{task_id}/ directory structure."""
        manager = QualityStateManager(tmp_path, "002")
        state = QualityGateState(task_id="002")

        manager.save(state)

        expected_dir = tmp_path / ".vibraphone" / "tasks" / "002"
        assert expected_dir.exists()

    def test_manager_load_handles_json_decode_error(self, tmp_path: Path) -> None:
        """load() raises JSONDecodeError for invalid JSON."""
        manager = QualityStateManager(tmp_path, "001")
        state_file = tmp_path / ".vibraphone" / "tasks" / "001" / "state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text("not valid json {")

        with pytest.raises(json.JSONDecodeError):
            manager.load()

    def test_manager_load_handles_missing_fields(self, tmp_path: Path) -> None:
        """load() raises ValidationError for missing required fields."""
        from pydantic import ValidationError

        manager = QualityStateManager(tmp_path, "001")
        state_file = tmp_path / ".vibraphone" / "tasks" / "001" / "state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        # Missing required task_id field
        state_file.write_text("{}")

        with pytest.raises(ValidationError):
            manager.load()

    def test_manager_load_handles_wrong_type(self, tmp_path: Path) -> None:
        """load() raises ValidationError for wrong field type."""
        from pydantic import ValidationError

        manager = QualityStateManager(tmp_path, "001")
        state_file = tmp_path / ".vibraphone" / "tasks" / "001" / "state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        # task_id should be string, not int
        state_file.write_text(json.dumps({"task_id": 123}))

        with pytest.raises(ValidationError):
            manager.load()


class TestGetQualityStateManager:
    """Tests for get_quality_state_manager helper."""

    def test_get_quality_state_manager(self, mocker, tmp_path: Path) -> None:
        """Helper function returns QualityStateManager."""
        # get_project_root is imported inside get_quality_state_manager from vibraphone.config
        mocker.patch("vibraphone.config.get_project_root", return_value=tmp_path)

        manager = get_quality_state_manager("003")

        assert isinstance(manager, QualityStateManager)
        assert manager.task_id == "003"
        assert manager.project_root == tmp_path

    def test_get_quality_state_manager_state_file_path(self, mocker, tmp_path: Path) -> None:
        """Manager has correct state file path."""
        mocker.patch("vibraphone.config.get_project_root", return_value=tmp_path)

        manager = get_quality_state_manager("004")

        expected_path = tmp_path / ".vibraphone" / "tasks" / "004" / "state.json"
        assert manager.state_file == expected_path


class TestStateWithReviewData:
    """Tests for state with review data."""

    def test_state_with_review_data(self) -> None:
        """State can store review data."""
        issues = [
            {"file": "src/main.py", "line": 10, "message": "Unused import", "severity": "warning"},
            {"file": "src/utils.py", "line": 5, "message": "Missing docstring", "severity": "error"},
        ]
        state = QualityGateState(
            task_id="005",
            last_review_status="REJECTED",
            last_review_diff_hash="hash123",
            last_review_issues=issues,
        )

        assert state.last_review_status == "REJECTED"
        assert state.last_review_diff_hash == "hash123"
        assert len(state.last_review_issues) == 2
        assert state.last_review_issues[0]["file"] == "src/main.py"

    def test_state_empty_issues_list(self) -> None:
        """State with no issues has empty list."""
        state = QualityGateState(
            task_id="006",
            last_review_status="APPROVED",
            last_review_issues=[],
        )

        assert state.last_review_issues == []
