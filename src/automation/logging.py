import logging
import os

# Log file directory
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "prefect.log")

# Ensure the logs directory exists
os.makedirs(LOG_DIR, exist_ok=True)


def get_prefect_logger() -> logging.Logger:
    """
    Creates and configures a logger for Prefect flows and deployments.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger("prefect")  # Prefect-specific logger
    logger.setLevel(logging.INFO)  # Default logging level

    # Formatter for logs
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # Console handler (logs to stdout)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (logs to a file)
    file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# Create logger instance
logger = get_prefect_logger()

# Test log
logger.info("Prefect logger initialized successfully.")
