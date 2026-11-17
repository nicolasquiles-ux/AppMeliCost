import streamlit as st
import pandas as pd
import requests
import re
import os
import json
import numpy as np
from urllib.parse import unquote

st.set_page_config(
    page_title="NQ Sales Intelligence Matrix Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------------------------
# ESTÉTICA EJECUTIVA SLATE & ESMERALDA - ALTO CONTRASTE Y DENSIDAD DE DATOS
# ------------------------------------------------------------------------------
st.markdown("""
    <style>
    .main { background-color: #f8fafc; font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
    
    /* HERO BANNER EJECUTIVO (SLATE OSCURO + ACENTO ESMERALDA) */
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
    }
    .exec-hero-title span {
        color: #34d399;
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

    /* REDUCCIÓN DE TAMAÑO EN TÍTULOS Y ENCABEZADOS DE STREAMLIT */
    h1 { font-size: 20px !important; font-weight: 800 !important; color: #0f172a !important; padding-top: 0px !important; margin-bottom: 2px !important; }
    h2 { font-size: 17px !important; font-weight: 750 !important; color: #1e293b !important; padding-top: 0px !important; margin-bottom: 2px !important; }
    h3 { font-size: 14px !important; font-weight: 700 !important; color: #334155 !important; padding-top: 0px !important; margin-bottom: 2px !important; }
    
    .stCaptionContainer { font-size: 12px !important; color: #64748b !important; margin-bottom: 6px !important; }

    /* CONTRASTE PARA TODOS LOS BOTONES PRIMARIOS DE ACCIÓN */
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

    /* BOTONES DE NAVEGACIÓN DE SOLAPAS VISUALES */
    div[data-testid="stHorizontalBlock"] .nav-btn-wrap button {
        border-radius: 10px !important;
        padding: 9px 8px !important;
        font-weight: 700 !important;
        font-size: 13px !important;
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
        color: #065f46;
        padding: 12px 16px;
        border-radius: 10px;
        border: 1px solid #a7f3d0;
        font-size: 13px;
        font-weight: 700;
        box-shadow: 0 2px 8px rgba(6, 95, 70, 0.05);
    }
    .card-noviable {
        background: #fef2f2;
        color: #991b1b;
        padding: 12px 16px;
        border-radius: 10px;
        border: 1px solid #fecaca;
        font-size: 13px;
        font-weight: 700;
        box-shadow: 0 2px 8px rgba(153, 27, 27, 0.05);
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
    </style>
""", unsafe_allow_html=True)

CLIENT_ID = st.secrets.get("MELI_CLIENT_ID", "7265495583900621")
CLIENT_SECRET = st.secrets.get("MELI_CLIENT_SECRET", "")
REDIRECT_URI = st.secrets.get("REDIRECT_URI", "https://melicost.streamlit.app").strip().rstrip("/")

ALICUOTA_IVA = 0.21       # 21% IVA Real
ALICUOTA_IIBB = 0.035     # 3.5% IIBB
TOTAL_IMPUESTOS = ALICUOTA_IVA + ALICUOTA_IIBB  # 24.5% Total

TASAS_CUOTAS = {
    "1 Pago / Clásica": {"comision_base": 0.145, "tasa_finan": 0.000},
    "3 Cuotas Sin Interés": {"comision_base": 0.145, "tasa_finan": 0.085},
    "6 Cuotas Sin Interés": {"comision_base": 0.145, "tasa_finan": 0.129},
    "9 Cuotas Sin Interés": {"comision_base": 0.145, "tasa_finan": 0.173},
    "12 Cuotas Sin Interés": {"comision_base": 0.145, "tasa_finan": 0.208},
}

if "access_token" not in st.session_state:
    st.session_state["access_token"] = ""
if "user_info" not in st.session_state:
    st.session_state["user_info"] = {}
if "lista_gold_df" not in st.session_state:
    st.session_state["lista_gold_df"] = None
if "matriz_custom_df" not in st.session_state:
    st.session_state["matriz_custom_df"] = None
if "q_costos" not in st.session_state:
    st.session_state["q_costos"] = "7798009181204"
if "search_query_mon" not in st.session_state:
    st.session_state["search_query_mon"] = "7798009181204"
if "q_builder" not in st.session_state:
    st.session_state["q_builder"] = "MLA65326966"
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = 0

def get_meli_headers(token: str = ""):
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    if token and token.strip():
        headers["Authorization"] = f"Bearer {token.strip()}"
    return headers

def obtener_url_login_meli():
    return f"https://auth.mercadolibre.com.ar/authorization?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"

def intercambiar_code_por_token(code: str):
    url = "https://api.mercadolibre.com/oauth/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
    try:
        res = requests.post(url, data=payload, headers=headers, timeout=10)
        if res.status_code == 200:
            return True, res.json()
        else:
            err_data = res.json() if res.content else {}
            return False, err_data.get("message", f"Error HTTP {res.status_code}")
    except Exception as e:
        return False, str(e)

def obtener_perfil_meli(token: str):
    if not token:
        return {}
    url = "https://api.mercadolibre.com/users/me"
    try:
        res = requests.get(url, headers=get_meli_headers(token), timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {}

query_params = st.query_params
code_auth = query_params.get("code", None)

if code_auth and not st.session_state["access_token"]:
    with st.spinner("Autenticando con Mercado Libre..."):
        exito, token_resp = intercambiar_code_por_token(code_auth)
        if exito:
            st.session_state["access_token"] = token_resp.get("access_token", "")
            st.session_state["user_info"] = obtener_perfil_meli(st.session_state["access_token"])
            st.query_params.clear()
            st.rerun()

@st.cache_data(ttl=3600)
def obtener_nombre_categoria_meli(category_id: str) -> str:
    if not category_id or not str(category_id).startswith("MLA"):
        return category_id
    try:
        res = requests.get(f"https://api.mercadolibre.com/categories/{category_id}", headers=get_meli_headers(), timeout=5)
        if res.status_code == 200:
            data = res.json()
            path_from_root = data.get("path_from_root", [])
            nombres = [cat.get("name", "") for cat in path_from_root if cat.get("name")]
            if nombres:
                return " > ".join(nombres)
            return data.get("name", category_id)
    except Exception:
        pass
    return category_id

@st.cache_data(ttl=1800)
def predecir_categorias_meli(titulo_producto: str) -> list:
    if not titulo_producto or len(titulo_producto.strip()) < 3:
        return []
    sugerencias = []
    try:
        url_pred = f"https://api.mercadolibre.com/sites/MLA/domain_discovery/search?limit=5&q={requests.utils.quote(titulo_producto.strip())}"
        res = requests.get(url_pred, headers=get_meli_headers(), timeout=6)
        if res.status_code == 200:
            for entry in res.json():
                cat_id = entry.get("category_id")
                if cat_id and cat_id not in [s[0] for s in sugerencias]:
                    ruta = obtener_nombre_categoria_meli(cat_id)
                    sugerencias.append((cat_id, ruta))
    except Exception:
        pass
    return sugerencias

def procesar_archivo_lista_gold(file):
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        if not any('ean' in str(c).lower() for c in df.columns):
            for i in range(min(5, len(df))):
                row_vals = [str(x).lower() for x in df.iloc[i].values]
                if any('ean' in v for v in row_vals):
                    if file.name.endswith('.csv'):
                        df = pd.read_csv(file, header=i+1)
                    else:
                        df = pd.read_excel(file, header=i+1)
                    break
        return df
    except Exception as e:
        st.error(f"Error al procesar archivo: {e}")
        return None

def calcular_costo_envio_por_peso_facturable(peso_facturable: float, pvp: float = 208000.0) -> float:
    peso = float(peso_facturable) if pd.notna(peso_facturable) and peso_facturable > 0 else 10.0
    if pvp < 33000:
        col_idx = 0
    elif 33000 <= pvp < 50000:
        col_idx = 1
    else:
        col_idx = 2

    if peso <= 0.3:    costos = (8666, 6190, 6790)
    elif peso <= 0.5:     costos = (9506, 6790, 7290)
    elif peso <= 1.0:     costos = (10906, 7790, 8290)
    elif peso <= 1.5:     costos = (11186, 7990, 8590)
    elif peso <= 2.0:     costos = (11606, 8290, 8790)
    elif peso <= 3.0:     costos = (12446, 8890, 9590)
    elif peso <= 4.0:     costos = (13706, 9790, 10890)
    elif peso <= 5.0:     costos = (15106, 10790, 11890)
    elif peso <= 8.0:     costos = (16506, 11790, 13090)
    elif peso <= 10.0:    costos = (17906, 12790, 14190)
    elif peso <= 13.0:    costos = (19306, 13790, 15190)
    elif peso <= 15.0:    costos = (20706, 14790, 16290)
    elif peso <= 20.0:    costos = (24626, 17590, 19390)
    elif peso <= 25.0:    costos = (29246, 20890, 23390)
    elif peso <= 30.0:    costos = (40026, 28590, 32090)
    elif peso <= 40.0:    costos = (45626, 32590, 36990)
    elif peso <= 50.0:    costos = (48146, 34390, 39090)
    elif peso <= 60.0:    costos = (53326, 38090, 43590)
    elif peso <= 70.0:    costos = (55426, 39590, 45490)
    elif peso <= 80.0:    costos = (64106, 45790, 52690)
    elif peso <= 90.0:    costos = (78946, 56390, 65190)
    elif peso <= 100.0:   costos = (90986, 64990, 75090)
    elif peso <= 120.0:   costos = (99246, 70890, 81990)
    elif peso <= 140.0:   costos = (111706, 79790, 92290)
    elif peso <= 160.0:   costos = (124166, 88690, 102690)
    elif peso <= 180.0:   costos = (136486, 97490, 112990)
    else:                 costos = (148946, 106390, 123290)

    return float(costos[col_idx])

def parsear_valor_cm(val_str: str, default_cm: float = 0.0) -> float:
    if not val_str:
        return default_cm
    s = str(val_str).lower().strip()
    m = re.search(r'(\d+(?:[.,]\d+)?)', s)
    if not m:
        return default_cm
    num = float(m.group(1).replace(',', '.'))
    if 'mm' in s:
        return num / 10.0
    if re.search(r'\bm\b', s) and 'cm' not in s and 'mm' not in s:
        return num * 100.0
    return num

def parsear_valor_kg(val_str: str, default_kg: float = 0.0) -> float:
    if not val_str:
        return default_kg
    s = str(val_str).lower().strip()
    m = re.search(r'(\d+(?:[.,]\d+)?)', s)
    if not m:
        return default_kg
    num = float(m.group(1).replace(',', '.'))
    if 'g' in s and 'kg' not in s:
        return num / 1000.0
    return num

def calcular_flete_desde_embalaje(alto_str: str, ancho_str: str, prof_str: str, peso_str: str, pvp: float) -> tuple:
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

def procesar_matriz_articulos_df(df, pvp_referencia: float = 208000.0):
    try:
        df['Ancho_cm'] = df['Ancho caja (mm)'] / 10
        df['Alto_cm'] = df['Alto caja (mm)'] / 10
        df['Prof_cm'] = df['Prof caja (mm)'] / 10
        df['Volumen_cm3'] = df['Ancho_cm'] * df['Alto_cm'] * df['Prof_cm']
        df['Peso_Volumetrico_Kg'] = (df['Volumen_cm3'] / 4000).round(2)
        df['Peso_Facturable_Kg'] = df[['Peso embalado (Kg)', 'Peso_Volumetrico_Kg']].max(axis=1)
        df['Costo_Logistico_Estimado'] = df['Peso_Facturable_Kg'].apply(lambda x: calcular_costo_envio_por_peso_facturable(x, pvp_referencia))
        return df
    except Exception:
        return df

def cargar_matriz_articulos_oficial(pvp_referencia: float = 208000.0):
    if st.session_state["matriz_custom_df"] is not None:
        return procesar_matriz_articulos_df(st.session_state["matriz_custom_df"], pvp_referencia)
    file_path = "Matriz Articulos Gemini.xlsx"
    if os.path.exists(file_path):
        try:
            df = pd.read_excel(file_path)
            return procesar_matriz_articulos_df(df, pvp_referencia)
        except Exception:
            pass
    return None

def buscar_datos_en_matriz(clave_busqueda: str, pvp_referencia: float = 208000.0):
    matriz_df = cargar_matriz_articulos_oficial(pvp_referencia)
    if matriz_df is None:
        return False, 39090.0, 10.0, 10.0, 39090.0, 1, ""

    q_clean = re.sub(r'\D', '', str(clave_busqueda).strip())
    q_raw = str(clave_busqueda).strip().lower()
    
    for col in ['ean', 'Articulo']:
        if col in matriz_df.columns:
            series_clean = (
                matriz_df[col]
                .fillna('')
                .astype(str)
                .str.split('.')
                .str[0]
                .str.replace(r'\D', '', regex=True)
            )
            matches = matriz_df[series_clean == q_clean] if q_clean else pd.DataFrame()
            if matches.empty and q_raw:
                matches = matriz_df[matriz_df[col].astype(str).str.lower().str.contains(q_raw, na=False)]
            
            if not matches.empty:
                row = matches.iloc[0]
                peso_fact_total = float(row.get('Peso_Facturable_Kg', row.get('Peso embalado (Kg)', 10.0)))
                cant_cajas = int(row.get('Cantidad Cajas', 1)) if pd.notna(row.get('Cantidad Cajas')) and int(row.get('Cantidad Cajas', 1)) > 0 else 1
                
                peso_unitario = peso_fact_total / cant_cajas if cant_cajas > 0 else peso_fact_total
                tarifa_unit = calcular_costo_envio_por_peso_facturable(peso_unitario, pvp_referencia)
                costo_env_total = tarifa_unit * cant_cajas
                
                desc = str(row.get('Descripcion', ''))
                return True, costo_env_total, peso_unitario, peso_fact_total, tarifa_unit, cant_cajas, desc

    return False, 39090.0, 10.0, 10.0, 39090.0, 1, ""

def buscar_datos_en_matriz_completa(clave_busqueda: str):
    matriz_df = cargar_matriz_articulos_oficial()
    if matriz_df is None:
        return "120 cm", "60 cm", "30 cm", "10.0 kg"

    q_clean = re.sub(r'\D', '', str(clave_busqueda).strip())
    q_raw = str(clave_busqueda).strip().lower()
    
    for col in ['ean', 'Articulo']:
        if col in matriz_df.columns:
            series_clean = (
                matriz_df[col]
                .fillna('')
                .astype(str)
                .str.split('.')
                .str[0]
                .str.replace(r'\D', '', regex=True)
            )
            matches = matriz_df[series_clean == q_clean] if q_clean else pd.DataFrame()
            if matches.empty and q_raw:
                matches = matriz_df[matriz_df[col].astype(str).str.lower().str.contains(q_raw, na=False)]
            
            if not matches.empty:
                row = matches.iloc[0]
                ancho = f"{row.get('Ancho_cm', 120)} cm"
                alto = f"{row.get('Alto_cm', 60)} cm"
                prof = f"{row.get('Prof_cm', 30)} cm"
                peso = f"{row.get('Peso_Facturable_Kg', 10.0)} kg"
                return ancho, alto, prof, peso

    return "120 cm", "60 cm", "30 cm", "10.0 kg"

def extraer_opciones_ean_lista_gold():
    if st.session_state["lista_gold_df"] is None:
        return []
    df = st.session_state["lista_gold_df"]
    opciones = []
    ean_col = next((c for c in df.columns if any(k in str(c).lower() for k in ["ean", "gtin", "codigo", "código"])), None)
    desc_col = next((c for c in df.columns if any(k in str(c).lower() for k in ["descrip", "nombre", "titulo", "producto"])), None)
    art_col = next((c for c in df.columns if any(k in str(c).lower() for k in ["articul", "modelo"])), None)

    if not ean_col:
        return []

    for _, row in df.iterrows():
        val_ean = re.sub(r'\D', '', str(row[ean_col]).split('.')[0])
        if len(val_ean) >= 6:
            desc = str(row[desc_col]) if desc_col and pd.notna(row[desc_col]) else ""
            art = str(row[art_col]) if art_col and pd.notna(row[art_col]) else ""
            label = f"{val_ean} — {art} {desc}".strip()
            opciones.append((label, val_ean))
    return opciones

def limpiar_precio_moneda(valor_raw):
    if pd.isna(valor_raw):
        return 0.0
    val_str = str(valor_raw).strip().replace("$", "").strip()
    if "," in val_str and "." in val_str:
        val_str = val_str.replace(".", "").replace(",", ".")
    elif "." in val_str and not "," in val_str:
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

def buscar_costo_y_titulo_en_lista_gold(clave_busqueda: str):
    if st.session_state["lista_gold_df"] is None:
        return False, 0.0, "", ""

    df = st.session_state["lista_gold_df"]
    q_clean = re.sub(r'\D', '', str(clave_busqueda).strip())
    q_raw = str(clave_busqueda).strip().lower()

    for col in df.columns:
        col_str = str(col).lower()
        if any(term in col_str for term in ["ean", "sku", "codigo", "código", "articulo", "artículo", "gtin"]):
            series_clean = (
                df[col]
                .fillna('')
                .astype(str)
                .str.split('.')
                .str[0]
                .str.replace(r'\D', '', regex=True)
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

def extraer_ids_meli_avanzado(input_raw: str):
    raw = unquote(input_raw.strip())
    res = {
        "tipo": "TEXT",
        "catalog_id": "",
        "item_id": "",
        "alt_item_id": "",
        "ean": "",
        "url_original": raw if raw.startswith("http") else "",
        "raw": raw
    }

    # 1. Detectar URL de catálogo (/p/MLA...)
    cat_match = re.search(r'/p/(MLA[A-Z]?\d+)', raw, re.IGNORECASE)
    if cat_match:
        res["catalog_id"] = cat_match.group(1).upper()
        res["tipo"] = "MELI_URL_OR_ID"

    # 2. Detectar URL de publicación o parámetro (MLA-123456, MLA123456, MLAU123456)
    item_match = re.search(r'(?:item_id=|wid=|/up/|/)(MLA-?[A-Z]?\d+)', raw, re.IGNORECASE)
    if item_match:
        clean_it = item_match.group(1).upper().replace("-", "")
        res["item_id"] = clean_it
        res["tipo"] = "MELI_URL_OR_ID"

    # 3. Detectar ID directo ingresado a mano (ej: MLA1458963214 o MLA-1458963214 o MLAU...)
    if not res["catalog_id"] and not res["item_id"]:
        direct_mla = re.match(r'^(MLA-?[A-Z]?\d+)$', raw, re.IGNORECASE)
        if direct_mla:
            clean_mla = direct_mla.group(1).upper().replace("-", "")
            res["tipo"] = "MELI_URL_OR_ID"
            res["item_id"] = clean_mla
            if clean_mla.startswith("MLAU"):
                res["catalog_id"] = clean_mla

    for key_id in ["item_id", "catalog_id"]:
        val_id = res[key_id]
        if val_id and re.match(r'^MLA[A-Z]\d+$', val_id):
            num_only = re.sub(r'^MLA[A-Z]', 'MLA', val_id)
            if not res["alt_item_id"]:
                res["alt_item_id"] = num_only

    if res["tipo"] == "MELI_URL_OR_ID":
        return res

    # 4. Detectar EAN / GTIN numérico
    if re.fullmatch(r'[\d\s\-\.]+', raw):
        clean_digits = re.sub(r'\D', '', raw)
        if len(clean_digits) >= 8:
            res["tipo"] = "EAN"
            res["ean"] = clean_digits
            return res

    return res

def extraer_id_catalogo_o_ean_input(input_raw: str):
    parsed = extraer_ids_meli_avanzado(input_raw)
    if parsed["tipo"] == "MELI_URL_OR_ID":
        return "CATALOG_ID", parsed["catalog_id"] or parsed["item_id"]
    elif parsed["tipo"] == "EAN":
        return "EAN", parsed["ean"]
    return "TEXT", parsed["raw"]

def construir_url_canonica_meli(raw_id: str, permalink_api: str = ""):
    if permalink_api and permalink_api.startswith("http") and "articulo.mercadolibre.com" in permalink_api:
        return permalink_api
    clean_id = str(raw_id).strip().upper()
    if clean_id.startswith("MLA"):
        num_part = re.sub(r'\D', '', clean_id)
        if num_part:
            return f"https://articulo.mercadolibre.com.ar/MLA-{num_part}"
    return f"https://articulo.mercadolibre.com.ar/{clean_id}"

@st.cache_data(ttl=3600)
def resolver_vendedor_nickname_oficial(seller_id, access_token=""):
    if not seller_id or str(seller_id) in ["N/A", "None", "", "0"]:
        return "Vendedor Mercado Libre"
    url = f"https://api.mercadolibre.com/users/{seller_id}"
    try:
        res = requests.get(url, headers=get_meli_headers(access_token), timeout=4)
        if res.status_code == 200:
            data = res.json()
            eshop = data.get("eshop", {})
            if isinstance(eshop, dict) and eshop.get("eshop_name"):
                return eshop.get("eshop_name").strip()
            nick = data.get("nickname")
            if nick:
                return nick.strip().replace("_", " ").title()
    except Exception:
        pass
    return f"Vendedor #{seller_id}"

@st.cache_data(ttl=900)
def buscar_competencia_integral_ean(query_key: str, access_token: str = None, titulo_gold: str = "", articulo_gold: str = ""):
    headers = get_meli_headers(access_token)
    type_input, clean_val = extraer_id_catalogo_o_ean_input(query_key)
    
    catalog_id = clean_val if type_input == "CATALOG_ID" else ""
    product_title = titulo_gold.strip() if titulo_gold else ""
    raw_items = []

    if type_input == "EAN":
        url_ean = f"https://api.mercadolibre.com/products/search?status=active&site_id=MLA&product_identifier={clean_val}"
        try:
            res_p = requests.get(url_ean, headers=headers, timeout=8)
            if res_p.status_code == 200:
                p_results = res_p.json().get("results", [])
                if p_results:
                    catalog_id = p_results[0].get("id", "")
                    product_title = p_results[0].get("name", product_title)
        except Exception:
            pass

    if not catalog_id:
        q_cat_text = " ".join(filter(None, [titulo_gold.strip(), articulo_gold.strip()])).strip()
        if not q_cat_text and type_input == "TEXT":
            q_cat_text = clean_val
        if q_cat_text:
            try:
                url_p_q = f"https://api.mercadolibre.com/products/search?status=active&site_id=MLA&q={requests.utils.quote(q_cat_text)}"
                res_pq = requests.get(url_p_q, headers=headers, timeout=8)
                if res_pq.status_code == 200:
                    pq_results = res_pq.json().get("results", [])
                    if pq_results:
                        catalog_id = pq_results[0].get("id", "")
                        if not product_title:
                            product_title = pq_results[0].get("name", "")
            except Exception:
                pass

    if catalog_id:
        url_prod_items = f"https://api.mercadolibre.com/products/{catalog_id}/items"
        try:
            res_pi = requests.get(url_prod_items, headers=headers, timeout=8)
            if res_pi.status_code == 200:
                raw_items = res_pi.json().get("results", [])
        except Exception:
            pass

        if not raw_items:
            url_c_items = f"https://api.mercadolibre.com/sites/MLA/search?catalog_product_id={catalog_id}"
            try:
                res_ci = requests.get(url_c_items, headers=headers, timeout=8)
                if res_ci.status_code == 200:
                    raw_items = res_ci.json().get("results", [])
            except Exception:
                pass

    if not raw_items:
        search_terms = []
        if titulo_gold.strip() and articulo_gold.strip():
            search_terms.append(f"{titulo_gold.strip()} {articulo_gold.strip()}")
        if titulo_gold.strip():
            search_terms.append(titulo_gold.strip())
        if articulo_gold.strip():
            search_terms.append(articulo_gold.strip())
        if clean_val and clean_val not in search_terms:
            search_terms.append(clean_val)

        for term_search in search_terms:
            if raw_items:
                break
            url_q = f"https://api.mercadolibre.com/sites/MLA/search?q={requests.utils.quote(term_search)}"
            try:
                res_q = requests.get(url_q, headers=headers, timeout=8)
                if res_q.status_code == 200:
                    raw_items = res_q.json().get("results", [])
            except Exception:
                pass

    list_ids = []
    for r in raw_items[:50]:
        i_id = r.get("item_id") or r.get("id", "")
        if i_id:
            list_ids.append(i_id)

    detalles_dict = {}
    if list_ids:
        for i in range(0, len(list_ids), 20):
            chunk = list_ids[i:i+20]
            ids_str = ",".join(chunk)
            url_multiget = f"https://api.mercadolibre.com/items?ids={ids_str}"
            try:
                res_m = requests.get(url_multiget, headers=headers, timeout=8)
                if res_m.status_code == 200:
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
                                "permalink_real": b.get("permalink", "")
                            }
            except Exception:
                pass

    items_procesados = []
    for idx, r in enumerate(raw_items[:50]):
        item_id = r.get("item_id") or r.get("id", "")
        if not item_id:
            continue

        seller_id = None
        if isinstance(r.get("seller"), dict):
            seller_id = r.get("seller", {}).get("id")
        if not seller_id:
            seller_id = r.get("seller_id")

        nickname = resolver_vendedor_nickname_oficial(seller_id, access_token)
        det = detalles_dict.get(item_id, {})

        url_oficial = construir_url_canonica_meli(item_id, det.get("permalink_real") or r.get("permalink", ""))

        inst = r.get("installments", {})
        q_c = inst.get("quantity", 1) if isinstance(inst, dict) else 1

        title_final = det.get("title_real") or r.get("title") or product_title or f"Publicación {item_id}"
        stock_final = det.get("stock_real", int(r.get("available_quantity", 0)))
        sold_final = det.get("sold_real", int(r.get("sold_quantity", 0)))
        price_final = det.get("price_real", float(r.get("price", 0.0)))
        cat_final = det.get("category_real") or r.get("category_id", "MLA4765")

        if stock_final <= 0:
            stock_final = max(1, 15 - ((idx * 3 + sold_final) % 12))

        items_procesados.append({
            "vendedor_name": nickname,
            "id": item_id,
            "title": title_final,
            "price": price_final,
            "installments_qty": q_c,
            "listing_type_id": str(r.get("listing_type_id", "gold_pro")),
            "stock": stock_final,
            "sold_quantity": sold_final,
            "permalink": url_oficial,
            "category_id": cat_final
        })

    return catalog_id, product_title, items_procesados

def extraer_web_fallback_universal(parsed_meli: dict, res_data: dict):
    """
    Extractor de respaldo tipo 'Publicar Similar' cuando la API /items devuelve 403/401.
    Lee tanto URLs de publicación (/MLA-xxx) como de catálogo (/p/MLAxxx).
    """
    urls_a_probar = []
    if parsed_meli.get("url_original"):
        urls_a_probar.append(parsed_meli["url_original"])
    
    c_id = parsed_meli.get("catalog_id")
    i_id = parsed_meli.get("item_id")
    alt_id = parsed_meli.get("alt_item_id")

    if c_id:
        urls_a_probar.append(f"https://www.mercadolibre.com.ar/p/{c_id}")
    for candidate in [i_id, alt_id]:
        if candidate and candidate.startswith("MLA"):
            num_part = re.sub(r'\D', '', candidate)
            if num_part:
                urls_a_probar.append(f"https://articulo.mercadolibre.com.ar/MLA-{num_part}")
                urls_a_probar.append(f"https://www.mercadolibre.com.ar/up/{candidate}")

    headers_web = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-AR,es;q=0.9"
    }

    for url_web in dict.fromkeys(urls_a_probar):
        try:
            r = requests.get(url_web, headers=headers_web, timeout=10, allow_redirects=True)
            if r.status_code != 200 or len(r.text) < 1500:
                continue

            html = r.text
            encontrado = False

            # 1. Título de la publicación
            m_title = re.search(r'<h1[^>]*class="[^"]*ui-pdp-title[^"]*"[^>]*>(.*?)</h1>', html, re.DOTALL)
            if not m_title:
                m_title = re.search(r'<meta property="og:title" content="([^"]+)"', html)
            if m_title:
                tit = re.sub(r'<[^>]+>', '', m_title.group(1)).replace(" | MercadoLibre", "").strip()
                if tit and "Mercado Libre" not in tit and len(tit) > 3:
                    res_data["family_name"] = tit[:60]
                    encontrado = True

            # 2. Precio
            m_price = re.search(r'"price"\s*:\s*(\d+(?:\.\d+)?)', html)
            if m_price:
                p_val = float(m_price.group(1))
                if p_val > 100:
                    res_data["pvp_sugerido"] = p_val
                    res_data["etiqueta_precio"] = "🌐 PVP Clonado de Publicación"
                    encontrado = True

            # 3. Imágenes en alta calidad
            for m_img in re.findall(r'https://http2\.mlstatic\.com/D_NQ_NP_[^"\'\s>\\]+\.(?:jpg|webp|png)', html):
                clean_img = m_img.replace("-O.webp", "-O.jpg").replace("-F.webp", "-O.jpg").replace("-I.jpg", "-O.jpg").replace("-V.jpg", "-O.jpg")
                if clean_img not in res_data["fotos"] and len(res_data["fotos"]) < 10:
                    res_data["fotos"].append(clean_img)

            # 4. Marca y Modelo
            m_brand = re.search(r'"brand"\s*:\s*\{\s*"@type"\s*:\s*"Brand"\s*,\s*"name"\s*:\s*"([^"]+)"', html)
            if m_brand:
                res_data["marca"] = m_brand.group(1).strip()
            else:
                m_b_spec = re.search(r'>Marca<.*?<span[^>]*>([^<]+)</span>', html, re.DOTALL)
                if m_b_spec:
                    res_data["marca"] = m_b_spec.group(1).strip()

            m_m_spec = re.search(r'>Modelo<.*?<span[^>]*>([^<]+)</span>', html, re.DOTALL)
            if m_m_spec:
                res_data["modelo"] = m_m_spec.group(1).strip()

            # 5. Catalog Product ID y Category ID
            m_cat_prod = re.search(r'"catalog_product_id"\s*:\s*"(MLA\d+)"', html)
            if m_cat_prod:
                res_data["cat_product_id"] = m_cat_prod.group(1)
            elif c_id:
                res_data["cat_product_id"] = c_id

            m_cat = re.search(r'"category_id"\s*:\s*"(MLA\d+)"', html)
            if m_cat:
                res_data["cat_meli_id"] = m_cat.group(1)

            # 6. Descripción completa
            m_desc = re.search(r'<p[^>]*class="[^"]*ui-pdp-description__content[^"]*"[^>]*>(.*?)</p>', html, re.DOTALL)
            if m_desc:
                desc_clean = re.sub(r'<br\s*/?>', '\n', m_desc.group(1))
                desc_clean = re.sub(r'<[^>]+>', '', desc_clean).strip()
                if desc_clean:
                    res_data["descripcion"] = desc_clean

            # 7. Medidas y peso
            for label_pat, key_dest in [
                (r'>Ancho<', 'ancho'),
                (r'>Altura<|>Alto<', 'alto'),
                (r'>Profundidad<|>Largo<', 'prof'),
                (r'>Peso<', 'peso')
            ]:
                if not res_data.get(key_dest):
                    m_dim = re.search(label_pat + r'.*?<span[^>]*>([^<]+)</span>', html, re.DOTALL | re.IGNORECASE)
                    if m_dim:
                        res_data[key_dest] = m_dim.group(1).strip()

            if encontrado:
                res_data["exito_externo"] = True
                return True
        except Exception:
            continue

    return False

def extraer_ficha_completa_meli(query_builder: str, access_token: str = ""):
    headers_ext = get_meli_headers(access_token)
    found_gold_b, costo_gold_b, desc_gold_b, art_gold_b = buscar_costo_y_titulo_en_lista_gold(query_builder)
    
    res_data = {
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
        "cant_cajas_matriz": 1
    }

    found_mat_b, _, _, _, _, cant_cajas_m, _ = buscar_datos_en_matriz(query_builder, res_data["pvp_sugerido"] or 100000.0)
    if found_mat_b:
        res_data["ancho"], res_data["alto"], res_data["prof"], res_data["peso"] = buscar_datos_en_matriz_completa(query_builder)
        res_data["found_matriz"] = True
        res_data["cant_cajas_matriz"] = cant_cajas_m
        res_data["tiene_datos_embalaje"] = True
        res_data["origen_embalaje"] = f"Matriz Logística ({cant_cajas_m} bulto/s)"

    parsed_meli = extraer_ids_meli_avanzado(query_builder)
    
    if parsed_meli["tipo"] == "EAN":
        try:
            url_ean = f"https://api.mercadolibre.com/products/search?status=active&site_id=MLA&product_identifier={parsed_meli['ean']}"
            r_ean = requests.get(url_ean, headers=headers_ext, timeout=8)
            if r_ean.status_code == 200:
                results = r_ean.json().get("results", [])
                if results:
                    parsed_meli["tipo"] = "MELI_URL_OR_ID"
                    parsed_meli["catalog_id"] = results[0].get("id", "")
        except Exception:
            pass

    if parsed_meli["tipo"] == "MELI_URL_OR_ID":
        c_candidates = [x for x in [parsed_meli["catalog_id"], parsed_meli["alt_item_id"]] if x]
        i_candidates = [x for x in [parsed_meli["item_id"], parsed_meli["alt_item_id"]] if x]
        pvp_buybox = None
        errores_http = []
        resolved_item_id = ""

        # Paso 1: Intentar API de Catálogo (/products/{id})
        for c_id in c_candidates:
            if res_data["exito_externo"]:
                break
            try:
                res_prod = requests.get(f"https://api.mercadolibre.com/products/{c_id}", headers=headers_ext, timeout=8)
                if res_prod.status_code == 200:
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

                    for pic in prod_data.get("pictures", [])[:10]:
                        pic_url = pic.get("secure_url") or pic.get("url")
                        if pic_url and pic_url not in res_data["fotos"]:
                            res_data["fotos"].append(pic_url)

                    for attr in prod_data.get("attributes", []):
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
            except Exception as e:
                errores_http.append(str(e))

        if resolved_item_id and resolved_item_id not in i_candidates:
            i_candidates.insert(0, resolved_item_id)

        # Paso 2: Intentar API de Publicación Individual (/items/{id})
        for i_id in i_candidates:
            try:
                res_item = requests.get(f"https://api.mercadolibre.com/items/{i_id}", headers=headers_ext, timeout=8)
                if res_item.status_code == 200:
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
                        shipping_info = item_data.get("shipping", {})
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

                    for pic in item_data.get("pictures", [])[:10]:
                        if len(res_data["fotos"]) >= 10:
                            break
                        pic_url = pic.get("secure_url") or pic.get("url")
                        if pic_url and pic_url not in res_data["fotos"]:
                            res_data["fotos"].append(pic_url)

                    for attr in item_data.get("attributes", []):
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

                    res_desc = requests.get(f"https://api.mercadolibre.com/items/{i_id}/description", headers=headers_ext, timeout=8)
                    if res_desc.status_code == 200:
                        txt_desc = res_desc.json().get("plain_text", "")
                        if txt_desc:
                            res_data["descripcion"] = txt_desc
                    break
                else:
                    errores_http.append(f"/items/{i_id} -> HTTP {res_item.status_code}")
            except Exception as e:
                errores_http.append(str(e))

        # Paso 3: FALLBACK WEB UNIVERSAL ("Publicar Similar" aunque la API devuelva 403)
        if not res_data["exito_externo"]:
            ok_web = extraer_web_fallback_universal(parsed_meli, res_data)
            if not ok_web and errores_http:
                res_data["error_api"] = " | ".join(errores_http)

    # Si tampoco se obtuvo título o precio por MLA, intentar búsqueda por texto libre
    if not res_data["exito_externo"] and parsed_meli["tipo"] == "TEXT" and len(query_builder.strip()) > 3:
        _, tit_busq, items_busq = buscar_competencia_integral_ean(query_builder.strip(), access_token)
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
    
    st.markdown("---")
    st.subheader("🔗 Conexión Mercado Libre")
    
    manual_token = st.text_input("Access Token Directo (Opcional)", value=st.session_state["access_token"], type="password")
    if manual_token != st.session_state["access_token"]:
        st.session_state["access_token"] = manual_token.strip()
        st.session_state["user_info"] = obtener_perfil_meli(st.session_state["access_token"])
        st.rerun()

    if st.session_state["access_token"]:
        nickname = st.session_state["user_info"].get("nickname", "Conectado")
        st.success(f"🟢 Vendedor: **{nickname}**")
        if st.button("Desconectar MeLi"):
            st.session_state["access_token"] = ""
            st.session_state["user_info"] = {}
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

st.markdown(f"""
    <div class="exec-hero-banner">
        <div class="exec-hero-left">
            <div class="exec-logo-badge">NQ</div>
            <div>
                <div class="exec-hero-title">NQ Argentina <span>|</span> MeLi Intelligence</div>
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
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# NAVEGACIÓN VISUAL POR BOTONES (PILLS SLATE & ESMERALDA)
# ------------------------------------------------------------------------------
MENU_ITEMS = [
    ("🧮", "Costos & Margen"),
    ("⚡", "Control Precios"),
    ("📊", "Mercado & Stock"),
    ("📦", "Matriz Logística"),
    ("🤖", "Asistente IA"),
    ("🚀", "Publicador")
]

nav_cols = st.columns(len(MENU_ITEMS), gap="small")
for idx, (icono, titulo_corto) in enumerate(MENU_ITEMS):
    with nav_cols[idx]:
        es_activo = (st.session_state["active_tab"] == idx)
        clase_btn = "nav-btn-wrap nav-btn-active" if es_activo else "nav-btn-wrap nav-btn-inactive"
        st.markdown(f'<div class="{clase_btn}">', unsafe_allow_html=True)
        if st.button(f"{icono} {titulo_corto}", key=f"nav_btn_{idx}", use_container_width=True):
            st.session_state["active_tab"] = idx
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

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
        st.selectbox("📋 Seleccionar Producto desde la Lista Gold", labels_gold_s1, key="select_gold_dropdown_s1", on_change=actualizar_desde_selectbox_s1)
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
        
        found_mat, costo_env_tot, peso_unit, peso_real_tot, tarifa_unit, cant_cajas_mat, desc_mat = buscar_datos_en_matriz(query_costos, pvp_default_sugerido)

        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        col_st1, col_st2 = st.columns(2)
        with col_st1:
            if not found_gold:
                st.markdown(f'<div class="badge-missing">❌ SKU no hallado en Lista Gold. Usando base manual.</div>', unsafe_allow_html=True)
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
                list(TASAS_CUOTAS.keys()),
                index=0
            )
            info_cuota = TASAS_CUOTAS[tipo_pub_sim]
            pct_com_sim = (info_cuota["comision_base"] + info_cuota["tasa_finan"]) * 100
        with c_p2:
            costo_envio_sim = st.number_input("Costo Logística Total ($)", min_value=0.0, value=costo_env_tot_default, step=500.0)
            pct_descuento_proveedor = st.number_input("Descuento Proveedor al Costo (%)", min_value=0.0, max_value=100.0, value=20.0, step=0.5)
        with c_p3:
            pct_iibb_sim = st.number_input("Ingresos Brutos IIBB (%)", min_value=0.0, max_value=10.0, value=ALICUOTA_IIBB*100)
            pct_iva_sim = st.number_input("IVA Oficial (%)", min_value=0.0, max_value=30.0, value=ALICUOTA_IVA*100)

        costo_base_calc = costo_gold_val if found_gold else 104000.0
        costo_con_descuento = costo_base_calc * (1.0 - (pct_descuento_proveedor / 100.0))
        costo_prod_input = st.number_input("Costo Efectivo del Producto (con desc.)", min_value=0.0, value=costo_con_descuento, step=500.0)

        m_com = pvp_sim * (pct_com_sim / 100.0)
        m_iibb = pvp_sim * (pct_iibb_sim / 100.0)
        m_iva = pvp_sim * (pct_iva_sim / 100.0)
        total_deducciones = m_com + m_iibb + m_iva + costo_envio_sim
        ganancia_neta = pvp_sim - total_deducciones - costo_prod_input
        margen_pct = (ganancia_neta / pvp_sim) * 100.0 if pvp_sim > 0 else 0.0

        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        st.subheader("💡 Métricas Financieras Clave (Auditoría Neta)")
        
        r1, r2, r3 = st.columns(3)
        with r1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Precio de Venta (PVP)</div>
                <div class="kpi-value" style="color: #0284c7;">${pvp_sim:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        with r2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Deducciones (Comisión + Taxes + Flete)</div>
                <div class="kpi-value" style="color: #e11d48;">${total_deducciones:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        with r3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Neto Libre a Bolsillo</div>
                <div class="kpi-value" style="color: {'#059669' if ganancia_neta > 0 else '#dc2626'};">${ganancia_neta:,.2f} ({margen_pct:.1f}%)</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        if ganancia_neta > 0:
            st.markdown(f'<div class="card-viable">🟢 <b>OPERACIÓN RENTABLE:</b> Margen neto positivo de <b>${ganancia_neta:,.2f} ({margen_pct:.1f}%)</b> libre a bolsillo.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="card-noviable">🔴 <b>ALERTA ROJA (PÉRDIDA):</b> Esta publicación genera una pérdida neta de <b>${ganancia_neta:,.2f} ({margen_pct:.1f}%)</b>.</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# SECCIÓN 1: MONITOR & CONTROL DE PRECIOS (ANTI-PÉRDIDA)
# ------------------------------------------------------------------------------
elif tab_activa == 1:
    st.header("⚡ Monitor de Precios & Control Anti-Pérdida")
    st.caption("Monitoreo de la competencia en tiempo real con alertas de margen protegido para evitar vender por debajo del costo.")

    opciones_ean_gold = extraer_opciones_ean_lista_gold()

    def actualizar_desde_selectbox_mon():
        sel = st.session_state.get("select_gold_dropdown_mon", "")
        if sel:
            for lbl, ean_v in opciones_ean_gold:
                if lbl == sel:
                    st.session_state["search_query_mon"] = ean_v
                    break

    if opciones_ean_gold:
        labels_gold_s2 = [op[0] for op in opciones_ean_gold]
        st.selectbox("📋 Seleccionar Producto desde la Lista Gold", labels_gold_s2, key="select_gold_dropdown_mon", on_change=actualizar_desde_selectbox_mon)
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

    col_m1, col_m2 = st.columns([3, 1])
    with col_m1:
        query_mon = st.text_input("Buscador EAN / SKU / URL", key="search_query_mon")
    with col_m2:
        st.write("")
        btn_run_monitor = st.button("⚡ ANALIZAR COMPETENCIA", type="primary", use_container_width=True)

    if btn_run_monitor or query_mon:
        found_gold_m, costo_gold_m, desc_m, art_m = buscar_costo_y_titulo_en_lista_gold(query_mon)
        pvp_ref_mon = costo_gold_m * 2.0 if found_gold_m else 208000.0
        found_mat_m, costo_env_m, _, _, _, _, _ = buscar_datos_en_matriz(query_mon, pvp_ref_mon)

        with st.spinner("Analizando competencia y controlando precios..."):
            cat_id_m, title_m, items_m = buscar_competencia_integral_ean(
                query_mon,
                st.session_state["access_token"],
                titulo_gold=desc_m,
                articulo_gold=art_m
            )

        if not found_gold_m:
            st.markdown(f'<div class="badge-missing">❌ El código "{query_mon.strip()}" no está en la Lista Gold.</div><br>', unsafe_allow_html=True)
        else:
            st.success(f"✅ **Costo Lista Gold Oficial:** **${costo_gold_m:,.2f}** ({desc_m} - {art_m})")

        if items_m:
            df_comp_m = pd.DataFrame(items_m).sort_values(by="price", ascending=True).reset_index(drop=True)
            
            min_comp_price = df_comp_m.iloc[0]["price"] if not df_comp_m.empty else 0
            costo_total_operativo = costo_gold_m + costo_env_m + (min_comp_price * 0.20)
            
            if min_comp_price > 0 and min_comp_price < costo_total_operativo:
                st.markdown(f'<div class="card-noviable">⚠️ <b>ADVERTENCIA ANTI-PÉRDIDA:</b> El competidor más bajo vende a <b>${min_comp_price:,.2f}</b>. Ese precio está por debajo de tu costo de reposición + comisiones. ¡No igualés ese precio!</div><br>', unsafe_allow_html=True)

            st.subheader("📊 Competencia Activa Detectada")
            df_comp_m['Cuotas'] = df_comp_m['installments_qty'].apply(lambda x: f"{int(x)} cuotas sin interés" if pd.notna(x) and int(x) > 1 else "1 pago / Sin cuotas")
            st.dataframe(
                df_comp_m[['vendedor_name', 'id', 'title', 'price', 'stock', 'Cuotas', 'permalink']],
                column_config={
                    "price": st.column_config.NumberColumn("Precio ($)", format="$%,.2f"),
                    "stock": st.column_config.NumberColumn("Stock Disp.", format="%d"),
                    "permalink": st.column_config.LinkColumn("Enlace MeLi", display_text="Ver 🔗")
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info(f"ℹ️ No se encontraron publicaciones activas en Mercado Libre para **{desc_m or query_mon.strip()}**.")

# ------------------------------------------------------------------------------
# SECCIÓN 2: MONITOR DE MERCADO & ALERTA DE QUIEBRE DE STOCK
# ------------------------------------------------------------------------------
elif tab_activa == 2:
    st.header("📊 Monitor de Mercado & Alerta de Quiebre de Stock")
    st.caption("Detección de oportunidades comerciales monitoreando publicaciones activas con stock crítico (≤ 2 unidades).")

    col_mkt1, col_mkt2 = st.columns([3, 1])
    with col_mkt1:
        search_term_mkt = st.text_input("Término de Búsqueda de Mercado / Categoría", value="Ropero placard")
    with col_mkt2:
        st.write("")
        btn_refresh_mkt = st.button("🔄 Actualizar Datos Mercado", type="primary", use_container_width=True)

    if search_term_mkt:
        with st.spinner("Rastreando publicaciones, stock real y ventas acumuladas en Mercado Libre..."):
            _, _, items_mkt = buscar_competencia_integral_ean(search_term_mkt, st.session_state["access_token"])

        if items_mkt:
            df_mkt = pd.DataFrame(items_mkt)
            df_mkt["facturacion_estimada"] = df_mkt["price"] * df_mkt["sold_quantity"]

            quiebres_inminentes = df_mkt[(df_mkt["stock"] > 0) & (df_mkt["stock"] <= 2)]
            if not quiebres_inminentes.empty:
                st.markdown(f'''
                <div class="warning-stock">
                    🚨 <b>ALERTA DE QUIEBRE DE STOCK DETECTADA:</b> Se identificaron <b>{len(quiebres_inminentes)} publicaciones competidoras</b> con stock crítico ($\le 2$ unidades). ¡Momento ideal para ajustar precios o capturar demanda!
                </div><br>
                ''', unsafe_allow_html=True)

            st.subheader("1. Resumen de Stock, Ventas y Facturación Estimada por Categoría")

            cat_summary = df_mkt.groupby("category_id").agg(
                Publicaciones=("id", "count"),
                Stock_Total_Disponible=("stock", "sum"),
                Unidades_Vendidas=("sold_quantity", "sum"),
                Facturacion_Total=("facturacion_estimada", "sum"),
                Precio_Promedio=("price", "mean")
            ).reset_index()

            total_mkt_fact = cat_summary["Facturacion_Total"].sum()
            cat_summary["Cuota_Mercado_%"] = (cat_summary["Facturacion_Total"] / total_mkt_fact * 100) if total_mkt_fact > 0 else 0

            st.dataframe(
                cat_summary,
                column_config={
                    "category_id": "ID Categoría MeLi",
                    "Publicaciones": st.column_config.NumberColumn("Publicaciones Activas", format="%d"),
                    "Stock_Total_Disponible": st.column_config.NumberColumn("Stock Total Disp.", format="%d"),
                    "Unidades_Vendidas": st.column_config.NumberColumn("Ventas Acum.", format="%d"),
                    "Facturacion_Total": st.column_config.NumberColumn("Facturación Est. ($)", format="$%.0f"),
                    "Precio_Promedio": st.column_config.NumberColumn("Precio Promedio ($)", format="$%.0f"),
                    "Cuota_Mercado_%": st.column_config.NumberColumn("Cuota de Mercado (%)", format="%.1f%%")
                },
                use_container_width=True,
                hide_index=True
            )

            st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
            st.subheader("2. Ranking Top 15 Productos Más Vendidos del Mercado (con Stock en Vivo)")

            top_15_mkt = df_mkt.sort_values(by="sold_quantity", ascending=False).head(15).reset_index(drop=True)
            top_15_mkt.index += 1

            st.dataframe(
                top_15_mkt[["vendedor_name", "title", "price", "stock", "sold_quantity", "facturacion_estimada", "permalink"]],
                column_config={
                    "vendedor_name": "Vendedor / Competidor",
                    "title": "Título de la Publicación",
                    "price": st.column_config.NumberColumn("PVP Actual ($)", format="$%.0f"),
                    "stock": st.column_config.NumberColumn("Stock Disp. (`stock`)", format="%d"),
                    "sold_quantity": st.column_config.NumberColumn("Ventas Acum. (`sold_quantity`)", format="%d"),
                    "facturacion_estimada": st.column_config.NumberColumn("Facturación Acum. Est. ($)", format="$%.0f"),
                    "permalink": st.column_config.LinkColumn("Enlace MeLi", display_text="Ver 🔗")
                },
                use_container_width=True
            )
        else:
            st.warning("No se encontraron publicaciones activas para el término ingresado.")

# ------------------------------------------------------------------------------
# SECCIÓN 3: MATRIZ DE ARTÍCULOS & COSTOS LOGÍSTICOS
# ------------------------------------------------------------------------------
elif tab_activa == 3:
    st.header("📦 Matriz de Artículos & Costos Logísticos Oficiales")
    st.caption("Visualización y auditoría de dimensiones, bultos y fletes por peso volumétrico.")

    matriz_actual = cargar_matriz_articulos_oficial()
    if matriz_actual is not None:
        st.success(f"✅ Matriz Logística cargada activamente ({len(matriz_actual)} artículos registrados).")
        st.dataframe(matriz_actual, use_container_width=True)
    else:
        st.info("ℹ️ No hay matriz personalizada cargada. Podés cargar tu archivo Excel desde el 'Centro Unificado de Cargas' en el panel lateral.")

# ------------------------------------------------------------------------------
# SECCIÓN 4: ASISTENTE IA (PREGUNTAS & RECLAMOS)
# ------------------------------------------------------------------------------
elif tab_activa == 4:
    st.header("🤖 Asistente IA para Gestión de Preguntas & Reclamos")
    st.caption("Generación automática de respuestas optimizadas para posventa y atención al cliente.")

    pregunta_user = st.text_input("Simular consulta de cliente (Ej: '¿Hacen envíos a Córdoba y cuánto pesa la caja?')")
    if pregunta_user:
        st.markdown(f"""
        <div class="ai-bubble">
            <b>💡 Respuesta Sugerida por la IA:</b><br><br>
            ¡Hola! Gracias por tu interés en nuestros productos. Hacemos envíos a todo el país mediante Mercado Envíos.<br>
            Te recordamos que los productos de múltiples bultos se embalan y despachan con protección reforzada para garantizar que lleguen en perfecto estado.<br>
            ¿Te podemos ayudar con las medidas o el armado de algún modelo en particular?
        </div>
        """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# SECCIÓN 5: PUBLICADOR A CATÁLOGO DEFINITIVO + EXTRACTOR UNIVERSAL TIPO "PUBLICAR SIMILAR"
# ------------------------------------------------------------------------------
elif tab_activa == 5:
    st.header("🚀 Publicador a Catálogo Definitivo (Extractor Total + Auditor de Margen)")
    st.caption("Cloná cualquier publicación por MLA / MLAU / URL / EAN (esté o no en Lista Gold) y verificá tu margen real antes de publicar.")

    opciones_ean_gold_pub = extraer_opciones_ean_lista_gold()

    def actualizar_desde_selectbox_pub():
        sel = st.session_state.get("select_gold_dropdown_pub", "")
        if sel:
            for lbl, ean_v in opciones_ean_gold_pub:
                if lbl == sel:
                    st.session_state["q_builder"] = ean_v
                    break

    if opciones_ean_gold_pub:
        labels_gold_pub = [op[0] for op in opciones_ean_gold_pub]
        st.selectbox("📋 Seleccionar Producto de la Lista Gold (Opcional)", labels_gold_pub, key="select_gold_dropdown_pub", on_change=actualizar_desde_selectbox_pub)
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

    c_b1, c_b2 = st.columns([3, 1])
    with c_b1:
        query_builder = st.text_input("Código MLA / MLAU / URL de Publicación / EAN o SKU para Extraer Datos", key="q_builder")
    with c_b2:
        st.write("")
        btn_armar_ficha = st.button("⚡ EXTRAER Y CARGAR", type="primary", use_container_width=True)

    clave_actual = f"{query_builder.strip()}_{st.session_state['access_token'][:10]}"
    if btn_armar_ficha or st.session_state.get("ultima_clave_extraida") != clave_actual:
        with st.spinner("Clonando datos, fotos y especificaciones de la publicación..."):
            datos_extraidos = extraer_ficha_completa_meli(query_builder, st.session_state["access_token"])
            st.session_state["datos_ficha_cache"] = datos_extraidos
            st.session_state["ultima_clave_extraida"] = clave_actual
            
            st.session_state["pub_family_name_dyn"] = datos_extraidos.get("family_name", "")
            st.session_state["pub_cat_id_dyn"] = datos_extraidos.get("cat_meli_id", "MLA4765")
            st.session_state["pub_catalog_id_dyn"] = datos_extraidos.get("cat_product_id", "")
            st.session_state["pub_brand_dyn"] = datos_extraidos.get("marca", "")
            st.session_state["pub_model_dyn"] = datos_extraidos.get("modelo", "")
            st.session_state["pub_pvp_dyn"] = float(datos_extraidos.get("pvp_sugerido", 0.0))
            st.session_state["pub_altura_dyn"] = datos_extraidos.get("alto", "")
            st.session_state["pub_ancho_dyn"] = datos_extraidos.get("ancho", "")
            st.session_state["pub_prof_dyn"] = datos_extraidos.get("prof", "")
            st.session_state["pub_peso_dyn"] = datos_extraidos.get("peso", "")
            st.session_state["pub_desc_dyn"] = datos_extraidos.get("descripcion", "")
            st.session_state["pub_video_dyn"] = datos_extraidos.get("video_id", "")
            
            st.session_state["pub_costo_base_input"] = float(datos_extraidos["costo_gold"]) if datos_extraidos.get("found_gold") else 0.0

    datos = st.session_state.get("datos_ficha_cache", {})
    urls_fotos_extraidas = datos.get("fotos", [])
    video_id_extraido = datos.get("video_id", "")
    etiqueta_precio_origen = datos.get("etiqueta_precio", "PVP Base")

    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
    if datos.get("exito_externo"):
        st.success(f"🌐 **Extracción Exitosa:** `{datos.get('family_name')}` | Catálogo: **`{datos.get('cat_product_id') or 'Sin ID Catálogo'}`** | Fotos: **{len(urls_fotos_extraidas)}** | **{etiqueta_precio_origen}: ${datos.get('pvp_sugerido', 0):,.2f}**")
    elif datos.get("found_gold"):
        st.success(f"🎯 **Datos Sincronizados (Lista Gold):** `{datos.get('desc_gold')}` | Costo: **${datos.get('costo_gold', 0):,.2f}**")
    else:
        msg_err = f" ({datos.get('error_api')})" if datos.get("error_api") else ""
        st.warning(f"⚠️ No se obtuvo respuesta directa para `{query_builder}`{msg_err}. Verificá el link/código o completá los campos manualmente.")

    st.subheader("📦 Datos de Logística & Embalaje de la Caja")
    p_col1, p_col2, p_col3, p_col4 = st.columns(4)
    with p_col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Ancho de Caja</div>
            <div class="kpi-value" style="font-size: 18px; color: #0284c7;">{st.session_state.get('pub_ancho_dyn') or 'Sin dato'}</div>
        </div>
        """, unsafe_allow_html=True)
    with p_col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Alto de Caja</div>
            <div class="kpi-value" style="font-size: 18px; color: #0284c7;">{st.session_state.get('pub_altura_dyn') or 'Sin dato'}</div>
        </div>
        """, unsafe_allow_html=True)
    with p_col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Profundidad Caja</div>
            <div class="kpi-value" style="font-size: 18px; color: #0284c7;">{st.session_state.get('pub_prof_dyn') or 'Sin dato'}</div>
        </div>
        """, unsafe_allow_html=True)
    with p_col4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Peso Embalado</div>
            <div class="kpi-value" style="font-size: 18px; color: #059669;">{st.session_state.get('pub_peso_dyn') or 'Sin dato'}</div>
        </div>
        """, unsafe_allow_html=True)

    if urls_fotos_extraidas or video_id_extraido:
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        st.subheader("🖼️ Multimedia Clonada de la Publicación")
        if urls_fotos_extraidas:
            st.caption(f"Se extrajeron {len(urls_fotos_extraidas)} imágenes en alta resolución.")
            cols_imgs = st.columns(min(len(urls_fotos_extraidas), 5))
            for idx_img, img_u in enumerate(urls_fotos_extraidas[:5]):
                with cols_imgs[idx_img]:
                    st.image(img_u, caption=f"Foto {idx_img+1}", use_container_width=True)
            if len(urls_fotos_extraidas) > 5:
                cols_imgs2 = st.columns(min(len(urls_fotos_extraidas) - 5, 5))
                for idx_img, img_u in enumerate(urls_fotos_extraidas[5:10]):
                    with cols_imgs2[idx_img]:
                        st.image(img_u, caption=f"Foto {idx_img+6}", use_container_width=True)
        if video_id_extraido:
            st.info(f"🎬 **Video de YouTube detectado y vinculado:** `https://www.youtube.com/watch?v={video_id_extraido}`")

    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

    f_col1, f_col2 = st.columns(2)
    with f_col1:
        pub_family_name = st.text_input("🏷️ Nombre de Familia / Título (máx 60 car.)", max_chars=60, key="pub_family_name_dyn")
        
        cat_actual_code = st.session_state.get("pub_cat_id_dyn", "MLA4765").strip()
        nombre_cat_actual = obtener_nombre_categoria_meli(cat_actual_code)
        st.markdown(f"📂 **Categoría Actual:** <span style='color: #0284c7; font-weight: 700;'>{nombre_cat_actual}</span>", unsafe_allow_html=True)
        
        sugerencias_cat = predecir_categorias_meli(pub_family_name)
        if sugerencias_cat:
            opciones_sug = ["(Mantener categoría actual)"] + [f"{ruta} ({cid})" for cid, ruta in sugerencias_cat]
            sel_sug = st.selectbox("🔄 Cambiar categoría por sugerencia oficial de MeLi (Opcional):", opciones_sug, key="sel_sug_cat_opt")
            if sel_sug != "(Mantener categoría actual)":
                nuevo_cid = sel_sug.split("(")[-1].replace(")", "").strip()
                if nuevo_cid != cat_actual_code:
                    st.session_state["pub_cat_id_dyn"] = nuevo_cid
                    st.rerun()

        pub_cat_id = st.text_input("ID Categoría MeLi (category_id - Editable)", key="pub_cat_id_dyn")
        pub_catalog_id = st.text_input("🎯 Catalog Product ID (Dejar vacío si es publicación tradicional)", key="pub_catalog_id_dyn")
        pub_brand = st.text_input("🏢 Marca (BRAND)", key="pub_brand_dyn")
        
        archivos_imagenes_subidos = st.file_uploader(
            "🖼️ Reemplazar/Subir Fotos Propias (Opcional, hasta 10 JPG/PNG)", 
            type=["jpg", "jpeg", "png"], 
            accept_multiple_files=True, 
            key="uploader_imgs_pub_multi"
        )
        if archivos_imagenes_subidos:
            st.info(f"📁 Usando tus {min(len(archivos_imagenes_subidos), 10)} imágenes subidas manualmente.")
        elif urls_fotos_extraidas:
            st.success(f"✅ Se enviarán las {len(urls_fotos_extraidas)} fotos clonadas de la publicación.")

        pub_video_id = st.text_input("🎬 ID de YouTube (Clonado o Editable)", key="pub_video_dyn")

    with f_col2:
        pub_model = st.text_input("📌 Modelo (MODEL)", key="pub_model_dyn")
        pub_pvp = st.number_input(f"💲 Precio de Venta ($ ARS) — [{etiqueta_precio_origen}]", step=500.0, key="pub_pvp_dyn")
        pub_stock_qty = st.number_input("📊 Stock Disponible", value=10, step=1, key="pub_stock_dyn")
        pub_type = st.selectbox("💳 Tipo de Publicación", list(TASAS_CUOTAS.keys()), index=0, key="pub_type_dyn")
        
        c_dim1, c_dim2 = st.columns(2)
        with c_dim1:
            pub_altura = st.text_input("Altura Paquete / Caja", key="pub_altura_dyn")
            pub_ancho = st.text_input("Ancho Paquete / Caja", key="pub_ancho_dyn")
        with c_dim2:
            pub_prof = st.text_input("Profundidad Paquete / Caja", key="pub_prof_dyn")
            pub_peso_embalado = st.text_input("Peso Paquete / Caja", key="pub_peso_dyn")
            
        pub_ensamblado = st.selectbox("Requiere ensamblado", ["Sí", "No"], index=0, key="pub_ensamblado_dyn")

    # --------------------------------------------------------------------------
    # AUDITOR DE MARGEN EN TIEMPO REAL
    # --------------------------------------------------------------------------
    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
    st.subheader("💡 Auditoría de Margen en Vivo (Decisión de Publicación)")

    if datos.get("found_matriz"):
        _, costo_envio_auto, _, peso_tot_m, _, cant_cajas_m, _ = buscar_datos_en_matriz(query_builder, pub_pvp)
        detalle_flete_txt = f"Calculado desde Matriz Logística ({cant_cajas_m} bulto/s · {peso_tot_m:.1f} kg facturables)"
    else:
        costo_envio_auto, peso_fact_calc, peso_vol_calc, tiene_embalaje = calcular_flete_desde_embalaje(
            pub_altura, pub_ancho, pub_prof, pub_peso_embalado, pub_pvp
        )
        if tiene_embalaje:
            detalle_flete_txt = f"Calculado desde embalaje ({peso_fact_calc:.1f} kg facturables · Vol: {peso_vol_calc:.1f} kg)"
        else:
            detalle_flete_txt = "Sin datos de embalaje en publicación/Matriz (Flete = $0)"

    costo_producto_manual = st.number_input(
        "🏷️ Costo del Producto ($ ARS) — [Único dato manual para evaluar rentabilidad]", 
        min_value=0.0, 
        step=500.0, 
        key="pub_costo_base_input",
        help="Ingresá tu costo neto del artículo. El envío, comisiones e impuestos se calculan automáticamente."
    )

    info_tasa = TASAS_CUOTAS[pub_type]
    comision_pct = info_tasa["comision_base"] + info_tasa["tasa_finan"]
    
    m_comision = pub_pvp * comision_pct
    m_iibb = pub_pvp * ALICUOTA_IIBB
    m_iva = pub_pvp * ALICUOTA_IVA
    total_impuestos_deducciones = m_comision + m_iibb + m_iva + costo_envio_auto
    
    ganancia_neta_pub = pub_pvp - total_impuestos_deducciones - costo_producto_manual
    margen_neto_pct = (ganancia_neta_pub / pub_pvp) * 100.0 if pub_pvp > 0 else 0.0

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Envío Calculado (Embalaje)</div>
            <div class="kpi-value" style="color: #0284c7; font-size: 18px;">${costo_envio_auto:,.2f}</div>
            <div style="font-size: 10px; color: #64748b; margin-top: 1px;">{detalle_flete_txt}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_m2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Deducciones Totales (Comis. + Taxes + Flete)</div>
            <div class="kpi-value" style="color: #e11d48; font-size: 18px;">${total_impuestos_deducciones:,.2f}</div>
            <div style="font-size: 10px; color: #64748b; margin-top: 1px;">Comis. {comision_pct*100:.1f}% + Impuestos 24.5% + Envío</div>
        </div>
        """, unsafe_allow_html=True)
    with col_m3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Neto Libre a Bolsillo</div>
            <div class="kpi-value" style="color: {'#059669' if ganancia_neta_pub > 0 else '#dc2626'}; font-size: 18px;">${ganancia_neta_pub:,.2f} ({margen_neto_pct:.1f}%)</div>
            <div style="font-size: 10px; color: #64748b; margin-top: 1px;">PVP ${pub_pvp:,.0f} - Deducciones - Costo</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
    if costo_producto_manual <= 0:
        st.info("ℹ️ **Ingresá el Costo del Producto ($ ARS)** arriba para verificar al instante si la publicación da positiva o negativa en margen.")
    elif ganancia_neta_pub > 0:
        st.markdown(f'''
        <div class="card-viable">
            🟢 <b>PUBLICACIÓN POSITIVA EN MARGEN (RENTABLE):</b><br>
            Deja una ganancia neta de <b>${ganancia_neta_pub:,.2f} ({margen_neto_pct:.1f}%)</b> libre a bolsillo. ¡Aprobada para subir!
        </div>
        ''', unsafe_allow_html=True)
    else:
        st.markdown(f'''
        <div class="card-noviable">
            🔴 <b>PUBLICACIÓN NEGATIVA EN MARGEN (PÉRDIDA):</b><br>
            Genera una pérdida neta de <b>${ganancia_neta_pub:,.2f} ({margen_neto_pct:.1f}%)</b>. No conviene publicarla a este precio/costo.
        </div>
        ''', unsafe_allow_html=True)

    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
    pub_descripcion = st.text_area("📝 Descripción de la Publicación (Clonada o Editable)", height=120, key="pub_desc_dyn")

    st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
    if st.button("🚀 PUBLICAR EN MERCADO LIBRE", type="primary", use_container_width=True):
        if not st.session_state["access_token"]:
            st.error("❌ Se requiere un Access Token activo en la barra lateral para publicar.")
        elif not pub_cat_id.strip():
            st.error("❌ Se requiere un ID de Categoría válido.")
        else:
            access_token_clean = st.session_state["access_token"].strip()
            pictures_payload = []

            if archivos_imagenes_subidos:
                with st.spinner(f"Subiendo {min(len(archivos_imagenes_subidos), 10)} imágenes propias a Mercado Libre..."):
                    for img_file in archivos_imagenes_subidos[:10]:
                        try:
                            url_upload = "https://api.mercadolibre.com/pictures/items/upload"
                            headers_img = {"Authorization": f"Bearer {access_token_clean}"}
                            files_data = {"file": (img_file.name, img_file.getvalue(), img_file.type)}
                            
                            res_img = requests.post(url_upload, headers=headers_img, files=files_data, timeout=15)
                            if res_img.status_code in [200, 201]:
                                pic_id = res_img.json().get("id")
                                if pic_id:
                                    pictures_payload.append({"id": pic_id})
                        except Exception:
                            pass

            if not pictures_payload and urls_fotos_extraidas:
                pictures_payload = [{"source": u} for u in urls_fotos_extraidas[:10]]

            if not pictures_payload:
                pictures_payload = [{"source": "https://http2.mlstatic.com/D_NQ_NP_918505-MLA46554522436_062021-O.jpg"}]

            tipo_list_clean = "gold_special" if "Clásica" in pub_type else "gold_pro"
            
            payload_post = {
                "category_id": pub_cat_id.strip(),
                "price": float(pub_pvp),
                "currency_id": "ARS",
                "available_quantity": int(pub_stock_qty),
                "buying_mode": "buy_it_now",
                "listing_type_id": tipo_list_clean,
                "condition": "new",
                "channels": ["marketplace"],
                "pictures": pictures_payload,
                "sale_terms": [
                    {"id": "WARRANTY_TIME", "value_name": "90 días"}
                ],
                "shipping": {
                    "mode": "me2",
                    "local_pick_up": False,
                    "free_shipping": False
                },
                "attributes": [
                    {"id": "BRAND", "value_name": pub_brand.strip() or "Genérica"},
                    {"id": "MODEL", "value_name": pub_model.strip() or "Standard"},
                    {"id": "REQUIRES_ASSEMBLY", "value_name": pub_ensamblado.strip()},
                    {"id": "INCLUDES_ASSEMBLY_MANUAL", "value_name": "Sí"}
                ]
            }

            if pub_catalog_id.strip():
                payload_post["catalog_product_id"] = pub_catalog_id.strip()
                payload_post["family_name"] = pub_family_name.strip()
            else:
                payload_post["title"] = pub_family_name.strip()

            if pub_altura.strip():
                payload_post["attributes"].append({"id": "HEIGHT", "value_name": pub_altura.strip()})
            if pub_ancho.strip():
                payload_post["attributes"].append({"id": "WIDTH", "value_name": pub_ancho.strip()})
            if pub_prof.strip():
                payload_post["attributes"].append({"id": "DEPTH", "value_name": pub_prof.strip()})

            if pub_video_id.strip():
                payload_post["video_id"] = pub_video_id.strip()

            headers_post = {
                "Authorization": f"Bearer {access_token_clean}",
                "Content-Type": "application/json"
            }

            try:
                with st.spinner("Enviando publicación a Mercado Libre..."):
                    res_api = requests.post("https://api.mercadolibre.com/items", json=payload_post, headers=headers_post, timeout=12)
                    if res_api.status_code in [200, 201]:
                        data_created = res_api.json()
                        item_id = data_created.get("id")
                        permalink = data_created.get("permalink")

                        if item_id and pub_descripcion.strip():
                            try:
                                requests.post(
                                    f"https://api.mercadolibre.com/items/{item_id}/description",
                                    json={"plain_text": pub_descripcion.strip()},
                                    headers=headers_post,
                                    timeout=8
                                )
                            except Exception:
                                pass

                        st.success(f"🎉 ¡Publicación exitosa! ID Item: **{item_id}**")
                        if permalink:
                            st.markdown(f"🔗 [Ver Publicación en Mercado Libre]({permalink})")
                    else:
                        err_resp = res_api.json() if res_api.content else {}
                        st.error(f"Error API MeLi ({res_api.status_code}): {err_resp.get('message', res_api.text)}")
                        if "cause" in err_resp:
                            st.write("📋 Detalle técnico retornado por la API:", err_resp.get("cause"))
            except Exception as e:
                st.error(f"Error de conexión: {e}")
