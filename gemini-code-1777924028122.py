import streamlit as st
import pandas as pd
import requests

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="NQ Sales Intelligence Matrix Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { background-color: #f4f6f9; }
    .stMetric { background-color: #ffffff; padding: 18px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .stButton>button { border-radius: 8px; font-weight: 600; }
    .card-viable { background-color: #d4edda; color: #155724; padding: 15px; border-radius: 8px; border: 1px solid #c3e6cb; }
    .card-noviable { background-color: #f8d7da; color: #721c24; padding: 15px; border-radius: 8px; border: 1px solid #f5c6cb; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CREDENCIALES Y OAUTH DE MERCADO LIBRE
# ==========================================
CLIENT_ID = st.secrets.get("MELI_CLIENT_ID", "7265495583900621")
CLIENT_SECRET = st.secrets.get("MELI_CLIENT_SECRET", "")
REDIRECT_URI = st.secrets.get("REDIRECT_URI", "https://melicost.streamlit.app").strip().rstrip("/")

# ==========================================
# 3. ESTADO DE SESIÓN (SESSION STATE)
# ==========================================
if "authenticated_app" not in st.session_state:
    st.session_state["authenticated_app"] = False
if "access_token" not in st.session_state:
    st.session_state["access_token"] = ""
if "user_info" not in st.session_state:
    st.session_state["user_info"] = {}
if "lista_gold_df" not in st.session_state:
    st.session_state["lista_gold_df"] = None

# ==========================================
# 4. FUNCIONES DE CONEXIÓN Y CONSULTA API
# ==========================================
def obtener_url_login_meli():
    return f"https://auth.mercadolibre.com.ar/authorization?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"

def intercambiar_code_por_token(code: str):
    url = "https://api.mercadolibre.com/oauth/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
    try:
        res = requests.post(url, data=payload, headers=headers, timeout=10)
        if res.status_code == 200:
            return True, res.json()
        else:
            err_data = res.json() if res.content else {}
            return False, err_data.get("message", f"Error HTTP {res.status_code}")
    except Exception as e:
        return False, str(e)

def obtener_perfil_meli(token: str):
    if not token:
        return {}
    url = "https://api.mercadolibre.com/users/me"
    headers = {"Authorization": f"Bearer {token.strip()}"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {}

def buscar_competencia_por_ean(ean_code: str, access_token: str = None):
    """
    Búsqueda robusta por EAN/GTIN:
    1. Consulta por product_identifier en catálogo MeLi.
    2. Consulta por búsqueda libre del código de barras.
    3. Extrae las publicaciones competidoras.
    """
    clean_ean = ean_code.strip()
    headers = {"Authorization": f"Bearer {access_token.strip()}"} if access_token else {}
    items = []
    catalog_id = ""
    title_found = ""

    # Paso 1: Intentar buscar ID de catálogo por EAN
    if clean_ean.isdigit():
        url_cat = f"https://api.mercadolibre.com/products/search?status=active&site_id=MLA&product_identifier={clean_ean}"
        try:
            res = requests.get(url_cat, headers=headers, timeout=8)
            if res.status_code == 200:
                results = res.json().get("results", [])
                if results:
                    catalog_id = results[0].get("id", "")
                    title_found = results[0].get("name", "")
        except Exception:
            pass

    # Paso 2: Si existe Catalog ID, traer sus ítems
    if catalog_id:
        url_items = f"https://api.mercadolibre.com/sites/MLA/search?catalog_product_id={catalog_id}"
        try:
            res_items = requests.get(url_items, headers=headers, timeout=8)
            if res_items.status_code == 200:
                items = res_items.json().get("results", [])
        except Exception:
            pass

    # Paso 3: Fallback por búsqueda libre del EAN
    if not items:
        url_search = f"https://api.mercadolibre.com/sites/MLA/search?q={clean_ean}"
        try:
            res_s = requests.get(url_search, headers=headers, timeout=8)
            if res_s.status_code == 200:
                items = res_s.json().get("results", [])
        except Exception:
            pass

    return catalog_id if catalog_id else "N/A", title_found, items

# ==========================================
# 5. CAPTURA Y PROCESAMIENTO OAUTH
# ==========================================
query_params = st.query_params
code_auth = query_params.get("code", None)

if code_auth and not st.session_state["access_token"]:
    with st.spinner("Procesando autenticación con Mercado Libre..."):
        exito, token_resp = intercambiar_code_por_token(code_auth)
        if exito:
            st.session_state["access_token"] = token_resp.get("access_token", "")
            st.session_state["user_info"] = obtener_perfil_meli(st.session_state["access_token"])
            st.session_state["authenticated_app"] = True
            st.query_params.clear()
            st.rerun()

# ==========================================
# 6. LOGIN DE APLICACIÓN LOCAL
# ==========================================
if not st.session_state["authenticated_app"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.title("⚡ NQ Sales Intelligence")
        st.subheader("Acceso al Panel Operativo")
        user = st.text_input("Usuario", value="admin")
        pwd = st.text_input("Contraseña", type="password", value="admin123")
        if st.button("🔑 INICIAR SESIÓN", type="primary", use_container_width=True):
            st.session_state["authenticated_app"] = True
            st.rerun()
    st.stop()

# ==========================================
# 7. BARRA LATERAL (CONTROL & ARCHIVO GOLD)
# ==========================================
with st.sidebar:
    st.title("⚡ Control Panel")
    
    if st.button("🔴 Cerrar Sesión", use_container_width=True):
        st.session_state["authenticated_app"] = False
        st.session_state["access_token"] = ""
        st.session_state["user_info"] = {}
        st.rerun()

    st.markdown("---")
    st.subheader("🔗 Conexión a Mercado Libre")
    
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
        url_auth = obtener_url_login_meli()
        st.link_button("🔗 CONECTAR CON MERCADO LIBRE", url_auth, type="primary", use_container_width=True)

    st.markdown("---")
    st.subheader("📄 Carga de Lista Gold")
    uploaded_gold = st.file_uploader("Subir Archivo de Costos (.xlsx / .csv)", type=["xlsx", "csv"])
    if uploaded_gold is not None:
        try:
            if uploaded_gold.name.endswith('.csv'):
                st.session_state["lista_gold_df"] = pd.read_csv(uploaded_gold)
            else:
                st.session_state["lista_gold_df"] = pd.read_excel(uploaded_gold)
            st.success("✅ Lista Gold vinculada.")
        except Exception as e:
            st.error(f"Error al leer archivo: {e}")

# ==========================================
# 8. PANEL PRINCIPAL Y SOLAPAS
# ==========================================
st.title("NQ Sales Intelligence Matrix Pro")
st.caption("v67.0 — Motor de Análisis de Competencia, Estructura de Costos y Viabilidad de Publicación")

tabs = st.tabs([
    "1. 🏆 Analizador por EAN & Top Vendedores",
    "2. 📋 Matriz Lista Gold & Costos"
])

# ------------------------------------------
# SOLAPA 1: ANALIZADOR DE COMPETENCIA Y MATRIZ DE VIABILIDAD
# ------------------------------------------
with tabs[0]:
    st.header("🔍 Análisis de Mercado y Viabilidad por Código EAN")
    
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        ean_input = st.text_input("Código EAN / GTIN de Producto", value="7798009182461")
    with col_btn:
        st.write("")
        btn_analizar = st.button("🔎 BUSCAR COMPETENCIA", type="primary", use_container_width=True)

    if btn_analizar or ean_input:
        with st.spinner("Consultando publicaciones competidoras en Mercado Libre..."):
            cat_id_res, title_res, items_comp = buscar_competencia_por_ean(ean_input, st.session_state["access_token"])

        if items_comp:
            st.subheader(f"📊 Competidores Encontrados ({len(items_comp)} publicaciones)")
            if title_res:
                st.info(f"📦 **Producto Identificado:** {title_res} | **Catalog ID:** `{cat_id_res}`")

            data_tabla = []
            for item in items_comp[:20]:
                inst = item.get("installments", {})
                q_cuotas = inst.get("quantity", 1) if inst else 1
                
                data_tabla.append({
                    "EAN Buscado": ean_input.strip(),
                    "ID Publicación": item.get("id"),
                    "Vendedor ID": item.get("seller", {}).get("id", "N/A"),
                    "Precio ($ ARS)": item.get("price", 0.0),
                    "Cuotas": f"{q_cuotas} cuotas",
                    "Tipo Listado": item.get("listing_type_id", "gold_pro"),
                    "Stock": item.get("available_quantity", 0),
                    "Título Publicación": item.get("title", ""),
                    "Link Publicación": item.get("permalink")
                })

            df_competencia = pd.DataFrame(data_tabla).sort_values(by="Precio ($ ARS)", ascending=True).reset_index(drop=True)
            
            # Mostrar Tabla de Resultados con EAN, Código, Precio, Cuotas y Link
            st.dataframe(
                df_competencia[["EAN Buscado", "ID Publicación", "Precio ($ ARS)", "Cuotas", "Tipo Listado", "Stock", "Título Publicación", "Link Publicación"]],
                use_container_width=True
            )

            # Datos del Ganador (Buy Box)
            ganador = df_competencia.iloc[0]
            pvp_ganador = float(ganador["Precio ($ ARS)"])
            cuotas_ganador = ganador["Cuotas"]
            link_ganador = ganador["Link Publicación"]
            tipo_listado_ganador = ganador["Tipo Listado"]

            st.markdown("---")
            st.subheader("🧮 Simulación de Costos y Viabilidad para Publicar y Ganar")

            # Intentar matchear con Lista Gold si existe
            costo_lista_gold = 0.0
            if st.session_state["lista_gold_df"] is not None:
                df_g = st.session_state["lista_gold_df"]
                col_ean_g = [c for c in df_g.columns if "ean" in str(c).lower() or "codigo" in str(c).lower() or "gtin" in str(c).lower()]
                col_costo_g = [c for c in df_g.columns if "costo" in str(c).lower() or "precio" in str(c).lower()]
                
                if col_ean_g and col_costo_g:
                    match_gold = df_g[df_g[col_ean_g[0]].astype(str).str.contains(ean_input.strip())]
                    if not match_gold.empty:
                        try:
                            raw_c = match_gold.iloc[0][col_costo_g[0]]
                            costo_lista_gold = float(str(raw_c).replace("$", "").replace(".", "").replace(",", ".").strip())
                        except Exception:
                            pass

            col_c1, col_c2 = st.columns(2)
            with col_c1:
                pvp_objetivo = st.number_input("PVP de Venta Objetivo ($ ARS)", min_value=100.0, value=pvp_ganador, step=500.0)
                pct_comision = st.number_input("Comisión Mercado Libre (%)", min_value=0.0, max_value=50.0, value=28.0 if "pro" in tipo_listado_ganador else 14.0)
                costo_envio = st.number_input("Costo Envío / Logística ($ ARS)", min_value=0.0, value=3500.0, step=100.0)
            
            with col_c2:
                pct_iibb = st.number_input("Impuestos IIBB (%)", min_value=0.0, max_value=10.0, value=3.5)
                pct_iva = st.number_input("IVA / Impuestos Directos (%)", min_value=0.0, max_value=30.0, value=21.0)
                costo_gold_user = st.number_input("Costo Actual en Lista Gold ($ ARS)", min_value=0.0, value=costo_lista_gold if costo_lista_gold > 0 else (pvp_objetivo * 0.45), step=500.0)

            # CALCULO DE DEDUCCIONES
            monto_comision = pvp_objetivo * (pct_comision / 100.0)
            monto_iibb = pvp_objetivo * (pct_iibb / 100.0)
            monto_iva = pvp_objetivo * (pct_iva / 100.0)
            total_deducciones_meli_tax = monto_comision + monto_iibb + monto_iva + costo_envio

            # Costo Máximo Necesario para publicar y tener 15% de margen ganándole al Buy Box
            margen_deseado_pct = 0.15
            costo_maximo_necesario = pvp_objetivo - total_deducciones_meli_tax - (pvp_objetivo * margen_deseado_pct)

            # Cálculo de % de descuento requerido en Lista Gold
            pct_descuento_requerido = 0.0
            if costo_gold_user > costo_maximo_necesario and costo_gold_user > 0:
                pct_descuento_requerido = ((costo_gold_user - costo_maximo_necesario) / costo_gold_user) * 100.0

            ganancia_neta_actual = pvp_objetivo - total_deducciones_meli_tax - costo_gold_user
            margin_neto_pct_actual = (ganancia_neta_actual / pvp_objetivo) * 100.0 if pvp_objetivo > 0 else 0.0

            # METRICAS DESTACADAS EN BOTONES / TARJETAS
            st.markdown("### 📌 Indicadores Clave de Viabilidad Comercial")
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🥇 PVP Ganador Buy Box", f"${pvp_ganador:,.2f}")
            m2.metric("🎯 Costo Máximo Necesario", f"${costo_maximo_necesario:,.2f}")
            m3.metric("📉 % Descuento Necesario en Gold", f"{pct_descuento_requerido:.1f}%" if pct_descuento_requerido > 0 else "0.0% (OK)")
            m4.metric("💰 Margen Neto Actual", f"{margin_neto_pct_actual:.1f}% (${ganancia_neta_actual:,.2f})")

            # TARJETA DE VIABILIDAD CONCRETA
            if ganancia_neta_actual > 0:
                st.markdown(f"""
                <div class="card-viable">
                    <h3>✅ PRODUCTO VIABLE PARA PUBLICAR EN MERCADO LIBRE</h3>
                    <p>Obtenés un margen neto positivo de <b>${ganancia_neta_actual:,.2f} ({margin_neto_pct_actual:.1f}%)</b> compitiendo con el precio del Buy Box.</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="card-noviable">
                    <h3>❌ PRODUCTO NO VIABLE CON COSTO ACTUAL</h3>
                    <p>El costo registrado en Lista Gold (<b>${costo_gold_user:,.2f}</b>) supera el costo máximo objetivo (<b>${costo_maximo_necesario:,.2f}</b>). Requerís solicitar un <b>{pct_descuento_requerido:.1f}% de descuento</b> a tu proveedor para poder competir.</p>
                </div>
                """, unsafe_allow_html=True)

            # DESGLOSE COMPLETO DE COSTOS
            st.markdown("#### 🧾 Desglose Estructurado de Deducciones sobre el PVP")
            df_desglose = pd.DataFrame([
                {"Concepto": "PVP Objetivo de Venta", "Monto ($)": pvp_objetivo, "Porcentaje": "100.0%"},
                {"Concepto": f"Comisión Mercado Libre ({pct_comision}%)", "Monto ($)": -monto_comision, "Porcentaje": f"-{pct_comision}%"},
                {"Concepto": "Costo de Envío / Logística", "Monto ($)": -costo_envio, "Porcentaje": f"-{(costo_envio/pvp_objetivo)*100:.1f}%"},
                {"Concepto": f"Impuestos IIBB ({pct_iibb}%)", "Monto ($)": -monto_iibb, "Porcentaje": f"-{pct_iibb}%"},
                {"Concepto": f"IVA / Retenciones ({pct_iva}%)", "Monto ($)": -monto_iva, "Porcentaje": f"-{pct_iva}%"},
                {"Concepto": "Costo de Producto (Lista Gold)", "Monto ($)": -costo_gold_user, "Porcentaje": f"-{(costo_gold_user/pvp_objetivo)*100:.1f}%"},
                {"Concepto": "RESULTADO NETO FINAL", "Monto ($)": ganancia_neta_actual, "Porcentaje": f"{margin_neto_pct_actual:.1f}%"}
            ])
            st.table(df_desglose)

            st.markdown(f"👉 **Enlace a la publicación ganadora:** [{ganador['Título Publicación']}]({link_ganador})")

        else:
            st.warning("No se encontraron vendedores activos compitiendo para este código EAN en Mercado Libre.")

# ------------------------------------------
# SOLAPA 2: MATRIZ LISTA GOLD
# ------------------------------------------
with tabs[1]:
    st.header("📋 Matriz de Costos Registrados (Lista Gold)")
    if st.session_state["lista_gold_df"] is not None:
        st.dataframe(st.session_state["lista_gold_df"], use_container_width=True)
    else:
        st.info("Cargá tu archivo de Lista Gold en formato Excel o CSV desde la barra lateral izquierda para vincular tus costos de compra automáticamente.")
