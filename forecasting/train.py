"""
Random Forest: supervised next-day close-price prediction using
engineered features (lags, moving averages, volatility).

This answers "given today's pattern, what's tomorrow's close likely to
be?" -- distinct from ARIMA's pure time-series extrapolation in forecast.py.

Uses a time-aware (non-shuffled) train/test split to avoid leaking future
information into training, matching how the model would actually be used.
"""

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

from config.config import RANDOM_FOREST_TEST_SIZE, RANDOM_STATE, TICKER
from database.connection import get_connection, get_engine
from etl.logger import logger
from forecasting.evaluate import regression_metrics

FEATURE_COLUMNS = ["lag1", "lag2", "ma3", "ma7", "volatility"]

UPSERT_QUERY = """
INSERT INTO stock_predictions
    (ticker, `date`, actual_price, predicted_price, model_name, mae, rmse, r2_score)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    actual_price = VALUES(actual_price), predicted_price = VALUES(predicted_price),
    mae = VALUES(mae), rmse = VALUES(rmse), r2_score = VALUES(r2_score)
"""


def train_and_predict(ticker: str = TICKER) -> dict | None:
    """Train a Random Forest on engineered features and store test-set predictions."""

    engine = get_engine()
    df = pd.read_sql(
        "SELECT * FROM stock_features WHERE ticker = %(ticker)s ORDER BY `date`",
        engine,
        params={"ticker": ticker},
    )

    if len(df) < 20:
        logger.warning(f"Not enough feature rows ({len(df)}) to train a model for {ticker}")
        return None

    X = df[FEATURE_COLUMNS]
    y = df["close"]

    # shuffle=False preserves chronological order -- the test set is strictly
    # the most recent rows, never randomly interleaved with training rows.
    X_train, X_test, y_train, y_test, dates_train, dates_test = train_test_split(
        X, y, df["date"], test_size=RANDOM_FOREST_TEST_SIZE, shuffle=False
    )

    model = RandomForestRegressor(random_state=RANDOM_STATE)
    model.fit(X_train, y_train)
    logger.info(f"Random Forest trained on {len(X_train)} rows")

    predictions = model.predict(X_test)
    metrics = regression_metrics(y_test, predictions)
    logger.info(
        f"Random Forest evaluation -- MAE: {metrics['mae']:.4f}, "
        f"RMSE: {metrics['rmse']:.4f}, R2: {metrics['r2']:.4f}"
    )

    pred_df = pd.DataFrame({
        "ticker": ticker,
        "date": dates_test.values,
        "actual_price": y_test.values,
        "predicted_price": predictions,
        "model_name": "random_forest",
        "mae": metrics["mae"],
        "rmse": metrics["rmse"],
        "r2_score": metrics["r2"],
    })
    _upsert_predictions(pred_df)

    return metrics


def _upsert_predictions(df: pd.DataFrame) -> None:
    values = list(
        df[["ticker", "date", "actual_price", "predicted_price", "model_name", "mae", "rmse", "r2_score"]]
        .itertuples(index=False, name=None)
    )
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany(UPSERT_QUERY, values)
    conn.commit()
    cursor.close()
    conn.close()
    logger.info(f"{len(values)} prediction rows upserted")


if __name__ == "__main__":
    train_and_predict()
