"""
Central logger for the whole pipeline (ETL + forecasting).

Every module imports `logger` from here instead of configuring its own
logging or falling back to print(). Logs go to both logs/pipeline.log
and the console, so `python run_pipeline.py` is readable interactively
while still leaving a durable audit trail on disk.
"""

import logging
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "pipeline.log")

logger = logging.getLogger("stock_pipeline")
logger.setLevel(logging.INFO)

if not logger.handlers:  # avoid duplicate handlers on repeated imports
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
