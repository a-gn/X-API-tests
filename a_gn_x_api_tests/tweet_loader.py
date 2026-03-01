"""Load tweets from an X account between two dates.

Originally written by Claude Sonnet 4.6 on 2026/03/01
"""

from datetime import datetime, timezone

import requests

from .credentials import Credentials


def _get_user_id(username: str, creds: Credentials) -> str:
    """Look up the numeric user ID for a given username.

    @param username: X username (without @)
    @param creds: API credentials
    @return: Numeric user ID string
    @raises requests.HTTPError: If the API request fails
    """
    response = requests.get(
        f"https://api.x.com/2/users/by/username/{username}",
        headers=creds.to_http_headers(),
    )
    response.raise_for_status()
    return str(response.json()["data"]["id"])


def load_tweets(
    username: str,
    start: datetime,
    end: datetime,
    creds: Credentials,
) -> list[dict[str, object]]:
    """Fetch all tweets from a user account between two dates.

    @param username: X username (without @)
    @param start: Start of date range (timezone-aware)
    @param end: End of date range (timezone-aware)
    @param creds: API credentials
    @return: List of tweet objects (each has at minimum id, text, created_at, author_id)
    @raises ValueError: If start or end are not timezone-aware
    @raises requests.HTTPError: If any API request fails
    """
    if start.tzinfo is None:
        raise ValueError("start must be a timezone-aware datetime")
    if end.tzinfo is None:
        raise ValueError("end must be a timezone-aware datetime")

    user_id = _get_user_id(username, creds)

    start_time = start.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    end_time = end.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    tweets: list[dict[str, object]] = []
    pagination_token: str | None = None

    while True:
        params: dict[str, str | int] = {
            "start_time": start_time,
            "end_time": end_time,
            "max_results": 100,
            "tweet.fields": "id,text,created_at,author_id",
        }
        if pagination_token is not None:
            params["pagination_token"] = pagination_token

        response = requests.get(
            f"https://api.x.com/2/users/{user_id}/tweets",
            headers=creds.to_http_headers(),
            params=params,
        )
        response.raise_for_status()

        body: dict[str, object] = response.json()
        data = body.get("data")
        if isinstance(data, list):
            tweets.extend(data)

        meta = body.get("meta")
        if not isinstance(meta, dict):
            break
        next_token = meta.get("next_token")
        if not isinstance(next_token, str):
            break
        pagination_token = next_token

    return tweets
