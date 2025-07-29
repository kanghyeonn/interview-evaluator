import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_token(client_id: str, client_secret: str):
    response = requests.post(
        "https://openapi.vito.ai/v1/authenticate",
        data={"client_id": client_id, "client_secret": client_secret},
        headers={"Accept": "application/json"},
    )
    response.raise_for_status()
    result = response.json()
    return result["access_token"], result["expire_at"]

print(get_token(os.getenv("VITO_CLIENT_ID"), os.getenv("VITO_CLIENT_SECRET")))