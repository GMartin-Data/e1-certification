"""
Logging configuration for e1-certification project.
Provides both console and JSON logging for CloudWatch compatibility.
"""

import logging
import sys
from pathlib import Path

# Try to import rich for better console output
try:
    from rich.logging import RichHandler

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def setup_logging(
    name: str = "e1_certification",
    level: str = "INFO",
    log_file: Path | None = None,
    use_json: bool = False,
) -> logging.Logger:
    """
    Configure logging for the application.

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for file logging
        use_json: If True, use JSON format (for CloudWatch)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler
    if use_json or not RICH_AVAILABLE:
        console_handler = logging.StreamHandler(sys.stdout)
        formatter = (
            logging.Formatter(
                '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
                '"logger": "%(name)s", "message": "%(message)s"}'
            )
            if use_json
            else logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        console_handler.setFormatter(formatter)
    else:
        # Rich handler for local development
        console_handler = RichHandler(show_time=True, show_path=False, markup=True)

    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"logger": "%(name)s", "message": "%(message)s"}'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


# Create a default logger instance
logger = setup_logging()
