import requests

from .credentials import Credentials


def check_access(creds: Credentials) -> None:
    # curl "https://api.x.com/2/users/by/username/xdevelopers" \
    #   -H "Authorization: Bearer $BEARER_TOKEN"

    response = requests.get(
        "https://api.x.com/2/users/by/username/xdevelopers",
        headers=creds.to_http_headers(),
    )
    response.raise_for_status()
