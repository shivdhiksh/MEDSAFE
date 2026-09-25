"""Logging infrastructure for MEDSAFE.

Provides standardized, privacy-conscious application logging.
Follows MEDSAFE safety guidelines:
- Never logs sensitive personal data or medicine notes.
- Logs technical status, notifications, database integrity, and errors safely.
"""

import logging
from typing import Optional


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """Return a configured logger with standard MEDSAFE formatting.

    Args:
        name: Name of the module requesting the logger (usually __name__).
        level: Optional log level override (defaults to logging.INFO).

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    if level is not None:
        logger.setLevel(level)
    elif logger.level == logging.NOTSET:
        logger.setLevel(logging.INFO)

    return logger
