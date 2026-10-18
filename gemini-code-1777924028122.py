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
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ESTADO DE SESIÓN (SESSION STATE)
# ==========================================
if "authenticated_app" not in st.session_state:
    st.session_state["authenticated_app"] = False
if "access_token" not in st.session_state:
    st.session_state["access_token"] = ""
if "user_info" not in st.session_state:
    st.session_state["user_info"] = {}
if "lista_gold_df" not in st.session_state:
    st.session_state["lista_gold_df"] = None
if "matriz_productos_df" not in st.session_state:
    st.session_state["matriz_productos_df"] = None

# ==========================================
# 3. FUNCIONES DE API MERCADO LIBRE
# ==========================================
def validar_token_meli(token: str):
    """Verifica y valida el token contra la API de MeLi."""
    if not token or not token.strip():
        return False, {}
    url = "https://api.mercadolibre.com/users/me"
    headers = {"Authorization": f"Bearer {token.strip()}"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            return True, res.json()
    except Exception:
        pass
    return False, {}

def consultar_catalogo_meli(catalog_id: str, access_token: str = None):
    """Consulta los datos de un producto de catálogo."""
    url = f"https://api.mercadolibre.com/products/{catalog_id.strip()}"
    headers = {"Authorization": f"Bearer {access_token}"} if access_token else {}
    try:
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None

def buscar_items_por_catalogo(catalog_id: str, access_token: str = None):
    """Busca las publicaciones activas asociadas al catálogo (Top de Vendedores / Buy Box)."""
    url = f"https://api.mercadolibre.com/sites/MLA/search?catalog_product_id={catalog_id.strip()}"
    headers = {"Authorization": f"Bearer {access_token}"} if access_token else {}
    try:
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code == 200:
            return res.json().get("results", [])
    except Exception:
        pass
    return []

def publicar_item_en_catalogo(
    catalog_product_id: str,
    precio_venta: float,
    listing_type_id: str = "gold_pro",
    quantity: int = 1,
    condition: str = "new",
    access_token: str = None
):
    """Ejecuta el POST /items para publicación directa en catálogo de Mercado Libre."""
    if not access_token or not access_token.strip():
        return False, "⚠️ Ingresá tu Access Token en la barra lateral para poder publicar."

    url = "https://api.mercadolibre.com/items"
    headers = {
        "Authorization": f"Bearer {access_token.strip()}",
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
                "message": f"✅ ¡Publicación creada con éxito! ID: {data.get('id')}"
            }
        else:
            err_data = response.json() if response.content else {}
            err_msg = err_data.get("message", f"Error HTTP {response.status_code}")
            return False, f"❌ Error API MeLi: {err_msg}"
    except Exception as e:
        return False, f"❌ Excepción durante la conexión: {str(e)}"

# ==========================================
# 4. PANTALLA DE LOGIN LOCAL DE LA APLICACIÓN
# ==========================================
if not st.session_state["authenticated_app"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c_left, c_main, c_right = st.columns([1, 2, 1])
    
    with c_main:
        st.title("⚡ NQ Sales Intelligence Matrix")
        st.subheader("Acceso a la Plataforma SaaS")
        
        usuario_input = st.text_input("Usuario", value="admin")
        password_input = st.text_input("Contraseña", type="password", value="admin123")
        
        col_b1, col_b2 = st.columns(2)
        if col_b1.button("🔑 INICIAR SESIÓN", type="primary", use_container_width=True):
            if password_input:
                st.session_state["authenticated_app"] = True
                st.rerun()
            else:
                st.error("Ingresá tu contraseña.")
        if col_b2.button("👁️ MODO DEMO", use_container_width=True):
            st.session_state["authenticated_app"] = True
            st.rerun()
    st.stop()

# ==========================================
# 5. BARRA LATERAL (PANEL DE CONTROL & TOKEN)
# ==========================================
with st.sidebar:
    st.title("⚡ NQ Control Panel")
    
    if st.button("🔴 Cerrar Sesión App", use_container_width=True):
        st.session_state["authenticated_app"] = False
        st.session_state["access_token"] = ""
        st.session_state["user_info"] = {}
        st.rerun()

    st.markdown("---")
    st.subheader("🔑 Conexión a Mercado Libre")
    
    token_input = st.text_input(
        "Access Token de MeLi",
        value=st.session_state["access_token"],
        type="password",
        placeholder="APP_USR-...",
        help="Pegá tu token de Mercado Libre aquí para habilitar consultas en vivo y publicaciones."
    )
    
    if token_input != st.session_state["access_token"]:
        st.session_state["access_token"] = token_input

    if st.session_state["access_token"]:
        valido, info_u = validar_token_meli(st.session_state["access_token"])
        if valido:
            st.session_state["user_info"] = info_u
            st.success(f"🟢 Conectado: **{info_u.get('nickname', 'Vendedor')}**")
        else:
            st.warning("⚠️ Token no verificado o expirado.")
    else:
        st.info("💡 Ingresá tu token para operar en vivo.")

    st.markdown("---")
    st.subheader("📄 Carga de Lista Gold")
    uploaded_gold = st.file_uploader("Subir Excel / CSV (Costos)", type=["xlsx", "xls", "csv"], key="gold_up")
    if uploaded_gold is not None:
        try:
            if uploaded_gold.name.endswith('.csv'):
                st.session_state["lista_gold_df"] = pd.read_csv(uploaded_gold)
            else:
                st.session_state["lista_gold_df"] = pd.read_excel(uploaded_gold)
            st.success("✅ Lista Gold vinculada.")
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
            st.error(f"Error al leer la matriz: {e}")

# ==========================================
# 6. PESTAÑAS PRINCIPALES (1 A 7)
# ==========================================
st.title("NQ Sales Intelligence Matrix Pro")
st.caption("v49.0 — Dashboard Operativo, Analizador de Catálogo y Publicador Directo")

tabs = st.tabs([
    "1. Resumen",
    "2. Competencia",
    "3. Costos & Lista Gold",
    "4. Financiación & Cuotas",
    "5. Envíos & Logística",
    "6. Matriz de Margen",
    "7. Analizador de Catálogo & Publicador"
])

# ------------------------------------------
# TAB 1: RESUMEN
# ------------------------------------------
with tabs[0]:
    st.header("📊 Dashboard de Control")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("API Mercado Libre", "Conectado 🟢" if st.session_state["access_token"] else "Sin Token ⚪")
    m2.metric("Lista Gold", "Cargada 🟢" if st.session_state["lista_gold_df"] is not None else "Pendiente ⚪")
    m3.metric("Matriz Productos", "Cargada 🟢" if st.session_state["matriz_productos_df"] is not None else "Pendiente ⚪")
    m4.metric("Moneda Base", "ARS ($)")

    if st.session_state["matriz_productos_df"] is not None:
        st.markdown("---")
        st.subheader("📦 Vista de la Matriz de Productos")
        st.dataframe(st.session_state["matriz_productos_df"].head(10), use_container_width=True)

# ------------------------------------------
# TAB 2: COMPETENCIA
# ------------------------------------------
with tabs[1]:
    st.header("🔍 Auditoría de Competencia")
    item_id_input = st.text_input("ID de Publicación MeLi", value="MLA138291029")
    if st.button("Buscar en MeLi"):
        headers = {"Authorization": f"Bearer {st.session_state['access_token']}"} if st.session_state["access_token"] else {}
        res_item = requests.get(f"https://api.mercadolibre.com/items/{item_id_input}", headers=headers).json()
        if "id" in res_item:
            st.success(f"Producto: {res_item.get('title')}")
            c1, c2, c3 = st.columns(3)
            c1.metric("Precio", f"${res_item.get('price'):,.2f}")
            c2.metric("Catalog ID", res_item.get("catalog_product_id", "N/A"))
            c3.metric("Stock", res_item.get("available_quantity"))
        else:
            st.error("No se pudo obtener la publicación. Verificá tu token en la barra lateral.")

# ------------------------------------------
# TAB 3: COSTOS & LISTA GOLD
# ------------------------------------------
with tabs[2]:
    st.header("📋 Matriz de Costos (Lista Gold)")
    if st.session_state["lista_gold_df"] is not None:
        df_g = st.session_state["lista_gold_df"]
        st.dataframe(df_g, use_container_width=True)
        sku_col = df_g.columns[0]
        sel_sku = st.selectbox("Seleccionar SKU", df_g[sku_col].dropna().unique())
        match = df_g[df_g[sku_col] == sel_sku]
        if not match.empty:
            st.success(f"Costo detectado: ${float(match.iloc[0, 1]):,.2f}")
    else:
        st.warning("Subí la Lista Gold en el panel lateral.")

# ------------------------------------------
# TAB 4: FINANCIACIÓN
# ------------------------------------------
with tabs[3]:
    st.header("💳 Financiación & Cuotas")
    plan = st.selectbox("Plan", ["Clásica", "3 Cuotas", "6 Cuotas Premium", "12 Cuotas"])
    monto = st.number_input("Monto Ref ($)", value=25000.0)
    pct = 0.15 if "6 Cuotas" in plan else (0.28 if "12 Cuotas" in plan else 0.0)
    st.metric("Costo Financiero", f"${monto * pct:,.2f}")

# ------------------------------------------
# TAB 5: ENVÍOS
# ------------------------------------------
with tabs[4]:
    st.header("🚚 Envíos & Logística")
    peso = st.number_input("Peso (kg)", value=1.0)
    st.metric("Costo Envío", f"${2800.0 if peso <= 2 else 5200.0:,.2f}")

# ------------------------------------------
# TAB 6: MATRIZ DE MARGEN
# ------------------------------------------
with tabs[5]:
    st.header("📈 Simulación de Margen")
    pvp = st.number_input("PVP ($)", value=35000.0)
    costo = st.number_input("Costo ($)", value=12000.0)
    com = st.slider("Comisión (%)", 10.0, 35.0, 28.0)
    st.metric("Margen Neto", f"${pvp - costo - (pvp * com / 100):,.2f}")

# ------------------------------------------
# TAB 7: ANALIZADOR DE CATÁLOGO & TOP DE VENDEDORES
# ------------------------------------------
with tabs[6]:
    st.header("📦 Analizador por Producto / Catálogo & Top de Vendedores")
    st.write("Ingresá un ID de Catálogo (ej. `MLA20491823`) para analizar la competencia, ver el Top de Vendedores y evaluar el costo de tu Lista Gold.")

    col_a1, col_a2 = st.columns([2, 1])
    with col_a1:
        cat_search_id = st.text_input("Catalog Product ID", value="MLA20491823")
    with col_a2:
        st.write("")
        analizar_btn = st.button("🔍 Analizar Competencia y Buy Box", type="primary", use_container_width=True)

    if analizar_btn or cat_search_id:
        with st.spinner("Consultando datos de catálogo y competidores en Mercado Libre..."):
            cat_details = consultar_catalogo_meli(cat_search_id, st.session_state["access_token"])
            vendedores_items = buscar_items_por_catalogo(cat_search_id, st.session_state["access_token"])

        if cat_details:
            st.success(f"**Producto:** {cat_details.get('title', 'Sin Título')} | **Categoría:** {cat_details.get('category_id', 'N/A')}")
        
        if vendedores_items:
            st.subheader("🏆 Top de Vendedores Activos en este Catálogo (Buy Box)")
            
            data_competencia = []
            for item in vendedores_items[:10]:
                seller_id = item.get("seller", {}).get("id")
                precio_item = item.get("price", 0)
                permalink_item = item.get("permalink")
                listing_t = item.get("listing_type_id")
                
                data_competencia.append({
                    "Título Publicación": item.get("title"),
                    "Precio ($ ARS)": precio_item,
                    "Tipo Listado": listing_t,
                    "Stock": item.get("available_quantity"),
                    "Vendedor ID": seller_id,
                    "Link": permalink_item
                })
            
            df_comp = pd.DataFrame(data_competencia)
            st.dataframe(df_comp, use_container_width=True)
            
            precio_minimo_mercado = df_comp["Precio ($ ARS)"].min() if not df_comp.empty else 0.0
            st.info(f"💡 **Precio mínimo detectado en la competencia:** ${precio_minimo_mercado:,.2f}")
        else:
            st.warning("No se encontraron publicaciones competidoras activas para este ID de catálogo exacto.")

        st.markdown("---")
        st.subheader("🚀 Simulador y Ejecutor de Publicación en Catálogo (`POST /items`)")

        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            precio_final_pub = st.number_input("Precio de Venta Objetivo ($)", min_value=0.0, value=38000.0, step=500.0)
        with col_p2:
            tipo_list_pub = st.selectbox("Modalidad de Listado", ["gold_pro (Premium / Cuotas)", "gold_special (Clásica)"])
            code_list_pub = "gold_pro" if "gold_pro" in tipo_list_pub else "gold_special"
        with col_p3:
            stock_pub = st.number_input("Stock Inicial", min_value=1, value=5)

        if st.button("🚀 PUBLICAR EN EL CATÁLOGO DE MERCADO LIBRE", type="primary", use_container_width=True):
            with st.spinner("Enviando publicación..."):
                exito, respuesta = publicar_item_en_catalogo(
                    catalog_product_id=cat_search_id,
                    precio_venta=precio_final_pub,
                    listing_type_id=code_list_pub,
                    quantity=int(stock_pub),
                    access_token=st.session_state.get("access_token")
                )
                if exito:
                    st.success(respuesta["message"])
                    st.markdown(f"👉 [Abrir publicación creada en Mercado Libre]({respuesta['permalink']})")
                else:
                    st.error(respuesta)
