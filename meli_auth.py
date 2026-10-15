import os
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.environ.get("MELI_CLIENT_ID")
CLIENT_SECRET = os.environ.get("MELI_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("MELI_REDIRECT_URI", "https://api.melicost.com/webhooks/meli")

AUTH_URL = "https://auth.mercadolibre.com.ar/authorization"
TOKEN_URL = "https://api.mercadolibre.com/oauth/token"

def obtener_link_autorizacion():
    return f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"

def intercambiar_code_por_tokens(authorization_code: str):
    payload = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": authorization_code,
        "redirect_uri": REDIRECT_URI
    }
    headers = {"accept": "application/json", "content-type": "application/x-www-form-urlencoded"}
    response = requests.post(TOKEN_URL, data=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error OAuth ({response.status_code}): {response.text}")
