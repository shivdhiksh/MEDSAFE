"""File and directory interaction utilities for MEDSAFE.

Provides platform-safe folder navigation (such as Windows Explorer)
and local path resolution.
"""

import os
from pathlib import Path
import subprocess
import sys
from typing import Tuple, Union

from backend.utils.logger import get_logger

logger = get_logger(__name__)


def open_folder_in_explorer(folder_path: Union[str, Path]) -> Tuple[bool, str]:
    """Safely open a local directory in the operating system's native file explorer.

    - Ensures the directory exists locally before attempting to launch the file explorer.
    - Uses os.startfile on Windows for native shell integration.
    - Catches and logs all OS exceptions to avoid crashing the desktop interface.

    Args:
        folder_path: Target directory path to open.

    Returns:
        Tuple of (success: bool, status_message: str).
    """
    path = Path(folder_path).resolve()
    try:
        path.mkdir(parents=True, exist_ok=True)
        logger.info("Opening folder in explorer: %s", path)

        if sys.platform == "win32":
            os.startfile(str(path))
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=True)
        else:
            subprocess.run(["xdg-open", str(path)], check=True)

        return True, f"Opened {path.name} folder."
    except Exception as exc:
        logger.error("Failed to open folder '%s': %s", path, exc)
        return False, f"Could not open folder: {exc}"
