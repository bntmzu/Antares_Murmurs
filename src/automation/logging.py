import logging
from prefect.logging import get_run_logger

def get_prefect_logger():
    logger = get_run_logger()
    return logger
