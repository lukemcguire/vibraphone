"""Tests for vibraphone configuration loading."""

import os
from pathlib import Path

import pytest

from vibraphone.config import VibraphoneConfig, clear_config_cache, get_config


class TestGetConfig:
    """Tests for get_config function."""

    def setup_method(self):
        """Clear config cache before each test."""
        clear_config_cache()

    def test_returns_none_when_no_config_file(self, tmp_path: Path, monkeypatch):
        """Verify get_config returns None when vibraphone.yaml doesn't exist."""
        monkeypatch.chdir(tmp_path)
        assert get_config() is None

    def test_returns_cached_config(self, tmp_path: Path, monkeypatch):
        """Verify config is cached after first load."""
        monkeypatch.chdir(tmp_path)

        # First call
        result1 = get_config()
        # Second call (should return same cached value)
        result2 = get_config()

        assert result1 is result2

    def test_clear_cache_allows_reload(self, tmp_path: Path, monkeypatch):
        """Verify clear_config_cache allows config to be reloaded."""
        monkeypatch.chdir(tmp_path)

        get_config()
        clear_config_cache()

        # After clear, should fetch again (still None for no file)
        result = get_config()
        assert result is None


class TestVibraphoneConfig:
    """Tests for VibraphoneConfig dataclass."""

    def test_is_dataclass(self):
        """Verify VibraphoneConfig is a dataclass."""
        from dataclasses import is_dataclass

        assert is_dataclass(VibraphoneConfig)

    def test_has_project_root_field(self):
        """Verify VibraphoneConfig has project_root field."""
        config = VibraphoneConfig(project_root=Path("/tmp"))
        assert config.project_root == Path("/tmp")
