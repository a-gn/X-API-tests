"""CLI to fetch tweets from an X account between two dates and print them as JSON."""

import json
from datetime import datetime, timezone
from pathlib import Path

import click

from a_gn_x_api_tests.credentials import load_credentials
from a_gn_x_api_tests.tweet_loader import load_tweets


@click.command()
@click.argument("username")
@click.option(
    "--start",
    required=True,
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Start date (inclusive), e.g. 2025-01-01",
)
@click.option(
    "--end",
    required=True,
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="End date (inclusive), e.g. 2025-01-31",
)
@click.option(
    "--credentials",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to credentials JSON file. Defaults to CREDENTIALS.json.",
)
def main(
    username: str, start: datetime, end: datetime, credentials: Path | None
) -> None:
    """Fetch all tweets from USERNAME between START and END and print as JSON."""
    if end <= start:
        raise click.BadParameter("end must be after start", param_hint="--end")

    creds = load_credentials(credentials)
    start_utc = start.replace(tzinfo=timezone.utc)
    end_utc = end.replace(tzinfo=timezone.utc)

    tweets = load_tweets(username, start_utc, end_utc, creds)
    click.echo(f"Fetched {len(tweets)} tweets from @{username}", err=True)
    click.echo(json.dumps(tweets, indent=2))


if __name__ == "__main__":
    main()
