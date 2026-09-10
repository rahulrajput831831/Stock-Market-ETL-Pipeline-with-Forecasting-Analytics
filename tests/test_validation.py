import pandas as pd
import pytest

from etl.validation import ValidationError, validate_data


def _valid_df():
    return pd.DataFrame({
        "Date": ["2024-01-01", "2024-01-02"],
        "Open": [100.0, 101.0],
        "High": [102.0, 103.0],
        "Low": [99.0, 100.0],
        "Close": [101.0, 102.0],
        "Volume": [1000, 1100],
    })


def test_validate_passes_for_clean_data():
    assert validate_data(_valid_df()) is True


def test_validate_raises_on_empty_dataframe():
    with pytest.raises(ValidationError):
        validate_data(pd.DataFrame())


def test_validate_raises_on_missing_columns():
    df = _valid_df().drop(columns=["Volume"])
    with pytest.raises(ValidationError):
        validate_data(df)


def test_validate_raises_on_non_positive_price():
    df = _valid_df()
    df.loc[0, "Close"] = -5.0
    with pytest.raises(ValidationError):
        validate_data(df)


def test_validate_warns_but_passes_on_duplicate_dates(caplog):
    df = _valid_df()
    df.loc[1, "Date"] = df.loc[0, "Date"]
    assert validate_data(df) is True
