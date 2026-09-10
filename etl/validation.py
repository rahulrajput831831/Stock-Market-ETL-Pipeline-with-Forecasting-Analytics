"""
Validation step: run BEFORE transformation, on raw yfinance column names
(Date, Open, High, Low, Close, Volume) -- so this must stay in sync with
whatever extract.py produces.
"""

import pandas as pd

from etl.logger import logger

REQUIRED_COLUMNS = ["Date", "Open", "High", "Low", "Close", "Volume"]
PRICE_COLUMNS = ["Open", "High", "Low", "Close"]


class ValidationError(Exception):
    """Raised when the dataset fails a data-quality check."""


def validate_data(df: pd.DataFrame) -> bool:
    """Run a small set of data-quality checks. Raises ValidationError on failure."""

    if df.empty:
        raise ValidationError("Dataset is empty")

    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValidationError(f"Missing required columns: {missing_cols}")

    for col in PRICE_COLUMNS:
        if (df[col] <= 0).any():
            raise ValidationError(f"Invalid (non-positive) values found in '{col}'")

    null_counts = df[REQUIRED_COLUMNS].isnull().sum()
    if null_counts.sum() > 0:
        logger.warning(f"Missing values detected before transform:\n{null_counts[null_counts > 0]}")

    duplicate_dates = df["Date"].duplicated().sum()
    if duplicate_dates > 0:
        logger.warning(f"{duplicate_dates} duplicate date rows found -- will be de-duplicated in transform")

    logger.info(f"Validation passed for {len(df)} records")
    return True
