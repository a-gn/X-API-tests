"""Tests for TweetRow widget."""

from textual.app import App, ComposeResult
from textual.widgets import Label

from x_api_tui.widgets.tweet_list import TweetRow

TWEET: dict[str, object] = {
    "id": "42",
    "text": "hello world",
    "created_at": "2024-01-15T10:00:00Z",
    "author_id": "99",
}

LONG_TEXT = "a" * 100


class RowApp(App[None]):
    def __init__(self, tweet: dict[str, object], index: int = 0) -> None:
        super().__init__()
        self._tweet = tweet
        self._index = index

    def compose(self) -> ComposeResult:
        yield TweetRow(self._tweet, self._index)


async def test_tweet_row_renders_date_and_text() -> None:
    async with RowApp(TWEET).run_test() as pilot:
        label = pilot.app.query_one(TweetRow).query_one(Label)
        rendered = str(label.content)
        assert "[2024-01-15]" in rendered
        assert "hello world" in rendered


async def test_tweet_row_truncates_long_text() -> None:
    tweet: dict[str, object] = {**TWEET, "text": LONG_TEXT}
    async with RowApp(tweet).run_test() as pilot:
        label = pilot.app.query_one(TweetRow).query_one(Label)
        rendered = str(label.content)
        assert "…" in rendered
        # Preview is capped at 80 chars of text, plus date prefix
        assert LONG_TEXT not in rendered


async def test_tweet_row_short_text_no_ellipsis() -> None:
    async with RowApp(TWEET).run_test() as pilot:
        label = pilot.app.query_one(TweetRow).query_one(Label)
        rendered = str(label.content)
        assert "…" not in rendered


async def test_tweet_row_selected_defaults_false() -> None:
    async with RowApp(TWEET).run_test() as pilot:
        row = pilot.app.query_one(TweetRow)
        assert row.selected is False
        assert not row.has_class("selected")


async def test_tweet_row_selected_true_adds_class() -> None:
    async with RowApp(TWEET).run_test() as pilot:
        row = pilot.app.query_one(TweetRow)
        row.selected = True
        await pilot.pause()
        assert row.has_class("selected")


async def test_tweet_row_selected_false_removes_class() -> None:
    async with RowApp(TWEET).run_test() as pilot:
        row = pilot.app.query_one(TweetRow)
        row.selected = True
        await pilot.pause()
        row.selected = False
        await pilot.pause()
        assert not row.has_class("selected")


def test_tweet_row_tweet_id_property() -> None:
    row = TweetRow(TWEET, index=0)
    assert row.tweet_id == "42"


def test_tweet_row_index_property() -> None:
    row = TweetRow(TWEET, index=7)
    assert row.index == 7
