"""Top-level Textual application.

Originally written by Claude Sonnet 4.6 on 2026/03/01
"""

import sqlite3

from a_gn_x_api_tests.credentials import Credentials
from textual.app import App

from x_api_tui.screens.main_screen import MainScreen
from x_api_tui.screens.user_screen import UserSelectionScreen


class TweetViewerApp(App[None]):
    """Root application class."""

    BINDINGS = [("ctrl+c", "ctrl_c", "Quit")]

    def __init__(self, creds: Credentials, db: sqlite3.Connection) -> None:
        super().__init__()
        self._creds = creds
        self._db = db
        self._ctrl_c_pending = False

    def on_mount(self) -> None:
        self.push_screen(
            UserSelectionScreen(self._creds),
            callback=self._on_user_confirmed,
        )

    def _on_user_confirmed(self, username: str | None) -> None:
        if username is not None:
            self.push_screen(MainScreen(username, self._creds, self._db))

    def action_ctrl_c(self) -> None:
        """Quit on second Ctrl+C, show hint on first."""
        if self._ctrl_c_pending:
            self.exit()
        else:
            self._ctrl_c_pending = True
            self.notify("Press Ctrl+C again to quit.", timeout=2)
            self.set_timer(2, self._reset_ctrl_c)

    def _reset_ctrl_c(self) -> None:
        self._ctrl_c_pending = False
