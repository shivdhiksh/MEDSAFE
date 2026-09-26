"""Inventory view for MEDSAFE.

Provides complete inventory browsing with real-time name search, status filtering,
storage location filtering, multi-criteria sorting, and a polished table/card hybrid.
"""

from typing import Callable, List, Optional
import customtkinter as ctk

from backend.models import InventoryItem
from backend.services.inventory_service import InventoryService
from frontend.components.ambient_background import CapsuleCanvas
from frontend.components.glass_card import GlassCard, GlassCardHover
from frontend.components.search_bar import SearchBar
from frontend.components.status_badge import StatusBadge
from frontend.config import (
    COLOR_BORDER,
    COLOR_BTN_SECONDARY,
    COLOR_BTN_SECONDARY_HOVER,
    COLOR_BTN_SECONDARY_TEXT,
    COLOR_CARD,
    COLOR_CARD_ELEVATED,
    COLOR_INPUT_BG,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_CAPTION,
    FONT_CAPTION_BOLD,
    FONT_SECTION,
    FONT_SUBTITLE,
    FONT_TITLE,
)


class InventoryView(ctk.CTkScrollableFrame):
    """View container for browsing, filtering, and searching medicine inventory."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        inventory_service: Optional[InventoryService] = None,
        on_view_medicine: Optional[Callable[[int], None]] = None,
        on_add_medicine: Optional[Callable[[], None]] = None,
        initial_search: str = "",
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)

        self.inventory_service = inventory_service or InventoryService()
        self.on_view_medicine_callback = on_view_medicine
        self.on_add_medicine_callback = on_add_medicine
        self.initial_search = initial_search

        self.grid_columnconfigure(0, weight=1)

        self._build_controls()

        # Results container
        self.results_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.results_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 20))
        self.results_frame.grid_columnconfigure(0, weight=1)

        self.refresh()

    def _build_controls(self) -> None:
        """Construct glassmorphism filter control center."""
        controls_card = GlassCard(self)
        controls_card.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        controls_card.grid_columnconfigure(0, weight=2)
        controls_card.grid_columnconfigure(1, weight=1)

        # Row 0: Search & Sort
        row_0 = ctk.CTkFrame(controls_card, fg_color="transparent")
        row_0.pack(fill="x", padx=16, pady=(16, 12))
        row_0.grid_columnconfigure(0, weight=3)
        row_0.grid_columnconfigure(1, weight=2)

        # Search Bar
        search_box = ctk.CTkFrame(row_0, fg_color="transparent")
        search_box.grid(row=0, column=0, sticky="ew", padx=(0, 12))

        ctk.CTkLabel(
            search_box,
            text="Search Medicine Name",
            font=FONT_CAPTION_BOLD,
            text_color=COLOR_TEXT_SECONDARY,
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self.search_bar = SearchBar(
            search_box,
            placeholder="Type medicine name to search...",
            on_search=lambda q: self.refresh(),
            height=36,
        )
        self.search_bar.pack(fill="x")

        # Sort Dropdown
        sort_box = ctk.CTkFrame(row_0, fg_color="transparent")
        sort_box.grid(row=0, column=1, sticky="ew")

        ctk.CTkLabel(
            sort_box,
            text="Sort By",
            font=FONT_CAPTION_BOLD,
            text_color=COLOR_TEXT_SECONDARY,
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self.sort_menu = ctk.CTkOptionMenu(
            sort_box,
            values=[
                "Nearest Expiry",
                "Farthest Expiry",
                "Name A-Z",
                "Name Z-A",
            ],
            font=FONT_BODY,
            height=36,
            fg_color=COLOR_INPUT_BG,
            button_color=COLOR_PRIMARY,
            button_hover_color=COLOR_PRIMARY_HOVER,
            dropdown_fg_color=COLOR_CARD,
            dropdown_hover_color=COLOR_CARD_ELEVATED,
            dropdown_text_color=COLOR_TEXT_PRIMARY,
            text_color=COLOR_TEXT_PRIMARY,
            corner_radius=8,
            command=lambda v: self.refresh(),
        )
        self.sort_menu.set("Nearest Expiry")
        self.sort_menu.pack(fill="x")

        # Divider
        divider = ctk.CTkFrame(controls_card, height=1, fg_color=COLOR_BORDER)
        divider.pack(fill="x", padx=16, pady=(0, 12))

        # Row 1: Filters & Reset
        filters_row = ctk.CTkFrame(controls_card, fg_color="transparent")
        filters_row.pack(fill="x", padx=16, pady=(0, 16))
        filters_row.grid_columnconfigure((0, 1), weight=2)
        filters_row.grid_columnconfigure(2, weight=1)
        filters_row.grid_columnconfigure(3, weight=1)

        # Status filter
        status_box = ctk.CTkFrame(filters_row, fg_color="transparent")
        status_box.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        ctk.CTkLabel(
            status_box,
            text="Status Filter",
            font=FONT_CAPTION_BOLD,
            text_color=COLOR_TEXT_SECONDARY,
            anchor="w",
        ).pack(fill="x", pady=(0, 4))
        self.status_menu = ctk.CTkOptionMenu(
            status_box,
            values=["All", "Valid", "Expiring Soon", "Expired", "Disposed"],
            font=FONT_BODY,
            height=34,
            fg_color=COLOR_INPUT_BG,
            button_color=COLOR_PRIMARY,
            button_hover_color=COLOR_PRIMARY_HOVER,
            dropdown_fg_color=COLOR_CARD,
            dropdown_hover_color=COLOR_CARD_ELEVATED,
            dropdown_text_color=COLOR_TEXT_PRIMARY,
            text_color=COLOR_TEXT_PRIMARY,
            corner_radius=8,
            command=lambda v: self.refresh(),
        )
        self.status_menu.set("All")
        self.status_menu.pack(fill="x")

        # Location filter
        location_box = ctk.CTkFrame(filters_row, fg_color="transparent")
        location_box.grid(row=0, column=1, padx=8, sticky="ew")
        ctk.CTkLabel(
            location_box,
            text="Location Filter",
            font=FONT_CAPTION_BOLD,
            text_color=COLOR_TEXT_SECONDARY,
            anchor="w",
        ).pack(fill="x", pady=(0, 4))
        self.location_menu = ctk.CTkOptionMenu(
            location_box,
            values=["All Locations"],
            font=FONT_BODY,
            height=34,
            fg_color=COLOR_INPUT_BG,
            button_color=COLOR_PRIMARY,
            button_hover_color=COLOR_PRIMARY_HOVER,
            dropdown_fg_color=COLOR_CARD,
            dropdown_hover_color=COLOR_CARD_ELEVATED,
            dropdown_text_color=COLOR_TEXT_PRIMARY,
            text_color=COLOR_TEXT_PRIMARY,
            corner_radius=8,
            command=lambda v: self.refresh(),
        )
        self.location_menu.set("All Locations")
        self.location_menu.pack(fill="x")

        # Reset button
        reset_box = ctk.CTkFrame(filters_row, fg_color="transparent")
        reset_box.grid(row=0, column=2, padx=8, sticky="ew")
        ctk.CTkLabel(reset_box, text=" ", font=FONT_CAPTION).pack(pady=(0, 4))
        self.reset_btn = ctk.CTkButton(
            reset_box,
            text="Reset Filters",
            font=FONT_BODY,
            fg_color=COLOR_BTN_SECONDARY,
            hover_color=COLOR_BTN_SECONDARY_HOVER,
            text_color=COLOR_BTN_SECONDARY_TEXT,
            height=34,
            corner_radius=8,
            command=self._reset_filters,
        )
        self.reset_btn.pack(fill="x")

        # Results counter label
        counter_box = ctk.CTkFrame(filters_row, fg_color="transparent")
        counter_box.grid(row=0, column=3, padx=(8, 0), sticky="e")
        ctk.CTkLabel(counter_box, text=" ", font=FONT_CAPTION).pack(pady=(0, 4))
        self.count_label = ctk.CTkLabel(
            counter_box,
            text="",
            font=FONT_CAPTION_BOLD,
            text_color=COLOR_TEXT_MUTED,
            anchor="e",
        )
        self.count_label.pack(fill="x", pady=(6, 0))

        if self.initial_search:
            self.search_bar.set_text(self.initial_search, trigger_callback=False)

    def _reset_filters(self) -> None:
        """Reset search and filter selections to default values."""
        self.search_bar.clear()
        self.status_menu.set("All")
        self.location_menu.set("All Locations")
        self.sort_menu.set("Nearest Expiry")
        self.refresh()

    def refresh(self) -> None:
        """Query and display inventory items matching current search and filters."""
        # 1. Update dynamic location options
        locations = self.inventory_service.get_storage_locations()
        location_options = ["All Locations"] + locations
        self.location_menu.configure(values=location_options)
        if self.location_menu.get() not in location_options:
            self.location_menu.set("All Locations")

        # 2. Map sort menu choice to internal sort key
        sort_map = {
            "Nearest Expiry": "nearest_expiry",
            "Farthest Expiry": "oldest_expiry",
            "Name A-Z": "name_asc",
            "Name Z-A": "name_desc",
        }
        sort_key = sort_map.get(self.sort_menu.get(), "nearest_expiry")

        # 3. Retrieve filtered items from service
        search_query = self.search_bar.get()
        status_filter = self.status_menu.get()
        selected_location = self.location_menu.get()
        loc_filter = "" if selected_location == "All Locations" else selected_location

        items: List[InventoryItem] = self.inventory_service.get_inventory(
            search_query=search_query,
            status_filter=status_filter,
            location_filter=loc_filter,
            sort_by=sort_key,
        )

        # Update count indicator
        count_text = f"{len(items)} item{'s' if len(items) != 1 else ''}"
        self.count_label.configure(text=count_text)

        # 4. Clear existing items
        for child in self.results_frame.winfo_children():
            child.destroy()

        # 5. Handle empty states
        if not items:
            self._render_empty_state(search_query, status_filter, selected_location)
            return

        # 6. Render column header row
        self._render_table_header()

        # 7. Render inventory cards
        for item in items:
            self._render_item_card(item)

    def _render_table_header(self) -> None:
        """Render column header hints for the table/card hybrid list."""
        header_row = ctk.CTkFrame(self.results_frame, fg_color="transparent", height=24)
        header_row.pack(fill="x", padx=16, pady=(0, 4))
        header_row.grid_columnconfigure(0, weight=2)
        header_row.grid_columnconfigure(1, weight=1)
        header_row.grid_columnconfigure(2, weight=1)
        header_row.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(
            header_row,
            text="MEDICINE & DETAILS",
            font=FONT_CAPTION_BOLD,
            text_color=COLOR_TEXT_MUTED,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header_row,
            text="BATCH & STORAGE",
            font=FONT_CAPTION_BOLD,
            text_color=COLOR_TEXT_MUTED,
            anchor="w",
        ).grid(row=0, column=1, sticky="w", padx=10)

        ctk.CTkLabel(
            header_row,
            text="EXPIRY & TIMELINE",
            font=FONT_CAPTION_BOLD,
            text_color=COLOR_TEXT_MUTED,
            anchor="w",
        ).grid(row=0, column=2, sticky="w", padx=10)

        ctk.CTkLabel(
            header_row,
            text="STATUS & ACTION",
            font=FONT_CAPTION_BOLD,
            text_color=COLOR_TEXT_MUTED,
            anchor="e",
        ).grid(row=0, column=3, sticky="e")

    def _render_empty_state(self, search: str, status: str, loc: str) -> None:
        """Display an actionable empty state message when no medicines match."""
        card = GlassCard(self.results_frame)
        card.pack(fill="x", pady=20, padx=4)

        if search.strip():
            msg = "No medicines match your search."
            sub_msg = f"No records found matching '{search.strip()}'. Check for spelling mistakes or reset search."
            icon = "🔍"
        elif status == "Disposed":
            msg = "No disposed batches found."
            sub_msg = "You have not marked any medicine batches as disposed yet."
            icon = "🗑️"
        elif status != "All" or loc != "All Locations":
            msg = "No medicines match the selected filters."
            sub_msg = "Try clearing active filters to view all recorded medicines."
            icon = "📋"
        else:
            msg = "No medicines added yet."
            sub_msg = "Add your first medicine and batch to start tracking expiry dates locally."
            icon = "📦"

        ctk.CTkLabel(card, text=icon, font=(FONT_TITLE[0], 32)).pack(pady=(28, 6))
        ctk.CTkLabel(card, text=msg, font=FONT_SECTION, text_color=COLOR_TEXT_PRIMARY).pack(pady=(0, 4))
        ctk.CTkLabel(card, text=sub_msg, font=FONT_BODY, text_color=COLOR_TEXT_MUTED).pack(pady=(0, 20))

        if not search.strip() and status == "All" and loc == "All Locations":
            if self.on_add_medicine_callback is not None:
                cta = ctk.CTkButton(
                    card,
                    text="➕ Add First Medicine",
                    font=FONT_BODY_BOLD,
                    fg_color=COLOR_PRIMARY,
                    hover_color=COLOR_PRIMARY_HOVER,
                    text_color="white",
                    height=36,
                    corner_radius=8,
                    command=self.on_add_medicine_callback,
                )
                cta.pack(pady=(0, 28))

    def _render_item_card(self, item: InventoryItem) -> None:
        """Render a single inventory item row in glass hover card format."""
        card = GlassCardHover(
            self.results_frame,
            default_fg=COLOR_CARD,
            hover_fg=COLOR_CARD_ELEVATED,
            corner_radius=10,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        card.pack(fill="x", pady=4, padx=2)
        card.grid_columnconfigure(0, weight=2)
        card.grid_columnconfigure(1, weight=1)
        card.grid_columnconfigure(2, weight=1)
        card.grid_columnconfigure(3, weight=1)

        # Column 0: Capsule Icon + Medicine Name, Type, Strength, Manufacturer
        col0 = ctk.CTkFrame(card, fg_color="transparent")
        col0.grid(row=0, column=0, sticky="w", padx=16, pady=12)

        capsule = CapsuleCanvas(col0, size=28)
        capsule.pack(side="left", padx=(0, 10))

        text_sub = ctk.CTkFrame(col0, fg_color="transparent")
        text_sub.pack(side="left", fill="y", expand=True)

        name_text = item.medicine_name
        if item.strength:
            name_text += f" ({item.strength})"

        title_lbl = ctk.CTkLabel(
            text_sub,
            text=name_text,
            font=FONT_BODY_BOLD,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
            wraplength=240,
            justify="left",
        )
        title_lbl.pack(anchor="w")

        meta_parts = []
        if item.medicine_type:
            meta_parts.append(item.medicine_type)
        if item.manufacturer:
            meta_parts.append(item.manufacturer)

        if meta_parts:
            meta_lbl = ctk.CTkLabel(
                text_sub,
                text=" • ".join(meta_parts),
                font=FONT_CAPTION,
                text_color=COLOR_TEXT_MUTED,
                anchor="w",
            )
            meta_lbl.pack(anchor="w", pady=(2, 0))

        # Column 1: Batch & Storage Location
        col1 = ctk.CTkFrame(card, fg_color="transparent")
        col1.grid(row=0, column=1, sticky="w", padx=10, pady=12)

        batch_str = f"Batch: {item.batch_number or 'Standard'}"
        batch_lbl = ctk.CTkLabel(
            col1,
            text=batch_str,
            font=FONT_BODY,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        )
        batch_lbl.pack(anchor="w")

        info_sub = []
        if item.storage_location:
            info_sub.append(f"📍 {item.storage_location}")
        info_sub.append(f"Qty: {item.quantity}")

        col1_sub = ctk.CTkLabel(
            col1,
            text=" • ".join(info_sub),
            font=FONT_CAPTION,
            text_color=COLOR_TEXT_MUTED,
            anchor="w",
        )
        col1_sub.pack(anchor="w", pady=(2, 0))

        # Column 2: Expiry Date and countdown
        col2 = ctk.CTkFrame(card, fg_color="transparent")
        col2.grid(row=0, column=2, sticky="w", padx=10, pady=12)

        exp_lbl = ctk.CTkLabel(
            col2,
            text=f"Expires: {item.expiry_date}",
            font=FONT_BODY,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        )
        exp_lbl.pack(anchor="w")

        countdown_lbl = ctk.CTkLabel(
            col2,
            text=item.expiry_label,
            font=FONT_CAPTION_BOLD,
            text_color=COLOR_TEXT_SECONDARY,
            anchor="w",
        )
        countdown_lbl.pack(anchor="w", pady=(2, 0))

        # Column 3: Badge & Action Button
        col3 = ctk.CTkFrame(card, fg_color="transparent")
        col3.grid(row=0, column=3, sticky="e", padx=16, pady=12)

        badge_status = "disposed" if item.status.lower() == "disposed" else item.expiry_status
        badge = StatusBadge(col3, status=badge_status)
        badge.pack(side="left", padx=(0, 10))

        if self.on_view_medicine_callback is not None:
            view_btn = ctk.CTkButton(
                col3,
                text="View / Edit",
                font=FONT_BODY,
                width=88,
                height=32,
                corner_radius=8,
                fg_color=COLOR_BTN_SECONDARY,
                hover_color=COLOR_BTN_SECONDARY_HOVER,
                text_color=COLOR_BTN_SECONDARY_TEXT,
                command=lambda m_id=item.medicine_id: self.on_view_medicine_callback(m_id),
            )
            view_btn.pack(side="left")
