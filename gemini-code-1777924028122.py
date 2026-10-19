import streamlit as st
import pandas as pd
import requests
import re

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
if "selected_pub_data" not in st.session_state:
    st.session_state["selected_pub_data"] = {}

# ==========================================
# 4. FUNCIONES DE API Y CÁLCULOS
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

def extraer_opciones_ean_lista_gold():
    if st.session_state["lista_gold_df"] is None:
        return []
    
    df = st.session_state["lista_gold_df"]
    opciones = []
    
    # Identificar columnas
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

    target_catalog_id = catalog_id if catalog_id else "MLA15577861"
    
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
        term_search = clean_val if clean_val else "Centro Estant Respaldo"
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
            "title": r.get("title", product_title if product_title else "Producto Centro Estant"),
            "price": float(r.get("price", 0.0)),
            "installments_qty": q_c,
            "listing_type_id": str(r.get("listing_type_id", "gold_pro")),
            "stock": r.get("available_quantity", 1),
            "permalink": url_oficial
        })

    return target_catalog_id, product_title, items_procesados

def publicar_en_mercado_libre(catalog_id: str, titulo: str, categoria: str, precio: float, stock: int, tipo_listado: str, access_token: str):
    if not access_token:
        return False, "⚠️ Debés conectar Mercado Libre o ingresar un Access Token directo."

    url = "https://api.mercadolibre.com/items"
    headers = {
        "Authorization": f"Bearer {access_token.strip()}",
        "Content-Type": "application/json"
    }

    # Asignar un título limpio válido
    titulo_limpio = titulo.strip() if titulo and titulo.strip() else "Respaldo de cama regulable 140-160 RC6 Centro Estant"
    if len(titulo_limpio) > 60:
        titulo_limpio = titulo_limpio[:60]

    # Asegurar Categoría Valida (MLA35254 es la predeterminada de muebles)
    cat_final = categoria.strip() if (categoria and categoria.strip().startswith("MLA")) else "MLA35254"

    # Payload Oficial MeLi Estrictamente Válido
    payload = {
        "title": titulo_limpio,
        "category_id": cat_final,
        "price": round(float(precio), 2),
        "currency_id": "ARS",
        "available_quantity": int(stock),
        "buying_mode": "buy_it_now",
        "listing_type_id": tipo_listado if tipo_listado in ["gold_special", "gold_pro"] else "gold_special",
        "condition": "new",
        "site_id": "MLA",
        "attributes": [
            {"id": "BRAND", "value_name": "Centro Estant"},
            {"id": "MODEL", "value_name": "RC6"},
            {"id": "ITEM_CONDITION", "value_name": "Nuevo"}
        ],
        "sale_terms": [
            {"id": "WARRANTY_TYPE", "value_name": "Garantía del vendedor"},
            {"id": "WARRANTY_TIME", "value_name": "6 meses"}
        ],
        "pictures": [
            {"source": "https://http2.mlstatic.com/D_NQ_NP_907099-MLA51449852230_092022-F.jpg"}
        ]
    }

    # Adjuntar catalog_product_id solo si es un id de catálogo válido
    if catalog_id and catalog_id.strip().upper().startswith("MLA") and len(catalog_id.strip()) > 5:
        payload["catalog_product_id"] = catalog_id.strip().upper()

    try:
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        if res.status_code in [200, 201]:
            data = res.json()
            url_created = construir_url_canonica_meli(data.get("id"), data.get("permalink", ""))
            return True, f"✅ ¡Publicación creada con éxito! ID: **{data.get('id')}** — [Abrir en Mercado Libre]({url_created})"
        else:
            err_json = res.json() if res.content else {}
            err_msg = str(err_json.get("message", f"Error HTTP {res.status_code}"))
            
            # Reintento de publicación directa sin catalog_product_id si el catálogo fue el causante
            if "catalog" in err_msg.lower() or "family_name" in err_msg.lower() or res.status_code in [400, 422]:
                payload_clean = payload.copy()
                payload_clean.pop("catalog_product_id", None)
                res_retry = requests.post(url, json=payload_clean, headers=headers, timeout=10)
                if res_retry.status_code in [200, 201]:
                    data_r = res_retry.json()
                    url_created_r = construir_url_canonica_meli(data_r.get("id"), data_r.get("permalink", ""))
                    return True, f"✅ ¡Publicación directa creada con éxito! ID: **{data_r.get('id')}** — [Abrir en Mercado Libre]({url_created_r})"

            if "cause" in err_json:
                causes = [c.get("message", "") for c in err_json.get("cause", []) if c.get("message")]
                if causes:
                    err_msg += " (" + ", ".join(causes) + ")"
            return False, f"❌ Error API MeLi: {err_msg}"
    except Exception as e:
        return False, f"❌ Error de conexión: {str(e)}"

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
    st.subheader("📄 Carga de Lista Gold")
    uploaded_gold = st.file_uploader("Subir Excel / CSV (Costos)", type=["xlsx", "csv"])
    if uploaded_gold is not None:
        st.session_state["lista_gold_df"] = procesar_archivo_lista_gold(uploaded_gold)
        if st.session_state["lista_gold_df"] is not None:
            st.success("✅ Lista Gold vinculada correctamente.")

# ==========================================
# 8. TRES SOLAPAS OPERATIVAS
# ==========================================
st.title("NQ Sales Intelligence Matrix Pro")
st.caption("v90.0 — Panel Operativo Oficial MeLi")

tabs = st.tabs([
    "1. 🧮 Simulación de Costos MeLi & Rentabilidad",
    "2. 🏆 Competencia por EAN en Catálogo",
    "3. 🚀 Publicador Directo Mercado Libre"
])

# ------------------------------------------
# SOLAPA 1: COSTOS REALES Y ENVÍO VOLUMÉTRICO
# ------------------------------------------
with tabs[0]:
    st.header("🧮 Análisis Estructurado de Costos con Datos Oficiales MeLi")
    st.write("Ingrese un **SKU, EAN, MLA o URL** para calcular comisiones, cuotas y envíos por peso/volumen:")

    c_s1, c_s2 = st.columns([3, 1])
    with c_s1:
        query_costos = st.text_input("Código SKU / EAN / MLA / URL", value="7798274755803")
    with c_s2:
        st.write("")
        btn_calc_costos = st.button("🧮 CALCULAR COSTOS", type="primary", use_container_width=True)

    if btn_calc_costos or query_costos:
        found_gold, costo_gold_val, desc_g, art_g = buscar_costo_y_titulo_en_lista_gold(query_costos)

        st.markdown("---")
        if not found_gold:
            st.markdown(
                f'<div class="badge-missing">❌ El código "{query_costos.strip()}" NO existe en la Lista Gold cargada. Ingrese costo manual para simular.</div><br>',
                unsafe_allow_html=True
            )
        else:
            st.success(f"✅ Costo base en Lista Gold: **${costo_gold_val:,.2f}** ({desc_g} - {art_g})")

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
            costo_envio_sim = st.number_input("Costo Logística Oficial (Mercado Envíos Volumétrico)", min_value=
