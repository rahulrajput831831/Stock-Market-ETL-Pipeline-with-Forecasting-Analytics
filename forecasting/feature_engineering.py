"""
Feature engineering: moving averages, volatility, and lag features
built from stock_prices, written to stock_features.

Previously a standalone script that connected to the DB itself; now a
callable function invoked by run_pipeline.py.
"""

import pandas as pd

from config.config import TICKER
from database.connection import get_connection, get_engine
from etl.logger import logger

UPSERT_QUERY = """
INSERT INTO stock_features (ticker, `date`, close, ma3, ma7, volatility, lag1, lag2)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    close = VALUES(close), ma3 = VALUES(ma3), ma7 = VALUES(ma7),
    volatility = VALUES(volatility), lag1 = VALUES(lag1), lag2 = VALUES(lag2)
"""


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pure calculation step (no DB access) -- kept separate from build_features()
    so the feature math can be unit tested without a live MySQL connection.

    Expects a DataFrame with 'date' and 'close' columns, sorted by date.
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    df["ma3"] = df["close"].rolling(3).mean()
    df["ma7"] = df["close"].rolling(7).mean()
    df["volatility"] = df["close"].rolling(7).std()
    df["lag1"] = df["close"].shift(1)
    df["lag2"] = df["close"].shift(2)

    return df.dropna().reset_index(drop=True)


def build_features(ticker: str = TICKER) -> pd.DataFrame:
    """Compute engineered features for `ticker` and upsert them into stock_features."""

    engine = get_engine()
    df = pd.read_sql(
        "SELECT `date`, close FROM stock_prices WHERE ticker = %(ticker)s ORDER BY `date`",
        engine,
        params={"ticker": ticker},
    )

    if df.empty:
        logger.warning(f"No price history found for {ticker}; skipping feature engineering")
        return df

    rows_before = len(df)
    df = compute_features(df)
    logger.info(f"Feature engineering: {rows_before} rows -> {len(df)} after dropping warm-up NaNs")

    df["ticker"] = ticker
    _upsert_features(df, ticker)

    return df


def _upsert_features(df: pd.DataFrame, ticker: str) -> None:
    values = list(
        df[["ticker", "date", "close", "ma3", "ma7", "volatility", "lag1", "lag2"]]
        .itertuples(index=False, name=None)
    )
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany(UPSERT_QUERY, values)
    conn.commit()
    cursor.close()
    conn.close()
    logger.info(f"{len(values)} feature rows upserted for {ticker}")


if __name__ == "__main__":
    build_features()
