"""
logger.py
---------
Centralized logging configuration for all modules.
"""

import logging
import sys

def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger instance for the given module name.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
