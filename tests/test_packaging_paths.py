"""Tests for production and development path resolution in MEDSAFE.

Validates that:
- In development mode (not frozen), paths default to the repository root.
- In packaged mode (frozen), paths resolve to %LOCALAPPDATA%\\MedSafe.
- MEDSAFE_DATA_DIR explicitly overrides storage paths without touching default directories.
- ensure_directories_exist creates the required directories safely.
"""

import os
from pathlib import Path
import sys
from unittest.mock import patch
import pytest

from backend import config


def test_development_paths_default_to_repo(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify paths resolve to the workspace root when not frozen and no env override is set."""
    monkeypatch.delenv("MEDSAFE_DATA_DIR", raising=False)
    with patch.object(sys, "frozen", False, create=True):
        assert not config.is_frozen()
        repo_root = Path(__file__).resolve().parent.parent

        assert config.get_app_root() == repo_root
        assert config.get_user_data_dir() == repo_root
        assert config.get_data_dir() == repo_root / "data"
        assert config.get_backups_dir() == repo_root / "backups"
        assert config.get_logs_dir() == repo_root / "logs"
        assert config.get_assets_dir() == repo_root / "assets"
        assert config.get_db_path() == repo_root / "data" / "medsafe.db"


def test_frozen_paths_resolve_to_localappdata(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Verify that when running in frozen packaged mode, user data resolves to %LOCALAPPDATA%\\MedSafe."""
    monkeypatch.delenv("MEDSAFE_DATA_DIR", raising=False)
    fake_localappdata = tmp_path / "FakeLocalAppData"
    monkeypatch.setenv("LOCALAPPDATA", str(fake_localappdata))

    with patch.object(sys, "frozen", True, create=True), patch.object(sys, "executable", str(tmp_path / "MedSafe.exe")):
        assert config.is_frozen()

        expected_user_dir = fake_localappdata / "MedSafe"
        assert config.get_user_data_dir() == expected_user_dir
        assert config.get_data_dir() == expected_user_dir / "data"
        assert config.get_backups_dir() == expected_user_dir / "backups"
        assert config.get_logs_dir() == expected_user_dir / "logs"
        assert config.get_db_path() == expected_user_dir / "data" / "medsafe.db"


def test_frozen_with_meipass(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Verify that in PyInstaller onefile mode, get_app_root resolves to sys._MEIPASS."""
    fake_meipass = tmp_path / "_MEI12345"
    fake_meipass.mkdir()

    with patch.object(sys, "frozen", True, create=True), patch.object(sys, "_MEIPASS", str(fake_meipass), create=True):
        assert config.get_app_root() == fake_meipass
        assert config.get_assets_dir() == fake_meipass / "assets"


def test_environment_variable_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Verify MEDSAFE_DATA_DIR overrides user data path in both dev and frozen mode."""
    custom_dir = tmp_path / "CustomStorage"
    monkeypatch.setenv("MEDSAFE_DATA_DIR", str(custom_dir))

    # Dev mode with override
    with patch.object(sys, "frozen", False, create=True):
        assert config.get_user_data_dir() == custom_dir
        assert config.get_data_dir() == custom_dir / "data"
        assert config.get_backups_dir() == custom_dir / "backups"
        assert config.get_db_path() == custom_dir / "data" / "medsafe.db"

    # Frozen mode with override
    with patch.object(sys, "frozen", True, create=True):
        assert config.get_user_data_dir() == custom_dir
        assert config.get_data_dir() == custom_dir / "data"
        assert config.get_backups_dir() == custom_dir / "backups"
        assert config.get_db_path() == custom_dir / "data" / "medsafe.db"


def test_ensure_directories_exist_creates_all_folders(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Verify ensure_directories_exist creates data, backups, and logs directories safely."""
    custom_dir = tmp_path / "EnsureTest"
    monkeypatch.setenv("MEDSAFE_DATA_DIR", str(custom_dir))

    data_dir = config.get_data_dir()
    backups_dir = config.get_backups_dir()
    logs_dir = config.get_logs_dir()

    assert not data_dir.exists()
    assert not backups_dir.exists()
    assert not logs_dir.exists()

    config.ensure_directories_exist()

    assert data_dir.is_dir()
    assert backups_dir.is_dir()
    assert logs_dir.is_dir()


def test_dynamic_module_attributes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Verify backward-compatible module attributes (DATA_DIR, DB_PATH, etc.) update dynamically."""
    custom_dir = tmp_path / "DynamicAttrTest"
    monkeypatch.setenv("MEDSAFE_DATA_DIR", str(custom_dir))

    assert config.DATA_DIR == custom_dir / "data"
    assert config.BACKUPS_DIR == custom_dir / "backups"
    assert config.LOGS_DIR == custom_dir / "logs"
    assert config.DB_PATH == custom_dir / "data" / "medsafe.db"
