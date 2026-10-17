import streamlit as st
import pandas as pd
import requests

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y CREDENCIALES MELI
# ==========================================
st.set_page_config(
    page_title="NQ Sales Intelligence Matrix",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ⚠️ Reemplazá estos valores con los de tu aplicación en dev.mercadolibre.com.ar
CLIENT_ID = "TU_CLIENT_ID"
CLIENT_SECRET = "TU_CLIENT_SECRET"
REDIRECT_URI = "https://tu-app-streamlit.streamlit.app"  # O http://localhost:8501 si testeás local

# ==========================================
# 2. ESTADO DE SESIÓN (SESSION STATE)
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "access_token" not in st.session_state:
    st.session_state["access_token"] = ""
if "user_info" not in st.session_state:
    st.session_state["user_info"] = {}
if "lista_gold_df" not in st.session_state:
    st.session_state["lista_gold_df"] = None
if "matriz_productos_df" not in st.session_state:
    st.session_state["matriz_productos_df"] = None
if "selected_item_data" not in st.session_state:
    st.session_state["selected_item_data"] = {}

# ==========================================
# 3. FUNCIONES DE AUTENTICACIÓN OAUTH AUTOMÁTICA
# ==========================================
def obtener_link_autorizacion():
    """Genera la URL para redirigir al usuario al login oficial de Mercado Libre."""
    return f"https://auth.mercadolibre.com.ar/authorization?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"

def intercambiar_code_por_token(code: str):
    """Intercambia el código temporal enviado por MeLi por el Access Token real."""
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
            return False, res.json().get("message", "Error al procesar el código")
    except Exception as e:
        return False, str(e)

def obtener_perfil_usuario(token: str):
    """Obtiene los datos del vendedor logueado."""
    url = "https://api.mercadolibre.com/users/me"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {}

# Capturar el parámetro 'code' cuando Mercado Libre redirige de vuelta
query_params = st.query_params
if "code" in query_params and not st.session_state["authenticated"]:
    auth_code = query_params["code"]
    exito, token_data = intercambiar_code_por_token(auth_code)
    if exito:
        st.session_state["access_token"] = token_data.get("access_token")
        st.session_state["user_info"] = obtener_perfil_usuario(st.session_state["access_token"])
        st.session_state["authenticated"] = True
        st.query_params.clear()  # Limpiar la URL
        st.rerun()
    else:
        st.error(f"Error al autenticar con Mercado Libre: {token_data}")

# ==========================================
# 4. FUNCIONES DE API MERCADO LIBRE
# ==========================================
def obtener_item_meli(item_id: str, access_token: str = None):
    if not item_id or not item_id.strip():
        return None
    url = f"https://api.mercadolibre.com/items/{item_id.strip()}"
    headers = {"Authorization": f"Bearer {access_token}"} if access_token else {}
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
    if not access_token:
        return False, "⚠️ Se requiere estar autenticado con Mercado Libre."

    url = "https://api.mercadolibre.com/items"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "site_id": "MLA",
        "catalog_product_id": catalog_product_id.strip(),
        "price": round(float(precio_venta), 2),
        "currency_id": "ARS",
        "available_quantity": int(quantity),
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
                "message": f"✅ ¡Publicación creada exitosamente en el Catálogo! ID: {data.get('id')}"
            }
        else:
            err_data = response.json() if response.content else {}
            err_msg = err_data.get("message", f"Error HTTP {response.status_code}")
            return False, f"❌ Error API MeLi: {err_msg}"
    except Exception as e:
        return False, f"❌ Excepción durante la conexión: {str(e)}"

# ==========================================
# 5. PANTALLA DE INICIO (LOGIN DIRECTO)
# ==========================================
if not st.session_state["authenticated"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c_left, c_main, c_right = st.columns([1, 2, 1])
    
    with c_main:
        st.title("⚡ NQ Sales Intelligence Matrix")
        st.subheader("Acceso a la Plataforma Operativa")
        st.write("Hacé clic en el botón para vincular tu cuenta oficial de Mercado Libre de forma segura sin copiar tokens manualmente.")
        
        url_auth = obtener_link_autorizacion()
        
        st.link_button("🔗 CONECTAR CON MERCADO LIBRE", url_auth, type="primary", use_container_width=True)
        
        st.markdown("---")
        if st.button("👁️ Ingresar en Modo Demo / Vista Previa", use_container_width=True):
            st.session_state["authenticated"] = True
            st.session_state["user_info"] = {"nickname": "Usuario_Demo"}
            st.rerun()
            
    st.stop()

# ==========================================
# 6. BARRA LATERAL (PANEL DE CONTROL)
# ==========================================
with st.sidebar:
    st.title("⚡ NQ Control Panel")
    user_name = st.session_state["user_info"].get("nickname", "Vendedor MeLi")
    st.success(f"🟢 Vendedor: **{user_name}**")
    
    if st.button("🔴 Desconectar Cuenta", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["access_token"] = ""
        st.session_state["user_info"] = {}
        st.rerun()

    st.markdown("---")
    st.subheader("📄 Carga de Lista Gold")
    uploaded_gold = st.file_uploader("Subir Excel / CSV (Costos)", type=["xlsx", "xls", "csv"], key="gold_up")
    if uploaded_gold is not None:
        try:
            if uploaded_gold.name.endswith('.csv'):
                st.session_state["lista_gold_df"] = pd.read_csv(uploaded_gold)
            else:
                st.session_state["lista_gold_df"] = pd.read_excel(uploaded_gold)
            st.success("✅ Lista Gold sincronizada.")
        except Exception as e:
            st.error(f"Error al leer Lista Gold: {e}")

    st.markdown("---")
    st.subheader("📊 Matriz de Productos")
    uploaded_matrix = st.file_uploader("Subir Matriz de Productos", type=["xlsx", "xls", "csv"], key="matrix_up")
    if uploaded_matrix is not None:
        try:
            if uploaded_matrix.name.endswith('.csv'):
                st.session_state["matriz_productos_df"] = pd.read_csv(uploaded_matrix)
            else:
                st.session_state["matriz_productos_df"] = pd.read_excel(uploaded_matrix)
            st.success("✅ Matriz de Productos cargada.")
        except Exception as e:
            st.error(f"Error al leer Matriz: {e}")

# ==========================================
# 7. PESTAÑAS PRINCIPALES (1 A 7)
# ==========================================
st.title("NQ Sales Intelligence Matrix Pro")
st.caption("v45.0 — Dashboard Inteligente y Publicador Directo")

tabs = st.tabs([
    "1. Resumen",
    "2. Competencia",
    "3. Costos & Lista Gold",
    "4. Financiación & Cuotas",
    "5. Envíos & Logística",
    "6. Matriz de Margen",
    "7. Publicador Directo"
])

# TAB 1: RESUMEN
with tabs[0]:
    st.header("📊 Dashboard de Control")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Cuenta MeLi", "Conectada 🟢" if st.session_state["access_token"] else "Modo Demo 🟡")
    m2.metric("Lista Gold", "Cargada 🟢" if st.session_state["lista_gold_df"] is not None else "Pendiente ⚪")
    m3.metric("Matriz Productos", "Cargada 🟢" if st.session_state["matriz_productos_df"] is not None else "Pendiente ⚪")
    m4.metric("Moneda Base", "ARS ($)")

    if st.session_state["matriz_productos_df"] is not None:
        st.markdown("---")
        st.subheader("📦 Vista de Matriz de Productos")
        st.dataframe(st.session_state["matriz_productos_df"].head(10), use_container_width=True)

# TAB 2: COMPETENCIA
with tabs[1]:
    st.header("🔍 Auditoría de Competencia")
    col_c1, col_c2 = st.columns([3, 1])
    item_id_input = col_c1.text_input("ID de Publicación (ej. MLA138291029)", value="MLA138291029")
    if col_c2.button("Buscar en MeLi", use_container_width=True):
        data_item = obtener_item_meli(item_id_input, st.session_state["access_token"])
        if data_item:
            st.session_state["selected_item_data"] = data_item
            st.success(f"Producto: **{data_item.get('title')}**")
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Precio Competencia", f"${data_item.get('price', 0):,.2f}")
            k2.metric("Catalog Product ID", data_item.get("catalog_product_id", "Sin Catálogo"))
            k3.metric("Tipo de Lista", data_item.get("listing_type_id", "N/A"))
            k4.metric("Vendidos", data_item.get("sold_quantity", 0))

# TAB 3: COSTOS & LISTA GOLD
with tabs[2]:
    st.header("📋 Costos Baseline (Lista Gold)")
    if st.session_state["lista_gold_df"] is not None:
        df_g = st.session_state["lista_gold_df"]
        st.dataframe(df_g, use_container_width=True)
        sku_col = df_g.columns[0]
        skus = df_g[sku_col].dropna().unique()
        sel_sku = st.selectbox("Seleccionar SKU/Producto", skus)
        match = df_g[df_g[sku_col] == sel_sku]
        if not match.empty and len(df_g.columns) > 1:
            val_costo = match.iloc[0, 1]
            st.success(f"💵 Costo base detectado para **{sel_sku}**: **${val_costo}**")

# TAB 4: FINANCIACIÓN
with tabs[3]:
    st.header("💳 Calculadora de Financiación")
    col_f1, col_f2 = st.columns(2)
    plan_cuotas = col_f1.selectbox("Plan de Financiación", ["Clásica (1 pago)", "3 Cuotas sin interés", "6 Cuotas Premium (gold_pro)", "12 Cuotas sin interés"])
    monto_ref = col_f2.number_input("Precio de Venta Base ($)", value=25000.0, step=1000.0)
    pct_recargo = 0.15 if "6 Cuotas" in plan_cuotas else (0.28 if "12 Cuotas" in plan_cuotas else 0.0)
    st.metric("Cargo por Financiación Estimado", f"${monto_ref * pct_recargo:,.2f}", delta=f"{pct_recargo*100:.1f}%")

# TAB 5: ENVÍOS
with tabs[4]:
    st.header("🚚 Costos Logísticos (Mercado Envíos / Flex)")
    peso_paq = st.number_input("Peso estimado (kg)", min_value=0.1, value=1.0)
    costo_envio = 2800.0 if peso_paq <= 2.0 else 5200.0
    st.metric("Costo de Envío Estimado", f"${costo_envio:,.2f}")

# TAB 6: MATRIZ DE MARGEN
with tabs[5]:
    st.header("📈 Simulación de Margen Neto")
    col_m1, col_m2, col_m3 = st.columns(3)
    pvp_val = col_m1.number_input("Precio Propuesto ($)", value=35000.0)
    costo_val = col_m2.number_input("Costo Directo ($)", value=12000.0)
    comision_pct = col_m3.slider("Comisión MeLi (%)", 10.0, 35.0, 28.0)
    margen_neto = pvp_val - costo_val - (pvp_val * (comision_pct / 100.0))
    st.metric("Margen Neto Estimado", f"${margen_neto:,.2f}")

# TAB 7: PUBLICADOR DIRECTO
with tabs[6]:
    st.header("📦 Publicador Directo en Catálogo (`POST /items`)")
    cat_def = st.session_state["selected_item_data"].get("catalog_product_id", "MLA20491823") if st.session_state["selected_item_data"] else "MLA20491823"
    
    col_p1, col_p2 = st.columns(2)
    cat_id = col_p1.text_input("Catalog Product ID", value=cat_def)
    precio_pub = col_p2.number_input("Precio Final ($ ARS)", value=38000.0)
    
    col_p3, col_p4 = st.columns(2)
    list_type = col_p3.selectbox("Tipo de Publicación", ["gold_pro (Premium / Cuotas)", "gold_special (Clásica)"])
    list_code = "gold_pro" if "gold_pro" in list_type else "gold_special"
    stock_pub = col_p4.number_input("Stock Disponible", min_value=1, value=5)
    
    st.markdown("---")
    if st.button("🚀 PUBLICAR EN MERCADO LIBRE", type="primary", use_container_width=True):
        with st.spinner("Procesando publicación en catálogo..."):
            ok, resp = publicar_item_en_catalogo(
                catalog_product_id=cat_id,
                precio_venta=precio_pub,
                listing_type_id=list_code,
                quantity=int(stock_pub),
                access_token=st.session_state.get("access_token")
            )
            if ok:
                st.success(resp["message"])
                st.markdown(f"👉 [Ver Publicación en Mercado Libre]({resp['permalink']})")
            else:
                st.error(resp)
