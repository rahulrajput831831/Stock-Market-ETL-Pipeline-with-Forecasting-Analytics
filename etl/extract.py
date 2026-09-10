"""
Extraction step: pull historical OHLCV data from Yahoo Finance.

The ticker and lookback window are configurable (via .env / config.py)
instead of hardcoded, so the same pipeline can be pointed at a different
stock or date range without editing code.
"""

import os
import time
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from config.config import LOOKBACK_DAYS, MAX_RETRIES, RETRY_DELAY_SECONDS, TICKER
from etl.logger import logger


class ExtractionError(Exception):
    """Raised when data cannot be extracted after all retries are exhausted."""


def extract_data(ticker: str = TICKER, lookback_days: int = LOOKBACK_DAYS) -> pd.DataFrame:
    """
    Download daily OHLCV data for `ticker` over the trailing `lookback_days`.

    Retries transient network/API failures up to MAX_RETRIES times before
    raising ExtractionError. Saves a copy to data/raw/ for traceability.
    """
    end_date = datetime.today()
    start_date = end_date - timedelta(days=lookback_days)

    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Extracting {ticker} data (attempt {attempt}/{MAX_RETRIES})")
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)

            if df.empty:
                raise ExtractionError(f"No data returned for ticker '{ticker}'")

            df.reset_index(inplace=True)

            # yfinance can return MultiIndex columns like ('Close', 'AAPL');
            # flatten to plain column names.
            df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
            df["ticker"] = ticker

            _save_raw(df, ticker)

            logger.info(f"Extraction successful: {len(df)} records for {ticker}")
            return df

        except Exception as exc:  # network errors, empty results, etc.
            last_error = exc
            logger.warning(f"Extraction attempt {attempt} failed: {exc}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)

    logger.error(f"Extraction failed after {MAX_RETRIES} attempts: {last_error}")
    raise ExtractionError(f"Could not extract data for '{ticker}'") from last_error


def _save_raw(df: pd.DataFrame, ticker: str) -> None:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_dir = os.path.join(base_dir, "data", "raw")
    os.makedirs(raw_dir, exist_ok=True)

    raw_path = os.path.join(raw_dir, "stock_raw.csv")
    df.to_csv(raw_path, index=False)
    logger.info(f"Raw data saved: {raw_path}")


if __name__ == "__main__":
    extract_data()
