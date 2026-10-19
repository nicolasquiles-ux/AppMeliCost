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
if "matriz_productos_df" not in st.session_state:
    st.session_state["matriz_productos_df"] = None

# ==========================================
# 4. FUNCIONES DE API MERCADO LIBRE
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

def resolver_id_catalogo_o_ean(input_text: str, access_token: str = None):
    val = input_text.strip()
    headers = {"Authorization": f"Bearer {access_token.strip()}"} if access_token else {}
    
    catalog_id = ""
    if val.upper().startswith("MLA"):
        catalog_id = val
    elif val.isdigit():
        url_search = f"https://api.mercadolibre.com/products/search?status=active&site_id=MLA&product_identifier={val}"
        try:
            res = requests.get(url_search, headers=headers, timeout=8)
            if res.status_code == 200:
                results = res.json().get("results", [])
                if results:
                    catalog_id = results[0].get("id", "")
        except Exception:
            pass

    if not catalog_id:
        return None

    # Obtener info básica del catálogo
    url_prod = f"https://api.mercadolibre.com/products/{catalog_id}"
    prod_data = {}
    try:
        res = requests.get(url_prod, headers=headers, timeout=8)
        if res.status_code == 200:
            prod_data = res.json()
    except Exception:
        pass

    title = prod_data.get("name", prod_data.get("title", ""))
    category_id = prod_data.get("category_id", "")
    domain_id = prod_data.get("domain_id", "")

    # Búsqueda de publicaciones asociadas para extraer metadatos
    vendedores = buscar_items_por_catalogo(catalog_id, title, access_token)
    if vendedores:
        primer_item = vendedores[0]
        if not title:
            title = primer_item.get("title", f"Producto {catalog_id}")
        if not category_id:
            category_id = primer_item.get("category_id", "MLA35254")

    # Extraer family_name o usar el título base como familia de producto
    family_name = title if title else "Mobiliario"
    for attr in prod_data.get("attributes", []):
        if attr.get("id") == "FAMILY_NAME":
            family_name = attr.get("value_name", family_name)

    return {
        "id": catalog_id,
        "title": title if title else f"Producto {catalog_id}",
        "category_id": category_id if category_id else "MLA35254",
        "domain_id": domain_id if domain_id else "MLA-BIBLIOTHEQUES",
        "family_name": family_name,
        "vendedores": vendedores
    }

def buscar_items_por_catalogo(catalog_id: str, titulo: str = "", access_token: str = None):
    headers = {"Authorization": f"Bearer {access_token.strip()}"} if access_token else {}
    results = []

    # 1. Búsqueda directa por catalog_product_id
    if catalog_id:
        url = f"https://api.mercadolibre.com/sites/MLA/search?catalog_product_id={catalog_id.strip()}"
        try:
            res = requests.get(url, headers=headers, timeout=8)
            if res.status_code == 200:
                results = res.json().get("results", [])
        except Exception:
            pass

    # 2. Fallback de búsqueda libre por Query si la búsqueda de catálogo no retornó ítems
    if not results and titulo:
        query_str = requests.utils.quote(titulo[:35])
        url_q = f"https://api.mercadolibre.com/sites/MLA/search?q={query_str}"
        try:
            res = requests.get(url_q, headers=headers, timeout=8)
            if res.status_code == 200:
                results = res.json().get("results", [])
        except Exception:
            pass

    return results

def publicar_item_en_catalogo(
    catalog_product_id: str,
    titulo_producto: str,
    categoria_id: str,
    family_name: str,
    precio_venta: float,
    listing_type_id: str = "gold_pro",
    quantity: int = 1,
    condition: str = "new",
    access_token: str = None
):
    if not access_token or not access_token.strip():
        return False, "⚠️ Se requiere conectar la cuenta de Mercado Libre para publicar."

    url = "https://api.mercadolibre.com/items"
    headers = {
        "Authorization": f"Bearer {access_token.strip()}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Asignar un family_name seguro basado en el título si viene vacío
    clean_family = family_name if (family_name and family_name != "Mobiliario") else titulo_producto[:30]

    # Payload estandarizado de POST /items para Catálogo en MeLi
    payload = {
        "title": titulo_producto[:60] if titulo_producto else "Producto de Catálogo",
        "category_id": categoria_id if categoria_id else "MLA35254",
        "price": round(float(precio_venta), 2),
        "currency_id": "ARS",
        "available_quantity": int(quantity),
        "buying_mode": "buy_it_now",
        "listing_type_id": listing_type_id,
        "condition": condition,
        "site_id": "MLA",
        "catalog_product_id": catalog_product_id.strip(),
        "family_name": clean_family,
        "attributes": [
            {
                "id": "FAMILY_NAME",
                "value_name": clean_family
            },
            {
                "id": "BRAND",
                "value_name": "Genérica"
            },
            {
                "id": "MODEL",
                "value_name": catalog_product_id.strip()
            }
        ]
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
            if "cause" in err_data:
                causes = [c.get("message", "") for c in err_data.get("cause", []) if c.get("message")]
                if causes:
                    err_msg += " (" + ", ".join(causes) + ")"
            return False, f"❌ Error API MeLi: {err_msg}"
    except Exception as e:
        return False, f"❌ Excepción durante la conexión: {str(e)}"

# ==========================================
# 5. CAPTURA Y PROCESAMIENTO AUTOMÁTICO DE OAUTH
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
        else:
            st.error(f"❌ Falló el intercambio de Token con MeLi: {token_resp}")

# ==========================================
# 6. PANTALLA DE LOGIN LOCAL DE LA APLICACIÓN
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
# 7. BARRA LATERAL (CONTROL PANEL & OAUTH)
# ==========================================
with st.sidebar:
    st.title("⚡ NQ Control Panel")
    
    if st.button("🔴 Cerrar Sesión App", use_container_width=True):
        st.session_state["authenticated_app"] = False
        st.session_state["access_token"] = ""
        st.session_state["user_info"] = {}
        st.rerun()

    st.markdown("---")
    st.subheader("🔗 Conexión a Mercado Libre")
    
    if st.session_state["access_token"]:
        nickname_v = st.session_state["user_info"].get("nickname", "AURORAHOMEOK")
        st.success(f"🟢 Vendedor: **{nickname_v}**")
        if st.button("Desconectar MeLi"):
            st.session_state["access_token"] = ""
            st.session_state["user_info"] = {}
            st.rerun()
    else:
        st.warning("⚠️ Sin conexión con Mercado Libre")
        url_auth = obtener_url_login_meli()
        st.link_button("🔗 CONECTAR CON MERCADO LIBRE", url_auth, type="primary", use_container_width=True)

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
# 8. PESTAÑAS PRINCIPALES (1 A 7)
# ==========================================
st.title("NQ Sales Intelligence Matrix Pro")
st.caption("v63.0 — Dashboard Operativo, Analizador de Catálogo, Top de Vendedores y Publicador Directo")

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
    m1.metric("API Mercado Libre", "Conectado 🟢" if st.session_state["access_token"] else "Desconectado 🔴")
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
        try:
            res_item = requests.get(f"https://api.mercadolibre.com/items/{item_id_input.strip()}", headers=headers).json()
            if "id" in res_item:
                st.success(f"Producto: **{res_item.get('title')}**")
                c1, c2, c3 = st.columns(3)
                c1.metric("Precio", f"${res_item.get('price', 0):,.2f}")
                c2.metric("Catalog ID", res_item.get("catalog_product_id", "N/A"))
                c3.metric("Stock", res_item.get("available_quantity", 0))
            else:
                st.error("No se pudo obtener la publicación.")
        except Exception as e:
            st.error(f"Error al consultar la publicación: {e}")

# ------------------------------------------
# TAB 3: COSTOS & LISTA GOLD
# ------------------------------------------
with tabs[2]:
    st.header("📋 Matriz de Costos (Lista Gold)")
    if st.session_state["lista_gold_df"] is not None:
        df_g = st.session_state["lista_gold_df"]
        st.dataframe(df_g, use_container_width=True)
        
        col_sku = df_g.columns[0]
        sel_sku = st.selectbox("Seleccionar SKU/Artículo", df_g[col_sku].dropna().unique())
        match = df_g[df_g[col_sku] == sel_sku]
        
        if not match.empty:
            cost_cols = [c for c in df_g.columns if "costo" in str(c).lower() or "precio" in str(c).lower()]
            col_costo_usr = cost_cols[0] if cost_cols else (df_g.columns[1] if len(df_g.columns) > 1 else df_g.columns[0])
            
            raw_val = match.iloc[0][col_costo_usr]
            try:
                clean_val = float(str(raw_val).replace("$", "").replace(".", "").replace(",", ".").strip())
                st.success(f"💵 Costo detectado para **{sel_sku}** (`{col_costo_usr}`): **${clean_val:,.2f}**")
            except Exception:
                st.warning(f"Costo registrado para **{sel_sku}**: **{raw_val}**")
    else:
        st.warning("Subí tu archivo de Lista Gold en la barra lateral.")

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
    st.write("Ingresá un ID de Catálogo (ej. `MLA20491823`) o código EAN (ej. `7798009182461`) para analizar la competencia, el Buy Box, cuotas y costo necesario para ganar.")

    col_a1, col_a2 = st.columns([2, 1])
    with col_a1:
        search_input = st.text_input("Catalog Product ID o EAN", value="7798009182461")
    with col_a2:
        st.write("")
        analizar_btn = st.button("🔍 Analizar Competencia y Buy Box", type="primary", use_container_width=True)

    cat_details = None
    real_catalog_id = ""

    if analizar_btn or search_input:
        with st.spinner("Consultando producto de catálogo en Mercado Libre..."):
            cat_details = resolver_id_catalogo_o_ean(search_input, st.session_state["access_token"])

        if cat_details:
            real_catalog_id = cat_details.get("id", "")
            title_p = cat_details.get("title", "Sin Título")
            cat_id_p = cat_details.get("category_id", "")
            fam_name = cat_details.get("family_name", title_p[:30])
            
            st.success(f"✅ **Producto Identificado:** {title_p} | **Catalog ID:** `{real_catalog_id}` | **Categoría:** `{cat_id_p}`")
            
            vendedores_items = cat_details.get("vendedores", [])

            if vendedores_items:
                st.subheader("🏆 Top de Vendedores Activos en este Catálogo (Buy Box)")
                data_competencia = []
                for item in vendedores_items[:15]:
                    installments_info = item.get("installments", {})
                    cuotas_qty = installments_info.get("quantity", 1) if installments_info else 1
                    
                    data_competencia.append({
                        "Vendedor ID": item.get("seller", {}).get("id", "N/A"),
                        "Precio ($ ARS)": item.get("price", 0),
                        "Cuotas": f"{cuotas_qty} cuotas",
                        "Tipo Listado": item.get("listing_type_id", "gold_pro"),
                        "Stock": item.get("available_quantity", 1),
                        "Título Publicación": item.get("title", title_p),
                        "Link": item.get("permalink", "#")
                    })
                
                df_comp = pd.DataFrame(data_competencia)
                df_comp = df_comp.sort_values(by="Precio ($ ARS)", ascending=True).reset_index(drop=True)
                
                st.dataframe(df_comp, use_container_width=True)
                
                precio_ganador = df_comp.iloc[0]["Precio ($ ARS)"]
                cuotas_ganador = df_comp.iloc[0]["Cuotas"]
                link_ganador = df_comp.iloc[0]["Link"]
                
                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("🥇 PVP Ganador (Buy Box)", f"${precio_ganador:,.2f}")
                col_m2.metric("💳 Cuotas Ganadoras", cuotas_ganador)
                col_m3.metric("🎯 Costo Máximo Sugerido (Est. 30% Margen)", f"${precio_ganador * 0.70:,.2f}")
                
                if link_ganador and link_ganador != "#":
                    st.markdown(f"👉 **Enlace directo a la publicación ganadora en Mercado Libre:** [Ver Competidor]({link_ganador})")
            else:
                st.warning("No se encontraron vendedores competidores activos para esta publicación.")
        else:
            st.error("No se encontró un producto de catálogo para la clave ingresada. Verificá que sea un Catalog ID (`MLA...`) o EAN válido.")

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
            if not cat_details or not real_catalog_id:
                st.error("⚠️ Analizá y validá primero un producto de catálogo válido antes de publicar.")
            else:
                with st.spinner("Enviando publicación a Mercado Libre..."):
                    exito, respuesta = publicar_item_en_catalogo(
                        catalog_product_id=real_catalog_id,
                        titulo_producto=cat_details.get("title", ""),
                        categoria_id=cat_details.get("category_id", ""),
                        family_name=cat_details.get("family_name", ""),
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
