import streamlit as st
import pandas as pd
import requests

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ==========================================
st.set_page_config(
    page_title="NQ Sales Intelligence Matrix v46",
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
# 3. FUNCIONES DE API MERCADO LIBRE
# ==========================================
def obtener_item_meli(item_id: str, access_token: str = None):
    """Consulta los datos de una publicación o ítem de catálogo."""
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
    """Ejecuta el POST /items para publicar directamente en catálogo."""
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
            err_msg = err_data.get("message", "Error en la API de Mercado Libre")
            return False, f"❌ Error ({response.status_code}): {err_msg}"
    except Exception as e:
        return False, f"❌ Excepción durante la conexión: {str(e)}"

# ==========================================
# 4. BARRA LATERAL (SIDEBAR)
# ==========================================
with st.sidebar:
    st.title("⚡ NQ Control Panel")
    st.subheader("🔑 Conexión Mercado Libre")
    st.session_state["access_token"] = st.text_input(
        "Access Token (OAuth)",
        value=st.session_state["access_token"],
        type="password"
    )

    st.markdown("---")
    st.subheader("📄 Carga de Lista Gold")
    uploaded_file = st.file_uploader("Subir Archivo de Costos", type=["xlsx", "xls", "csv"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                st.session_state["lista_gold_df"] = pd.read_csv(uploaded_file)
            else:
                st.session_state["lista_gold_df"] = pd.read_excel(uploaded_file)
            st.success("✅ Lista Gold vinculada correctamente.")
        except Exception as e:
            st.error(f"Error al procesar la lista: {e}")

# ==========================================
# 5. HEADER Y NAVEGACIÓN PRINCIPAL
# ==========================================
st.title("NQ Sales Intelligence Matrix")
st.caption("v46.1 — Plataforma Operativa Comercial y Publicación en Vivo")

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
    st.header("📊 Dashboard Comercial")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Estado Conexión MeLi", "Conectado" if st.session_state["access_token"] else "Pendiente")
    col2.metric("Lista Gold", "Cargada" if st.session_state["lista_gold_df"] is not None else "No disponible")
    col3.metric("Comisión Promedio", "13% / 28%")
    col4.metric("Moneda Base", "ARS")
    
    st.info("Seleccioná las pestañas superiores para inspeccionar costos, analizar publicaciones ganadoras o publicar directo en catálogo.")

# ------------------------------------------
# TAB 2: ANÁLISIS DE COMPETENCIA
# ------------------------------------------
with tabs[1]:
    st.header("🔍 Análisis de Publicación de Competencia")
    item_search_id = st.text_input("Ingresá un ID de publicación (ej. MLA138291029)", value="MLA138291029")
    
    if st.button("Buscar Publicación"):
        item_data = obtener_item_meli(item_search_id, st.session_state["access_token"])
        if item_data:
            st.session_state["selected_item_data"] = item_data
            st.success(f"Producto encontrado: {item_data.get('title')}")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Precio Competencia", f"${item_data.get('price', 0):,.2f}")
            c2.metric("Catalog Product ID", item_data.get("catalog_product_id", "Sin Catálogo"))
            c3.metric("Tipo de Lista", item_data.get("listing_type_id"))
        else:
            st.error("No se pudo obtener la información de Mercado Libre.")

# ------------------------------------------
# TAB 3: COSTOS & LISTA GOLD
# ------------------------------------------
with tabs[2]:
    st.header("📋 Matriz de Costos Baseline (Lista Gold)")
    if st.session_state["lista_gold_df"] is not None:
        df_gold = st.session_state["lista_gold_df"]
        st.dataframe(df_gold, use_container_width=True)
        
        sku_selected = st.selectbox("Seleccionar SKU/Producto de la lista", df_gold.iloc[:, 0].dropna().unique())
        costo_detectado = df_gold[df_gold.iloc[:, 0] == sku_selected].iloc[0, 1] if len(df_gold) > 0 else 0
        st.success(f"Costo Base Seleccionado para {sku_selected}: ${costo_detectado:,.2f}")
    else:
        st.warning("Subí un archivo Excel o CSV en la barra lateral para sincronizar costos.")

# ------------------------------------------
# TAB 4: FINANCIACIÓN & CUOTAS
# ------------------------------------------
with tabs[3]:
    st.header("💳 Esquema de Financiación")
    st.markdown("Calculadora de recargos por cuotas según modalidad de Mercado Libre.")
    
    tipo_cuota = st.radio("Plan de Cuotas", ["Clásica (Sin cuotas s/i)", "3 Cuotas", "6 Cuotas Premium", "12 Cuotas"])
    costo_finan = 0.0
    if "6 Cuotas" in tipo_cuota:
        costo_finan = 0.15
    elif "12 Cuotas" in tipo_cuota:
        costo_finan = 0.28

    st.info(f"Costo de financiación estimado para la modalidad: {costo_finan * 100:.1f}%")

# ------------------------------------------
# TAB 5: ENVÍOS & LOGÍSTICA
# ------------------------------------------
with tabs[4]:
    st.header("🚚 Cálculo de Envíos (ME2 / Flex)")
    peso_kg = st.number_input("Peso estimado del paquete (kg)", min_value=0.1, value=1.0)
    flex_active = st.checkbox("Ofrece Mercado Envíos Flex", value=True)
    
    costo_envio = 2500.0 if peso_kg < 2 else 4500.0
    st.metric("Costo de Envío Estimado", f"${costo_envio:,.2f}")

# ------------------------------------------
# TAB 6: MATRIZ DE MARGEN
# ------------------------------------------
with tabs[5]:
    st.header("📈 Simulación de Margen Neto")
    col_a, col_b = st.columns(2)
    pvp_sim = col_a.number_input("Precio de Venta Simulado ($)", value=30000.0)
    costo_sim = col_b.number_input("Costo Directo Producto ($)", value=12000.0)
    
    margen_bruto = pvp_sim - costo_sim
    st.metric("Margen Estimado", f"${margen_bruto:,.2f}", delta=f"{(margen_bruto/pvp_sim)*100:.1f}%")

# ------------------------------------------
# TAB 7: PUBLICADOR DIRECTO EN CATÁLOGO
# ------------------------------------------
with tabs[6]:
    st.header("📦 Publicación Directa en Catálogo (`POST /items`)")
    
    catalog_default = st.session_state["selected_item_data"].get("catalog_product_id", "MLA12345678")
    
    col_p1, col_p2 = st.columns(2)
    cat_id = col_p1.text_input("Catalog Product ID", value=catalog_default)
    precio_pub = col_p2.number_input("Precio Final de Publicación ($)", value=35000.0)
    
    col_p3, col_p4 = st.columns(2)
    listing_pub = col_p3.selectbox("Tipo de Lista", ["gold_pro (Premium / Cuotas)", "gold_special (Clásica)"])
    listing_code = "gold_pro" if "gold_pro" in listing_pub else "gold_special"
    stock_pub = col_p4.number_input("Stock Disponible", min_value=1, value=5)
    
    st.markdown("---")
    if st.button("🚀 PUBLICAR AHORA EN MERCADO LIBRE", type="primary"):
        with st.spinner("Enviando publicación a Mercado Libre..."):
            ok, resp = publicar_item_en_catalogo(
                catalog_product_id=cat_id,
                precio_venta=precio_pub,
                listing_type_id=listing_code,
                quantity=int(stock_pub),
                access_token=st.session_state["access_token"]
            )
            if ok:
                st.success(resp["message"])
                st.markdown(f"👉 [Ver Publicación en MeLi]({resp['permalink']})")
            else:
                st.error(resp)
