from forecasting.evaluate import regression_metrics


def test_perfect_predictions_give_zero_error():
    metrics = regression_metrics([1, 2, 3], [1, 2, 3])
    assert metrics["mae"] == 0
    assert metrics["rmse"] == 0
    assert metrics["r2"] == 1.0


def test_metrics_returns_expected_keys():
    metrics = regression_metrics([1, 2, 3], [1.1, 2.2, 2.9])
    assert set(metrics.keys()) == {"mae", "rmse", "r2"}


def test_metrics_r2_none_for_single_point():
    metrics = regression_metrics([5], [4])
    assert metrics["r2"] is None
    assert metrics["mae"] == 1
