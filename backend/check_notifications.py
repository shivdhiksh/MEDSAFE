"""Standalone CLI runner for MEDSAFE expiry notifications.

Designed for scheduled execution (such as via Windows Task Scheduler)
or manual verification while the main graphical interface is closed.
Performs an offline expiry check, dispatches eligible toasts,
records alert history, and exits cleanly.
"""

import sys
from frontend.main import run_headless_notification_check


def main() -> int:
    """Run notification check delegating to the unified headless check."""
    return run_headless_notification_check()


if __name__ == "__main__":
    sys.exit(main())
