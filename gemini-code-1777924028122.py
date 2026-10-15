import io
import re
import pandas as pd
import requests
import streamlit as st

# Módulo OAuth local
import meli_auth

# Versión del sistema
V_NUMBER = "29.6"

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title=f"NQ | Sales Intelligence Dashboard v{V_NUMBER}", layout="wide"
)

# =========================================================
# DATOS MAESTROS VIGENTES SEPTIEMBRE 2026 (NQ Database Oficial)
# =========================================================
TABLA_ME2_BASE = {
    "Hasta 0,3 kg": [7868.0, 5620.0, 6080.0],
    "De 0,3 a 0,5 kg": [8596.0, 6140.0, 6600.0],
    "De 0,5 a 1 kg": [9800.0, 7000.0, 7470.0],
    "De 1 a 1,5 kg": [10122.0, 7230.0, 7720.0],
    "De 1,5 a 2 kg": [10458.0, 7470.0, 7970.0],
    "De 2 a 3 kg": [11550.0, 8250.0, 8710.0],
    "De 3 a 4 kg": [12866.0, 9190.0, 9860.0],
    "De 4 a 5 kg": [14070.0, 10050.0, 10760.0],
    "De 5 a 8 kg": [15512.0, 11080.0, 11830.0],
    "De 8 a 10 kg": [16926.0, 12090.0, 12840.0],
    "De 10 a 13 kg": [18270.0, 13050.0, 13920.0],
    "De 13 a 15 kg": [19684.0, 14060.0, 14930.0],
    "De 15 a 20 kg": [23506.0, 16790.0, 17830.0],
    "De 20 a 25 kg": [28182.0, 20130.0, 21420.0],
    "De 25 a 30 kg": [38780.0, 27700.0, 29410.0],
    "De 30 a 40 kg": [44268.0, 31620.0, 33570.0],
    "De 40 a 50 kg": [46802.0, 33430.0, 35490.0],
    "De 50 a 60 kg": [51996.0, 37140.0, 39610.0],
    "De 60 a 70 kg": [54068.0, 38620.0, 41290.0],
    "De 70 a 80 kg": [62524.0, 44660.0, 47850.0],
    "De 80 a 90 kg": [77308.0, 55220.0, 59180.0],
    "De 90 a 100 kg": [89152.0, 63680.0, 68230.0],
    "De 100 a 120 kg": [97328.0, 69520.0, 74490.0],
    "De 120 a 140 kg": [109592.0, 78280.0, 83890.0],
    "De 140 a 160 kg": [121870.0, 87050.0, 93280.0],
    "De 160 a 180 kg": [134120.0, 95800.0, 102660.0],
    "Más de 180 kg": [146398.0, 104570.0, 112060.0],
}

FINANCIACION_PRESETS = {
    "1 Pago / Clásica (0.00%)": 0.0,
    "2 Cuotas Mismo Precio (9.49%)": 9.49,
    "3 Cuotas Mismo Precio (12.19%)": 12.19,
    "6 Cuotas Mismo Precio (19.09%)": 19.09,
    "9 Cuotas Mismo Precio (27.29%)": 27.29,
    "12 Cuotas Mismo Precio (32.29%)": 32.29,
    "18 Cuotas Mismo Precio (41.59%)": 41.59,
    "Personalizado (Manual)": -1.0,
}

REPUTACION_DESCUENTOS = {
    "Verde / MercadoLíder (50% desc)": 1.0,
    "Amarilla (40% desc)": 1.20,
    "Roja / Sin Reputación (0% desc)": 2.0,
}

CLAVE_CORRECTA = "NQ_PRO_2026"
UMBRAL_ENVIO_GRATIS = 33000.0
CARGO_FIJO_MELI = 3800.0

nq_main_color = "#2B3E4F"
nq_green = "#1E8449"
nq_gold = "#BFA100"
gray_bg = "#F8FAFC"


# =========================================================
# FUNCIONES DE CONSULTA A LA API DE MERCADO LIBRE ENRIQUECIDAS
# =========================================================
def probar_conexion_meli():
    """Verifica el estado de respuesta de los servidores de Mercado Libre."""
    try:
        res = requests.get("https://api.mercadolibre.com/sites/MLA", timeout=4)
        if res.status_code == 200:
            return True, "Conexión MELI establecida (HTTP 200 OK)"
        else:
            return False, f"Respuesta MELI inusual (HTTP {res.status_code})"
    except Exception as e:
        return False, f"Error de conexión con MELI: {str(e)}"


def consultar_api_mercadolibre(link_o_mla, access_token=None):
    match = re.search(r"MLA-?(\d+)", link_o_mla, re.IGNORECASE)
    if not match:
        return None, "Link o ID MLA no válido. Ejemplo: MLA1428593851 o enlace de la publicación."

    item_id = f"MLA{match.group(1)}"
    headers = {"Authorization": f"Bearer {access_token}"} if access_token else {}
    url = f"https://api.mercadolibre.com/items/{item_id}"

    try:
        res = requests.get(url, headers=headers, timeout=6)
        if res.status_code == 200:
            data = res.json()
            pvp = data.get("price", 0.0)
            title = data.get("title", "")
            seller_id = data.get("seller_id")
            catalog_product_id = data.get("catalog_product_id")
            listing_type_id = data.get("listing_type_id", "gold_special")
            shipping = data.get("shipping", {})
            logistic_type = shipping.get("logistic_type", "default")

            winner_info = None
            if catalog_product_id:
                url_cat = f"https://api.mercadolibre.com/products/{catalog_product_id}"
                res_cat = requests.get(url_cat, headers=headers, timeout=4)
                if res_cat.status_code == 200:
                    data_cat = res_cat.json()
                    buy_box = data_cat.get("buy_box_winner", {})
                    if buy_box:
                        winner_info = {
                            "winner_seller_id": buy_box.get("seller_id"),
                            "winner_price": buy_box.get("price"),
                            "winner_item_id": buy_box.get("item_id"),
                        }

            modalidad = "Mercado Envíos Tradicional (ME2)"
            if logistic_type == "fulfillment":
                modalidad = "Mercado Envíos Full"
            elif logistic_type == "self_service":
                modalidad = "Mercado Envíos Flex"

            is_premium = listing_type_id == "gold_pro"

            return {
                "item_id": item_id,
                "title": title,
                "pvp": float(pvp),
                "seller_id": seller_id,
                "catalog_product_id": catalog_product_id,
                "winner_info": winner_info,
                "is_premium": is_premium,
                "modalidad": modalidad,
            }, None
        else:
            return None, f"No se encontró la publicación en Mercado Libre (Código HTTP {res.status_code})."
    except Exception as e:
        return None, f"Error de conexión con la API de MeLi: {str(e)}"


def buscar_pvp_meli_inteligente(ean_code, descripcion, articulo):
    """Paso 1: Busca por EAN. Paso 2: Si no encuentra, realiza fallback por Marca + Descripción."""
    ean_clean = str(ean_code).strip().split(".")[0] if pd.notnull(ean_code) else ""
    if ean_clean and len(ean_clean) >= 8 and ean_clean != "-":
        url_gtin = f"https://api.mercadolibre.com/sites/MLA/search?gtin={ean_clean}"
        try:
            res = requests.get(url_gtin, timeout=4)
            if res.status_code == 200:
                results = res.json().get("results", [])
                if results:
                    return float(results[0].get("price", 0.0)), "GTIN Directo"
        except Exception:
            pass

    query_str = f"Centro Estant {descripcion if pd.notnull(descripcion) else articulo}".strip()
    url_query = f"https://api.mercadolibre.com/sites/MLA/search?q={requests.utils.quote(query_str)}"

    try:
        res = requests.get(url_query, timeout=4)
        if res.status_code == 200:
            results = res.json().get("results", [])
            if results:
                return float(results[0].get("price", 0.0)), "Búsqueda Título"
    except Exception:
        pass

    return None, "No Encontrado"


def buscar_competencia_inteligente_v2(query_term, limit=12):
    """Estrategia de Búsqueda de 4 Niveles para Garantizar Hallazgo de Competencia."""
    term_clean = str(query_term).strip().split(".")[0]

    # Nivel 1: Búsqueda por parámetro oficial GTIN (EAN)
    if term_clean.isdigit() and len(term_clean) >= 8:
        url_gtin = f"https://api.mercadolibre.com/sites/MLA/search?gtin={term_clean}&limit={limit}"
        try:
            res = requests.get(url_gtin, timeout=5)
            if res.status_code == 200:
                results = res.json().get("results", [])
                if results:
                    return results, "GTIN / Código EAN Directo"
        except Exception:
            pass

    # Nivel 2: Búsqueda por query libre numérico o texto
    url_q = f"https://api.mercadolibre.com/sites/MLA/search?q={requests.utils.quote(term_clean)}&limit={limit}"
    try:
        res = requests.get(url_q, timeout=5)
        if res.status_code == 200:
            results = res.json().get("results", [])
            if results:
                return results, "Query Búsqueda Libre"
    except Exception:
        pass

    # Nivel 3: Búsqueda por productos de catálogo
    url_cat = f"https://api.mercadolibre.com/products/search?status=active&site_id=MLA&q={requests.utils.quote(term_clean)}"
    try:
        res = requests.get(url_cat, timeout=5)
        if res.status_code == 200:
            products = res.json().get("results", [])
            if products:
                # Si encontramos el producto de catálogo, buscamos los ítems que compiten en él
                cat_id = products[0].get("id")
                url_items_cat = f"https://api.mercadolibre.com/products/{cat_id}/items"
                res_items = requests.get(url_items_cat, timeout=5)
                if res_items.status_code == 200:
                    items_cat = res_items.json().get("results", [])
                    if items_cat:
                        return items_cat, "Catálogo Buy Box Mercado Libre"
    except Exception:
        pass

    # Nivel 4: Fallback Comercial (Marca + Término)
    query_fallback = f"Centro Estant {term_clean}".strip()
    url_fallback = f"https://api.mercadolibre.com/sites/MLA/search?q={requests.utils.quote(query_fallback)}&limit={limit}"
    try:
        res = requests.get(url_fallback, timeout=5)
        if res.status_code == 200:
            results = res.json().get("results", [])
            if results:
                return results, "Fallback Comercial (Marca + Modelo)"
    except Exception:
        pass

    return [], "No Encontrado"


# =========================================================
# INYECCIÓN DE CSS Y MÓDULO SIDEBAR OAUTH
# =========================================================
css_template = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=400;600;700;800&display=swap');

html, body, [class*="css"] {{ 
    font-family: 'Plus Jakarta Sans', sans-serif; 
    background-color: #FFFFFF; 
}}
.stApp {{ background-color: #FFFFFF; }}

.nq-header-container {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 18px 25px; background-color: #FFFFFF;
    box-shadow: 0 4px 12px rgba(0,0,0,0.03); margin-bottom: 20px;
    border-radius: 14px; border: 1px solid #E2E8F0;
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

.tax-bar {{
    background-color: {gray_bg}; padding: 16px 20px; border-radius: 12px;
    margin-bottom: 20px; border: 1px solid #E2E8F0;
}}

.cost-breakdown-card {{
    background: #FFFFFF; padding: 22px; border-radius: 16px;
    border: 1px solid #E2E8F0; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05);
}}
.cost-card-title {{
    font-size: 1.15rem; font-weight: 800; color: {nq_main_color};
    border-bottom: 2px solid #F1F5F9; padding-bottom: 8px; margin-bottom: 14px;
}}
.section-header-tag {{
    font-size: 0.75rem; font-weight: 800; text-transform: uppercase;
    color: #64748B; background: #F1F5F9; padding: 3px 8px; border-radius: 6px;
    margin-top: 10px; margin-bottom: 4px; display: inline-block;
}}
.cost-item {{ 
    display: flex; justify-content: space-between; align-items: center; font-size: 0.88rem; 
    border-bottom: 1px solid #F8FAFC; padding: 6px 0;
}}
.cost-label {{ color: #334155; font-weight: 600; }}
.cost-label-bold {{ color: #0F172A; font-weight: 800; }}
.cost-value {{ color: #0F172A; font-weight: 700; text-align: right; }}
.cost-value-highlight {{ color: #0055A0; font-weight: 800; text-align: right; font-size: 0.95rem; }}

.banner-card {{
    color: white; padding: 18px; display: flex; flex-direction: column;
    justify-content: center; align-items: center; text-align: center; gap: 2px;
    border-radius: 14px; margin-bottom: 15px;
    box-shadow: 0 8px 16px rgba(0,0,0,0.06);
}}
.bg-pvp {{ background-color: {nq_main_color}; }}
.bg-costo {{ background-color: {nq_gold}; }}
.bg-ganancia {{ background-color: {nq_green}; }}
.bg-loss {{ background-color: #C0392B; }}

.label-banner {{ color: rgba(255,255,255,0.85); font-size: 0.75rem; font-weight: 700; text-transform: uppercase; }}
.price-main {{ color: white; font-size: 1.8rem; font-weight: 800; margin: 2px 0; }}
.badge-banner {{
    background: rgba(255,255,255,0.22); color: white;
    padding: 3px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 700;
}}
</style>
"""

st.markdown(css_template, unsafe_allow_html=True)

# --- LOGIN SITEMA NQ ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
    with col_l2:
        st.markdown(
            "<div style='text-align:center; margin-top:100px;'><span class='nq-logo'>NQ</span></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div style='text-align:center; padding: 20px 0;'><h2 style='color: {nq_main_color}; font-weight:900;'>NQ INTELLIGENCE LOGIN</h2></div>",
            unsafe_allow_html=True,
        )
        clave_input = st.text_input("Ingresa Clave Operador", type="password", placeholder="Access Key")
        if st.button("DESBLOQUEAR SISTEMA", use_container_width=True):
            if clave_input == CLAVE_CORRECTA:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Clave incorrecta")
    st.stop()

# --- SIDEBAR: OAUTH MERCADO LIBRE ---
st.sidebar.title("🔗 Mercado Libre OAuth")
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
        url_login = meli_auth.obtener_link_autorizacion()
        st.sidebar.markdown(
            f"""
            <a href="{url_login}" target="_blank">
                <button style="background-color:#0055A0; color:white; border:none; padding:10px 15px; border-radius:8px; cursor:pointer; font-weight:bold; width:100%;">
                    🔑 Conectar cuenta de MeLi
                </button>
            </a>
            """,
            unsafe_allow_html=True,
        )

# =========================================================
# ENCABEZADO CORPORATIVO
# =========================================================
st.markdown(
    f"""
    <div class="nq-header-container">
        <div class="nq-branding">
            <span class="nq-logo">NQ</span>
            <div class="nq-title-group">
                <div class="nq-title-country">NQ Argentina</div>
                <div class="nq-dashboard">NQ | Sales Intelligence Matrix v{V_NUMBER}</div>
            </div>
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

# --- BARRA DE IMPORTACIÓN DESDE API MELI ---
with st.expander("🔍 **IMPORTAR PUBLICACIÓN DIRECTO DESDE MERCADO LIBRE (LINK O MLA)**", expanded=False):
    c_api1, c_api2 = st.columns([3, 1])
    with c_api1:
        input_meli_link = st.text_input(
            "Pega el Link o ID MLA (Ej: https://articulo.mercadolibre.com.ar/MLA-1428593851... o MLA1428593851)",
            key="input_api_meli",
        )
    with c_api2:
        st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
        btn_importar = st.button("🚀 Cargar de MeLi", use_container_width=True)

    if btn_importar and input_meli_link:
        data_item, error_msg = consultar_api_mercadolibre(
            input_meli_link, access_token=st.session_state.get("access_token")
        )
        if error_msg:
            st.error(f"❌ {error_msg}")
        else:
            st.session_state["fetched_pvp"] = data_item["pvp"]
            st.session_state["fetched_title"] = data_item["title"]
            st.session_state["fetched_modalidad"] = data_item["modalidad"]
            st.session_state["fetched_is_premium"] = data_item["is_premium"]
            st.success(
                f"✅ Cargado: **{data_item['title']}** | PVP: **${data_item['pvp']:,.2f}** | Logística: **{data_item['modalidad']}**"
            )

# =========================================================
# CONTROL FISCAL Y CONFIGURACIÓN GENERAL
# =========================================================
with st.container():
    st.markdown("<div class='tax-bar'>", unsafe_allow_html=True)
    c_tax1, c_tax2, c_tax3, c_tax4, c_tax5, c_tax6 = st.columns([1.5, 1, 1, 1, 1, 1])
    with c_tax1:
        tipo_iva = st.radio("Configuración Impositiva", ["Responsable Inscripto", "Monotributista"], horizontal=True)
    with c_tax2:
        reputacion_sel = st.selectbox("Reputación Vendedor", list(REPUTACION_DESCUENTOS.keys()), index=0)
    with c_tax3:
        iibb_perc = st.number_input("% Ingresos Brutos (IIBB)", value=3.5, step=0.1)
    with c_tax4:
        comision_vender_input = st.number_input("% Cargo Vender MeLi (Clásica)", value=14.50, step=0.05)
    with c_tax5:
        alicuota
