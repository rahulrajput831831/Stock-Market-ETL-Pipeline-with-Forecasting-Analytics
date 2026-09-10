import pandas as pd

from etl.transform import transform_data


def _sample_raw_df():
    return pd.DataFrame({
        "Date": ["2024-01-02", "2024-01-01", "2024-01-01"],  # unsorted + duplicate
        "Open": [101.0, 100.0, 100.0],
        "High": [102.0, 101.0, 101.0],
        "Low": [99.0, 98.0, 98.0],
        "Close": [100.5, 100.2, 100.2],
        "Volume": [1000, 900, 900],
        "ticker": ["AAPL", "AAPL", "AAPL"],
    })


def test_transform_sorts_by_date():
    result = transform_data(_sample_raw_df())
    assert list(result["date"]) == sorted(result["date"])


def test_transform_removes_duplicates():
    result = transform_data(_sample_raw_df())
    assert result["date"].is_unique


def test_transform_lowercases_columns():
    result = transform_data(_sample_raw_df())
    assert set(["date", "open", "high", "low", "close", "volume"]).issubset(result.columns)


def test_transform_fills_missing_values():
    df = _sample_raw_df()
    df.loc[0, "Close"] = None
    result = transform_data(df)
    assert result["close"].isnull().sum() == 0


def test_transform_correct_dtypes():
    result = transform_data(_sample_raw_df())
    assert result["volume"].dtype == "int64"
    assert result["close"].dtype == "float64"
