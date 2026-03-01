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

    BINDINGS = [("ctrl+q", "quit", "Quit")]

    def __init__(self, creds: Credentials, db: sqlite3.Connection) -> None:
        super().__init__()
        self._creds = creds
        self._db = db

    def on_mount(self) -> None:
        self.push_screen(
            UserSelectionScreen(self._creds),
            callback=self._on_user_confirmed,
        )

    def _on_user_confirmed(self, username: str | None) -> None:
        if username is not None:
            self.push_screen(MainScreen(username, self._creds, self._db))
