"""Tests for cache.py — uses in-memory SQLite, no mocking needed."""

import sqlite3
from datetime import datetime, timezone

import pytest

from x_api_tui.cache import (
    evict_tweet,
    get_tweets,
    invalidate_range,
    is_cached,
    open_db,
    store_tweets,
)

START = datetime(2024, 1, 1, tzinfo=timezone.utc)
END = datetime(2024, 1, 31, tzinfo=timezone.utc)
TWEET: dict[str, object] = {
    "id": "1",
    "text": "hello",
    "created_at": "2024-01-15T10:00:00Z",
    "author_id": "99",
}


@pytest.fixture
def conn() -> sqlite3.Connection:
    """In-memory DB, fully initialised."""
    return open_db(":memory:")


def test_not_cached_initially(conn: sqlite3.Connection) -> None:
    assert not is_cached(conn, "alice", START, END)


def test_cached_after_store(conn: sqlite3.Connection) -> None:
    store_tweets(conn, "alice", START, END, [TWEET])
    assert is_cached(conn, "alice", START, END)


def test_get_tweets_returns_stored(conn: sqlite3.Connection) -> None:
    store_tweets(conn, "alice", START, END, [TWEET])
    result = get_tweets(conn, "alice", START, END)
    assert len(result) == 1
    assert result[0]["id"] == "1"


def test_evict_removes_tweet(conn: sqlite3.Connection) -> None:
    store_tweets(conn, "alice", START, END, [TWEET])
    evict_tweet(conn, "1")
    assert get_tweets(conn, "alice", START, END) == []


def test_evict_does_not_clear_fetch_log(conn: sqlite3.Connection) -> None:
    store_tweets(conn, "alice", START, END, [TWEET])
    evict_tweet(conn, "1")
    assert is_cached(conn, "alice", START, END)


def test_invalidate_range_clears_fetch_log(conn: sqlite3.Connection) -> None:
    store_tweets(conn, "alice", START, END, [TWEET])
    invalidate_range(conn, "alice", START, END)
    assert not is_cached(conn, "alice", START, END)


def test_store_is_idempotent(conn: sqlite3.Connection) -> None:
    store_tweets(conn, "alice", START, END, [TWEET])
    store_tweets(conn, "alice", START, END, [TWEET])
    assert len(get_tweets(conn, "alice", START, END)) == 1


def test_username_is_case_insensitive(conn: sqlite3.Connection) -> None:
    store_tweets(conn, "Alice", START, END, [TWEET])
    assert is_cached(conn, "alice", START, END)
    assert len(get_tweets(conn, "ALICE", START, END)) == 1
