"""Configuration loading for vibraphone.

Config is loaded lazily on first access, not on server startup.
This allows the server to start without vibraphone.yaml present.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class VibraphoneConfig:
    """Configuration for vibraphone MCP server.

    This is a stub for Phase 2. Full implementation will include
    worktree paths, quality gate settings, and stack configuration.
    """

    project_root: Path
    # Phase 2 will add:
    # worktrees_path: Path
    # quality_gate: QualityGateConfig
    # stack: StackConfig


_config: VibraphoneConfig | None = None


def get_config() -> VibraphoneConfig | None:
    """Load config lazily. Returns None if vibraphone.yaml not found.

    This implements the lazy loading pattern from RESEARCH.md:
    - Config loads on first access, not on server startup
    - Returns None when vibraphone.yaml is absent (PKG-04)
    - Caches result for subsequent calls

    Full implementation coming in Phase 2: Configuration & Core Utilities.
    """
    global _config
    if _config is not None:
        return _config

    # Stub: Check for vibraphone.yaml in current directory
    # Phase 2 will implement directory walking and YAML parsing
    config_path = Path.cwd() / "vibraphone.yaml"
    if not config_path.exists():
        return None

    # Placeholder: Would parse YAML and create VibraphoneConfig
    # For now, just indicate config file exists
    _config = VibraphoneConfig(project_root=Path.cwd())
    return _config


def clear_config_cache() -> None:
    """Clear the cached config. Useful for testing."""
    global _config
    _config = None


def find_config_file() -> Path | None:
    """Walk up directories to find vibraphone.yaml.

    Search stops at:
    - First vibraphone.yaml found
    - .git directory (project root boundary)
    - $HOME directory (fallback boundary)

    Follows symlinks via Path.resolve().

    Returns:
        Path to vibraphone.yaml or None if not found.
    """
    current = Path.cwd().resolve()
    home = Path.home().resolve()

    while True:
        # Check for config file first
        config_path = current / "vibraphone.yaml"
        if config_path.is_file():
            return config_path

        # Check for .git directory (project root)
        if (current / ".git").exists():
            return None

        # Check if we've reached home
        if current == home:
            return None

        # Move up
        parent = current.parent
        if parent == current:
            # Filesystem root
            return None
        current = parent
