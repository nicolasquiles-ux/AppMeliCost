import streamlit as st
import pandas as pd
import requests

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="NQ Sales Intelligence Matrix",
    page_icon="⚡",
    layout="wide"
)

# ==========================================
# 2. ESTADO DE SESIÓN (SESSION STATE)
# ==========================================
if "access_token" not in st.session_state:
    st.session_state["access_token"] = ""
if "lista_gold_df" not in st.session_state:
    st.session_state["lista_gold_df"] = None
if "selected_item_data" not in st.session_state:
    st.session_state["selected_item_data"] = {}

# ==========================================
# 3. FUNCIONES CONEXIÓN MERCADO LIBRE
# ==========================================
def probar_conexion_meli(access_token: str):
    """Valida la validez del token OAuth mediante /users/me."""
    if not access_token or not access_token.strip():
        return False, "Token no ingresado"
    url = "https://api.mercadolibre.com/users/me"
    headers = {"Authorization": f"Bearer {access_token.strip()}"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            return True, f"Conectado como: {data.get('nickname', 'Usuario MeLi')}"
        else:
            return False, f"Token inválido (HTTP {res.status_code})"
    except Exception as e:
        return False, f"Error de conexión: {str(e)}"

def obtener_item_meli(item_id: str, access_token: str = None):
    """Consulta los datos de un ítem/publicación."""
    if not item_id or not item_id.strip():
        return None
    url = f"https://api.mercadolibre.com/items/{item_id.strip()}"
    headers = {}
    if access_token and access_token.strip():
        headers["Authorization"] = f"Bearer {access_token.strip()}"
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
    """Ejecuta el POST /items para publicar directo en catálogo."""
    if not access_token or not access_token.strip():
        return False, "⚠️ Se requiere un Access Token activo de Mercado Libre para publicar."

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
                "message": f"✅ ¡Publicación creada exitosamente en Catálogo! ID: {data.get('id')}"
            }
        else:
            err_data = response.json() if response.content else {}
            err_msg = err_data.get("message", f"Error HTTP {response.status_code}")
            return False, f"❌ Error API MeLi: {err_msg}"
    except Exception as e:
        return False, f"❌ Excepción durante la publicación: {str(e)}"

# ==========================================
# 4. BARRA LATERAL (SIDEBAR)
# ==========================================
with st.sidebar:
    st.title("⚡ NQ Control Panel")
    st.subheader("🔑 Conexión Mercado Libre")
    
    token_input = st.text_input(
        "Access Token (OAuth)",
        value=st.session_state["access_token"],
        type="password"
    )
    st.session_state["access_token"] = token_input

    if token_input:
        is_valid, msg = probar_conexion_meli(token_input)
        if is_valid:
            st.success(f"🟢 {msg}")
        else:
            st.warning(f"⚠️ {msg}")
    else:
        st.info("Sin token OAuth configurado.")

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
            st.error(f"Error al leer el archivo: {e}")

# ==========================================
# 5. HEADER Y NAVEGACIÓN
# ==========================================
st.title("NQ Sales Intelligence Matrix")
st.caption("v46.3 — Módulo Integral Operativo y Publicador Directo")

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
# TAB 1: RESUMEN
# ------------------------------------------
with tabs[0]:
    st.header("📊 Dashboard Operativo")
    c1, c2, c3, c4 = st.columns(4)
    
    is_conn, conn_text = probar_conexion_meli(st.session_state["access_token"])
    
    c1.metric("Estado API MeLi", "Conectado 🟢" if is_conn else "Desconectado 🔴")
    c2.metric("Lista Gold", "Cargada 🟢" if st.session_state["lista_gold_df"] is not None else "Pendiente ⚪")
    c3.metric("Moneda Base", "ARS ($)")
    c4.metric("Entorno", "Producción / Live")
    
    st.markdown("---")
    st.info("Navegá por las pestañas para auditar costos, simular comisiones y publicar directo al catálogo de Mercado Libre.")

# ------------------------------------------
# TAB 2: COMPETENCIA
# ------------------------------------------
with tabs[1]:
    st.header("🔍 Análisis de Competencia")
    item_search_id = st.text_input("ID de Publicación MeLi", value="MLA138291029")
    
    if st.button("Consultar Publicación"):
        item_data = obtener_item_meli(item_search_id, st.session_state["access_token"])
        if item_data:
            st.session_state["selected_item_data"] = item_data
            st.success(f"Título: {item_data.get('title')}")
            
            k1, k2, k3 = st.columns(3)
            k1.metric("Precio Competencia", f"${item_data.get('price', 0):,.2f}")
            k2.metric("Catalog Product ID", item_data.get("catalog_product_id", "Sin Catálogo"))
            k3.metric("Tipo de Lista", item_data.get("listing_type_id", "N/A"))
        else:
            st.error("No se pudo obtener información del ítem indicado.")

# ------------------------------------------
# TAB 3: COSTOS & LISTA GOLD (CORREGIDO)
# ------------------------------------------
with tabs[2]:
    st.header("📋 Costos Baseline (Lista Gold)")
    if st.session_state["lista_gold_df"] is not None:
        df_gold = st.session_state["lista_gold_df"]
        st.dataframe(df_gold, use_container_width=True)
        
        sku_col = df_gold.columns[0]
        skus_disponibles = df_gold[sku_col].dropna().unique()
        
        sku_selected = st.selectbox("Seleccionar SKU de la Lista Gold", skus_disponibles)
        
        match_row = df_gold[df_gold[sku_col] == sku_selected]
        if not match_row.empty and len(df_gold.columns) > 1:
            try:
                raw_val = match_row.iloc[0, 1]
                costo_val = float(raw_val) if pd.notnull(raw_val) else 0.0
                st.success(f"Costo base detectado para **{sku_selected}**: **${costo_val:,.2f}**")
            except (ValueError, TypeError):
                st.warning(f"El valor de costo ({match_row.iloc[0, 1]}) no es un formato numérico válido.")
    else:
        st.warning("⚠️ Subí un archivo Excel o CSV en la barra lateral para sincronizar la Lista Gold.")

# ------------------------------------------
# TAB 4: FINANCIACIÓN
# ------------------------------------------
with tabs[3]:
    st.header("💳 Financiación & Cuotas")
    plan_cuota = st.selectbox("Modalidad de Financiación", ["Clásica (1 pago)", "3 Cuotas sin interés", "6 Cuotas sin interés (gold_pro)", "12 Cuotas sin interés"])
    monto_ref = st.number_input("Monto de Referencia ($)", value=25000.0)
    
    pct_cargo = 0.15 if "6 Cuotas" in plan_cuota else (0.28 if "12 Cuotas" in plan_cuota else 0.0)
    st.metric("Costo Financiero Estimado", f"${monto_ref * pct_cargo:,.2f}", delta=f"{pct_cargo * 100:.1f}%")

# ------------------------------------------
# TAB 5: ENVÍOS
# ------------------------------------------
with tabs[4]:
    st.header("🚚 Logística & Envíos")
    peso_kg = st.number_input("Peso estimado (kg)", min_value=0.1, value=1.0)
    costo_log = 2800.0 if peso_kg <= 2.0 else 5200.0
    st.metric("Costo de Envío Estimado", f"${costo_log:,.2f}")

# ------------------------------------------
# TAB 6: MATRIZ DE MARGEN
# ------------------------------------------
with tabs[5]:
    st.header("📈 Matriz de Margen Neto")
    pvp_calc = st.number_input("Precio de Venta ($)", value=35000.0)
    costo_calc = st.number_input("Costo Directo ($)", value=12000.0)
    comision_pct = st.slider("Comisión MeLi (%)", 10.0, 35.0, 28.0)
    
    margen_valor = pvp_calc - costo_calc - (pvp_calc * (comision_pct / 100.0))
    st.metric("Margen Neto Estimado", f"${margen_valor:,.2f}")

# ------------------------------------------
# TAB 7: PUBLICADOR DIRECTO
# ------------------------------------------
with tabs[6]:
    st.header("📦 Publicación Directa en Catálogo (`POST /items`)")
    
    cat_default = st.session_state["selected_item_data"].get("catalog_product_id", "MLA20491823") if st.session_state["selected_item_data"] else "MLA20491823"
    
    col_p1, col_p2 = st.columns(2)
    cat_id_input = col_p1.text_input("Catalog Product ID", value=cat_default)
    precio_pub_input = col_p2.number_input("Precio de Venta ($ ARS)", value=38000.0)
    
    col_p3, col_p4 = st.columns(2)
    tipo_listado = col_p3.selectbox("Modalidad de Publicación", ["gold_pro (Premium / Cuotas)", "gold_special (Clásica)"])
    code_listado = "gold_pro" if "gold_pro" in tipo_listado else "gold_special"
    stock_input = col_p4.number_input("Stock Inicial", min_value=1, value=5)
    
    st.markdown("---")
    if st.button("🚀 PUBLICAR EN MERCADO LIBRE", type="primary", use_container_width=True):
        with st.spinner("Procesando publicación..."):
            ok, resp = publicar_item_en_catalogo(
                catalog_product_id=cat_id_input,
                precio_venta=precio_pub_input,
                listing_type_id=code_listado,
                quantity=int(stock_input),
                access_token=st.session_state.get("access_token")
            )
            if ok:
                st.success(resp["message"])
                st.markdown(f"👉 [Ver Publicación en Mercado Libre]({resp['permalink']})")
            else:
                st.error(resp)
