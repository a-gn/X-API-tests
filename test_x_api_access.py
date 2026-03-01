import requests


# curl "https://api.x.com/2/users/by/username/xdevelopers" \
#   -H "Authorization: Bearer $BEARER_TOKEN"

bearer_token = input("Bearer token?")
response = requests.get(
    "https://api.x.com/2/users/by/username/xdevelopers",
    headers={"Authorization": f"Bearer {bearer_token}"},
)
print(response)
