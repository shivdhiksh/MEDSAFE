"""Inventory view for MEDSAFE.

Provides complete inventory browsing with real-time name search, status filtering,
storage location filtering, and multi-criteria sorting.
"""

from typing import Callable, List, Optional
import customtkinter as ctk

from backend.models import InventoryItem
from backend.services.inventory_service import InventoryService
from frontend.components.status_badge import StatusBadge
from frontend.config import (
    COLOR_CARD,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_CAPTION,
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
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)

        self.inventory_service = inventory_service or InventoryService()
        self.on_view_medicine_callback = on_view_medicine
        self.on_add_medicine_callback = on_add_medicine

        self.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_controls()

        # Results container
        self.results_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.results_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 20))
        self.results_frame.grid_columnconfigure(0, weight=1)

        self.refresh()

    def _build_header(self) -> None:
        """Construct view header with title and action button."""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        header.grid_columnconfigure(0, weight=1)

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w")

        title = ctk.CTkLabel(title_box, text="Inventory", font=FONT_TITLE, anchor="w")
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            title_box,
            text="Browse, filter, and inspect your recorded medicines and batches.",
            font=FONT_CAPTION,
            text_color="gray",
            anchor="w",
        )
        subtitle.pack(anchor="w", pady=(2, 0))

        if self.on_add_medicine_callback is not None:
            add_btn = ctk.CTkButton(
                header,
                text="+ Add Medicine",
                font=FONT_BODY_BOLD,
                fg_color=COLOR_PRIMARY,
                hover_color=COLOR_PRIMARY_HOVER,
                height=38,
                command=self.on_add_medicine_callback,
            )
            add_btn.grid(row=0, column=1, sticky="e")

    def _build_controls(self) -> None:
        """Construct search bar, status filter, location filter, and sort options."""
        controls_card = ctk.CTkFrame(
            self,
            fg_color=COLOR_CARD,
            corner_radius=10,
            border_width=1,
            border_color=("gray85", "gray30"),
        )
        controls_card.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        controls_card.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Row 0: Search input
        search_box = ctk.CTkFrame(controls_card, fg_color="transparent")
        search_box.grid(row=0, column=0, columnspan=2, padx=14, pady=(14, 10), sticky="ew")

        ctk.CTkLabel(search_box, text="Search Medicine Name", font=FONT_CAPTION, text_color="gray", anchor="w").pack(
            fill="x", pady=(0, 2)
        )
        self.search_entry = ctk.CTkEntry(
            search_box,
            placeholder_text="Type medicine name to search...",
            font=FONT_BODY,
            height=36,
        )
        self.search_entry.pack(fill="x")
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh())

        # Row 0: Sort dropdown
        sort_box = ctk.CTkFrame(controls_card, fg_color="transparent")
        sort_box.grid(row=0, column=2, columnspan=2, padx=14, pady=(14, 10), sticky="ew")

        ctk.CTkLabel(sort_box, text="Sort By", font=FONT_CAPTION, text_color="gray", anchor="w").pack(
            fill="x", pady=(0, 2)
        )
        self.sort_menu = ctk.CTkOptionMenu(
            sort_box,
            values=[
                "Nearest Expiry First",
                "Oldest Expiry First",
                "Medicine Name A-Z",
                "Medicine Name Z-A",
            ],
            font=FONT_BODY,
            height=36,
            command=lambda v: self.refresh(),
        )
        self.sort_menu.set("Nearest Expiry First")
        self.sort_menu.pack(fill="x")

        # Row 1: Filters
        filters_row = ctk.CTkFrame(controls_card, fg_color="transparent")
        filters_row.grid(row=1, column=0, columnspan=4, padx=14, pady=(0, 14), sticky="ew")
        filters_row.grid_columnconfigure((0, 1, 2), weight=1)

        # Status filter
        status_box = ctk.CTkFrame(filters_row, fg_color="transparent")
        status_box.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        ctk.CTkLabel(status_box, text="Status Filter", font=FONT_CAPTION, text_color="gray", anchor="w").pack(
            fill="x", pady=(0, 2)
        )
        self.status_menu = ctk.CTkOptionMenu(
            status_box,
            values=["All", "Valid", "Expiring Soon", "Expired", "Disposed"],
            font=FONT_BODY,
            height=34,
            command=lambda v: self.refresh(),
        )
        self.status_menu.set("All")
        self.status_menu.pack(fill="x")

        # Location filter
        location_box = ctk.CTkFrame(filters_row, fg_color="transparent")
        location_box.grid(row=0, column=1, padx=8, sticky="ew")
        ctk.CTkLabel(location_box, text="Location Filter", font=FONT_CAPTION, text_color="gray", anchor="w").pack(
            fill="x", pady=(0, 2)
        )
        self.location_menu = ctk.CTkOptionMenu(
            location_box,
            values=["All Locations"],
            font=FONT_BODY,
            height=34,
            command=lambda v: self.refresh(),
        )
        self.location_menu.set("All Locations")
        self.location_menu.pack(fill="x")

        # Reset button
        reset_box = ctk.CTkFrame(filters_row, fg_color="transparent")
        reset_box.grid(row=0, column=2, padx=(8, 0), sticky="ew")
        ctk.CTkLabel(reset_box, text=" ", font=FONT_CAPTION).pack(pady=(0, 2))
        self.reset_btn = ctk.CTkButton(
            reset_box,
            text="Reset Filters",
            font=FONT_BODY,
            fg_color=("gray85", "gray30"),
            hover_color=("gray75", "gray40"),
            text_color=("black", "white"),
            height=34,
            command=self._reset_filters,
        )
        self.reset_btn.pack(fill="x")

    def _reset_filters(self) -> None:
        """Reset search and filter selections to defaults."""
        self.search_entry.delete(0, "end")
        self.status_menu.set("All")
        self.location_menu.set("All Locations")
        self.sort_menu.set("Nearest Expiry First")
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
            "Nearest Expiry First": "nearest_expiry",
            "Oldest Expiry First": "oldest_expiry",
            "Medicine Name A-Z": "name_asc",
            "Medicine Name Z-A": "name_desc",
        }
        sort_key = sort_map.get(self.sort_menu.get(), "nearest_expiry")

        # 3. Retrieve filtered items
        search_query = self.search_entry.get()
        status_filter = self.status_menu.get()
        selected_location = self.location_menu.get()
        loc_filter = "" if selected_location == "All Locations" else selected_location

        items: List[InventoryItem] = self.inventory_service.get_inventory(
            search_query=search_query,
            status_filter=status_filter,
            location_filter=loc_filter,
            sort_by=sort_key,
        )

        # 4. Clear existing widgets
        for child in self.results_frame.winfo_children():
            child.destroy()

        # 5. Handle empty states
        if not items:
            self._render_empty_state(search_query, status_filter, selected_location)
            return

        # 6. Render inventory cards
        for item in items:
            self._render_item_card(item)

    def _render_empty_state(self, search: str, status: str, loc: str) -> None:
        """Display an appropriate, actionable empty state message."""
        card = ctk.CTkFrame(
            self.results_frame,
            fg_color=COLOR_CARD,
            corner_radius=10,
            border_width=1,
            border_color=("gray85", "gray30"),
        )
        card.pack(fill="x", pady=20, padx=4)

        if search.strip():
            msg = "No medicines match your search."
            sub_msg = f"No medicines match '{search.strip()}'. Try checking for spelling mistakes or clearing search."
        elif status == "Disposed":
            msg = "No disposed batches found."
            sub_msg = "You have not marked any medicine batches as disposed yet."
        elif status != "All" or loc != "All Locations":
            msg = "No medicines match the selected filters."
            sub_msg = "Try selecting 'All' or clearing active filters to view all medicines."
        else:
            msg = "No medicines added yet."
            sub_msg = "Add your first medicine and batch to start tracking expiry dates."

        ctk.CTkLabel(card, text=msg, font=FONT_SECTION).pack(pady=(28, 4))
        ctk.CTkLabel(card, text=sub_msg, font=FONT_BODY, text_color=("gray40", "gray70")).pack(pady=(0, 16))

        if not search.strip() and status == "All" and loc == "All Locations":
            if self.on_add_medicine_callback is not None:
                cta = ctk.CTkButton(
                    card,
                    text="+ Add First Medicine",
                    font=FONT_BODY_BOLD,
                    fg_color=COLOR_PRIMARY,
                    hover_color=COLOR_PRIMARY_HOVER,
                    height=36,
                    command=self.on_add_medicine_callback,
                )
                cta.pack(pady=(0, 24))

    def _render_item_card(self, item: InventoryItem) -> None:
        """Render a single inventory item row."""
        card = ctk.CTkFrame(
            self.results_frame,
            fg_color=COLOR_CARD,
            corner_radius=10,
            border_width=1,
            border_color=("gray85", "gray30"),
        )
        card.pack(fill="x", pady=4, padx=2)
        card.grid_columnconfigure(0, weight=2)
        card.grid_columnconfigure(1, weight=1)
        card.grid_columnconfigure(2, weight=1)

        # Left Column: Medicine Name, Type, Strength, Manufacturer, Batch Number
        left = ctk.CTkFrame(card, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w", padx=16, pady=12)

        name_text = item.medicine_name
        if item.strength:
            name_text += f" ({item.strength})"
        if item.medicine_type:
            name_text += f" • {item.medicine_type}"

        title_lbl = ctk.CTkLabel(left, text=name_text, font=FONT_BODY_BOLD, anchor="w")
        title_lbl.pack(anchor="w")

        meta_parts = []
        if item.manufacturer:
            meta_parts.append(f"Mfr: {item.manufacturer}")
        if item.batch_number:
            meta_parts.append(f"Batch: {item.batch_number}")
        if item.storage_location:
            meta_parts.append(f"Location: {item.storage_location}")
        meta_parts.append(f"Quantity: {item.quantity}")

        meta_lbl = ctk.CTkLabel(
            left,
            text=" | ".join(meta_parts),
            font=FONT_CAPTION,
            text_color="gray",
            anchor="w",
        )
        meta_lbl.pack(anchor="w", pady=(2, 0))

        # Center Column: Expiry Date and readable countdown
        center = ctk.CTkFrame(card, fg_color="transparent")
        center.grid(row=0, column=1, sticky="w", padx=10, pady=12)

        exp_lbl = ctk.CTkLabel(center, text=f"Expires: {item.expiry_date}", font=FONT_BODY, anchor="w")
        exp_lbl.pack(anchor="w")

        countdown_lbl = ctk.CTkLabel(
            center,
            text=item.expiry_label,
            font=FONT_CAPTION,
            text_color=("gray30", "gray75"),
            anchor="w",
        )
        countdown_lbl.pack(anchor="w")

        # Right Column: Badge & Action Button
        right = ctk.CTkFrame(card, fg_color="transparent")
        right.grid(row=0, column=2, sticky="e", padx=16, pady=12)

        badge_status = "disposed" if item.status.lower() == "disposed" else item.expiry_status
        badge = StatusBadge(right, status=badge_status)
        badge.pack(side="left", padx=(0, 12))

        if self.on_view_medicine_callback is not None:
            view_btn = ctk.CTkButton(
                right,
                text="View / Edit",
                font=FONT_BODY,
                width=84,
                height=32,
                fg_color=("gray85", "gray30"),
                hover_color=("gray75", "gray40"),
                text_color=("black", "white"),
                command=lambda m_id=item.medicine_id: self.on_view_medicine_callback(m_id),
            )
            view_btn.pack(side="left")
