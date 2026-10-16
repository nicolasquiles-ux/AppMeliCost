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

V_NUMBER = "36.0"

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title=f"NQ | Sales Intelligence Matrix v{V_NUMBER}", layout="wide"
)

HEADERS_MELI = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

# =========================================================
# 1. CARGA LOCAL Y TABLA DE FLETES BASE (v29)
# =========================================================
@st.cache_data(ttl=3600)
def cargar_base_articulos():
    """Carga y normaliza la matriz local de productos Centro Estant."""
    try:
        df = pd.read_excel("Matriz Articulos Gemini.xlsm", sheet_name=0)
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


df_articulos_base = cargar_base_articulos()

# TABLA MAESTRA ME2 (Tarifas con Descuento MercadoLíder 50% v29)
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


def obtener_flete_real_api(
    item_id, desc_factor=0.50, access_token=None, zip_code="1414"
):
    """Consulta la API de ME2 y aplica el descuento comercial del vendedor."""
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


# =========================================================
# 2. MOTOR BÚSQUEDA MULTI-NIVEL EN CASCADA
# =========================================================
def buscar_items_api_oficial(query_term, limit=10, access_token=None):
    headers = get_headers(access_token)
    term_clean = str(query_term).strip().split(".")[0]

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
                    f'<a href="{url_login}" target="_blank"><button'
                    ' style="background-color:#0055A0; color:white;'
                    " border:none; padding:10px 15px; border-radius:8px;"
                    ' cursor:pointer; font-weight:bold; width:100%;">🔑 Conectar'
                    " cuenta de MeLi</button></a>",
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

# CONTROL FISCAL GLOBAL (v29)
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

desc_rep_factor = REPUTACION_DESCUENTOS[reputacion_sel]

# =========================================================
# 4. SOLAPAS OPERATIVAS V29 + MONITOR API V33
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

# --- SOLAPA 1: REALIDAD REAL ---
with tab1:
    st.subheader("📊 Análisis de Realidad Real por Unidad")
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        pvp_in = st.number_input(
            "PVP Publicado ($)", value=106815.0, step=1000.0, key="pvp_r1"
        )
        costo_in = st.number_input(
            "Costo Producto ($)", value=48198.0, step=1000.0, key="costo_r1"
        )
        finan_sel = st.selectbox(
            "Financiación Ofrecida",
            list(FINANCIACION_PRESETS.keys()),
            index=0,
            key="finan_r1",
        )
        rango_peso_r1 = st.selectbox(
            "Categoría de Peso (Logística ME2)",
            list(TABLA_ME2_BASE.keys()),
            index=13,
            key="peso_r1",
        )

    with col_r2:
        tasa_finan = FINANCIACION_PRESETS[finan_sel]
        comi_val = pvp_in * ((comision_vender_input + tasa_finan) / 100)
        flete_val = TABLA_ME2_BASE[rango_peso_r1][1] * desc_rep_factor
        fijo_val = CARGO_FIJO_MELI if pvp_in < UMBRAL_ENVIO_GRATIS else 0.0
        iibb_val = (pvp_in / 1.21) * (iibb_perc / 100)

        ganancia_limpia = (
            (pvp_in / 1.21)
            - costo_in
            - (comi_val / 1.21)
            - (flete_val / 1.21)
            - (fijo_val / 1.21)
            - iibb_val
        )
        margen_pct = (ganancia_limpia / pvp_in) * 100

        st.metric("Ganancia Limpia Neta ($)", f"${ganancia_limpia:,.2f}")
        st.metric("Margen Neto sobre PVP (%)", f"{margen_pct:.2f}%")

# --- SOLAPA 2: PVP RECOMENDADO ---
with tab2:
    st.subheader("☝️ Cálculo de PVP Recomendado de Venta")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        costo_base = st.number_input(
            "Costo de Compra ($)", value=50000.0, key="c_pvp"
        )
        margen_deseado = (
            st.number_input(
                "% Margen Objetivo Deseado", value=15.0, key="m_pvp"
            )
            / 100
        )
        rango_peso_r2 = st.selectbox(
            "Categoría de Peso ME2",
            list(TABLA_ME2_BASE.keys()),
            index=13,
            key="peso_r2",
        )

    with col_p2:
        flete_r2 = TABLA_ME2_BASE[rango_peso_r2][1] * desc_rep_factor
        pvp_calc = (costo_base + (flete_r2 / 1.21)) / (
            1
            - (comision_vender_input / 100)
            - (iibb_perc / 100)
            - margen_deseado
        )
        st.success(
            "💰 PVP Sugerido de Venta Recomendado:"
            f" **${max(0.0, pvp_calc):,.2f}**"
        )

# --- SOLAPA 3: COSTO OBJETIVO ---
with tab3:
    st.subheader("🎯 Costo Máximo Objetivo de Compra")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        pvp_target = st.number_input(
            "PVP Objetivo de Mercado ($)", value=106000.0, key="p_target"
        )
        m_target_c3 = (
            st.number_input("% Margen Objetivo Target", value=10.0, key="m_c3")
            / 100
        )
        rango_peso_r3 = st.selectbox(
            "Categoría de Peso ME2",
            list(TABLA_ME2_BASE.keys()),
            index=13,
            key="peso_r3",
        )

    with col_c2:
        flete_r3 = TABLA_ME2_BASE[rango_peso_r3][1] * desc_rep_factor
        costo_max = (
            (pvp_target / 1.21)
            - (pvp_target * (comision_vender_input / 100) / 1.21)
            - (flete_r3 / 1.21)
            - (pvp_target * m_target_c3)
        )
        st.info(
            "📦 Costo Máximo de Compra Permitido al Proveedor:"
            f" **${max(0.0, costo_max):,.2f}**"
        )

# --- SOLAPA 4: COMPETIDOR ---
with tab4:
    st.subheader("🕵️ Análisis y Estimación de Competencia")
    pvp_comp = st.number_input(
        "PVP Publicado por Competidor ($)", value=105000.0, key="pvp_comp"
    )
    rango_peso_r4 = st.selectbox(
        "Peso Estimado del Producto",
        list(TABLA_ME2_BASE.keys()),
        index=13,
        key="peso_r4",
    )
    flete_r4 = TABLA_ME2_BASE[rango_peso_r4][1] * desc_rep_factor
    comi_comp = pvp_comp * (comision_vender_input / 100)
    ingreso_neto_est = (
        (pvp_comp / 1.21)
        - (comi_comp / 1.21)
        - (flete_r4 / 1.21)
        - ((pvp_comp / 1.21) * (iibb_perc / 100))
    )
    st.write(
        f"Caja Limpia Estimada que recibe el Competidor: **${ingreso_neto_est:,.2f}**"
    )

# --- SOLAPA 5: PROCESAMIENTO MASIVO ---
with tab5:
    st.subheader("📁 Auditoría y Procesamiento Masivo en Lote")
    up = st.file_uploader(
        "Subir Archivo de Catálogo (Excel / CSV)", type=["xlsx", "csv"]
    )
    if up:
        df_up = (
            pd.read_excel(up)
            if up.name.endswith(".xlsx")
            else pd.read_csv(up)
        )
        st.write("Vista previa cargada:", df_up.head(3))

# --- SOLAPA 6: LISTA CENTRO ESTANT ---
with tab6:
    st.subheader("🏆 Lista Oficial de Productos Centro Estant")
    if not df_articulos_base.empty:
        st.dataframe(df_articulos_base, use_container_width=True)
    else:
        st.info(
            "Cargue o verifique la matriz `Matriz Articulos Gemini.xlsm` en el"
            " directorio."
        )

# --- SOLAPA 7: MONITOR BUY BOX & REPORTE EJECUTIVO ---
with tab7:
    st.subheader(
        "🎯 Monitor de Catálogo & Buy Box + Costos Automatizados por API"
    )
    st.markdown(
        "Ingresá un **EAN, SKU o Descripción** para auditar en tiempo real con"
        " fletes y comisiones de la API."
    )

    col_s1, col_s2, col_s3 = st.columns([2.5, 1, 1])
    with col_s1:
        query_sku = st.text_input(
            "SKU / EAN / Descripción",
            value="7798009182461",
            key="input_sku_tab7",
        )
    with col_s2:
        costo_lista_f = st.number_input(
            "Costo Lista Proveedor ($)",
            value=70500.0,
            step=1000.0,
            key="costo_f_tab7",
        )
    with col_s3:
        margen_objetivo_tab7 = (
            st.number_input(
                "% Margen Objetivo", value=10.0, step=0.5, key="m_target_tab7"
            )
            / 100
        )

    if st.button(
        "🚀 AUDITAR CATÁLOGO Y COMPETENCIA",
        use_container_width=True,
        key="btn_audit_tab7",
    ):
        token = st.session_state.get("access_token")

        with st.spinner("Consultando Mercado Libre API en vivo..."):
            items_competencia, metodo_hallado = buscar_items_api_oficial(
                query_sku, limit=10, access_token=token
            )

            if items_competencia:
                first_item = items_competencia[0]
                item_id_first = str(
                    first_item.get("id", first_item.get("item_id", ""))
                ).replace("MLA", "").strip()

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

                # Extrae el flete de la API aplicando el beneficio del vendedor seleccionado en el header
                flete_std = obtener_flete_real_api(
                    item_id_first,
                    desc_factor=desc_rep_factor,
                    access_token=token,
                )
                fijo_std = (
                    CARGO_FIJO_MELI if pvp_ganador < UMBRAL_ENVIO_GRATIS else 0.0
                )

                pvp_objetivo = pvp_ganador - 100.0
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

                st.caption(
                    f"🔎 **Origen de datos:** {metodo_hallado} | 🟢 **Flete ME2"
                    f" Neto Vendedor:** ${flete_std:,.2f}"
                )

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("🏆 PVP Ganador Actual", f"${pvp_ganador:,.2f}")
                m2.metric("🎯 PVP Objetivo (N.º 1)", f"${pvp_objetivo:,.2f}")
                m3.metric(
                    "📦 Costo Máx Compra", f"${max(0.0, costo_max_compra):,.2f}"
                )
                m4.metric("📉 Bonificación a Pedir", f"{bonif_requerida:.2f}%")

                st.markdown("---")
                st.markdown(
                    "### 💸 Desglose Estructural de Gastos del Vendedor para"
                    " Ganar la Buy Box"
                )

                desglose_df = pd.DataFrame({
                    "Concepto / Gasto": [
                        "PVP Recomendado (Objetivo #1)",
                        (
                            "(-) Comisión Mercado Libre Clásica"
                            f" ({comision_vender_input:.2f}%)"
                        ),
                        "(-) Flete Logística Mercado Envíos 2 (API Neto)",
                        "(-) Cargo Fijo por Unidad",
                        "(-) Retención / Impuesto IIBB",
                        "(-) Margen Neto Ganancia Objetivo",
                        "(=) COSTO MÁXIMO DE COMPRA PERMITIDO (Neto)",
                    ],
                    "Monto ($)": [
                        f"${pvp_objetivo:,.2f}",
                        f"-${comi_std:,.2f}",
                        f"-${flete_std:,.2f}",
                        f"-${fijo_std:,.2f}",
                        f"-${iibb_std:,.2f}",
                        f"-${ganancia_target_std:,.2f}",
                        f"${max(0.0, costo_max_compra):,.2f}",
                    ],
                })
                st.table(desglose_df)

                st.markdown("---")
                st.markdown(
                    f"### 📋 Publicaciones Detectadas para: **{title_product}**"
                )

                tabla_comp = []
                for rank, it in enumerate(items_competencia, start=1):
                    raw_id = str(it.get("id", it.get("item_id", "")))
                    clean_id = raw_id.replace("MLA", "").strip()

                    link_real = it.get("permalink") or (
                        f"https://articulo.mercadolibre.com.ar/MLA-{clean_id}"
                        if clean_id
                        else "#"
                    )

                    title = it.get("title") or it.get("name") or title_product
                    price = float(it.get("price", 0.0))
                    seller_id = str(it.get("seller_id", "Sin ID"))
                    seller_nickname = obtener_nickname_vendedor(
                        seller_id, access_token=token
                    )

                    tabla_comp.append({
                        "Posición": (
                            "🥇 Ganador Buy Box" if rank == 1 else f"Puesto #{rank}"
                        ),
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
                            "Enlace Publicación",
                            display_text="Ver en Mercado Libre",
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
                    <br>
                    <h4>Estructura de Margen y Costos Permisibles:</h4>
                    <ul>
                        <li><b>Costo Lista Proveedor:</b> ${costo_lista_f:,.2f}</li>
                        <li><b>Flete Mercado Envíos (API ME2 Neto):</b> ${flete_std:,.2f}</li>
                        <li><b>Comisión Venta MeLi ({comision_vender_input:.2f}%):</b> ${comi_std:,.2f}</li>
                        <li><b>Costo Máximo de Compra Target:</b> ${max(0.0, costo_max_compra):,.2f}</li>
                        <li><b>Bonificación Requerida a Proveedor:</b> {bonif_requerida:.2f}%</li>
                        <li><b>Margen Neto Proyectado:</b> {margen_objetivo_tab7*100:.2f}%</li>
                    </ul>
                </div>
                """
                st.markdown(reporte_html, unsafe_allow_html=True)
                st.download_button(
                    "🖨️ Descargar Reporte Gerencial Imprimible (.html)",
                    data=reporte_html,
                    file_name=f"NQ_Reporte_{query_sku}.html",
                    mime="text/html",
                    use_container_width=True,
                )

            else:
                st.error(
                    "⚠️ No se encontraron publicaciones activas para ese SKU o"
                    " EAN."
                )
