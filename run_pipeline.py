"""
Single entry point for the whole project.

    python run_pipeline.py
    python run_pipeline.py --ticker MSFT --lookback-days 730
    python run_pipeline.py --skip-forecasting   # ETL only

Flow: extract -> validate -> transform -> load (MySQL)
      -> feature engineering -> Random Forest train/predict -> ARIMA forecast

Feature engineering / training / forecasting are meant to run on a
schedule (e.g. once a day after new data lands), not on every dashboard
refresh -- the dashboard only ever reads the resulting MySQL tables.
"""

import argparse

from config.config import LOOKBACK_DAYS, TICKER
from etl.logger import logger
from etl.pipeline import run_etl_pipeline
from forecasting.feature_engineering import build_features
from forecasting.forecast import generate_forecast
from forecasting.train import train_and_predict


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Stock ETL + Forecasting pipeline")
    parser.add_argument("--ticker", default=TICKER, help="Stock ticker symbol (default: %(default)s)")
    parser.add_argument(
        "--lookback-days", type=int, default=LOOKBACK_DAYS,
        help="Days of history to extract (default: %(default)s)",
    )
    parser.add_argument("--skip-forecasting", action="store_true", help="Run ETL only, skip the ML stage")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    logger.info(f"##### PIPELINE RUN STARTED (ticker={args.ticker}) #####")

    etl_ok = run_etl_pipeline(ticker=args.ticker, lookback_days=args.lookback_days)
    if not etl_ok:
        logger.error("ETL stage failed -- skipping forecasting stage")
        logger.info("##### PIPELINE RUN FINISHED: FAILED #####")
        raise SystemExit(1)

    if args.skip_forecasting:
        logger.info("##### PIPELINE RUN FINISHED: SUCCESS (ETL only) #####")
        return

    try:
        build_features(ticker=args.ticker)
        train_and_predict(ticker=args.ticker)
        generate_forecast(ticker=args.ticker)
        logger.info("##### PIPELINE RUN FINISHED: SUCCESS #####")
    except Exception as exc:
        # ETL already succeeded and is committed; a forecasting failure
        # shouldn't be reported as a full pipeline failure, just flagged.
        logger.error(f"Forecasting stage failed (ETL data is still valid): {exc}")
        logger.info("##### PIPELINE RUN FINISHED: PARTIAL SUCCESS (ETL only) #####")
        raise SystemExit(2)


if __name__ == "__main__":
    main()
