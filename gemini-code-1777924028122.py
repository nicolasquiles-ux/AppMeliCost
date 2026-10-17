import streamlit as st
import pandas as pd
import requests

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ==========================================
st.set_page_config(
    page_title="NQ Sales Intelligence Matrix Pro",
    page_icon="⚡",
    layout="wide"
)

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. GESTIÓN DE SESSION STATE
# ==========================================
if "access_token" not in st.session_state:
    st.session_state["access_token"] = ""
if "lista_gold_df" not in st.session_state:
    st.session_state["lista_gold_df"] = None
if "selected_item_data" not in st.session_state:
    st.session_state["selected_item_data"] = {}

# ==========================================
# 3. FUNCIONES DE API MERCADO LIBRE & CONEXIÓN
# ==========================================
def probar_conexion_meli(access_token: str):
    """Verifica si el token de MeLi es válido consultando el perfil del usuario."""
    if not access_token:
        return False, "Token vacío"
    url = "https://api.mercadolibre.com/users/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            return True, res.json()
        else:
            return False, f"Error {res.status_code}: Token inválido o expirado"
    except Exception as e:
        return False, str(e)

def obtener_item_meli(item_id: str, access_token: str = None):
    """Consulta los datos de una publicación o ítem de catálogo en MeLi."""
    url = f"https://api.mercadolibre.com/items/{item_id}"
    headers = {}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None

def publicar_item_en_catalogo(
    catalog_product_id: str,
    precio_venta: float,
    listing_type_id: str = "gold_pro",
    quantity: int = 1,
    condition: str = "new",
    access_token: str = None
):
    """Ejecuta el POST /items para publicar directamente en catálogo de Mercado Libre."""
    if not access_token:
        return False, "⚠️ Se requiere un Access Token activo de Mercado Libre para publicar."

    url = "https://api.mercadolibre.com/items"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "site_id": "MLA",
        "catalog_product_id": catalog_product_id,
        "price": round(precio_venta, 2),
        "currency_id": "ARS",
        "available_quantity": quantity,
        "buying_mode": "buy_it_now",
        "listing_type_id": listing_type_id,
        "condition": condition
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code in [200, 201]:
            data = response.json()
            return True, {
                "item_id": data.get("id"),
                "permalink": data.get("permalink"),
                "message": f"✅ ¡Publicación creada con éxito! ID: {data.get('id')}"
            }
        else:
            err_data = response.json()
            err_msg = err_data.get("message", "Error devuelto por la API de Mercado Libre")
            return False, f"❌ Error ({response.status_code}): {err_msg}"
    except Exception as e:
        return False, f"❌ Excepción durante la conexión: {str(e)}"

# ==========================================
# 4. BARRA LATERAL (SIDEBAR)
# ==========================================
with st.sidebar:
    st.title("⚡ NQ Control Panel")
    st.subheader("🔑 Conexión Mercado Libre")
    
    token_input = st.text_input(
        "Access Token (OAuth)",
        value=st.session_state["access_token"],
        type="password",
        help="Pegá tu token de acceso de Mercado Libre"
    )
    st.session_state["access_token"] = token_input

    if token_input:
        is_valid, user_data = probar_conexion_meli(token_input)
        if is_valid:
            st.success(f"Conectado como: {user_data.get('nickname', 'Usuario MeLi')}")
        else:
            st.warning("⚠️ Token no verificado o desconectado.")

    st.markdown("---")
    st.subheader("📄 Carga de Lista Gold")
    uploaded_file = st.file_uploader("Subir Excel / CSV de Costos Baseline", type=["xlsx", "xls", "csv"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                st.session_state["lista_gold_df"] = pd.read_csv(uploaded_file)
            else:
                st.session_state["lista_gold_df"] = pd.read_excel(uploaded_file)
            st.success("✅ Lista Gold vinculada correctamente.")
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")

# ==========================================
# 5. HEADER Y NAVEGACIÓN PRINCIPAL
# ==========================================
st.title("NQ Sales Intelligence Matrix Pro")
st.caption("v46.2 — Sistema Integral de Análisis Comercial y Publicador en Vivo para Mercado Libre")

tabs = st.tabs([
    "1. Resumen",
    "2. Competencia",
    "3. Costos & Lista Gold",
    "4. Financiación & Cuotas",
    "5. Envíos & Logística",
    "6. Matriz de Margen",
    "7. Publicador Directo"
])

# ------------------------------------------
# TAB 1: RESUMEN OPERATIVO
# ------------------------------------------
with tabs[0]:
    st.header("📊 Dashboard Operativo")
    col1, col2, col3, col4 = st.columns(4)
    
    token_status = "Conectado 🟢" if st.session_state["access_token"] else "Desconectado 🔴"
    gold_status = "Cargada 🟢" if st.session_state["lista_gold_df"] is not None else "Pendiente ⚪"
    
    col1.metric("Estado API MeLi", token_status)
    col2.metric("Estado Lista Gold", gold_status)
    col3.metric("Moneda Base", "ARS ($)")
    col4.metric("Entorno", "Producción / Live")
    
    st.markdown("---")
    st.info("💡 **Bienvenido al núcleo operativo.** Utilizá las solapas superiores para auditar a la competencia, verificar los costos de tu Lista Gold, calcular financiación y enviar publicaciones directamente al catálogo de Mercado Libre desde la Solapa 7.")

# ------------------------------------------
# TAB 2: ANÁLISIS DE COMPETENCIA
# ------------------------------------------
with tabs[1]:
    st.header("🔍 Análisis de Publicación de Competencia")
    st.write("Ingresá el ID de una publicación de Mercado Libre para analizar su precio, tipo de publicación y ID de catálogo.")
    
    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        item_search_id = st.text_input("ID de Publicación (ej. MLA138291029)", value="MLA138291029")
    with col_s2:
        st.write("")
        buscar_btn = st.button("Consultar Ítem", use_container_width=True)
    
    if buscar_btn or item_search_id:
        item_data = obtener_item_meli(item_search_id, st.session_state["access_token"])
        if item_data:
            st.session_state["selected_item_data"] = item_data
            st.success(f"✅ Éxito: {item_data.get('title')}")
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Precio Competencia", f"${item_data.get('price', 0):,.2f}")
            c2.metric("Catalog Product ID", item_data.get("catalog_product_id", "Sin Catálogo"))
            c3.metric("Tipo de Listado", item_data.get("listing_type_id", "N/A"))
            c4.metric("Stock Disponible", item_data.get("available_quantity", 0))
        else:
            st.error("No se pudo obtener la información. Verificá que el ID sea correcto o que el token sea válido.")

# ------------------------------------------
# TAB 3: COSTOS & LISTA GOLD
# ------------------------------------------
with tabs[2]:
    st.header("📋 Matriz de Costos Baseline (Lista Gold)")
    if st.session_state["lista_gold_df"] is not None:
        df_gold = st.session_state["lista_gold_df"]
        st.dataframe(df_gold, use_container_width=True)
        
        sku_col = df_gold.columns[0]
        sku_selected = st.selectbox("Seleccionar SKU / Producto de la Lista Gold", df_gold[sku_col].dropna().unique())
        
        match_row = df_gold[df_gold[sku_col] == sku_selected]
        if not match_row.empty and len(df_gold.columns) > 1:
            costo_detectado = match_row.iloc[0, 1]
            st.success(f"💵 Costo base detectado para **{sku_selected}**: **${costo_detectado:,.2f}**")
        else:
            st.warning("No se pudo extraer la columna numérica de costos automáticamente.")
    else:
        st.warning("⚠️ Todavía no cargaste la Lista Gold. Subí tu archivo Excel o CSV desde la barra lateral.")

# ------------------------------------------
# TAB 4: FINANCIACIÓN & CUOTAS
# ------------------------------------------
with tabs[3]:
    st.header("💳 Esquema de Financiación y Costos Financieros")
    st.markdown("Calculadora de impacto financiero según la cantidad de cuotas ofrecidas.")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        tipo_cuota = st.selectbox(
            "Seleccioná el plan de financiación",
            ["Clásica (1 pago / Sin cuotas s/i)", "3 Cuotas sin interés", "6 Cuotas sin interés (Gold Pro)", "12 Cuotas sin interés"]
        )
    with col_f2:
        monto_referencia = st.number_input("Precio base de referencia ($)", value=25000.0, step=1000.0)

    porcentaje_cargo = 0.0
    if "3 Cuotas" in tipo_cuota:
        porcentaje_cargo = 0.08
    elif "6 Cuotas" in tipo_cuota:
        porcentaje_cargo = 0.15
    elif "12 Cuotas" in tipo_cuota:
        porcentaje_cargo = 0.28

    costo_financiero_ARS = monto_referencia * porcentaje_cargo
    st.metric("Costo Financiero Estimado", f"${costo_financiero_ARS:,.2f}", delta=f"{porcentaje_cargo*100:.1f}% sobre PVP")

# ------------------------------------------
# TAB 5: ENVÍOS & LOGÍSTICA
# ------------------------------------------
with tabs[4]:
    st.header("🚚 Logística y Envíos (Mercado Envíos / Flex)")
    
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        peso_paquete = st.number_input("Peso estimado del paquete (kg)", min_value=0.1, value=1.0, step=0.5)
        ofrece_flex = st.checkbox("Ofrecer Envío en el Día (Mercado Envíos Flex)", value=True)
    with col_l2:
        monto_producto_envio = st.number_input("Precio del producto para gratuidad ($)", value=30000.0)

    # Lógica de costos de envío aproximados según tarifa de MeLi
    costo_envio_fijo = 2800.0 if peso_paquete <= 2 else 5200.0
    if monto_producto_envio >= 30000:
        st.info("📦 Este producto supera el umbral para **Envío Gratis obligatorio** bonificado parcialmente por reputación.")
    
    st.metric("Costo Logístico Estimado", f"${costo_envio_fijo:,.2f}")

# ------------------------------------------
# TAB 6: MATRIZ DE MARGEN
# ------------------------------------------
with tabs[5]:
    st.header("📈 Matriz de Margen Neto y Rentabilidad")
    
    col_m1, col_m2, col_m3 = st.columns(3)
    pvp_simulacion = col_m1.number_input("Precio de Venta Propuesto ($)", value=35000.0, step=1000.0)
    costo_prod_sim = col_m2.number_input("Costo de Adquisición / Lista Gold ($)", value=12000.0, step=500.0)
    comision_porc = col_m3.slider("Comisión de Plataforma (%)", min_value=10.0, max_value=35.0, value=28.0, step=0.5)

    comision_monto = pvp_simulacion * (comision_porc / 100.0)
    impuestos_estimados = pvp_simulacion * 0.05 # IIBB / Impuestos internos estimados
    margen_neto = pvp_simulacion - costo_prod_sim - comision_monto - impuestos_estimados
    rentabilidad_pct = (margen_neto / pvp_simulacion * 100) if pvp_simulacion > 0 else 0

    col_res1, col_res2 = st.columns(2)
    col_res1.metric("Margen Neto en Pesos", f"${margen_neto:,.2f}")
    col_res2.metric("Rentabilidad Porcentual", f"{rentabilidad_pct:.1f}%", delta="Saludable" if rentabilidad_pct > 15 else "Revisar")

# ------------------------------------------
# TAB 7: PUBLICADOR DIRECTO EN CATÁLOGO
# ------------------------------------------
with tabs[6]:
    st.header("📦 Publicación Directa en Catálogo (`POST /items`)")
    st.write("Utiliza los datos analizados para realizar la publicación formal directamente en Mercado Libre.")

    catalog_default = st.session_state["selected_item_data"].get("catalog_product_id", "MLA20491823")
    
    col_p1, col_p2 = st.columns(2)
    cat_id = col_p1.text_input("Catalog Product ID (Obligatorio para Catálogo)", value=catalog_default)
    precio_pub = col_p2.number_input("Precio Final de Venta ($ ARS)", value=38000.0, step=500.0)
    
    col_p3, col_p4 = st.columns(2)
    listing_pub = col_p3.selectbox("Tipo de Listado / Financiación", ["gold_pro (Premium / Cuotas sin interés)", "gold_special (Clásica / 1 pago)"])
    listing_code = "gold_pro" if "gold_pro" in listing_pub else "gold_special"
    stock_pub = col_p4.number_input("Stock Inicial Disponible", min_value=1, value=10)
    
    st.markdown("---")
    
    if st.button("🚀 PUBLICAR AHORA EN MERCADO LIBRE", type="primary", use_container_width=True):
        with st.spinner("Conectando con la API de Mercado Libre para crear la publicación..."):
            ok, resp = publicar_item_en_catalogo(
                catalog_product_id=cat_id,
                precio_venta=precio_pub,
                listing_type_id=listing_code,
                quantity=int(stock_pub),
                access_token=st.session_state.get("access_token")
            )
            if ok:
                st.success(resp["message"])
                st.markdown(f"👉 [Hacé clic acá para ver tu publicación en Mercado Libre]({resp['permalink']})", unsafe_allow_html=True)
            else:
                st.error(resp)
