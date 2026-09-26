"""Application configuration and path definitions for MEDSAFE.

Provides directory paths, database locations, runtime execution mode detection,
and core application metadata.

Path Architecture:
- Development Mode: Uses workspace data/ and backups/ directories.
- Packaged Mode (PyInstaller frozen):
    - App resources (read-only): extracted bundled files / application root.
    - User storage (writable): %LOCALAPPDATA%\\MedSafe\\ (data, backups, logs).
- Environment Override: MEDSAFE_DATA_DIR overrides user storage directory (for tests/custom setups).
"""

import os
from pathlib import Path
import sys
from typing import Any, List

# Core App Metadata
APP_NAME: str = "MedSafe"
APP_FULL_TITLE: str = "MEDSAFE — Offline Medicine Expiry Tracker"
APP_VERSION: str = "1.1.0"
APP_ID: str = "MedSafe"

# Safety and Compliance Disclaimer
APP_DISCLAIMER: str = (
    "This application helps organize medicine expiry information. "
    "It does not provide medical advice. Always verify the original packaging "
    "and consult a pharmacist or healthcare professional if you are unsure whether "
    "a medicine can be used."
)


def is_frozen() -> bool:
    """Return True if running inside a PyInstaller frozen bundle, False otherwise."""
    return getattr(sys, "frozen", False)


def get_app_root() -> Path:
    """Return the base root directory for application binaries and bundled resources.

    - In PyInstaller onefile: sys._MEIPASS (temporary extracted bundle).
    - In PyInstaller onedir: directory containing the executable.
    - In development: the repository root (two levels above this file).
    """
    if is_frozen():
        if hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS).resolve()
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def get_user_data_dir() -> Path:
    """Return the persistent directory for writable user data (database, backups, logs).

    Precedence:
    1. MEDSAFE_DATA_DIR environment variable (explicit override for testing or portable mode).
    2. Packaged Mode: %LOCALAPPDATA%\\MedSafe (Windows) or ~/.medsafe (other OS).
    3. Development Mode: The project workspace root directory.
    """
    env_override = os.environ.get("MEDSAFE_DATA_DIR")
    if env_override and env_override.strip():
        return Path(env_override).resolve()

    if is_frozen():
        if sys.platform == "win32":
            local_appdata = os.environ.get("LOCALAPPDATA")
            if local_appdata:
                return Path(local_appdata).resolve() / APP_NAME
            return Path.home().resolve() / "AppData" / "Local" / APP_NAME
        return Path.home().resolve() / f".{APP_NAME.lower()}"

    # Development mode: default to repository root
    return get_app_root()


def get_data_dir() -> Path:
    """Return directory for SQLite database storage."""
    return get_user_data_dir() / "data"


def get_backups_dir() -> Path:
    """Return directory for exported backups (CSV, JSON)."""
    return get_user_data_dir() / "backups"


def get_logs_dir() -> Path:
    """Return directory for application logs."""
    return get_user_data_dir() / "logs"


def get_assets_dir() -> Path:
    """Return directory for read-only bundled assets (icons, images)."""
    app_root = get_app_root()
    if (app_root / "assets").exists():
        return app_root / "assets"
    if (app_root / "_internal" / "assets").exists():
        return app_root / "_internal" / "assets"
    return app_root / "assets"


def get_icon_path() -> Path:
    """Return path to the active application icon (.ico file)."""
    return get_assets_dir() / "icons" / "medsafe.ico"


def get_icon_png_path() -> Path:
    """Return path to the active application icon (.png file)."""
    return get_assets_dir() / "icons" / "medsafe.png"


def get_db_path() -> Path:
    """Return path to the active SQLite database file."""
    return get_data_dir() / "medsafe.db"


def ensure_directories_exist() -> None:
    """Ensure that essential runtime directories exist locally."""
    get_data_dir().mkdir(parents=True, exist_ok=True)
    get_backups_dir().mkdir(parents=True, exist_ok=True)
    get_logs_dir().mkdir(parents=True, exist_ok=True)


# Module-level path aliases for backward-compatibility.
# Evaluated dynamically via __getattr__ so changes to is_frozen() or
# MEDSAFE_DATA_DIR take effect immediately.
def __getattr__(name: str) -> Any:
    if name == "BASE_DIR":
        return get_app_root()
    if name == "DATA_DIR":
        return get_data_dir()
    if name == "BACKUPS_DIR":
        return get_backups_dir()
    if name == "LOGS_DIR":
        return get_logs_dir()
    if name == "ASSETS_DIR":
        return get_assets_dir()
    if name == "DB_PATH":
        return get_db_path()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> List[str]:
    return [
        "APP_NAME",
        "APP_FULL_TITLE",
        "APP_VERSION",
        "APP_ID",
        "APP_DISCLAIMER",
        "BASE_DIR",
        "DATA_DIR",
        "BACKUPS_DIR",
        "LOGS_DIR",
        "ASSETS_DIR",
        "DB_PATH",
        "is_frozen",
        "get_app_root",
        "get_user_data_dir",
        "get_data_dir",
        "get_backups_dir",
        "get_logs_dir",
        "get_assets_dir",
        "get_icon_path",
        "get_icon_png_path",
        "get_db_path",
        "ensure_directories_exist",
    ]
