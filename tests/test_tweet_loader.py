"""Tests for tweet_loader module."""

from datetime import datetime, timezone

import pytest
import requests_mock as requests_mock_module

from a_gn_x_api_tests.credentials import Credentials
from a_gn_x_api_tests.tweet_loader import load_tweets

CREDS = Credentials(
    consumer_key="test_consumer_key",
    secret_key="test_secret_key",
    bearer_token="test_bearer_token",
)

START = datetime(2024, 1, 1, tzinfo=timezone.utc)
END = datetime(2024, 1, 31, tzinfo=timezone.utc)

USER_URL = "https://api.x.com/2/users/by/username/testuser"
TWEETS_URL = "https://api.x.com/2/users/123/tweets"


def test_load_tweets_requires_aware_start() -> None:
    with pytest.raises(ValueError, match="start must be a timezone-aware datetime"):
        load_tweets("testuser", datetime(2024, 1, 1), END, CREDS)


def test_load_tweets_requires_aware_end() -> None:
    with pytest.raises(ValueError, match="end must be a timezone-aware datetime"):
        load_tweets("testuser", START, datetime(2024, 1, 31), CREDS)


def test_load_tweets_sends_bearer_token(
    requests_mock: requests_mock_module.Mocker,
) -> None:
    requests_mock.get(USER_URL, json={"data": {"id": "123"}})
    requests_mock.get(TWEETS_URL, json={"meta": {"result_count": 0}})

    load_tweets("testuser", START, END, CREDS)

    assert (
        requests_mock.request_history[0].headers["Authorization"]
        == "Bearer test_bearer_token"
    )
    assert (
        requests_mock.request_history[1].headers["Authorization"]
        == "Bearer test_bearer_token"
    )


def test_load_tweets_looks_up_user_by_username(
    requests_mock: requests_mock_module.Mocker,
) -> None:
    requests_mock.get(USER_URL, json={"data": {"id": "123"}})
    requests_mock.get(TWEETS_URL, json={"meta": {"result_count": 0}})

    load_tweets("testuser", START, END, CREDS)

    assert requests_mock.request_history[0].url == USER_URL


def test_load_tweets_sends_correct_time_params(
    requests_mock: requests_mock_module.Mocker,
) -> None:
    requests_mock.get(USER_URL, json={"data": {"id": "123"}})
    requests_mock.get(TWEETS_URL, json={"meta": {"result_count": 0}})

    load_tweets("testuser", START, END, CREDS)

    qs = requests_mock.request_history[1].qs
    assert qs["start_time"] == ["2024-01-01t00:00:00z"]
    assert qs["end_time"] == ["2024-01-31t00:00:00z"]
    assert qs["max_results"] == ["100"]


def test_load_tweets_returns_tweets(requests_mock: requests_mock_module.Mocker) -> None:
    tweet = {
        "id": "1",
        "text": "hello",
        "created_at": "2024-01-15T10:00:00Z",
        "author_id": "123",
    }
    requests_mock.get(USER_URL, json={"data": {"id": "123"}})
    requests_mock.get(TWEETS_URL, json={"data": [tweet], "meta": {"result_count": 1}})

    result = load_tweets("testuser", START, END, CREDS)

    assert result == [tweet]


def test_load_tweets_paginates(requests_mock: requests_mock_module.Mocker) -> None:
    tweet1 = {"id": "1", "text": "first"}
    tweet2 = {"id": "2", "text": "second"}
    requests_mock.get(USER_URL, json={"data": {"id": "123"}})
    requests_mock.get(
        TWEETS_URL,
        [
            {
                "json": {
                    "data": [tweet1],
                    "meta": {"result_count": 1, "next_token": "page2token"},
                }
            },
            {"json": {"data": [tweet2], "meta": {"result_count": 1}}},
        ],
    )

    result = load_tweets("testuser", START, END, CREDS)

    assert result == [tweet1, tweet2]
    assert requests_mock.request_history[2].qs["pagination_token"] == ["page2token"]


def test_load_tweets_empty_result(requests_mock: requests_mock_module.Mocker) -> None:
    requests_mock.get(USER_URL, json={"data": {"id": "123"}})
    requests_mock.get(TWEETS_URL, json={"meta": {"result_count": 0}})

    result = load_tweets("testuser", START, END, CREDS)

    assert result == []


def test_load_tweets_raises_on_user_not_found(
    requests_mock: requests_mock_module.Mocker,
) -> None:
    requests_mock.get(USER_URL, status_code=404)

    with pytest.raises(Exception):
        load_tweets("testuser", START, END, CREDS)


def test_load_tweets_raises_on_tweets_error(
    requests_mock: requests_mock_module.Mocker,
) -> None:
    requests_mock.get(USER_URL, json={"data": {"id": "123"}})
    requests_mock.get(TWEETS_URL, status_code=401)

    with pytest.raises(Exception):
        load_tweets("testuser", START, END, CREDS)
