"""Tests for MainScreen."""

import sqlite3
from unittest.mock import MagicMock, patch

import requests
from a_gn_x_api_tests.credentials import Credentials
from textual.app import App
from textual.events import MouseDown
from textual.widgets import Button, Label

from x_api_tui.cache import open_db
from x_api_tui.screens.main_screen import MainScreen
from x_api_tui.widgets.tweet_list import TweetListWidget, TweetRow

CREDS = Credentials(consumer_key="k", secret_key="s", bearer_token="tok")

TWEETS: list[dict[str, object]] = [
    {
        "id": "1",
        "text": "hello world",
        "created_at": "2024-01-15T10:00:00Z",
        "author_id": "99",
    },
    {
        "id": "2",
        "text": "another tweet",
        "created_at": "2024-01-20T08:00:00Z",
        "author_id": "99",
    },
]

_COUNT_PATCH = "x_api_tui.screens.main_screen.count_tweets"
_LOAD_PATCH = "x_api_tui.screens.main_screen.load_tweets"
_DELETE_PATCH = "x_api_tui.screens.main_screen.delete_tweet"


def open_memory_db() -> sqlite3.Connection:
    return open_db(":memory:")


class MainApp(App[None]):
    def __init__(self, db: sqlite3.Connection) -> None:
        super().__init__()
        self._db = db

    def on_mount(self) -> None:
        self.push_screen(MainScreen("testuser", CREDS, self._db))


def _make_click(widget: TweetRow, shift: bool = False) -> MouseDown:
    event = MagicMock(spec=MouseDown)
    event.widget = widget
    event.shift = shift
    event.stop = MagicMock()
    return event


async def _type_dates(pilot: object, start: str, end: str) -> None:
    from textual.pilot import Pilot

    assert isinstance(pilot, Pilot)
    await pilot.click("#start-date")
    for ch in start:
        await pilot.press(ch)
    await pilot.click("#end-date")
    for ch in end:
        await pilot.press(ch)
    await pilot.pause()


# --- Date input / UI state ---


async def test_show_refresh_disabled_initially() -> None:
    async with MainApp(open_memory_db()).run_test() as pilot:
        screen = pilot.app.screen
        assert screen.query_one("#show-btn", Button).disabled
        assert screen.query_one("#refresh-btn", Button).disabled
        assert screen.query_one("#delete-btn", Button).disabled


async def test_valid_dates_enable_show_refresh() -> None:
    with patch(_COUNT_PATCH, return_value=0):
        async with MainApp(open_memory_db()).run_test() as pilot:
            await _type_dates(pilot, "2024-01-01", "2024-01-31")
            screen = pilot.app.screen
            assert not screen.query_one("#show-btn", Button).disabled
            assert not screen.query_one("#refresh-btn", Button).disabled


async def test_start_after_end_keeps_buttons_disabled() -> None:
    async with MainApp(open_memory_db()).run_test() as pilot:
        await _type_dates(pilot, "2024-02-01", "2024-01-01")
        assert pilot.app.screen.query_one("#show-btn", Button).disabled


async def test_count_label_updates_after_valid_dates() -> None:
    with patch(_COUNT_PATCH, return_value=42):
        async with MainApp(open_memory_db()).run_test() as pilot:
            await _type_dates(pilot, "2024-01-01", "2024-01-31")
            await pilot.app.workers.wait_for_complete()
            await pilot.pause()
            label = pilot.app.screen.query_one("#count-label", Label)
            assert "42" in str(label.content)


async def test_invalid_date_resets_count_label() -> None:
    async with MainApp(open_memory_db()).run_test() as pilot:
        await pilot.click("#start-date")
        await pilot.press("x")
        await pilot.pause()
        label = pilot.app.screen.query_one("#count-label", Label)
        assert "—" in str(label.content)


# --- Show tweets ---


async def test_show_tweets_loads_from_api() -> None:
    with patch(_COUNT_PATCH, return_value=2), patch(_LOAD_PATCH, return_value=TWEETS):
        async with MainApp(open_memory_db()).run_test() as pilot:
            await _type_dates(pilot, "2024-01-01", "2024-01-31")
            await pilot.app.workers.wait_for_complete()
            await pilot.click("#show-btn")
            await pilot.app.workers.wait_for_complete()
            await pilot.pause()
            rows = list(pilot.app.screen.query(TweetRow))
            assert len(rows) == 2


async def test_show_tweets_updates_status() -> None:
    with patch(_COUNT_PATCH, return_value=2), patch(_LOAD_PATCH, return_value=TWEETS):
        async with MainApp(open_memory_db()).run_test() as pilot:
            await _type_dates(pilot, "2024-01-01", "2024-01-31")
            await pilot.app.workers.wait_for_complete()
            await pilot.click("#show-btn")
            await pilot.app.workers.wait_for_complete()
            await pilot.pause()
            status = pilot.app.screen.query_one("#status", Label)
            assert "2" in str(status.content)
            assert "tweet" in str(status.content)


async def test_show_tweets_uses_cache_on_second_load() -> None:
    with (
        patch(_COUNT_PATCH, return_value=2),
        patch(_LOAD_PATCH, return_value=TWEETS) as mock_load,
    ):
        async with MainApp(open_memory_db()).run_test() as pilot:
            await _type_dates(pilot, "2024-01-01", "2024-01-31")
            await pilot.app.workers.wait_for_complete()
            await pilot.click("#show-btn")
            await pilot.app.workers.wait_for_complete()
            await pilot.pause()
            await pilot.click("#show-btn")
            await pilot.app.workers.wait_for_complete()
            await pilot.pause()
            assert mock_load.call_count == 1


async def test_refresh_bypasses_cache() -> None:
    with (
        patch(_COUNT_PATCH, return_value=2),
        patch(_LOAD_PATCH, return_value=TWEETS) as mock_load,
    ):
        async with MainApp(open_memory_db()).run_test() as pilot:
            await _type_dates(pilot, "2024-01-01", "2024-01-31")
            await pilot.app.workers.wait_for_complete()
            await pilot.click("#show-btn")
            await pilot.app.workers.wait_for_complete()
            await pilot.pause()
            await pilot.click("#refresh-btn")
            await pilot.app.workers.wait_for_complete()
            await pilot.pause()
            assert mock_load.call_count == 2


# --- Selection enabling delete button ---


async def test_selection_enables_delete_button() -> None:
    with patch(_COUNT_PATCH, return_value=2), patch(_LOAD_PATCH, return_value=TWEETS):
        async with MainApp(open_memory_db()).run_test() as pilot:
            await _type_dates(pilot, "2024-01-01", "2024-01-31")
            await pilot.app.workers.wait_for_complete()
            await pilot.click("#show-btn")
            await pilot.app.workers.wait_for_complete()
            await pilot.pause()
            widget = pilot.app.screen.query_one(TweetListWidget)
            rows = list(widget.query(TweetRow))
            widget.on_mouse_down(_make_click(rows[0]))
            await pilot.pause()
            assert not pilot.app.screen.query_one("#delete-btn", Button).disabled


# --- Delete flow ---


async def test_cancel_confirm_no_deletion() -> None:
    with (
        patch(_COUNT_PATCH, return_value=2),
        patch(_LOAD_PATCH, return_value=TWEETS),
        patch(_DELETE_PATCH) as mock_del,
    ):
        async with MainApp(open_memory_db()).run_test() as pilot:
            await _type_dates(pilot, "2024-01-01", "2024-01-31")
            await pilot.app.workers.wait_for_complete()
            await pilot.click("#show-btn")
            await pilot.app.workers.wait_for_complete()
            await pilot.pause()
            widget = pilot.app.screen.query_one(TweetListWidget)
            rows = list(widget.query(TweetRow))
            widget.on_mouse_down(_make_click(rows[0]))
            await pilot.pause()
            await pilot.click("#delete-btn")
            await pilot.pause()
            await pilot.click("#cancel-btn")
            await pilot.pause()
            mock_del.assert_not_called()


async def test_confirm_delete_calls_api() -> None:
    with (
        patch(_COUNT_PATCH, return_value=2),
        patch(_LOAD_PATCH, return_value=TWEETS),
        patch(_DELETE_PATCH) as mock_del,
    ):
        async with MainApp(open_memory_db()).run_test() as pilot:
            await _type_dates(pilot, "2024-01-01", "2024-01-31")
            await pilot.app.workers.wait_for_complete()
            await pilot.click("#show-btn")
            await pilot.app.workers.wait_for_complete()
            await pilot.pause()
            widget = pilot.app.screen.query_one(TweetListWidget)
            rows = list(widget.query(TweetRow))
            widget.on_mouse_down(_make_click(rows[0]))
            await pilot.pause()
            # Open confirm modal
            await pilot.click("#delete-btn")
            await pilot.pause()
            # Confirm deletion (the modal's delete button also has id="delete-btn")
            await pilot.click("#delete-btn")
            await pilot.app.workers.wait_for_complete()
            await pilot.pause()
            mock_del.assert_called_once_with("1", CREDS)


async def test_confirm_delete_shows_success_status() -> None:
    with (
        patch(_COUNT_PATCH, return_value=2),
        patch(_LOAD_PATCH, return_value=TWEETS),
        patch(_DELETE_PATCH),
    ):
        async with MainApp(open_memory_db()).run_test() as pilot:
            await _type_dates(pilot, "2024-01-01", "2024-01-31")
            await pilot.app.workers.wait_for_complete()
            await pilot.click("#show-btn")
            await pilot.app.workers.wait_for_complete()
            await pilot.pause()
            widget = pilot.app.screen.query_one(TweetListWidget)
            rows = list(widget.query(TweetRow))
            widget.on_mouse_down(_make_click(rows[0]))
            await pilot.pause()
            await pilot.click("#delete-btn")
            await pilot.pause()
            await pilot.click("#delete-btn")
            await pilot.app.workers.wait_for_complete()
            await pilot.pause()
            status = pilot.app.screen.query_one("#status", Label)
            assert "Deleted 1" in str(status.content)


async def test_partial_delete_failure_status() -> None:
    def _delete_side_effect(tweet_id: str, creds: Credentials) -> None:
        if tweet_id == "1":
            raise requests.HTTPError("403 Forbidden")

    with (
        patch(_COUNT_PATCH, return_value=2),
        patch(_LOAD_PATCH, return_value=TWEETS),
        patch(_DELETE_PATCH, side_effect=_delete_side_effect),
    ):
        async with MainApp(open_memory_db()).run_test() as pilot:
            await _type_dates(pilot, "2024-01-01", "2024-01-31")
            await pilot.app.workers.wait_for_complete()
            await pilot.click("#show-btn")
            await pilot.app.workers.wait_for_complete()
            await pilot.pause()
            widget = pilot.app.screen.query_one(TweetListWidget)
            rows = list(widget.query(TweetRow))
            widget.on_mouse_down(_make_click(rows[0]))
            widget.on_mouse_down(_make_click(rows[1], shift=True))
            await pilot.pause()
            await pilot.click("#delete-btn")
            await pilot.pause()
            await pilot.click("#delete-btn")
            await pilot.app.workers.wait_for_complete()
            await pilot.pause()
            status = pilot.app.screen.query_one("#status", Label)
            assert "failed" in str(status.content)


# --- Worker error handling ---


async def test_load_tweets_error_shows_in_status() -> None:
    with (
        patch(_COUNT_PATCH, return_value=0),
        patch(_LOAD_PATCH, side_effect=requests.HTTPError("403 Forbidden")),
    ):
        async with MainApp(open_memory_db()).run_test() as pilot:
            await _type_dates(pilot, "2024-01-01", "2024-01-31")
            await pilot.app.workers.wait_for_complete()
            await pilot.click("#show-btn")
            await pilot.app.workers.wait_for_complete()
            await pilot.pause()
            status = pilot.app.screen.query_one("#status", Label)
            assert "Error" in str(status.content)
