import requests
import streamlit as st

# =========================================================
# OBTENCIÓN SEGURA DE CREDENCIALES DESDE STREAMLIT SECRETS
# =========================================================
# Intenta leer desde st.secrets. Si estás en local sin secretos,
# usa valores por defecto o vacíos para no romper la ejecución.
CLIENT_ID = st.secrets.get("MELI_CLIENT_ID", "")
CLIENT_SECRET = st.secrets.get("MELI_CLIENT_SECRET", "")
REDIRECT_URI = st.secrets.get("MELI_REDIRECT_URI", "https://melicost.streamlit.app/")

# Endpoints oficiales de OAuth 2.0 de Mercado Libre Argentina
AUTH_URL = "https://auth.mercadolibre.com.ar/authorization"
TOKEN_URL = "https://api.mercadolibre.com/oauth/token"


def obtener_link_autorizacion():
    """Genera la URL de autorización OAuth a la que debe redirigirse el usuario.

    Devuelve un enlace para iniciar sesión en Mercado Libre y otorgar permisos.
    """
    if not CLIENT_ID or not REDIRECT_URI:
        st.error(
            "⚠️ Error de configuración: Falta MELI_CLIENT_ID o MELI_REDIRECT_URI en st.secrets."
        )
        return "#"

    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
    }

    # Construye el query string completo
    req_prep = requests.Request("GET", AUTH_URL, params=params).prepare()
    return req_prep.url


def intercambiar_code_por_tokens(auth_code):
    """Intercambia el parámetro 'code' obtenido tras la redirección por un access_token y refresh_token de Mercado Libre.

    :param auth_code: Código de autorización enviado por MeLi en la URL.
    :return: Diccionario JSON con access_token, refresh_token, user_id, etc.
    """
    if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
        raise ValueError(
            "Faltan credenciales en st.secrets (MELI_CLIENT_ID, MELI_CLIENT_SECRET o MELI_REDIRECT_URI)"
        )

    payload = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    response = requests.post(
        TOKEN_URL, data=payload, headers=headers, timeout=10
    )

    if response.status_code == 200:
        return response.json()
    else:
        # Extrae detalles del error devueltos por la API de MeLi
        try:
            error_data = response.json()
            error_msg = error_data.get(
                "message", error_data.get("error", response.text)
            )
        except Exception:
            error_msg = response.text
        raise Exception(
            f"Error al obtener token de MeLi (HTTP {response.status_code}): {error_msg}"
        )


def refrescar_access_token(refresh_token):
    """Renueva un access_token vencido utilizando el refresh_token guardado.

    :param refresh_token: El refresh token previo.
    :return: Diccionario JSON con los nuevos tokens.
    """
    if not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError("Faltan credenciales MELI_CLIENT_ID o MELI_CLIENT_SECRET en st.secrets")

    payload = {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": refresh_token,
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    response = requests.post(
        TOKEN_URL, data=payload, headers=headers, timeout=10
    )

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(
            f"Error al refrescar token (HTTP {response.status_code}): {response.text}"
        )
