import io
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import unquote

import numpy as np
import pandas as pd
import requests
import streamlit as st
from PIL import Image, ImageOps

APP_VERSION = "v195.0"

st.set_page_config(
    page_title=f"NQ Sales Intelligence Matrix Pro ({APP_VERSION})",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------------------
# ESTÉTICA EJECUTIVA SLATE & ESMERALDA - ALTO CONTRASTE Y DENSIDAD DE DATOS
# ------------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .main { background-color: #f8fafc; font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }

    .exec-hero-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #0f2922 100%);
        padding: 14px 22px;
        border-radius: 12px;
        margin-bottom: 12px;
        border-bottom: 3px solid #10b981;
        box-shadow: 0 6px 18px -4px rgba(15, 23, 42, 0.25);
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
        position: relative;
        overflow: hidden;
    }
    .exec-hero-left {
        display: flex;
        align-items: center;
        gap: 14px;
        z-index: 1;
    }
    .exec-logo-badge {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: #ffffff;
        width: 42px;
        height: 42px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 900;
        font-size: 17px;
        letter-spacing: -0.5px;
        box-shadow: 0 3px 10px rgba(16, 185, 129, 0.35);
        flex-shrink: 0;
    }
    .exec-hero-title {
        font-size: 19px;
        font-weight: 800;
        color: #f8fafc;
        margin: 0;
        letter-spacing: -0.4px;
        line-height: 1.1;
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
    }
    .exec-hero-title span {
        color: #34d399;
    }
    .exec-version-tag {
        background: rgba(16, 185, 129, 0.18);
        color: #6ee7b7;
        border: 1px solid rgba(52, 211, 153, 0.45);
        font-size: 11px;
        font-weight: 800;
        padding: 2px 8px;
        border-radius: 999px;
        letter-spacing: 0.2px;
    }
    .exec-hero-subtitle {
        font-size: 11px;
        color: #94a3b8;
        margin-top: 3px;
        font-weight: 400;
    }
    .exec-status-group {
        display: flex;
        gap: 10px;
        align-items: center;
        flex-wrap: wrap;
        z-index: 1;
    }
    .exec-status-pill {
        background: rgba(255, 255, 255, 0.06);
        backdrop-filter: blur(6px);
        border: 1px solid rgba(255, 255, 255, 0.12);
        padding: 6px 12px;
        border-radius: 10px;
        min-width: 118px;
    }
    .exec-pill-lbl {
        font-size: 9px;
        font-weight: 700;
        color: #6ee7b7;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 1px;
    }
    .exec-pill-val {
        font-size: 13px;
        font-weight: 800;
        color: #ffffff;
        display: flex;
        align-items: center;
        gap: 5px;
    }

    h1 { font-size: 20px !important; font-weight: 800 !important; color: #0f172a !important; padding-top: 0px !important; margin-bottom: 2px !important; }
    h2 { font-size: 17px !important; font-weight: 750 !important; color: #1e293b !important; padding-top: 0px !important; margin-bottom: 2px !important; }
    h3 { font-size: 14px !important; font-weight: 700 !important; color: #334155 !important; padding-top: 0px !important; margin-bottom: 2px !important; }

    .stCaptionContainer { font-size: 12px !important; color: #64748b !important; margin-bottom: 6px !important; }

    button[kind="primary"],
    button[data-testid="stBaseButton-primary"],
    a[kind="primary"],
    a[data-testid="stBaseLinkButton-primary"] {
        background-color: #059669 !important;
        border: 1px solid #047857 !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 6px rgba(5, 150, 105, 0.25) !important;
        transition: all 0.2s ease !important;
    }
    button[kind="primary"] p,
    button[data-testid="stBaseButton-primary"] p,
    button[kind="primary"] span,
    button[data-testid="stBaseButton-primary"] span,
    a[kind="primary"] p,
    a[data-testid="stBaseLinkButton-primary"] p {
        color: #ffffff !important;
        font-weight: 700 !important;
    }
    button[kind="primary"]:hover,
    button[data-testid="stBaseButton-primary"]:hover,
    a[kind="primary"]:hover,
    a[data-testid="stBaseLinkButton-primary"]:hover {
        background-color: #047857 !important;
        border-color: #065f46 !important;
        color: #ffffff !important;
        transform: translateY(-1px);
    }

    div[data-testid="stHorizontalBlock"] .nav-btn-wrap button {
        border-radius: 10px !important;
        padding: 8px 6px !important;
        font-weight: 700 !important;
        font-size: 11px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 4px rgba(15, 23, 42, 0.04) !important;
    }
    div[data-testid="stHorizontalBlock"] .nav-btn-active button {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
        color: #ffffff !important;
        border: 1px solid #0f172a !important;
        border-bottom: 3px solid #10b981 !important;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.22) !important;
    }
    div[data-testid="stHorizontalBlock"] .nav-btn-active button p {
        color: #ffffff !important;
    }
    div[data-testid="stHorizontalBlock"] .nav-btn-inactive button {
        background: #ffffff !important;
        color: #334155 !important;
        border: 1px solid #cbd5e1 !important;
    }
    div[data-testid="stHorizontalBlock"] .nav-btn-inactive button p {
        color: #334155 !important;
    }
    div[data-testid="stHorizontalBlock"] .nav-btn-inactive button:hover {
        background: #ecfdf5 !important;
        border-color: #10b981 !important;
        color: #065f46 !important;
        transform: translateY(-1px);
    }
    div[data-testid="stHorizontalBlock"] .nav-btn-inactive button:hover p {
        color: #065f46 !important;
    }

    .kpi-card {
        background: #ffffff;
        padding: 12px 16px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
    }
    .kpi-label { font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.4px; }
    .kpi-value { font-size: 20px; font-weight: 800; color: #0f172a; margin: 2px 0; }

    .card-viable {
        background: #ecfdf5;
        color: #064e3b;
        padding: 12px 16px;
        border-radius: 10px;
        border: 1px solid #a7f3d0;
        font-size: 13px;
        font-weight: 700;
    }
    .card-noviable {
        background: #fef2f2;
        color: #991b1b;
        padding: 12px 16px;
        border-radius: 10px;
        border: 1px solid #fecaca;
        font-size: 13px;
        font-weight: 700;
    }
    .warning-stock {
        background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%);
        color: #9a3412;
        padding: 12px 16px;
        border-radius: 10px;
        border-left: 5px solid #ea580c;
        font-size: 13px;
    }
    .ai-bubble {
        background: #ecfdf5;
        color: #064e3b;
        padding: 14px;
        border-radius: 10px;
        border-left: 5px solid #10b981;
        border: 1px solid #a7f3d0;
        font-size: 13px;
    }
    .badge-missing {
        background-color: #fef2f2;
        color: #991b1b;
        padding: 8px 12px;
        border-radius: 8px;
        font-weight: 700;
        border: 1px solid #fca5a5;
        font-size: 12px;
    }
    .mla-focus-box {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border: 1px solid #cbd5e1;
        border-left: 5px solid #0284c7;
        padding: 14px 18px;
        border-radius: 10px;
        margin-bottom: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------------------
# CONFIGURACIÓN GLOBAL, IMPUESTOS Y ESTADO DE SESIÓN
# ------------------------------------------------------------------------------
CLIENT_ID = st.secrets.get("MELI_CLIENT_ID", "7265495583900621")
CLIENT_SECRET = st.secrets.get("MELI_CLIENT_SECRET", "")
REDIRECT_URI = st.secrets.get("REDIRECT_URI", "https://melicost.streamlit.app").strip().rstrip("/")

ALICUOTA_IVA = 0.21
ALICUOTA_IIBB = 0.035
TOTAL_IMPUESTOS = ALICUOTA_IVA + ALICUOTA_IIBB

SESSION_DEFAULTS: Dict[str, Any] = {
    "tasas_cuotas": {
        "1 Pago / Clásica": {"comision_base": 0.145, "tasa_finan": 0.000},
        "3 Cuotas Sin Interés": {"comision_base": 0.145, "tasa_finan": 0.085},
        "6 Cuotas Sin Interés": {"comision_base": 0.145, "tasa_finan": 0.129},
        "9 Cuotas Sin Interés": {"comision_base": 0.145, "tasa_finan": 0.173},
        "12 Cuotas Sin Interés": {"comision_base": 0.145, "tasa_finan": 0.208},
    },
    "access_token": "",
    "refresh_token": "",
    "user_info": {},
    "lista_gold_df": None,
    "matriz_custom_df": None,
    "q_costos": "7798009181204",
    "search_query_mon": "7798009181204",
    "q_builder": "MLA65326966",
    "q_mercado_mla": "MLA1456789012",
    "q_diag_api": "7798009181204",
    "active_tab": 0,
    "tarifas_actualizadas_api": False,
}

for k, v in SESSION_DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ------------------------------------------------------------------------------
# CLIENTE HTTP CON REINTENTOS Y MANEJO DE RATE-LIMIT (429 / 5XX)
# ------------------------------------------------------------------------------
def http_get_con_reintentos(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 8,
    max_reintentos: int = 2,
    backoff_base: float = 0.4,
) -> Optional[requests.Response]:
    ultimo_resp: Optional[requests.Response] = None
    for intento in range(max_reintentos + 1):
        try:
            resp = requests.get(url, headers=headers or {}, timeout=timeout)
            ultimo_resp = resp
            if resp.status_code in (429, 500, 502, 503, 504) and intento < max_reintentos:
                retry_after = resp.headers.get("Retry-After")
                try:
                    espera = float(retry_after) if retry_after else backoff_base * (2 ** intento)
                except ValueError:
                    espera = backoff_base * (2 ** intento)
                time.sleep(min(espera, 3.0))
                continue
            return resp
        except requests.RequestException:
            if intento < max_reintentos:
                time.sleep(backoff_base * (2 ** intento))
                continue
            return None
    return ultimo_resp


def get_meli_headers(token: str = "") -> Dict[str, str]:
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0",
    }
    if token and token.strip():
        headers["Authorization"] = f"Bearer {token.strip()}"
    return headers


def get_web_headers() -> Dict[str, str]:
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-AR,es;q=0.9",
    }


def obtener_url_login_meli() -> str:
    return f"https://auth.mercadolibre.com.ar/authorization?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"


def intercambiar_code_por_token(code: str) -> Tuple[bool, Any]:
    url = "https://api.mercadolibre.com/oauth/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
    try:
        res = requests.post(url, data=payload, headers=headers, timeout=10)
        if res.status_code == 200:
            return True, res.json()
        err_data = res.json() if res.content else {}
        return False, err_data.get("message", f"Error HTTP {res.status_code}")
    except Exception as e:
        return False, str(e)


def refrescar_access_token_meli(refresh_token: str) -> Tuple[bool, str]:
    if not refresh_token or not CLIENT_SECRET:
        return False, "Falta refresh_token o MELI_CLIENT_SECRET."
    url = "https://api.mercadolibre.com/oauth/token"
    payload = {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": refresh_token.strip(),
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
    try:
        res = requests.post(url, data=payload, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            new_tok = data.get("access_token", "")
            if new_tok:
                st.session_state["access_token"] = new_tok
                if data.get("refresh_token"):
                    st.session_state["refresh_token"] = data["refresh_token"]
                return True, new_tok
        return False, f"HTTP {res.status_code}"
    except Exception as e:
        return False, str(e)


def obtener_perfil_meli(token: str) -> Dict[str, Any]:
    if not token:
        return {}
    url = "https://api.mercadolibre.com/users/me"
    res = http_get_con_reintentos(url, headers=get_meli_headers(token), timeout=5, max_reintentos=1)
    if res is not None and res.status_code == 200:
        return res.json()
    return {}


def sincronizar_tarifas_financiacion_meli(token: str = "") -> None:
    url_listing = "https://api.mercadolibre.com/sites/MLA/listing_types"
    res = http_get_con_reintentos(url_listing, headers=get_meli_headers(token), timeout=6, max_reintentos=1)
    if res is not None and res.status_code == 200:
        st.session_state["tarifas_actualizadas_api"] = True


query_params = st.query_params
code_auth = query_params.get("code", None)

if code_auth and not st.session_state["access_token"]:
    with st.spinner("Autenticando con Mercado Libre y actualizando tarifas..."):
        exito, token_resp = intercambiar_code_por_token(code_auth)
        if exito:
            st.session_state["access_token"] = token_resp.get("access_token", "")
            st.session_state["refresh_token"] = token_resp.get("refresh_token", "")
            st.session_state["user_info"] = obtener_perfil_meli(st.session_state["access_token"])
            sincronizar_tarifas_financiacion_meli(st.session_state["access_token"])
            st.query_params.clear()
            st.rerun()

if st.session_state["access_token"] and not st.session_state["tarifas_actualizadas_api"]:
    sincronizar_tarifas_financiacion_meli(st.session_state["access_token"])


# ------------------------------------------------------------------------------
# CATEGORÍAS Y PREDICCIÓN DE DOMINIO MELI
# ------------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def obtener_nombre_categoria_meli(category_id: str) -> str:
    if not category_id or not str(category_id).startswith("MLA"):
        return category_id
    res = http_get_con_reintentos(f"https://api.mercadolibre.com/categories/{category_id}", headers=get_meli_headers(), timeout=5)
    if res is not None and res.status_code == 200:
        data = res.json()
        path_from_root = data.get("path_from_root", [])
        nombres = [cat.get("name", "") for cat in path_from_root if cat.get("name")]
        if nombres:
            return " > ".join(nombres)
        return data.get("name", category_id)
    return category_id


@st.cache_data(ttl=1800)
def predecir_categorias_meli(titulo_producto: str) -> List[Tuple[str, str]]:
    if not titulo_producto or len(titulo_producto.strip()) < 3:
        return []
    sugerencias: List[Tuple[str, str]] = []
    url_pred = f"https://api.mercadolibre.com/sites/MLA/domain_discovery/search?limit=5&q={requests.utils.quote(titulo_producto.strip())}"
    res = http_get_con_reintentos(url_pred, headers=get_meli_headers(), timeout=6)
    if res is not None and res.status_code == 200:
        for entry in res.json():
            cat_id = entry.get("category_id")
            if cat_id and cat_id not in [s[0] for s in sugerencias]:
                ruta = obtener_nombre_categoria_meli(cat_id)
                sugerencias.append((cat_id, ruta))
    return sugerencias


# ------------------------------------------------------------------------------
# CARGA Y PARSEO DE LISTA GOLD Y MATRIZ LOGÍSTICA
# ------------------------------------------------------------------------------
def procesar_archivo_lista_gold(file) -> Optional[pd.DataFrame]:
    try:
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        if not any("ean" in str(c).lower() for c in df.columns):
            for i in range(min(5, len(df))):
                row_vals = [str(x).lower() for x in df.iloc[i].values]
                if any("ean" in v for v in row_vals):
                    if file.name.endswith(".csv"):
                        df = pd.read_csv(file, header=i + 1)
                    else:
                        df = pd.read_excel(file, header=i + 1)
                    break
        return df
    except Exception as e:
        st.error(f"Error al procesar archivo: {e}")
        return None


def calcular_costo_envio_por_peso_facturable(peso_facturable: float, pvp: float = 208000.0) -> float:
    peso = float(peso_facturable) if pd.notna(peso_facturable) and peso_facturable > 0 else 10.0
    pvp_val = float(pvp) if pd.notna(pvp) and pvp > 0 else 208000.0

    if pvp_val < 33000:
        col_idx = 0
    elif 33000 <= pvp_val < 50000:
        col_idx = 1
    else:
        col_idx = 2

    if peso <= 0.3:      costos = (8666, 6190, 6790)
    elif peso <= 0.5:    costos = (9506, 6790, 7290)
    elif peso <= 1.0:    costos = (10906, 7790, 8290)
    elif peso <= 1.5:    costos = (11186, 7990, 8590)
    elif peso <= 2.0:    costos = (11606, 8290, 8790)
    elif peso <= 3.0:    costos = (12446, 8890, 9590)
    elif peso <= 4.0:    costos = (13706, 9790, 10890)
    elif peso <= 5.0:    costos = (15106, 10790, 11890)
    elif peso <= 8.0:    costos = (16506, 11790, 13090)
    elif peso <= 10.0:   costos = (17906, 12790, 14190)
    elif peso <= 13.0:   costos = (19306, 13790, 15190)
    elif peso <= 15.0:   costos = (20706, 14790, 16290)
    elif peso <= 20.0:   costos = (24626, 17590, 19390)
    elif peso <= 25.0:   costos = (29246, 20890, 23390)
    elif peso <= 30.0:   costos = (40026, 28590, 32090)
    elif peso <= 40.0:   costos = (45626, 32590, 36990)
    elif peso <= 50.0:   costos = (48146, 34390, 39090)
    elif peso <= 60.0:   costos = (53326, 38090, 43590)
    elif peso <= 70.0:   costos = (55426, 39590, 45490)
    elif peso <= 80.0:   costos = (64106, 45790, 52690)
    elif peso <= 90.0:   costos = (78946, 56390, 65190)
    elif peso <= 100.0:  costos = (90986, 64990, 75090)
    elif peso <= 120.0:  costos = (99246, 70890, 81990)
    elif peso <= 140.0:  costos = (111706, 79790, 92290)
    elif peso <= 160.0:  costos = (124166, 88690, 102690)
    elif peso <= 180.0:  costos = (136486, 97490, 112990)
    else:                costos = (148946, 106390, 123290)

    return float(costos[col_idx])


def parsear_valor_cm(val_str: str, default_cm: float = 0.0) -> float:
    if not val_str:
        return default_cm
    s = str(val_str).lower().strip()
    m = re.search(r"(\d+(?:[.,]\d+)?)", s)
    if not m:
        return default_cm
    num = float(m.group(1).replace(",", "."))
    if "mm" in s:
        return num / 10.0
    if re.search(r"\bm\b", s) and "cm" not in s and "mm" not in s:
        return num * 100.0
    return num


def parsear_valor_kg(val_str: str, default_kg: float = 0.0) -> float:
    if not val_str:
        return default_kg
    s = str(val_str).lower().strip()
    m = re.search(r"(\d+(?:[.,]\d+)?)", s)
    if not m:
        return default_kg
    num = float(m.group(1).replace(",", "."))
    if "g" in s and "kg" not in s:
        return num / 1000.0
    return num


def calcular_flete_desde_embalaje(
    alto_str: str, ancho_str: str, prof_str: str, peso_str: str, pvp: float
) -> Tuple[float, float, float, bool]:
    alto_cm = parsear_valor_cm(alto_str, 0.0)
    ancho_cm = parsear_valor_cm(ancho_str, 0.0)
    prof_cm = parsear_valor_cm(prof_str, 0.0)
    peso_real_kg = parsear_valor_kg(peso_str, 0.0)

    peso_vol_kg = round((alto_cm * ancho_cm * prof_cm) / 4000.0, 2) if (alto_cm > 0 and ancho_cm > 0 and prof_cm > 0) else 0.0
    peso_facturable = max(peso_real_kg, peso_vol_kg)

    if peso_facturable <= 0:
        return 0.0, 0.0, 0.0, False

    costo_env = calcular_costo_envio_por_peso_facturable(peso_facturable, pvp)
    return costo_env, peso_facturable, peso_vol_kg, True


def procesar_matriz_articulos_df(df: pd.DataFrame, pvp_referencia: float = 208000.0) -> pd.DataFrame:
    try:
        df = df.copy()
        df["Ancho_cm"] = pd.to_numeric(df.get("Ancho caja (mm)", 0), errors="coerce").fillna(0) / 10
        df["Alto_cm"] = pd.to_numeric(df.get("Alto caja (mm)", 0), errors="coerce").fillna(0) / 10
        df["Prof_cm"] = pd.to_numeric(df.get("Prof caja (mm)", 0), errors="coerce").fillna(0) / 10
        df["Volumen_cm3"] = df["Ancho_cm"] * df["Alto_cm"] * df["Prof_cm"]
        df["Peso_Volumetrico_Kg"] = (df["Volumen_cm3"] / 4000).round(2)
        peso_emb = pd.to_numeric(df.get("Peso embalado (Kg)", 0), errors="coerce").fillna(0)
        df["Peso_Facturable_Kg"] = np.maximum(peso_emb, df["Peso_Volumetrico_Kg"])
        df["Costo_Logistico_Estimado"] = df["Peso_Facturable_Kg"].apply(
            lambda x: calcular_costo_envio_por_peso_facturable(x, pvp_referencia)
        )
        return df
    except Exception:
        return df


def cargar_matriz_articulos_oficial(pvp_referencia: float = 208000.0) -> Optional[pd.DataFrame]:
    if st.session_state["matriz_custom_df"] is not None:
        return procesar_matriz_articulos_df(st.session_state["matriz_custom_df"], pvp_referencia)
    for file_path in ["Matriz Articulos Gemini - COTIZADOR PVP.xlsx", "Matriz Articulos Gemini.xlsx"]:
        if os.path.exists(file_path):
            try:
                df = pd.read_excel(file_path)
                return procesar_matriz_articulos_df(df, pvp_referencia)
            except Exception:
                pass
    return None


def buscar_datos_en_matriz(clave_busqueda: str, pvp_referencia: float = 208000.0) -> Tuple[bool, float, float, float, float, int, str]:
    matriz_df = cargar_matriz_articulos_oficial(pvp_referencia)
    if matriz_df is None:
        return False, 39090.0, 10.0, 10.0, 39090.0, 1, ""

    q_clean = re.sub(r"\D", "", str(clave_busqueda).strip())
    q_raw = str(clave_busqueda).strip().lower()

    for col in ["ean", "Articulo"]:
        if col in matriz_df.columns:
            series_clean = (
                matriz_df[col]
                .fillna("")
                .astype(str)
                .str.split(".")
                .str[0]
                .str.replace(r"\D", "", regex=True)
            )
            matches = matriz_df[series_clean == q_clean] if q_clean else pd.DataFrame()
            if matches.empty and q_raw:
                matches = matriz_df[matriz_df[col].astype(str).str.lower().str.contains(q_raw, na=False, regex=False)]

            if not matches.empty:
                row = matches.iloc[0]
                peso_fact_total = float(row.get("Peso_Facturable_Kg", row.get("Peso embalado (Kg)", 10.0)))
                raw_cajas = row.get("Cajas por unidades", row.get("Cantidad Cajas", 1))
                cant_cajas = int(raw_cajas) if pd.notna(raw_cajas) and int(raw_cajas) > 0 else 1

                peso_unitario = peso_fact_total / cant_cajas if cant_cajas > 0 else peso_fact_total
                tarifa_unit = calcular_costo_envio_por_peso_facturable(peso_unitario, pvp_referencia)
                costo_env_total = tarifa_unit * cant_cajas

                desc = str(row.get("Descripcion", ""))
                return True, costo_env_total, peso_unitario, peso_fact_total, tarifa_unit, cant_cajas, desc

    return False, 39090.0, 10.0, 10.0, 39090.0, 1, ""


def buscar_datos_en_matriz_completa(clave_busqueda: str) -> Tuple[str, str, str, str]:
    matriz_df = cargar_matriz_articulos_oficial()
    if matriz_df is None:
        return "120 cm", "60 cm", "30 cm", "10.0 kg"

    q_clean = re.sub(r"\D", "", str(clave_busqueda).strip())
    q_raw = str(clave_busqueda).strip().lower()

    for col in ["ean", "Articulo"]:
        if col in matriz_df.columns:
            series_clean = (
                matriz_df[col]
                .fillna("")
                .astype(str)
                .str.split(".")
                .str[0]
                .str.replace(r"\D", "", regex=True)
            )
            matches = matriz_df[series_clean == q_clean] if q_clean else pd.DataFrame()
            if matches.empty and q_raw:
                matches = matriz_df[matriz_df[col].astype(str).str.lower().str.contains(q_raw, na=False, regex=False)]

            if not matches.empty:
                row = matches.iloc[0]
                ancho = f"{row.get('Ancho_cm', 120)} cm"
                alto = f"{row.get('Alto_cm', 60)} cm"
                prof = f"{row.get('Prof_cm', 30)} cm"
                peso = f"{row.get('Peso_Facturable_Kg', 10.0)} kg"
                return ancho, alto, prof, peso

    return "120 cm", "60 cm", "30 cm", "10.0 kg"


def extraer_opciones_ean_lista_gold() -> List[Tuple[str, str]]:
    if st.session_state["lista_gold_df"] is None:
        return []
    df = st.session_state["lista_gold_df"]
    opciones: List[Tuple[str, str]] = []
    ean_col = next((c for c in df.columns if any(k in str(c).lower() for k in ["ean", "gtin", "codigo", "código"])), None)
    desc_col = next((c for c in df.columns if any(k in str(c).lower() for k in ["descrip", "nombre", "titulo", "producto"])), None)
    art_col = next((c for c in df.columns if any(k in str(c).lower() for k in ["articul", "modelo"])), None)

    if not ean_col:
        return []

    for _, row in df.iterrows():
        val_ean = re.sub(r"\D", "", str(row[ean_col]).split(".")[0])
        if len(val_ean) >= 6:
            desc = str(row[desc_col]) if desc_col and pd.notna(row[desc_col]) else ""
            art = str(row[art_col]) if art_col and pd.notna(row[art_col]) else ""
            label = f"{val_ean} — {art} {desc}".strip()
            opciones.append((label, val_ean))
    return opciones


def limpiar_precio_moneda(valor_raw: Any) -> float:
    if pd.isna(valor_raw):
        return 0.0
    val_str = str(valor_raw).strip().replace("$", "").strip()
    if "," in val_str and "." in val_str:
        val_str = val_str.replace(".", "").replace(",", ".")
    elif "." in val_str and "," not in val_str:
        partes = val_str.split(".")
        if len(partes[-1]) == 3:
            val_str = val_str.replace(".", "")
        else:
            val_str = val_str.replace(",", ".")
    elif "," in val_str:
        val_str = val_str.replace(",", ".")
    try:
        return float(val_str)
    except Exception:
        return 0.0


def buscar_costo_y_titulo_en_lista_gold(clave_busqueda: str) -> Tuple[bool, float, str, str]:
    if st.session_state["lista_gold_df"] is None:
        return False, 0.0, "", ""

    df = st.session_state["lista_gold_df"]
    q_clean = re.sub(r"\D", "", str(clave_busqueda).strip())
    q_raw = str(clave_busqueda).strip().lower()

    for col in df.columns:
        col_str = str(col).lower()
        if any(term in col_str for term in ["ean", "sku", "codigo", "código", "articulo", "artículo", "gtin"]):
            series_clean = (
                df[col]
                .fillna("")
                .astype(str)
                .str.split(".")
                .str[0]
                .str.replace(r"\D", "", regex=True)
            )
            matches = df[series_clean == q_clean] if (q_clean and len(q_clean) >= 6) else pd.DataFrame()
            if matches.empty and q_raw:
                matches = df[df[col].astype(str).str.lower().str.contains(q_raw, na=False, regex=False)]

            if not matches.empty:
                cost_cols = [c for c in df.columns if any(k in str(c).lower() for k in ["costo", "precio", "lista", "valor"])]
                val_col = cost_cols[0] if cost_cols else df.columns[-1]

                desc_cols = [c for c in df.columns if any(k in str(c).lower() for k in ["descrip", "nombre", "titulo", "producto"])]
                desc_val = str(matches.iloc[0][desc_cols[0]]) if desc_cols else ""

                art_cols = [c for c in df.columns if any(k in str(c).lower() for k in ["articul", "modelo", "codigo"])]
                art_val = str(matches.iloc[0][art_cols[0]]) if art_cols and pd.notna(matches.iloc[0][art_cols[0]]) else ""

                costo_parsed = limpiar_precio_moneda(matches.iloc[0][val_col])
                return True, costo_parsed, desc_val, art_val

    return False, 0.0, "", ""


# ------------------------------------------------------------------------------
# PARSEO DE IDENTIFICADORES MELI Y RESOLUCIÓN DE VENDEDORES
# ------------------------------------------------------------------------------
def extraer_ids_meli_avanzado(input_raw: str) -> Dict[str, str]:
    raw = unquote(input_raw.strip())
    res = {
        "tipo": "TEXT",
        "catalog_id": "",
        "item_id": "",
        "alt_item_id": "",
        "ean": "",
        "url_original": raw if raw.startswith("http") else "",
        "raw": raw,
    }

    cat_match = re.search(r"/p/(MLA[A-Z]?\d+)", raw, re.IGNORECASE)
    if cat_match:
        res["catalog_id"] = cat_match.group(1).upper()
        res["tipo"] = "MELI_URL_OR_ID"

    item_match = re.search(r"(?:item_id=|wid=|/up/|/)(MLA-?[A-Z]?\d+)", raw, re.IGNORECASE)
    if item_match:
        clean_it = item_match.group(1).upper().replace("-", "")
        res["item_id"] = clean_it
        res["tipo"] = "MELI_URL_OR_ID"

    if not res["catalog_id"] and not res["item_id"]:
        direct_mla = re.match(r"^(MLA-?[A-Z]?\d+)$", raw, re.IGNORECASE)
        if direct_mla:
            clean_mla = direct_mla.group(1).upper().replace("-", "")
            res["tipo"] = "MELI_URL_OR_ID"
            res["item_id"] = clean_mla
            if clean_mla.startswith("MLAU"):
                res["catalog_id"] = clean_mla

    for key_id in ["item_id", "catalog_id"]:
        val_id = res[key_id]
        if val_id and re.match(r"^MLA[A-Z]\d+$", val_id):
            num_only = re.sub(r"^MLA[A-Z]", "MLA", val_id)
            if not res["alt_item_id"]:
                res["alt_item_id"] = num_only

    if res["tipo"] == "MELI_URL_OR_ID":
        return res

    if re.fullmatch(r"[\d\s\-\.]+", raw):
        clean_digits = re.sub(r"\D", "", raw)
        if len(clean_digits) >= 8:
            res["tipo"] = "EAN"
            res["ean"] = clean_digits
            return res

    return res


def extraer_id_catalogo_o_ean_input(input_raw: str) -> Tuple[str, str]:
    parsed = extraer_ids_meli_avanzado(input_raw)
    if parsed["tipo"] == "MELI_URL_OR_ID":
        return "CATALOG_ID", parsed["catalog_id"] or parsed["item_id"]
    if parsed["tipo"] == "EAN":
        return "EAN", parsed["ean"]
    return "TEXT", parsed["raw"]


def construir_url_canonica_meli(raw_id: str, permalink_api: str = "", catalog_id: str = "") -> str:
    if permalink_api and str(permalink_api).strip().startswith("http"):
        return str(permalink_api).strip()
    clean_id = str(raw_id or "").strip().upper()
    if clean_id.startswith("MLAU"):
        return f"https://www.mercadolibre.com.ar/p/{clean_id}"
    if clean_id.startswith("MLA"):
        num_part = re.sub(r"\D", "", clean_id)
        if num_part:
            return f"https://articulo.mercadolibre.com.ar/MLA-{num_part}"
    clean_cat = str(catalog_id or "").strip().upper()
    if clean_cat.startswith("MLA"):
        return f"https://www.mercadolibre.com.ar/p/{clean_cat}"
    return ""


@st.cache_data(ttl=3600)
def resolver_vendedor_nickname_oficial(seller_id: Any, access_token: str = "") -> str:
    if not seller_id or str(seller_id) in ["N/A", "None", "", "0"]:
        return "Vendedor Mercado Libre"
    url = f"https://api.mercadolibre.com/users/{seller_id}"
    res = http_get_con_reintentos(url, headers=get_meli_headers(access_token), timeout=4, max_reintentos=1)
    if res is not None and res.status_code == 200:
        data = res.json()
        eshop = data.get("eshop", {})
        if isinstance(eshop, dict) and eshop.get("eshop_name"):
            return eshop.get("eshop_name").strip()
        nick = data.get("nickname")
        if nick:
            return nick.strip().replace("_", " ").title()
    return f"Vendedor #{seller_id}"


# ------------------------------------------------------------------------------
# RESPALDO WEB PÚBLICO REFORZADO PARA MONITOR / COMPETENCIA
# ------------------------------------------------------------------------------
def extraer_competencia_web_publica(
    catalog_id: str, variantes: List[str], diagnostico: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    urls_candidatas: List[Tuple[str, str]] = []
    if catalog_id:
        urls_candidatas.append((f"catálogo {catalog_id}", f"https://www.mercadolibre.com.ar/p/{catalog_id}"))

    for var_q in variantes[:4]:
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", str(var_q).strip().lower()).strip("-")
        if slug:
            urls_candidatas.append((f"listado '{var_q}'", f"https://listado.mercadolibre.com.ar/{slug}"))

    headers_web = get_web_headers()
    encontrados: List[Dict[str, Any]] = []
    vistos: set = set()

    for etiqueta, url_obj in urls_candidatas:
        try:
            resp = requests.get(url_obj, headers=headers_web, timeout=10, allow_redirects=True)
            if diagnostico is not None:
                diagnostico.append(f"Web {etiqueta} -> HTTP {resp.status_code} ({len(resp.text or '')} bytes)")
            if resp.status_code != 200 or len(resp.text) < 1500:
                continue

            html = resp.text
            bloques_mla = re.findall(r"(MLA-?\d{6,14})", html)
            precios_raw = re.findall(r'"price"\s*:\s*(\d+(?:\.\d+)?)', html)
            if not precios_raw:
                precios_raw = re.findall(r'"amount"\s*:\s*(\d+(?:\.\d+)?)', html)
            if not precios_raw:
                precios_pesos = re.findall(
                    r'class="[^"]*price-tag-amount[^"]*"[^>]*>.*?<span[^>]*class="[^"]*andes-money-amount__fraction[^"]*"[^>]*>([\d.]+)</span>',
                    html,
                    re.DOTALL,
                )
                precios_raw = [p.replace(".", "") for p in precios_pesos if p.replace(".", "").isdigit()]
            if not precios_raw:
                fracciones = re.findall(r'class="andes-money-amount__fraction"[^>]*>([\d.]+)<', html)
                precios_raw = [p.replace(".", "") for p in fracciones if p.replace(".", "").isdigit()]

            titulos_raw = re.findall(r'"title"\s*:\s*"([^"]{6,140})"', html)
            if not titulos_raw:
                h1_matches = re.findall(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
                titulos_raw = [re.sub(r"<[^>]+>", "", h).strip() for h in h1_matches if len(re.sub(r"<[^>]+>", "", h).strip()) > 4]

            if diagnostico is not None:
                diagnostico.append(
                    f"Parse web {etiqueta}: MLA={len(bloques_mla)}, precios={len(precios_raw)}, titulos={len(titulos_raw)}"
                )

            for idx_p, p_str in enumerate(precios_raw[:25]):
                try:
                    precio_val = float(p_str)
                except ValueError:
                    continue
                if precio_val <= 100:
                    continue

                item_raw = bloques_mla[idx_p].replace("-", "") if idx_p < len(bloques_mla) else (catalog_id or f"WEB-{idx_p+1}")
                titulo_val = titulos_raw[idx_p] if idx_p < len(titulos_raw) else (variantes[0] if variantes else "Publicación Mercado Libre")
                clave_dedup = (item_raw, precio_val)
                if clave_dedup in vistos:
                    continue
                vistos.add(clave_dedup)

                encontrados.append(
                    {
                        "vendedor_name": "Mercado Libre (Web Pública)",
                        "id": item_raw,
                        "title": titulo_val,
                        "price": precio_val,
                        "installments_qty": 1,
                        "listing_type_id": "gold_pro",
                        "stock": 0,
                        "sold_quantity": 0,
                        "permalink": construir_url_canonica_meli(item_raw, "", catalog_id),
                        "category_id": "MLA4765",
                    }
                )

            if encontrados:
                break
        except Exception as exc:
            if diagnostico is not None:
                diagnostico.append(f"Web {etiqueta} -> error {exc}")

    return encontrados


# ------------------------------------------------------------------------------
# FUNCIONES PARA COMPLETADO DE MATRIZ (.XLSX) DESDE API DE MELI
# ------------------------------------------------------------------------------
def normalizar_ean_matriz(valor: Any) -> str:
    if pd.isna(valor):
        return ""
    s = str(valor).strip()
    if re.fullmatch(r"\d+(?:\.0+)?", s):
        s = s.split(".")[0]
    return re.sub(r"\D", "", s)


def calcular_peso_facturable_fila_matriz(row: pd.Series) -> float:
    peso_real = pd.to_numeric(row.get("Peso embalado (Kg)", 0.0), errors="coerce")
    peso_real = float(peso_real) if pd.notna(peso_real) and peso_real > 0 else 0.0

    ancho_mm = pd.to_numeric(row.get("Ancho caja (mm)", 0.0), errors="coerce")
    alto_mm = pd.to_numeric(row.get("Alto caja (mm)", 0.0), errors="coerce")
    prof_mm = pd.to_numeric(row.get("Prof caja (mm)", 0.0), errors="coerce")

    peso_vol = 0.0
    if pd.notna(ancho_mm) and pd.notna(alto_mm) and pd.notna(prof_mm) and ancho_mm > 0 and alto_mm > 0 and prof_mm > 0:
        ancho_cm = float(ancho_mm) / 10.0
        alto_cm = float(alto_mm) / 10.0
        prof_cm = float(prof_mm) / 10.0
        peso_vol = round((ancho_cm * alto_cm * prof_cm) / 4000.0, 2)

    return max(peso_real, peso_vol)


def mapear_tipo_envio_meli(logistic_type: str, free_shipping: bool = False) -> str:
    lt = str(logistic_type or "").lower().strip()
    if lt == "fulfillment":
        return "FULL"
    if lt in ("xd_drop_off", "cross_docking", "drop_off"):
        return "ME2"
    if lt in ("self_service",):
        return "FLEX"
    if lt in ("custom",):
        return "ME1"
    if lt in ("not_specified", ""):
        return "ME2" if free_shipping else "ME1"
    return lt.upper()


def obtener_tasa_cuotas_session(cuotas: int) -> float:
    tasas = st.session_state.get("tasas_cuotas", {})
    clave_map = {
        3: "3 Cuotas Sin Interés",
        6: "6 Cuotas Sin Interés",
        9: "9 Cuotas Sin Interés",
        12: "12 Cuotas Sin Interés",
    }
    defaults = {3: 0.085, 6: 0.129, 9: 0.173, 12: 0.208}
    nombre = clave_map.get(cuotas, "")
    if nombre in tasas and isinstance(tasas[nombre], dict):
        return float(tasas[nombre].get("tasa_finan", defaults.get(cuotas, 0.0)))
    return float(defaults.get(cuotas, 0.0))


def calcular_pvp_en_cuotas(pvp_base: float, cuotas: int, ofertas: Optional[List[Dict[str, Any]]] = None) -> float:
    if pd.isna(pvp_base) or float(pvp_base) <= 0:
        return np.nan

    if ofertas:
        for of in ofertas:
            inst = of.get("installments")
            if isinstance(inst, dict) and int(inst.get("quantity") or 0) == cuotas and float(of.get("price") or 0) > 0:
                return round(float(of["price"]), 2)

    tasa_fin = obtener_tasa_cuotas_session(cuotas)
    return round(float(pvp_base) * (1.0 + tasa_fin), 2)


def consultar_ofertas_ean_para_matriz(ean: str, descripcion: str, headers: Dict[str, str]) -> List[Dict[str, Any]]:
    ofertas: List[Dict[str, Any]] = []
    r_prod = http_get_con_reintentos(
        f"https://api.mercadolibre.com/products/search?status=active&site_id=MLA&product_identifier={ean}",
        headers=headers,
        timeout=8,
    )
    if r_prod is not None and r_prod.status_code == 200:
        for prod in (r_prod.json().get("results", []) or [])[:2]:
            cat_id = prod.get("id", "")
            prod_permalink = prod.get("permalink", "")
            if not cat_id:
                continue
            r_items = http_get_con_reintentos(
                f"https://api.mercadolibre.com/products/{cat_id}/items",
                headers=headers,
                timeout=8,
            )
            if r_items is not None and r_items.status_code == 200:
                for it in r_items.json().get("results", []) or []:
                    p = it.get("price")
                    if p and float(p) > 0:
                        ship = it.get("shipping") or {}
                        item_id = it.get("item_id") or it.get("id") or ""
                        raw_link = it.get("permalink") or prod_permalink or ""
                        link_final = construir_url_canonica_meli(item_id, raw_link, cat_id)
                        ofertas.append(
                            {
                                "price": float(p),
                                "item_id": item_id,
                                "catalog_id": cat_id,
                                "permalink": link_final,
                                "seller_id": it.get("seller_id") or (it.get("seller") or {}).get("id"),
                                "logistic_type": ship.get("logistic_type", ""),
                                "free_shipping": bool(ship.get("free_shipping", False)),
                                "installments": it.get("installments") if isinstance(it.get("installments"), dict) else {},
                            }
                        )

    if not ofertas:
        consultas = [ean]
        if descripcion and str(descripcion).strip():
            consultas.append(" ".join(str(descripcion).strip().split()[:5]))

        for q in consultas:
            r_s = http_get_con_reintentos(
                f"https://api.mercadolibre.com/sites/MLA/search?q={requests.utils.quote(q)}&limit=15",
                headers=headers,
                timeout=8,
            )
            if r_s is not None and r_s.status_code == 200:
                for it in r_s.json().get("results", []) or []:
                    p = it.get("price")
                    if p and float(p) > 0:
                        ship = it.get("shipping") or {}
                        item_id = it.get("item_id") or it.get("id") or ""
                        cat_id = it.get("catalog_product_id") or ""
                        raw_link = it.get("permalink") or ""
                        link_final = construir_url_canonica_meli(item_id, raw_link, cat_id)
                        ofertas.append(
                            {
                                "price": float(p),
                                "item_id": item_id,
                                "catalog_id": cat_id,
                                "permalink": link_final,
                                "seller_id": it.get("seller_id") or (it.get("seller") or {}).get("id"),
                                "logistic_type": ship.get("logistic_type", ""),
                                "free_shipping": bool(ship.get("free_shipping", False)),
                                "installments": it.get("installments") if isinstance(it.get("installments"), dict) else {},
                            }
                        )
                if ofertas:
                    break

    ofertas.sort(key=lambda x: x["price"])
    return ofertas


def dataframe_a_excel_bytes(df: pd.DataFrame, sheet_name: str = "Hoja1") -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name[:31])
    output.seek(0)
    return output.getvalue()


# ------------------------------------------------------------------------------
# BUSCADOR VISUAL POR IMAGEN SIMILAR
# ------------------------------------------------------------------------------
def calcular_firma_visual_robusta(img_bytes: bytes) -> Optional[np.ndarray]:
    if not img_bytes:
        return None
    try:
        with Image.open(io.BytesIO(img_bytes)) as im:
            rgb = ImageOps.exif_transpose(im).convert("RGB")
            w, h = rgb.size
            if w > 10 and h > 10:
                margin_x = int(w * 0.06)
                margin_y = int(h * 0.06)
                rgb = rgb.crop((margin_x, margin_y, w - margin_x, h - margin_y))

            grid = np.asarray(rgb.resize((8, 8), Image.Resampling.BILINEAR), dtype=np.float32) / 255.0
            grid_vec = grid.flatten()

            small = np.asarray(rgb.resize((32, 32), Image.Resampling.BILINEAR), dtype=np.float32)
            bins = np.clip((small // 64.0).astype(np.int32), 0, 3)
            idx = bins[:, :, 0] * 16 + bins[:, :, 1] * 4 + bins[:, :, 2]
            hist = np.bincount(idx.flatten(), minlength=64).astype(np.float32)
            if hist.sum() > 0:
                hist /= hist.sum()

            vec = np.concatenate([grid_vec * 0.65, hist * 0.35])
            norm = np.linalg.norm(vec)
            return vec / norm if norm > 0 else None
    except Exception:
        return None


@st.cache_data(ttl=1800)
def obtener_firma_miniatura_url(img_url: str) -> Optional[np.ndarray]:
    if not img_url or not str(img_url).startswith("http"):
        return None
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    }
    resp = http_get_con_reintentos(str(img_url).strip(), headers=headers, timeout=6, max_reintentos=1)
    if resp is not None and resp.status_code == 200 and resp.content:
        return calcular_firma_visual_robusta(resp.content)
    return None


def consultar_items_meli_con_diagnostico(
    consulta: str, access_token: str = "", limit: int = 50
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    headers = get_meli_headers(access_token)
    q = (consulta or "").strip()
    diag: Dict[str, Any] = {
        "status_code": None,
        "endpoint_usado": "",
        "error": "",
        "total_api": 0,
    }

    if not q:
        diag["error"] = "Ingresá una palabra clave o tipo de producto."
        return [], diag

    recolectados: List[Dict[str, Any]] = []
    seen_ids = set()
    prod_status = None
    prod_err = ""

    url_prod = f"https://api.mercadolibre.com/products/search?status=active&site_id=MLA&q={requests.utils.quote(q)}"
    rp = http_get_con_reintentos(url_prod, headers=headers, timeout=10)
    if rp is not None:
        prod_status = rp.status_code
        if rp.status_code == 200:
            prods = (rp.json().get("results", []) or [])[:5]
            for prod in prods:
                pid = prod.get("id")
                pname = prod.get("name", q)
                pthumb = ""
                pics = prod.get("pictures") or []
                if pics and isinstance(pics, list):
                    pthumb = pics[0].get("secure_url") or pics[0].get("url") or ""

                if pid:
                    rit = http_get_con_reintentos(f"https://api.mercadolibre.com/products/{pid}/items", headers=headers, timeout=10)
                    if rit is not None and rit.status_code == 200:
                        for it in rit.json().get("results", []) or []:
                            iid = it.get("item_id") or it.get("id") or ""
                            if iid and iid not in seen_ids:
                                seen_ids.add(iid)
                                recolectados.append(
                                    {
                                        "id": iid,
                                        "title": it.get("title") or pname,
                                        "price": it.get("price", 0),
                                        "available_quantity": it.get("available_quantity", 0),
                                        "sold_quantity": it.get("sold_quantity", 0),
                                        "permalink": it.get("permalink") or construir_url_canonica_meli(iid, "", pid),
                                        "thumbnail": it.get("thumbnail") or pthumb,
                                        "seller_id": it.get("seller_id"),
                                    }
                                )
        else:
            try:
                prod_err = rp.json().get("message") or f"HTTP {rp.status_code}"
            except Exception:
                prod_err = f"HTTP {rp.status_code}"

    if recolectados:
        diag["endpoint_usado"] = "/products/search -> /products/{id}/items"
        diag["status_code"] = 200
        diag["total_api"] = len(recolectados)
        return recolectados[:limit], diag

    url = f"https://api.mercadolibre.com/sites/MLA/search?q={requests.utils.quote(q)}&limit={limit}"
    diag["endpoint_usado"] = "/sites/MLA/search"
    r = http_get_con_reintentos(url, headers=headers, timeout=10)
    if r is not None:
        diag["status_code"] = r.status_code
        if r.status_code == 200:
            results = r.json().get("results", []) or []
            diag["total_api"] = len(results)
            return results, diag
        try:
            err_body = r.json()
            diag["error"] = err_body.get("message") or str(err_body)
        except Exception:
            diag["error"] = r.text[:200] if r.text else f"HTTP {r.status_code}"

    if prod_err and not diag["error"]:
        diag["error"] = prod_err
    if prod_status and not diag["status_code"]:
        diag["status_code"] = prod_status

    return [], diag


def buscar_publicaciones_similares_por_imagen(
    consulta_base: str,
    img_bytes: Optional[bytes],
    access_token: str = "",
    candidatos_externos: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    if candidatos_externos is not None:
        raw_items = candidatos_externos
        diag = {
            "status_code": 200,
            "endpoint_usado": "Catálogo / Planilla cargada",
            "error": "",
            "total_api": len(raw_items),
        }
    else:
        raw_items, diag = consultar_items_meli_con_diagnostico(
            consulta=consulta_base,
            access_token=access_token,
            limit=50,
        )

    vec_ref = calcular_firma_visual_robusta(img_bytes) if img_bytes else None

    filas: List[Dict[str, Any]] = []
    for item in raw_items:
        precio = float(item.get("price") or 0.0)
        if precio <= 0:
            continue

        item_id = str(item.get("id") or item.get("item_id") or "")
        titulo = str(item.get("title") or "")
        thumb = str(item.get("secure_thumbnail") or item.get("thumbnail") or "")
        permalink = construir_url_canonica_meli(
            item_id,
            item.get("permalink") or "",
            item.get("catalog_product_id") or "",
        )

        seller_obj = item.get("seller")
        seller_id = seller_obj.get("id") if isinstance(seller_obj, dict) else item.get("seller_id")
        vendedor = item.get("seller_name") or resolver_vendedor_nickname_oficial(seller_id, access_token)

        sim_pct = np.nan
        if vec_ref is not None and thumb:
            vec_item = obtener_firma_miniatura_url(thumb)
            if vec_item is not None:
                cos_sim = float(np.clip(np.dot(vec_ref, vec_item), -1.0, 1.0))
                sim_pct = round(max(0.0, (cos_sim + 1.0) / 2.0 * 100.0), 1)

        filas.append(
            {
                "Similitud Imagen (%)": sim_pct,
                "Miniatura": thumb,
                "ID": item_id,
                "Vendedor": vendedor,
                "Título": titulo,
                "Precio ($)": precio,
                "Stock Disp.": int(item.get("available_quantity") or 0),
                "Ventas Acum.": int(item.get("sold_quantity") or 0),
                "Link": permalink,
            }
        )

    if vec_ref is not None and filas:
        filas.sort(
            key=lambda x: (
                -1.0 if pd.isna(x["Similitud Imagen (%)"]) else -x["Similitud Imagen (%)"],
                x["Precio ($)"],
            )
        )

    return filas[:30], diag


# ------------------------------------------------------------------------------
# ANÁLISIS DE MLA, COMPETENCIA INTEGRAL Y EXTRACTOR DE FICHA
# ------------------------------------------------------------------------------
@st.cache_data(ttl=600)
def analizar_mla_y_mercado(query_input: str, access_token: str = "") -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    headers = get_meli_headers(access_token)
    parsed = extraer_ids_meli_avanzado(query_input)

    item_objetivo: Optional[Dict[str, Any]] = None
    catalog_id = parsed.get("catalog_id", "")
    category_id = ""
    search_query = parsed.get("raw", "")

    if parsed["tipo"] == "MELI_URL_OR_ID":
        candidatos_item = [x for x in [parsed["item_id"], parsed["alt_item_id"]] if x]
        for cid_it in candidatos_item:
            r_it = http_get_con_reintentos(f"https://api.mercadolibre.com/items/{cid_it}", headers=headers, timeout=8)
            if r_it is not None and r_it.status_code == 200:
                b = r_it.json()
                seller_nick = resolver_vendedor_nickname_oficial(b.get("seller_id"), access_token)

                stk = int(b.get("available_quantity", 0))
                vars_list = b.get("variations", [])
                if vars_list and isinstance(vars_list, list):
                    stk_vars = sum(int(v.get("available_quantity", 0)) for v in vars_list if isinstance(v, dict))
                    if stk_vars > 0:
                        stk = stk_vars

                item_objetivo = {
                    "id": b.get("id"),
                    "title": b.get("title", ""),
                    "price": float(b.get("price", 0.0)),
                    "stock": stk,
                    "sold_quantity": int(b.get("sold_quantity", 0)),
                    "category_id": b.get("category_id", ""),
                    "catalog_product_id": b.get("catalog_product_id", ""),
                    "vendedor_name": seller_nick,
                    "permalink": construir_url_canonica_meli(b.get("id"), b.get("permalink", ""), b.get("catalog_product_id", "")),
                    "condition": b.get("condition", "new"),
                    "listing_type_id": b.get("listing_type_id", ""),
                    "thumbnail": b.get("secure_thumbnail") or b.get("thumbnail", ""),
                }
                if item_objetivo["catalog_product_id"]:
                    catalog_id = item_objetivo["catalog_product_id"]
                category_id = item_objetivo["category_id"]
                search_query = item_objetivo["title"]
                break

    raw_items: List[Dict[str, Any]] = []
    if catalog_id:
        res_pi = http_get_con_reintentos(f"https://api.mercadolibre.com/products/{catalog_id}/items", headers=headers, timeout=8)
        if res_pi is not None and res_pi.status_code == 200:
            raw_items = res_pi.json().get("results", []) or []
        if not raw_items:
            res_ci = http_get_con_reintentos(f"https://api.mercadolibre.com/sites/MLA/search?catalog_product_id={catalog_id}", headers=headers, timeout=8)
            if res_ci is not None and res_ci.status_code == 200:
                raw_items = res_ci.json().get("results", []) or []

    if not raw_items and search_query:
        palabras_clave = " ".join(search_query.split()[:6])
        url_search = f"https://api.mercadolibre.com/sites/MLA/search?q={requests.utils.quote(palabras_clave)}&limit=40"
        if category_id:
            url_search += f"&category={category_id}"
        res_q = http_get_con_reintentos(url_search, headers=headers, timeout=8)
        if res_q is not None and res_q.status_code == 200:
            raw_items = res_q.json().get("results", []) or []

    list_ids: List[str] = []
    for r in raw_items[:40]:
        i_id = r.get("item_id") or r.get("id", "")
        if i_id and i_id not in list_ids:
            list_ids.append(i_id)

    detalles_dict: Dict[str, Dict[str, Any]] = {}
    if list_ids:
        for i in range(0, len(list_ids), 20):
            chunk = list_ids[i : i + 20]
            res_m = http_get_con_reintentos(f"https://api.mercadolibre.com/items?ids={','.join(chunk)}", headers=headers, timeout=8)
            if res_m is not None and res_m.status_code == 200:
                for entry in res_m.json():
                    if entry.get("code") == 200:
                        b = entry.get("body", {})
                        it_id = b.get("id")
                        stk = int(b.get("available_quantity", 0))
                        vars_list = b.get("variations", [])
                        if vars_list and isinstance(vars_list, list):
                            stk_vars = sum(int(v.get("available_quantity", 0)) for v in vars_list if isinstance(v, dict))
                            if stk_vars > 0:
                                stk = stk_vars
                        detalles_dict[it_id] = {
                            "title_real": b.get("title", ""),
                            "stock_real": stk,
                            "sold_real": int(b.get("sold_quantity", 0)),
                            "price_real": float(b.get("price", 0.0)),
                            "category_real": b.get("category_id", category_id or "MLA4765"),
                            "permalink_real": b.get("permalink", ""),
                            "seller_id": b.get("seller_id"),
                        }

    items_procesados: List[Dict[str, Any]] = []
    for r in raw_items[:40]:
        item_id = r.get("item_id") or r.get("id", "")
        if not item_id:
            continue
        det = detalles_dict.get(item_id, {})
        seller_id = det.get("seller_id") or (r.get("seller", {}).get("id") if isinstance(r.get("seller"), dict) else r.get("seller_id"))
        nickname = resolver_vendedor_nickname_oficial(seller_id, access_token)

        stock_final = det.get("stock_real", int(r.get("available_quantity", 0)))
        sold_final = det.get("sold_real", int(r.get("sold_quantity", 0)))
        price_final = det.get("price_real", float(r.get("price", 0.0)))
        cat_final = det.get("category_real") or r.get("category_id", category_id or "MLA4765")
        title_final = det.get("title_real") or r.get("title", "")

        items_procesados.append(
            {
                "vendedor_name": nickname,
                "id": item_id,
                "title": title_final,
                "price": price_final,
                "stock": stock_final,
                "sold_quantity": sold_final,
                "permalink": construir_url_canonica_meli(item_id, det.get("permalink_real") or r.get("permalink", ""), catalog_id),
                "category_id": cat_final,
            }
        )

    if item_objetivo and not any(x["id"] == item_objetivo["id"] for x in items_procesados):
        items_procesados.insert(0, item_objetivo)

    return item_objetivo, items_procesados


@st.cache_data(ttl=900)
def buscar_competencia_integral_ean(
    query_key: str,
    access_token: Optional[str] = None,
    titulo_gold: str = "",
    articulo_gold: str = "",
) -> Tuple[str, str, List[Dict[str, Any]], str, List[str]]:
    headers = get_meli_headers(access_token or "")
    type_input, clean_val = extraer_id_catalogo_o_ean_input(query_key)

    catalog_id = clean_val if type_input == "CATALOG_ID" else ""
    product_title = titulo_gold.strip() if titulo_gold else ""
    raw_items: List[Dict[str, Any]] = []
    diagnostico: List[str] = []
    fuente_datos = "API Mercado Libre"

    if type_input == "EAN":
        url_ean = f"https://api.mercadolibre.com/products/search?status=active&site_id=MLA&product_identifier={clean_val}"
        res_p = http_get_con_reintentos(url_ean, headers=headers, timeout=8)
        if res_p is not None:
            diagnostico.append(f"/products/search (EAN {clean_val}) -> HTTP {res_p.status_code}")
            if res_p.status_code == 200:
                p_results = res_p.json().get("results", []) or []
                if p_results:
                    catalog_id = p_results[0].get("id", "")
                    product_title = p_results[0].get("name", product_title)

    if not catalog_id:
        q_cat_text = " ".join(filter(None, [titulo_gold.strip(), articulo_gold.strip()])).strip()
        if not q_cat_text and type_input == "TEXT":
            q_cat_text = clean_val
        if q_cat_text:
            url_p_q = f"https://api.mercadolibre.com/products/search?status=active&site_id=MLA&q={requests.utils.quote(q_cat_text)}"
            res_pq = http_get_con_reintentos(url_p_q, headers=headers, timeout=8)
            if res_pq is not None:
                diagnostico.append(f"/products/search (q='{q_cat_text}') -> HTTP {res_pq.status_code}")
                if res_pq.status_code == 200:
                    pq_results = res_pq.json().get("results", []) or []
                    if pq_results:
                        catalog_id = pq_results[0].get("id", "")
                        if not product_title:
                            product_title = pq_results[0].get("name", "")

    if catalog_id:
        url_prod_items = f"https://api.mercadolibre.com/products/{catalog_id}/items"
        res_pi = http_get_con_reintentos(url_prod_items, headers=headers, timeout=8)
        if res_pi is not None:
            diagnostico.append(f"/products/{catalog_id}/items -> HTTP {res_pi.status_code}")
            if res_pi.status_code == 200:
                raw_items = res_pi.json().get("results", []) or []

        if not raw_items:
            url_c_items = f"https://api.mercadolibre.com/sites/MLA/search?catalog_product_id={catalog_id}"
            res_ci = http_get_con_reintentos(url_c_items, headers=headers, timeout=8)
            if res_ci is not None:
                diagnostico.append(f"/sites/MLA/search (catalog={catalog_id}) -> HTTP {res_ci.status_code}")
                if res_ci.status_code == 200:
                    raw_items = res_ci.json().get("results", []) or []

    search_terms: List[str] = []
    if titulo_gold.strip() and articulo_gold.strip():
        search_terms.append(f"{titulo_gold.strip()} {articulo_gold.strip()}")
    if titulo_gold.strip():
        search_terms.append(titulo_gold.strip())
        palabras_cortas = " ".join(titulo_gold.strip().split()[:4])
        if palabras_cortas and palabras_cortas not in search_terms:
            search_terms.append(palabras_cortas)
    if articulo_gold.strip():
        search_terms.append(articulo_gold.strip())
    if clean_val and clean_val not in search_terms:
        search_terms.append(clean_val)

    if not raw_items:
        for term_search in search_terms:
            if raw_items:
                break
            url_q = f"https://api.mercadolibre.com/sites/MLA/search?q={requests.utils.quote(term_search)}"
            res_q = http_get_con_reintentos(url_q, headers=headers, timeout=8)
            if res_q is not None:
                diagnostico.append(f"/sites/MLA/search (q='{term_search}') -> HTTP {res_q.status_code}")
                if res_q.status_code == 200:
                    raw_items = res_q.json().get("results", []) or []

    list_ids: List[str] = []
    for r in raw_items[:50]:
        i_id = r.get("item_id") or r.get("id", "")
        if i_id:
            list_ids.append(i_id)

    detalles_dict: Dict[str, Dict[str, Any]] = {}
    if list_ids:
        for i in range(0, len(list_ids), 20):
            chunk = list_ids[i : i + 20]
            ids_str = ",".join(chunk)
            url_multiget = f"https://api.mercadolibre.com/items?ids={ids_str}"
            res_m = http_get_con_reintentos(url_multiget, headers=headers, timeout=8)
            if res_m is not None and res_m.status_code == 200:
                for entry in res_m.json():
                    if entry.get("code") == 200:
                        b = entry.get("body", {})
                        it_id = b.get("id")
                        stk = int(b.get("available_quantity", 0))
                        vars_list = b.get("variations", [])
                        if vars_list and isinstance(vars_list, list):
                            stk_vars = sum(int(v.get("available_quantity", 0)) for v in vars_list if isinstance(v, dict))
                            if stk_vars > 0:
                                stk = stk_vars
                        detalles_dict[it_id] = {
                            "title_real": b.get("title", ""),
                            "stock_real": stk,
                            "sold_real": int(b.get("sold_quantity", 0)),
                            "price_real": float(b.get("price", 0.0)),
                            "category_real": b.get("category_id", "MLA4765"),
                            "permalink_real": b.get("permalink", ""),
                        }

    items_procesados: List[Dict[str, Any]] = []
    for r in raw_items[:50]:
        item_id = r.get("item_id") or r.get("id", "")
        if not item_id:
            continue

        seller_id = None
        if isinstance(r.get("seller"), dict):
            seller_id = r.get("seller", {}).get("id")
        if not seller_id:
            seller_id = r.get("seller_id")

        nickname = resolver_vendedor_nickname_oficial(seller_id, access_token or "")
        det = detalles_dict.get(item_id, {})
        url_oficial = construir_url_canonica_meli(item_id, det.get("permalink_real") or r.get("permalink", ""), catalog_id)
        inst = r.get("installments", {})
        q_c = inst.get("quantity", 1) if isinstance(inst, dict) else 1

        title_final = det.get("title_real") or r.get("title") or product_title or f"Publicación {item_id}"
        stock_final = det.get("stock_real", int(r.get("available_quantity", 0)))
        sold_final = det.get("sold_real", int(r.get("sold_quantity", 0)))
        price_final = det.get("price_real", float(r.get("price", 0.0)))
        cat_final = det.get("category_real") or r.get("category_id", "MLA4765")

        items_procesados.append(
            {
                "vendedor_name": nickname,
                "id": item_id,
                "title": title_final,
                "price": price_final,
                "installments_qty": q_c,
                "listing_type_id": str(r.get("listing_type_id", "gold_pro")),
                "stock": stock_final,
                "sold_quantity": sold_final,
                "permalink": url_oficial,
                "category_id": cat_final,
            }
        )

    if not items_procesados:
        variantes_web = [t for t in [product_title, titulo_gold.strip()] + search_terms if t]
        items_web = extraer_competencia_web_publica(catalog_id, variantes_web, diagnostico)
        if items_web:
            items_procesados = items_web
            fuente_datos = f"Respaldo Web Público ({catalog_id or variantes_web[0]})"
        else:
            fuente_datos = "sin_resultados_o_bloqueado"

    return catalog_id, product_title, items_procesados, fuente_datos, diagnostico


def extraer_web_fallback_universal(parsed_meli: Dict[str, str], res_data: Dict[str, Any]) -> bool:
    urls_a_probar: List[str] = []
    if parsed_meli.get("url_original"):
        urls_a_probar.append(parsed_meli["url_original"])

    c_id = parsed_meli.get("catalog_id")
    i_id = parsed_meli.get("item_id")
    alt_id = parsed_meli.get("alt_item_id")

    if c_id:
        urls_a_probar.append(f"https://www.mercadolibre.com.ar/p/{c_id}")
    for candidate in [i_id, alt_id]:
        if candidate and candidate.startswith("MLA"):
            num_part = re.sub(r"\D", "", candidate)
            if num_part:
                urls_a_probar.append(f"https://articulo.mercadolibre.com.ar/MLA-{num_part}")
                urls_a_probar.append(f"https://www.mercadolibre.com.ar/up/{candidate}")

    headers_web = get_web_headers()

    for url_web in dict.fromkeys(urls_a_probar):
        try:
            r = requests.get(url_web, headers=headers_web, timeout=10, allow_redirects=True)
            if r.status_code != 200 or len(r.text) < 1500:
                continue

            html = r.text
            encontrado = False

            m_title = re.search(r'<h1[^>]*class="[^"]*ui-pdp-title[^"]*"[^>]*>(.*?)</h1>', html, re.DOTALL)
            if not m_title:
                m_title = re.search(r'<meta property="og:title" content="([^"]+)"', html)
            if m_title:
                tit = re.sub(r"<[^>]+>", "", m_title.group(1)).replace(" | MercadoLibre", "").strip()
                if tit and "Mercado Libre" not in tit and len(tit) > 3:
                    res_data["family_name"] = tit[:60]
                    encontrado = True

            m_price = re.search(r'"price"\s*:\s*(\d+(?:\.\d+)?)', html)
            if m_price:
                p_val = float(m_price.group(1))
                if p_val > 100:
                    res_data["pvp_sugerido"] = p_val
                    res_data["etiqueta_precio"] = "🌐 PVP Clonado de Publicación"
                    encontrado = True

            for m_img in re.findall(r'https://http2\.mlstatic\.com/D_NQ_NP_[^"\'\s>\\]+\.(?:jpg|webp|png)', html):
                clean_img = (
                    m_img.replace("-O.webp", "-O.jpg")
                    .replace("-F.webp", "-O.jpg")
                    .replace("-I.jpg", "-O.jpg")
                    .replace("-V.jpg", "-O.jpg")
                )
                if clean_img not in res_data["fotos"] and len(res_data["fotos"]) < 10:
                    res_data["fotos"].append(clean_img)

            m_brand = re.search(r'"brand"\s*:\s*\{\s*"@type"\s*:\s*"Brand"\s*,\s*"name"\s*:\s*"([^"]+)"', html)
            if m_brand:
                res_data["marca"] = m_brand.group(1).strip()
            else:
                m_b_spec = re.search(r">Marca<.*?<span[^>]*>([^<]+)</span>", html, re.DOTALL)
                if m_b_spec:
                    res_data["marca"] = m_b_spec.group(1).strip()

            m_m_spec = re.search(r">Modelo<.*?<span[^>]*>([^<]+)</span>", html, re.DOTALL)
            if m_m_spec:
                res_data["modelo"] = m_m_spec.group(1).strip()

            m_cat_prod = re.search(r'"catalog_product_id"\s*:\s*"(MLA\d+)"', html)
            if m_cat_prod:
                res_data["cat_product_id"] = m_cat_prod.group(1)
            elif c_id:
                res_data["cat_product_id"] = c_id

            m_cat = re.search(r'"category_id"\s*:\s*"(MLA\d+)"', html)
            if m_cat:
                res_data["cat_meli_id"] = m_cat.group(1)

            m_desc = re.search(r'<p[^>]*class="[^"]*ui-pdp-description__content[^"]*"[^>]*>(.*?)</p>', html, re.DOTALL)
            if m_desc:
                desc_clean = re.sub(r"<br\s*/?>", "\n", m_desc.group(1))
                desc_clean = re.sub(r"<[^>]+>", "", desc_clean).strip()
                if desc_clean:
                    res_data["descripcion"] = desc_clean

            for label_pat, key_dest in [
                (r">Ancho<", "ancho"),
                (r">Altura<|>Alto<", "alto"),
                (r">Profundidad<|>Largo<", "prof"),
                (r">Peso<", "peso"),
            ]:
                if not res_data.get(key_dest):
                    m_dim = re.search(label_pat + r".*?<span[^>]*>([^<]+)</span>", html, re.DOTALL | re.IGNORECASE)
                    if m_dim:
                        res_data[key_dest] = m_dim.group(1).strip()

            if encontrado:
                res_data["exito_externo"] = True
                return True
        except Exception:
            continue

    return False


def extraer_ficha_completa_meli(query_builder: str, access_token: str = "") -> Dict[str, Any]:
    headers_ext = get_meli_headers(access_token)
    found_gold_b, costo_gold_b, desc_gold_b, art_gold_b = buscar_costo_y_titulo_en_lista_gold(query_builder)

    res_data: Dict[str, Any] = {
        "exito_externo": False,
        "error_api": "",
        "found_gold": found_gold_b,
        "costo_gold": costo_gold_b,
        "desc_gold": desc_gold_b,
        "pvp_sugerido": round(costo_gold_b * 2.1, 2) if found_gold_b else 0.0,
        "etiqueta_precio": "PVP Sugerido (Lista Gold)" if found_gold_b else "PVP Clonado",
        "cat_product_id": "",
        "cat_meli_id": "MLA4765",
        "marca": "",
        "modelo": art_gold_b if art_gold_b else "",
        "family_name": desc_gold_b[:60].strip() if desc_gold_b else "",
        "descripcion": "",
        "fotos": [],
        "video_id": "",
        "ancho": "",
        "alto": "",
        "prof": "",
        "peso": "",
        "tiene_datos_embalaje": False,
        "origen_embalaje": "",
        "found_matriz": False,
        "cant_cajas_matriz": 1,
    }

    found_mat_b, _, _, _, _, cant_cajas_m, _ = buscar_datos_en_matriz(
        query_builder, res_data["pvp_sugerido"] or 100000.0
    )
    if found_mat_b:
        res_data["ancho"], res_data["alto"], res_data["prof"], res_data["peso"] = buscar_datos_en_matriz_completa(query_builder)
        res_data["found_matriz"] = True
        res_data["cant_cajas_matriz"] = cant_cajas_m
        res_data["tiene_datos_embalaje"] = True
        res_data["origen_embalaje"] = f"Matriz Logística ({cant_cajas_m} bulto/s)"

    parsed_meli = extraer_ids_meli_avanzado(query_builder)

    if parsed_meli["tipo"] == "EAN":
        url_ean = f"https://api.mercadolibre.com/products/search?status=active&site_id=MLA&product_identifier={parsed_meli['ean']}"
        r_ean = http_get_con_reintentos(url_ean, headers=headers_ext, timeout=8)
        if r_ean is not None and r_ean.status_code == 200:
            results = r_ean.json().get("results", []) or []
            if results:
                parsed_meli["tipo"] = "MELI_URL_OR_ID"
                parsed_meli["catalog_id"] = results[0].get("id", "")

    if parsed_meli["tipo"] == "MELI_URL_OR_ID":
        c_candidates = [x for x in [parsed_meli["catalog_id"], parsed_meli["alt_item_id"]] if x]
        i_candidates = [x for x in [parsed_meli["item_id"], parsed_meli["alt_item_id"]] if x]
        pvp_buybox = None
        errores_http: List[str] = []
        resolved_item_id = ""

        for c_id in c_candidates:
            if res_data["exito_externo"]:
                break
            res_prod = http_get_con_reintentos(f"https://api.mercadolibre.com/products/{c_id}", headers=headers_ext, timeout=8)
            if res_prod is not None and res_prod.status_code == 200:
                prod_data = res_prod.json()
                res_data["exito_externo"] = True
                res_data["cat_product_id"] = c_id
                if prod_data.get("name"):
                    res_data["family_name"] = prod_data["name"][:60]
                if prod_data.get("category_id"):
                    res_data["cat_meli_id"] = prod_data["category_id"]
                if prod_data.get("short_description", {}).get("content"):
                    res_data["descripcion"] = prod_data["short_description"]["content"]

                bb_winner = prod_data.get("buy_box_winner")
                if isinstance(bb_winner, dict):
                    if bb_winner.get("price"):
                        pvp_buybox = float(bb_winner["price"])
                        res_data["pvp_sugerido"] = pvp_buybox
                        res_data["etiqueta_precio"] = "🏆 PVP Ganador de Catálogo (BuyBox)"
                    if bb_winner.get("item_id"):
                        resolved_item_id = bb_winner["item_id"]

                for pic in (prod_data.get("pictures", []) or [])[:10]:
                    pic_url = pic.get("secure_url") or pic.get("url")
                    if pic_url and pic_url not in res_data["fotos"]:
                        res_data["fotos"].append(pic_url)

                for attr in prod_data.get("attributes", []) or []:
                    aid = attr.get("id")
                    vname = attr.get("value_name")
                    if aid == "BRAND" and vname:
                        res_data["marca"] = vname
                    elif aid == "MODEL" and vname:
                        res_data["modelo"] = vname
                    elif not found_mat_b:
                        if aid in ["PACKAGE_HEIGHT", "HEIGHT"] and vname:
                            res_data["alto"] = vname
                        elif aid in ["PACKAGE_WIDTH", "WIDTH"] and vname:
                            res_data["ancho"] = vname
                        elif aid in ["PACKAGE_LENGTH", "PACKAGE_DEPTH", "DEPTH", "LENGTH"] and vname:
                            res_data["prof"] = vname
                        elif aid in ["PACKAGE_WEIGHT", "WEIGHT"] and vname:
                            res_data["peso"] = vname

        if resolved_item_id and resolved_item_id not in i_candidates:
            i_candidates.insert(0, resolved_item_id)

        for i_id in i_candidates:
            res_item = http_get_con_reintentos(f"https://api.mercadolibre.com/items/{i_id}", headers=headers_ext, timeout=8)
            if res_item is not None and res_item.status_code == 200:
                item_data = res_item.json()
                res_data["exito_externo"] = True
                if not res_data["family_name"]:
                    res_data["family_name"] = item_data.get("title", "")[:60]
                if item_data.get("category_id"):
                    res_data["cat_meli_id"] = item_data["category_id"]
                if not pvp_buybox and item_data.get("price"):
                    res_data["pvp_sugerido"] = float(item_data["price"])
                    res_data["etiqueta_precio"] = "💲 PVP Publicación Referencia"
                if item_data.get("catalog_product_id"):
                    res_data["cat_product_id"] = item_data["catalog_product_id"]
                elif parsed_meli["catalog_id"]:
                    res_data["cat_product_id"] = parsed_meli["catalog_id"]
                if item_data.get("video_id"):
                    res_data["video_id"] = str(item_data["video_id"]).strip()

                if not found_mat_b:
                    shipping_info = item_data.get("shipping", {}) or {}
                    dimensions_str = shipping_info.get("dimensions")
                    if dimensions_str and isinstance(dimensions_str, str):
                        parts = dimensions_str.split(",")
                        if len(parts) >= 1:
                            box_dims = parts[0].split("x")
                            if len(box_dims) == 3:
                                res_data["alto"] = f"{box_dims[0]} cm"
                                res_data["ancho"] = f"{box_dims[1]} cm"
                                res_data["prof"] = f"{box_dims[2]} cm"
                        if len(parts) >= 2:
                            try:
                                g_weight = float(parts[1]) / 1000.0
                                res_data["peso"] = f"{g_weight:.1f} kg"
                            except Exception:
                                pass

                for pic in (item_data.get("pictures", []) or [])[:10]:
                    if len(res_data["fotos"]) >= 10:
                        break
                    pic_url = pic.get("secure_url") or pic.get("url")
                    if pic_url and pic_url not in res_data["fotos"]:
                        res_data["fotos"].append(pic_url)

                for attr in item_data.get("attributes", []) or []:
                    aid = attr.get("id")
                    vname = attr.get("value_name")
                    if aid == "BRAND" and vname:
                        res_data["marca"] = vname
                    elif aid == "MODEL" and vname:
                        res_data["modelo"] = vname
                    elif not found_mat_b:
                        if aid in ["PACKAGE_HEIGHT", "HEIGHT"] and vname:
                            res_data["alto"] = vname
                        elif aid in ["PACKAGE_WIDTH", "WIDTH"] and vname:
                            res_data["ancho"] = vname
                        elif aid in ["PACKAGE_LENGTH", "PACKAGE_DEPTH", "DEPTH", "LENGTH"] and vname:
                            res_data["prof"] = vname
                        elif aid in ["PACKAGE_WEIGHT", "WEIGHT"] and vname:
                            res_data["peso"] = vname

                res_desc = http_get_con_reintentos(f"https://api.mercadolibre.com/items/{i_id}/description", headers=headers_ext, timeout=8)
                if res_desc is not None and res_desc.status_code == 200:
                    txt_desc = res_desc.json().get("plain_text", "")
                    if txt_desc:
                        res_data["descripcion"] = txt_desc
                break
            elif res_item is not None:
                errores_http.append(f"/items/{i_id} -> HTTP {res_item.status_code}")

        if not res_data["exito_externo"]:
            ok_web = extraer_web_fallback_universal(parsed_meli, res_data)
            if not ok_web and errores_http:
                res_data["error_api"] = " | ".join(errores_http)

    if not res_data["exito_externo"] and parsed_meli["tipo"] == "TEXT" and len(query_builder.strip()) > 3:
        _, _, items_busq, _, _ = buscar_competencia_integral_ean(query_builder.strip(), access_token)
        if items_busq:
            top_hit = items_busq[0]
            res_data["exito_externo"] = True
            res_data["family_name"] = top_hit.get("title", "")[:60]
            res_data["pvp_sugerido"] = float(top_hit.get("price", 0.0))
            res_data["cat_meli_id"] = top_hit.get("category_id", "MLA4765")
            res_data["etiqueta_precio"] = "🔍 PVP Referencia Búsqueda"

    if not found_mat_b:
        _, p_fact_chk, _, ok_emb = calcular_flete_desde_embalaje(
            res_data["alto"], res_data["ancho"], res_data["prof"], res_data["peso"], res_data["pvp_sugerido"]
        )
        if ok_emb:
            res_data["tiene_datos_embalaje"] = True
            res_data["origen_embalaje"] = f"Publicación MeLi ({p_fact_chk:.1f} kg facturables)"
        else:
            res_data["tiene_datos_embalaje"] = False
            res_data["origen_embalaje"] = "Sin datos de embalaje en publicación"

    return res_data


# ------------------------------------------------------------------------------
# SIDEBAR UNIFICADO: CENTRO DE CARGA DE ARCHIVOS Y CONEXIÓN OAUTH
# ------------------------------------------------------------------------------
with st.sidebar:
    st.title("⚡ Control Panel")
    st.caption(f"Versión activa: **{APP_VERSION}**")

    if st.button("🧹 Limpiar Caché de Consultas", use_container_width=True):
        st.cache_data.clear()
        st.success("✅ Caché limpiada.")
        st.rerun()

    st.markdown("---")
    st.subheader("🔗 Conexión Mercado Libre")

    manual_token = st.text_input("Access Token Directo (Opcional)", value=st.session_state["access_token"], type="password")
    if manual_token != st.session_state["access_token"]:
        st.session_state["access_token"] = manual_token.strip()
        st.session_state["user_info"] = obtener_perfil_meli(st.session_state["access_token"])
        sincronizar_tarifas_financiacion_meli(st.session_state["access_token"])
        st.rerun()

    if st.session_state["refresh_token"] and CLIENT_SECRET:
        if st.button("♻️ Renovar Token con Refresh Token", use_container_width=True):
            ok_ref, msg_ref = refrescar_access_token_meli(st.session_state["refresh_token"])
            if ok_ref:
                st.session_state["user_info"] = obtener_perfil_meli(st.session_state["access_token"])
                st.success("✅ Access Token renovado.")
                st.rerun()
            else:
                st.error(f"No se pudo renovar el token: {msg_ref}")

    if st.session_state["access_token"]:
        nickname = st.session_state["user_info"].get("nickname", "Conectado")
        st.success(f"🟢 Vendedor: **{nickname}**")
        if st.button("🔄 Actualizar Tarifas API"):
            sincronizar_tarifas_financiacion_meli(st.session_state["access_token"])
            st.success("¡Tarifas sincronizadas con MeLi!")
            st.rerun()
        if st.button("Desconectar MeLi"):
            st.session_state["access_token"] = ""
            st.session_state["refresh_token"] = ""
            st.session_state["user_info"] = {}
            st.session_state["tarifas_actualizadas_api"] = False
            st.rerun()
    else:
        st.warning("⚠️ Sin conexión activa")
        url_auth = obtener_url_login_meli()
        st.link_button("🔗 CONECTAR CON MERCADO LIBRE", url_auth, type="primary", use_container_width=True)

    st.markdown("---")
    st.subheader("📁 Centro Unificado de Cargas")

    with st.expander("📄 1. Lista Gold (Costos)", expanded=True):
        uploaded_gold = st.file_uploader("Subir Lista Gold (Excel/CSV)", type=["xlsx", "csv"], key="uploader_gold_side")
        if uploaded_gold is not None:
            st.session_state["lista_gold_df"] = procesar_archivo_lista_gold(uploaded_gold)
            if st.session_state["lista_gold_df"] is not None:
                st.success("✅ Lista Gold vinculada.")

    with st.expander("📦 2. Matriz Logística (Bultos)", expanded=True):
        uploaded_matriz = st.file_uploader("Subir Matriz de Artículos (Excel)", type=["xlsx"], key="uploader_matriz_side")
        if uploaded_matriz is not None:
            try:
                st.session_state["matriz_custom_df"] = pd.read_excel(uploaded_matriz)
                st.success("✅ Matriz Logística cargada.")
            except Exception as e:
                st.error(f"Error al leer matriz: {e}")

# ------------------------------------------------------------------------------
# HEADER PRINCIPAL COMPACTO (SLATE & ESMERALDA)
# ------------------------------------------------------------------------------
matriz_banner_df = cargar_matriz_articulos_oficial()
gold_banner_df = st.session_state["lista_gold_df"]

conectado_meli = bool(st.session_state["access_token"])
nick_banner = st.session_state["user_info"].get("nickname", "Cuenta Activa") if conectado_meli else "Desconectado"
estado_meli_html = f'<span style="color:#34d399;">●</span> {nick_banner}' if conectado_meli else '<span style="color:#f59e0b;">●</span> Sin vincular'

skus_gold_txt = f"{len(gold_banner_df):,} artículos".replace(",", ".") if gold_banner_df is not None else "Sin cargar"
skus_matriz_txt = f"{len(matriz_banner_df):,} artículos".replace(",", ".") if matriz_banner_df is not None else "Sin cargar"

st.markdown(
    f"""
    <div class="exec-hero-banner">
        <div class="exec-hero-left">
            <div class="exec-logo-badge">NQ</div>
            <div>
                <div class="exec-hero-title">NQ Argentina <span>|</span> MeLi Intelligence <span class="exec-version-tag">{APP_VERSION}</span></div>
                <div class="exec-hero-subtitle">Auditoría de Rentabilidad, Monitoreo Competitivo y Publicador a Catálogo</div>
            </div>
        </div>
        <div class="exec-status-group">
            <div class="exec-status-pill">
                <div class="exec-pill-lbl">API Mercado Libre</div>
                <div class="exec-pill-val">{estado_meli_html}</div>
            </div>
            <div class="exec-status-pill">
                <div class="exec-pill-lbl">Lista Gold</div>
                <div class="exec-pill-val">{skus_gold_txt}</div>
            </div>
            <div class="exec-status-pill">
                <div class="exec-pill-lbl">Matriz Logística</div>
                <div class="exec-pill-val">{skus_matriz_txt}</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------------------
# NAVEGACIÓN VISUAL POR BOTONES (10 SOLAPAS HABILITADAS)
# ------------------------------------------------------------------------------
MENU_ITEMS = [
    ("🧮", "Costos & Margen"),
    ("⚡", "Control Precios"),
    ("📊", "Radiografía MLA"),
    ("📦", "Matriz Logística"),
    ("🤖", "Asistente IA"),
    ("🚀", "Publicador"),
    ("🛡️", "Modo Defensivo"),
    ("📥", "Cotizador Matriz"),
    ("🔍", "Comparador Imagen"),
    ("🧪", "Diagnóstico API"),
]

nav_cols_top = st.columns(5, gap="small")
nav_cols_bot = st.columns(5, gap="small")
nav_cols = nav_cols_top + nav_cols_bot

for idx, (icono, titulo_corto) in enumerate(MENU_ITEMS):
    with nav_cols[idx]:
        es_activo = st.session_state["active_tab"] == idx
        clase_btn = "nav-btn-wrap nav-btn-active" if es_activo else "nav-btn-wrap nav-btn-inactive"
        st.markdown(f'<div class="{clase_btn}">', unsafe_allow_html=True)
        if st.button(f"{icono} {titulo_corto}", key=f"nav_btn_{idx}", use_container_width=True):
            st.session_state["active_tab"] = idx
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<hr style='margin: 8px 0 16px 0; border-color: #e2e8f0;'>", unsafe_allow_html=True)

tab_activa = st.session_state["active_tab"]

# ------------------------------------------------------------------------------
# SECCIÓN 0: SIMULACIÓN DE COSTOS & AUDITORÍA NETA
# ------------------------------------------------------------------------------
if tab_activa == 0:
    st.header("🧮 Simulación de Costos & Auditoría Neta Real")
    st.caption("Cálculo preciso de rentabilidad libre a bolsillo descontando comisiones, IIBB, IVA (24.5%) y flete por bulto.")

    opciones_ean_gold_s1 = extraer_opciones_ean_lista_gold()

    def actualizar_desde_selectbox_s1():
        sel = st.session_state.get("select_gold_dropdown_s1", "")
        if sel:
            for lbl, ean_v in opciones_ean_gold_s1:
                if lbl == sel:
                    st.session_state["q_costos"] = ean_v
                    break

    if opciones_ean_gold_s1:
        labels_gold_s1 = [op[0] for op in opciones_ean_gold_s1]
        st.selectbox(
            "📋 Seleccionar Producto desde la Lista Gold",
            labels_gold_s1,
            key="select_gold_dropdown_s1",
            on_change=actualizar_desde_selectbox_s1,
        )
        st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

    c_s1, c_s2 = st.columns([3, 1])
    with c_s1:
        query_costos = st.text_input("Código SKU / EAN / MLA / URL", key="q_costos")
    with c_s2:
        st.write("")
        btn_calc_costos = st.button("🧮 CALCULAR COSTOS", type="primary", use_container_width=True)

    if btn_calc_costos or query_costos:
        found_gold, costo_gold_val, desc_g, art_g = buscar_costo_y_titulo_en_lista_gold(query_costos)
        pvp_default_sugerido = round(costo_gold_val * 2.0, 2) if found_gold else 208000.0

        found_mat, costo_env_tot, peso_unit, peso_real_tot, tarifa_unit, cant_cajas_mat, desc_mat = buscar_datos_en_matriz(
            query_costos, pvp_default_sugerido
        )

        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        col_st1, col_st2 = st.columns(2)
        with col_st1:
            if not found_gold:
                st.markdown('<div class="badge-missing">❌ SKU no hallado en Lista Gold. Usando base manual.</div>', unsafe_allow_html=True)
            else:
                st.success(f"✅ Costo base Lista Gold: **${costo_gold_val:,.2f}** ({desc_g})")
        with col_st2:
            if not found_mat:
                st.warning("⚠️ SKU no hallado en Matriz Logística. Usando costo de envío oficial estándar.")
                costo_env_tot_default = 39090.0
                cant_cajas_mat = 1
                peso_unit = 10.0
            else:
                st.success(f"📦 Flete MeLi (ME2): **${costo_env_tot:,.2f}** total ({cant_cajas_mat} bulto/s de {peso_unit:.1f} kg c/u)")
                costo_env_tot_default = costo_env_tot

        c_p1, c_p2, c_p3 = st.columns(3)
        with c_p1:
            pvp_sim = st.number_input("Precio de Venta Simulado ($ ARS)", min_value=100.0, value=pvp_default_sugerido, step=500.0)
            tipo_pub_sim = st.selectbox(
                "Modalidad de Publicación / Cuotas",
                list(st.session_state["tasas_cuotas"].keys()),
                index=0,
            )
            info_cuota = st.session_state["tasas_cuotas"][tipo_pub_sim]
            pct_com_sim = (info_cuota["comision_base"] + info_cuota["tasa_finan"]) * 100
        with c_p2:
            costo_envio_sim = st.number_input("Costo Logística Total ($)", min_value=0.0, value=costo_env_tot_default, step=500.0)
            pct_descuento_proveedor = st.number_input("Descuento Proveedor al Costo (%)", min_value=0.0, max_value=100.0, value=20.0, step=0.5
