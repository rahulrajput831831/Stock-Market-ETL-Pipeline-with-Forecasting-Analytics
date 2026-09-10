-- Stock ETL Pipeline -- database schema
-- Run once to provision the database, e.g.:
--   mysql -u root -p < database/schema.sql



-- ---------------------------------------------------------------------
-- Historical OHLCV data (one row per ticker per trading day)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS stock_prices (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    ticker      VARCHAR(10)     NOT NULL,
    `date`      DATE            NOT NULL,
    open        DECIMAL(12, 4)  NOT NULL,
    high        DECIMAL(12, 4)  NOT NULL,
    low         DECIMAL(12, 4)  NOT NULL,
    close       DECIMAL(12, 4)  NOT NULL,
    volume      BIGINT          NOT NULL,
    created_at  TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP       DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_ticker_date (ticker, `date`),
    INDEX idx_date (`date`)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Engineered features (moving averages, volatility, lags)
-- Rebuilt from stock_prices on each pipeline run.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS stock_features (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    ticker      VARCHAR(10)     NOT NULL,
    `date`      DATE            NOT NULL,
    close       DECIMAL(12, 4)  NOT NULL,
    ma3         DECIMAL(12, 4),
    ma7         DECIMAL(12, 4),
    volatility  DECIMAL(12, 6),
    lag1        DECIMAL(12, 4),
    lag2        DECIMAL(12, 4),
    created_at  TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_ticker_date (ticker, `date`),
    INDEX idx_date (`date`)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Random Forest predictions on the held-out test split
-- (supervised, feature-based, next-day prediction)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS stock_predictions (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    ticker          VARCHAR(10)     NOT NULL,
    `date`          DATE            NOT NULL,
    actual_price    DECIMAL(12, 4)  NOT NULL,
    predicted_price DECIMAL(12, 4)  NOT NULL,
    model_name      VARCHAR(50)     NOT NULL DEFAULT 'random_forest',
    mae             DECIMAL(12, 6),
    rmse            DECIMAL(12, 6),
    r2_score        DECIMAL(12, 6),
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_ticker_date_model (ticker, `date`, model_name)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- ARIMA future forecast (pure time-series extrapolation beyond history)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS stock_forecast (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    ticker          VARCHAR(10)     NOT NULL,
    `date`          DATE            NOT NULL,
    predicted_price DECIMAL(12, 4)  NOT NULL,
    model_name      VARCHAR(50)     NOT NULL DEFAULT 'arima',
    generated_at    TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_ticker_date_model (ticker, `date`, model_name)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Pipeline run metadata -- lets the dashboard show "data freshness" /
-- last successful run without scraping log files.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id                  BIGINT AUTO_INCREMENT PRIMARY KEY,
    started_at          TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    finished_at         TIMESTAMP       NULL,
    status              ENUM('running', 'success', 'failed') NOT NULL DEFAULT 'running',
    ticker              VARCHAR(10)     NOT NULL,
    records_extracted   INT             DEFAULT 0,
    records_loaded      INT             DEFAULT 0,
    error_message       TEXT,
    INDEX idx_started_at (started_at)
) ENGINE=InnoDB;
