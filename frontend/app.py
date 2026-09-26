"""Root CustomTkinter window for MEDSAFE.

Assembles the permanent desktop application layout with a responsive left navigation sidebar,
modern top header with search and contextual actions, and seamless view routing across
Dashboard, Inventory, Add Medicine, Medicine Detail, Settings, and About views.
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
from frontend.components.ambient_background import AmbientBackground
from frontend.components.search_bar import SearchBar
from frontend.components.sidebar import Sidebar
from frontend.config import (
    COLOR_BACKGROUND,
    COLOR_BORDER,
    COLOR_HEADER_BG,
    COLOR_BTN_SECONDARY,
    COLOR_BTN_SECONDARY_HOVER,
    COLOR_BTN_SECONDARY_TEXT,
    COLOR_CARD,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_PRIMARY_SUBTLE,
    COLOR_SIDEBAR,
    COLOR_SIDEBAR_BORDER,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_CAPTION,
    FONT_CAPTION_BOLD,
    FONT_SECTION,
    FONT_TITLE,
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

        # Set application icon (both taskbar and window frame)
        try:
            if sys.platform == "win32":
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("MedSafe.App.1.1.0")
            from backend.config import get_icon_path
            icon_file = get_icon_path()
            if icon_file.exists():
                self.iconbitmap(str(icon_file))
        except Exception as exc:
            logger.warning("Could not set application window icon: %s", exc)

        # Center the window on display
        self._center_window()

        # Configure root grid: col 0 is sidebar (fixed), col 1 is main area (expanding)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.current_view: Optional[ctk.CTkFrame] = None
        self.active_view_key: str = "dashboard"
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
        """Construct the full-window ambient background, floating glass sidebar, top header, and workspace."""
        # 0. Full-Window Ambient Background
        self.ambient_bg = AmbientBackground(
            self,
            draw_blobs=True,
            draw_waves=True,
        )
        self.ambient_bg.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        # 1. Floating Glass Sidebar (Detached with margins and rounded corners)
        self.sidebar = Sidebar(
            self,
            on_navigate=self.show_view,
            on_theme_change=self._change_theme,
        )
        self.sidebar.grid(row=0, column=0, padx=(16, 8), pady=16, sticky="ns")

        # 2. Main Right Container (Transparent workspace over ambient background)
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, padx=(6, 16), pady=16, sticky="nsew")
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(1, weight=1)

        # 3. Floating Glass Top Header Bar
        self._build_top_header()

        # 4. Viewport Area (contains current view)
        self.content_area = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_area.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        self.content_area.grid_columnconfigure(0, weight=1)
        self.content_area.grid_rowconfigure(0, weight=1)

    def _build_top_header(self) -> None:
        """Construct floating glass top header with page title, search bar, and contextual actions."""
        self.top_header = ctk.CTkFrame(
            self.main_container,
            height=58,
            corner_radius=14,
            fg_color=COLOR_HEADER_BG,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.top_header.grid(row=0, column=0, sticky="ew", pady=(0, 2))
        self.top_header.grid_columnconfigure(0, weight=1)

        # Left title container
        self.header_title_box = ctk.CTkFrame(self.top_header, fg_color="transparent")
        self.header_title_box.grid(row=0, column=0, sticky="w", padx=16, pady=10)

        self.header_title_lbl = ctk.CTkLabel(
            self.header_title_box,
            text="Dashboard",
            font=FONT_TITLE,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        )
        self.header_title_lbl.pack(anchor="w")

        self.header_subtitle_lbl = ctk.CTkLabel(
            self.header_title_box,
            text="Overview of medicine inventory and active batches",
            font=FONT_CAPTION,
            text_color=COLOR_TEXT_MUTED,
            anchor="w",
        )
        self.header_subtitle_lbl.pack(anchor="w")

        # Right action & search container
        self.header_right_box = ctk.CTkFrame(self.top_header, fg_color="transparent")
        self.header_right_box.grid(row=0, column=1, sticky="e", padx=16, pady=10)

        # Header Search Bar
        self.header_search = SearchBar(
            self.header_right_box,
            placeholder="Search medicines...",
            on_search=self._handle_header_search,
            width=220,
            height=34,
        )
        self.header_search.pack(side="left", padx=(0, 10))

        # Contextual Action Button (Add Medicine / Back)
        self.header_action_btn = ctk.CTkButton(
            self.header_right_box,
            text="➕ Add Medicine",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            text_color="white",
            height=34,
            corner_radius=8,
            command=lambda: self.show_view("add_medicine"),
        )
        self.header_action_btn.pack(side="left")

    def _handle_header_search(self, query: str) -> None:
        """Route header search to inventory view."""
        if self.active_view_key != "inventory":
            # Switch to inventory with the search prefilled
            self.show_view("inventory", search=query)
        else:
            if isinstance(self.current_view, InventoryView):
                self.current_view.search_bar.set_text(query)

    def _update_header(self, view_key: str, **kwargs) -> None:
        """Update top header title, subtitle, and contextual action for active view."""
        self.active_view_key = view_key

        if view_key == "dashboard":
            self.header_title_lbl.configure(text="Dashboard")
            self.header_subtitle_lbl.configure(text="Real-time household medicine stock and expiry tracking")
            self.header_action_btn.configure(
                text="➕ Add Medicine",
                fg_color=COLOR_PRIMARY,
                hover_color=COLOR_PRIMARY_HOVER,
                text_color="white",
                command=lambda: self.show_view("add_medicine"),
            )
            self.header_action_btn.pack(side="left")
            self.header_search.pack(side="left", padx=(0, 10))
        elif view_key == "inventory":
            self.header_title_lbl.configure(text="Inventory")
            self.header_subtitle_lbl.configure(text="Browse, filter, and inspect tracked medicines and batches")
            self.header_action_btn.configure(
                text="➕ Add Medicine",
                fg_color=COLOR_PRIMARY,
                hover_color=COLOR_PRIMARY_HOVER,
                text_color="white",
                command=lambda: self.show_view("add_medicine"),
            )
            self.header_action_btn.pack(side="left")
            # In inventory, header search can stay or hide since inventory has its own prominent search
            self.header_search.pack(side="left", padx=(0, 10))
        elif view_key == "add_medicine":
            self.header_title_lbl.configure(text="Add Medicine")
            self.header_subtitle_lbl.configure(text="Record drug profile details and initial batch expiry date")
            self.header_action_btn.configure(
                text="← Back to Dashboard",
                fg_color=COLOR_BTN_SECONDARY,
                hover_color=COLOR_BTN_SECONDARY_HOVER,
                text_color=COLOR_BTN_SECONDARY_TEXT,
                command=lambda: self.show_view("dashboard"),
            )
            self.header_action_btn.pack(side="left")
            self.header_search.pack_forget()
        elif view_key == "medicine_detail":
            self.header_title_lbl.configure(text="Medicine Details")
            self.header_subtitle_lbl.configure(text="Inspect profile, edit information, and manage batches")
            self.header_action_btn.configure(
                text="← Back to Inventory",
                fg_color=COLOR_BTN_SECONDARY,
                hover_color=COLOR_BTN_SECONDARY_HOVER,
                text_color=COLOR_BTN_SECONDARY_TEXT,
                command=lambda: self.show_view("inventory"),
            )
            self.header_action_btn.pack(side="left")
            self.header_search.pack_forget()
        elif view_key == "settings":
            self.header_title_lbl.configure(text="Settings")
            self.header_subtitle_lbl.configure(text="Notifications, appearance, offline data management, and storage")
            self.header_action_btn.pack_forget()
            self.header_search.pack_forget()
        elif view_key == "about":
            self.header_title_lbl.configure(text="About MedSafe")
            self.header_subtitle_lbl.configure(text="Offline privacy commitment and mandatory safety notices")
            self.header_action_btn.pack_forget()
            self.header_search.pack_forget()
        else:
            self.header_title_lbl.configure(text=view_key.title())
            self.header_subtitle_lbl.configure(text="")
            self.header_action_btn.pack_forget()

    def show_view(self, view_key: str, **kwargs) -> None:
        """Switch active view inside the content area.

        Args:
            view_key: Identifier for target view ('dashboard', 'inventory', 'add_medicine',
                      'medicine_detail', 'settings', 'about').
            kwargs: Extra parameters (e.g. medicine_id for 'medicine_detail', search for 'inventory').
        """
        if self.current_view is not None:
            self.current_view.destroy()
            self.current_view = None

        # Update sidebar active selection
        self.sidebar.set_active(view_key)

        # Update top header
        self._update_header(view_key, **kwargs)

        if view_key == "dashboard":
            self.current_view = DashboardView(
                self.content_area,
                inventory_service=self.inventory_service,
                notification_service=self.notification_service,
                on_add_medicine=lambda: self.show_view("add_medicine"),
                on_view_medicine=lambda m_id: self.show_view("medicine_detail", medicine_id=m_id),
                on_view_inventory=lambda: self.show_view("inventory"),
            )
        elif view_key == "inventory":
            search_query = kwargs.get("search", "")
            self.current_view = InventoryView(
                self.content_area,
                inventory_service=self.inventory_service,
                on_view_medicine=lambda m_id: self.show_view("medicine_detail", medicine_id=m_id),
                on_add_medicine=lambda: self.show_view("add_medicine"),
                initial_search=search_query,
            )
        elif view_key == "add_medicine":
            self.current_view = AddMedicineView(
                self.content_area,
                medicine_service=self.medicine_service,
                on_back=lambda: self.show_view("dashboard"),
                on_medicine_saved=lambda res: self.show_view("medicine_detail", medicine_id=res.medicine.id),
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
                notification_service=self.notification_service,
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
                on_view_inventory=lambda: self.show_view("inventory"),
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
        """Switch appearance mode interactively and refresh ambient canvas."""
        ctk.set_appearance_mode(mode.lower())
        if hasattr(self, "ambient_bg"):
            self.after(50, self.ambient_bg.redraw)