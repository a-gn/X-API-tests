"""Confirmation modal screen for bulk tweet deletion.

Originally written by Claude Sonnet 4.6 on 2026/03/01
"""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class ConfirmDeleteScreen(ModalScreen[bool]):
    """Confirmation modal. Dismisses True on confirm, False on cancel."""

    DEFAULT_CSS = """
    ConfirmDeleteScreen {
        align: center middle;
    }
    #dialog {
        padding: 2 4;
        border: double $error;
        background: $panel;
        width: 50;
        height: auto;
    }
    #prompt {
        text-align: center;
        margin-bottom: 1;
    }
    #warning {
        color: $error;
        text-align: center;
        margin-bottom: 2;
    }
    #buttons {
        align: center middle;
        height: auto;
    }
    #buttons Button {
        margin: 0 1;
    }
    """

    def __init__(self, count: int) -> None:
        super().__init__()
        self._count = count

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(f"Delete {self._count} tweet(s)?", id="prompt")
            yield Label("This cannot be undone.", id="warning")
            with Horizontal(id="buttons"):
                yield Button("Cancel", id="cancel-btn", variant="default")
                yield Button("Delete", id="delete-btn", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "delete-btn")
