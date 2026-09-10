"""
Central configuration for the Stock ETL Pipeline.

All values are read from environment variables (loaded from a local .env
file via python-dotenv). Nothing sensitive is hardcoded here -- copy
.env.example to .env and fill in real values before running the pipeline.
"""

import os

from dotenv import load_dotenv

load_dotenv()


def _get_int(name: str, default: int) -> int:
    """Read an int env var, falling back to a default if missing/invalid."""
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


# --- Database ---------------------------------------------------------
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": _get_int("DB_PORT", 3306),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "stock_pipeline"),
}

# --- ETL ----------------------------------------------------------------
TICKER = os.getenv("TICKER", "AAPL")
LOOKBACK_DAYS = _get_int("LOOKBACK_DAYS", 365)

# --- Forecasting ----------------------------------------------------------
FORECAST_HORIZON_DAYS = _get_int("FORECAST_HORIZON_DAYS", 7)
RANDOM_FOREST_TEST_SIZE = float(os.getenv("RANDOM_FOREST_TEST_SIZE", "0.2"))
RANDOM_STATE = _get_int("RANDOM_STATE", 42)

# --- Retry behaviour (used by extract/load) -------------------------------
MAX_RETRIES = _get_int("MAX_RETRIES", 3)
RETRY_DELAY_SECONDS = _get_int("RETRY_DELAY_SECONDS", 5)
