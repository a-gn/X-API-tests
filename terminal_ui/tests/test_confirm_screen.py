"""Tests for ConfirmDeleteScreen modal."""

from textual.app import App
from textual.widgets import Label

from x_api_tui.screens.confirm_screen import ConfirmDeleteScreen


class ConfirmApp(App[bool | None]):
    def __init__(self, count: int) -> None:
        super().__init__()
        self._count = count

    def on_mount(self) -> None:
        self.push_screen(ConfirmDeleteScreen(self._count), callback=self.exit)


async def test_confirm_screen_shows_count() -> None:
    async with ConfirmApp(3).run_test() as pilot:
        prompt = pilot.app.screen.query_one("#prompt", Label)
        assert "3" in str(prompt.content)
        assert "tweet(s)" in str(prompt.content)


async def test_confirm_screen_shows_warning() -> None:
    async with ConfirmApp(3).run_test() as pilot:
        warning = pilot.app.screen.query_one("#warning", Label)
        assert "cannot be undone" in str(warning.content)


async def test_cancel_button_dismisses_false() -> None:
    async with ConfirmApp(3).run_test() as pilot:
        await pilot.click("#cancel-btn")
        await pilot.pause()
        assert pilot.app.return_value is False


async def test_delete_button_dismisses_true() -> None:
    async with ConfirmApp(3).run_test() as pilot:
        await pilot.click("#delete-btn")
        await pilot.pause()
        assert pilot.app.return_value is True


async def test_confirm_screen_count_one() -> None:
    async with ConfirmApp(1).run_test() as pilot:
        prompt = pilot.app.screen.query_one("#prompt", Label)
        assert "1" in str(prompt.content)
        assert "tweet(s)" in str(prompt.content)
