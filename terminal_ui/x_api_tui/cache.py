"""SQLite cache for tweets.

Originally written by Claude Sonnet 4.6 on 2026/03/01
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

_DEFAULT_DB: Path = Path.home() / ".local" / "share" / "x-tweet-ui" / "cache.db"

_CREATE_TWEET_CACHE = """
CREATE TABLE IF NOT EXISTS tweet_cache (
    id         TEXT PRIMARY KEY,
    username   TEXT NOT NULL,
    created_at TEXT NOT NULL,
    text       TEXT NOT NULL,
    author_id  TEXT NOT NULL,
    raw_json   TEXT NOT NULL
)
"""

_CREATE_FETCH_LOG = """
CREATE TABLE IF NOT EXISTS fetch_log (
    username   TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date   TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (username, start_date, end_date)
)
"""


def open_db(path: Path | str = _DEFAULT_DB) -> sqlite3.Connection:
    """Open (and initialise) the SQLite database.

    @param path: Path to the .db file, or ":memory:" for an in-memory database.
    @return: Open sqlite3 connection with WAL mode and row_factory set.
    """
    path_str = str(path)
    if path_str != ":memory:":
        db_path = Path(path_str)
        db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path_str)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(_CREATE_TWEET_CACHE)
    conn.execute(_CREATE_FETCH_LOG)
    conn.commit()
    return conn


def _date_key(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")


def is_cached(
    conn: sqlite3.Connection,
    username: str,
    start: datetime,
    end: datetime,
) -> bool:
    """Return True if we have a fetch_log entry for this (username, range) pair."""
    row = conn.execute(
        "SELECT 1 FROM fetch_log WHERE username=? AND start_date=? AND end_date=?",
        (username.lower(), _date_key(start), _date_key(end)),
    ).fetchone()
    return row is not None


def store_tweets(
    conn: sqlite3.Connection,
    username: str,
    start: datetime,
    end: datetime,
    tweets: list[dict[str, object]],
) -> None:
    """Upsert tweets into tweet_cache and record the fetch in fetch_log.

    @param tweets: Tweet dicts as returned by load_tweets().
    """
    now = datetime.now(timezone.utc).isoformat()
    with conn:
        for tweet in tweets:
            conn.execute(
                "INSERT OR REPLACE INTO tweet_cache"
                " (id, username, created_at, text, author_id, raw_json)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (
                    str(tweet["id"]),
                    username.lower(),
                    str(tweet.get("created_at", "")),
                    str(tweet.get("text", "")),
                    str(tweet.get("author_id", "")),
                    json.dumps(tweet),
                ),
            )
        conn.execute(
            "INSERT OR REPLACE INTO fetch_log (username, start_date, end_date, fetched_at)"
            " VALUES (?, ?, ?, ?)",
            (username.lower(), _date_key(start), _date_key(end), now),
        )


def get_tweets(
    conn: sqlite3.Connection,
    username: str,
    start: datetime,
    end: datetime,
) -> list[dict[str, object]]:
    """Return cached tweets for the given (username, range), newest-first.

    @return: List of tweet dicts reconstructed from raw_json.
    """
    start_key = _date_key(start)
    end_key = _date_key(end)
    rows = conn.execute(
        "SELECT raw_json FROM tweet_cache"
        " WHERE username=? AND created_at >= ? AND created_at <= ?"
        " ORDER BY created_at DESC",
        (username.lower(), start_key, end_key + "T23:59:59Z"),
    ).fetchall()
    return [json.loads(row["raw_json"]) for row in rows]


def evict_tweet(conn: sqlite3.Connection, tweet_id: str) -> None:
    """Remove a single tweet from the cache after deletion."""
    with conn:
        conn.execute("DELETE FROM tweet_cache WHERE id=?", (tweet_id,))


def invalidate_range(
    conn: sqlite3.Connection,
    username: str,
    start: datetime,
    end: datetime,
) -> None:
    """Remove the fetch_log entry, forcing a network refresh next time."""
    with conn:
        conn.execute(
            "DELETE FROM fetch_log WHERE username=? AND start_date=? AND end_date=?",
            (username.lower(), _date_key(start), _date_key(end)),
        )
