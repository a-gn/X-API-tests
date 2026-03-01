"""Tests for _parse_date in main_screen.py."""

from datetime import datetime, timezone

import pytest

from x_api_tui.screens.main_screen import _parse_date


@pytest.mark.parametrize(
    ["value", "expected"],
    [
        ("2024-01-15", datetime(2024, 1, 15, tzinfo=timezone.utc)),
        ("2024-12-31", datetime(2024, 12, 31, tzinfo=timezone.utc)),
        ("  2024-01-15  ", datetime(2024, 1, 15, tzinfo=timezone.utc)),
        ("", None),
        ("not-a-date", None),
        ("01/15/2024", None),
        ("2024-13-01", None),
        ("2024-01-32", None),
    ],
)
def test_parse_date(value: str, expected: datetime | None) -> None:
    assert _parse_date(value) == expected


def test_parse_date_returns_utc_aware() -> None:
    result = _parse_date("2024-06-01")
    assert result is not None
    assert result.tzinfo == timezone.utc
