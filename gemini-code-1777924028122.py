import io
import math
import os
import re
import time
import urllib.parse
import numpy as np
import pandas as pd
import requests
import streamlit as st
from PIL import Image

APP_VERSION = "v191.0"

st.set_page_config(
    page_title=f"NQ Argentina | MeLi Intelligence {APP_VERSION}",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

ALICUOTA_IIBB = 0.035
ALICUOTA_IVA = 0.21

TASAS_CUOTAS_DEFAULT = {
    "Clásica (0 cuotas sin interés)": {"comision_base": 0.145, "tasa_finan": 0.0},
    "Premium 3 cuotas sin interés": {"comision_base": 0.145, "tasa_finan": 0.065},
    "Premium 6 cuotas sin interés": {"comision_base": 0.145, "tasa_finan": 0.115},
    "Premium 9 cuotas sin interés": {"comision_base": 0.145, "tasa_finan": 0.155},
    "Premium 12 cuotas sin interés": {"comision_base": 0.145, "tasa_finan": 0.195},
}

st.markdown(
    """
    <style>
        .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
        .exec-hero-banner {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 65%, #064e3b 100%);
            color: #f8fafc;
            padding: 16px 20px;
            border-radius: 12px;
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            gap: 14px;
            margin-bottom: 12px;
            border: 1px solid #334155;
        }
        .exec-hero-left { display: flex; align-items: center; gap: 14px; }
        .exec-logo-badge {
            background: #10b981;
            color: #06281e;
            font-weight: 900;
            font-size: 18px;
            width: 44px;
            height: 44px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .exec-hero-title { font-size: 19px; font-weight: 800; letter-spacing: -0.01em; }
        .exec-hero-title span { color: #34d399; }
        .exec-version-tag {
            background: rgba(16, 185, 129, 0.2);
            color: #6ee7b7;
            font-size: 11px;
            padding: 2px 7px;
            border-radius: 999px;
            margin-left: 6px;
            font-weight: 700;
        }
        .exec-hero-subtitle { font-size: 12px; color: #cbd5e1; margin-top: 2px; }
        .exec-status-group { display: flex; flex-wrap: wrap; gap: 10px; }
        .exec-status-pill {
            background: rgba(15, 23, 42, 0.65);
            border: 1px solid rgba(148, 163, 184, 0.25);
            padding: 7px 12px;
            border-radius: 8px;
            min-width: 120px;
        }
        .exec-pill-lbl { font-size: 10px; text-transform: uppercase; color: #94a3b8; font-weight: 700; }
        .exec-pill-val { font-size: 13px; font-weight: 700; color: #f8fafc; margin-top: 2px; }
        .kpi-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 12px 14px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        }
        .kpi-label { font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; }
        .kpi-value { font-size: 20px; font-weight: 800; margin-top: 3px; }
        .card-viable {
            background: #ecfdf5;
            border: 1px solid #10b981;
            color: #064e3b;
            padding: 12px 14px;
            border-radius: 10px;
            font-size: 13px;
        }
        .card-noviable {
            background: #fef2f2;
            border: 1px solid #ef4444;
            color: #7f1d1d;
            padding: 12px 14px;
            border-radius: 10px;
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
        .mla-focus-box {
            background: #f8fafc;
            border: 1px solid #cbd5e1;
            border-left: 4px solid #0284c7;
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 12px;
        }
        .warning-stock {
            background: #fffbeb;
            border: 1px solid #f59e0b;
            color: #78350f;
            padding: 10px 14px;
            border-radius: 8px;
            font-size: 13px;
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
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------------------
# SESSION STATE
# ------------------------------------------------------------------------------
defaults_session = {
    "access_token": os.getenv("MELI_ACCESS_TOKEN", ""),
    "user_info": {},
    "tasas_cuotas": TASAS_CUOTAS_DEFAULT.copy(),
    "tarifas_actualizadas_api": False,
    "lista_gold_df": None,
    "matriz_custom_df": None,
    "active_tab": 8,
    "datos_ficha_cache": {},
    "ultima_clave_extraida": "",
}
for k, v in defaults_session.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ------------------------------------------------------------------------------
# UTILIDADES GENERALES Y CONEXIÓN MELI
# ------------------------------------------------------------------------------
def get_meli_headers(access_token: str = "") -> dict:
    headers = {
        "Accept": "application/json",
        "User-Agent": f"NQ-MeLi-Intelligence/{APP_VERSION}",
    }
    tok = (access_token or "").strip()
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    return headers


def obtener_url_login_meli() -> str:
    app_id = os.getenv("MELI_APP_ID", "TU_APP_ID")
    redirect_uri = os.getenv("MELI_REDIRECT_URI", "https://localhost:8501/")
    return (
        f"https://auth.mercadolibre.com.ar/authorization"
        f"?response_type=code&client_id={urllib.parse.quote(app_id)}"
        f"&redirect_uri={urllib.parse.quote(redirect_uri)}"
    )


def obtener_perfil_meli(access_token: str) -> dict:
    tok = (access_token or "").strip()
    if not tok:
        return {}
    try:
        r = requests.get("https://api.mercadolibre.com/users/me", headers=get_meli_headers(tok), timeout=8)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {}


def sincronizar_tarifas_financiacion_meli(access_token: str):
    if not (access_token or "").strip():
        return
    st.session_state["tarifas_actualizadas_api"] = True


def limpiar_precio_moneda(val) -> float:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = re.sub(r"[^\d,.-]", "", str(val).strip())
    if not s:
        return 0.0
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        partes = s.split(",")
        if len(partes[-1]) == 2:
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    try:
        return float(s)
    except Exception:
        return 0.0


def construir_url_canonica_meli(item_id: str = "", permalink: str = "", catalog_id: str = "") -> str:
    if permalink and str(permalink).startswith("http"):
        return str(permalink).strip()
    it = str(item_id or "").strip()
    if it.startswith("MLA"):
        num = re.sub(r"\D", "", it)
        if num:
            return f"https://articulo.mercadolibre.com.ar/MLA-{num}"
    cid = str(catalog_id or "").strip()
    if cid:
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
    cid = (category_id or "").strip()
    if not cid:
        return "Sin categoría"
    try:
        r = requests.get(f"https://api.mercadolibre.com/categories/{cid}", timeout=6)
        if r.status_code == 200:
            data = r.json()
            path = data.get("path_from_root", [])
            if path:
                return " > ".join(p.get("name", "") for p in path if p.get("name"))
            return data.get("name", cid)
    except Exception:
        pass
    return cid


@st.cache_data(ttl=1800)
def predecir_categorias_meli(titulo: str) -> list:
    q = (titulo or "").strip()
    if len(q) < 3:
        return []
    try:
        r = requests.get(
            f"https://api.mercadolibre.com/sites/MLA/domain_discovery/search?q={urllib.parse.quote(q)}",
            timeout=6,
        )
        if r.status_code == 200:
            out = []
            for item in r.json()[:5]:
                cid = item.get("category_id")
                cname = item.get("category_name") or cid
                dname = item.get("domain_name") or ""
                ruta = f"{dname} - {cname}" if dname and dname != cname else cname
                if cid:
                    out.append((cid, ruta))
            return out
    except Exception:
        pass
    return []


# ------------------------------------------------------------------------------
# LISTA GOLD Y MATRIZ LOGÍSTICA
# ------------------------------------------------------------------------------
def procesar_archivo_lista_gold(uploaded_file):
    try:
        if uploaded_file.name.lower().endswith(".csv"):
            return pd.read_csv(uploaded_file)
        return pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error al leer Lista Gold: {e}")
        return None


def cargar_matriz_articulos_oficial():
    if st.session_state.get("matriz_custom_df") is not None:
        return st.session_state["matriz_custom_df"]
    for ruta in [
        "Matriz Articulos Gemini - COTIZADOR PVP.xlsx",
        "Matriz Articulos.xlsx",
    ]:
        if os.path.exists(ruta):
            try:
                return pd.read_excel(ruta)
            except Exception:
                pass
    return None


def extraer_opciones_ean_lista_gold() -> list:
    df = st.session_state.get("lista_gold_df")
    if df is None or df.empty:
        return []
    cols_map = {str(c).strip().lower(): c for c in df.columns}
    col_ean = cols_map.get("ean") or cols_map.get("codigo") or cols_map.get("sku")
    col_desc = cols_map.get("descripcion") or cols_map.get("descripción") or cols_map.get("titulo")
    if not col_ean:
        return []
    opciones = [("-- Seleccionar desde Lista Gold --", "")]
    for _, row in df.head(300).iterrows():
        ean_v = str(row.get(col_ean) or "").strip()
        if not ean_v or ean_v.lower() == "nan":
            continue
        desc_v = str(row.get(col_desc) or "").strip() if col_desc else ""
        lbl = f"{desc_v[:45]} ({ean_v})" if desc_v else ean_v
        opciones.append((lbl, ean_v))
    return opciones


def buscar_costo_y_titulo_en_lista_gold(query: str):
    df = st.session_state.get("lista_gold_df")
    q = (query or "").strip().lower()
    if df is None or df.empty or not q:
        return False, 0.0, "", ""
    cols_map = {str(c).strip().lower(): c for c in df.columns}
    col_costo = cols_map.get("costo") or cols_map.get("precio_costo") or cols_map.get("costo_neto")
    col_desc = cols_map.get("descripcion") or cols_map.get("descripción") or cols_map.get("titulo")
    col_art = cols_map.get("articulo") or cols_map.get("artículo") or cols_map.get("sku") or cols_map.get("ean")

    for _, row in df.iterrows():
        row_str = " ".join(str(v).lower() for v in row.values if v is not None)
        if q in row_str:
            costo = limpiar_precio_moneda(row.get(col_costo)) if col_costo else 0.0
            desc = str(row.get(col_desc) or "") if col_desc else ""
            art = str(row.get(col_art) or "") if col_art else ""
            return True, costo, desc, art
    return False, 0.0, "", ""


def normalizar_ean_matriz(val) -> str:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return ""
    s = str(val).strip()
    if s.endswith(".0"):
        s = s[:-2]
    digits = re.sub(r"\D", "", s)
    return digits if len(digits) >= 8 else ""


def calcular_peso_facturable_fila_matriz(row) -> float:
    def _num(keys):
        for k in keys:
            if k in row and pd.notna(row[k]):
                v = limpiar_precio_moneda(row[k])
                if v > 0:
                    return v
        return 0.0

    alto = _num(["Alto", "alto", "HEIGHT", "height"])
    ancho = _num(["Ancho", "ancho", "WIDTH", "width"])
    prof = _num(["Profundidad", "Prof", "prof", "Largo", "largo", "DEPTH", "depth"])
    peso = _num(["Peso", "peso", "Peso kg", "peso_kg", "WEIGHT", "weight"])
    bultos = max(1.0, _num(["Bultos", "bultos", "Cajas", "cajas", "Cantidad bultos"]))

    peso_vol = (alto * ancho * prof) / 4000.0 if (alto > 0 and ancho > 0 and prof > 0) else 0.0
    peso_fact = max(peso, peso_vol) * bultos
    return peso_fact if peso_fact > 0 else 5.0


def calcular_costo_envio_por_peso_facturable(peso_kg: float, pvp: float = 200000.0) -> float:
    p = max(0.1, float(peso_kg or 1.0))
    if p <= 1:
        base = 8500.0
    elif p <= 5:
        base = 12500.0
    elif p <= 10:
        base = 18500.0
    elif p <= 20:
        base = 29000.0
    elif p <= 30:
        base = 39090.0
    else:
        base = 39090.0 + (p - 30.0) * 1150.0
    return round(base, 2)


def calcular_flete_desde_embalaje(alto, ancho, prof, peso, pvp: float = 200000.0):
    def _extraer_num(txt):
        if not txt:
            return 0.0
        m = re.search(r"(\d+(?:[.,]\d+)?)", str(txt))
        if not m:
            return 0.0
        return float(m.group(1).replace(",", "."))

    h = _extraer_num(alto)
    w = _extraer_num(ancho)
    d = _extraer_num(prof)
    kg = _extraer_num(peso)

    peso_vol = (h * w * d) / 4000.0 if (h > 0 and w > 0 and d > 0) else 0.0
    peso_fact = max(kg, peso_vol)
    if peso_fact <= 0:
        return 0.0, 0.0, 0.0, False
    return calcular_costo_envio_por_peso_facturable(peso_fact, pvp), peso_fact, peso_vol, True


def buscar_datos_en_matriz(query: str, pvp: float = 200000.0):
    df = cargar_matriz_articulos_oficial()
    q = (query or "").strip().lower()
    if df is None or df.empty or not q:
        return False, 0.0, 0.0, 0.0, 0.0, 1, ""
    for _, row in df.iterrows():
        row_str = " ".join(str(v).lower() for v in row.values if v is not None)
        if q in row_str:
            peso_fact = calcular_peso_facturable_fila_matriz(row)
            bultos = 1
            for k in ["Bultos", "bultos", "Cajas", "cajas"]:
                if k in row and pd.notna(row[k]):
                    b = int(limpiar_precio_moneda(row[k]))
                    if b > 0:
                        bultos = b
                        break
            costo_env = calcular_costo_envio_por_peso_facturable(peso_fact, pvp)
            peso_unit = round(peso_fact / max(1, bultos), 2)
            desc = str(row.get("Descripcion") or row.get("Articulo") or "")
            return True, costo_env, peso_unit, peso_fact, costo_env / max(1, bultos), bultos, desc
    return False, 0.0, 0.0, 0.0, 0.0, 1, ""


def buscar_datos_en_matriz_completa(query: str):
    df = cargar_matriz_articulos_oficial()
    q = (query or "").strip().lower()
    if df is None or df.empty or not q:
        return "", "", "", ""
    for _, row in df.iterrows():
        row_str = " ".join(str(v).lower() for v in row.values if v is not None)
        if q in row_str:
            ancho = str(row.get("Ancho") or row.get("ancho") or "")
            alto = str(row.get("Alto") or row.get("alto") or "")
            prof = str(row.get("Profundidad") or row.get("Prof") or row.get("Largo") or "")
            peso = str(row.get("Peso") or row.get("peso") or "")
            return ancho, alto, prof, peso
    return "", "", "", ""


def extraer_ids_meli_avanzado(texto: str) -> dict:
    raw = (texto or "").strip()
    out = {
        "raw": raw,
        "tipo": "TEXT",
        "url_original": raw if raw.startswith("http") else "",
        "item_id": "",
        "alt_item_id": "",
        "catalog_id": "",
        "ean": "",
    }
    if not raw:
        return out

    m_mla = re.search(r"\b(MLA[-_]?\d+)\b", raw, re.IGNORECASE)
    if m_mla:
        clean_mla = re.sub(r"[^A-Za-z0-9]", "", m_mla.group(1)).upper()
        out["tipo"] = "MELI_URL_OR_ID"
        out["item_id"] = clean_mla

    m_mlau = re.search(r"\b(MLAU\d+)\b", raw, re.IGNORECASE)
    if m_mlau:
        out["tipo"] = "MELI_URL_OR_ID"
        out["alt_item_id"] = m_mlau.group(1).upper()

    m_cat = re.search(r"/p/(MLA\d+)", raw, re.IGNORECASE)
    if m_cat:
        out["tipo"] = "MELI_URL_OR_ID"
        out["catalog_id"] = m_cat.group(1).upper()

    if out["tipo"] == "TEXT":
        digits = re.sub(r"\D", "", raw)
        if len(digits) in (8, 12, 13, 14) and digits == re.sub(r"\s", "", raw):
            out["tipo"] = "EAN"
            out["ean"] = digits

    return out


def extraer_id_catalogo_o_ean_input(val: str):
    s = (val or "").strip()
    if re.match(r"^MLA\d+$", s, re.IGNORECASE):
        return "CATALOG_ID", s.upper()
    digits = re.sub(r"\D", "", s)
    if len(digits) in (8, 12, 13, 14):
        return "EAN", digits
    return "TEXT", s


def mapear_tipo_envio_meli(logistic_type: str, free_shipping: bool) -> str:
    lt = (logistic_type or "").lower()
    if lt == "fulfillment":
        return "Full"
    if lt in ("xd_drop_off", "cross_docking", "drop_off"):
        return "Colecta / Agencia"
    if lt == "self_service":
        return "Flex"
    return "Envío Gratis" if free_shipping else "Mercado Envíos"


def calcular_pvp_en_cuotas(pvg_base: float, cuotas: int, ofertas: list) -> float:
    for of in ofertas or []:
        inst = of.get("installments")
        if isinstance(inst, dict) and int(inst.get("quantity") or 0) == cuotas:
            amt = limpiar_precio_moneda(inst.get("amount"))
            if amt > 0:
                return round(amt * cuotas, 2)
    mapa_tasas = {3: 0.065, 6: 0.115, 9: 0.155, 12: 0.195}
    recargo = mapa_tasas.get(cuotas, 0.0)
    return round(float(pvg_base) * (1.0 + recargo), 2)


def consultar_ofertas_ean_para_matriz(ean: str, desc: str, headers: dict) -> list:
    ofertas = []
    try:
        url = f"https://api.mercadolibre.com/products/search?status=active&site_id=MLA&product_identifier={urllib.parse.quote(ean)}"
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200:
            for prod in r.json().get("results", [])[:2]:
                cid = prod.get("id")
                bb = prod.get("buy_box_winner") or {}
                if bb.get("price"):
                    ofertas.append({
                        "price": float(bb["price"]),
                        "permalink": construir_url_canonica_meli(bb.get("item_id", ""), "", cid),
                        "seller_id": bb.get("seller_id"),
                        "logistic_type": (bb.get("shipping") or {}).get("logistic_type", ""),
                        "free_shipping": bool((bb.get("shipping") or {}).get("free_shipping", False)),
                        "installments": bb.get("installments"),
                        "item_id": bb.get("item_id", ""),
                        "catalog_id": cid or "",
                    })
                if cid:
                    ri = requests.get(f"https://api.mercadolibre.com/products/{cid}/items", headers=headers, timeout=8)
                    if ri.status_code == 200:
                        for it in ri.json().get("results", [])[:8]:
                            if it.get("price"):
                                ofertas.append({
                                    "price": float(it["price"]),
                                    "permalink": construir_url_canonica_meli(it.get("item_id") or it.get("id", ""), it.get("permalink", ""), cid),
                                    "seller_id": it.get("seller_id") or (it.get("seller") or {}).get("id"),
                                    "logistic_type": (it.get("shipping") or {}).get("logistic_type", ""),
                                    "free_shipping": bool((it.get("shipping") or {}).get("free_shipping", False)),
                                    "installments": it.get("installments"),
                                    "item_id": it.get("item_id") or it.get("id", ""),
                                    "catalog_id": cid,
                                })
    except Exception:
        pass
    ofertas.sort(key=lambda x: x["price"])
    return ofertas


def dataframe_a_excel_bytes(df: pd.DataFrame, sheet_name: str = "Hoja1") -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name[:31] or "Hoja1")
    buf.seek(0)
    return buf.getvalue()


# ------------------------------------------------------------------------------
# COMPARADOR POR IMAGEN SIMILAR (UNIVERSAL PARA CUALQUIER PRODUCTO - v191.0)
# ------------------------------------------------------------------------------
def calcular_firma_visual_robusta(img_bytes: bytes):
    if not img_bytes:
        return None
    try:
        im = Image.open(io.BytesIO(img_bytes)).convert("RGB").resize((32, 32))
        arr = np.asarray(im, dtype=np.float32) / 255.0
        hist_r, _ = np.histogram(arr[:, :, 0], bins=8, range=(0.0, 1.0))
        hist_g, _ = np.histogram(arr[:, :, 1], bins=8, range=(0.0, 1.0))
        hist_b, _ = np.histogram(arr[:, :, 2], bins=8, range=(0.0, 1.0))
        grid = arr.mean(axis=2).resize if hasattr(arr.mean(axis=2), "resize") else np.asarray(
            Image.fromarray((arr.mean(axis=2) * 255).astype(np.uint8)).resize((8, 8)),
            dtype=np.float32,
        ) / 255.0
        vec = np.concatenate([hist_r, hist_g, hist_b, grid.flatten()]).astype(np.float32)
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else None
    except Exception:
        return None


@st.cache_data(ttl=3600)
def obtener_firma_miniatura_url(url: str):
    if not url or not str(url).startswith("http"):
        return None
    try:
        r = requests.get(str(url).strip(), timeout=6)
        if r.status_code == 200 and r.content:
            return calcular_firma_visual_robusta(r.content)
    except Exception:
        pass
    return None


def generar_variantes_consulta_producto(consulta: str) -> list:
    base = re.sub(r"\s+", " ", (consulta or "").strip())
    if not base:
        return []
    variantes = [base]
    palabras = base.split()
    if len(palabras) > 3:
        variantes.append(" ".join(palabras[:3]))
    if len(palabras) > 2:
        variantes.append(" ".join(palabras[:2]))
    if len(palabras) > 1:
        variantes.append(palabras[0])
    vistas = []
    for v in variantes:
        vl = v.lower()
        if vl not in vistas:
            vistas.append(vl)
    return [v for v in variantes if v.lower() in vistas][:4]


def buscar_web_publica_meli_candidatos(consulta: str) -> list:
    q = (consulta or "").strip()
    if not q:
        return []
    slug = urllib.parse.quote(q.lower().replace(" ", "-"))
    url_listado = f"https://listado.mercadolibre.com.ar/{slug}"
    headers_web = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
    }
    candidatos = []
    try:
        r = requests.get(url_listado, headers=headers_web, timeout=10, allow_redirects=True)
        if r.status_code == 200 and len(r.text) > 1000:
            html = r.text
            for m in re.finditer(
                r'<a[^>]+href="(https://(?:articulo|www)\.mercadolibre\.com\.ar/[^"]+)"[^>]*>(.*?)</a>',
                html,
                re.DOTALL | re.IGNORECASE,
            ):
                link = m.group(1).split("#")[0].split("?")[0]
                inner = re.sub(r"<[^>]+>", " ", m.group(2))
                titulo = re.sub(r"\s+", " ", inner).strip()
                if len(titulo) < 8 or "mercadolibre" in titulo.lower():
                    continue
                m_id = re.search(r"MLA[-_]?(\d+)", link, re.IGNORECASE)
                item_id = f"MLA{m_id.group(1)}" if m_id else f"WEB-{len(candidatos)+1}"
                if any(c["link"] == link for c in candidatos):
                    continue
                candidatos.append({
                    "id": item_id,
                    "title": titulo[:120],
                    "price": 0.0,
                    "available_quantity": 0,
                    "sold_quantity": 0,
                    "permalink": link,
                    "thumbnail": "",
                    "seller_name": "Mercado Libre Web",
                })
                if len(candidatos) >= 25:
                    break

            imgs = []
            for img_u in re.findall(
                r'https://http2\.mlstatic\.com/D_NQ_NP_[^"\'\s>\\]+\.(?:jpg|webp|png)',
                html,
            ):
                clean_u = img_u.replace("-O.webp", "-O.jpg").replace("-F.webp", "-O.jpg")
                if clean_u not in imgs:
                    imgs.append(clean_u)

            precios = [
                limpiar_precio_moneda(p)
                for p in re.findall(r'"price"\s*:\s*"?(\d+(?:[.,]\d+)?)"?', html)
                if limpiar_precio_moneda(p) > 50
            ]

            for idx_c, c in enumerate(candidatos):
                if idx_c < len(imgs):
                    c["thumbnail"] = imgs[idx_c]
                if idx_c < len(precios):
                    c["price"] = precios[idx_c]
    except Exception:
        pass
    return candidatos


def consultar_items_meli_con_diagnostico(consulta: str, access_token: str = "", limit: int = 40):
    headers = get_meli_headers(access_token)
    variantes = generar_variantes_consulta_producto(consulta)
    diag = {
        "endpoint_usado": "",
        "status_code": "",
        "error": "",
        "total_api": 0,
    }

    for var in variantes:
        q_enc = urllib.parse.quote(var)
        endpoints_api = [
            f"https://api.mercadolibre.com/sites/MLA/search?q={q_enc}&limit={limit}",
            f"https://api.mercadolibre.com/products/search?status=active&site_id=MLA&q={q_enc}&limit={min(limit, 30)}",
        ]
        for ep in endpoints_api:
            try:
                r = requests.get(ep, headers=headers, timeout=8)
                diag["endpoint_usado"] = ep.split("?")[0].replace("https://api.mercadolibre.com", "")
                diag["status_code"] = r.status_code
                if r.status_code == 200:
                    data = r.json()
                    results = data.get("results", [])
                    items = []
                    for it in results:
                        if it.get("price") is not None or it.get("title") or it.get("name"):
                            items.append({
                                "id": it.get("id") or it.get("item_id") or "",
                                "title": it.get("title") or it.get("name") or "",
                                "price": float(it.get("price") or ((it.get("buy_box_winner") or {}).get("price") or 0.0)),
                                "available_quantity": int(it.get("available_quantity") or 0),
                                "sold_quantity": int(it.get("sold_quantity") or 0),
                                "permalink": it.get("permalink") or "",
                                "thumbnail": it.get("secure_thumbnail") or it.get("thumbnail") or ((it.get("pictures") or [{}])[0].get("secure_url") if it.get("pictures") else ""),
                                "seller": it.get("seller"),
                                "seller_id": it.get("seller_id"),
                                "catalog_product_id": it.get("catalog_product_id") or it.get("id") or "",
                            })
                    if items:
                        diag["total_api"] = len(items)
                        return items, diag
                else:
                    try:
                        err_msg = r.json().get("message", r.text[:120])
                    except Exception:
                        err_msg = r.text[:120]
                    diag["error"] = f"HTTP {r.status_code} en {diag['endpoint_usado']}: {err_msg}"
            except Exception as e:
                diag["error"] = str(e)

    for var in variantes:
        web_items = buscar_web_publica_meli_candidatos(var)
        if web_items:
            diag["endpoint_usado"] = f"web_fallback:/listado/{var}"
            diag["status_code"] = 200
            diag["error"] = ""
            diag["total_api"] = len(web_items)
            return web_items, diag

    return [], diag


def buscar_publicaciones_similares_por_imagen(
    consulta_base: str,
    img_bytes: bytes = None,
    access_token: str = "",
    candidatos_externos: list = None,
):
    if candidatos_externos is not None:
        raw_items = candidatos_externos
        diag = {
            "endpoint_usado": "planilla_externa",
            "status_code": 200,
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
        precio = float(item.get("price") or 0.0)
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


# ------------------------------------------------------------------------------
# RADIOGRAFÍA MLA, COMPETENCIA Y EXTRACTOR
# ------------------------------------------------------------------------------
@st.cache_data(ttl=600)
def analizar_mla_y_mercado(query_input: str, access_token: str = ""):
    headers = get_meli_headers(access_token)
    parsed = extraer_ids_meli_avanzado(query_input)
    item_objetivo = None
    catalog_id = parsed.get("catalog_id", "")
    category_id = ""
    search_query = parsed.get("raw", "")

    if parsed["tipo"] == "MELI_URL_OR_ID":
        for cid_it in [x for x in [parsed["item_id"], parsed["alt_item_id"]] if x]:
            try:
                r_it = requests.get(f"https://api.mercadolibre.com/items/{cid_it}", headers=headers, timeout=8)
                if r_it.status_code == 200:
                    b = r_it.json()
                    item_objetivo = {
                        "id": b.get("id"),
                        "title": b.get("title", ""),
                        "price": float(b.get("price", 0.0)),
                        "stock": int(b.get("available_quantity", 0)),
                        "sold_quantity": int(b.get("sold_quantity", 0)),
                        "category_id": b.get("category_id", ""),
                        "catalog_product_id": b.get("catalog_product_id", ""),
                        "vendedor_name": resolver_vendedor_nickname_oficial(b.get("seller_id"), access_token),
                        "permalink": construir_url_canonica_meli(b.get("id"), b.get("permalink", ""), b.get("catalog_product_id", "")),
                    }
                    catalog_id = item_objetivo["catalog_product_id"] or catalog_id
                    category_id = item_objetivo["category_id"]
                    search_query = item_objetivo["title"]
                    break
            except Exception:
                pass

    raw_items = []
    if catalog_id:
        try:
            res_pi = requests.get(f"https://api.mercadolibre.com/products/{catalog_id}/items", headers=headers, timeout=8)
            if res_pi.status_code == 200:
                raw_items = res_pi.json().get("results", [])
        except Exception:
            pass
    if not raw_items and search_query:
        items_tmp, _ = consultar_items_meli_con_diagnostico(" ".join(search_query.split()[:5]), access_token, limit=40)
        raw_items = items_tmp

    items_procesados = []
    for r in raw_items[:40]:
        item_id = r.get("item_id") or r.get("id", "")
        seller_id = r.get("seller_id") or ((r.get("seller") or {}).get("id") if isinstance(r.get("seller"), dict) else None)
        items_procesados.append({
            "vendedor_name": resolver_vendedor_nickname_oficial(seller_id, access_token),
            "id": item_id,
            "title": r.get("title", ""),
            "price": float(r.get("price", 0.0)),
            "stock": int(r.get("stock") or r.get("available_quantity") or 0),
            "sold_quantity": int(r.get("sold_quantity", 0)),
            "permalink": construir_url_canonica_meli(item_id, r.get("permalink", ""), catalog_id),
            "category_id": r.get("category_id", category_id or "MLA4765"),
        })

    if item_objetivo and not any(x["id"] == item_objetivo["id"] for x in items_procesados):
        items_procesados.insert(0, item_objetivo)

    return item_objetivo, items_procesados


@st.cache_data(ttl=900)
def buscar_competencia_integral_ean(query_key: str, access_token: str = None, titulo_gold: str = "", articulo_gold: str = ""):
    termino = " ".join(filter(None, [titulo_gold.strip(), articulo_gold.strip()])).strip() or query_key.strip()
    items_raw, _ = consultar_items_meli_con_diagnostico(termino, access_token or "", limit=40)
    procesados = []
    for r in items_raw:
        procesados.append({
            "vendedor_name": r.get("seller_name") or "Vendedor MeLi",
            "id": r.get("id", ""),
            "title": r.get("title", ""),
            "price": float(r.get("price", 0.0)),
            "installments_qty": 1,
            "stock": int(r.get("available_quantity", 0)),
            "permalink": r.get("permalink", ""),
        })
    return "", termino, procesados


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
        "modelo": art_gold_b or "",
        "family_name": (desc_gold_b or "")[:60].strip(),
        "descripcion": "",
        "fotos": [],
        "video_id": "",
        "ancho": "",
        "alto": "",
        "prof": "",
        "peso": "",
        "found_matriz": False,
    }
    parsed = extraer_ids_meli_avanzado(query_builder)
    if parsed["tipo"] == "MELI_URL_OR_ID":
        for cid in [x for x in [parsed["catalog_id"], parsed["item_id"], parsed["alt_item_id"]] if x]:
            ep = f"https://api.mercadolibre.com/products/{cid}" if cid.startswith("MLA") and parsed["catalog_id"] == cid else f"https://api.mercadolibre.com/items/{cid}"
            try:
                r = requests.get(ep, headers=headers_ext, timeout=8)
                if r.status_code == 200:
                    d = r.json()
                    res_data["exito_externo"] = True
                    res_data["family_name"] = (d.get("name") or d.get("title") or res_data["family_name"])[:60]
                    if d.get("category_id"):
                        res_data["cat_meli_id"] = d["category_id"]
                    if d.get("price"):
                        res_data["pvp_sugerido"] = float(d["price"])
                    for pic in d.get("pictures", [])[:10]:
                        u = pic.get("secure_url") or pic.get("url")
                        if u and u not in res_data["fotos"]:
                            res_data["fotos"].append(u)
                    break
            except Exception as e:
                res_data["error_api"] = str(e)
    return res_data


# ------------------------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------------------------
with st.sidebar:
    st.title("⚡ Control Panel")
    st.caption(f"Versión activa: **{APP_VERSION}**")
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
        st.link_button("🔗 CONECTAR CON MERCADO LIBRE", obtener_url_login_meli(), type="primary", use_container_width=True)

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
# HEADER Y NAVEGACIÓN (9 SOLAPAS)
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
            <div class="exec-status-pill"><div class="exec-pill-lbl">API Mercado Libre</div><div class="exec-pill-val">{estado_meli_html}</div></div>
            <div class="exec-status-pill"><div class="exec-pill-lbl">Lista Gold</div><div class="exec-pill-val">{skus_gold_txt}</div></div>
            <div class="exec-status-pill"><div class="exec-pill-lbl">Matriz Logística</div><div class="exec-pill-val">{skus_matriz_txt}</div></div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

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
]

nav_cols = st.columns(len(MENU_ITEMS), gap="small")
for idx, (icono, titulo_corto) in enumerate(MENU_ITEMS):
    with nav_cols[idx]:
        if st.button(f"{icono} {titulo_corto}", key=f"nav_btn_{idx}", use_container_width=True):
            st.session_state["active_tab"] = idx
            st.rerun()

st.markdown("<hr style='margin: 8px 0 16px 0; border-color: #e2e8f0;'>", unsafe_allow_html=True)
tab_activa = st.session_state["active_tab"]

if tab_activa == 0:
    st.header("🧮 Simulación de Costos & Auditoría Neta Real")
    query_costos = st.text_input("Código SKU / EAN / MLA / URL", key="q_costos")
    if query_costos:
        found_g, costo_g, desc_g, _ = buscar_costo_y_titulo_en_lista_gold(query_costos)
        pvp_sim = st.number_input("Precio de Venta Simulado ($ ARS)", min_value=100.0, value=costo_g * 2.0 if found_g else 200000.0, step=500.0)
        costo_sim = st.number_input("Costo Producto ($ ARS)", min_value=0.0, value=costo_g if found_g else 90000.0, step=500.0)
        neto = pvp_sim * (1.0 - 0.145 - ALICUOTA_IIBB - ALICUOTA_IVA) - costo_sim
        st.metric("Neto Estimado", f"${neto:,.2f}")

elif tab_activa == 1:
    st.header("⚡ Monitor de Precios & Control Anti-Pérdida")
    q_mon = st.text_input("Buscador EAN / SKU / Producto", key="search_query_mon")
    if st.button("⚡ ANALIZAR COMPETENCIA", type="primary") and q_mon:
        _, _, items_m = buscar_competencia_integral_ean(q_mon, st.session_state["access_token"])
        if items_m:
            st.dataframe(pd.DataFrame(items_m), use_container_width=True, hide_index=True)
        else:
            st.info("No se encontraron publicaciones activas.")

elif tab_activa == 2:
    st.header("📊 Radiografía de Cualquier MLA & Inteligencia de Mercado")
    q_mla = st.text_input("Código MLA / URL / Palabra Clave", key="q_mercado_mla")
    if st.button("🔍 AUDITAR MLA / MERCADO", type="primary") and q_mla:
        foco, mercado = analizar_mla_y_mercado(q_mla, st.session_state["access_token"])
        if foco:
            st.json(foco)
        if mercado:
            st.dataframe(pd.DataFrame(mercado), use_container_width=True, hide_index=True)

elif tab_activa == 3:
    st.header("📦 Matriz de Artículos & Costos Logísticos Oficiales")
    mat = cargar_matriz_articulos_oficial()
    if mat is not None:
        st.dataframe(mat, use_container_width=True)
    else:
        st.info("Subí una matriz desde el panel lateral.")

elif tab_activa == 4:
    st.header("🤖 Asistente IA para Gestión de Preguntas & Reclamos")
    preg = st.text_input("Simular consulta de cliente")
    if preg:
        st.markdown('<div class="ai-bubble">¡Hola! Gracias por tu consulta. Realizamos envíos a todo el país con embalaje protegido.</div>', unsafe_allow_html=True)

elif tab_activa == 5:
    st.header("🚀 Publicador a Catálogo Definitivo")
    q_b = st.text_input("Código MLA / URL / EAN", key="q_builder")
    if st.button("⚡ EXTRAER Y CARGAR", type="primary") and q_b:
        st.json(extraer_ficha_completa_meli(q_b, st.session_state["access_token"]))

elif tab_activa == 6:
    st.header("🛡️ Modo Defensivo")
    if not st.session_state["access_token"]:
        st.warning("Conectá tu Access Token en el panel lateral.")
    else:
        st.info("Token conectado. Listo para escanear publicaciones.")

elif tab_activa == 7:
    st.header("📥 Cotizador & Completador Masivo de Matriz (.xlsx)")
    up_cot = st.file_uploader("Subí tu archivo de matriz (.xlsx)", type=["xlsx"], key="uploader_matriz_cotizador_tab7")
    if up_cot is not None:
        df_c = pd.read_excel(up_cot)
        st.dataframe(df_c.head(20), use_container_width=True)

elif tab_activa == 8:
    st.header(f"🔍 Comparador por Imagen Similar ({APP_VERSION})")
    st.caption(
        "Funciona para cualquier producto combinando /sites/MLA/search, /products/search, consultas reducidas, respaldo web público de Mercado Libre o planilla CSV/XLSX, y similitud visual con tu foto."
    )

    col_img, col_txt = st.columns([1, 2])
    with col_img:
        img_subida = st.file_uploader(
            "🖼️ Imagen de referencia",
            type=["jpg", "jpeg", "png", "webp"],
            key="cmp_img_ref_v191",
        )
        if img_subida is not None:
            st.image(img_subida, caption="Referencia cargada", use_container_width=True)

    with col_txt:
        termino = st.text_input(
            "🏷️ Palabra clave / tipo de producto para consultar",
            value="placard 2 puertas 2 cajones",
            key="cmp_txt_query_v191",
        )
        archivo_cand = st.file_uploader(
            "📄 Planilla opcional de candidatos (CSV/XLSX) con columnas: titulo, precio, link, miniatura",
            type=["csv", "xlsx"],
            key="cmp_cand_file_v191",
        )

    if st.button("🔍 BUSCAR PUBLICACIONES SIMILARES", type="primary", use_container_width=True, key="cmp_btn_run_v191"):
        img_bytes = img_subida.getvalue() if img_subida is not None else None
        candidatos_ext = None

        if archivo_cand is not None:
            try:
                df_c = pd.read_csv(archivo_cand) if archivo_cand.name.lower().endswith(".csv") else pd.read_excel(archivo_cand)
                candidatos_ext = []
                for idx_c, r_c in df_c.iterrows():
                    candidatos_ext.append({
                        "id": str(r_c.get("id") or f"ITEM-{idx_c+1}"),
                        "title": str(r_c.get("titulo") or r_c.get("title") or ""),
                        "price": limpiar_precio_moneda(r_c.get("precio") or r_c.get("price") or 0),
                        "available_quantity": int(pd.to_numeric(r_c.get("stock") or 0, errors="coerce") or 0),
                        "sold_quantity": int(pd.to_numeric(r_c.get("ventas") or 0, errors="coerce") or 0),
                        "permalink": str(r_c.get("link") or r_c.get("permalink") or ""),
                        "thumbnail": str(r_c.get("miniatura") or r_c.get("thumbnail") or ""),
                        "seller_name": str(r_c.get("vendedor") or "Catálogo / Planilla"),
                    })
            except Exception as e:
                st.error(f"Error al leer la planilla de candidatos: {e}")

        with st.spinner("Consultando candidatos y calculando similitud visual..."):
            filas, diag = buscar_publicaciones_similares_por_imagen(
                consulta_base=termino,
                img_bytes=img_bytes,
                access_token=st.session_state["access_token"],
                candidatos_externos=candidatos_ext,
            )
        st.session_state["cmp_sim_filas_v191"] = filas
        st.session_state["cmp_sim_diag_v191"] = diag

    if "cmp_sim_filas_v191" in st.session_state:
        filas = st.session_state["cmp_sim_filas_v191"]
        diag = st.session_state.get("cmp_sim_diag_v191", {})
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

        if diag.get("endpoint_usado"):
            st.caption(f"Fuente usada: `{diag.get('endpoint_usado')}` · HTTP {diag.get('status_code')}")

        if not filas and diag.get("error"):
            st.warning(f"Detalle API: {diag.get('error')}")

        if filas:
            st.success(f"Se encontraron **{len(filas)}** publicaciones con su enlace directo.")
            df_res = pd.DataFrame(filas)
            st.dataframe(
                df_res,
                column_config={
                    "Similitud Imagen (%)": st.column_config.NumberColumn(format="%.1f%%"),
                    "Miniatura": st.column_config.ImageColumn("Imagen", width="small"),
                    "Precio ($)": st.column_config.NumberColumn(format="$%,.0f"),
                    "Stock Disp.": st.column_config.NumberColumn(format="%d"),
                    "Ventas Acum.": st.column_config.NumberColumn(format="%d"),
                    "Link": st.column_config.LinkColumn("Link MeLi", display_text="Abrir 🔗"),
                },
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info(
                "No se obtuvieron publicaciones para ese término. Probá con una palabra clave más general o subí una planilla CSV/XLSX de candidatos."
            )
