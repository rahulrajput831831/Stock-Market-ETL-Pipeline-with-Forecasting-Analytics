"""
Load step: write cleaned data into MySQL.

Uses an UPSERT (INSERT ... ON DUPLICATE KEY UPDATE) against the
(ticker, date) unique key in stock_prices, rather than a plain INSERT.
This makes re-running the pipeline over an overlapping date range safe --
existing rows are updated in place instead of erroring or duplicating.
"""

import time

import pandas as pd

from config.config import MAX_RETRIES, RETRY_DELAY_SECONDS
from database.connection import get_connection
from etl.logger import logger

UPSERT_QUERY = """
INSERT INTO stock_prices (ticker, `date`, open, high, low, close, volume)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    open = VALUES(open),
    high = VALUES(high),
    low = VALUES(low),
    close = VALUES(close),
    volume = VALUES(volume)
"""


class LoadError(Exception):
    """Raised when data cannot be loaded into MySQL after all retries."""


def load_data(df: pd.DataFrame) -> int:
    """Upsert all rows in `df` into stock_prices. Returns the row count written."""

    if df.empty:
        logger.info("No data to load")
        return 0

    values = list(
        df[["ticker", "date", "open", "high", "low", "close", "volume"]]
        .itertuples(index=False, name=None)
    )

    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        connection = None
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.executemany(UPSERT_QUERY, values)
            connection.commit()
            cursor.close()

            logger.info(f"{len(values)} rows upserted into stock_prices")
            return len(values)

        except Exception as exc:
            last_error = exc
            logger.warning(f"Load attempt {attempt} failed: {exc}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)
        finally:
            if connection is not None:
                connection.close()

    logger.error(f"Load failed after {MAX_RETRIES} attempts: {last_error}")
    raise LoadError("Could not load data into MySQL") from last_error
