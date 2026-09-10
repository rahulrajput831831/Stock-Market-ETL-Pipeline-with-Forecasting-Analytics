"""
Shared evaluation metrics for both the Random Forest and ARIMA models.

Kept as one small module so both models are scored the same way and the
metrics only need to be defined once. Previously each model script
computed (or skipped) metrics independently.
"""

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def regression_metrics(y_true, y_pred) -> dict:
    """Return MAE, RMSE and R^2 for a set of predictions. R^2 is None for n<2."""
    mae = mean_absolute_error(y_true, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = r2_score(y_true, y_pred) if len(y_true) >= 2 else None

    return {"mae": mae, "rmse": rmse, "r2": r2}
