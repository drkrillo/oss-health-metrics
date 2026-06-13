"""Centralised logging configuration for the oss-health-metrics package."""

from __future__ import annotations

import logging
import sys


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure the root logger with a consistent format.

    Call once at process start.  Every module then does::

        import logging
        logger = logging.getLogger(__name__)

    and inherits this configuration automatically.
    """
    fmt = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
    datefmt = "%H:%M:%S"

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt, datefmt=datefmt))

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)

    # Silence noisy libraries.
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    return root
