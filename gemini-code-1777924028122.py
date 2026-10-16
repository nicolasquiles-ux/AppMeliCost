import io
import re
import os
from datetime import datetime
import pandas as pd
import requests
import streamlit as st

# Módulo OAuth local opcional
try:
    import meli_auth
    HAS_MELI_AUTH = True
except ImportError:
    HAS_MELI_AUTH = False

V_NUMBER = "42.0 Pro SaaS"

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title=f"NQ | Sales Intelligence Matrix v{V_NUMBER}",
    layout="wide",
    initial_sidebar_state="expanded"
)

HEADERS_MELI = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

# =========================================================
# 1. FUNCIÓN DE LIMPIEZA DE ESTRUCTURA PANDAS
# =========================================================
def procesar_dataframe_lista_gold(df_raw):
    """Procesa cualquier DataFrame (Excel/CSV/Google Sheets) y extrae EAN, SKU, Descripción y Costo."""
    try:
        header_row = None
        for idx, row in df_raw.iterrows():
            row_str = [str(val).upper() for val in row.values if pd.notna(val)]
            if any("EAN" in x for x in row_str) or any("ARTICULO" in x for x in row_str):
                header_row = idx
                break

        if header_row is not None:
            df = df_raw.iloc[header_row + 1:].copy()
            df.columns = [str(c).strip().upper() for c in df_raw.iloc[header_row].values]
        else:
            df = df_raw.copy()
            df.columns = [str(c).strip().upper() for c in df.columns]

        col_ean = [c for c in df.columns if "EAN" in c]
        col_art = [c for c in df.columns if "ART" in c]
        col_desc = [c for c in df.columns if "DESC" in c]
        col_precio = [c for c in df.columns if any(k in c for k in ["LISTA", "PRECIO", "SEPT", "CE", "GOLD", "COSTO"])]

        renames = {}
        if col_ean: renames[col_ean[0]] = "EAN"
        if col_art: renames[col_art[0]] = "ARTICULO"
        if col_desc: renames[col_desc[0]] = "DESCRIPCION"
        if col_precio: renames[col_precio[0]] = "COSTO_LISTA_GOLD"

        df = df.rename(columns=renames)

        if "EAN" in df.columns and "COSTO_LISTA_GOLD" in df.columns:
            df = df.dropna(subset=["EAN", "COSTO_LISTA_GOLD"], how="all")
            df["EAN"] = df["EAN"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
            df["COSTO_LISTA_GOLD"] = pd.to_numeric(df["COSTO_LISTA_GOLD"], errors="coerce").fillna(0.0)
            df = df[df["COSTO_LISTA_GOLD"] > 0]
            return df
    except Exception:
        pass
    return pd.DataFrame()

# =========================================================
# 2. CARGA MULTI-FUENTE (UPLOADER + GSHEETS + ARCHIVO LOCAL)
# =========================================================
def Cargar_lista_precios_general(uploaded_file, url_gsheets):
    # Fuente 1: Archivo subido manualmente en el sidebar o pantalla
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                df_raw = pd.read_csv(uploaded_file)
            else:
                df_raw = pd.read_excel(uploaded_file, header=None)
            df_proc = procesar_dataframe_lista_gold(df_raw)
            if not df_proc.empty:
                return df_proc, "Archivo Subido Manualmente"
        except Exception:
            pass

    # Fuente 2: Google Sheets con auto-corrección de URL
    if url_gsheets:
        url_clean = str(url_gsheets).strip()
        if "docs.google.com" in url_clean:
            try:
                pos = url_clean.find("docs.google.com")
                url_fixed = "https://" + url_clean[pos:]
                sheet_id = url_fixed.split("/d/")[1].split("/")[0]
                csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
                df_gsheet = pd.read_csv(csv_url)
                df_proc = procesar_dataframe_lista_gold(df_gsheet)
                if not df_proc.empty:
                    return df_proc, "Google Sheets en Vivo"
            except Exception:
                pass

    # Fuente 3: Archivo local en el servidor
    nombre_archivo = "Lista de Precios Centro Estant Septiembre 2026 (LISTA GOLD).xlsx"
    if os.path.exists(nombre_archivo):
        try:
            df_raw = pd.read_excel(nombre_archivo, header=None)
            df_proc = procesar_dataframe_lista_gold(df_raw)
            if not df_proc.empty:
                return df_proc, "Excel Local Gold Septiembre 2026"
        except Exception:
            pass

    # Fuente 4: Matriz Gemini secundaria
    if os.path.exists("Matriz Articulos Gemini.xlsm"):
        try:
            df_raw = pd.read_excel("Matriz Articulos Gemini.xlsm", sheet_name=0)
            df_proc = procesar_dataframe_lista_gold(df_raw)
            if not df_proc.empty:
                return df_proc, "Matriz Gemini Local"
        except Exception:
            pass

    return pd.DataFrame(), "Sin Cargar"

# --- SIDEBAR: CARGA DE ARCHIVOS Y REFRESH ---
st.sidebar.title("📁 Cargar Lista de Precios Gold")
file_up_sidebar = st.sidebar.file_uploader(
    "Subir Lista Excel (.xlsx / .csv)",
    type=["xlsx", "csv"],
    key="file_up_side"
)

url_gsheet_input = st.sidebar.text_input(
    "🌐 Enlace Google Sheets",
    placeholder="https://docs.google.com/spreadsheets/d/...",
    key="url_gsheet_sidebar"
)

if st.sidebar.button("🔄 Recargar Matriz de Precios", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

df_articulos_base, origen_lista = Cargar_lista_precios_general(file_up_sidebar, url_gsheet_input)

def buscar_costo_lista_gold(term_busqueda):
    if df_articulos_base.empty or not term_busqueda:
        return 70500.0

    term_str = str(term_busqueda).strip().upper()

    match_ean = df_articulos_base[df_articulos_base["EAN"] == term_str]
    if not match_ean.empty:
        return float(match_ean.iloc[0]["COSTO_LISTA_GOLD"])

    if "ARTICULO" in df_articulos_base.columns:
        match_art = df_articulos_base[df_articulos_base["ARTICULO"].astype(str).str.upper() == term_str]
        if not match_art.empty:
            return float(match_art.iloc[0]["COSTO_LISTA_GOLD"])

    if "DESCRIPCION" in df_articulos_base.columns:
        match_desc = df_articulos_base[df_articulos_base["DESCRIPCION"].astype(str).str.upper().str.contains(term_str)]
        if not match_desc.empty:
            return float(match_desc.iloc[0]["COSTO_LISTA_GOLD"])

    return 70500.0

# TABLA MAESTRA ME2
TABLA_ME2_BASE = {
    "Hasta 0,3 kg": [7868.0, 3934.0, 6080.0],
    "De 0,3 a 0,5 kg": [8596.0, 4298.0, 6600.0],
    "De 0,5 a 1 kg": [9800.0, 4900.0, 7470.0],
    "De 1 a 1,5 kg": [10122.0, 5061.0, 7720.0],
    "De 1,5 a 2 kg": [10458.0, 5229.0, 7970.0],
    "De 2 a 3 kg": [11550.0, 5775.0, 8710.0],
    "De 3 a 4 kg": [12866.0, 6433.0, 9860.0],
    "De 4 a 5 kg": [14070.0, 7035.0, 10760.0],
    "De 5 a 8 kg": [15512.0, 7756.0, 11830.0],
    "De 8 a 10 kg": [16926.0, 8463.0, 12840.0],
    "De 10 a 13 kg": [18270.0, 9135.0, 13920.0],
    "De 13 a 15 kg": [19684.0, 9842.0, 14930.0],
    "De 15 a 20 kg": [23506.0, 11753.0, 17830.0],
    "De 20 a 25 kg": [28182.0, 14091.0, 21420.0],
    "De 25 a 30 kg": [38780.0, 19390.0, 29410.0],
    "De 30 a 40 kg": [44268.0, 22134.0, 33570.0],
}

REPUTACION_DESCUENTOS = {
    "Verde / MercadoLíder (50% desc)": 0.50,
    "Amarilla (40% desc)": 0.60,
    "Roja / Sin Reputación (0% desc)": 1.00,
}

FINANCIACION_PRESETS = {
    "1 Pago / Clásica (0.00%)": 0.0,
    "2 Cuotas Mismo Precio (9.49%)": 9.49,
    "3 Cuotas Mismo Precio (12.19%)": 12.19,
    "6 Cuotas Mismo Precio (19.09%)": 19.09,
    "9 Cuotas Mismo Precio (27.29%)": 27.29,
    "12 Cuotas Mismo Precio (32.29%)": 32.29,
    "18 Cuotas Mismo Precio (41.59%)": 41.59,
}

CLAVE_CORRECTA = "NQ_PRO_2026"
UMBRAL_ENVIO_GRATIS = 33000.0
CARGO_FIJO_MELI = 3800.0
TARIFA_FLEX_AMBA = 4500.0
nq_main_color = "#
