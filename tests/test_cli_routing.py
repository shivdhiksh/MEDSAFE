"""Tests for CLI argument routing in MEDSAFE.

Verifies that:
- --help displays help text and exits with code 0 without GUI initialization.
- --version displays application version and exits with code 0.
- --check-notifications executes headless notification checking without creating Tkinter widgets.
- --migrate-db migrates the specified database.
- Standard invocation without CLI flags invokes the CustomTkinter GUI.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from backend.config import APP_NAME, APP_VERSION
from backend.database import init_db
from frontend.main import main, parse_arguments


def test_cli_help_flag(capsys: pytest.CaptureFixture) -> None:
    """Verify --help flag prints friendly CLI instructions and exits cleanly."""
    exit_code = main(["--help"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Usage:" in captured.out
    assert "--check-notifications" in captured.out
    assert "--migrate-db" in captured.out
    assert "--version" in captured.out


def test_cli_version_flag(capsys: pytest.CaptureFixture) -> None:
    """Verify --version flag prints application name and version."""
    exit_code = main(["--version"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert APP_NAME in captured.out
    assert APP_VERSION in captured.out


def test_cli_check_notifications_executes_service_without_gui(
    capsys: pytest.CaptureFixture,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify --check-notifications runs NotificationService without importing or launching GUI."""
    test_db = tmp_path / "cli_notif_test.db"
    init_db(test_db)
    monkeypatch.setenv("MEDSAFE_DATA_DIR", str(tmp_path))

    with patch("frontend.main.NotificationService") as mock_service_cls, patch("frontend.main.run_gui") as mock_gui:
        mock_instance = MagicMock()
        mock_res = MagicMock()
        mock_res.checked_count = 5
        mock_res.notifications_sent = 1
        mock_res.duplicates_suppressed = 2
        mock_res.errors_count = 0
        mock_instance.check_and_notify_expiring_batches.return_value = mock_res
        mock_service_cls.return_value = mock_instance

        exit_code = main(["--check-notifications"])

        assert exit_code == 0
        mock_instance.check_and_notify_expiring_batches.assert_called_once()
        mock_gui.assert_not_called()

        captured = capsys.readouterr()
        assert "MEDSAFE Expiry Check: 5 checked, 1 sent, 2 duplicates suppressed, 0 errors." in captured.out


def test_cli_migrate_db_flag(tmp_path: Path, capsys: pytest.CaptureFixture, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify --migrate-db routes to migrate_database with the provided file path."""
    source_db = tmp_path / "legacy.db"
    init_db(source_db)

    prod_dir = tmp_path / "prod"
    monkeypatch.setenv("MEDSAFE_DATA_DIR", str(prod_dir))

    exit_code = main(["--migrate-db", str(source_db)])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "[SUCCESS]" in captured.out
    assert (prod_dir / "data" / "medsafe.db").exists()


def test_cli_default_routes_to_gui() -> None:
    """Verify invoking main without flags routes to run_gui."""
    with patch("frontend.main.run_gui", return_value=0) as mock_gui:
        exit_code = main([])
        assert exit_code == 0
        mock_gui.assert_called_once()
