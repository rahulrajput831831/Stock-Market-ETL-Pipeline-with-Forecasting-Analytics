"""
ETL orchestration: extract -> validate -> transform -> load.

This only covers the ETL stage. Feature engineering / training / forecasting
are separate stages orchestrated by run_pipeline.py at the project root, so
that ETL can be run and tested independently of the ML stage.
"""

from config.config import LOOKBACK_DAYS, TICKER
from database.connection import get_connection
from etl.extract import extract_data
from etl.load import load_data
from etl.logger import logger
from etl.transform import transform_data
from etl.validation import validate_data


def _record_run_start(ticker: str) -> int | None:
    """Insert a 'running' row into pipeline_runs; returns its id (or None if DB unavailable)."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO pipeline_runs (ticker, status) VALUES (%s, 'running')", (ticker,)
        )
        conn.commit()
        run_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return run_id
    except Exception as exc:
        logger.warning(f"Could not record pipeline run start (continuing anyway): {exc}")
        return None


def _record_run_end(run_id: int | None, status: str, extracted: int, loaded: int, error: str = None) -> None:
    if run_id is None:
        return
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE pipeline_runs
            SET status = %s, finished_at = CURRENT_TIMESTAMP,
                records_extracted = %s, records_loaded = %s, error_message = %s
            WHERE id = %s
            """,
            (status, extracted, loaded, error, run_id),
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as exc:
        logger.warning(f"Could not record pipeline run end: {exc}")


def run_etl_pipeline(ticker: str = TICKER, lookback_days: int = LOOKBACK_DAYS) -> bool:
    """Run the full ETL stage. Returns True on success, False on failure."""

    logger.info(f"=== ETL pipeline started (ticker={ticker}) ===")
    run_id = _record_run_start(ticker)
    extracted_count = 0

    try:
        df = extract_data(ticker=ticker, lookback_days=lookback_days)
        extracted_count = len(df)

        validate_data(df)

        df = transform_data(df)

        loaded_count = load_data(df)

        _record_run_end(run_id, "success", extracted_count, loaded_count)
        logger.info("=== ETL pipeline finished successfully ===")
        return True

    except Exception as exc:
        logger.error(f"=== ETL pipeline FAILED: {exc} ===")
        _record_run_end(run_id, "failed", extracted_count, 0, error=str(exc))
        return False


if __name__ == "__main__":
    run_etl_pipeline()
