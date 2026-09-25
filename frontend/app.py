"""Root CustomTkinter window for MEDSAFE.

Assembles the permanent desktop application layout with a responsive left navigation sidebar
and seamless view routing across Dashboard, Inventory, Add Medicine, Medicine Detail,
Settings, and About views.
"""

import threading
from typing import Optional, Union
import customtkinter as ctk

from backend.config import APP_FULL_TITLE, ensure_directories_exist
from backend.database import init_db
from backend.services.backup_service import BackupService
from backend.services.inventory_service import InventoryService
from backend.services.medicine_service import MedicineService
from backend.services.notification_service import NotificationService
from backend.services.settings_service import SettingsService
from backend.utils.logger import get_logger
from frontend.components.sidebar import Sidebar
from frontend.config import (
    COLOR_BACKGROUND,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_TITLE,
)
from frontend.views.about_view import AboutView
from frontend.views.add_medicine_view import AddMedicineView
from frontend.views.dashboard_view import DashboardView
from frontend.views.inventory_view import InventoryView
from frontend.views.medicine_detail_view import MedicineDetailView
from frontend.views.settings_view import SettingsView

logger = get_logger(__name__)


class MedSafeApp(ctk.CTk):
    """Main application window for MedSafe desktop app."""

    def __init__(self) -> None:
        super().__init__()

        # Ensure runtime directories exist (data, backups) and initialize database
        ensure_directories_exist()
        init_db()

        # Shared backend services
        self.medicine_service = MedicineService()
        self.inventory_service = InventoryService()
        self.notification_service = NotificationService()
        self.settings_service = SettingsService()
        self.backup_service = BackupService()

        # Restore saved theme
        try:
            saved_theme = self.settings_service.get_settings().theme
            self._change_theme(saved_theme)
        except Exception:
            pass

        # Window configuration
        self.title(WINDOW_TITLE)
        self.geometry("1040x680")
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        # Center the window on display
        self._center_window()

        # Configure root layout: column 0 is sidebar (fixed), column 1 is content (expanding)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.current_view: Optional[ctk.CTkFrame] = None
        self._build_layout()

        # Start on Dashboard by default
        self.show_view("dashboard")

        # Non-blocking startup check for expiring medicine batches
        self.after(500, self._run_startup_expiry_check)

    def _center_window(self) -> None:
        """Position the window in the center of the user's primary monitor."""
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        width = 1040
        height = 680
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _build_layout(self) -> None:
        """Construct the permanent sidebar and main content viewport."""
        # 1. Left Sidebar
        self.sidebar = Sidebar(
            self,
            on_navigate=self.show_view,
            on_theme_change=self._change_theme,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # 2. Main Content Container
        self.content_area = ctk.CTkFrame(self, fg_color=COLOR_BACKGROUND, corner_radius=0)
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.content_area.grid_columnconfigure(0, weight=1)
        self.content_area.grid_rowconfigure(0, weight=1)

    def show_view(self, view_key: str, **kwargs) -> None:
        """Switch active view inside the content area.

        Args:
            view_key: Identifier for target view ('dashboard', 'inventory', 'add_medicine',
                      'medicine_detail', 'settings', 'about').
            kwargs: Extra parameters (e.g. medicine_id for 'medicine_detail').
        """
        if self.current_view is not None:
            self.current_view.destroy()
            self.current_view = None

        # Update sidebar active selection
        self.sidebar.set_active(view_key)

        if view_key == "dashboard":
            self.current_view = DashboardView(
                self.content_area,
                inventory_service=self.inventory_service,
                notification_service=self.notification_service,
                on_add_medicine=lambda: self.show_view("add_medicine"),
                on_view_medicine=lambda m_id: self.show_view("medicine_detail", medicine_id=m_id),
            )
        elif view_key == "inventory":
            self.current_view = InventoryView(
                self.content_area,
                inventory_service=self.inventory_service,
                on_view_medicine=lambda m_id: self.show_view("medicine_detail", medicine_id=m_id),
                on_add_medicine=lambda: self.show_view("add_medicine"),
            )
        elif view_key == "add_medicine":
            self.current_view = AddMedicineView(
                self.content_area,
                medicine_service=self.medicine_service,
                on_back=lambda: self.show_view("dashboard"),
            )
        elif view_key == "medicine_detail":
            med_id = kwargs.get("medicine_id", 0)
            self.current_view = MedicineDetailView(
                self.content_area,
                medicine_id=med_id,
                inventory_service=self.inventory_service,
                on_back=lambda: self.show_view("inventory"),
            )
        elif view_key == "settings":
            self.current_view = SettingsView(
                self.content_area,
                settings_service=self.settings_service,
                backup_service=self.backup_service,
                on_theme_change=self._change_theme,
            )
        elif view_key == "about":
            self.current_view = AboutView(self.content_area)
        else:
            self.current_view = DashboardView(
                self.content_area,
                inventory_service=self.inventory_service,
                notification_service=self.notification_service,
                on_add_medicine=lambda: self.show_view("add_medicine"),
                on_view_medicine=lambda m_id: self.show_view("medicine_detail", medicine_id=m_id),
            )

        self.current_view.grid(row=0, column=0, sticky="nsew")

    def _run_startup_expiry_check(self) -> None:
        """Execute the startup expiry notification check asynchronously without freezing the UI.

        Runs completely in a daemon background thread to keep Tkinter responsive.
        Thread-safe: does not touch Tkinter widgets or UI state directly.
        """
        def worker() -> None:
            try:
                logger.info("Starting background startup expiry notification check...")
                result = self.notification_service.check_and_notify_expiring_batches()
                logger.info(
                    "Startup expiry check finished: %d sent, %d duplicates suppressed, %d errors",
                    result.notifications_sent,
                    result.duplicates_suppressed,
                    result.errors_count,
                )
            except Exception as exc:
                logger.error("Startup expiry notification check encountered an error: %s", exc)

        threading.Thread(target=worker, daemon=True, name="StartupExpiryCheckWorker").start()

    def _change_theme(self, mode: str) -> None:
        """Switch appearance mode interactively."""
        ctk.set_appearance_mode(mode.lower())