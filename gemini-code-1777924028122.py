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

# ==========================================
# 4. FUNCIONES ORIGINALES DE API MERCADO LIBRE (v39/v58)
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
    """Lógica exacta v38/v58: Resuelve EAN o Catalog ID a producto completo."""
    val = input_text.strip()
    headers = {"Authorization": f"Bearer {access_token.strip()}"} if access_token else {}
    
    catalog_id = ""
    title = ""
    category_id = ""

    if val.upper().startswith("MLA"):
        catalog_id = val
    else:
        # Búsqueda por EAN o texto
        url_search = f"https://api.mercadolibre.com/products/search?status=active&site_id=MLA&product_identifier={val}"
        try:
            res = requests.get(url_search, headers=headers, timeout=8)
            if res.status_code == 200:
                results = res.json().get("results", [])
                if results:
                    catalog_id = results[0].get("id", "")
                    title = results[0].get("name", "")
                    category_id = results[0].get("domain_id", "")
        except Exception:
            pass

    if catalog_id:
        url_prod = f"https://api.mercadolibre.com/products/{catalog_id}"
        try:
            res_p = requests.get(url_prod, headers=headers, timeout=8)
            if res_p.status_code == 200:
                pdata = res_p.json()
                title = pdata.get("name", pdata.get("title", title))
                category_id = pdata.get("category_id", pdata.get("domain_id", category_id))
        except Exception:
            pass

    return {
        "id": catalog_id if catalog_id else val,
        "title": title if title else val,
        "category_id": category_id
    }

def buscar_items_por_catalogo(catalog_id: str, titulo: str = "", access_token: str = None):
    """Lógica encadenada v39: Busca por Catálogo y hace fallback por Query si no halla resultados."""
    headers = {"Authorization": f"Bearer {access_token.strip()}"} if access_token else {}
    results = []

    if catalog_id and catalog_id.upper().startswith("MLA"):
        url_cat = f"https://api.mercadolibre.com/sites/MLA/search?catalog_product_id={catalog_id.strip()}"
        try:
            res = requests.get(url_cat, headers=headers, timeout=8)
            if res.status_code == 200:
                results = res.json().get("results", [])
        except Exception:
            pass

    # Fallback por título o EAN
    if not results and titulo:
        query_clean = requests.utils.quote(titulo[:40])
        url_q = f"https://api.mercadolibre.com/sites/MLA/search?q={query_clean}"
        try:
            res_q = requests.get(url_q, headers=headers, timeout=8)
            if res_q.status_code == 200:
                results = res_q.json().get("results", [])
        except Exception:
            pass

    return results

def publicar_en_mercado_libre(catalog_id: str, titulo: str, categoria: str, precio: float, stock: int, tipo_listado: str, access_token: str):
    if not access_token:
        return False, "⚠️ Debés conectar Mercado Libre o ingresar un Access Token válido."

    url = "https://api.mercadolibre.com/items"
    headers = {
        "Authorization": f"Bearer {access_token.strip()}",
        "Content-Type": "application/json"
    }

    payload = {
        "title": titulo[:60] if titulo else "Producto Publicado",
        "category_id": categoria if (categoria and not categoria.startswith("MLA-")) else "MLA35254",
        "price": round(float(precio), 2),
        "currency_id": "ARS",
        "available_quantity": int(stock),
        "buying_mode": "buy_it_now",
        "listing_type_id": tipo_listado,
        "condition": "new",
        "site_id": "MLA"
    }

    if catalog_id and catalog_id.upper().startswith("MLA"):
        payload["catalog_product_id"] = catalog_id.strip()

    try:
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        if res.status_code in [200, 201]:
            data = res.json()
            return True, f"✅ ¡Publicación creada con éxito! ID: {data.get('id')} — [Ver en MeLi]({data.get('permalink')})"
        else:
            err = res.json() if res.content else {}
            msg = err.get("message", f"Error HTTP {res.status_code}")
            if "cause" in err:
                causes = [c.get("message", "") for c in err.get("cause", []) if c.get("message")]
                if causes:
                    msg += " (" + ", ".join(causes) + ")"
            return False, f"❌ Error API MeLi: {msg}"
    except Exception as e:
        return False, f"❌ Error de conexión: {str(e)}"

# ==========================================
# 5. CAPTURA AUTOMÁTICA DE CALLBACK OAUTH
# ==========================================
query_params = st.query_params
code_auth = query_params.get("code", None)

if code_auth and not st.session_state["access_token"]:
    with st.spinner("Conectando con Mercado Libre..."):
        exito, token_resp = intercambiar_code_por_token(code_auth)
        if exito:
            st.session_state["access_token"] = token_resp.get("access_token", "")
            st.session_state["user_info"] = obtener_perfil_meli(st.session_state["access_token"])
            st.session_state["authenticated_app"] = True
            st.query_params.clear()
            st.rerun()

# ==========================================
# 6. PANTALLA DE LOGIN LOCAL
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
# 7. BARRA LATERAL (CONTROL & CONEXIÓN MELI)
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
# 8. ESTRUCTURA CON TRATAMIENTO DE BÚSQUEDA v39
# ==========================================
st.title("NQ Sales Intelligence Matrix Pro")
st.caption("v66.0 — Panel de Inteligencia de Mercado y Publicación")

tabs = st.tabs([
    "1. 📊 Resumen & Lista Gold",
    "2. 🏆 Analizador de Competencia & Top Vendedores",
    "3. 🚀 Publicador en Mercado Libre"
])

# ------------------------------------------
# SOLAPA 1: RESUMEN Y LISTA GOLD
# ------------------------------------------
with tabs[0]:
    st.header("📊 Resumen Operativo")
    col1, col2, col3 = st.columns(3)
    col1.metric("Estado MeLi", "Conectado 🟢" if st.session_state["access_token"] else "Desconectado 🔴")
    col2.metric("Lista Gold", "Cargada 🟢" if st.session_state["lista_gold_df"] is not None else "Pendiente ⚪")
    col3.metric("Moneda Base", "ARS ($)")

    st.markdown("---")
    st.subheader("📋 Lista de Costos (Lista Gold)")
    if st.session_state["lista_gold_df"] is not None:
        st.dataframe(st.session_state["lista_gold_df"], use_container_width=True)
    else:
        st.info("Subí tu archivo de Lista Gold desde la barra lateral para ver tus costos cargados.")

# ------------------------------------------
# SOLAPA 2: ANALIZADOR DE COMPETENCIA (v39 Restaurado)
# ------------------------------------------
with tabs[1]:
    st.header("🏆 Analizador de Competencia & Top de Vendedores")
    st.write("Ingresá un **ID de Catálogo** (ej. `MLA20491823`), **EAN** (ej. `7798274750037`) o **Título del Producto**:")

    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        query_input = st.text_input("Buscador", value="7798274750037", label_visibility="collapsed")
    with col_s2:
        btn_buscar = st.button("🔍 Buscar Competencia", type="primary", use_container_width=True)

    if btn_buscar or query_input:
        with st.spinner("Consultando producto de catálogo en Mercado Libre..."):
            resolved = resolver_id_catalogo_o_ean(query_input, st.session_state["access_token"])
            cat_id = resolved.get("id", "")
            title_p = resolved.get("title", "")
            
            items_list = buscar_items_por_catalogo(cat_id, title_p, st.session_state["access_token"])

        if items_list:
            st.success(f"✅ **Producto Identificado:** {title_p} | **Catalog ID / Ref:** `{cat_id}`")
            st.subheader("🏆 Top de Vendedores Activos en este Catálogo (Buy Box)")
            
            data_comp = []
            for item in items_list[:15]:
                cuotas = item.get("installments", {}).get("quantity", 1) if item.get("installments") else 1
                data_comp.append({
                    "Vendedor ID": item.get("seller", {}).get("id", "N/A"),
                    "Precio ($ ARS)": item.get("price", 0),
                    "Cuotas": f"{cuotas} cuotas",
                    "Tipo Listado": item.get("listing_type_id", "gold_pro"),
                    "Stock": item.get("available_quantity", 1),
                    "Título Publicación": item.get("title", ""),
                    "Link": item.get("permalink", "#")
                })

            df_c = pd.DataFrame(data_comp).sort_values(by="Precio ($ ARS)", ascending=True).reset_index(drop=True)
            st.dataframe(df_c, use_container_width=True)

            precio_min = df_c.iloc[0]["Precio ($ ARS)"]
            cuotas_win = df_c.iloc[0]["Cuotas"]
            link_win = df_c.iloc[0]["Link"]

            m1, m2, m3 = st.columns(3)
            m1.metric("🥇 PVP Ganador (Buy Box)", f"${precio_min:,.2f}")
            m2.metric("💳 Cuotas Ganadoras", cuotas_win)
            m3.metric("🎯 Costo Máximo Sugerido (30% Margen)", f"${precio_min * 0.70:,.2f}")

            st.markdown(f"👉 **Enlace directo a la publicación ganadora:** [{df_c.iloc[0]['Título Publicación']}]({link_win})")
        else:
            st.warning("No se encontraron vendedores activos para esta búsqueda. Probá ingresando el nombre del producto o revisá el código.")

# ------------------------------------------
# SOLAPA 3: PUBLICADOR
# ------------------------------------------
with tabs[2]:
    st.header("🚀 Publicador Directo en Mercado Libre")
    st.write("Completá los campos para crear la publicación en tu cuenta conectada:")

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        pub_titulo = st.text_input("Título de la Publicación", value="Biblioteca 5 Estantes Centro Estant")
        pub_cat_id = st.text_input("ID de Catálogo (Opcional)", value="")
        pub_categoria = st.text_input("Categoría MeLi", value="MLA35254")
    
    with col_p2:
        pub_precio = st.number_input("Precio de Venta ($ ARS)", min_value=100.0, value=38000.0, step=500.0)
        pub_stock = st.number_input("Stock Inicial", min_value=1, value=5)
        pub_tipo = st.selectbox("Modalidad", ["gold_pro", "gold_special"], format_func=lambda x: "Premium / Cuotas (gold_pro)" if x=="gold_pro" else "Clásica (gold_special)")

    st.markdown("---")
    if st.button("🚀 CREAR PUBLICACIÓN EN MERCADO LIBRE", type="primary", use_container_width=True):
        with st.spinner("Enviando publicación a Mercado Libre..."):
            exito, msg = publicar_en_mercado_libre(
                catalog_id=pub_cat_id,
                titulo=pub_titulo,
                categoria=pub_categoria,
                precio=pub_precio,
                stock=pub_stock,
                tipo_listado=pub_tipo,
                access_token=st.session_state.get("access_token")
            )
            if exito:
                st.success(msg)
            else:
                st.error(msg)
