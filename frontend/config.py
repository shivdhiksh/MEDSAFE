"""UI configuration, theme settings, color palettes, and fonts for MEDSAFE.
"""

from typing import Tuple

# Window dimensions
WINDOW_TITLE: str = "MedSafe"
WINDOW_DEFAULT_SIZE: str = "960x640"
WINDOW_MIN_WIDTH: int = 840
WINDOW_MIN_HEIGHT: int = 540

# Fonts (using Windows native typography)
FONT_FAMILY: str = "Segoe UI"
FONT_TITLE: Tuple[str, int, str] = (FONT_FAMILY, 22, "bold")
FONT_SUBTITLE: Tuple[str, int, str] = (FONT_FAMILY, 16, "bold")
FONT_SECTION: Tuple[str, int, str] = (FONT_FAMILY, 14, "bold")
FONT_BODY: Tuple[str, int] = (FONT_FAMILY, 13)
FONT_BODY_BOLD: Tuple[str, int, str] = (FONT_FAMILY, 13, "bold")
FONT_CAPTION: Tuple[str, int] = (FONT_FAMILY, 11)
FONT_DISCLAIMER: Tuple[str, int, str] = (FONT_FAMILY, 11, "italic")

# Color palette: Tuple of (Light Mode, Dark Mode)
# Soft medical blue/teal aesthetic
COLOR_PRIMARY: Tuple[str, str] = ("#0284C7", "#38BDF8")         # Medical Sky/Blue
COLOR_PRIMARY_HOVER: Tuple[str, str] = ("#0369A1", "#0284C7")
COLOR_BACKGROUND: Tuple[str, str] = ("#F8FAFC", "#0F172A")      # Light Slate / Dark Navy
COLOR_CARD: Tuple[str, str] = ("#FFFFFF", "#1E293B")            # White card / Slate card
COLOR_BORDER: Tuple[str, str] = ("#E2E8F0", "#334155")

# Status Colors
STATUS_VALID: Tuple[str, str] = ("#16A34A", "#22C55E")          # Green
STATUS_EXPIRING: Tuple[str, str] = ("#D97706", "#F59E0B")       # Amber/Orange
STATUS_EXPIRED: Tuple[str, str] = ("#DC2626", "#EF4444")        # Red
STATUS_INACTIVE: Tuple[str, str] = ("#64748B", "#94A3B8")       # Slate Grey
