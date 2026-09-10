# Stock Market ETL + ML Forecasting Pipeline

An end-to-end data engineering project: extracts daily stock price data from Yahoo Finance, validates and cleans it, loads it into MySQL, engineers features, trains a Random Forest for next-day price prediction, runs an ARIMA model for multi-day forecasting, and stores everything for a Power BI dashboard to read.

## 1. Project Overview

This project simulates a realistic (student/internship-scale) production data pipeline for stock market data. It's built to demonstrate core data engineering and ML engineering skills: reliable extraction, data validation, MySQL schema design, feature engineering, model evaluation, and orchestration — without over-engineering with tools that wouldn't be justified at this scale.

## 2. Problem Statement

Manually downloading, cleaning, and analyzing stock price data every day doesn't scale, and ad-hoc scripts don't produce trustworthy, repeatable predictions. This project automates the full path from raw market data to a stored, evaluated forecast that a dashboard can read at any time without re-running any code.

## 3. Architecture

```
Yahoo Finance
     │
     ▼
 Extraction  (etl/extract.py)      -- configurable ticker & date range, retries on failure
     │
     ▼
 Validation  (etl/validation.py)   -- schema, missing values, non-positive prices
     │
     ▼
Transformation (etl/transform.py)  -- dedup, missing-value fill, correct dtypes
     │
     ▼
   MySQL Load (etl/load.py)        -- UPSERT into stock_prices (safe to re-run)
     │
     ▼
Feature Engineering (forecasting/feature_engineering.py) -- MAs, volatility, lags
     │
     ├──────────────────┐
     ▼                  ▼
Random Forest      ARIMA Forecast
(next-day price)   (N-day-ahead trend)
     │                  │
     ▼                  ▼
stock_predictions   stock_forecast
     │                  │
     └────────┬─────────┘
              ▼
        Power BI Dashboard
```

Everything is triggered from a single entry point, `run_pipeline.py`.

## 4. Features

- Configurable ticker and lookback window (no hardcoded stock symbol)
- Retry logic on extraction and database load
- Data validation before anything touches the database
- UPSERT-based loading — safe to re-run over overlapping date ranges
- Feature engineering (3/7-day moving averages, rolling volatility, lag features)
- Two models with distinct, documented purposes (see §9)
- Time-aware train/test splitting — no data leakage
- MAE / RMSE / R² evaluation, stored alongside predictions
- Centralized logging (file + console)
- Pipeline run metadata table (for a dashboard "last run" / freshness indicator)
- `.env`-based configuration — no secrets in source
- Docker Compose setup (MySQL + app, one command)
- Unit tests for the pure-logic parts of the pipeline

## 5. Technologies

Python, pandas, yfinance, scikit-learn, statsmodels (ARIMA), MySQL, SQLAlchemy, Power BI, Docker, pytest.

## 6. Project Structure

```
STOCK-ETL-PIPELINE/
├── config/              # env-driven configuration
├── etl/                 # extract, validate, transform, load, orchestration, logging
├── forecasting/         # feature engineering, RF training, ARIMA forecasting, metrics
├── database/            # schema.sql, queries.sql, connection helper
├── dashboard/           # Power BI file
├── notebooks/           # exploratory analysis (not part of the automated pipeline)
├── data/                # sample raw + processed CSVs
├── logs/                # runtime logs (gitignored)
├── tests/               # unit tests
├── run_pipeline.py      # single entry point
├── .env.example
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## 7. ETL Workflow

1. **Extract** — download OHLCV data for the configured ticker/date range from Yahoo Finance, with retries on transient failures. Raw output is saved to `data/raw/` for traceability.
2. **Validate** — check required columns exist, no non-positive prices, flag missing values / duplicate dates before they reach transformation.
3. **Transform** — normalize column names, remove duplicate dates, forward/back-fill any missing values, enforce correct dtypes. Cleaned output saved to `data/processed/`.
4. **Load** — UPSERT into `stock_prices` keyed on `(ticker, date)`, so re-running the pipeline over an overlapping window updates existing rows instead of erroring or duplicating.

## 8. Database Design

Five tables, each earning its place (see `database/schema.sql`):

| Table | Purpose | Key constraints |
|---|---|---|
| `stock_prices` | Historical OHLCV | `UNIQUE(ticker, date)` |
| `stock_features` | Engineered features | `UNIQUE(ticker, date)` |
| `stock_predictions` | RF test-set predictions + metrics | `UNIQUE(ticker, date, model_name)` |
| `stock_forecast` | ARIMA future forecast | `UNIQUE(ticker, date, model_name)` |
| `pipeline_runs` | Run metadata (status, timestamps, row counts) | indexed on `started_at` |

No feature-store abstraction, no generic "events" table — just what the pipeline and dashboard actually query.

## 9. ML / Forecasting Approach

Two models, each answering a different question:

- **Random Forest** (`forecasting/train.py`) — supervised, feature-based prediction of the *next day's* close price, using lag values, moving averages, and rolling volatility. Uses a **time-aware split** (`shuffle=False`) so the test set is strictly the most recent rows, never randomly interleaved with training data.
- **ARIMA** (`forecasting/forecast.py`) — genuine multi-step **time-series extrapolation** of price N days into the future, independent of engineered features. Backtested on a held-out tail of history before producing the final forward forecast, so there's an honest error estimate rather than a blind forecast.

Both are legitimate and complementary — Random Forest for "what's tomorrow likely to look like given today's pattern," ARIMA for "where is the trend headed over the next week."

## 10. Evaluation Metrics

Both models are scored with MAE, RMSE, and R² (`forecasting/evaluate.py`), computed on held-out data and stored in `stock_predictions` so the dashboard can show model accuracy over time, not just point predictions.

## 11. Dashboard

The Power BI dashboard (`dashboard/POWERBI.pbix`) reads directly from MySQL. Recommended visuals:
- Price trend + OHLC (from `stock_prices`)
- Moving averages / volatility overlay (from `stock_features`)
- Actual vs. predicted price + accuracy metrics (from `stock_predictions`)
- Forward forecast (from `stock_forecast`)
- Last pipeline run status / data freshness (from `pipeline_runs`)

The dashboard never triggers training — it only reads whatever the last scheduled pipeline run produced.

## 12. Installation

```bash
git clone <your-repo-url>
cd STOCK-ETL-PIPELINE
pip install -r requirements.txt
```

## 13. Environment Configuration

```bash
cp .env.example .env
# then fill in DB_HOST, DB_USER, DB_PASSWORD, etc.
```

## 14. How to Run Locally

```bash
mysql -u root -p < database/schema.sql
python run_pipeline.py
```

## 15. How to Run the Pipeline

```bash
python run_pipeline.py                                  # default ticker/lookback from .env
python run_pipeline.py --ticker MSFT --lookback-days 730
python run_pipeline.py --skip-forecasting                # ETL only
```

## 16. Docker Instructions

```bash
docker compose up
```

This starts MySQL (auto-provisioned from `database/schema.sql` on first boot) and runs the pipeline once. Re-run with `docker compose run app` for subsequent runs.

## 17. Deployment Architecture

- **Database**: any managed MySQL (RDS, Cloud SQL, PlanetScale, etc.) — just point `.env` at it.
- **Scheduling**: a daily cron job (`0 18 * * 1-5 docker compose run app`) is the simplest reliable option at this scale — no Airflow needed for a single daily job with no cross-task dependencies.
- **Dashboard**: Power BI connects directly to the MySQL instance; no API layer needed since Power BI can query MySQL natively.

## 18. Example Output

After a successful run, `logs/pipeline.log` shows each stage completing with record counts, and `stock_predictions` / `stock_forecast` contain the latest model output — e.g. Random Forest MAE/RMSE/R² for the test window, and a 7-business-day ARIMA forecast beyond the last known trading day.

## 19. Future Improvements

- Multi-ticker support in a single run (currently one ticker per run, configurable per invocation)
- Model versioning / experiment tracking if the project grows beyond two models
- Alerting on pipeline failure (e.g. a Slack/email webhook) instead of log-only failure visibility

## 20. Limitations

- ARIMA order `(5,1,0)` is fixed, not auto-tuned per ticker — fine for a portfolio project, but a production system would re-tune periodically.
- No intraday data — daily granularity only.
- Random Forest treats the problem as single-step prediction; it doesn't produce a multi-day-ahead forecast (that's what ARIMA is for).
