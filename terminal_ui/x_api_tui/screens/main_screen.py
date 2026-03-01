"""Main screen: date range, tweet count, tweet list, and bulk delete.

Originally written by Claude Sonnet 4.6 on 2026/03/01
"""

import sqlite3
from datetime import datetime, timezone

from a_gn_x_api_tests.credentials import Credentials
from a_gn_x_api_tests.tweet_loader import count_tweets, delete_tweet, load_tweets
from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label
from textual.worker import Worker, WorkerState

from x_api_tui.cache import (
    evict_tweet,
    get_tweets,
    invalidate_range,
    is_cached,
    store_tweets,
)
from x_api_tui.screens.confirm_screen import ConfirmDeleteScreen
from x_api_tui.widgets.tweet_list import TweetListWidget


def _parse_date(value: str) -> datetime | None:
    """Parse YYYY-MM-DD to UTC-aware datetime, return None if invalid."""
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


class MainScreen(Screen[None]):
    """Main screen after user is confirmed."""

    DEFAULT_CSS = """
    MainScreen {
        layout: horizontal;
    }
    #left-panel {
        width: 2fr;
        border-right: tall $primary;
    }
    #right-panel {
        width: 1fr;
        padding: 1 2;
    }
    #panel-title {
        text-style: bold;
        margin-bottom: 1;
    }
    #count-label {
        margin-bottom: 1;
    }
    #status {
        margin-top: 1;
        height: auto;
    }
    Button {
        width: 100%;
        margin-bottom: 1;
    }
    """

    def __init__(
        self,
        username: str,
        creds: Credentials,
        db: sqlite3.Connection,
    ) -> None:
        super().__init__()
        self._username = username
        self._creds = creds
        self._db = db
        self._selected_ids: frozenset[str] = frozenset()

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(id="left-panel"):
                yield TweetListWidget(id="tweet-list")
            with Vertical(id="right-panel"):
                yield Label(f"@{self._username}", id="panel-title")
                yield Input(placeholder="Start date (YYYY-MM-DD)", id="start-date")
                yield Input(placeholder="End date (YYYY-MM-DD)", id="end-date")
                yield Label("Count: —", id="count-label")
                yield Button("Show Tweets", id="show-btn", disabled=True)
                yield Button("Refresh from API", id="refresh-btn", disabled=True)
                yield Button(
                    "Delete Selected",
                    id="delete-btn",
                    disabled=True,
                    variant="error",
                )
                yield Label("", id="status")

    def _get_dates(self) -> tuple[datetime, datetime] | None:
        """Return (start, end) if both inputs are valid, else None."""
        start = _parse_date(self.query_one("#start-date", Input).value)
        end = _parse_date(self.query_one("#end-date", Input).value)
        if start is None or end is None or start > end:
            return None
        return start, end

    def on_input_changed(self, event: Input.Changed) -> None:
        dates = self._get_dates()
        valid = dates is not None
        self.query_one("#show-btn", Button).disabled = not valid
        self.query_one("#refresh-btn", Button).disabled = not valid
        if valid:
            assert dates is not None
            start, end = dates
            self.query_one("#count-label", Label).update("Count: …")
            self._fetch_count(self._username, start, end)
        else:
            self.query_one("#count-label", Label).update("Count: —")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        dates = self._get_dates()
        if event.button.id == "show-btn" and dates is not None:
            start, end = dates
            self._set_status("Loading tweets…")
            self._load_tweets(self._username, start, end, force_refresh=False)
        elif event.button.id == "refresh-btn" and dates is not None:
            start, end = dates
            self._set_status("Refreshing from API…")
            invalidate_range(self._db, self._username, start, end)
            self._load_tweets(self._username, start, end, force_refresh=True)
        elif event.button.id == "delete-btn" and self._selected_ids:
            count = len(self._selected_ids)
            self.app.push_screen(
                ConfirmDeleteScreen(count),
                callback=self._on_delete_confirmed,
            )

    def _on_delete_confirmed(self, confirmed: bool | None) -> None:
        if confirmed and self._selected_ids:
            ids = self._selected_ids
            self._set_status(f"Deleting {len(ids)} tweet(s)…")
            self._do_delete(ids)

    def _set_status(self, message: str) -> None:
        self.query_one("#status", Label).update(message)

    @work(exclusive=True, exit_on_error=False, thread=True)
    def _fetch_count(self, username: str, start: datetime, end: datetime) -> None:
        total = count_tweets(username, start, end, self._creds)
        self.app.call_from_thread(
            self.query_one("#count-label", Label).update,
            f"Count: {total:,}",
        )

    @work(exclusive=True, exit_on_error=False, thread=True)
    def _load_tweets(
        self,
        username: str,
        start: datetime,
        end: datetime,
        force_refresh: bool,
    ) -> None:
        if not force_refresh and is_cached(self._db, username, start, end):
            tweets = get_tweets(self._db, username, start, end)
        else:
            tweets = load_tweets(username, start, end, self._creds)
            store_tweets(self._db, username, start, end, tweets)
        self.app.call_from_thread(self._populate_list, tweets)

    def _populate_list(self, tweets: list[dict[str, object]]) -> None:
        self.query_one("#tweet-list", TweetListWidget).populate(tweets)
        self._set_status(f"Loaded {len(tweets):,} tweet(s).")

    @work(exclusive=False, exit_on_error=False, thread=True)
    def _do_delete(self, tweet_ids: frozenset[str]) -> None:
        succeeded = 0
        failed = 0
        for tweet_id in tweet_ids:
            try:
                delete_tweet(tweet_id, self._creds)
                evict_tweet(self._db, tweet_id)
                succeeded += 1
            except Exception as exc:
                failed += 1
                self.app.call_from_thread(
                    self._set_status,
                    f"Error deleting {tweet_id}: {exc}",
                )
        # Refresh the visible list from cache
        dates = self._get_dates()
        if dates is not None:
            start, end = dates
            tweets = get_tweets(self._db, self._username, start, end)
            self.app.call_from_thread(self._populate_list, tweets)
        msg = f"Deleted {succeeded}"
        if failed:
            msg += f", {failed} failed"
        self.app.call_from_thread(self._set_status, msg + ".")

    def on_tweet_list_widget_selection_changed(
        self, event: TweetListWidget.SelectionChanged
    ) -> None:
        self._selected_ids = event.selected_ids
        self.query_one("#delete-btn", Button).disabled = not self._selected_ids

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.state == WorkerState.ERROR:
            error = str(event.worker.error)
            self.app.call_from_thread(self._set_status, f"[red]Error: {error}[/red]")
