import io
import re
import pandas as pd
import requests
import streamlit as st

# Módulo OAuth local (opcional)
try:
    import meli_auth
    HAS_MELI_AUTH = True
except ImportError:
    HAS_MELI_AUTH = False

# Versión del sistema
V_NUMBER = "30.0"

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title=f"NQ | Sales Intelligence Dashboard v{V_NUMBER}", layout="wide"
)

# --- HEADERS MULTI-BROWSER PARA EVITAR BLOQUEOS Y HTTP 403 ---
HEADERS_BROWSER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-AR,es;q=0.9,en-US;q=0.8,en;q=0.7",
}

HEADERS_API = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

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


def get_headers_api(access_token=None):
    headers = HEADERS_API.copy()
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return headers


# =========================================================
# BUSCADOR HÍBRIDO CON SCRAPING DE RESPALDO ANTE FALLO DE API
# =========================================================
def buscar_competencia_hibrida(query_term, limit=10, access_token=None):
    """
    Intenta primero por API con Token.
    Si falla o no hay Token, recurre a Web Scraping directo de la web pública de Mercado Libre.
    """
    term_clean = str(query_term).strip().split(".")[0]
    headers_api = get_headers_api(access_token)

    # --- ESTRATEGIA 1: API OFICIAL SI HAY TOKEN O RESPUESTA LIBRE ---
    try:
        url_api = f"https://api.mercadolibre.com/sites/MLA/search?q={requests.utils.quote(term_clean)}&limit={limit}"
        res = requests.get(url_api, headers=headers_api, timeout=4)
        if res.status_code == 200:
            results = res.json().get("results", [])
            if results:
                return results, "API Oficial MeLi (Conectado)"
    except Exception:
        pass

    # --- ESTRATEGIA 2: WEB SCRAPING AUTÓNOMO (RESILIENTE A ERRORES 403) ---
    try:
        url_web = f"https://listado.mercadolibre.com.ar/{requests.utils.quote(term_clean)}"
        res_web = requests.get(url_web, headers=HEADERS_BROWSER, timeout=5)

        if res_web.status_code == 200:
            html = res_web.text
            # Extraer títulos y precios con Regex del HTML público
            precios = re.findall(r'class="poly-price__current".*?class="andes-money-amount__fraction">([\d\.]+)', html)
            titulos = re.findall(r'class="poly-component__title".*?>(.*?)</a>', html)

            if not precios:
                precios = re.findall(r'class="andes-money-amount__fraction">([\d\.]+)', html)

            items_scraped = []
            for i in range(min(len(precios), limit)):
                price_clean = float(precios[i].replace(".", ""))
                title_clean = titulos[i] if i < len(titulos) else f"Producto {term_clean}"
                items_scraped.append({
                    "id": f"SCRAP-{i+1}",
                    "title": title_clean,
                    "price": price_clean,
                    "seller_id": "Vendedor Público MeLi",
                    "listing_type_id": "gold_special",
                    "shipping": {"logistic_type": "tradicional"},
                    "permalink": url_web,
                })

            if items_scraped:
                return items_scraped, "Búsqueda Web Pública (Modo Contingencia NQ)"
    except Exception as e:
        pass

    return [], "Sin Resultados"


# =========================================================
# INYECCIÓN DE CSS Y LOGIN SISTEMA
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

# --- SIDEBAR OAUTH Y DIAGNÓSTICO ---
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
                st.sidebar.markdown(f"""
                <a href="{url_login}" target="_blank">
                    <button style="background-color:#0055A0; color:white; border:none; padding:10px 15px; border-radius:8px; cursor:pointer; font-weight:bold; width:100%;">
                        🔑 Conectar cuenta de MeLi
                    </button>
                </a>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.sidebar.warning("⚠️ Módulo OAuth no configurado.")

st.sidebar.markdown("---")
st.sidebar.info("ℹ️ **Modo Autónomo NQ:** Si la app de MeLi rechaza la conexión OAuth, el sistema utiliza extracción web inteligente sin interrumpir tus búsquedas.")

# =========================================================
# ENCABEZADO CORPORATIVO
# =========================================================
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

# =========================================================
# SOLAPAS PRINCIPALES
# =========================================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 REALIDAD REAL",
    "☝️ PVP RECOMENDADO",
    "🎯 COSTO OBJETIVO",
    "🕵️ COMPETIDOR",
    "📁 PROCESAMIENTO MASIVO",
    "🏆 LISTA CENTRO ESTANT",
    "🎯 MONITOR DE CATÁLOGO & BUY BOX",
])

with tab7:
    st.subheader("🎯 Monitor de Catálogo & Ganadores de Buy Box por SKU")
    st.markdown("Ingresá un **EAN, SKU o Título de Producto** para auditar en tiempo real quién gana la **Buy Box** y calcular la bonificación requerida a fábrica.")

    col_s1, col_s2, col_s3 = st.columns([2.5, 1, 1])
    with col_s1:
        query_sku = st.text_input("SKU / EAN / Descripción a Monitorear", value="7798274754660", key="input_sku_tab7")
    with col_s2:
        costo_lista_f = st.number_input("Costo Lista Proveedor ($)", value=70500.0, step=1000.0, key="costo_f_tab7")
    with col_s3:
        margen_objetivo_tab7 = st.number_input("% Margen Objetivo", value=10.0, step=0.5, key="m_target_tab7") / 100

    if st.button("🚀 AUDITAR CATÁLOGO Y COMPETENCIA", use_container_width=True, key="btn_audit_tab7"):
        if query_sku:
            with st.spinner("Consultando precios del mercado en tiempo real..."):
                items_competencia, modo_origen = buscar_competencia_hibrida(
                    query_sku, limit=10, access_token=st.session_state.get("access_token")
                )

                if items_competencia:
                    first_item = items_competencia[0]
                    pvp_ganador = float(first_item.get("price", 0.0))
                    title_product = first_item.get("title", "Producto Mercado Libre")

                    pvp_objetivo = pvp_ganador - 100.0
                    flete_std = TABLA_ME2_BASE["De 20 a 25 kg"][1]
                    fijo_std = CARGO_FIJO_MELI if pvp_objetivo < UMBRAL_ENVIO_GRATIS else 0.0
                    comi_std = pvp_objetivo * 0.145
                    pvp_neto_std = pvp_objetivo / 1.21
                    iibb_std = pvp_neto_std * 0.035
                    ganancia_target_std = pvp_objetivo * margen_objetivo_tab7

                    costo_max_compra = (pvp_neto_std - (comi_std / 1.21) - (flete_std / 1.21) - (fijo_std / 1.21) - iibb_std - ganancia_target_std)
                    bonif_requerida = ((1 - (costo_max_compra / costo_lista_f)) * 100) if costo_lista_f > 0 else 0.0

                    st.success(f"🟢 Datos extraídos vía: **{modo_origen}**")

                    m1, m2, m3, m4 = st.columns(4)
                    with m1:
                        st.metric("🏆 PVP Ganador Actual", f"${pvp_ganador:,.2f}")
                    with m2:
                        st.metric("🎯 PVP Objetivo (N.º 1)", f"${pvp_objetivo:,.2f}")
                    with m3:
                        st.metric("📦 Costo Máx Compra", f"${max(0.0, costo_max_compra):,.2f}")
                    with m4:
                        st.metric("📉 Bonificación a Pedir", f"{bonif_requerida:.2f}%")

                    st.markdown("---")
                    st.markdown(f"### 📋 Publicaciones Competidoras Detectadas para: **{title_product}**")

                    tabla_comp = []
                    for rank, it in enumerate(items_competencia, start=1):
                        p = float(it.get("price", 0.0))
                        is_buybox = "🥇 Ganador Buy Box" if rank == 1 else f"Puesto #{rank}"
                        tabla_comp.append({
                            "Posición": is_buybox,
                            "Título / Publicación": it.get("title"),
                            "PVP Publicado ($)": f"${p:,.2f}",
                            "Origen": modo_origen,
                        })

                    st.dataframe(pd.DataFrame(tabla_comp), use_container_width=True)
                else:
                    st.warning("⚠️ No se encontraron publicaciones activas para ese SKU/EAN o descripción.")
        else:
            st.error("Ingresá un SKU o EAN válido.")
