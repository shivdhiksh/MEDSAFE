"""Milestone 0 Setup verification tests.
"""

from pathlib import Path
from backend.config import (
    APP_DISCLAIMER,
    APP_NAME,
    APP_VERSION,
    BACKUPS_DIR,
    BASE_DIR,
    DATA_DIR,
    DB_PATH,
    ensure_directories_exist,
)


def test_paths_and_directories():
    """Verify paths resolve to valid locations and directories are creatable."""
    assert BASE_DIR.exists()
    ensure_directories_exist()
    assert DATA_DIR.exists()
    assert BACKUPS_DIR.exists()
    assert DB_PATH.parent == DATA_DIR


def test_app_metadata_and_safety_disclaimer():
    """Verify application metadata and non-negotiable safety notice."""
    assert APP_NAME == "MedSafe"
    assert APP_VERSION != ""
    assert "medical advice" in APP_DISCLAIMER.lower()
    assert "pharmacist or healthcare professional" in APP_DISCLAIMER.lower()


def test_frontend_importability():
    """Verify that frontend modules can be imported cleanly without errors."""
    import frontend.config as f_config
    from frontend.app import MedSafeApp
    from frontend.components.confirmation_dialog import ConfirmationDialog
    from frontend.components.medicine_form import MedicineForm
    from frontend.components.sidebar import Sidebar
    from frontend.components.status_badge import StatusBadge
    from frontend.views.about_view import AboutView
    from frontend.views.add_medicine_view import AddMedicineView
    from frontend.views.dashboard_view import DashboardView
    from frontend.views.inventory_view import InventoryView
    from frontend.views.medicine_detail_view import MedicineDetailView
    from frontend.views.settings_view import SettingsView

    assert f_config.WINDOW_TITLE == "MedSafe"
    assert MedSafeApp is not None
    assert Sidebar is not None
    assert StatusBadge is not None
    assert ConfirmationDialog is not None
    assert DashboardView is not None
    assert InventoryView is not None
    assert AddMedicineView is not None
    assert MedicineDetailView is not None
    assert SettingsView is not None
    assert AboutView is not None


def test_app_window_lifecycle():
    """Verify that MedSafeApp window initializes and switches views cleanly."""
    from frontend.app import MedSafeApp
    from frontend.views.about_view import AboutView
    from frontend.views.add_medicine_view import AddMedicineView
    from frontend.views.dashboard_view import DashboardView
    from frontend.views.inventory_view import InventoryView
    from frontend.views.settings_view import SettingsView

    app = MedSafeApp()
    try:
        assert app.title() == "MedSafe"
        assert isinstance(app.current_view, DashboardView)

        app.show_view("inventory")
        assert isinstance(app.current_view, InventoryView)

        app.show_view("add_medicine")
        assert isinstance(app.current_view, AddMedicineView)

        app.show_view("settings")
        assert isinstance(app.current_view, SettingsView)

        app.show_view("about")
        assert isinstance(app.current_view, AboutView)

        app.show_view("dashboard")
        assert isinstance(app.current_view, DashboardView)
    finally:
        app.destroy()
