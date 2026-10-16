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

    if "DESCRIPCION"
