import logging
import sys


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Configure project-wide logging.
    
    Args:
        level: Logging level (default: INFO)
    
    Returns:
        The root logger for the project
    """
    # Create a custom logger
    logger = logging.getLogger("substack_downloader")
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times
    if not logger.handlers:
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        # Create formatter
        formatter = logging.Formatter("[%(levelname)s] %(message)s")
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Optional module name for the logger
    
    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"substack_downloader.{name}")
    return logging.getLogger("substack_downloader")

