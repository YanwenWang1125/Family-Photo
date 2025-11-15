"""Structured logging configuration with correlation IDs."""

import logging
import sys
from typing import Optional

from app.core.config import settings

# Configure root logger
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)
