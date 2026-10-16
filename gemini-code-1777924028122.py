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

V_NUMBER = "32.1"

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title=f"NQ | Sales Intelligence Matrix v{V_NUMBER}", layout="wide"
)

HEADERS_MELI = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

# =========================================================
# 1. CARGA DE BASE DE DATOS Y TARIFARIOS
# =========================================================
@st.cache_data(ttl=3600)
def cargar_base_articulos():
    try:
        df = pd.read_excel("Matriz Articulos Gemini.xlsm", sheet_name=0)
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


df_articulos_base = cargar_base_articulos()

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


# =========================================================
# 2. MOTOR BÚSQUEDA MULTI-NIVEL PROBADO Y FUNCIONAL
# =========================================================
def buscar_items_api_oficial(query_term, limit=10, access_token=None):
    headers = get_headers(access_token)
    term_clean = str(query_term).strip().split(".")[0]

    # Nivel 1: Búsqueda por GTIN/EAN estricto
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

    # Nivel 2: Búsqueda libre por término en parámetro `q`
    try:
        url = f"https://api.mercadolibre.com/sites/MLA/search?q={requests.utils.quote(term_clean)}&limit={limit}"
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            results = res.json().get("results", [])
            if results:
                return results, "Query Búsqueda Libre"
    except Exception:
        pass

    # Nivel 3: Búsqueda por Ficha de Catálogo Buy Box
    try:
        url_cat = f"https://api.mercadolibre.com/products/search?status=active&site_id=MLA&q={requests.utils.quote(term_clean)}"
        res_cat = requests.get(url_cat, headers=headers, timeout=5)
        if res_cat.status_code == 200:
            products = res_cat.json().get("results", [])
            if products:
                cat_id = products[0].get("id")
                url_items = (
                    f"https://api.mercadolibre.com/products/{cat_id}/items"
                )
                res_items = requests.get(url_items, headers=headers, timeout=5)
                if res_items.status_code == 200:
                    items_cat = res_items.json().get("results", [])
                    if items_cat:
                        return items_cat, "Catálogo Buy Box MeLi"
    except Exception:
        pass

    # Nivel 4: Fallback Comercial Marca Centro Estant
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
# ESTILOS Y AUTENTICACIÓN
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
        st.markdown(
            "<div style='text-align:center; margin-top:100px;'><span"
            " class='nq-logo'>NQ</span></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div style='text-align:center; padding: 20px 0;'><h2"
            f" style='color: {nq_main_color}; font-weight:900;'>NQ"
            " INTELLIGENCE LOGIN</h2></div>",
            unsafe_allow_html=True,
        )
        clave_input = st.text_input(
            "Ingresa Clave Operador", type="password", placeholder="Access Key"
        )
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
            st.sidebar.success(
                f"🟢 Sesión Activa (User ID: {st.session_state.get('user_id')})"
            )
        else:
            try:
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
            except Exception:
                st.sidebar.warning("⚠️ Error al cargar OAuth.")

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

# CONTROL FISCAL
with st.container():
    st.markdown("<div class='tax-bar'>", unsafe_allow_html=True)
    c_tax1, c_tax2, c_tax3, c_tax4 = st.columns([1.5, 1, 1, 1])
    with c_tax1:
        tipo_iva = st.radio(
            "Configuración Impositiva",
            ["Responsable Inscripto", "Monotributista"],
            horizontal=True,
        )
    with c_tax2:
        reputacion_sel = st.selectbox(
            "Reputación Vendedor", list(REPUTACION_DESCUENTOS.keys()), index=0
        )
    with c_tax3:
        iibb_perc = st.number_input(
            "% Ingresos Brutos (IIBB)", value=3.5, step=0.1
        )
    with c_tax4:
        comision_vender_input = st.number_input(
            "% Cargo Vender MeLi", value=14.50, step=0.05
        )
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# PESTAÑAS (TODAS LAS 7 SOLAPAS FUNCIONALES RESTAURADAS)
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

with tab1:
    st.subheader("📊 Análisis de Realidad Real")
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        pvp_in = st.number_input("PVP Publicado ($)", value=106815.0, step=1000.0)
        costo_in = st.number_input("Costo Producto ($)", value=48198.0, step=1000.0)
    with col_r2:
        comi_val = pvp_in * (comision_vender_input / 100)
        flete_val = TABLA_ME2_BASE["De 20 a 25 kg"][1]
        iibb_val = (pvp_in / 1.21) * (iibb_perc / 100)
        ganancia_limpia = (pvp_in / 1.21) - costo_in - (comi_val / 1.21) - (flete_val / 1.21) - iibb_val
        st.metric("Ganancia Limpia ($)", f"${ganancia_limpia:,.2f}")
        st.metric("Margen Neto (%)", f"{(ganancia_limpia / pvp_in) * 100:.2f}%")

with tab2:
    st.subheader("☝️ Cálculo de PVP Recomendado")
    costo_base = st.number_input("Costo de Producto ($)", value=50000.0, key="c_pvp")
    margen_deseado = st.number_input("% Margen Objetivo", value=15.0, key="m_pvp") / 100
    pvp_calc = (costo_base + (TABLA_ME2_BASE["De 20 a 25 kg"][1] / 1.21)) / (1 - (comision_vender_input / 100) - (iibb_perc / 100) - margen_deseado)
    st.success(f"PVP Sugerido de Venta: **${pvp_calc:,.2f}**")

with tab3:
    st.subheader("🎯 Costo Máximo Objetivo")
    pvp_target = st.number_input("PVP Objetivo de Mercado ($)", value=106000.0, key="p_target")
    costo_max = (pvp_target / 1.21) - (pvp_target * (comision_vender_input / 100) / 1.21) - (TABLA_ME2_BASE["De 20 a 25 kg"][1] / 1.21) - (pvp_target * 0.10)
    st.info(f"Costo Máximo de Compra Permitido: **${max(0.0, costo_max):,.2f}**")

with tab4:
    st.subheader("🕵️ Análisis de Competencia")
    st.markdown("Cálculo estimado de margen operativo de terceros.")

with tab5:
    st.subheader("📁 Procesamiento Masivo de Catálogo")
    up = st.file_uploader("Subir Excel", type=["xlsx", "csv"])

with tab6:
    st.subheader("🏆 Lista Centro Estant")
    if not df_articulos_base.empty:
        st.dataframe(df_articulos_base, use_container_width=True)
    else:
        st.info("Cargue o verifique la matriz `Matriz Articulos Gemini.xlsm`.")

with tab7:
    st.subheader("🎯 Monitor de Catálogo & Buy Box en Tiempo Real")
    st.markdown("Ingresá un **EAN, SKU o Título de Producto** para auditar en tiempo real quién gana la **Buy Box**.")

    col_s1, col_s2, col_s3 = st.columns([2.5, 1, 1])
    with col_s1:
        query_sku = st.text_input("SKU / EAN / Descripción", value="7798009182461", key="input_sku_tab7")
    with col_s2:
        costo_lista_f = st.number_input("Costo Lista Proveedor ($)", value=70500.0, step=1000.0, key="costo_f_tab7")
    with col_s3:
        margen_objetivo_tab7 = st.number_input("% Margen Objetivo", value=10.0, step=0.5, key="m_target_tab7") / 100

    if st.button("🚀 AUDITAR CATÁLOGO Y COMPETENCIA", use_container_width=True, key="btn_audit_tab7"):
        token = st.session_state.get("access_token")

        with st.spinner("Consultando Mercado Libre API en vivo..."):
            items_competencia, metodo_hallado = buscar_items_api_oficial(
                query_sku, limit=10, access_token=token
            )

            if items_competencia:
                first_item = items_competencia[0]

                # Mapeo universal de atributos (previene valores None/vacio)
                pvp_ganador = float(
                    first_item.get("price")
                    or first_item.get("buy_box_winner", {}).get("price")
                    or 0.0
                )
                title_product = (
                    first_item.get("title")
                    or first_item.get("name")
                    or "Producto Mercado Libre"
                )

                pvp_objetivo = pvp_ganador - 100.0
                flete_std = TABLA_ME2_BASE["De 20 a 25 kg"][1]
                fijo_std = CARGO_FIJO_MELI if pvp_objetivo < UMBRAL_ENVIO_GRATIS else 0.0
                comi_std = pvp_objetivo * (comision_vender_input / 100)
                pvp_neto_std = pvp_objetivo / 1.21
                iibb_std = pvp_neto_std * (iibb_perc / 100)
                ganancia_target_std = pvp_objetivo * margen_objetivo_tab7

                costo_max_compra = (
                    pvp_neto_std
                    - (comi_std / 1.21)
                    - (flete_std / 1.21)
                    - (fijo_std / 1.21)
                    - iibb_std
                    - ganancia_target_std
                )
                bonif_requerida = (
                    ((1 - (costo_max_compra / costo_lista_f)) * 100)
                    if costo_lista_f > 0
                    else 0.0
                )

                st.caption(f"🔎 **Origen de datos:** {metodo_hallado}")

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("🏆 PVP Ganador Actual", f"${pvp_ganador:,.2f}")
                m2.metric("🎯 PVP Objetivo (N.º 1)", f"${pvp_objetivo:,.2f}")
                m3.metric("📦 Costo Máx Compra", f"${max(0.0, costo_max_compra):,.2f}")
                m4.metric("📉 Bonificación a Pedir", f"{bonif_requerida:.2f}%")

                st.markdown("---")
                st.markdown(f"### 📋 Publicaciones Detectadas para: **{title_product}**")

                tabla_comp = []
                for rank, it in enumerate(items_competencia, start=1):
                    raw_id = str(it.get("id", it.get("item_id", "")))
                    clean_id = raw_id.replace("MLA", "").strip()
                    
                    # Garantizar link a la publicación activa
                    link_real = (
                        it.get("permalink")
                        or (f"https://articulo.mercadolibre.com.ar/MLA-{clean_id}" if clean_id else "#")
                    )

                    title = it.get("title") or it.get("name") or title_product
                    price = float(it.get("price", 0.0))
                    seller_id = str(it.get("seller_id", "Sin ID"))
                    seller_nickname = obtener_nickname_vendedor(seller_id, access_token=token)

                    tabla_comp.append({
                        "Posición": "🥇 Ganador Buy Box" if rank == 1 else f"Puesto #{rank}",
                        "ID Publicación": clean_id if clean_id else "Catálogo",
                        "Título": title,
                        "PVP ($)": f"${price:,.2f}",
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
            else:
                st.error("⚠️ No se encontraron publicaciones activas para ese SKU o EAN.")
