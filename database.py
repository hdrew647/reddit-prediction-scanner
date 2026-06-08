"""Database helpers for reddit-prediction-scanner.

This file owns the SQLite connection and table creation logic.
Keeping database code here makes scanner.py easier for beginners to read.
"""

import sqlite3
from pathlib import Path


DATABASE_PATH = Path("predictions.db")


CREATE_PREDICTIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_platform TEXT NOT NULL,
    subreddit TEXT,
    author TEXT,
    post_or_comment_id TEXT NOT NULL UNIQUE,
    prediction_text TEXT,
    full_text TEXT,
    asset TEXT,
    target_value TEXT,
    deadline TEXT,
    confidence TEXT,
    created_utc REAL,
    source_url TEXT,
    status TEXT,
    notes TEXT
);
"""


INSERT_PREDICTION_SQL = """
INSERT OR IGNORE INTO predictions (
    source_platform,
    subreddit,
    author,
    post_or_comment_id,
    prediction_text,
    full_text,
    asset,
    target_value,
    deadline,
    confidence,
    created_utc,
    source_url,
    status,
    notes
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""


def get_connection(database_path=DATABASE_PATH):
    """Create a SQLite connection.

    SQLite stores the whole database in one local file. If predictions.db does
    not exist yet, SQLite creates it automatically when we connect.
    """
    return sqlite3.connect(database_path)


def initialize_database(database_path=DATABASE_PATH):
    """Create the predictions table if it does not already exist."""
    with get_connection(database_path) as connection:
        connection.execute(CREATE_PREDICTIONS_TABLE_SQL)
        connection.commit()


def save_prediction(prediction, database_path=DATABASE_PATH):
    """Save one candidate prediction.

    The post_or_comment_id column is UNIQUE, and the INSERT OR IGNORE statement
    keeps duplicate Reddit posts/comments from being inserted twice.
    """
    values = (
        prediction.get("source_platform"),
        prediction.get("subreddit"),
        prediction.get("author"),
        prediction.get("post_or_comment_id"),
        prediction.get("prediction_text"),
        prediction.get("full_text"),
        prediction.get("asset"),
        prediction.get("target_value"),
        prediction.get("deadline"),
        prediction.get("confidence"),
        prediction.get("created_utc"),
        prediction.get("source_url"),
        prediction.get("status"),
        prediction.get("notes"),
    )

    with get_connection(database_path) as connection:
        cursor = connection.execute(INSERT_PREDICTION_SQL, values)
        connection.commit()
        return cursor.rowcount
