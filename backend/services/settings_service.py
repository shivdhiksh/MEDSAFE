"""Settings service for MEDSAFE.

Coordinates application configuration, user preferences, notification thresholds,
theme settings, and directory location interactions.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from backend.config import BACKUPS_DIR, DATA_DIR, DB_PATH
from backend.models import Settings
from backend.repositories.settings_repository import (
    DEFAULT_ALERT_DAYS,
    DEFAULT_ALERT_DAYS_STR,
    SettingsRepository,
    parse_alert_days,
)
from backend.utils.file_utils import open_folder_in_explorer
from backend.utils.logger import get_logger

logger = get_logger(__name__)

VALID_THEMES: Tuple[str, ...] = ("system", "light", "dark")


class SettingsService:
    """Provides business logic for configuring MEDSAFE settings and accessing local folders."""

    def __init__(
        self,
        db_path: Optional[Union[str, Path]] = None,
        settings_repo: Optional[SettingsRepository] = None,
    ) -> None:
        self.db_path = db_path
        self.settings_repo = settings_repo or SettingsRepository(db_path=db_path)

    def get_settings(self) -> Settings:
        """Retrieve the current persistent application settings."""
        return self.settings_repo.get_settings()

    def validate_and_normalize_thresholds(
        self, thresholds_str: Optional[str]
    ) -> Tuple[bool, str, List[int]]:
        """Validate and normalize comma-separated alert thresholds.

        Validation rules:
        - Must contain non-negative integers.
        - Comma-separated.
        - Trims whitespace.
        - Deduplicates values.
        - Sorts in descending order (e.g. 30, 7, 1).
        - Rejects invalid text, negative numbers, or empty strings.

        Returns:
            Tuple of (is_valid: bool, normalized_string_or_error_message: str, list_of_ints).
        """
        if not thresholds_str or not str(thresholds_str).strip():
            return False, "Please enter notification thresholds such as 30,7,1.", []

        parts = str(thresholds_str).split(",")
        numbers: List[int] = []

        for p in parts:
            cleaned = p.strip()
            if not cleaned:
                continue
            try:
                val = int(cleaned)
                if val < 0:
                    return False, "Thresholds cannot be negative. Please enter values such as 30,7,1.", []
                if val not in numbers:
                    numbers.append(val)
            except ValueError:
                return False, "Please enter notification thresholds such as 30,7,1.", []

        if not numbers:
            return False, "Please enter notification thresholds such as 30,7,1.", []

        # Sort descending for consistent alert evaluation
        numbers.sort(reverse=True)
        normalized = ",".join(str(n) for n in numbers)
        return True, normalized, numbers

    def update_notifications_enabled(self, enabled: bool) -> bool:
        """Toggle notification alerts on or off in the database."""
        logger.info("Setting notifications_enabled to %s", enabled)
        return self.settings_repo.update_notifications_enabled(enabled)

    def update_alert_thresholds(self, thresholds_str: str) -> Tuple[bool, str]:
        """Validate and update the configured alert thresholds.

        Returns:
            Tuple of (success: bool, status_message: str).
        """
        is_valid, normalized_or_err, _ = self.validate_and_normalize_thresholds(thresholds_str)
        if not is_valid:
            logger.warning("Rejected invalid threshold input: '%s'", thresholds_str)
            return False, normalized_or_err

        success = self.settings_repo.update_alert_days(normalized_or_err)
        if success:
            logger.info("Updated alert thresholds to: %s", normalized_or_err)
            return True, "Alert thresholds updated successfully."
        return False, "Unable to save settings. Please try again."

    def update_theme(self, theme: str) -> Tuple[bool, str]:
        """Validate and update the application theme preference.

        Returns:
            Tuple of (success: bool, status_message: str).
        """
        clean_theme = theme.strip().lower()
        if clean_theme not in VALID_THEMES:
            return False, f"Invalid theme '{theme}'. Must be one of {VALID_THEMES}."

        success = self.settings_repo.update_theme(clean_theme)
        if success:
            logger.info("Updated theme preference to: %s", clean_theme)
            return True, "Theme updated successfully."
        return False, "Unable to save settings. Please try again."

    def save_settings(
        self,
        notifications_enabled: bool,
        thresholds_str: str,
        theme: str,
    ) -> Tuple[bool, str]:
        """Validate and save all settings in one coordinated action.

        Returns:
            Tuple of (success: bool, user_message: str).
        """
        try:
            # 1. Validate thresholds
            is_valid, normalized_thresholds, _ = self.validate_and_normalize_thresholds(thresholds_str)
            if not is_valid:
                return False, normalized_thresholds

            # 2. Validate theme
            clean_theme = theme.strip().lower()
            if clean_theme not in VALID_THEMES:
                return False, f"Invalid theme '{theme}'."

            # 3. Persist values
            self.settings_repo.update_notifications_enabled(notifications_enabled)
            self.settings_repo.update_alert_days(normalized_thresholds)
            self.settings_repo.update_theme(clean_theme)

            logger.info(
                "All settings saved successfully (enabled=%s, thresholds=%s, theme=%s)",
                notifications_enabled,
                normalized_thresholds,
                clean_theme,
            )
            return True, "Settings saved successfully."
        except Exception as exc:
            logger.error("Failed to save settings: %s", exc)
            return False, "Unable to save settings. Please try again."

    def get_data_info(self) -> Dict[str, str]:
        """Return clean, user-friendly paths for display in Settings."""
        from backend.config import get_backups_dir, get_data_dir, get_db_path, is_frozen

        db_path = get_db_path()
        data_dir = get_data_dir()
        backups_dir = get_backups_dir()
        rel_path = "data/medsafe.db" if not is_frozen() else str(db_path)
        return {
            "relative_db_path": rel_path,
            "db_path": str(db_path),
            "data_dir": str(data_dir),
            "backups_dir": str(backups_dir),
        }

    def open_data_folder(self) -> Tuple[bool, str]:
        """Open the local data/ folder in Windows Explorer."""
        from backend.config import get_data_dir

        return open_folder_in_explorer(get_data_dir())

    def open_backups_folder(self) -> Tuple[bool, str]:
        """Open the local backups/ folder in Windows Explorer."""
        from backend.config import get_backups_dir

        return open_folder_in_explorer(get_backups_dir())
