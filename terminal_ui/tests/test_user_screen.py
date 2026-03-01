"""Tests for UserSelectionScreen."""

from unittest.mock import patch

import requests
from a_gn_x_api_tests.credentials import Credentials
from textual.app import App
from textual.widgets import Button, Label

from x_api_tui.screens.user_screen import UserSelectionScreen

CREDS = Credentials(consumer_key="k", secret_key="s", bearer_token="tok")
_PATCH_TARGET = "x_api_tui.screens.user_screen._get_user_id"


class UserApp(App[str | None]):
    def __init__(self, creds: Credentials) -> None:
        super().__init__()
        self._creds = creds

    def on_mount(self) -> None:
        self.push_screen(UserSelectionScreen(self._creds), callback=self.exit)


async def test_confirm_button_disabled_initially() -> None:
    async with UserApp(CREDS).run_test() as pilot:
        btn = pilot.app.screen.query_one("#confirm-btn", Button)
        assert btn.disabled


async def test_typing_username_enables_button() -> None:
    async with UserApp(CREDS).run_test() as pilot:
        await pilot.click("#username-input")
        await pilot.press("a", "l", "i", "c", "e")
        await pilot.pause()
        btn = pilot.app.screen.query_one("#confirm-btn", Button)
        assert not btn.disabled


async def test_clearing_username_disables_button() -> None:
    async with UserApp(CREDS).run_test() as pilot:
        await pilot.click("#username-input")
        await pilot.press("a")
        await pilot.pause()
        await pilot.press("backspace")
        await pilot.pause()
        btn = pilot.app.screen.query_one("#confirm-btn", Button)
        assert btn.disabled


async def test_valid_username_dismisses_with_username() -> None:
    with patch(_PATCH_TARGET, return_value="123"):
        async with UserApp(CREDS).run_test() as pilot:
            await pilot.click("#username-input")
            await pilot.press("a", "l", "i", "c", "e")
            await pilot.click("#confirm-btn")
            await pilot.app.workers.wait_for_complete()
            await pilot.pause()
            assert pilot.app.return_value == "alice"


async def test_invalid_username_shows_error() -> None:
    with patch(_PATCH_TARGET, side_effect=requests.HTTPError("404 Not Found")):
        async with UserApp(CREDS).run_test() as pilot:
            await pilot.click("#username-input")
            await pilot.press("n", "o", "b", "o", "d", "y")
            await pilot.click("#confirm-btn")
            await pilot.app.workers.wait_for_complete()
            await pilot.pause()
            status = pilot.app.screen.query_one("#status", Label)
            assert "Error" in str(status.content)


async def test_invalid_username_re_enables_button() -> None:
    with patch(_PATCH_TARGET, side_effect=requests.HTTPError("404 Not Found")):
        async with UserApp(CREDS).run_test() as pilot:
            await pilot.click("#username-input")
            await pilot.press("n", "o", "b", "o", "d", "y")
            await pilot.click("#confirm-btn")
            await pilot.app.workers.wait_for_complete()
            await pilot.pause()
            btn = pilot.app.screen.query_one("#confirm-btn", Button)
            assert not btn.disabled


async def test_enter_submits_validation() -> None:
    with patch(_PATCH_TARGET, return_value="456"):
        async with UserApp(CREDS).run_test() as pilot:
            await pilot.click("#username-input")
            await pilot.press("b", "o", "b")
            await pilot.press("enter")
            await pilot.app.workers.wait_for_complete()
            await pilot.pause()
            assert pilot.app.return_value == "bob"
