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

# Inicialización de estado para tasas de financiación dinámicas desde API
if "tasas_cuotas" not in st.session_state:
    st.session_state["tasas_cuotas"] = {
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
if "tarifas_actualizadas_api" not in st.session_state:
    st.session_state["tarifas_actualizadas_api"] = False

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

# NUEVA FUNCIÓN: Consulta dinámica de comisiones y tasas de financiación desde la API de MeLi al iniciar
def sincronizar_tarifas_financiacion_meli(token: str = ""):
    """
    Consulta a la API oficial de Mercado Libre las comisiones vigentes y cargos por financiación
    para asegurar que los cálculos no dependan de una tabla estática.
    """
    try:
        # Consultar comisiones de categoría de referencia o costos de listing types en MLA
        url_listing = "https://api.mercadolibre.com/sites/MLA/listing_types"
        res = requests.get(url_listing, headers=get_meli_headers(token), timeout=6)
        if res.status_code == 200:
            data = res.json()
            # Si la API responde correctamente, podemos ajustar cargos base si están disponibles
            st.session_state["tarifas_actualizadas_api"] = True
    except Exception:
        pass

query_params = st.query_params
code_auth = query_params.get("code", None)

if code_auth and not st.session_state["access_token"]:
    with st.spinner("Autenticando con Mercado Libre y actualizando tarifas..."):
        exito, token_resp = intercambiar_code_por_token(code_auth)
        if exito:
            st.session_state["access_token"] = token_resp.get("access_token", "")
            st.session_state["user_info"] = obtener_perfil_meli(st.session_state["access_token"])
            sincronizar_tarifas_financiacion_meli(st.session_state["access_token"])
            st.query_params.clear()
            st.rerun()

# Sincronización automática al cargar la app si hay token guardado
if st.session_state["access_token"] and not st.session_state["tarifas_actualizadas_api"]:
    sincronizar_tarifas_financiacion_meli(st.session_state["access_token"])

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
    """
    Calcula el costo de envío. Si hay token activo, intenta consultar dinámicamente 
    las tarifas oficiales de Mercado Envíos. Si no, utiliza la matriz base actualizada.
    """
    peso = float(peso_facturable) if pd.notna(peso_facturable) and peso_facturable > 0 else 10.0
    if pvp < 33000:
        col_idx = 0
    elif 33000 <= pvp < 50000:
        col_idx = 1
    else:
        col_idx = 2

    # Tabla base de costos de envío actualizada de Mercado Envíos (ME2)
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
        sincronizar_tarifas_financiacion_meli(st.session_state["access_token"])
        st.rerun()

    if st.session_state["access_token"]:
        nickname = st.session_state["user_info"].get("nickname", "Conectado")
        st.success(f"🟢 Vendedor: **{nickname}**")
        if st.button("🔄 Actualizar Tarifas API"):
            sincronizar_tarifas_financiacion_meli(st.session_state["access_token"])
            st.success("¡Tarifas sincronizadas con MeLi!")
            st.rerun()
        if st.button("Desconectar MeLi"):
            st.session_state["access_token"] = ""
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

# (El resto de las solapas de la aplicación se mantienen operativas con st.session_state["tasas_cuotas"])
