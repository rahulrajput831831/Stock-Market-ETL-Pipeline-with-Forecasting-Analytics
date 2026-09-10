-- Reference queries -- useful for Power BI, ad-hoc analysis, or debugging.
-- These are examples to copy from, not executed automatically by the pipeline.

-- Latest pipeline run status (for a dashboard "data freshness" card)
SELECT ticker, status, started_at, finished_at, records_loaded, error_message
FROM pipeline_runs
ORDER BY started_at DESC
LIMIT 1;

-- Historical price trend for a ticker
SELECT `date`, open, high, low, close, volume
FROM stock_prices
WHERE ticker = 'AAPL'
ORDER BY `date`;

-- Historical price with 3/7-day moving averages, for a trend chart
SELECT p.`date`, p.close, f.ma3, f.ma7, f.volatility
FROM stock_prices p
LEFT JOIN stock_features f
    ON p.ticker = f.ticker AND p.`date` = f.`date`
WHERE p.ticker = 'AAPL'
ORDER BY p.`date`;

-- Actual vs. Random Forest predicted price (model accuracy view)
SELECT `date`, actual_price, predicted_price, mae, rmse, r2_score
FROM stock_predictions
WHERE ticker = 'AAPL' AND model_name = 'random_forest'
ORDER BY `date`;

-- ARIMA future forecast (beyond the last known trading day)
SELECT `date`, predicted_price
FROM stock_forecast
WHERE ticker = 'AAPL' AND model_name = 'arima'
ORDER BY `date`;
