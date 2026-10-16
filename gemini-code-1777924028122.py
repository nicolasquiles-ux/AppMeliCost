import io
import re
import os
from datetime import datetime
import pandas as pd
import requests
import streamlit as st

# Módulo OAuth local
try:
    import meli_auth
    HAS_MELI_AUTH = True
except ImportError:
    HAS_MELI_AUTH = False

V_NUMBER = "45.0 Pro SaaS"

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
# 1. MOTOR ROBUSTO DE LECTURA DE LA LISTA GOLD 2026
# =========================================================
def procesar_dataframe_lista_gold(df_raw):
    """Detecta la fila exacta de encabezados y extrae los artículos Gold."""
    try:
        header_row = None
        for idx in range(min(15, len(df_raw))):
            row_vals = [str(v).upper() for v in df_raw.iloc[idx].values if pd.notna(v)]
            if any("EAN" in v for v in row_vals) or any("ARTICULO" in v for v in row_vals):
                header_row = idx
                break

        if header_row is not None:
            headers = [str(v).strip().upper() for v in df_raw.iloc[header_row].values]
            df = df_raw.iloc[header_row + 1:].copy()
            df.columns = headers
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


def cargar_lista_precios_general(uploaded_file, url_gsheets):
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                df_raw = pd.read_csv(uploaded_file)
            else:
                df_raw = pd.read_excel(uploaded_file, header=None)
            df_proc = procesar_dataframe_lista_gold(df_raw)
            if not df_proc.empty:
                return df_proc, f"Archivo Subido Manualmente ({uploaded_file.name})"
        except Exception:
            pass

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

    nombre_archivo = "Lista de Precios Centro Estant Septiembre 2026 (LISTA GOLD).xlsx"
    if os.path.exists(nombre_archivo):
        try:
            df_raw = pd.read_excel(nombre_archivo, header=None)
            df_proc = procesar_dataframe_lista_gold(df_raw)
            if not df_proc.empty:
                return df_proc, "Excel Local Gold Septiembre 2026"
        except Exception:
            pass

    return pd.DataFrame(), "Sin Cargar"


# --- CONTROLES EN SIDEBAR ---
st.sidebar.title("📁 Cargar Lista de Precios")
file_up_sidebar = st.sidebar.file_uploader(
    "Subir Archivo Excel/CSV Manual",
    type=["xlsx", "csv"],
    key="file_up_side"
)

url_gsheet_input = st.sidebar.text_input(
    "🌐 Enlace Google Sheets",
    placeholder="https://docs.google.com/spreadsheets/d/...",
    key="url_gsheet_sidebar"
)

if st.sidebar.button("🔄 Recargar y Limpiar Caché", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

df_articulos_base, origen_lista = cargar_lista_precios_general(file_up_sidebar, url_gsheet_input)


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
nq_main_color = "#2B3E4F"
gray_bg = "#F8FAFC"


def get_headers(access_token=None):
    headers = HEADERS_MELI.copy()
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return headers


@st.cache_data(ttl=3600)
def obtener_nickname_vendedor(seller_id, access_token=None):
    if not seller_id or str(seller_id) in ["Sin ID", "None", "0"]:
        return "Oficial / Catálogo"
    try:
        url = f"https://api.mercadolibre.com/users/{seller_id}"
        res = requests.get(url, headers=get_headers(access_token), timeout=4)
        if res.status_code == 200:
            return res.json().get("nickname", f"Vendedor {seller_id}")
    except Exception:
        pass
    return f"Vendedor {seller_id}"


def obtener_flete_real_api(item_id, desc_factor=0.50, access_token=None, zip_code="1414"):
    if not item_id or item_id == "Sin ID":
        return TABLA_ME2_BASE["De 20 a 25 kg"][1]

    raw_id = item_id if item_id.startswith("MLA") else f"MLA{item_id}"
    url = f"https://api.mercadolibre.com/items/{raw_id}/shipping_options?zip_code={zip_code}"

    try:
        res = requests.get(url, headers=get_headers(access_token), timeout=4)
        if res.status_code == 200:
            options = res.json().get("options", [])
            for opt in options:
                if opt.get("shipping_method_id") in [182, 73328]:
                    costo_full = float(opt.get("list_cost", 0.0))
                    return costo_full * desc_factor
            if options:
                return float(options[0].get("list_cost", 0.0)) * desc_factor
    except Exception:
        pass
    return TABLA_ME2_BASE["De 20 a 25 kg"][1]


def extraer_ventas_de_objeto(item_dict, access_token=None):
    if not item_dict:
        return None

    if "sold_quantity" in item_dict and item_dict["sold_quantity"] is not None:
        return int(item_dict["sold_quantity"])

    bb_winner = item_dict.get("buy_box_winner", {})
    if "sold_quantity" in bb_winner and bb_winner["sold_quantity"] is not None:
        return int(bb_winner["sold_quantity"])

    item_id = str(item_dict.get("id", item_dict.get("item_id", ""))).replace("MLA", "").strip()
    if item_id:
        raw_id = f"MLA{item_id}"
        url = f"https://api.mercadolibre.com/items/{raw_id}"
        try:
            res = requests.get(url, headers=get_headers(access_token), timeout=4)
            if res.status_code == 200:
                data = res.json()
                if "sold_quantity" in data and data["sold_quantity"] is not None:
                    return int(data["sold_quantity"])
        except Exception:
            pass

    return None


def detectar_financiacion_item(item_dict):
    """Detecta si la publicación es Premium o incluye Cuotas Mismo Precio."""
    listing_type = item_dict.get("listing_type_id", "")
    tags = item_dict.get("tags", [])

    if listing_type == "gold_pro" or "gold_pro" in tags:
        return "6 Cuotas Mismo Precio (19.09%)", 19.09
    
    return "1 Pago / Clásica (0.00%)", 0.0


# =========================================================
# 2. MOTOR BÚSQUEDA MULTI-NIVEL EN CASCADA
# =========================================================
def buscar_items_api_oficial(query_term, limit=10, access_token=None):
    headers = get_headers(access_token)
    term_clean = str(query_term).strip().split(".")[0]

    # Soporte para enlaces directos tipo MLA-2857011148 o URLs de MeLi
    match_mla = re.search(r"MLA-?(\d+)", term_clean, re.IGNORECASE)
    if match_mla:
        raw_mla = f"MLA{match_mla.group(1)}"
        try:
            url_single = f"https://api.mercadolibre.com/items/{raw_mla}"
            res_s = requests.get(url_single, headers=headers, timeout=5)
            if res_s.status_code == 200:
                return [res_s.json()], "Publicación Directa (URL / ID)"
        except Exception:
            pass

    if term_clean.isdigit() and len(term_clean) >= 8:
        try:
            url = f"https://api.mercadolibre.com/sites/MLA/search?gtin={term_clean}&limit={limit}"
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                results = res.json().get("results", [])
                if results:
                    return results, "GTIN / EAN Directo"
        except Exception:
            pass

    try:
        url = f"https://api.mercadolibre.com/sites/MLA/search?q={requests.utils.quote(term_clean)}&limit={limit}"
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            results = res.json().get("results", [])
            if results:
                return results, "Query Búsqueda Libre"
    except Exception:
        pass

    try:
        url_cat = f"https://api.mercadolibre.com/products/search?status=active&site_id=MLA&q={requests.utils.quote(term_clean)}"
        res_cat = requests.get(url_cat, headers=headers, timeout=5)
        if res_cat.status_code == 200:
            products = res_cat.json().get("results", [])
            if products:
                cat_id = products[0].get("id")
                url_items = f"https://api.mercadolibre.com/products/{cat_id}/items"
                res_items = requests.get(url_items, headers=headers, timeout=5)
                if res_items.status_code == 200:
                    items_cat = res_items.json().get("results", [])
                    if items_cat:
                        return items_cat, "Catálogo Buy Box MeLi"
    except Exception:
        pass

    try:
        url_fb = f"https://api.mercadolibre.com/sites/MLA/search?q={requests.utils.quote('Centro Estant ' + term_clean)}&limit={limit}"
        res_fb = requests.get(url_fb, headers=headers, timeout=5)
        if res_fb.status_code == 200:
            results = res_fb.json().get("results", [])
            if results:
                return results, "Fallback Comercial (Marca + Modelo)"
    except Exception:
        pass

    return [], "Sin Resultados"


# =========================================================
# 3. INTERFAZ Y ESTILOS
# =========================================================
css_template = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=400;600;700;800&display=swap');
html, body, [class*="css"] {{ font-family: 'Plus Jakarta Sans', sans-serif; background-color: #FFFFFF; }}
.stApp {{ background-color: #FFFFFF; }}
.nq-header-container {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 18px 25px; background-color: #FFFFFF; box-shadow: 0 4px 12px rgba(0,0,0,0.03); 
    margin-bottom: 20px; border-radius: 14px; border: 1px solid #E2E8F0;
}}
.nq-branding {{ display: flex; align-items: center; }}
.nq-logo {{
    background: linear-gradient(135deg, #0055A0 0%, #00BFBF 100%);
    color: white; padding: 10px 18px; border-radius: 10px; 
    font-weight: 800; font-size: 1.5rem; margin-right: 15px; letter-spacing: -1px;
}}
.nq-title-group {{ display: flex; flex-direction: column; }}
.nq-title-country {{ color: #64748B; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; }}
.nq-dashboard {{ color: {nq_main_color}; font-weight: 800; font-size: 1.25rem; }}
.tax-bar {{ background-color: {gray_bg}; padding: 16px 20px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #E2E8F0; }}
</style>
"""

st.markdown(css_template, unsafe_allow_html=True)

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
    with col_l2:
        st.markdown("<div style='text-align:center; margin-top:100px;'><span class='nq-logo'>NQ</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center; padding: 20px 0;'><h2 style='color: {nq_main_color}; font-weight:900;'>NQ INTELLIGENCE LOGIN</h2></div>", unsafe_allow_html=True)
        clave_input = st.text_input("Ingresa Clave Operador", type="password", placeholder="Access Key")
        if st.button("DESBLOQUEAR SISTEMA", use_container_width=True):
            if clave_input == CLAVE_CORRECTA:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Clave incorrecta")
    st.stop()

# --- SIDEBAR OAUTH ---
st.sidebar.title("🔗 Mercado Libre OAuth")

if HAS_MELI_AUTH:
    query_params = st.query_params
    if "code" in query_params:
        auth_code = query_params["code"]
        st.sidebar.info("Procesando autorización...")
        try:
            tokens = meli_auth.intercambiar_code_por_tokens(auth_code)
            st.session_state["access_token"] = tokens.get("access_token")
            st.session_state["user_id"] = tokens.get("user_id")
            st.sidebar.success(f"✅ Conectado! User ID: {tokens.get('user_id')}")
            st.query_params.clear()
        except Exception as e:
            st.sidebar.error(f"Error de vinculación: {str(e)}")
    else:
        if "access_token" in st.session_state:
            st.sidebar.success(f"🟢 Sesión Activa (User ID: {st.session_state.get('user_id')})")
        else:
            try:
                url_login = meli_auth.obtener_link_autorizacion()
                st.sidebar.markdown(f'<a href="{url_login}" target="_blank"><button style="background-color:#0055A0; color:white; border:none; padding:10px 15px; border-radius:8px; cursor:pointer; font-weight:bold; width:100%;">🔑 Conectar cuenta de MeLi</button></a>', unsafe_allow_html=True)
            except Exception:
                st.sidebar.warning("⚠️ Error al cargar OAuth.")

st.markdown(f"""
    <div class="nq-header-container">
        <div class="nq-branding">
            <span class="nq-logo">NQ</span>
            <div class="nq-title-group">
                <div class="nq-title-country">NQ Argentina</div>
                <div class="nq-dashboard">NQ | Sales Intelligence Matrix v{V_NUMBER}</div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# CONTROL FISCAL GLOBAL
with st.container():
    st.markdown("<div class='tax-bar'>", unsafe_allow_html=True)
    c_tax1, c_tax2, c_tax3, c_tax4 = st.columns([1.5, 1, 1, 1])
    with c_tax1:
        tipo_iva = st.radio("Configuración Impositiva", ["Responsable Inscripto", "Monotributista"], horizontal=True)
    with c_tax2:
        reputacion_sel = st.selectbox("Reputación Vendedor", list(REPUTACION_DESCUENTOS.keys()), index=0)
    with c_tax3:
        iibb_perc = st.number_input("% Ingresos Brutos (IIBB)", value=3.5, step=0.1)
    with c_tax4:
        comision_vender_input = st.number_input("% Cargo Vender MeLi (Base)", value=14.50, step=0.05)
    st.markdown("</div>", unsafe_allow_html=True)

desc_rep_factor = REPUTACION_DESCUENTOS[reputacion_sel]

# =========================================================
# 4. PESTAÑAS OPERATIVAS CON CONTROL CENTER ACTIVO
# =========================================================
tab0, tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🏠 CONTROL CENTER",
    "📊 REALIDAD REAL",
    "☝️ PVP RECOMENDADO",
    "🎯 COSTO OBJETIVO",
    "🕵️ COMPETIDOR",
    "📁 PROCESAMIENTO MASIVO",
    "🏆 LISTA CENTRO ESTANT (GOLD)",
    "🎯 MONITOR DE CATÁLOGO & BUY BOX",
])

# --- SOLAPA 0: CONTROL CENTER ---
with tab0:
    st.subheader("🏠 Control Center Gerencial & Análisis Macro")

    if not df_articulos_base.empty and "COSTO_LISTA_GOLD" in df_articulos_base.columns:
        tot_skus = len(df_articulos_base)
        costo_prom = df_articulos_base["COSTO_LISTA_GOLD"].mean()
        costo_min = df_articulos_base["COSTO_LISTA_GOLD"].min()
        costo_max = df_articulos_base["COSTO_LISTA_GOLD"].max()

        st.success(f"🟢 **Matriz Activa:** {origen_lista} | **{tot_skus} Productos Cargados**")

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("📦 SKUs en Lista Gold", f"{tot_skus} Productos")
        k2.metric("💵 Costo Lista Promedio", f"${costo_prom:,.2f}")
        k3.metric("📉 Costo Mínimo de Lista", f"${costo_min:,.2f}")
        k4.metric("📈 Costo Máximo de Lista", f"${costo_max:,.2f}")

        st.markdown("---")
        st.markdown("### 🔍 Selector Rápido de Producto para Inspección")

        opciones_art = []
        for idx, row in df_articulos_base.iterrows():
            ean_str = str(row.get("EAN", ""))
            art_str = str(row.get("ARTICULO", ""))
            desc_str = str(row.get("DESCRIPCION", ""))
            precio_val = float(row.get("COSTO_LISTA_GOLD", 0.0))
            opciones_art.append(f"{art_str} | {desc_str} | EAN: {ean_str} | Costo: ${precio_val:,.2f}")

        prod_sel = st.selectbox("Seleccionar Producto del Catálogo Gold:", opciones_art)

        st.markdown("---")
        st.markdown("### 📊 Vista Completa de la Matriz Cargada")
        st.dataframe(df_articulos_base, use_container_width=True)

    else:
        st.warning("⚠️ No se pudo cargar automáticamente la base. Utilice el cargador manual en la barra lateral izquierda (Sidebar).")

# --- SOLAPA 1: REALIDAD REAL ---
with tab1:
    st.subheader("📊 Análisis de Realidad Real por Unidad")
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        pvp_in = st.number_input("PVP Publicado ($)", value=106815.0, step=1000.0, key="pvp_r1")
        costo_in = st.number_input("Costo Producto ($)", value=48198.0, step=1000.0, key="costo_r1")
        finan_sel = st.selectbox("Financiación Ofrecida", list(FINANCIACION_PRESETS.keys()), index=0, key="finan_r1")
        rango_peso_r1 = st.selectbox("Categoría de Peso (Logística ME2)", list(TABLA_ME2_BASE.keys()), index=13, key="peso_r1")

    with col_r2:
        tasa_finan = FINANCIACION_PRESETS[finan_sel]
        comi_val = pvp_in * ((comision_vender_input + tasa_finan) / 100)
        flete_val = TABLA_ME2_BASE[rango_peso_r1][1] * desc_rep_factor
        fijo_val = CARGO_FIJO_MELI if pvp_in < UMBRAL_ENVIO_GRATIS else 0.0
        iibb_val = (pvp_in / 1.21) * (iibb_perc / 100)

        ganancia_limpia = (pvp_in / 1.21) - costo_in - (comi_val / 1.21) - (flete_val / 1.21) - (fijo_val / 1.21) - iibb_val
        margen_pct = (ganancia_limpia / pvp_in) * 100

        st.metric("Ganancia Limpia Neta ($)", f"${ganancia_limpia:,.2f}")
        st.metric("Margen Neto sobre PVP (%)", f"{margen_pct:.2f}%")

# --- SOLAPA 2: PVP RECOMENDADO ---
with tab2:
    st.subheader("☝️ Cálculo de PVP Recomendado de Venta")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        costo_base = st.number_input("Costo de Compra ($)", value=50000.0, key="c_pvp")
        finan_p2 = st.selectbox("Programa de Cuotas / Financiación", list(FINANCIACION_PRESETS.keys()), index=0, key="fin_p2")
        margen_deseado = st.number_input("% Margen Objetivo Deseado", value=15.0, key="m_pvp") / 100
        rango_peso_r2 = st.selectbox("Categoría de Peso ME2", list(TABLA_ME2_BASE.keys()), index=13, key="peso_r2")

    with col_p2:
        tasa_f2 = FINANCIACION_PRESETS[finan_p2]
        comi_tot_p2 = comision_vender_input + tasa_f2
        flete_r2 = TABLA_ME2_BASE[rango_peso_r2][1] * desc_rep_factor
        pvp_calc = (costo_base + (flete_r2 / 1.21)) / (1 - (comi_tot_p2 / 100) - (iibb_perc / 100) - margen_deseado)
        st.success(f"💰 PVP Sugerido de Venta Recomendado: **${max(0.0, pvp_calc):,.2f}**")

# --- SOLAPA 3: COSTO OBJETIVO ---
with tab3:
    st.subheader("🎯 Costo Máximo Objetivo de Compra")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        pvp_target = st.number_input("PVP Objetivo de Mercado ($)", value=106000.0, key="p_target")
        finan_c3 = st.selectbox("Financiación Publicación", list(FINANCIACION_PRESETS.keys()), index=0, key="fin_c3")
        m_target_c3 = st.number_input("% Margen Objetivo Target", value=10.0, key="m_c3") / 100
        rango_peso_r3 = st.selectbox("Categoría de Peso ME2", list(TABLA_ME2_BASE.keys()), index=13, key="peso_r3")

    with col_c2:
        tasa_f3 = FINANCIACION_PRESETS[finan_c3]
        comi_tot_c3 = comision_vender_input + tasa_f3
        flete_r3 = TABLA_ME2_BASE[rango_peso_r3][1] * desc_rep_factor
        costo_max = (pvp_target / 1.21) - (pvp_target * (comi_tot_c3 / 100) / 1.21) - (flete_r3 / 1.21) - (pvp_target * m_target_c3)
        st.info(f"📦 Costo Máximo de Compra Permitido al Proveedor: **${max(0.0, costo_max):,.2f}**")

# --- SOLAPA 4: COMPETIDOR ---
with tab4:
    st.subheader("🕵️ Análisis y Estimación de Competencia")
    col_comp1, col_comp2 = st.columns(2)
    with col_comp1:
        pvp_comp = st.number_input("PVP Publicado por Competidor ($)", value=105000.0, key="pvp_comp")
        finan_comp = st.selectbox("Financiación Competidor", list(FINANCIACION_PRESETS.keys()), index=0, key="fin_comp")
    with col_comp2:
        rango_peso_r4 = st.selectbox("Peso Estimado del Producto", list(TABLA_ME2_BASE.keys()), index=13, key="peso_r4")
        tasa_fc = FINANCIACION_PRESETS[finan_comp]
        flete_r4 = TABLA_ME2_BASE[rango_peso_r4][1] * desc_rep_factor
        comi_comp = pvp_comp * ((comision_vender_input + tasa_fc) / 100)
        ingreso_neto_est = (pvp_comp / 1.21) - (comi_comp / 1.21) - (flete_r4 / 1.21) - ((pvp_comp / 1.21) * (iibb_perc / 100))
        st.write(f"Caja Limpia Estimada que recibe el Competidor: **${ingreso_neto_est:,.2f}**")

# --- SOLAPA 5: PROCESAMIENTO MASIVO ---
with tab5:
    st.subheader("📁 Auditoría y Procesamiento Masivo en Lote")
    up = st.file_uploader("Subir Archivo de Catálogo (Excel / CSV)", type=["xlsx", "csv"])
    if up:
        df_up = pd.read_excel(up) if up.name.endswith(".xlsx") else pd.read_csv(up)
        st.write("Vista previa cargada:", df_up.head(5))

# --- SOLAPA 6: LISTA CENTRO ESTANT ---
with tab6:
    st.subheader("🏆 Lista Oficial Centro Estant — LISTA GOLD SEPTIEMBRE 2026")
    if not df_articulos_base.empty:
        st.success(f"✅ Se cargaron exitosamente **{len(df_articulos_base)} artículos** ({origen_lista}).")
        st.dataframe(df_articulos_base, use_container_width=True)
    else:
        st.info("No se encontró la matriz local.")

# --- SOLAPA 7: MONITOR BUY BOX (CON DETECCIÓN DE FINANCIACIÓN / CUOTAS) ---
with tab7:
    st.subheader("🎯 Monitor de Catálogo, Buy Box & Suite de Inteligencia Comercial")
    st.markdown("Auditoría en tiempo real cruzada con la **Lista Gold Septiembre 2026**, calculando la **Bonificación Real a Proveedor**, **Cuotas Financieras** y el **PVP Break-Even**.")

    col_s1, col_s2, col_s3, col_s4 = st.columns([2.5, 1, 1, 1.2])

    if not df_articulos_base.empty:
        dict_opciones = {}
        for idx, row in df_articulos_base.iterrows():
            ean_s = str(row.get("EAN", "")).strip()
            art_s = str(row.get("ARTICULO", "")).strip()
            desc_s = str(row.get("DESCRIPCION", "")).strip()
            p_val = float(row.get("COSTO_LISTA_GOLD", 0.0))
            
            label_opcion = f"EAN: {ean_s} | Modelo: {art_s} | {desc_s} | Costo: ${p_val:,.2f}"
            dict_opciones[label_opcion] = {
                "ean": ean_s,
                "costo": p_val
            }

        lista_opciones_combo = list(dict_opciones.keys())
        lista_opciones_combo.append("✏️ Ingresar EAN / SKU / URL Manualmente...")

        with col_s1:
            prod_seleccionado_label = st.selectbox("📋 Seleccionar Producto de la Matriz Gold:", lista_opciones_combo, key="combo_ean_tab7")

        if prod_seleccionado_label == "✏️ Ingresar EAN / SKU / URL Manualmente...":
            query_sku = st.text_input("Ingresar EAN, SKU o Enlace MeLi Manual", value="7798009182461", key="input_sku_manual_tab7")
            costo_auto_gold = buscar_costo_lista_gold(query_sku)
        else:
            item_data = dict_opciones[prod_seleccionado_label]
            query_sku = item_data["ean"]
            costo_auto_gold = item_data["costo"]

        with col_s2:
            costo_lista_f = st.number_input(
                "Costo Lista Gold Proveedor ($)",
                value=costo_auto_gold,
                step=1000.0,
                key=f"costo_f_{query_sku}"
            )
        with col_s3:
            finan_tab7_sel = st.selectbox(
                "💳 Financiación / Cuotas",
                list(FINANCIACION_PRESETS.keys()),
                index=0,
                key=f"finan_tab7_{query_sku}"
            )
        with col_s4:
            margen_objetivo_tab7 = st.number_input("% Margen Objetivo Target", value=10.0, step=0.5, key="m_target_tab7") / 100

    else:
        with col_s1:
            query_sku = st.text_input("SKU / EAN / URL", value="7798009182461", key="input_sku_tab7_fallback")
        costo_auto_gold = buscar_costo_lista_gold(query_sku)
        with col_s2:
            costo_lista_f = st.number_input("Costo Lista Gold Proveedor ($)", value=costo_auto_gold, step=1000.0, key="costo_f_tab7_fb")
        with col_s3:
            finan_tab7_sel = st.selectbox("💳 Financiación", list(FINANCIACION_PRESETS.keys()), index=0, key="finan_fb")
        with col_s4:
            margen_objetivo_tab7 = st.number_input("% Margen Target", value=10.0, step=0.5, key="m_target_fb") / 100

    tasa_finan_tab7 = FINANCIACION_PRESETS[finan_tab7_sel]

    if st.button("🚀 AUDITAR CATÁLOGO Y COMPETENCIA", use_container_width=True, key="btn_audit_tab7"):
        token = st.session_state.get("access_token")

        with st.spinner("Consultando Mercado Libre API en vivo y analizando comisiones/cuotas..."):
            items_competencia, metodo_hallado = buscar_items_api_oficial(query_sku, limit=10, access_token=token)

            if items_competencia:
                first_item = items_competencia[0]
                item_id_first = str(first_item.get("id", first_item.get("item_id", ""))).replace("MLA", "").strip()

                pvp_ganador = float(first_item.get("price") or first_item.get("buy_box_winner", {}).get("price") or 0.0)
                title_product = first_item.get("title") or first_item.get("name") or "Producto Mercado Libre"

                # Detección automática de cuotas sin interés si no se forzó en el selector
                lbl_finan_auto, pct_finan_auto = detectar_financiacion_item(first_item)
                tasa_finan_efectiva = tasa_finan_tab7 if tasa_finan_tab7 > 0 else pct_finan_auto

                sold_total = extraer_ventas_de_objeto(first_item, access_token=token)
                flete_std = obtener_flete_real_api(item_id_first, desc_factor=desc_rep_factor, access_token=token)
                fijo_std = CARGO_FIJO_MELI if pvp_ganador < UMBRAL_ENVIO_GRATIS else 0.0

                pvp_objetivo = pvp_ganador - 100.0
                
                # Comisión total incluyendo cargo de venta + recargo de financiación de cuotas
                comision_porcentaje_total = comision_vender_input + tasa_finan_efectiva
                comi_std = pvp_objetivo * (comision_porcentaje_total / 100)
                
                pvp_neto_std = pvp_objetivo / 1.21
                iibb_std = pvp_neto_std * (iibb_perc / 100)
                ganancia_target_std = pvp_objetivo * margen_objetivo_tab7

                costo_max_compra = pvp_neto_std - (comi_std / 1.21) - (flete_std / 1.21) - (fijo_std / 1.21) - iibb_std - ganancia_target_std
                bonif_requerida = ((1 - (costo_max_compra / costo_lista_f)) * 100) if costo_lista_f > 0 else 0.0

                denom = 1 - (comision_porcentaje_total / 100) - ((iibb_perc / 100) / 1.21)
                pvp_breakeven = (costo_lista_f + (flete_std / 1.21) + (fijo_std / 1.21)) / denom if denom > 0 else 0.0

                flete_flex_neto = max(0.0, flete_std - TARIFA_FLEX_AMBA)
                ganancia_extra_flex = (flete_std - flete_flex_neto) / 1.21

                st.caption(f"🔎 **Origen:** {metodo_hallado} | 🟢 **Flete ME2 Neto Vendedor:** ${flete_std:,.2f} | 💳 **Cargo Financiación:** {tasa_finan_efectiva:.2f}%")

                col_c1, col_c2, col_c3 = st.columns(3)

                with col_c1:
                    if bonif_requerida <= 25.0:
                        st.markdown(f'<div style="background-color: #D4EDDA; border: 2px solid #28A745; padding: 15px; border-radius: 10px; text-align: center;"><h3 style="color: #155724; margin:0;">🟢 LUZ VERDE</h3><p style="color: #155724; margin:5px 0 0 0;">Bonificación Real: <b>{bonif_requerida:.2f}%</b></p></div>', unsafe_allow_html=True)
                    elif bonif_requerida <= 40.0:
                        st.markdown(f'<div style="background-color: #FFF3CD; border: 2px solid #FFC107; padding: 15px; border-radius: 10px; text-align: center;"><h3 style="color: #856404; margin:0;">🟡 LUZ AMARILLA</h3><p style="color: #856404; margin:5px 0 0 0;">Bonificación Real: <b>{bonif_requerida:.2f}%</b></p></div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div style="background-color: #F8D7DA; border: 2px solid #DC3545; padding: 15px; border-radius: 10px; text-align: center;"><h3 style="color: #721C24; margin:0;">🔴 LUZ ROJA</h3><p style="color: #721C24; margin:5px 0 0 0;">Bonificación Real: <b>{bonif_requerida:.2f}%</b></p></div>', unsafe_allow_html=True)

                with col_c2:
                    st.markdown(f'<div style="background-color: #E2E8F0; border: 2px solid #64748B; padding: 15px; border-radius: 10px; text-align: center;"><h3 style="color: #1E293B; margin:0;">🛡️ PVP BREAK-EVEN</h3><p style="font-size: 1.2rem; font-weight: 800; color: #1E293B; margin: 5px 0;">${pvp_breakeven:,.2f}</p></div>', unsafe_allow_html=True)

                with col_c3:
                    txt_ventas = f"{sold_total:,} un" if sold_total is not None else "Privado por MeLi"
                    st.markdown(f'<div style="background-color: #D1ECF1; border: 2px solid #17A2B8; padding: 15px; border-radius: 10px; text-align: center;"><h3 style="color: #0C5460; margin:0;">📈 VENTAS ACUMULADAS</h3><p style="font-size: 1.2rem; font-weight: 800; color: #0C5460; margin: 5px 0;">{txt_ventas}</p></div>', unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("🏆 PVP Ganador Actual", f"${pvp_ganador:,.2f}")
                m2.metric("🎯 PVP Objetivo (N.º 1)", f"${pvp_objetivo:,.2f}")
                m3.metric("📦 Costo Máx Compra Target", f"${max(0.0, costo_max_compra):,.2f}")
                m4.metric("📉 Bonificación Real a Pedir", f"{bonif_requerida:.2f}%")

                st.markdown("---")
                st.markdown("### 💸 Desglose Estructural de Gastos del Vendedor para Ganar la Buy Box")

                desglose_df = pd.DataFrame({
                    "Concepto / Gasto": [
                        "PVP Recomendado (Objetivo #1)",
                        f"(-) Cargo de Venta MeLi Base ({comision_vender_input:.2f}%)",
                        f"(-) Recargo por Financiación de Cuotas ({tasa_finan_efectiva:.2f}%)",
                        "(-) Flete Logística Mercado Envíos 2 (Neto Vendedor)",
                        "(-) Cargo Fijo por Unidad",
                        "(-) Retención / Impuesto IIBB",
                        "(-) Margen Neto Ganancia Objetivo",
                        "(=) COSTO MÁXIMO DE COMPRA PERMITIDO (Neto)"
                    ],
                    "Monto ($)": [
                        f"${pvp_objetivo:,.2f}",
                        f"-${pvp_objetivo * (comision_vender_input / 100):,.2f}",
                        f"-${pvp_objetivo * (tasa_finan_efectiva / 100):,.2f}",
                        f"-${flete_std:,.2f}",
                        f"-${fijo_std:,.2f}",
                        f"-${iibb_std:,.2f}",
                        f"-${ganancia_target_std:,.2f}",
                        f"${max(0.0, costo_max_compra):,.2f}"
                    ]
                })
                st.table(desglose_df)

                st.markdown("---")
                st.markdown(f"### 📋 Publicaciones Detectadas para: **{title_product}**")

                tabla_comp = []
                for rank, it in enumerate(items_competencia, start=1):
                    raw_id = str(it.get("id", it.get("item_id", "")))
                    clean_id = raw_id.replace("MLA", "").strip()

                    link_real = it.get("permalink") or (f"https://articulo.mercadolibre.com.ar/MLA-{clean_id}" if clean_id else "#")

                    title = it.get("title") or it.get("name") or title_product
                    price = float(it.get("price", 0.0))
                    seller_id = str(it.get("seller_id", "Sin ID"))
                    seller_nickname = obtener_nickname_vendedor(seller_id, access_token=token)

                    lbl_f, _ = detectar_financiacion_item(it)

                    tabla_comp.append({
                        "Posición": "🥇 Ganador Buy Box" if rank == 1 else f"Puesto #{rank}",
                        "ID Publicación": clean_id if clean_id else "Catálogo",
                        "Título": title,
                        "PVP ($)": f"${price:,.2f}",
                        "Financiación / Tipo": lbl_f,
                        "Vendedor ID": seller_id,
                        "Nombre Vendedor": seller_nickname,
                        "Enlace": link_real,
                    })

                df_tabla = pd.DataFrame(tabla_comp)
                st.dataframe(
                    df_tabla,
                    column_config={
                        "Enlace": st.column_config.LinkColumn(
                            "Enlace Publicación", display_text="Ver en Mercado Libre"
                        )
                    },
                    use_container_width=True,
                )

                st.markdown("---")
                st.markdown("### 📄 Generador de Reporte Gerencial Imprimible")

                reporte_html = f"""
                <div style="padding: 25px; border: 2px solid #2B3E4F; border-radius: 12px; font-family: sans-serif; background-color: #FFFFFF;">
                    <h2 style="color: #0055A0; margin-bottom: 5px;">NQ Sales Intelligence — Reporte Ejecutivo</h2>
                    <p style="color: #64748B; font-size: 0.85rem;">Fecha de Emisión: 16/10/2026 | Sistema NQ Matrix v{V_NUMBER}</p>
                    <hr>
                    <h3>Producto Auditado: {title_product}</h3>
                    <p><b>EAN / SKU:</b> {query_sku}</p>
                    <p><b>PVP Ganador Actual en Mercado Libre:</b> ${pvp_ganador:,.2f}</p>
                    <p><b>PVP Objetivo Comercial (Puesto #1):</b> ${pvp_objetivo:,.2f}</p>
                    <p><b>PVP Break-Even (Piso Mínimo sin Pérdida):</b> ${pvp_breakeven:,.2f}</p>
                    <p><b>Recargo por Financiación Aplicado:</b> {tasa_finan_efectiva:.2f}%</p>
                    <p><b>Ventas Acumuladas Registradas:</b> {txt_ventas}</p>
                    <br>
                    <h4>Estructura de Margen y Compra Sugerida (Lista Gold Septiembre 2026):</h4>
                    <ul>
                        <li><b>Costo Lista Gold Proveedor:</b> ${costo_lista_f:,.2f}</li>
                        <li><b>Costo Máximo de Compra Target:</b> ${max(0.0, costo_max_compra):,.2f}</li>
                        <li><b>Bonificación Real Requerida a Proveedor:</b> {bonif_requerida:.2f}%</li>
                        <li><b>Ahorro Adicional por Envío Flex:</b> ${ganancia_extra_flex:,.2f} / un</li>
                    </ul>
                </div>
                """
                st.markdown(reporte_html, unsafe_allow_html=True)
                st.download_button(
                    "🖨️ Descargar Reporte Gerencial Imprimible (.html)",
                    data=reporte_html,
                    file_name=f"NQ_Reporte_{query_sku}.html",
                    mime="text/html",
                    use_container_width=True
                )

            else:
                st.error("⚠️ No se encontraron publicaciones activas para ese SKU o EAN.")
