"""Export saved Reddit prediction candidates to a CSV file."""

import sqlite3
from pathlib import Path

import pandas as pd

from database import DATABASE_PATH


EXPORT_PATH = Path("predictions_export.csv")


def export_predictions_to_csv():
    """Read all rows from SQLite and write them to predictions_export.csv."""
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            "predictions.db does not exist yet. Run scanner.py before exporting."
        )

    with sqlite3.connect(DATABASE_PATH) as connection:
        dataframe = pd.read_sql_query("SELECT * FROM predictions ORDER BY id", connection)

    dataframe.to_csv(EXPORT_PATH, index=False)
    print(f"Exported {len(dataframe)} rows to {EXPORT_PATH}.")


if __name__ == "__main__":
    export_predictions_to_csv()
