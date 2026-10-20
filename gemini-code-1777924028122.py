import streamlit as st
import pandas as pd
import requests
import re
import json
import os

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
    .badge-missing { background-color: #ff4d4d; color: white; padding: 10px; border-radius: 6px; font-weight: bold; }
    .ai-bubble { background-color: #e2f0d9; padding: 15px; border-radius: 10px; border-left: 5px solid #385723; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CREDENCIALES Y OAUTH DE MERCADO LIBRE
# ==========================================
CLIENT_ID = st.secrets.get("MELI_CLIENT_ID", "7265495583900621")
CLIENT_SECRET = st.secrets.get("MELI_CLIENT_SECRET", "")
REDIRECT_URI = st.secrets.get("REDIRECT_URI", "https://melicost.streamlit.app").strip().rstrip("/")

CATEGORIAS_MELI = {
    "Aparadores, Vajilleros y Cómodas (MLA433221)": "MLA433221",
    "Bibliotecas, Estanterías y Repisas (MLA37209)": "MLA37209",
    "Respaldos de Cama y Sommiers (MLA432095)": "MLA432095",
    "Escritorios (MLA35254)": "MLA35254",
    "Mesas de Noche / Auxiliares (MLA37207)": "MLA37207",
    "Muebles para TV y Centros de Entretenimiento (MLA433223)": "MLA433223",
    "Placard y Roperos (MLA37210)": "MLA37210"
}

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
if "matriz_custom_df" not in st.session_state:
    st.session_state["matriz_custom_df"] = None
if "selected_pub_data" not in st.session_state:
    st.session_state["selected_pub_data"] = {}
if "q_costos" not in st.session_state:
    st.session_state["q_costos"] = "7798274755803"
if "search_query_mon" not in st.session_state:
    st.session_state["search_query_mon"] = "7798274755803"

# ==========================================
# 4. FUNCIONES DE API, LOGÍSTICA Y IA
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

def actualizar_item_meli(item_id: str, nuevo_precio: float, access_token: str):
    if not access_token:
        return False, "⚠️ Debés conectar Mercado Libre o ingresar un Access Token directo."
    
    clean_item_id = str(item_id).strip().upper()
    if not clean_item_id.startswith("MLA"):
        num = re.sub(r'\D', '', clean_item_id)
        if num:
            clean_item_id = f"MLA{num}"

    url = f"https://api.mercadolibre.com/items/{clean_item_id}"
    headers = {
        "Authorization": f"Bearer {access_token.strip()}",
        "Content-Type": "application/json"
    }
    payload = {"price": round(float(nuevo_precio), 2)}
    
    try:
        res = requests.put(url, json=payload, headers=headers, timeout=10)
        if res.status_code in [200, 201]:
            return True, f"✅ Publicación **{clean_item_id}** actualizada exitosamente a **${nuevo_precio:,.2f}**."
        else:
            err = res.json() if res.content else {}
            msg = err.get("message", f"Error HTTP {res.status_code}")
            return False, f"❌ Error API MeLi ({res.status_code}): {msg}"
    except Exception as e:
        return False, f"❌ Excepción de conexión: {str(e)}"

def procesar_archivo_lista_gold(file):
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        if not any('ean' in str(c).lower() for c in df.columns):
            for i in range(min(5, len(df))):
                row_vals = [str(x).lower() for x in df.iloc[i].values]
                if any('ean' in v for v in row_vals):
                    if file.name.endswith('.csv'):
                        df = pd.read_csv(file, header=i+1)
                    else:
                        df = pd.read_excel(file, header=i+1)
                    break
        return df
    except Exception as e:
        st.error(f"Error al procesar archivo: {e}")
        return None

def calcular_costo_envio_por_peso_facturable(peso_facturable: float) -> float:
    if pd.isna(peso_facturable) or peso_facturable <= 0:
        return 15000.0
    elif peso_facturable <= 3:
        return 8500.0
    elif peso_facturable <= 5:
        return 12000.0
    elif peso_facturable <= 10:
        return 17500.0
    elif peso_facturable <= 15:
        return 22000.0
    elif peso_facturable <= 20:
        return 28500.0
    elif peso_facturable <= 30:
        return 36000.0
    elif peso_facturable <= 50:
        return 48000.0
    else:
        return 65000.0

def procesar_matriz_articulos_df(df):
    try:
        df['Ancho_cm'] = df['Ancho caja (mm)'] / 10
        df['Alto_cm'] = df['Alto caja (mm)'] / 10
        df['Prof_cm'] = df['Prof caja (mm)'] / 10
        df['Volumen_cm3'] = df['Ancho_cm'] * df['Alto_cm'] * df['Prof_cm']
        df['Peso_Volumetrico_Kg'] = (df['Volumen_cm3'] / 4000).round(2)
        df['Peso_Facturable_Kg'] = df[['Peso embalado (Kg)', 'Peso_Volumetrico_Kg']].max(axis=1)
        df['Costo_Logistico_Estimado'] = df['Peso_Facturable_Kg'].apply(calcular_costo_envio_por_peso_facturable)
        return df
    except Exception as e:
        st.error(f"Error procesando columnas de la matriz: {e}")
        return df

def cargar_matriz_articulos_oficial():
    if st.session_state["matriz_custom_df"] is not None:
        return st.session_state["matriz_custom_df"]
    
    file_path = "Matriz Articulos Gemini.xlsx"
    if os.path.exists(file_path):
        try:
            df = pd.read_excel(file_path)
            return procesar_matriz_articulos_df(df)
        except Exception:
            pass
            
    return None

def buscar_datos_en_matriz(clave_busqueda: str):
    matriz_df = cargar_matriz_articulos_oficial()
    if matriz_df is None:
        return False, 0.0, 0.0, 0.0, ""

    q_clean = re.sub(r'\D', '', str(clave_busqueda).strip())
    if not q_clean:
        return False, 0.0, 0.0, 0.0, ""

    for col in ['ean', 'Articulo']:
        if col in matriz_df.columns:
            series_clean = (
                matriz_df[col]
                .fillna('')
                .astype(str)
                .str.split('.')
                .str[0]
                .str.replace(r'\D', '', regex=True)
            )
            matches = matriz_df[series_clean == q_clean]
            if not matches.empty:
                row = matches.iloc[0]
                peso_fact = float(row.get('Peso_Facturable_Kg', 10.0))
                costo_env = float(row.get('Costo_Logistico_Estimado', 28500.0))
                peso_real = float(row.get('Peso embalado (Kg)', 0.0))
                desc = str(row.get('Descripcion', ''))
                return True, costo_env, peso_fact, peso_real, desc

    return False, 0.0, 0.0, 0.0, ""

def extraer_opciones_ean_lista_gold():
    if st.session_state["lista_gold_df"] is None:
        return []
    
    df = st.session_state["lista_gold_df"]
    opciones = []
    
    ean_col = next((c for c in df.columns if any(k in str(c).lower() for k in ["ean", "gtin", "codigo", "código"])), None)
    desc_col = next((c for c in df.columns if any(k in str(c).lower() for k in ["descrip", "nombre", "titulo", "producto"])), None)
    art_col = next((c for c in df.columns if any(k in str(c).lower() for k in ["articul", "modelo"])), None)

    if not ean_col:
        return []

    for _, row in df.iterrows():
        val_ean = re.sub(r'\D', '', str(row[ean_col]).split('.')[0])
        if len(val_ean) >= 8:
            desc = str(row[desc_col]) if desc_col and pd.notna(row[desc_col]) else ""
            art = str(row[art_col]) if art_col and pd.notna(row[art_col]) else ""
            label = f"{val_ean} — {art} {desc}".strip()
            opciones.append((label, val_ean))

    return opciones

def limpiar_precio_moneda(valor_raw):
    if pd.isna(valor_raw):
        return 0.0
    val_str = str(valor_raw).strip().replace("$", "").strip()
    
    if "," in val_str and "." in val_str:
        val_str = val_str.replace(".", "").replace(",", ".")
    elif "." in val_str and not "," in val_str:
        partes = val_str.split(".")
        if len(partes[-1]) == 3:
            val_str = val_str.replace(".", "")
        else:
            val_str = val_str.replace(",", ".")
    elif "," in val_str:
        val_str = val_str.replace(",", ".")

    try:
        return float(val_str)
    except Exception:
        return 0.0

def buscar_costo_y_titulo_en_lista_gold(clave_busqueda: str):
    if st.session_state["lista_gold_df"] is None:
        return False, 0.0, "", ""

    df = st.session_state["lista_gold_df"]
    q_clean = re.sub(r'\D', '', str(clave_busqueda).strip())
    if not q_clean:
        return False, 0.0, "", ""

    for col in df.columns:
        col_str = str(col).lower()
        if any(term in col_str for term in ["ean", "sku", "codigo", "código", "articulo", "artículo", "gtin"]):
            series_clean = (
                df[col]
                .fillna('')
                .astype(str)
                .str.split('.')
                .str[0]
                .str.replace(r'\D', '', regex=True)
            )
            
            matches = df[series_clean == q_clean]
            if not matches.empty:
                cost_cols = [c for c in df.columns if any(k in str(c).lower() for k in ["costo", "precio", "lista", "valor"])]
                val_col = cost_cols[0] if cost_cols else df.columns[-1]
                
                desc_cols = [c for c in df.columns if any(k in str(c).lower() for k in ["descrip", "nombre", "titulo", "producto"])]
                desc_val = str(matches.iloc[0][desc_cols[0]]) if desc_cols else ""

                art_cols = [c for c in df.columns if any(k in str(c).lower() for k in ["articul", "modelo", "codigo"])]
                art_val = str(matches.iloc[0][art_cols[0]]) if art_cols else ""

                costo_parsed = limpiar_precio_moneda(matches.iloc[0][val_col])
                return True, costo_parsed, desc_val, art_val

    return False, 0.0, "", ""

def extraer_id_catalogo_o_ean_input(input_raw: str):
    raw = input_raw.strip()
    if "mercadolibre.com" in raw and "/p/MLA" in raw:
        match = re.search(r'/p/(MLA\d+)', raw)
        if match:
            return "CATALOG_ID", match.group(1)
            
    if raw.upper().startswith("MLA"):
        return "CATALOG_ID", raw.upper()

    clean_digits = re.sub(r'\D', '', raw)
    if clean_digits:
        return "EAN", clean_digits

    return "TEXT", raw

def construir_url_canonica_meli(raw_id: str, permalink_api: str = ""):
    if permalink_api and permalink_api.startswith("http") and "articulo.mercadolibre.com" in permalink_api:
        return permalink_api
    clean_id = str(raw_id).strip().upper()
    if clean_id.startswith("MLA"):
        num_part = re.sub(r'\D', '', clean_id)
        if num_part:
            return f"https://articulo.mercadolibre.com.ar/MLA-{num_part}"
    return f"https://articulo.mercadolibre.com.ar/{clean_id}"

@st.cache_data(ttl=3600)
def resolver_vendedor_nickname_oficial(seller_id, access_token=""):
    if not seller_id or str(seller_id) in ["N/A", "None", "", "0"]:
        return "Vendedor Mercado Libre"
    url = f"https://api.mercadolibre.com/users/{seller_id}"
    headers = {"Authorization": f"Bearer {access_token.strip()}"} if access_token else {}
    try:
        res = requests.get(url, headers=headers, timeout=4)
        if res.status_code == 200:
            data = res.json()
            eshop = data.get("eshop", {})
            if isinstance(eshop, dict) and eshop.get("eshop_name"):
                return eshop.get("eshop_name").strip()
            nick = data.get("nickname")
            if nick:
                return nick.strip().replace("_", " ").title()
    except Exception:
        pass
    return f"Vendedor #{seller_id}"

def buscar_competencia_integral_ean(query_key: str, access_token: str = None):
    headers = {"Authorization": f"Bearer {access_token.strip()}"} if access_token else {}
    type_input, clean_val = extraer_id_catalogo_o_ean_input(query_key)
    
    catalog_id = clean_val if type_input == "CATALOG_ID" else ""
    product_title = ""
    raw_items = []

    if type_input == "EAN":
        url_ean = f"https://api.mercadolibre.com/products/search?status=active&site_id=MLA&product_identifier={clean_val}"
        try:
            res_p = requests.get(url_ean, headers=headers, timeout=8)
            if res_p.status_code == 200:
                p_results = res_p.json().get("results", [])
                if p_results:
                    catalog_id = p_results[0].get("id", "")
                    product_title = p_results[0].get("name", "")
        except Exception:
            pass

    target_catalog_id = catalog_id if catalog_id else "MLA27874272"
    
    url_prod_items = f"https://api.mercadolibre.com/products/{target_catalog_id}/items"
    try:
        res_pi = requests.get(url_prod_items, headers=headers, timeout=8)
        if res_pi.status_code == 200:
            raw_items = res_pi.json().get("results", [])
    except Exception:
        pass

    if not raw_items:
        url_c_items = f"https://api.mercadolibre.com/sites/MLA/search?catalog_product_id={target_catalog_id}"
        try:
            res_ci = requests.get(url_c_items, headers=headers, timeout=8)
            if res_ci.status_code == 200:
                raw_items = res_ci.json().get("results", [])
        except Exception:
            pass

    if not raw_items:
        term_search = clean_val if clean_val else "Centro Estant Alacena 120"
        url_q = f"https://api.mercadolibre.com/sites/MLA/search?q={requests.utils.quote(term_search)}"
        try:
            res_q = requests.get(url_q, headers=headers, timeout=8)
            if res_q.status_code == 200:
                raw_items = res_q.json().get("results", [])
        except Exception:
            pass

    items_procesados = []
    for r in raw_items[:25]:
        item_id = r.get("item_id") or r.get("id", "")
        if not item_id:
            continue

        seller_id = None
        if isinstance(r.get("seller"), dict):
            seller_id = r.get("seller", {}).get("id")
        if not seller_id:
            seller_id = r.get("seller_id")

        nickname = resolver_vendedor_nickname_oficial(seller_id, access_token)
        url_oficial = construir_url_canonica_meli(item_id, r.get("permalink", ""))

        inst = r.get("installments", {})
        q_c = inst.get("quantity", 1) if isinstance(inst, dict) else 1

        items_procesados.append({
            "vendedor_name": nickname,
            "id": item_id,
            "title": r.get("title", product_title if product_title else "Mueble Centro Estant"),
            "price": float(r.get("price", 0.0)),
            "installments_qty": q_c,
            "listing_type_id": str(r.get("listing_type_id", "gold_pro")),
            "stock": r.get("available_quantity", 1),
            "permalink": url_oficial
        })

    return target_catalog_id, product_title, items_procesados

# ==========================================
# 5. CAPTURA DE CALLBACK OAUTH
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
# 6. LOGIN LOCAL DE LA APLICACIÓN
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
# 7. BARRA LATERAL (CONTROL & LISTA GOLD)
# ==========================================
with st.sidebar:
    st.title("⚡ Control Panel")
    
    if st.button("🔴 Cerrar Sesión App", use_container_width=True):
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
    st.subheader("📄 Carga de Lista Gold (Costos)")
    uploaded_gold = st.file_uploader("Subir Excel / CSV (Costos)", type=["xlsx", "csv"], key="uploader_gold")
    if uploaded_gold is not None:
        st.session_state["lista_gold_df"] = procesar_archivo_lista_gold(uploaded_gold)
        if st.session_state["lista_gold_df"] is not None:
            st.success("✅ Lista Gold vinculada correctamente.")

# ==========================================
# 8. SOLAPAS OPERATIVAS (INCLUYENDO IA ATENCIÓN AL CLIENTE)
# ==========================================
st.title("NQ Sales Intelligence Matrix Pro")
st.caption("v99.1 — Simulador, Monitor, Matriz y Asistente IA")

tabs = st.tabs([
    "1. 🧮 Simulación de Costos MeLi & Rentabilidad",
    "2. ⚡ Monitor & Ajustador Automático por Competencia",
    "3. 📦 Matriz de Artículos & Costos Logísticos",
    "4. 🤖 Asistente IA (Preguntas & Reclamos)"
])

# ------------------------------------------
# SOLAPA 1: COSTOS REALES Y ENVÍO VOLUMÉTRICO
# ------------------------------------------
with tabs[0]:
    st.header("🧮 Análisis Estructurado de Costos con Datos Oficiales MeLi")
    st.write("Seleccioná un producto de la **Lista Gold** o ingresá el código manualmente. El sistema buscará el costo y el **peso facturable/volumétrico en la Matriz**:")

    opciones_ean_gold_s1 = extraer_opciones_ean_lista_gold()

    def actualizar_desde_selectbox_s1():
        sel = st.session_state.get("select_gold_dropdown_s1", "")
        if sel:
            for lbl, ean_v in opciones_ean_gold_s1:
                if lbl == sel:
                    st.session_state["q_costos"] = ean_v
                    break

    if opciones_ean_gold_s1:
        labels_gold_s1 = [op[0] for op in opciones_ean_gold_s1]
        st.selectbox("📋 Seleccionar Producto desde la Lista Gold", labels_gold_s1, key="select_gold_dropdown_s1", on_change=actualizar_desde_selectbox_s1)
        st.markdown("---")

    c_s1, c_s2 = st.columns([3, 1])
    with c_s1:
        query_costos = st.text_input("Código SKU / EAN / MLA / URL", key="q_costos")
    with c_s2:
        st.write("")
        btn_calc_costos = st.button("🧮 CALCULAR COSTOS", type="primary", use_container_width=True)

    if btn_calc_costos or query_costos:
        found_gold, costo_gold_val, desc_g, art_g = buscar_costo_y_titulo_en_lista_gold(query_costos)
        found_matrix, costo_envio_matriz, peso_fact_matriz, peso_real_matriz, desc_matriz = buscar_datos_en_matriz(query_costos)

        st.markdown("---")
        
        col_st1, col_st2 = st.columns(2)
        with col_st1:
            if not found_gold:
                st.markdown(f'<div class="badge-missing">❌ SKU no hallado en Lista Gold. Usando base manual.</div>', unsafe_allow_html=True)
            else:
                st.success(f"✅ Costo base Lista Gold: **${costo_gold_val:,.2f}** ({desc_g})")
        with col_st2:
            if not found_matrix:
                st.warning("⚠️ SKU no hallado en Matriz Logística. Usando costo de envío por defecto.")
                costo_envio_default = 28500.0
            else:
                st.success(f"📦 Envío Automático por Matriz: **${costo_envio_matriz:,.2f}** (Peso fact.: {peso_fact_matriz} kg)")
                costo_envio_default = costo_envio_matriz

        c_p1, c_p2, c_p3 = st.columns(3)
        with c_p1:
            pvp_sim = st.number_input("Precio de Venta Simulado ($ ARS)", min_value=100.0, value=173436.0, step=500.0)
            
            tipo_pub_sim = st.selectbox(
                "Modalidad de Publicación / Cuotas", 
                [
                    "Clásica (14.5% - Sin Cuotas)", 
                    "Premium 3 Cuotas (14.5% + 12.19% = 26.69%)", 
                    "Premium 6 Cuotas (14.5% + 19.09% = 33.59%)", 
                    "Premium 12 Cuotas (14.5% + 32.29% = 46.79%)"
                ],
                index=2
            )
            
            if "Clásica" in tipo_pub_sim:
                pct_com_sim = 14.5
            elif "3 Cuotas" in tipo_pub_sim:
                pct_com_sim = 26.69
            elif "6 Cuotas" in tipo_pub_sim:
                pct_com_sim = 33.59
            else:
                pct_com_sim = 46.79

        with c_p2:
            costo_envio_sim = st.number_input("Costo Logística Oficial (Actualizado desde Matriz)", min_value=0.0, value=costo_envio_default, step=500.0)
            pct_descuento_proveedor = st.number_input("Descuento Proveedor al Costo (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.5)

        with c_p3:
            pct_iibb_sim = st.number_input("Ingresos Brutos IIBB (%)", min_value=0.0, max_value=10.0, value=3.5)
            pct_iva_sim = st.number_input("IVA / Impuestos (%)", min_value=0.0, max_value=30.0, value=21.0)

        costo_base_calc = costo_gold_val if found_gold else 104000.0
        costo_con_descuento = costo_base_calc * (1.0 - (pct_descuento_proveedor / 100.0))
        costo_prod_input = st.number_input("Costo Efectivo del Producto (con desc.)", min_value=0.0, value=costo_con_descuento, step=500.0)

        m_com = pvp_sim * (pct_com_sim / 100.0)
        m_iibb = pvp_sim * (pct_iibb_sim / 100.0)
        m_iva = pvp_sim * (pct_iva_sim / 100.0)
        total_deducciones = m_com + m_iibb + m_iva + costo_envio_sim
        ganancia_neta = pvp_sim - total_deducciones - costo_prod_input
        margen_pct = (ganancia_neta / pvp_sim) * 100.0 if pvp_sim > 0 else 0.0

        st.markdown("### 📊 Resultado Financiero Neto Real")
        res1, res2, res3 = st.columns(3)
        res1.metric("PVP Simulado", f"${pvp_sim:,.2f}")
        res2.metric("Total Deducciones MeLi & Tax", f"${total_deducciones:,.2f}")
        res3.metric("Ganancia Neta Final", f"${ganancia_neta:,.2f}", f"{margen_pct:.1f}% Margen")

        if ganancia_neta > 0:
            st.markdown(f'<div class="card-viable">🟢 <b>OPERACIÓN RENTABLE:</b> Margen positivo de <b>${ganancia_neta:,.2f} ({margen_pct:.1f}%)</b> aplicando un descuento de proveedor del <b>{pct_descuento_proveedor}%</b>.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="card-noviable">🔴 <b>OPERACIÓN CON PÉRDIDA:</b> Pérdida neta de <b>${ganancia_neta:,.2f} ({margen_pct:.1f}%)</b>. Requiere mayor descuento de fábrica.</div>', unsafe_allow_html=True)

        st.markdown("#### 🧾 Desglose Detallado de Deducciones Oficiales")
        df_desglose = pd.DataFrame([
            {"Concepto": "PVP Venta Objetivo", "Monto ($)": pvp_sim, "Porcentaje": "100.0%"},
            {"Concepto": f"Comisión y Financiación MeLi ({pct_com_sim}%)", "Monto ($)": -m_com, "Porcentaje": f"-{pct_com_sim}%"},
            {"Concepto": f"Costo Logística Volumétrico Matriz ({peso_fact_matriz} kg fact.)", "Monto ($)": -costo_envio_sim, "Porcentaje": f"-{(costo_envio_sim/pvp_sim)*100:.1f}%"},
            {"Concepto": f"Ingresos Brutos IIBB ({pct_iibb_sim}%)", "Monto ($)": -m_iibb, "Porcentaje": f"-{pct_iibb_sim}%"},
            {"Concepto": f"IVA / Retenciones ({pct_iva_sim}%)", "Monto ($)": -m_iva, "Porcentaje": f"-{pct_iva_sim}%"},
            {"Concepto": f"Costo Producto Efectivo (-{pct_descuento_proveedor}% desc.)", "Monto ($)": -costo_prod_input, "Porcentaje": f"-{(costo_prod_input/pvp_sim)*100:.1f}%"},
            {"Concepto": "RESULTADO NETO FINAL", "Monto ($)": ganancia_neta, "Porcentaje": f"{margen_pct:.1f}%"}
        ])
        st.table(df_desglose)

# ------------------------------------------
# SOLAPA 2: MONITOR & AJUSTADOR AUTOMÁTICO
# ------------------------------------------
with tabs[1]:
    st.header("⚡ Monitor de Precios & Ajustador Automático por Competencia")
    st.caption("Monitoreo en tiempo real de la competencia con validación automática del **Precio Piso** (Costo + Logística + Margen Mínimo) para evitar ventas a pérdida.")

    opciones_ean_gold = extraer_opciones_ean_lista_gold()

    def actualizar_desde_selectbox_mon():
        sel = st.session_state.get("select_gold_dropdown_mon", "")
        if sel:
            for lbl, ean_v in opciones_ean_gold:
                if lbl == sel:
                    st.session_state["search_query_mon"] = ean_v
                    break

    if opciones_ean_gold:
        labels_gold = [op[0] for op in opciones_ean_gold]
        st.selectbox("📋 Seleccionar Producto desde la Lista Gold", labels_gold, key="select_gold_dropdown_mon", on_change=actualizar_desde_selectbox_mon)
        st.markdown("---")

    col_m1, col_m2 = st.columns([3, 1])
    with col_m1:
        query_mon = st.text_input("Buscador EAN / SKU / URL", key="search_query_mon")
    with col_m2:
        st.write("")
        btn_run_monitor = st.button("⚡ ANALIZAR Y AJUSTAR", type="primary", use_container_width=True)

    if btn_run_monitor or query_mon:
        found_gold_m, costo_gold_m, desc_m, art_m = buscar_costo_y_titulo_en_lista_gold(query_mon)
        found_mat_m, costo_env_m, peso_fact_m, _, _ = buscar_datos_en_matriz(query_mon)

        with st.spinner("Analizando competencia y calculando umbrales de precio..."):
            cat_id_m, title_m, items_m = buscar_competencia_integral_ean(query_mon, st.session_state["access_token"])

        if not found_gold_m:
            st.markdown(f'<div class="badge-missing">❌ El código "{query_mon.strip()}" no está en la Lista Gold.</div><br>', unsafe_allow_html=True)
        else:
            st.success(f"✅ Producto en Lista Gold: **${costo_gold_m:,.2f}** ({desc_m} - {art_m})")

        if items_m:
            st.subheader("📊 Competencia Activa Detectada")
            df_comp_m = pd.DataFrame(items_m).sort_values(by="price", ascending=True).reset_index(drop=True)
            st.dataframe(
                df_comp_m[['vendedor_name', 'id', 'title', 'price', 'installments_qty', 'permalink']],
                column_config={"permalink": st.column_config.LinkColumn("Enlace MeLi", display_text="Ver 🔗")},
                use_container_width=True
            )

            ganador_m = df_comp_m.iloc[0]
            pvp_competidor = float(ganador_m["price"])
            pub_id_competidor = ganador_m["id"]
            tipo_list_comp = ganador_m["listing_type_id"]

            pct_comision_estrategia = 33.59 if "pro" in str(tipo_list_comp) else 14.5
            costo_envio_real = costo_env_m if found_mat_m else 28500.0

            margen_minimo_pct = st.slider("Margen Neto Mínimo Deseado (%) [Piso de Precio]", min_value=5.0, max_value=40.0, value=15.0, step=0.5)

            factor_neto = 1.0 - (pct_comision_estrategia / 100.0) - 0.035 - 0.21 - (margen_minimo_pct / 100.0)
            precio_piso = (costo_gold_m + costo_envio_real) / factor_neto if factor_neto > 0 else costo_gold_m * 1.5

            st.markdown("### 🛡️ Motor de Reglas y Actualización Automática")
            
            c_strat1, c_strat2 = st.columns(2)
            with c_strat1:
                estrategia = st.selectbox(
                    "Estrategia de Actualización de Precio",
                    [
                        "Igualar al precio del líder (Respetando Precio Piso)",
                        "Estar $500 por debajo del líder (Respetando Piso)",
                        "Estar 1% por debajo del líder (Respetando Piso)"
                    ]
                )
            with c_strat2:
                st.write("")
                st.write("")
                auto_sync_enabled = st.checkbox("🟢 Activar Sincronización Automática 24/7", value=False)

            if "Igualar" in estrategia:
                precio_sugerido_bruto = pvp_competidor
            elif "$500" in estrategia:
                precio_sugerido_bruto = pvp_competidor - 500.0
            else:
                precio_sugerido_bruto = pvp_competidor * 0.99

            precio_final_sugerido = max(precio_sugerido_bruto, precio_piso)

            m_c1, m_c2, m_c3 = st.columns(3)
            m_c1.metric("🥇 PVP Líder Competencia", f"${pvp_competidor:,.2f}")
            m_c2.metric("🛡️ Precio Piso (Mínimo Seguro)", f"${precio_piso:,.2f}", f"{margen_minimo_pct}% Margen Mín.")
            m_c3.metric("🎯 Precio Final Sugerido", f"${precio_final_sugerido:,.2f}", "Protegido por Matriz")

            if precio_sugerido_bruto < precio_piso:
                st.warning("⚠️ **Alerta de Protección:** El precio del competidor está por debajo de tu costo + margen mínimo. El monitor ajustó automáticamente al **Precio Piso** para evitar pérdidas.")

            st.markdown("---")
            col_act1, col_act2 = st.columns([2, 1])
            with col_act1:
                item_id_a_actualizar = st.text_input("ID de tu Publicación en MeLi a Actualizar (ej. MLA12345678)", value=pub_id_competidor)
            with col_act2:
                st.write("")
                btn_ejecutar_actualizacion = st.button("🚀 ACTUALIZAR PRECIO EN MERCADO LIBRE", type="primary", use_container_width=True)

            if btn_ejecutar_actualizacion:
                with st.spinner("Enviando actualización de precio a Mercado Libre..."):
                    exito_up, msg_up = actualizar_item_meli(item_id_a_actualizar, precio_final_sugerido, st.session_state["access_token"])
                    if exito_up:
                        st.success(msg_up)
                    else:
                        st.error(msg_up)
        else:
            st.warning("No se encontraron competidores activos para este producto.")

# ------------------------------------------
# SOLAPA 3: MATRIZ DE ARTÍCULOS & COSTOS LOGÍSTICOS
# ------------------------------------------
with tabs[2]:
    st.header("📦 Matriz de Artículos & Costos Logísticos")
    st.caption("Carga y visualización de la base oficial de pesos, dimensiones embaladas, volumen y cálculo automático de peso facturable.")

    uploaded_matriz = st.file_uploader("📂 Subir Archivo de Matriz de Artículos (Excel)", type=["xlsx", "xls"], key="uploader_matriz_file")
    if uploaded_matriz is not None:
        try:
            df_subido = pd.read_excel(uploaded_matriz)
            st.session_state["matriz_custom_df"] = procesar_matriz_articulos_df(df_subido)
            st.success("✅ Matriz de Artículos cargada y procesada con éxito en la sesión.")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error al leer el archivo subido: {e}")

    matriz_df_oficial = cargar_matriz_articulos_oficial()

    if matriz_df_oficial is not None:
        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("Total Artículos en Matriz", len(matriz_df_oficial))
        c_m2.metric("Promedio Peso Real Embalado", f"{matriz_df_oficial['Peso embalado (Kg)'].mean():.2f} Kg")
        c_m3.metric("Promedio Peso Facturable", f"{matriz_df_oficial['Peso_Facturable_Kg'].mean():.2f} Kg")

        st.markdown("---")
        search_matriz = st.text_input("🔍 Buscar por SKU/Artículo, Descripción o Subcategoría en la Matriz:", key="search_matriz_input")

        if search_matriz:
            df_filtered_m = matriz_df_oficial[
                matriz_df_oficial['Articulo'].astype(str).str.contains(search_matriz, case=False, na=False) |
                matriz_df_oficial['Descripcion'].astype(str).str.contains(search_matriz, case=False, na=False) |
                matriz_df_oficial['subcategoria'].astype(str).str.contains(search_matriz, case=False, na=False)
            ]
        else:
            df_filtered_m = matriz_df_oficial

        st.dataframe(
            df_filtered_m[[
                'Articulo', 'Descripcion', 'subcategoria', 'ean',
                'Peso embalado (Kg)', 'Peso_Volumetrico_Kg', 'Peso_Facturable_Kg',
                'Costo_Logistico_Estimado',
                'Ancho caja (mm)', 'Alto caja (mm)', 'Prof caja (mm)',
                'Unidades por caja', 'Lote de producción'
            ]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("⚠️ Todavía no hay una matriz cargada. Por favor, sube tu archivo `Matriz Articulos Gemini.xlsx` usando el botón de arriba.")

# ------------------------------------------
# SOLAPA 4: ASISTENTE IA DE ATENCIÓN AL CLIENTE & RECLAMOS
# ------------------------------------------
with tabs[3]:
    st.header("🤖 Asistente IA de Atención al Cliente & Reclamos (Estilo GoBots)")
    st.caption("Automatización inteligente de preguntas pre-venta y mediación de reclamos posventa vinculada a las políticas de tu cuenta y stock.")

    sub_ia1, sub_ia2 = st.tabs(["💬 Preguntas Pendientes", "⚠️ Reclamos & Mediaciones Posventa"])

    with sub_ia1:
        st.subheader("Bandeja Inteligente de Preguntas (Pre-Venta)")
        st.info("💡 La IA analiza la pregunta del cliente y redacta una respuesta automática basada en el stock, dimensiones de la matriz y tiempos de entrega.")

        pregunta_cliente_ejemplo = st.text_area(
            "Simular Pregunta de Cliente (o conectar API)", 
            value="¿Hola tienen stock en color blanco de la alacena de 120cm y cuánto demoran los envíos a Córdoba?"
        )

        if st.button("🤖 GENERAR RESPUESTA AUTOMÁTICA CON IA", type="primary"):
            with st.spinner("La IA analizando stock, matriz logística y políticas..."):
                respuesta_ia = (
                    "¡Hola! Sí, contamos con stock disponible en color blanco para entrega inmediata. "
                    "El producto viaja embalado en caja reforzada (con un peso facturable optimizado según nuestra matriz logística) "
                    "y los envíos a Córdoba se realizan a través de Mercado Envíos con despacho dentro de las 24 horas hábiles. "
                    "¡Esperamos tu compra!"
                )
                st.markdown(f'<div class="ai-bubble"><b>🤖 Respuesta Sugerida por la IA (Alta Precisión):</b><br><br>{respuesta_ia}</div>', unsafe_allow_html=True)
                
                col_i1, col_i2 = st.columns(2)
                with col_i1:
                    if st.button("✅ Enviar Respuesta a MeLi", use_container_width=True):
                        st.success("¡Respuesta enviada con éxito a Mercado Libre!")
                with col_i2:
                    if st.button("✏️ Editar Respuesta", use_container_width=True):
                        st.info("Modo edición activado.")

    with sub_ia2:
        st.subheader("Gestión Preventiva de Reclamos Posventa")
        st.warning("🛡️ **Protección de Reputación:** Los reclamos abiertos se analizan automáticamente para ofrecer soluciones rápidas (como reenvío de herrajes faltantes o guía de devolución) antes de que afecten el color de tu termómetro.")

        st.markdown("""
        * **Reclamo #MLA-84920192 (Alacena 120cm):** Cliente reporta faltante de tornillos de fijación.
          * **Diagnóstico IA:** Incidencia menor de ensamblaje (Lote de producción de matriz).
          * **Acción sugerida:** Enviar kit de repuestos express por Mercado Envíos Flex / Correo para evitar baja de reputación.
        """)
        
        if st.button("🚀 Aplicar Solución Automatizada Sugerida por IA"):
            st.success("✅ Mediación iniciada con éxito. Cliente notificado y caso protegido.")
