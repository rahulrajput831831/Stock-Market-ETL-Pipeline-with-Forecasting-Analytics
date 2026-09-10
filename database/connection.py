"""
Single source of truth for MySQL connections.

Previously, connection logic (and hardcoded credentials) was duplicated
across eda.py, evaluate.py, feature.py, forecast.py and train_model.py.
Everything now goes through get_connection() (raw cursor access, used for
UPSERTs) or get_engine() (SQLAlchemy engine, used for pandas read_sql/to_sql).
"""

import mysql.connector
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from config.config import DB_CONFIG


def get_connection() -> mysql.connector.MySQLConnection:
    """Return a raw mysql-connector connection (for cursor-based operations)."""
    return mysql.connector.connect(**DB_CONFIG)


def get_engine() -> Engine:
    """Return a SQLAlchemy engine (for pandas .read_sql / .to_sql)."""
    url = (
        f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )
    return create_engine(url)
