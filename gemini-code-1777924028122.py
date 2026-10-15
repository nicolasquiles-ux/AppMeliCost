import io
import re
import pandas as pd
import requests
import streamlit as st

# Módulo OAuth local
try:
    import meli_auth
    HAS_MELI_AUTH = True
except ImportError:
    HAS_MELI_AUTH = False

# Versión del sistema
V_NUMBER = "30.1"

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title=f"NQ | Sales Intelligence Dashboard v{V_NUMBER}", layout="wide"
)

# --- HEADERS Y CONFIGURACIÓN BASE ---
HEADERS_BASE = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

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
}

CLAVE_CORRECTA = "NQ_PRO_2026"
UMBRAL_ENVIO_GRATIS = 33000.0
CARGO_FIJO_MELI = 3800.0
nq_main_color = "#2B3E4F"

def get_headers(access_token=None):
    headers = HEADERS_BASE.copy()
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return headers

# =========================================================
# MOTOR DE BÚSQUEDA API MULTI-NIVEL PARA EVITAR ERRORES
# =========================================================
def buscar_items_api_oficial(query_term, limit=10, access_token=None):
    headers = get_headers(access_token)
    term_clean = str(query_term).strip().split(".")[0]

    # Nivel 1: Búsqueda por EAN/GTIN
    if term_clean.isdigit() and len(term_clean) >= 8:
        try:
            url = f"https://api.mercadolibre.com/sites/MLA/search?gtin={term_clean}&limit={limit}"
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                results = res.json().get("results", [])
                if results:
                    return results, "Búsqueda por GTIN / EAN Directo"
        except Exception:
            pass

    # Nivel 2: Búsqueda por Query Libre
    try:
        url = f"https://api.mercadolibre.com/sites/MLA/search?q={requests.utils.quote(term_clean)}&limit={limit}"
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            results = res.json().get("results", [])
            if results:
                return results, "Búsqueda por Palabras Clave"
    except Exception:
        pass

    # Nivel 3: Fallback de búsqueda con Marca Centro Estant
    try:
        url_fb = f"https://api.mercadolibre.com/sites/MLA/search?q={requests.utils.quote('Centro Estant ' + term_clean)}&limit={limit}"
        res = requests.get(url_fb, headers=headers, timeout=5)
        if res.status_code == 200:
            results = res.json().get("results", [])
            if results:
                return results, "Fallback Marca + Modelo"
    except Exception:
        pass

    return [], "Sin Resultados"

# =========================================================
# INTERFAZ Y MONITOR DE CATÁLOGO
# =========================================================
st.markdown(f"""
    <div style="background-color: #FFFFFF; padding: 18px; border-radius: 12px; border: 1px solid #E2E8F0; margin-bottom: 20px;">
        <h2 style="color: {nq_main_color}; margin: 0;">NQ | Sales Intelligence Matrix v{V_NUMBER}</h2>
    </div>
""", unsafe_allow_html=True)

# --- SIDEBAR OAUTH ---
st.sidebar.title("🔑 Mercado Libre OAuth")
if HAS_MELI_AUTH:
    query_params = st.query_params
    if "code" in query_params:
        try:
            tokens = meli_auth.intercambiar_code_por_tokens(query_params["code"])
            st.session_state["access_token"] = tokens.get("access_token")
            st.sidebar.success("✅ Conectado con éxito a MeLi!")
            st.query_params.clear()
        except Exception as e:
            st.sidebar.error(f"Error OAuth: {str(e)}")
    
    if "access_token" in st.session_state:
        st.sidebar.success("🟢 Sesión Activa de API")
    else:
        try:
            url_login = meli_auth.obtener_link_autorizacion()
            st.sidebar.markdown(f'<a href="{url_login}" target="_blank"><button style="background-color:#0055A0; color:white; border:none; padding:10px; border-radius:6px; width:100%; font-weight:bold;">🔑 Conectar Mercado Libre</button></a>', unsafe_allow_html=True)
        except Exception:
            pass

st.subheader("🎯 Monitor de Catálogo & Buy Box en Tiempo Real")

col1, col2, col3 = st.columns([2.5, 1, 1])
with col1:
    query_sku = st.text_input("SKU / EAN / Descripción", value="7798274754660", key="sku_in")
with col2:
    costo_lista = st.number_input("Costo Lista Proveedor ($)", value=70500.0, step=1000.0, key="costo_in")
with col3:
    margen_obj = st.number_input("% Margen Objetivo", value=10.0, step=0.5, key="m_in") / 100

if st.button("🚀 AUDITAR CATÁLOGO Y COMPETENCIA", use_container_width=True):
    token = st.session_state.get("access_token")
    
    if not token:
        st.warning("⚠️ **Recomendación:** Conectá tu cuenta de Mercado Libre en el menú lateral para evitar bloqueos 403 y obtener resultados precisos por API.")

    with st.spinner("Consultando Mercado Libre API..."):
        items, modo = buscar_items_api_oficial(query_sku, limit=10, access_token=token)

        if items:
            winner = items[0]
            pvp_ganador = float(winner.get("price", 0.0))
            title_p = winner.get("title", "Producto MeLi")
            pvp_target = pvp_ganador - 100.0

            flete = TABLA_ME2_BASE["De 20 a 25 kg"][1]
            fijo = CARGO_FIJO_MELI if pvp_target < UMBRAL_ENVIO_GRATIS else 0.0
            comi = pvp_target * 0.145
            pvp_neto = pvp_target / 1.21
            iibb = pvp_neto * 0.035
            ganancia_obj = pvp_target * margen_obj

            costo_max = pvp_neto - (comi / 1.21) - (flete / 1.21) - (fijo / 1.21) - iibb - ganancia_obj
            bonif_req = ((1 - (costo_max / costo_lista)) * 100) if costo_lista > 0 else 0.0

            st.caption(f"🔎 **Origen de los datos:** {modo}")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🏆 PVP Ganador", f"${pvp_ganador:,.2f}")
            m2.metric("🎯 PVP Objetivo", f"${pvp_target:,.2f}")
            m3.metric("📦 Costo Máx Compra", f"${max(0.0, costo_max):,.2f}")
            m4.metric("📉 Bonificación Pedida", f"{bonif_req:.2f}%")

            st.markdown("---")
            st.markdown(f"### Publicaciones para: **{title_p}**")

            tabla = []
            for rank, it in enumerate(items, start=1):
                tabla.append({
                    "Posición": f"Puesto #{rank}" if rank > 1 else "🥇 Ganador Buy Box",
                    "ID": it.get("id"),
                    "Título": it.get("title"),
                    "PVP ($)": f"${float(it.get('price', 0.0)):,.2f}",
                    "Vendedor ID": it.get("seller_id"),
                })
            st.dataframe(pd.DataFrame(tabla), use_container_width=True)
        else:
            st.error("❌ No se encontraron publicaciones activas. Si el EAN es muy nuevo o no está catalogado por Mercado Libre, probá buscando por la descripción del producto (ej: 'Biblioteca 6001 Centro Estant').")
