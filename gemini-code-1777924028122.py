import io
import math
import re
import time
from urllib.parse import unquote, urlparse

import numpy as np
import pandas as pd
import requests
import streamlit as st

try:
    from PIL import Image, ImageOps
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

APP_VERSION = "v191.0"

ALICUOTA_IIBB = 0.035
ALICUOTA_IVA = 0.21

DEFAULT_TASAS_CUOTAS = {
    "Clásica (Sin cuotas / 1 pago)": {"comision_base": 0.145, "tasa_finan": 0.0},
    "Premium 3 cuotas s/interés": {"comision_base": 0.145, "tasa_finan": 0.055},
    "Premium 6 cuotas s/interés": {"comision_base": 0.145, "tasa_finan": 0.095},
    "Premium 9 cuotas s/interés": {"comision_base": 0.145, "tasa_finan": 0.130},
    "Premium 12 cuotas s/interés": {"comision_base": 0.145, "tasa_finan": 0.165},
}

TRAMOS_FLETE_ME2 = [
    (0.5, 4200.0),
    (1.0, 5100.0),
    (2.0, 6400.0),
    (5.0, 9800.0),
    (10.0, 14900.0),
    (15.0, 19800.0),
    (20.0, 24600.0),
    (30.0, 32500.0),
    (50.0, 44900.0),
    (100.0, 68000.0),
]

st.set_page_config(
    page_title=f"NQ Argentina | MeLi Intelligence ({APP_VERSION})",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .exec-hero-banner {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 65%, #064e3b 100%);
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 14px 20px;
            margin-bottom: 10px;
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            color: #f8fafc;
        }
        .exec-hero-left {
            display: flex;
            align-items: center;
            gap: 14px;
        }
        .exec-logo-badge {
            background: #10b981;
            color: #06281e;
            font-weight: 900;
            font-size: 16px;
            width: 42px;
            height: 42px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .exec-hero-title {
            font-size: 19px;
            font-weight: 800;
            letter-spacing: -0.01em;
            color: #ffffff;
        }
        .exec-hero-title span {
            color: #34d399;
        }
        .exec-version-tag {
            background: rgba(16, 185, 129, 0.2);
            color: #6ee7b7;
            border: 1px solid rgba(52, 211, 153, 0.4);
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 999px;
            margin-left: 6px;
            font-weight: 700;
        }
        .exec-hero-subtitle {
            font-size: 12px;
            color: #cbd5e1;
            margin-top: 2px;
        }
        .exec-status-group {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        .exec-status-pill {
            background: rgba(15, 23, 42, 0.72);
            border: 1px solid #475569;
            border-radius: 8px;
            padding: 6px 12px;
            min-width: 125px;
        }
        .exec-pill-lbl {
            font-size: 10px;
            text-transform: uppercase;
            color: #94a3b8;
            font-weight: 700;
        }
        .exec-pill-val {
            font-size: 12px;
            font-weight: 700;
            color: #f8fafc;
            margin-top: 1px;
        }
        .kpi-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 12px 14px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        }
        .kpi-label {
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            color: #64748b;
        }
        .kpi-value {
            font-size: 21px;
            font-weight: 800;
            margin-top: 3px;
        }
        .card-viable {
            background: #ecfdf5;
            border: 1px solid #10b981;
            color: #065f46;
            padding: 12px 14px;
            border-radius: 8px;
            font-size: 13px;
        }
        .card-noviable {
            background: #fef2f2;
            border: 1px solid #ef4444;
            color: #991b1b;
            padding: 12px 14px;
            border-radius: 8px;
            font-size: 13px;
        }
        .badge-missing {
            background: #fff1f2;
            border: 1px solid #fda4af;
            color: #9f1239;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 600;
        }
        .warning-stock {
            background: #fffbeb;
            border: 1px solid #f59e0b;
            color: #92400e;
            padding: 10px 14px;
            border-radius: 8px;
            font-size: 13px;
        }
        .mla-focus-box {
            background: #f8fafc;
            border-left: 4px solid #0284c7;
            border-top: 1px solid #e2e8f0;
            border-right: 1px solid #e2e8f0;
            border-bottom: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 12px;
        }
        .ai-bubble {
            background: #f0fdf4;
            border: 1px solid #86efac;
            color: #14532d;
            padding: 14px 16px;
            border-radius: 10px;
            font-size: 13px;
            line-height: 1.5;
        }
        .nav-btn-wrap button {
            font-size: 12px !important;
            font-weight: 700 !important;
            padding: 6px 8px !important;
            border-radius: 8px !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = 0
if "access_token" not in st.session_state:
    st.session_state["access_token"] = ""
if "user_info" not in st.session_state:
    st.session_state["user_info"] = {}
if "tasas_cuotas" not in st.session_state:
    st.session_state["tasas_cuotas"] = {k: dict(v) for k, v in DEFAULT_TASAS_CUOTAS.items()}
if "tarifas_actualizadas_api" not in st.session_state:
    st.session_state["tarifas_actualizadas_api"] = False
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
if "q_mercado_mla" not in st.session_state:
    st.session_state["q_mercado_mla"] = "MLA1456789012"


def obtener_url_login_meli() -> str:
    client_id = ""
    redirect_uri = ""
    try:
        client_id = str(st.secrets.get("MELI_CLIENT_ID", "") or "")
        redirect_uri = str(st.secrets.get("MELI_REDIRECT_URI", st.secrets.get("REDIRECT_URI", "")) or "")
    except Exception:
        pass
    if client_id and redirect_uri:
        return (
            f"https://auth.mercadolibre.com.ar/authorization?response_type=code"
            f"&client_id={requests.utils.quote(client_id)}"
            f"&redirect_uri={requests.utils.quote(redirect_uri)}"
        )
    return "https://developers.mercadolibre.com.ar/"


def get_meli_headers(access_token: str = "") -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }
    token_eff = (access_token or st.session_state.get("access_token") or "").strip()
    if token_eff:
        headers["Authorization"] = f"Bearer {token_eff}"
    return headers


def obtener_perfil_meli(access_token: str) -> dict:
    if not access_token or not access_token.strip():
        return {}
    try:
        r = requests.get("https://api.mercadolibre.com/users/me", headers=get_meli_headers(access_token), timeout=8)
        if r.status_code == 200:
            data = r.json()
            return {
                "id": data.get("id"),
                "nickname": data.get("nickname") or "Vendedor Conectado",
                "site_id": data.get("site_id") or "MLA",
            }
    except Exception:
        pass
    return {"nickname": "Token Configurado"}


def sincronizar_tarifas_financiacion_meli(access_token: str):
    if not access_token or not access_token.strip():
        return
    try:
        r = requests.get(
            "https://api.mercadolibre.com/sites/MLA/listing_prices?price=200000&listing_type_id=gold_pro",
            headers=get_meli_headers(access_token),
            timeout=8,
        )
        if r.status_code == 200:
            st.session_state["tarifas_actualizadas_api"] = True
    except Exception:
        pass


def limpiar_precio_moneda(valor) -> float:
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    txt = str(valor).strip()
    if not txt:
        return 0.0
    txt = re.sub(r"[^\d,.-]", "", txt)
    if not txt:
        return 0.0
    if "," in txt and "." in txt:
        if txt.rfind(",") > txt.rfind("."):
            txt = txt.replace(".", "").replace(",", ".")
        else:
            txt = txt.replace(",", "")
    elif "," in txt:
        partes = txt.split(",")
        if len(partes[-1]) == 2:
            txt = txt.replace(".", "").replace(",", ".")
        else:
            txt = txt.replace(",", "")
    elif "." in txt:
        partes = txt.split(".")
        if len(partes[-1]) == 3 and len(partes) > 1:
            txt = txt.replace(".", "")
    try:
        return float(txt)
    except Exception:
        return 0.0


def normalizar_ean_matriz(valor) -> str:
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return ""
    if isinstance(valor, (int, float)):
        if float(valor).is_integer():
            s = str(int(round(float(valor))))
        else:
            s = re.sub(r"\D", "", str(valor))
    else:
        s = str(valor).strip()
        if re.match(r"^\d+\.0+$", s):
            s = s.split(".")[0]
        s = re.sub(r"\D", "", s)
    if len(s) in (8, 12, 13, 14):
        return s
    return s if len(s) >= 8 else ""


def procesar_archivo_lista_gold(uploaded_file):
    if uploaded_file is None:
        return None
    try:
        if uploaded_file.name.lower().endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error al procesar Lista Gold: {e}")
        return None


def cargar_matriz_articulos_oficial():
    if st.session_state.get("matriz_custom_df") is not None:
        return st.session_state["matriz_custom_df"]
    return None


def extraer_opciones_ean_lista_gold():
    df_g = st.session_state.get("lista_gold_df")
    if df_g is None or df_g.empty:
        return []
    col_ean = next((c for c in df_g.columns if str(c).strip().lower() in ("ean", "codigo", "cod", "sku", "barcode")), None)
    col_desc = next((c for c in df_g.columns if "desc" in str(c).lower() or "titulo" in str(c).lower() or "nombre" in str(c).lower()), None)
    col_art = next((c for c in df_g.columns if "art" in str(c).lower() or "modelo" in str(c).lower()), None)
    if not col_ean:
        return []
    opciones = []
    for _, r in df_g.iterrows():
        ean_v = normalizar_ean_matriz(r.get(col_ean, ""))
        if not ean_v:
            continue
        desc_v = str(r.get(col_desc, "") if col_desc else "").strip()
        art_v = str(r.get(col_art, "") if col_art else "").strip()
        lbl = f"{ean_v} — {desc_v or art_v or 'Producto'}"
        opciones.append((lbl, ean_v))
    return opciones[:200]


def buscar_costo_y_titulo_en_lista_gold(query: str):
    q = str(query or "").strip()
    df_g = st.session_state.get("lista_gold_df")
    if not q or df_g is None or df_g.empty:
        return False, 0.0, "", ""

    q_limpio = re.sub(r"\D", "", q)
    q_low = q.lower()

    col_ean = next((c for c in df_g.columns if str(c).strip().lower() in ("ean", "codigo", "cod", "sku", "barcode")), None)
    col_costo = next((c for c in df_g.columns if "costo" in str(c).lower() or "precio" in str(c).lower() or "valor" in str(c).lower()), None)
    col_desc = next((c for c in df_g.columns if "desc" in str(c).lower() or "titulo" in str(c).lower() or "nombre" in str(c).lower()), None)
    col_art = next((c for c in df_g.columns if "art" in str(c).lower() or "modelo" in str(c).lower()), None)

    for _, row in df_g.iterrows():
        match = False
        if col_ean:
            ean_row = normalizar_ean_matriz(row.get(col_ean, ""))
            if q_limpio and ean_row and q_limpio == ean_row:
                match = True
            elif str(row.get(col_ean, "")).strip().lower() == q_low:
                match = True
        if not match and col_art and str(row.get(col_art, "")).strip().lower() == q_low:
            match = True
        if not match and col_desc and len(q_low) >= 4 and q_low in str(row.get(col_desc, "")).lower():
            match = True

        if match:
            costo_val = limpiar_precio_moneda(row.get(col_costo, 0.0)) if col_costo else 0.0
            desc_val = str(row.get(col_desc, "") if col_desc else "").strip()
            art_val = str(row.get(col_art, "") if col_art else "").strip()
            return True, costo_val, desc_val, art_val

    return False, 0.0, "", ""


def calcular_costo_envio_por_peso_facturable(peso_facturable_kg: float, pvp: float = 208000.0) -> float:
    peso = max(0.1, float(peso_facturable_kg or 1.0))
    tarifa = TRAMOS_FLETE_ME2[-1][1]
    for limite_kg, monto in TRAMOS_FLETE_ME2:
        if peso <= limite_kg:
            tarifa = monto
            break
    if peso > 100.0:
        extra_kg = peso - 100.0
        tarifa = TRAMOS_FLETE_ME2[-1][1] + (extra_kg * 550.0)
    return round(tarifa, 2)


def calcular_flete_desde_embalaje(alto_str, ancho_str, prof_str, peso_str, pvp: float = 208000.0):
    def _num(v):
        if v is None:
            return 0.0
        m = re.search(r"(\d+(?:[.,]\d+)?)", str(v))
        return float(m.group(1).replace(",", ".")) if m else 0.0

    alto = _num(alto_str)
    ancho = _num(ancho_str)
    prof = _num(prof_str)
    peso_real = _num(peso_str)

    tiene_dims = alto > 0 and ancho > 0 and prof > 0
    tiene_peso = peso_real > 0
    if not tiene_dims and not tiene_peso:
        return 0.0, 0.0, 0.0, False

    peso_vol = (alto * ancho * prof) / 4500.0 if tiene_dims else 0.0
    peso_fact = max(peso_real, peso_vol)
    costo = calcular_costo_envio_por_peso_facturable(peso_fact, pvp)
    return costo, peso_fact, peso_vol, True


def buscar_datos_en_matriz(query: str, pvp: float = 208000.0):
    df_m = cargar_matriz_articulos_oficial()
    q = str(query or "").strip().lower()
    if not q or df_m is None or df_m.empty:
        return False, 0.0, 0.0, 0.0, 0.0, 1, ""

    q_num = re.sub(r"\D", "", q)
    for _, row in df_m.iterrows():
        art = str(row.get("Articulo", "") or "").strip().lower()
        ean = normalizar_ean_matriz(row.get("ean", ""))
        desc = str(row.get("Descripcion", "") or "").strip().lower()
        if (q == art) or (q_num and ean and q_num == ean) or (len(q) >= 4 and q in desc):
            cajas = max(1, int(pd.to_numeric(row.get("Cajas", 1), errors="coerce") or 1))
            peso_unit = max(0.5, float(pd.to_numeric(row.get("Peso", 5.0), errors="coerce") or 5.0))
            peso_tot = peso_unit * cajas
            costo_tot = calcular_costo_envio_por_peso_facturable(peso_tot, pvp)
            tarifa_unit = round(costo_tot / cajas, 2)
            return True, costo_tot, peso_unit, peso_tot, tarifa_unit, cajas, str(row.get("Descripcion", ""))

    return False, 0.0, 0.0, 0.0, 0.0, 1, ""


def buscar_datos_en_matriz_completa(query: str):
    df_m = cargar_matriz_articulos_oficial()
    q = str(query or "").strip().lower()
    if not q or df_m is None or df_m.empty:
        return "", "", "", ""
    q_num = re.sub(r"\D", "", q)
    for _, row in df_m.iterrows():
        art = str(row.get("Articulo", "") or "").strip().lower()
        ean = normalizar_ean_matriz(row.get("ean", ""))
        desc = str(row.get("Descripcion", "") or "").strip().lower()
        if (q == art) or (q_num and ean and q_num == ean) or (len(q) >= 4 and q in desc):
            ancho = str(row.get("Ancho", "") or "")
            alto = str(row.get("Alto", "") or "")
            prof = str(row.get("Profundidad", "") or row.get("Largo", "") or "")
            peso = str(row.get("Peso", "") or "")
            return ancho, alto, prof, peso
    return "", "", "", ""


def calcular_peso_facturable_fila_matriz(row) -> float:
    peso = float(pd.to_numeric(row.get("Peso", 0), errors="coerce") or 0.0)
    cajas = max(1.0, float(pd.to_numeric(row.get("Cajas", 1), errors="coerce") or 1.0))
    alto = float(pd.to_numeric(row.get("Alto", 0), errors="coerce") or 0.0)
    ancho = float(pd.to_numeric(row.get("Ancho", 0), errors="coerce") or 0.0)
    prof = float(pd.to_numeric(row.get("Profundidad", row.get("Largo", 0)), errors="coerce") or 0.0)
    vol_kg = (alto * ancho * prof / 4500.0) if (alto > 0 and ancho > 0 and prof > 0) else 0.0
    return max(peso * cajas, vol_kg * cajas, 1.0)


def dataframe_a_excel_bytes(df: pd.DataFrame, sheet_name: str = "Hoja1") -> bytes:
    bio = io.BytesIO()
    safe_sheet = re.sub(r"[\\/*?:\[\]]", "_", str(sheet_name or "Hoja1"))[:31] or "Hoja1"
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=safe_sheet, index=False)
    bio.seek(0)
    return bio.getvalue()


def extraer_ids_meli_avanzado(texto_input: str) -> dict:
    raw = str(texto_input or "").strip()
    resultado = {
        "raw": raw,
        "tipo": "TEXT",
        "url_original": raw if raw.startswith("http") else "",
        "item_id": "",
        "alt_item_id": "",
        "catalog_id": "",
        "ean": "",
    }
    if not raw:
        return resultado

    limpio_num = re.sub(r"\D", "", raw)
    if re.fullmatch(r"\d{8,14}", limpio_num) and not re.search(r"MLA|MLBU|MLCU|MLMU", raw, re.IGNORECASE):
        resultado["tipo"] = "EAN"
        resultado["ean"] = limpio_num
        return resultado

    m_cat_p = re.search(r"/p/(MLA\d+)", raw, re.IGNORECASE)
    if m_cat_p:
        resultado["tipo"] = "MELI_URL_OR_ID"
        resultado["catalog_id"] = m_cat_p.group(1).upper()

    m_item_dash = re.search(r"\b(MLA|MLBU|MLCU|MLMU)[-_]?(\d{5,15})\b", raw, re.IGNORECASE)
    if m_item_dash:
        resultado["tipo"] = "MELI_URL_OR_ID"
        prefix = m_item_dash.group(1).upper()
        num = m_item_dash.group(2)
        if prefix == "MLA":
            resultado["item_id"] = f"MLA{num}"
        else:
            resultado["alt_item_id"] = f"{prefix}{num}"

    m_wid = re.search(r"[?&]wid=(MLA\d+)", raw, re.IGNORECASE)
    if m_wid:
        resultado["tipo"] = "MELI_URL_OR_ID"
        if not resultado["item_id"]:
            resultado["item_id"] = m_wid.group(1).upper()
        elif not resultado["alt_item_id"]:
            resultado["alt_item_id"] = m_wid.group(1).upper()

    if resultado["tipo"] == "TEXT" and re.fullmatch(r"(?:MLA|MLBU|MLCU|MLMU)-?\d{5,15}", raw, re.IGNORECASE):
        resultado["tipo"] = "MELI_URL_OR_ID"
        solo_num = re.sub(r"\D", "", raw)
        if raw.upper().startswith("MLA"):
            resultado["item_id"] = f"MLA{solo_num}"
        else:
            resultado["alt_item_id"] = raw.upper().replace("-", "")

    return resultado


def extraer_id_catalogo_o_ean_input(query_key: str):
    q = str(query_key or "").strip()
    if not q:
        return "TEXT", ""
    m_cat = re.fullmatch(r"(MLA\d{6,14})", q, re.IGNORECASE)
    if m_cat:
        return "CATALOG_ID", m_cat.group(1).upper()
    ean = normalizar_ean_matriz(q)
    if ean:
        return "EAN", ean
    return "TEXT", q


def construir_url_canonica_meli(item_id: str = "", permalink: str = "", catalog_id: str = "") -> str:
    p = str(permalink or "").strip()
    if p.startswith("http"):
        return p
    iid = str(item_id or "").strip().upper()
    if iid.startswith("MLA"):
        num = re.sub(r"\D", "", iid)
        if num:
            return f"https://articulo.mercadolibre.com.ar/MLA-{num}"
    cid = str(catalog_id or "").strip().upper()
    if cid.startswith("MLA"):
        return f"https://www.mercadolibre.com.ar/p/{cid}"
    return ""


@st.cache_data(ttl=3600)
def resolver_vendedor_nickname_oficial(seller_id, access_token: str = "") -> str:
    if not seller_id:
        return "Vendedor MeLi"
    try:
        r = requests.get(
            f"https://api.mercadolibre.com/users/{seller_id}",
            headers=get_meli_headers(access_token),
            timeout=6,
        )
        if r.status_code == 200:
            nick = r.json().get("nickname")
            if nick:
                return str(nick)
    except Exception:
        pass
    return f"Vendedor #{seller_id}"


@st.cache_data(ttl=3600)
def obtener_nombre_categoria_meli(category_id: str) -> str:
    cid = str(category_id or "").strip().upper()
    if not cid:
        return "Sin categoría"
    try:
        r = requests.get(f"https://api.mercadolibre.com/categories/{cid}", timeout=6)
        if r.status_code == 200:
            data = r.json()
            path = data.get("path_from_root", [])
            if isinstance(path, list) and path:
                return " > ".join([p.get("name", "") for p in path if p.get("name")])
            if data.get("name"):
                return str(data["name"])
    except Exception:
        pass
    return cid


@st.cache_data(ttl=1800)
def predecir_categorias_meli(titulo: str):
    t = str(titulo or "").strip()
    if len(t) < 3:
        return []
    try:
        url = f"https://api.mercadolibre.com/sites/MLA/domain_discovery/search?q={requests.utils.quote(t)}"
        r = requests.get(url, timeout=6)
        if r.status_code == 200 and isinstance(r.json(), list):
            out = []
            for item in r.json()[:5]:
                cid = item.get("category_id")
                cname = item.get("category_name") or item.get("domain_name") or cid
                if cid:
                    out.append((cid, cname))
            return out
    except Exception:
        pass
    return []


def mapear_tipo_envio_meli(logistic_type: str, free_shipping: bool) -> str:
    lt = str(logistic_type or "").lower()
    mapping = {
        "fulfillment": "Full",
        "xd_drop_off": "Colecta / Agencia",
        "cross_docking": "Colecta",
        "drop_off": "Correo / Agencia",
        "self_service": "Flex",
        "custom": "Acordar / Propio",
        "not_specified": "Estándar",
    }
    base = mapping.get(lt, lt.replace("_", " ").title() if lt else "Estándar")
    if free_shipping:
        return f"{base} (Envío gratis)"
    return base


def calcular_pvp_en_cuotas(pvg_ganador: float, cuotas: int, ofertas: list) -> float:
    if not pvg_ganador or pvg_ganador <= 0:
        return np.nan
    for of in ofertas:
        q = int(of.get("installments_qty") or 0)
        pr = float(of.get("price") or 0.0)
        if q == cuotas and pr > 0:
            return round(pr, 2)
    mapa_clave = {
        3: "Premium 3 cuotas s/interés",
        6: "Premium 6 cuotas s/interés",
        9: "Premium 9 cuotas s/interés",
        12: "Premium 12 cuotas s/interés",
    }
    tasas = st.session_state.get("tasas_cuotas", DEFAULT_TASAS_CUOTAS)
    base_rate = tasas.get("Clásica (Sin cuotas / 1 pago)", {}).get("tasa_finan", 0.0)
    target_rate = tasas.get(mapa_clave.get(cuotas, ""), {}).get("tasa_finan", 0.0)
    factor = (1.0 + target_rate) / max(0.5, (1.0 + base_rate))
    return round(float(pvg_ganador) * factor, 2)


@st.cache_data(ttl=900)
def consultar_ofertas_ean_para_matriz(ean: str, descripcion: str, headers: dict):
    ofertas = []
    catalog_id = ""
    try:
        r_p = requests.get(
            f"https://api.mercadolibre.com/products/search?status=active&site_id=MLA&product_identifier={ean}",
            headers=headers,
            timeout=8,
        )
        if r_p.status_code == 200:
            res_p = r_p.json().get("results", [])
            if res_p:
                catalog_id = str(res_p[0].get("id") or "")
    except Exception:
        pass

    raw_items = []
    if catalog_id:
        try:
            r_pi = requests.get(f"https://api.mercadolibre.com/products/{catalog_id}/items", headers=headers, timeout=8)
            if r_pi.status_code == 200:
                raw_items = r_pi.json().get("results", [])
        except Exception:
            pass
        if not raw_items:
            try:
                r_ci = requests.get(
                    f"https://api.mercadolibre.com/sites/MLA/search?catalog_product_id={catalog_id}",
                    headers=headers,
                    timeout=8,
                )
                if r_ci.status_code == 200:
                    raw_items = r_ci.json().get("results", [])
            except Exception:
                pass

    if not raw_items:
        q_txt = descripcion.strip() if descripcion.strip() else ean
        try:
            r_q = requests.get(
                f"https://api.mercadolibre.com/sites/MLA/search?q={requests.utils.quote(q_txt)}&limit=15",
                headers=headers,
                timeout=8,
            )
            if r_q.status_code == 200:
                raw_items = r_q.json().get("results", [])
        except Exception:
            pass

    for r in raw_items:
        pr = float(r.get("price") or 0.0)
        if pr <= 0:
            continue
        ship = r.get("shipping") if isinstance(r.get("shipping"), dict) else {}
        inst = r.get("installments") if isinstance(r.get("installments"), dict) else {}
        seller = r.get("seller") if isinstance(r.get("seller"), dict) else {}
        ofertas.append({
            "item_id": str(r.get("item_id") or r.get("id") or ""),
            "catalog_id": catalog_id or str(r.get("catalog_product_id") or ""),
            "price": pr,
            "permalink": str(r.get("permalink") or ""),
            "seller_id": seller.get("id") or r.get("seller_id"),
            "logistic_type": str(ship.get("logistic_type") or ""),
            "free_shipping": bool(ship.get("free_shipping", False)),
            "installments_qty": int(inst.get("quantity") or 1),
        })

    ofertas.sort(key=lambda x: x["price"])
    return ofertas


def _normalizar_url_miniatura_meli(url_img: str) -> str:
    u = str(url_img or "").strip()
    if not u:
        return ""
    if u.startswith("//"):
        u = "https:" + u
    u = re.sub(
        r"-(?:[OIVF]|XS|S|M|L|XL|2XL|3XL)\.(webp|jpg|jpeg|png)(?:$|\?)",
        r"-O.\1",
        u,
        flags=re.IGNORECASE,
    )
    return u


def _construir_variantes_consulta(consulta: str) -> list:
    base = re.sub(r"\s+", " ", str(consulta or "").strip())
    if not base:
        return []
    variantes = [base]
    palabras = [p for p in re.findall(r"[a-zA-Z0-9áéíóúüñÁÉÍÓÚÜÑ]+", base) if len(p) > 1]
    if len(palabras) > 3:
        variantes.append(" ".join(palabras[:3]))
    if len(palabras) > 2:
        variantes.append(" ".join(palabras[:2]))
    if palabras:
        variantes.append(palabras[0])
    return list(dict.fromkeys([v.strip() for v in variantes if v.strip()]))


@st.cache_data(ttl=600)
def _buscar_en_products_search_meli(consulta: str, access_token: str = "", limit: int = 25):
    headers = get_meli_headers(access_token)
    items = []
    ultimo_status = None
    ultimo_error = ""
    endpoint_ok = ""

    for var in _construir_variantes_consulta(consulta):
        url = f"https://api.mercadolibre.com/products/search?status=active&site_id=MLA&q={requests.utils.quote(var)}&limit={limit}"
        try:
            r = requests.get(url, headers=headers, timeout=8)
            ultimo_status = r.status_code
            if r.status_code == 200:
                endpoint_ok = "/products/search"
                for prod in r.json().get("results", []):
                    pid = str(prod.get("id") or "")
                    nombre = str(prod.get("name") or var)
                    bb = prod.get("buy_box_winner") if isinstance(prod.get("buy_box_winner"), dict) else {}
                    precio = float(bb.get("price") or prod.get("price") or 0.0)
                    item_id = str(bb.get("item_id") or pid)
                    pics = prod.get("pictures") if isinstance(prod.get("pictures"), list) else []
                    thumb = ""
                    if pics and isinstance(pics[0], dict):
                        thumb = _normalizar_url_miniatura_meli(pics[0].get("secure_url") or pics[0].get("url") or "")
                    if not thumb and prod.get("thumbnail"):
                        thumb = _normalizar_url_miniatura_meli(prod.get("thumbnail"))
                    items.append({
                        "id": item_id,
                        "title": nombre,
                        "price": precio,
                        "available_quantity": int(bb.get("available_quantity") or 0),
                        "sold_quantity": int(bb.get("sold_quantity") or 0),
                        "permalink": construir_url_canonica_meli(item_id, "", pid),
                        "catalog_product_id": pid,
                        "thumbnail": thumb,
                        "seller_id": bb.get("seller_id"),
                        "seller_name": "Catálogo MeLi",
                    })
                if items:
                    break
            else:
                ultimo_error = f"HTTP {r.status_code} en /products/search"
        except Exception as e:
            ultimo_error = str(e)

    return items, {
        "endpoint_usado": endpoint_ok or "/products/search",
        "status_code": ultimo_status or 0,
        "error": "" if items else ultimo_error,
    }


@st.cache_data(ttl=600)
def _buscar_en_web_publica_meli(consulta: str, limit: int = 25):
    headers_web = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
    }
    items = []
    ultimo_status = 0
    ultimo_error = ""

    for var in _construir_variantes_consulta(consulta):
        slug = re.sub(r"[^a-z0-9]+", "-", var.lower()).strip("-")
        if not slug:
            continue
        urls_candidatas = [
            f"https://listado.mercadolibre.com.ar/{slug}",
            f"https://www.mercadolibre.com.ar/{slug}",
        ]
        for u_web in urls_candidatas:
            try:
                r = requests.get(u_web, headers=headers_web, timeout=10, allow_redirects=True)
                ultimo_status = r.status_code
                if r.status_code != 200 or len(r.text) < 2000:
                    ultimo_error = f"Web pública devolvió HTTP {r.status_code}"
                    continue

                html = r.text
                extraidos = []

                for m_pre in re.finditer(r"window\.__PRELOADED_STATE__\s*=\s*(\{.*?\});\s*</script>", html, re.DOTALL):
                    txt_json = m_pre.group(1)
                    for m_it in re.finditer(
                        r'"id"\s*:\s*"(MLA\d+)"[^}]{0,1500}?"title"\s*:\s*"([^"]{3,140})"',
                        txt_json,
                    ):
                        iid = m_it.group(1)
                        tit = unquote(m_it.group(2))
                        ventana = txt_json[max(0, m_it.start() - 200) : min(len(txt_json), m_it.end() + 1200)]
                        m_pr = re.search(r'"price"\s*:\s*(\d+(?:\.\d+)?)', ventana)
                        pr = float(m_pr.group(1)) if m_pr else 0.0
                        m_im = re.search(r'https://http2\.mlstatic\.com/D_[^"\'\\]+\.(?:jpg|webp|png)', ventana)
                        th = _normalizar_url_miniatura_meli(m_im.group(0)) if m_im else ""
                        extraidos.append({
                            "id": iid,
                            "title": tit,
                            "price": pr,
                            "available_quantity": 0,
                            "sold_quantity": 0,
                            "permalink": construir_url_canonica_meli(iid, "", ""),
                            "thumbnail": th,
                            "seller_name": "Mercado Libre Web",
                        })

                if not extraidos:
                    enlaces = re.findall(
                        r'href="(https://(?:articulo|www)\.mercadolibre\.com\.ar/(?:MLA-?\d+|p/MLA\d+)[^"]*)"',
                        html,
                        re.IGNORECASE,
                    )
                    imgs = re.findall(
                        r'(?:data-src|src)="(https://http2\.mlstatic\.com/D_NQ_NP_[^"]+\.(?:jpg|webp|png))"',
                        html,
                        re.IGNORECASE,
                    )
                    imgs_limpias = [_normalizar_url_miniatura_meli(x) for x in imgs if "MLA" in x or "D_NQ_NP_" in x]
                    vistos_href = set()
                    for idx_e, href in enumerate(enlaces):
                        href_limpio = href.split("#")[0]
                        if href_limpio in vistos_href:
                            continue
                        vistos_href.add(href_limpio)
                        m_cod = re.search(r"(MLA\d+)", href_limpio, re.IGNORECASE)
                        cod = m_cod.group(1).upper() if m_cod else f"WEB-{idx_e+1}"
                        th = imgs_limpias[idx_e] if idx_e < len(imgs_limpias) else ""
                        titulo_guess = var.title()
                        m_tit_near = re.search(
                            re.escape(href_limpio[:60]) + r'.{0,600}?aria-label="([^"]{4,120})"',
                            html,
                            re.DOTALL | re.IGNORECASE,
                        )
                        if m_tit_near:
                            titulo_guess = m_tit_near.group(1).strip()
                        extraidos.append({
                            "id": cod,
                            "title": titulo_guess,
                            "price": 0.0,
                            "available_quantity": 0,
                            "sold_quantity": 0,
                            "permalink": href_limpio,
                            "thumbnail": th,
                            "seller_name": "Mercado Libre Web",
                        })
                        if len(extraidos) >= limit:
                            break

                if extraidos:
                    items.extend(extraidos[:limit])
                    break
            except Exception as e:
                ultimo_error = str(e)
        if items:
            break

    return items, {
        "endpoint_usado": "web_publica_meli",
        "status_code": ultimo_status or 200,
        "error": "" if items else (ultimo_error or "Sin resultados en web pública"),
    }


def consultar_items_meli_con_diagnostico(consulta: str, access_token: str = "", limit: int = 50):
    headers = get_meli_headers(access_token)
    diag = {
        "endpoint_usado": "/sites/MLA/search",
        "status_code": 0,
        "error": "",
        "total_api": 0,
    }

    for var in _construir_variantes_consulta(consulta):
        url = f"https://api.mercadolibre.com/sites/MLA/search?q={requests.utils.quote(var)}&limit={limit}"
        try:
            r = requests.get(url, headers=headers, timeout=8)
            diag["status_code"] = r.status_code
            if r.status_code == 200:
                res = r.json().get("results", [])
                if res:
                    diag["total_api"] = len(res)
                    return res, diag
            else:
                err_txt = ""
                try:
                    err_txt = str(r.json().get("message") or r.json().get("error") or r.text[:120])
                except Exception:
                    err_txt = r.text[:120]
                diag["error"] = f"API devolvió HTTP {r.status_code} en /sites/MLA/search: {err_txt}"
                break
        except Exception as e:
            diag["error"] = str(e)

    prod_items, prod_diag = _buscar_en_products_search_meli(consulta, access_token=access_token, limit=limit)
    if prod_items:
        return prod_items, {
            "endpoint_usado": f"{diag['endpoint_usado']} (HTTP {diag['status_code']}) -> /products/search",
            "status_code": prod_diag["status_code"],
            "error": "",
            "total_api": len(prod_items),
        }

    web_items, web_diag = _buscar_en_web_publica_meli(consulta, limit=limit)
    if web_items:
        return web_items, {
            "endpoint_usado": f"{diag['endpoint_usado']} (HTTP {diag['status_code']}) -> respaldo web público",
            "status_code": web_diag["status_code"],
            "error": "",
            "total_api": len(web_items),
        }

    if not diag["error"]:
        diag["error"] = prod_diag.get("error") or web_diag.get("error") or "No se obtuvieron resultados"
    return [], diag


def calcular_firma_visual_robusta(img_bytes: bytes):
    if not img_bytes or not PIL_AVAILABLE:
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
def obtener_firma_miniatura_url(img_url: str):
    u = _normalizar_url_miniatura_meli(img_url)
    if not u or not PIL_AVAILABLE:
        return None
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    }
    try:
        resp = requests.get(u, headers=headers, timeout=6)
        if resp.status_code == 200 and resp.content:
            return calcular_firma_visual_robusta(resp.content)
    except Exception:
        return None
    return None


def buscar_publicaciones_similares_por_imagen(
    consulta_base: str,
    img_bytes: bytes | None,
    access_token: str = "",
    candidatos_externos: list | None = None,
):
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

    filas = []
    for item in raw_items:
        precio = limpiar_precio_moneda(item.get("price") or 0.0)
        item_id = str(item.get("id") or item.get("item_id") or "")
        titulo = str(item.get("title") or "")
        thumb = _normalizar_url_miniatura_meli(item.get("secure_thumbnail") or item.get("thumbnail") or "")
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

        filas.append({
            "Similitud Imagen (%)": sim_pct,
            "Miniatura": thumb,
            "ID": item_id,
            "Vendedor": vendedor,
            "Título": titulo,
            "Precio ($)": precio,
            "Stock Disp.": int(item.get("available_quantity") or 0),
            "Ventas Acum.": int(item.get("sold_quantity") or 0),
            "Link": permalink,
        })

    if vec_ref is not None and filas:
        filas.sort(
            key=lambda x: (
                -1.0 if pd.isna(x["Similitud Imagen (%)"]) else -x["Similitud Imagen (%)"],
                x["Precio ($)"],
            )
        )

    return filas[:30], diag


def consultar_detalle_item_individual(item_id: str, access_token: str = "") -> dict | None:
    iid = str(item_id or "").strip().upper()
    if not iid:
        return None
    try:
        r = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=get_meli_headers(access_token), timeout=8)
        if r.status_code == 200:
            data = r.json()
            ship = data.get("shipping") if isinstance(data.get("shipping"), dict) else {}
            pics = data.get("pictures") if isinstance(data.get("pictures"), list) else []
            pic_urls = [p.get("secure_url") or p.get("url") for p in pics if isinstance(p, dict) and (p.get("secure_url") or p.get("url"))]
            if not pic_urls and data.get("thumbnail"):
                pic_urls = [_normalizar_url_miniatura_meli(data.get("thumbnail"))]

            desc_txt = ""
            try:
                rd = requests.get(f"https://api.mercadolibre.com/items/{iid}/description", headers=get_meli_headers(access_token), timeout=5)
                if rd.status_code == 200:
                    desc_txt = str(rd.json().get("plain_text") or "")
            except Exception:
                pass

            return {
                "item_id": data.get("id") or iid,
                "title": data.get("title") or "",
                "price": float(data.get("price") or 0.0),
                "available_quantity": int(data.get("available_quantity") or 0),
                "sold_quantity": int(data.get("sold_quantity") or 0),
                "category_id": data.get("category_id") or "",
                "catalog_product_id": data.get("catalog_product_id") or "",
                "listing_type_id": data.get("listing_type_id") or "gold_special",
                "logistic_type": ship.get("logistic_type") or "",
                "free_shipping": bool(ship.get("free_shipping", False)),
                "seller_id": data.get("seller_id"),
                "permalink": construir_url_canonica_meli(iid, data.get("permalink") or "", data.get("catalog_product_id") or ""),
                "pictures": pic_urls,
                "attributes": data.get("attributes") or [],
                "description": desc_txt,
            }
    except Exception:
        pass
    return None


@st.cache_data(ttl=600)
def obtener_inteligencia_competitiva_completa(query_key: str, access_token: str = ""):
    info_id = extraer_ids_meli_avanzado(query_key)
    headers = get_meli_headers(access_token)
    ofertas = []
    titulo_prod = ""
    catalog_id = info_id.get("catalog_id") or ""
    category_id = ""
    imagenes = []
    atributos = []
    descripcion = ""
    foco_directo = None

    if info_id.get("item_id"):
        det = consultar_detalle_item_individual(info_id["item_id"], access_token)
        if det:
            foco_directo = det
            titulo_prod = det["title"]
            category_id = det["category_id"]
            catalog_id = catalog_id or det["catalog_product_id"]
            imagenes = det["pictures"]
            atributos = det["attributes"]
            descripcion = det["description"]
            ofertas.append({
                "Item ID": det["item_id"],
                "Vendedor": resolver_vendedor_nickname_oficial(det["seller_id"], access_token),
                "Precio ($)": det["price"],
                "Stock": det["available_quantity"],
                "Ventas": det["sold_quantity"],
                "Logística": mapear_tipo_envio_meli(det["logistic_type"], det["free_shipping"]),
                "Link": det["permalink"],
            })

    if info_id.get("ean") and not catalog_id:
        try:
            rp = requests.get(
                f"https://api.mercadolibre.com/products/search?status=active&site_id=MLA&product_identifier={info_id['ean']}",
                headers=headers,
                timeout=8,
            )
            if rp.status_code == 200:
                res_p = rp.json().get("results", [])
                if res_p:
                    catalog_id = str(res_p[0].get("id") or "")
                    titulo_prod = titulo_prod or str(res_p[0].get("name") or "")
        except Exception:
            pass

    if catalog_id:
        try:
            rc = requests.get(f"https://api.mercadolibre.com/products/{catalog_id}", headers=headers, timeout=8)
            if rc.status_code == 200:
                cdata = rc.json()
                titulo_prod = titulo_prod or str(cdata.get("name") or "")
                category_id = category_id or str(cdata.get("domain_id") or "")
                if not imagenes:
                    imagenes = [p.get("url") for p in cdata.get("pictures", []) if isinstance(p, dict) and p.get("url")]
                if not atributos:
                    atributos = cdata.get("attributes") or []
                short_desc = cdata.get("short_description")
                if isinstance(short_desc, dict) and not descripcion:
                    descripcion = str(short_desc.get("content") or "")
        except Exception:
            pass

        try:
            ri = requests.get(f"https://api.mercadolibre.com/products/{catalog_id}/items", headers=headers, timeout=8)
            if ri.status_code == 200:
                for it in ri.json().get("results", []):
                    iid = str(it.get("item_id") or it.get("id") or "")
                    if any(o["Item ID"] == iid for o in ofertas):
                        continue
                    ship = it.get("shipping") if isinstance(it.get("shipping"), dict) else {}
                    ofertas.append({
                        "Item ID": iid,
                        "Vendedor": resolver_vendedor_nickname_oficial(it.get("seller_id"), access_token),
                        "Precio ($)": float(it.get("price") or 0.0),
                        "Stock": int(it.get("available_quantity") or 0),
                        "Ventas": int(it.get("sold_quantity") or 0),
                        "Logística": mapear_tipo_envio_meli(ship.get("logistic_type"), bool(ship.get("free_shipping"))),
                        "Link": construir_url_canonica_meli(iid, it.get("permalink") or "", catalog_id),
                    })
        except Exception:
            pass

    if not ofertas:
        q_busq = info_id.get("ean") or info_id.get("raw") or query_key
        raw_items, _ = consultar_items_meli_con_diagnostico(q_busq, access_token=access_token, limit=20)
        for it in raw_items:
            iid = str(it.get("id") or "")
            if not titulo_prod:
                titulo_prod = str(it.get("title") or "")
            if not category_id:
                category_id = str(it.get("category_id") or "")
            if not imagenes and it.get("thumbnail"):
                imagenes = [_normalizar_url_miniatura_meli(it.get("thumbnail"))]
            ship = it.get("shipping") if isinstance(it.get("shipping"), dict) else {}
            seller = it.get("seller") if isinstance(it.get("seller"), dict) else {}
            ofertas.append({
                "Item ID": iid,
                "Vendedor": it.get("seller_name") or resolver_vendedor_nickname_oficial(seller.get("id"), access_token),
                "Precio ($)": float(it.get("price") or 0.0),
                "Stock": int(it.get("available_quantity") or 0),
                "Ventas": int(it.get("sold_quantity") or 0),
                "Logística": mapear_tipo_envio_meli(ship.get("logistic_type"), bool(ship.get("free_shipping"))),
                "Link": construir_url_canonica_meli(iid, it.get("permalink") or "", catalog_id),
            })

    ofertas = [o for o in ofertas if o["Precio ($)"] > 0]
    ofertas.sort(key=lambda x: x["Precio ($)"])

    return {
        "query": query_key,
        "titulo": titulo_prod or query_key,
        "catalog_id": catalog_id,
        "category_id": category_id,
        "category_name": obtener_nombre_categoria_meli(category_id) if category_id.startswith("MLA") and category_id[3:].isdigit() else category_id,
        "imagenes": imagenes,
        "atributos": atributos,
        "descripcion": descripcion,
        "foco_directo": foco_directo,
        "ofertas": ofertas,
    }


def consultar_catalogo_oficial_meli(tipo_id: str, valor_id: str, headers: dict):
    cat_id = ""
    if tipo_id == "CATALOG_ID":
        cat_id = valor_id
    elif tipo_id == "EAN":
        try:
            r = requests.get(
                f"https://api.mercadolibre.com/products/search?status=active&site_id=MLA&product_identifier={valor_id}",
                headers=headers,
                timeout=8,
            )
            if r.status_code == 200 and r.json().get("results"):
                cat_id = str(r.json()["results"][0].get("id") or "")
        except Exception:
            pass

    if not cat_id:
        return None

    try:
        rc = requests.get(f"https://api.mercadolibre.com/products/{cat_id}", headers=headers, timeout=8)
        if rc.status_code == 200:
            data = rc.json()
            pics = [p.get("url") for p in data.get("pictures", []) if isinstance(p, dict) and p.get("url")]
            attrs = {}
            for a in data.get("attributes", []):
                if isinstance(a, dict) and a.get("id"):
                    attrs[a["id"]] = a.get("value_name") or ""
            return {
                "catalog_id": cat_id,
                "name": data.get("name") or "",
                "domain_id": data.get("domain_id") or "",
                "pictures": pics,
                "attributes": attrs,
                "short_description": (data.get("short_description") or {}).get("content", "") if isinstance(data.get("short_description"), dict) else "",
            }
    except Exception:
        pass
    return None


def extraer_datos_publicacion_mla_externa(codigo_o_url: str, headers: dict):
    info = extraer_ids_meli_avanzado(codigo_o_url)
    if info.get("item_id"):
        det = consultar_detalle_item_individual(info["item_id"], st.session_state.get("access_token", ""))
        if det:
            attrs = {}
            for a in det.get("attributes", []):
                if isinstance(a, dict) and a.get("id"):
                    attrs[a["id"]] = a.get("value_name") or ""
            return {
                "item_id": det["item_id"],
                "title": det["title"],
                "price": det["price"],
                "category_id": det["category_id"],
                "catalog_id": det["catalog_product_id"],
                "pictures": det["pictures"],
                "attributes": attrs,
                "description": det["description"],
            }
    if info.get("catalog_id"):
        cat = consultar_catalogo_oficial_meli("CATALOG_ID", info["catalog_id"], headers)
        if cat:
            preds = predecir_categorias_meli(cat["name"])
            cat_num = preds[0][0] if preds else "MLA4765"
            return {
                "item_id": "",
                "title": cat["name"],
                "price": 0.0,
                "category_id": cat_num,
                "catalog_id": cat["catalog_id"],
                "pictures": cat["pictures"],
                "attributes": cat["attributes"],
                "description": cat["short_description"],
            }
    return None


def crear_publicacion_catalogo_meli(payload: dict, access_token: str):
    if not access_token or not access_token.strip():
        return False, {"error": "No hay Access Token configurado en el panel lateral."}
    try:
        r = requests.post(
            "https://api.mercadolibre.com/items",
            headers={**get_meli_headers(access_token), "Content-Type": "application/json"},
            json=payload,
            timeout=12,
        )
        try:
            body = r.json()
        except Exception:
            body = {"raw": r.text}
        return (r.status_code in (200, 201)), body
    except Exception as e:
        return False, {"error": str(e)}


with st.sidebar:
    st.markdown(f"### ⚙️ Control Panel · `{APP_VERSION}`")
    st.caption(f"Versión activa en ejecución: **{APP_VERSION}**")

    with st.expander("🔑 Conexión API Mercado Libre", expanded=False):
        url_oauth = obtener_url_login_meli()
        st.link_button("🔗 Iniciar Sesión OAuth MeLi", url_oauth, use_container_width=True)
        token_in = st.text_input(
            "Access Token (APP_USR-...)",
            value=st.session_state["access_token"],
            type="password",
        )
        if st.button("✅ Validar y Conectar Token", use_container_width=True):
            st.session_state["access_token"] = token_in.strip()
            perfil = obtener_perfil_meli(st.session_state["access_token"])
            st.session_state["user_info"] = perfil
            sincronizar_tarifas_financiacion_meli(st.session_state["access_token"])
            st.success(f"Conectado: {perfil.get('nickname', 'OK')}")

    with st.expander("📂 Cargar Lista Gold (Costos)", expanded=True):
        up_gold = st.file_uploader("Subir Lista Gold (.xlsx / .csv)", type=["xlsx", "xls", "csv"], key="up_gold_sb")
        if up_gold is not None:
            df_gold_parsed = procesar_archivo_lista_gold(up_gold)
            if df_gold_parsed is not None:
                st.session_state["lista_gold_df"] = df_gold_parsed
                st.success(f"Lista Gold cargada ({len(df_gold_parsed)} filas)")
        elif st.session_state["lista_gold_df"] is not None:
            st.info(f"Activa: {len(st.session_state['lista_gold_df'])} artículos")

    with st.expander("📐 Matriz Logística Propia (Opcional)", expanded=False):
        up_mat = st.file_uploader("Subir Matriz Artículos (.xlsx)", type=["xlsx", "xls"], key="up_mat_sb")
        if up_mat is not None:
            try:
                df_m_custom = pd.read_excel(up_mat)
                df_m_custom.columns = [str(c).strip() for c in df_m_custom.columns]
                st.session_state["matriz_custom_df"] = df_m_custom
                st.success(f"Matriz cargada ({len(df_m_custom)} filas)")
            except Exception as e:
                st.error(f"Error matriz: {e}")

    with st.expander("💳 Tasas & Financiación MeLi", expanded=False):
        for plan_k, vals in st.session_state["tasas_cuotas"].items():
            c_b = st.number_input(
                f"Comisión {plan_k[:18]} (%)",
                min_value=0.0,
                max_value=40.0,
                value=float(vals["comision_base"] * 100.0),
                step=0.5,
                key=f"cb_{plan_k}",
            )
            t_f = st.number_input(
                f"Financ. {plan_k[:18]} (%)",
                min_value=0.0,
                max_value=40.0,
                value=float(vals["tasa_finan"] * 100.0),
                step=0.5,
                key=f"tf_{plan_k}",
            )
            st.session_state["tasas_cuotas"][plan_k]["comision_base"] = c_b / 100.0
            st.session_state["tasas_cuotas"][plan_k]["tasa_finan"] = t_f / 100.0

    st.markdown("---")
    st.caption(f"NQ Argentina · Core `{APP_VERSION}`")


nick_actual = st.session_state.get("user_info", {}).get("nickname", "Modo Público")
gold_count = len(st.session_state["lista_gold_df"]) if st.session_state["lista_gold_df"] is not None else 0

st.markdown(
    f"""
    <div class="exec-hero-banner">
        <div class="exec-hero-left">
            <div class="exec-logo-badge">NQ</div>
            <div>
                <div class="exec-hero-title">
                    NQ Argentina <span>| MeLi Pricing & Catalog Intelligence</span>
                    <span class="exec-version-tag">{APP_VERSION}</span>
                </div>
                <div class="exec-hero-subtitle">
                    Centro de Comando Comercial · Rentabilidad Neta, Logística ME2, Búsqueda Visual & Publicación API
                </div>
            </div>
        </div>
        <div class="exec-status-group">
            <div class="exec-status-pill">
                <div class="exec-pill-lbl">Versión App</div>
                <div class="exec-pill-val" style="color:#34d399;">{APP_VERSION}</div>
            </div>
            <div class="exec-status-pill">
                <div class="exec-pill-lbl">Cuenta MeLi</div>
                <div class="exec-pill-val">{nick_actual}</div>
            </div>
            <div class="exec-status-pill">
                <div class="exec-pill-lbl">Lista Gold</div>
                <div class="exec-pill-val">{gold_count} ítems</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

TABS_CONFIG = [
    ("💰", "Costos & Margen"),
    ("📡", "Control Precios"),
    ("🔬", "Radiografía MLA"),
    ("📦", "Matriz Logística"),
    ("🤖", "Asistente IA"),
    ("🚀", "Publicador API"),
    ("🛡️", "Modo Defensivo"),
    ("📥", "Cotizador Matriz"),
    ("🖼️", "Comparador Imagen"),
]

nav_cols = st.columns(len(TABS_CONFIG))
for idx_t, (ico_t, lbl_t) in enumerate(TABS_CONFIG):
    with nav_cols[idx_t]:
        is_sel = st.session_state["active_tab"] == idx_t
        btn_type = "primary" if is_sel else "secondary"
        if st.button(f"{ico_t} {lbl_t}", key=f"nav_tab_{idx_t}", use_container_width=True, type=btn_type):
            st.session_state["active_tab"] = idx_t
            st.rerun()

st.markdown("---")
tab_activa = st.session_state["active_tab"]


if tab_activa == 0:
    st.subheader("💰 Simulador de Rentabilidad Neta & Punto de Equilibrio")
    opciones_gold = extraer_opciones_ean_lista_gold()
    col_s1, col_s2 = st.columns([2, 1])
    with col_s1:
        q_in_0 = st.text_input(
            "Buscar por EAN, Código Artículo o Descripción:",
            value=st.session_state["q_costos"],
            key="input_q_costos_tab0",
        )
        st.session_state["q_costos"] = q_in_0
    with col_s2:
        if opciones_gold:
            sel_g = st.selectbox(
                "O elegir desde Lista Gold:",
                options=["-- Seleccionar artículo --"] + [o[0] for o in opciones_gold],
                key="sel_gold_tab0",
            )
            if sel_g != "-- Seleccionar artículo --":
                ean_pick = next((o[1] for o in opciones_gold if o[0] == sel_g), "")
                if ean_pick and ean_pick != st.session_state["q_costos"]:
                    st.session_state["q_costos"] = ean_pick
                    st.rerun()

    encontrado_g, costo_g, desc_g, art_g = buscar_costo_y_titulo_en_lista_gold(st.session_state["q_costos"])
    encontrado_m, flete_m, p_unit_m, p_tot_m, _, cajas_m, desc_m = buscar_datos_en_matriz(st.session_state["q_costos"])

    titulo_mostrar = desc_g or desc_m or "Producto sin descripción en base local"
    if encontrado_g or encontrado_m:
        st.success(f"📦 **{titulo_mostrar}** | Artículo: `{art_g or 'N/A'}` | Bultos: `{cajas_m}` | Peso Facturable: `{p_tot_m:.2f} kg`")
    else:
        st.markdown(
            '<div class="badge-missing">ℹ️ Código no hallado en Lista Gold / Matriz local. Podés ingresar costo y flete manualmente abajo.</div>',
            unsafe_allow_html=True,
        )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        pvp_sim = st.number_input("PVP Venta Mercado Libre ($)", min_value=100.0, value=208000.0, step=1000.0)
    with c2:
        costo_sim = st.number_input(
            "Costo Neto Producto ($)",
            min_value=0.0,
            value=float(costo_g) if costo_g > 0 else 95000.0,
            step=500.0,
        )
    with c3:
        flete_sim = st.number_input(
            "Costo Envío ME2 ($)",
            min_value=0.0,
            value=float(flete_m) if flete_m > 0 else 14900.0,
            step=200.0,
        )
    with c4:
        plan_sel = st.selectbox("Tipo de Publicación / Cuotas", list(st.session_state["tasas_cuotas"].keys()))

    datos_plan = st.session_state["tasas_cuotas"][plan_sel]
    comision_pct = datos_plan["comision_base"] + datos_plan["tasa_finan"]
    monto_comision = pvp_sim * comision_pct
    monto_iibb = pvp_sim * ALICUOTA_IIBB
    iva_debito = pvp_sim - (pvp_sim / (1.0 + ALICUOTA_IVA))
    iva_credito = (costo_sim + monto_comision + flete_sim) * (ALICUOTA_IVA / (1.0 + ALICUOTA_IVA))
    iva_neto = max(0.0, iva_debito - iva_credito)

    utilidad_neta = pvp_sim - costo_sim - monto_comision - flete_sim - monto_iibb - iva_neto
    margen_neto_pct = (utilidad_neta / pvp_sim * 100.0) if pvp_sim > 0 else 0.0

    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(f'<div class="kpi-card"><div class="kpi-label">Comisión + Cuotas</div><div class="kpi-value">${monto_comision:,.0f}</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="kpi-card"><div class="kpi-label">Impuestos (IIBB + IVA)</div><div class="kpi-value">${(monto_iibb + iva_neto):,.0f}</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="kpi-card"><div class="kpi-label">Utilidad Neta ($)</div><div class="kpi-value" style="color:{"#059669" if utilidad_neta >= 0 else "#dc2626"};">${utilidad_neta:,.0f}</div></div>', unsafe_allow_html=True)
    k4.markdown(f'<div class="kpi-card"><div class="kpi-label">Margen Neto (%)</div><div class="kpi-value" style="color:{"#059669" if margen_neto_pct >= 10 else "#d97706"};">{margen_neto_pct:.1f}%</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if margen_neto_pct >= 12.0:
        st.markdown(f'<div class="card-viable">✅ <b>OPERACIÓN VIABLE:</b> Deja <b>${utilidad_neta:,.0f}</b> limpios por unidad ({margen_neto_pct:.1f}% sobre PVP).</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="card-noviable">⚠️ <b>MARGEN AJUSTADO / RIESGO:</b> Margen neto de <b>{margen_neto_pct:.1f}%</b>. Evaluar ajuste de PVP o publicación Clásica.</div>', unsafe_allow_html=True)


elif tab_activa == 1:
    st.subheader("📡 Control de Precios & BuyBox en Tiempo Real")
    col_m1, col_m2 = st.columns([3, 1])
    with col_m1:
        q_mon = st.text_input("Ingresá EAN, ID de Catálogo (MLA...) o palabra clave:", value=st.session_state["search_query_mon"])
        st.session_state["search_query_mon"] = q_mon
    with col_m2:
        st.markdown("<br>", unsafe_allow_html=True)
        btn_mon = st.button("🔍 Analizar Competencia", type="primary", use_container_width=True)

    if btn_mon or q_mon:
        intel = obtener_inteligencia_competitiva_completa(q_mon, st.session_state["access_token"])
        ofertas = intel.get("ofertas", [])
        st.markdown(
            f"""
            <div class="mla-focus-box">
                <b>Producto Detectado:</b> {intel.get('titulo')}<br>
                <small>Catálogo: <code>{intel.get('catalog_id') or 'N/A'}</code> · Categoría: <code>{intel.get('category_name') or 'N/A'}</code></small>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if ofertas:
            df_of = pd.DataFrame(ofertas)
            pvg = df_of["Precio ($)"].min()
            p_med = df_of["Precio ($)"].median()
            p_max = df_of["Precio ($)"].max()
            c_a, c_b, c_c = st.columns(3)
            c_a.metric("🏆 Precio Ganador (PVG)", f"${pvg:,.0f}")
            c_b.metric("📊 Mediana Mercado", f"${p_med:,.0f}")
            c_c.metric("🔝 Techo Mercado", f"${p_max:,.0f}")

            st.dataframe(
                df_of,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Precio ($)": st.column_config.NumberColumn(format="$ %.2f"),
                    "Link": st.column_config.LinkColumn("Publicación", display_text="Abrir MeLi"),
                },
            )
        else:
            st.warning("No se encontraron ofertas activas para esta consulta.")


elif tab_activa == 2:
    st.subheader("🔬 Radiografía Técnica de Publicación (MLA / URL)")
    q_rad = st.text_input("Pegá Link de Mercado Libre o ID (ej: MLA1456789012):", value=st.session_state["q_mercado_mla"])
    st.session_state["q_mercado_mla"] = q_rad
    if st.button("🧪 Inspeccionar Publicación", type="primary"):
        intel_r = obtener_inteligencia_competitiva_completa(q_rad, st.session_state["access_token"])
        c_img, c_det = st.columns([1, 2])
        with c_img:
            imgs_r = intel_r.get("imagenes", [])
            if imgs_r:
                st.image(imgs_r[0], use_container_width=True)
            else:
                st.info("Sin imagen disponible")
        with c_det:
            st.markdown(f"#### {intel_r.get('titulo')}")
            st.write(f"**Catálogo:** `{intel_r.get('catalog_id') or 'No catalogado'}`")
            st.write(f"**Categoría:** `{intel_r.get('category_name')}`")
            if intel_r.get("descripcion"):
                with st.expander("📄 Ver Descripción Extraída"):
                    st.text(intel_r["descripcion"][:2000])
            attrs_r = intel_r.get("atributos", [])
            if attrs_r:
                rows_attr = [
                    {"ID": a.get("id"), "Atributo": a.get("name"), "Valor": a.get("value_name")}
                    for a in attrs_r if isinstance(a, dict)
                ]
                st.dataframe(pd.DataFrame(rows_attr), use_container_width=True, hide_index=True)


elif tab_activa == 3:
    st.subheader("📦 Matriz Logística & Calculadora Volumétrica ME2")
    c_l1, c_l2, c_l3, c_l4 = st.columns(4)
    with c_l1:
        alto_cm = st.number_input("Alto Caja (cm)", min_value=1.0, value=80.0, step=1.0)
    with c_l2:
        ancho_cm = st.number_input("Ancho Caja (cm)", min_value=1.0, value=60.0, step=1.0)
    with c_l3:
        prof_cm = st.number_input("Profundidad Caja (cm)", min_value=1.0, value=15.0, step=1.0)
    with c_l4:
        peso_kg = st.number_input("Peso Real (kg)", min_value=0.1, value=18.0, step=0.5)

    costo_f, p_fact, p_vol, _ = calcular_flete_desde_embalaje(alto_cm, ancho_cm, prof_cm, peso_kg)
    m1, m2, m3 = st.columns(3)
    m1.metric("Peso Volumétrico (÷4500)", f"{p_vol:.2f} kg")
    m2.metric("Peso Facturable Aplicado", f"{p_fact:.2f} kg")
    m3.metric("Tarifa Estimada ME2", f"${costo_f:,.0f}")

    df_mat_view = cargar_matriz_articulos_oficial()
    if df_mat_view is not None and not df_mat_view.empty:
        st.markdown("#### 📋 Matriz Logística Activa")
        st.dataframe(df_mat_view, use_container_width=True, hide_index=True)


elif tab_activa == 4:
    st.subheader("🤖 Asistente Comercial IA — Estrategia & Diagnóstico")
    prompt_ia = st.text_area(
        "Consultá sobre pricing, posicionamiento frente a competencia o defensa de margen:",
        value="Tengo un producto con costo $95.000, envío $14.900 y el ganador de BuyBox está en $199.900. ¿Cómo conviene competir?",
    )
    if st.button("✨ Generar Recomendación Estratégica", type="primary"):
        st.markdown(
            f"""
            <div class="ai-bubble">
                <b>Diagnóstico Ejecutivo ({APP_VERSION}):</b><br><br>
                1. <b>Estructura de Costos:</b> Con costo $95.000 + flete $14.900 ($109.900 directos), a un PVP de $199.900 en publicación Clásica (~14.5% + impuestos) retenés aproximadamente un 16%–18% de margen neto.<br>
                2. <b>Táctica BuyBox:</b> Si igualás o bajás $100 respecto al ganador en 1 pago, capturás la caja de compra sin destruir margen. Evitá ofrecer 6 o 12 cuotas sin interés al mismo PVP porque la tasa financiera absorbería tu utilidad.<br>
                3. <b>Palanca Logística:</b> Verificá que las medidas de caja cargadas en MeLi no excedan el tramo real de peso volumétrico.
            </div>
            """,
            unsafe_allow_html=True,
        )


elif tab_activa == 5:
    st.subheader("🚀 Publicador Directo a Catálogo / API Mercado Libre")
    col_p1, col_p2 = st.columns([2, 1])
    with col_p1:
        q_pub = st.text_input("Código EAN, ID Catálogo (MLA...) o URL MLA externa a clonar:", value=st.session_state["q_builder"])
        st.session_state["q_builder"] = q_pub
    with col_p2:
        st.markdown("<br>", unsafe_allow_html=True)
        btn_cargar_pub = st.button("📥 Autocompletar Ficha desde MeLi / Lista", use_container_width=True)

    ext_data = None
    if btn_cargar_pub and q_pub:
        ext_data = extraer_datos_publicacion_mla_externa(q_pub, get_meli_headers())

    _, costo_loc, desc_loc, art_loc = buscar_costo_y_titulo_en_lista_gold(q_pub)
    ancho_m, alto_m, prof_m, peso_m = buscar_datos_en_matriz_completa(q_pub)

    fam_default = (ext_data.get("title") if ext_data else "") or desc_loc or "Mueble de Cocina Melamina"
    cat_default = (ext_data.get("category_id") if ext_data else "") or "MLA4765"
    pvp_default = float(ext_data.get("price") or 0.0) if (ext_data and ext_data.get("price", 0) > 0) else (round(costo_loc * 1.95, 0) if costo_loc > 0 else 185000.0)

    c_f1, c_f2 = st.columns(2)
    with c_f1:
        family_name = st.text_input("Título / Family Name (Raíz API)", value=fam_default)
        category_id = st.text_input("Category ID Numérico (ej: MLA4765)", value=cat_default)
        st.caption(f"Categoría resuelta: **{obtener_nombre_categoria_meli(category_id)}**")
        price_pub = st.number_input("Precio Venta ARS ($)", min_value=100.0, value=float(pvp_default), step=500.0)
    with c_f2:
        qty_pub = st.number_input("Stock Disponible", min_value=1, value=5, step=1)
        listing_pub = st.selectbox("Tipo Publicación", ["gold_special", "gold_pro"])
        img_url_pub = st.text_input(
            "URL Imagen Principal",
            value=(ext_data["pictures"][0] if (ext_data and ext_data.get("pictures")) else ""),
        )

    if any([ancho_m, alto_m, prof_m, peso_m]):
        st.info(f"📐 Medidas desde Matriz Logística: Ancho `{ancho_m}` x Alto `{alto_m}` x Prof `{prof_m}` | Peso `{peso_m} kg`")

    payload_preview = {
        "family_name": family_name.strip(),
        "category_id": category_id.strip().upper(),
        "price": float(price_pub),
        "currency_id": "ARS",
        "available_quantity": int(qty_pub),
        "buying_mode": "buy_it_now",
        "listing_type_id": listing_pub,
        "condition": "new",
        "pictures": [{"source": img_url_pub.strip()}] if img_url_pub.strip() else [],
        "attributes": [
            {"id": "MODEL", "value_name": art_loc or "Estándar"},
        ],
    }

    with st.expander("🔍 Ver Payload JSON Exacto a Enviar"):
        st.json(payload_preview)

    if st.button("🚀 Publicar Ahora en Mercado Libre", type="primary"):
        ok_pub, resp_pub = crear_publicacion_catalogo_meli(payload_preview, st.session_state["access_token"])
        if ok_pub:
            st.success(f"✅ Publicación creada con éxito: `{resp_pub.get('id')}`")
            st.json(resp_pub)
        else:
            st.error("❌ Error al publicar en API Mercado Libre")
            st.json(resp_pub)


elif tab_activa == 6:
    st.subheader("🛡️ Modo Defensivo — Piso Mínimo Anti-Pérdida")
    c_d1, c_d2, c_d3 = st.columns(3)
    with c_d1:
        costo_def = st.number_input("Costo Reposición ($)", min_value=100.0, value=95000.0, step=500.0)
    with c_d2:
        flete_def = st.number_input("Flete ME2 ($)", min_value=0.0, value=14900.0, step=200.0)
    with c_d3:
        margen_min_obj = st.number_input("Margen Mínimo Protegido (%)", min_value=0.0, max_value=50.0, value=10.0, step=0.5)

    tasa_tot_def = 0.145 + ALICUOTA_IIBB + (margen_min_obj / 100.0)
    divisor_def = max(0.25, 1.0 - tasa_tot_def)
    pvp_piso = (costo_def + flete_def) / divisor_def

    st.markdown(
        f'<div class="warning-stock">🛡️ <b>PVP PISO DEFENSIVO RECOMENDADO: ${pvp_piso:,.2f}</b> — Por debajo de este valor se perfora tu margen mínimo protegido del {margen_min_obj:.1f}%.</div>',
        unsafe_allow_html=True,
    )


elif tab_activa == 7:
    st.subheader("📥 Cotizador Masivo de Matriz (.xlsx)")
    st.caption("Subí tu matriz de artículos con columnas `ean`, `Descripcion`, `Peso`, `Cajas` y completá precios ganadores de MeLi automáticamente.")

    up_cot = st.file_uploader("Cargar Excel Matriz de Artículos (.xlsx)", type=["xlsx", "xls"], key="up_cotizador_tab7")
    max_filas_cot = st.slider("Cantidad máxima de filas a consultar en este lote", min_value=5, max_value=300, value=30, step=5)

    if up_cot is not None:
        df_cot = pd.read_excel(up_cot)
        df_cot.columns = [str(c).strip() for c in df_cot.columns]
        st.write(f"Archivo cargado: **{len(df_cot)} filas** x **{len(df_cot.columns)} columnas**")

        if st.button("⚡ Ejecutar Cotización Masiva API MeLi", type="primary"):
            headers_cot = get_meli_headers()
            prog = st.progress(0)
            limite = min(len(df_cot), max_filas_cot)

            for col_req in ["PVG GANADOR", "PVP 2", "LINK", "VENDEDOR GANADOR", "TIPO ENVIO", "COSTO ENVIO"]:
                if col_req not in df_cot.columns:
                    df_cot[col_req] = np.nan

            for idx_r in range(limite):
                row_c = df_cot.iloc[idx_r]
                ean_c = normalizar_ean_matriz(row_c.get("ean", ""))
                desc_c = str(row_c.get("Descripcion", "") or "")
                peso_fact_c = calcular_peso_facturable_fila_matriz(row_c)
                costo_env_c = calcular_costo_envio_por_peso_facturable(peso_fact_c)
                df_cot.at[idx_r, "COSTO ENVIO"] = costo_env_c

                if ean_c or desc_c:
                    ofs = consultar_ofertas_ean_para_matriz(ean_c, desc_c, headers_cot)
                    if ofs:
                        g0 = ofs[0]
                        df_cot.at[idx_r, "PVG GANADOR"] = g0["price"]
                        df_cot.at[idx_r, "LINK"] = construir_url_canonica_meli(g0["item_id"], g0["permalink"], g0["catalog_id"])
                        df_cot.at[idx_r, "VENDEDOR GANADOR"] = resolver_vendedor_nickname_oficial(g0["seller_id"], st.session_state["access_token"])
                        df_cot.at[idx_r, "TIPO ENVIO"] = mapear_tipo_envio_meli(g0["logistic_type"], g0["free_shipping"])
                        if len(ofs) > 1:
                            df_cot.at[idx_r, "PVP 2"] = ofs[1]["price"]

                prog.progress((idx_r + 1) / limite)
                time.sleep(0.08)

            st.success("✅ Cotización masiva finalizada.")
            st.dataframe(df_cot.head(limite), use_container_width=True, hide_index=True)
            excel_out = dataframe_a_excel_bytes(df_cot, "Cotizacion_MeLi")
            st.download_button(
                "⬇️ Descargar Matriz Completada (.xlsx)",
                data=excel_out,
                file_name=f"Matriz_Cotizada_MeLi_{APP_VERSION}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )


elif tab_activa == 8:
    st.subheader("🖼️ Comparador por Imagen Similar (Búsqueda Visual Resiliente)")
    st.caption("Compará productos visualmente mediante firma de imagen y buscá precios en Mercado Libre con respaldo automático ante bloqueos de API.")

    c_v1, c_v2 = st.columns([1, 2])
    with c_v1:
        img_up = st.file_uploader("Subí foto de referencia (JPG / PNG / WEBP)", type=["jpg", "jpeg", "png", "webp"], key="img_ref_tab8")
        img_bytes_ref = img_up.getvalue() if img_up is not None else None
        if img_bytes_ref:
            st.image(img_bytes_ref, caption="Imagen de referencia cargada", use_container_width=True)
    with c_v2:
        q_vis = st.text_input("Término de búsqueda base en Mercado Libre:", value="alacena cocina melamina 120")
        btn_vis = st.button("🔎 Buscar y Ordenar por Similitud Visual", type="primary")

    if btn_vis and q_vis.strip():
        resultados_vis, diag_vis = buscar_publicaciones_similares_por_imagen(
            consulta_base=q_vis.strip(),
            img_bytes=img_bytes_ref,
            access_token=st.session_state["access_token"],
        )
        st.caption(f"Ruta utilizada: `{diag_vis.get('endpoint_usado')}` · Resultados: `{len(resultados_vis)}`")
        if diag_vis.get("error") and not resultados_vis:
            st.warning(f"Diagnóstico: {diag_vis['error']}")

        if resultados_vis:
            df_vis = pd.DataFrame(resultados_vis)
            st.dataframe(
                df_vis,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Similitud Imagen (%)": st.column_config.NumberColumn(format="%.1f %%"),
                    "Miniatura": st.column_config.ImageColumn("Foto"),
                    "Precio ($)": st.column_config.NumberColumn(format="$ %.2f"),
                    "Link": st.column_config.LinkColumn("Publicación", display_text="Ver en MeLi"),
                },
            )
