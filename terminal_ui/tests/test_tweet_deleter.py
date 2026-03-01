"""Tests for delete_tweet() in tweet_loader."""

import pytest
import requests
from a_gn_x_api_tests.credentials import Credentials
from a_gn_x_api_tests.tweet_loader import delete_tweet

CREDS = Credentials(consumer_key="k", secret_key="s", bearer_token="test_token")


def test_delete_sends_bearer_token(requests_mock: object) -> None:
    import requests_mock as rm_module

    assert isinstance(requests_mock, rm_module.Mocker)
    requests_mock.delete(
        "https://api.x.com/2/tweets/42",
        json={"data": {"deleted": True}},
    )
    delete_tweet("42", CREDS)
    assert (
        requests_mock.request_history[0].headers["Authorization"] == "Bearer test_token"
    )


def test_delete_raises_on_error(requests_mock: object) -> None:
    import requests_mock as rm_module

    assert isinstance(requests_mock, rm_module.Mocker)
    requests_mock.delete("https://api.x.com/2/tweets/42", status_code=403)
    with pytest.raises(requests.HTTPError):
        delete_tweet("42", CREDS)
