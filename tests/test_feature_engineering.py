import pandas as pd

from forecasting.feature_engineering import compute_features


def _sample_price_series(n=15):
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    closes = [100 + i * 0.5 for i in range(n)]
    return pd.DataFrame({"date": dates, "close": closes})


def test_compute_features_drops_warmup_nans():
    df = compute_features(_sample_price_series())
    assert df.isnull().sum().sum() == 0


def test_compute_features_has_expected_columns():
    df = compute_features(_sample_price_series())
    for col in ["ma3", "ma7", "volatility", "lag1", "lag2"]:
        assert col in df.columns


def test_lag1_matches_previous_close():
    df = compute_features(_sample_price_series())
    # lag1 at row i should equal the raw close one day earlier
    raw = _sample_price_series().set_index("date")["close"]
    for _, row in df.iterrows():
        expected = raw.loc[row["date"] - pd.Timedelta(days=1)]
        assert row["lag1"] == expected


def test_compute_features_shrinks_row_count():
    raw = _sample_price_series()
    result = compute_features(raw)
    assert len(result) < len(raw)
