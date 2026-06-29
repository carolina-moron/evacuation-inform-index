import os
import requests
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("ACLED_EMAIL")
PASSWORD = os.getenv("ACLED_PASSWORD")

TOKEN_URL = "https://acleddata.com/oauth/token"
API_URL = "https://acleddata.com/api/acled/read"


def get_token():
    resp = requests.post(TOKEN_URL, data={
        "username": EMAIL,
        "password": PASSWORD,
        "grant_type": "password",
        "client_id": "acled",
        "scope": "authenticated",
    })
    resp.raise_for_status()
    return resp.json()["access_token"]


def get_data(token, **params):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(API_URL, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    token = get_token()
    data = get_data(token, limit=10)
    print(data)
