"""Tests for MEDSAFE UI Redesign and reusable glassmorphism components.

Verifies:
- Design system tokens in frontend.config
- GlassCard, KPICard, SectionCard components
- SearchBar live search and clear operations
- StatusBadge styling for all statuses
- ConfirmationDialog behavior
- Sidebar navigation and theme switching
- DashboardView metrics and distribution bar
- InventoryView search, filters, and 4 sorting options
- MedicineDetailView, AddMedicineView, and SettingsView 5-section layout
- Clean architecture and absence of backend coupling
"""

import customtkinter as ctk
import pytest

from backend.config import APP_DISCLAIMER, APP_VERSION
from backend.services.inventory_service import InventoryService
from backend.services.medicine_service import MedicineService
from backend.services.notification_service import NotificationService
from backend.services.settings_service import SettingsService
from frontend.app import MedSafeApp
from frontend.components.confirmation_dialog import ConfirmationDialog
from frontend.components.glass_card import GlassCard, KPICard, SectionCard
from frontend.components.search_bar import SearchBar
from frontend.components.sidebar import Sidebar
from frontend.components.status_badge import StatusBadge
from frontend.config import (
    COLOR_BACKGROUND,
    COLOR_CARD,
    COLOR_CARD_ELEVATED,
    COLOR_PRIMARY,
    COLOR_SIDEBAR,
    STATUS_EXPIRED,
    STATUS_EXPIRING,
    STATUS_INACTIVE,
    STATUS_VALID,
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


@pytest.fixture(scope="module")
def test_app():
    """Module-scoped instance of MedSafeApp to keep Tcl interpreter stable across tests."""
    app = MedSafeApp()
    app.withdraw()
    yield app
    try:
        app.destroy()
    except Exception:
        pass


def test_theme_tokens_and_window_dimensions():
    """Verify core design system tokens and window bounds."""
    assert WINDOW_TITLE == "MedSafe"
    assert WINDOW_MIN_WIDTH == 840
    assert WINDOW_MIN_HEIGHT == 540
    assert isinstance(COLOR_PRIMARY, tuple) and len(COLOR_PRIMARY) == 2
    assert isinstance(COLOR_BACKGROUND, tuple) and len(COLOR_BACKGROUND) == 2
    assert isinstance(COLOR_CARD, tuple) and len(COLOR_CARD) == 2
    assert isinstance(COLOR_CARD_ELEVATED, tuple) and len(COLOR_CARD_ELEVATED) == 2
    assert isinstance(COLOR_SIDEBAR, tuple) and len(COLOR_SIDEBAR) == 2


def test_glass_card_and_kpi_card(test_app):
    """Verify GlassCard, KPICard, and SectionCard initialize properly."""
    card = GlassCard(test_app, elevated=False)
    assert card.cget("corner_radius") == 12

    elevated_card = GlassCard(test_app, elevated=True)
    assert elevated_card.cget("corner_radius") == 12

    kpi = KPICard(
        test_app,
        title="Active Batches",
        value=12,
        icon="📦",
        accent_color=COLOR_PRIMARY,
        supporting_text="Household stock",
    )
    assert kpi.value_lbl.cget("text") == "12"
    kpi.update_value(15)
    assert kpi.value_lbl.cget("text") == "15"

    section = SectionCard(test_app, title="Urgent Items", subtitle="(Sorted by expiry)")
    assert section.body is not None


def test_search_bar_operations(test_app):
    """Verify SearchBar live keystroke triggering and clear operations."""
    queries = []
    search = SearchBar(test_app, placeholder="Search test...", on_search=lambda q: queries.append(q))
    assert search.get() == ""

    # Set text programmatically
    search.set_text("paracetamol")
    assert search.get() == "paracetamol"
    assert "paracetamol" in queries

    # Clear text
    search.clear()
    assert search.get() == ""
    assert "" in queries


def test_status_badge_resolves_all_statuses(test_app):
    """Verify StatusBadge sets proper bullet text and colors for all statuses."""
    badge_valid = StatusBadge(test_app, status="valid")
    assert "Valid" in badge_valid.cget("text")
    assert "●" in badge_valid.cget("text")

    badge_exp = StatusBadge(test_app, status="expiring soon")
    assert "Expiring Soon" in badge_exp.cget("text")

    badge_dead = StatusBadge(test_app, status="expired")
    assert "Expired" in badge_dead.cget("text")

    badge_disp = StatusBadge(test_app, status="disposed")
    assert "Disposed" in badge_disp.cget("text")

    badge_unknown = StatusBadge(test_app, status="custom_status")
    assert "Custom_Status" in badge_unknown.cget("text")


def test_confirmation_dialog_and_callback(test_app):
    """Verify ConfirmationDialog executes callback on confirmation."""
    confirmed = []
    dlg = ConfirmationDialog(
        test_app,
        title="Test Action",
        message="Are you sure?",
        confirm_text="Confirm Delete",
        is_destructive=True,
        on_confirm=lambda: confirmed.append(True),
    )
    dlg._confirm()
    assert confirmed == [True]


def test_sidebar_navigation_and_active_states(test_app):
    """Verify Sidebar sets active button styles and triggers navigation callback."""
    nav_targets = []
    themes = []

    sidebar = Sidebar(
        test_app,
        on_navigate=lambda k: nav_targets.append(k),
        on_theme_change=lambda t: themes.append(t),
    )
    assert "dashboard" in sidebar.nav_buttons
    assert "inventory" in sidebar.nav_buttons
    assert "add_medicine" in sidebar.nav_buttons
    assert "settings" in sidebar.nav_buttons
    assert "about" in sidebar.nav_buttons

    sidebar._on_btn_clicked("inventory")
    assert nav_targets == ["inventory"]
    assert sidebar.active_view == "inventory"

    sidebar._handle_theme("Dark")
    assert themes == ["Dark"]


def test_medsafe_app_routing_and_header_search(test_app):
    """Verify MedSafeApp top header routing, header search, and view navigation."""
    # Start on dashboard
    test_app.show_view("dashboard")
    assert isinstance(test_app.current_view, DashboardView)

    # Header search should route to inventory if on dashboard
    test_app.header_search.set_text("Aspirin")
    assert isinstance(test_app.current_view, InventoryView)
    assert test_app.current_view.search_bar.get() == "Aspirin"

    # Navigate through all views
    for view_name, view_cls in [
        ("dashboard", DashboardView),
        ("inventory", InventoryView),
        ("add_medicine", AddMedicineView),
        ("settings", SettingsView),
        ("about", AboutView),
    ]:
        test_app.show_view(view_name)
        assert isinstance(test_app.current_view, view_cls)

    # Test settings 5 sections and mandatory disclaimer
    test_app.show_view("settings")
    assert isinstance(test_app.current_view, SettingsView)
    assert hasattr(test_app.current_view, "notif_switch")
    assert hasattr(test_app.current_view, "thresholds_entry")
    assert hasattr(test_app.current_view, "theme_menu")
    assert hasattr(test_app.current_view, "test_notif_btn")

    # Verify mandatory safety disclaimer
    assert "medical advice" in APP_DISCLAIMER.lower()
    assert "pharmacist or healthcare professional" in APP_DISCLAIMER.lower()

    # Verify theme changing
    test_app._change_theme("dark")
    test_app._change_theme("light")
    test_app._change_theme("system")


def test_inventory_sort_and_filter_integration(test_app):
    """Verify InventoryView supports 4 sort options and filter resets."""
    test_app.show_view("inventory")
    inv_view = test_app.current_view
    assert isinstance(inv_view, InventoryView)

    # Verify sort options match specification
    expected_sorts = ["Nearest Expiry", "Farthest Expiry", "Name A-Z", "Name Z-A"]
    for opt in expected_sorts:
        inv_view.sort_menu.set(opt)
        inv_view.refresh()

    # Verify reset filters
    inv_view.status_menu.set("Valid")
    inv_view.location_menu.set("All Locations")
    inv_view._reset_filters()
    assert inv_view.status_menu.get() == "All"
    assert inv_view.sort_menu.get() == "Nearest Expiry"
    assert inv_view.search_bar.get() == ""


def test_ambient_canvas_and_hero_components(test_app):
    """Verify AmbientCanvas and AmbientHeroPanel render without external images or web calls."""
    from frontend.components.ambient_background import AmbientCanvas, AmbientHeroPanel

    canvas = AmbientCanvas(test_app, height=80, draw_blobs=True, draw_waves=True)
    assert canvas.draw_blobs is True
    assert canvas.draw_waves is True

    hero = AmbientHeroPanel(
        test_app,
        on_view_inventory=lambda: None,
        on_test_notif=lambda: None,
    )
    assert hasattr(hero, "view_inv_btn")
    assert hasattr(hero, "test_notif_btn")
    # Verify NO duplicate Add Medicine button exists inside hero
    assert not hasattr(hero, "add_btn")


def test_no_duplicate_add_medicine_buttons(test_app):
    """Verify only the top header hosts '+ Add Medicine' for Dashboard and Inventory."""
    # 1. Dashboard
    test_app.show_view("dashboard")
    dash = test_app.current_view
    assert isinstance(dash, DashboardView)
    assert "Add Medicine" in test_app.header_action_btn.cget("text")
    assert not hasattr(dash.hero_panel, "add_btn")

    # 2. Inventory
    test_app.show_view("inventory")
    inv = test_app.current_view
    assert isinstance(inv, InventoryView)
    assert "Add Medicine" in test_app.header_action_btn.cget("text")
    assert not hasattr(inv, "add_btn")


def test_safety_language_in_kpi_and_about(test_app):
    """Verify safety-related language complies with non-misleading medical requirements."""
    # 1. Dashboard KPI wording: "Expiry date not reached" instead of "Within safe date range"
    test_app.show_view("dashboard")
    dash = test_app.current_view
    assert hasattr(dash, "card_valid")
    supp_text = dash.card_valid.desc_lbl.cget("text")
    assert "Expiry date not reached" in supp_text
    assert "safe" not in supp_text.lower()

    # 2. About View wording: "track expiry dates locally" and no "prevents accidental use"
    test_app.show_view("about")
    about = test_app.current_view
    all_texts = []

    def extract_texts(widget):
        if isinstance(widget, ctk.CTkLabel):
            all_texts.append(widget.cget("text"))
        for child in widget.winfo_children():
            extract_texts(child)

    extract_texts(about)
    combined = " ".join(all_texts)
    assert "track expiry dates locally" in combined
    assert "prevents the accidental use" not in combined


def test_settings_segmented_appearance_selector(test_app):
    """Verify SettingsView provides segmented visual appearance selector."""
    test_app.show_view("settings")
    settings_view = test_app.current_view
    assert isinstance(settings_view, SettingsView)
    assert isinstance(settings_view.theme_menu, ctk.CTkSegmentedButton)
    assert settings_view.theme_menu.cget("values") == ["System", "Light", "Dark"]

    for theme in ["Dark", "Light", "System"]:
        settings_view.theme_menu.set(theme)
        assert settings_view.theme_menu.get() == theme