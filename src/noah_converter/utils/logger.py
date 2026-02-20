"""Logging utilities"""

import sys
from pathlib import Path
from loguru import logger
from typing import Optional


def setup_logger(
    log_file: Optional[str] = None,
    level: str = "INFO",
    console: bool = True,
) -> None:
    """
    Setup logger with file and console output

    Args:
        log_file: Path to log file
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        console: Whether to output to console
    """
    # Remove default logger
    logger.remove()

    # Add console handler
    if console:
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=level,
            colorize=True,
        )

    # Add file handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            log_path,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=level,
            rotation="10 MB",
            retention="1 week",
            compression="zip",
        )

    logger.info(f"Logger initialized with level: {level}")


def get_logger(name: str):
    """Get a named logger instance"""
    return logger.bind(name=name)
