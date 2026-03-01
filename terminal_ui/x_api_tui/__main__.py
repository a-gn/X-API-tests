"""Entry point: python -m x_api_tui

Originally written by Claude Sonnet 4.6 on 2026/03/01
"""

from pathlib import Path

import click
from a_gn_x_api_tests.credentials import load_credentials

from x_api_tui.app import TweetViewerApp
from x_api_tui.cache import open_db


@click.command()
@click.option(
    "--credentials",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to credentials JSON. Defaults to CREDENTIALS.json.",
)
@click.option(
    "--db",
    type=click.Path(path_type=Path),
    default=None,
    help="Path to SQLite cache DB. Defaults to ~/.local/share/x-tweet-ui/cache.db.",
)
def main(credentials: Path | None, db: Path | None) -> None:
    """Launch the X tweet viewer/deleter terminal UI."""
    creds = load_credentials(credentials)
    conn = open_db(db) if db is not None else open_db()
    TweetViewerApp(creds, conn).run()


if __name__ == "__main__":
    main()
