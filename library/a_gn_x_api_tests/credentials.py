import json
from pathlib import Path

import pydantic


class Credentials(pydantic.BaseModel):
    """X API credentials."""

    consumer_key: str
    secret_key: str
    bearer_token: str

    model_config = pydantic.ConfigDict(frozen=True)

    def to_http_headers(self) -> dict[str, str]:
        """Make HTTP headers to set in an HTTP request to authenticate to the X API."""
        return {"Authorization": f"Bearer {self.bearer_token}"}


def load_credentials(path: Path | None = None) -> Credentials:
    """Load credentials from JSON file.

    @param path: Path to credentials file. Defaults to CREDENTIALS.json in project root.
    @return: Parsed credentials
    @raises FileNotFoundError: If credentials file doesn't exist
    @raises pydantic.ValidationError: If credentials are invalid
    """
    if path is None:
        path = Path("CREDENTIALS.json")

    with path.open() as f:
        data = json.load(f)

    return Credentials(**data)
