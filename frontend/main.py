"""Application entry point for MEDSAFE.

Launches the CustomTkinter desktop interface or handles CLI commands
for background scheduled notification checks and database utilities.

CLI Usage:
    python -m frontend.main                       # Launch desktop GUI
    python -m frontend.main --check-notifications # Headless expiry check (Task Scheduler)
    python -m frontend.main --migrate-db <path>   # Migrate existing database
    python -m frontend.main --version             # Display version
    python -m frontend.main --help                # Display help
"""

import argparse
import sys
from typing import List, Optional

from backend.config import APP_FULL_TITLE, APP_NAME, APP_VERSION, ensure_directories_exist
from backend.database import init_db, migrate_database
from backend.services.notification_service import NotificationService
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def parse_arguments(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line options for MEDSAFE."""
    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        description=f"{APP_FULL_TITLE} (v{APP_VERSION})",
        add_help=False,
    )
    parser.add_argument(
        "--check-notifications",
        action="store_true",
        help="Perform offline expiry checks and dispatch toast notifications without launching the GUI.",
    )
    parser.add_argument(
        "--migrate-db",
        metavar="SOURCE_PATH",
        type=str,
        help="Migrate an existing SQLite database file into the production database location.",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="store_true",
        help="Show program version and exit.",
    )
    parser.add_argument(
        "--help",
        "-h",
        action="store_true",
        help="Show this help message and exit.",
    )
    return parser.parse_args(argv)


def run_headless_notification_check() -> int:
    """Execute background expiry check for Task Scheduler or CLI verification.

    Does not import or initialize CustomTkinter.
    Returns 0 on success.
    """
    logger.info("Executing headless notification check via CLI flag --check-notifications")
    ensure_directories_exist()
    init_db()

    service = NotificationService()
    result = service.check_and_notify_expiring_batches()

    print(
        f"MEDSAFE Expiry Check: {result.checked_count} checked, "
        f"{result.notifications_sent} sent, "
        f"{result.duplicates_suppressed} duplicates suppressed, "
        f"{result.errors_count} errors."
    )
    return 0


def run_gui() -> int:
    """Initialize and run the MedSafe CustomTkinter desktop application."""
    import customtkinter as ctk
    from frontend.app import MedSafeApp

    # Set default CustomTkinter global appearance
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    # Start the desktop window loop
    app = MedSafeApp()
    app.mainloop()
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """Main routing function for both GUI and CLI invocations."""
    if argv is None:
        argv = sys.argv[1:]

    args = parse_arguments(argv)

    if args.help:
        print(f"{APP_FULL_TITLE} (v{APP_VERSION})")
        print("\nUsage:")
        print("  MedSafe                       Launch graphical desktop application")
        print("  MedSafe --check-notifications  Run scheduled background expiry checks")
        print("  MedSafe --migrate-db <path>   Migrate existing SQLite database to user profile")
        print("  MedSafe --version             Show version information")
        print("  MedSafe --help                Show this help message")
        return 0

    if args.version:
        print(f"{APP_NAME} {APP_VERSION}")
        return 0

    if args.migrate_db:
        success, msg = migrate_database(args.migrate_db)
        print(f"[{'SUCCESS' if success else 'ERROR'}] {msg}")
        return 0 if success else 1

    if args.check_notifications:
        return run_headless_notification_check()

    return run_gui()


if __name__ == "__main__":
    sys.exit(main())
