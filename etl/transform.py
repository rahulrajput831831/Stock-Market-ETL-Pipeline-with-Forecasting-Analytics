"""
Transformation step: normalize column names/types, de-duplicate,
handle missing values, and persist a cleaned copy to data/processed/.
"""

import os

import pandas as pd

from etl.logger import logger


def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Starting transform step")

    df = df.copy()
    df.columns = [col.lower() for col in df.columns]

    df["date"] = pd.to_datetime(df["date"])

    before = len(df)
    df = df.drop_duplicates(subset=["date"], keep="last")
    duplicates_removed = before - len(df)
    if duplicates_removed:
        logger.info(f"Removed {duplicates_removed} duplicate date rows")

    df = df.sort_values("date")

    numeric_cols = ["open", "high", "low", "close", "volume"]
    missing_before = df[numeric_cols].isnull().sum().sum()
    if missing_before:
        # forward-fill then back-fill: reasonable default for short gaps in
        # daily price series without inventing data at the series edges.
        df[numeric_cols] = df[numeric_cols].ffill().bfill()
        logger.info(f"Filled {missing_before} missing values via forward/back-fill")

    df["volume"] = df["volume"].astype("int64")
    for col in ["open", "high", "low", "close"]:
        df[col] = df[col].astype("float64")

    _save_processed(df)

    logger.info(f"Transform completed: {len(df)} records ready to load")
    return df


def _save_processed(df: pd.DataFrame) -> None:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    processed_dir = os.path.join(base_dir, "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)

    processed_path = os.path.join(processed_dir, "stock_clean.csv")
    df.to_csv(processed_path, index=False)
    logger.info(f"Processed data saved: {processed_path}")
