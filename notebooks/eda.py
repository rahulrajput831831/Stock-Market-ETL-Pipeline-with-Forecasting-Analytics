"""
Exploratory data analysis -- a dev-only script, not part of the
automated pipeline. Run manually (`python notebooks/eda.py`) after the
pipeline has loaded data, to sanity-check trends and correlations.

Uses the same shared connection helper and .env-based config as the
rest of the project, instead of a separate hardcoded connection.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from database.connection import get_engine

engine = get_engine()
query = "SELECT * FROM stock_prices"

df = pd.read_sql(query, engine)

df["date"] = pd.to_datetime(df["date"])

print(df.describe())

# price trend
plt.figure(figsize=(10,5))
plt.plot(df["date"], df["close"])
plt.title("Stock Closing Price Trend")
plt.show()

# correlation (numeric columns only -- 'ticker' and 'date' aren't correlatable)
sns.heatmap(df.select_dtypes(include="number").corr(), annot=True)
plt.show()