"""Custom tweet list widget with shift-click range selection.

Originally written by Claude Sonnet 4.6 on 2026/03/01
"""

from textual.app import ComposeResult
from textual.events import MouseDown
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label


class TweetRow(Widget):
    """A single tweet row. Manages its own selected visual state."""

    DEFAULT_CSS = """
    TweetRow {
        height: 3;
        padding: 0 1;
    }
    TweetRow.selected {
        background: $accent;
        color: $text;
    }
    TweetRow:hover {
        background: $surface-lighten-1;
    }
    """

    selected: reactive[bool] = reactive(False)

    def __init__(self, tweet: dict[str, object], index: int) -> None:
        super().__init__()
        self._tweet = tweet
        self._index = index

    def compose(self) -> ComposeResult:
        created_at = str(self._tweet.get("created_at", ""))[:10]
        text = str(self._tweet.get("text", ""))
        preview = text[:80] + ("…" if len(text) > 80 else "")
        yield Label(f"[{created_at}] {preview}")

    def watch_selected(self, selected: bool) -> None:
        self.set_class(selected, "selected")

    @property
    def tweet_id(self) -> str:
        return str(self._tweet["id"])

    @property
    def index(self) -> int:
        return self._index


class TweetListWidget(Widget):
    """Scrollable list of TweetRow widgets with shift-click range selection."""

    DEFAULT_CSS = """
    TweetListWidget {
        overflow-y: scroll;
    }
    """

    class SelectionChanged(Message):
        """Posted when the selected set changes."""

        def __init__(self, selected_ids: frozenset[str]) -> None:
            super().__init__()
            self.selected_ids = selected_ids

    def __init__(self, id: str | None = None) -> None:  # noqa: A002
        super().__init__(id=id)
        self._rows: list[TweetRow] = []
        self._last_clicked_index: int | None = None

    def populate(self, tweets: list[dict[str, object]]) -> None:
        """Replace all rows with the given tweets."""
        self._last_clicked_index = None
        self._rows = [TweetRow(t, i) for i, t in enumerate(tweets)]
        self.remove_children()
        if self._rows:
            self.mount(*self._rows)
        self.post_message(self.SelectionChanged(frozenset()))

    def get_selected_ids(self) -> frozenset[str]:
        return frozenset(r.tweet_id for r in self._rows if r.selected)

    def on_mouse_down(self, event: MouseDown) -> None:
        """Handle click with optional shift for range selection."""
        # Walk up from the event target to find the TweetRow ancestor.
        target = event.widget
        clicked_row: TweetRow | None = None
        while target is not None:
            if isinstance(target, TweetRow):
                clicked_row = target
                break
            target = target.parent  # type: ignore[assignment]

        if clicked_row is None:
            return

        event.stop()

        clicked_index = clicked_row.index

        if event.shift and self._last_clicked_index is not None:
            lo = min(self._last_clicked_index, clicked_index)
            hi = max(self._last_clicked_index, clicked_index)
            new_state = not clicked_row.selected
            for row in self._rows[lo : hi + 1]:
                row.selected = new_state
        else:
            clicked_row.selected = not clicked_row.selected

        self._last_clicked_index = clicked_index
        self.post_message(self.SelectionChanged(self.get_selected_ids()))
