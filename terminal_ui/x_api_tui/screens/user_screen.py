"""User account selection screen.

Originally written by Claude Sonnet 4.6 on 2026/03/01
"""

from a_gn_x_api_tests.credentials import Credentials
from a_gn_x_api_tests.tweet_loader import _get_user_id
from textual import work
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Input, Label
from textual.worker import Worker, WorkerState


class UserSelectionScreen(Screen[str]):
    """First screen: enter and validate a username. Dismisses with the username."""

    DEFAULT_CSS = """
    UserSelectionScreen {
        align: center middle;
    }
    #container {
        width: 60;
        height: auto;
        padding: 2 4;
        border: round $primary;
        background: $panel;
    }
    #title {
        text-align: center;
        text-style: bold;
        margin-bottom: 2;
    }
    #username-input {
        margin-bottom: 1;
    }
    #status {
        margin-bottom: 1;
        height: 1;
    }
    #confirm-btn {
        width: 100%;
    }
    """

    def __init__(self, creds: Credentials) -> None:
        super().__init__()
        self._creds = creds

    def compose(self) -> ComposeResult:
        from textual.containers import Vertical

        with Vertical(id="container"):
            yield Label("X Tweet Viewer", id="title")
            yield Input(placeholder="username (without @)", id="username-input")
            yield Label("", id="status")
            yield Button("Confirm", id="confirm-btn", disabled=True)

    def on_input_changed(self, event: Input.Changed) -> None:
        self.query_one("#confirm-btn", Button).disabled = not event.value.strip()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        username = event.value.strip()
        if username:
            self._start_validation(username)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm-btn":
            username = self.query_one("#username-input", Input).value.strip()
            if username:
                self._start_validation(username)

    def _start_validation(self, username: str) -> None:
        self.query_one("#confirm-btn", Button).disabled = True
        self.query_one("#status", Label).update("Checking…")
        self._validate_user(username)

    @work(exclusive=True, exit_on_error=False, thread=True)
    def _validate_user(self, username: str) -> None:
        """Confirm the user exists by resolving their ID. Runs in a thread."""
        _get_user_id(username, self._creds)
        self.app.call_from_thread(self.dismiss, username)

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.state == WorkerState.ERROR:
            error = str(event.worker.error)
            self.query_one("#status", Label).update(f"[red]Error: {error}[/red]")
            self.query_one("#confirm-btn", Button).disabled = False
        elif event.state == WorkerState.SUCCESS:
            pass  # dismiss already called from thread
