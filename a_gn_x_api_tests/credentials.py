import json
from pathlib import Path

import pydantic


class Credentials(pydantic.BaseModel):
    """X API credentials."""

    consumerKey: str
    secretKey: str
    bearerToken: str

    model_config = pydantic.ConfigDict(frozen=True)


def load_credentials(path: Path | None = None) -> Credentials:
    """Load credentials from JSON file.

    @param path: Path to credentials file. Defaults to CREDENTIALS.json in project root.
    @return: Parsed credentials
    @raises FileNotFoundError: If credentials file doesn't exist
    @raises pydantic.ValidationError: If credentials are invalid
    """
    if path is None:
        path = Path(__file__).parent.parent / "CREDENTIALS.json"

    with path.open() as f:
        data = json.load(f)

    return Credentials(**data)
