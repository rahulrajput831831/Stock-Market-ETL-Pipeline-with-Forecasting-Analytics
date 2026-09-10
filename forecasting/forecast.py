"""
ARIMA: pure time-series extrapolation of closing price, independent of
the engineered features used by the Random Forest model.

This answers "where is the price trending over the next N days?" -- a
genuine multi-step-ahead forecast beyond the end of known history, which
Random Forest (a single-step supervised model) doesn't attempt.

Backtests on a held-out tail of history before producing the final
forward forecast, so the pipeline logs an honest error estimate instead
of forecasting blind.
"""

import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

from config.config import FORECAST_HORIZON_DAYS, TICKER
from database.connection import get_connection, get_engine
from etl.logger import logger
from forecasting.evaluate import regression_metrics

ARIMA_ORDER = (5, 1, 0)

UPSERT_QUERY = """
INSERT INTO stock_forecast (ticker, `date`, predicted_price, model_name)
VALUES (%s, %s, %s, %s)
ON DUPLICATE KEY UPDATE predicted_price = VALUES(predicted_price)
"""


def _load_price_series(ticker: str) -> pd.Series:
    engine = get_engine()
    df = pd.read_sql(
        "SELECT `date`, close FROM stock_prices WHERE ticker = %(ticker)s ORDER BY `date`",
        engine,
        params={"ticker": ticker},
    )
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").asfreq("B").ffill()  # business-day frequency, ARIMA requires regular spacing
    return df["close"]


def backtest(series: pd.Series, horizon: int = FORECAST_HORIZON_DAYS) -> dict | None:
    """Fit on all but the last `horizon` points, forecast them, and score against actuals."""
    if len(series) < horizon * 4:
        logger.warning("Not enough history to backtest ARIMA; skipping evaluation")
        return None

    train, test = series[:-horizon], series[-horizon:]
    model = ARIMA(train, order=ARIMA_ORDER).fit()
    predictions = model.forecast(steps=horizon)

    metrics = regression_metrics(test.values, predictions.values)
    logger.info(
        f"ARIMA backtest ({horizon}-day holdout) -- MAE: {metrics['mae']:.4f}, "
        f"RMSE: {metrics['rmse']:.4f}"
    )
    return metrics


def generate_forecast(ticker: str = TICKER, horizon: int = FORECAST_HORIZON_DAYS) -> pd.DataFrame | None:
    """Backtest, then fit ARIMA on full history and forecast `horizon` business days forward."""

    series = _load_price_series(ticker)
    if len(series) < 30:
        logger.warning(f"Not enough price history ({len(series)}) to forecast for {ticker}")
        return None

    backtest(series, horizon)

    model = ARIMA(series, order=ARIMA_ORDER).fit()
    forecast_values = model.forecast(steps=horizon)

    future_dates = pd.date_range(start=series.index[-1] + pd.Timedelta(days=1), periods=horizon, freq="B")
    forecast_df = pd.DataFrame({
        "ticker": ticker,
        "date": future_dates,
        "predicted_price": forecast_values.values,
        "model_name": "arima",
    })

    _upsert_forecast(forecast_df)
    logger.info(f"ARIMA forecast generated for {horizon} business days ahead")
    return forecast_df


def _upsert_forecast(df: pd.DataFrame) -> None:
    values = list(df[["ticker", "date", "predicted_price", "model_name"]].itertuples(index=False, name=None))
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany(UPSERT_QUERY, values)
    conn.commit()
    cursor.close()
    conn.close()
    logger.info(f"{len(values)} forecast rows upserted")


if __name__ == "__main__":
    generate_forecast()
