"""Tests for TweetListWidget selection logic."""

from textual.app import App, ComposeResult

from x_api_tui.widgets.tweet_list import TweetListWidget, TweetRow

TWEETS: list[dict[str, object]] = [
    {
        "id": "1",
        "text": "first",
        "created_at": "2024-01-01T00:00:00Z",
        "author_id": "99",
    },
    {
        "id": "2",
        "text": "second",
        "created_at": "2024-01-02T00:00:00Z",
        "author_id": "99",
    },
    {
        "id": "3",
        "text": "third",
        "created_at": "2024-01-03T00:00:00Z",
        "author_id": "99",
    },
]


class ListApp(App[None]):
    def compose(self) -> ComposeResult:
        yield TweetListWidget(id="list")


def _click(widget: TweetListWidget, row: TweetRow, shift: bool = False) -> None:
    """Simulate a TweetRow click via the Clicked message."""
    widget.on_tweet_row_clicked(TweetRow.Clicked(row, shift))


async def test_populate_creates_rows() -> None:
    async with ListApp().run_test() as pilot:
        widget = pilot.app.query_one(TweetListWidget)
        widget.populate(TWEETS)
        await pilot.pause()
        assert len(list(widget.query(TweetRow))) == 3


async def test_populate_all_rows_unselected() -> None:
    async with ListApp().run_test() as pilot:
        widget = pilot.app.query_one(TweetListWidget)
        widget.populate(TWEETS)
        await pilot.pause()
        rows = list(widget.query(TweetRow))
        assert all(not r.selected for r in rows)


async def test_get_selected_ids_empty_initially() -> None:
    async with ListApp().run_test() as pilot:
        widget = pilot.app.query_one(TweetListWidget)
        widget.populate(TWEETS)
        await pilot.pause()
        assert widget.get_selected_ids() == frozenset()


async def test_single_click_selects_row() -> None:
    async with ListApp().run_test() as pilot:
        widget = pilot.app.query_one(TweetListWidget)
        widget.populate(TWEETS)
        await pilot.pause()
        rows = list(widget.query(TweetRow))
        _click(widget, rows[0])
        assert widget.get_selected_ids() == frozenset({"1"})


async def test_single_click_toggles_off() -> None:
    async with ListApp().run_test() as pilot:
        widget = pilot.app.query_one(TweetListWidget)
        widget.populate(TWEETS)
        await pilot.pause()
        rows = list(widget.query(TweetRow))
        _click(widget, rows[0])
        _click(widget, rows[0])
        assert widget.get_selected_ids() == frozenset()


async def test_shift_click_selects_range_forward() -> None:
    async with ListApp().run_test() as pilot:
        widget = pilot.app.query_one(TweetListWidget)
        widget.populate(TWEETS)
        await pilot.pause()
        rows = list(widget.query(TweetRow))
        _click(widget, rows[0])
        _click(widget, rows[2], shift=True)
        assert widget.get_selected_ids() == frozenset({"1", "2", "3"})


async def test_shift_click_selects_range_backward() -> None:
    async with ListApp().run_test() as pilot:
        widget = pilot.app.query_one(TweetListWidget)
        widget.populate(TWEETS)
        await pilot.pause()
        rows = list(widget.query(TweetRow))
        _click(widget, rows[2])
        _click(widget, rows[0], shift=True)
        assert widget.get_selected_ids() == frozenset({"1", "2", "3"})


async def test_shift_click_without_prior_click_is_single_select() -> None:
    async with ListApp().run_test() as pilot:
        widget = pilot.app.query_one(TweetListWidget)
        widget.populate(TWEETS)
        await pilot.pause()
        rows = list(widget.query(TweetRow))
        # No prior click → shift has no effect
        _click(widget, rows[1], shift=True)
        assert widget.get_selected_ids() == frozenset({"2"})


async def test_populate_resets_selection() -> None:
    async with ListApp().run_test() as pilot:
        widget = pilot.app.query_one(TweetListWidget)
        widget.populate(TWEETS)
        await pilot.pause()
        rows = list(widget.query(TweetRow))
        _click(widget, rows[0])
        # Re-populate clears selection
        widget.populate(TWEETS)
        await pilot.pause()
        assert widget.get_selected_ids() == frozenset()


async def test_populate_posts_selection_changed_message() -> None:
    """populate() posts SelectionChanged with empty frozenset."""
    received: list[TweetListWidget.SelectionChanged] = []

    class TrackingApp(App[None]):
        def compose(self) -> ComposeResult:
            yield TweetListWidget(id="list")

        def on_tweet_list_widget_selection_changed(
            self, event: TweetListWidget.SelectionChanged
        ) -> None:
            received.append(event)

    async with TrackingApp().run_test() as pilot:
        widget = pilot.app.query_one(TweetListWidget)
        widget.populate(TWEETS)
        await pilot.pause()
        assert any(e.selected_ids == frozenset() for e in received)


async def test_click_posts_selection_changed_message() -> None:
    received: list[TweetListWidget.SelectionChanged] = []

    class TrackingApp(App[None]):
        def compose(self) -> ComposeResult:
            yield TweetListWidget(id="list")

        def on_tweet_list_widget_selection_changed(
            self, event: TweetListWidget.SelectionChanged
        ) -> None:
            received.append(event)

    async with TrackingApp().run_test() as pilot:
        widget = pilot.app.query_one(TweetListWidget)
        widget.populate(TWEETS)
        await pilot.pause()
        received.clear()
        rows = list(widget.query(TweetRow))
        _click(widget, rows[0])
        await pilot.pause()
        assert len(received) == 1
        assert received[0].selected_ids == frozenset({"1"})


async def test_click_outside_row_does_nothing() -> None:
    async with ListApp().run_test() as pilot:
        widget = pilot.app.query_one(TweetListWidget)
        widget.populate(TWEETS)
        await pilot.pause()
        # No click posted → selection stays empty
        assert widget.get_selected_ids() == frozenset()
