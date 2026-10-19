import streamlit as st
import pandas as pd
import requests
import re
import json

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

def publicar_definitivo_multimodo(payload_dict: dict, access_token: str):
    if not access_token:
        return False, "⚠️ Debés conectar Mercado Libre o ingresar un Access Token directo."

    url = "https://api.mercadolibre.com/items"
    headers = {
        "Authorization": f"Bearer {access_token.strip()}",
        "Content-Type": "application/json"
    }

    # Intentar Petición Directa Estandarizada
    try:
        res = requests.post(url, json=payload_dict, headers=headers, timeout=12)
        if res.status_code in [200, 201]:
            data = res.json()
            url_created = construir_url_canonica_meli(data.get("id"), data.get("permalink", ""))
            return True, f"✅ ¡Publicación creada con éxito! ID: **{data.get('id')}** — [Abrir en Mercado Libre]({url_created})"
        
        err_json = res.json() if res.content else {}
        err_msg = str(err_json.get("message", f"Error HTTP {res.status_code}"))

        # Reintento con Atributo FAMILY_NAME inyectado en attributes
        if "family_name" in err_msg.lower() or res.status_code == 400:
            payload_alt = payload_dict.copy()
            attrs = payload_alt.get("attributes", [])
            fam_val = payload_alt.get("title", "Mueble Centro Estant")[:30]
            attrs.append({"id": "FAMILY_NAME", "value_name": fam_val})
            payload_alt["attributes"] = attrs
            
            res_alt = requests.post(url, json=payload_alt, headers=headers, timeout=12)
            if res_alt.status_code in [200, 201]:
                data_alt = res_alt.json()
                url_created_alt = construir_url_canonica_meli(data_alt.get("id"), data_alt.get("permalink", ""))
                return True, f"✅ ¡Publicación creada con éxito (Atributo Familia)! ID: **{data_alt.get('id')}** — [Abrir en Mercado Libre]({url_created_alt})"

        causes = [c.get("message", "") for c in err_json.get("cause", []) if c.get("message")]
        if causes:
            err_msg += " (" + ", ".join(causes) + ")"
        return False, f"❌ Error API MeLi ({res.status_code}): {err_msg}"
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
st.caption("v97.0 — Panel Operativo Oficial MeLi (Motor Definitivo v97)")

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
            costo_envio_sim = st.number_input("Costo Logística Oficial (Mercado Envíos Volumétrico)", min_value=0.0, value=28500.0, step=500.0)
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
            {"Concepto": "Costo Logística Volumétrico MeLi (Bulto Pesado)", "Monto ($)": -costo_envio_sim, "Porcentaje": f"-{(costo_envio_sim/pvp_sim)*100:.1f}%"},
            {"Concepto": f"Ingresos Brutos IIBB ({pct_iibb_sim}%)", "Monto ($)": -m_iibb, "Porcentaje": f"-{pct_iibb_sim}%"},
            {"Concepto": f"IVA / Retenciones ({pct_iva_sim}%)", "Monto ($)": -m_iva, "Porcentaje": f"-{pct_iva_sim}%"},
            {"Concepto": f"Costo Producto Efectivo (-{pct_descuento_proveedor}% desc.)", "Monto ($)": -costo_prod_input, "Porcentaje": f"-{(costo_prod_input/pvp_sim)*100:.1f}%"},
            {"Concepto": "RESULTADO NETO FINAL", "Monto ($)": ganancia_neta, "Porcentaje": f"{margen_pct:.1f}%"}
        ])
        st.table(df_desglose)

# ------------------------------------------
# SOLAPA 2: COMPETENCIA
# ------------------------------------------
with tabs[1]:
    st.header("🏆 Analizador de Competencia por Catálogo MeLi")
    st.write("Seleccione un **EAN de la Lista Gold** o ingrese un código/URL manualmente:")

    opciones_ean_gold = extraer_opciones_ean_lista_gold()
    query_ean_comp = "7798274755803"

    if opciones_ean_gold:
        st.subheader("📋 Seleccionar Producto desde la Lista Gold Cargada")
        labels_gold = [op[0] for op in opciones_ean_gold]
        selected_label = st.selectbox("EAN / Producto en Lista Gold", labels_gold)
        
        if selected_label:
            for lbl, ean_val in opciones_ean_gold:
                if lbl == selected_label:
                    query_ean_comp = ean_val
                    break
        st.markdown("---")

    col_e1, col_e2 = st.columns([3, 1])
    with col_e1:
        query_ean_comp = st.text_input("Buscador Manual (EAN / Catálogo / URL)", value=query_ean_comp)
    with col_e2:
        st.write("")
        btn_buscar_ean = st.button("🔎 BUSCAR COMPETIDORES", type="primary", use_container_width=True)

    if btn_buscar_ean or query_ean_comp:
        found_gold_comp, costo_gold_comp, desc_gold_comp, art_gold_comp = buscar_costo_y_titulo_en_lista_gold(query_ean_comp)

        with st.spinner("Buscando vendedores competidores en Mercado Libre..."):
            cat_id_comp, title_comp, items_comp = buscar_competencia_integral_ean(query_ean_comp, st.session_state["access_token"])

        if not found_gold_comp:
            st.markdown(f'<div class="badge-missing">❌ El código "{query_ean_comp.strip()}" NO está registrado en la Lista Gold cargada.</div><br>', unsafe_allow_html=True)
        else:
            st.success(f"✅ Costo registrado en Lista Gold: **${costo_gold_comp:,.2f}** ({desc_gold_comp} - {art_gold_comp})")

        if items_comp:
            st.subheader(f"📊 Vendedores Competidores Detectados ({len(items_comp)} publicaciones)")
            
            data_t = []
            for item in items_comp:
                q_c = item.get("installments_qty", 1)
                raw_tipo = str(item.get("listing_type_id", "gold_pro"))
                tipo_formateado = "Premium (Cuotas)" if "pro" in raw_tipo else ("Clásica" if "special" in raw_tipo else raw_tipo)

                data_t.append({
                    "Nombre Vendedor": item.get("vendedor_name"),
                    "Publicación ID": item.get("id"),
                    "Título Publicación": item.get("title"),
                    "Precio ($ ARS)": item.get("price", 0.0),
                    "Financiación": f"{q_c}x sin interés" if q_c > 1 else "1 pago / Contado",
                    "Tipo Listado": tipo_formateado,
                    "Stock": item.get("stock", 0),
                    "Link a MeLi": item.get("permalink")
                })

            df_comp = pd.DataFrame(data_t).sort_values(by="Precio ($ ARS)", ascending=True).reset_index(drop=True)
            
            st.dataframe(
                df_comp,
                column_config={
                    "Link a MeLi": st.column_config.LinkColumn("Enlace Verificado", display_text="Abrir Publicación 🔗")
                },
                use_container_width=True
            )

            ganador_bb = df_comp.iloc[0]
            pvp_ganador_bb = float(ganador_bb["Precio ($ ARS)"])
            link_ganador_bb = ganador_bb["Link a MeLi"]
            pub_id_win = ganador_bb["Publicación ID"]
            tipo_win = ganador_bb["Tipo Listado"]

            st.session_state["selected_pub_data"] = {
                "catalog_id": cat_id_comp,
                "title": ganador_bb["Título Publicación"],
                "price": pvp_ganador_bb
            }

            pct_com_win = 33.59 if "Premium" in tipo_win else 14.5
            costo_envio_win = 28500.0 if pvp_ganador_bb >= 30000.0 else 0.0
            
            deducc_com_win = pvp_ganador_bb * (pct_com_win / 100.0)
            deducc_iibb_win = pvp_ganador_bb * 0.035
            deducc_iva_win = pvp_ganador_bb * 0.21
            
            costo_max_necesario_win = pvp_ganador_bb - deducc_com_win - deducc_iibb_win - deducc_iva_win - costo_envio_win
            
            pct_desc_requerido = 0.0
            if found_gold_comp and costo_gold_comp > 0:
                if costo_gold_comp > costo_max_necesario_win:
                    pct_desc_requerido = ((costo_gold_comp - costo_max_necesario_win) / costo_gold_comp) * 100.0

            st.markdown("### 🎯 Estrategia e Igualación de Costos para Ganar el Buy Box")
            mb1, mb2, mb3 = st.columns(3)
            mb1.metric("🥇 PVP Ganador Buy Box", f"${pvp_ganador_bb:,.2f}", f"ID: {pub_id_win}")
            mb2.metric("🎯 Costo Máximo Necesario en Gold", f"${costo_max_necesario_win:,.2f}")
            mb3.metric("📉 % Descuento Necesario en Lista Gold", f"{pct_desc_requerido:.1f}%" if pct_desc_requerido > 0 else "0.0% (Viable)")

            st.markdown("#### 🧾 Desglose de Deducciones del Líder del Buy Box")
            df_desglose_bb = pd.DataFrame([
                {"Concepto": "PVP Ganador Objetivo", "Monto ($)": pvp_ganador_bb, "Porcentaje": "100.0%"},
                {"Concepto": f"Comisión / Financiación MeLi ({pct_com_win}%)", "Monto ($)": -deducc_com_win, "Porcentaje": f"-{pct_com_win}%"},
                {"Concepto": "Envío Logística Bulto Pesado", "Monto ($)": -costo_envio_win, "Porcentaje": f"-{(costo_envio_win/pvp_ganador_bb)*100:.1f}%"},
                {"Concepto": "Ingresos Brutos IIBB (3.5%)", "Monto ($)": -deducc_iibb_win, "Porcentaje": "-3.5%"},
                {"Concepto": "IVA / Retenciones (21.0%)", "Monto ($)": -deducc_iva_win, "Porcentaje": "-21.0%"},
                {"Concepto": "COSTO MÁXIMO SOPORTADO EN LISTA GOLD", "Monto ($)": costo_max_necesario_win, "Porcentaje": f"{(costo_max_necesario_win/pvp_ganador_bb)*100:.1f}%"}
            ])
            st.table(df_desglose_bb)

            st.markdown(f"👉 **Enlace directo a la publicación líder:** [{ganador_bb['Título Publicación']}]({link_ganador_bb})")
        else:
            st.warning("No se encontraron publicaciones competidoras activas para este código EAN o Catalog ID.")

# ------------------------------------------
# SOLAPA 3: PUBLICADOR DIRECTO (MOTOR CASCADA DE INTEGRACIÓN)
# ------------------------------------------
with tabs[2]:
    st.header("🚀 Publicador Directo Mercado Libre (`POST /items`)")
    st.write("Alta de publicaciones oficiales con **Motor Multimodo de Auto-Resolución**:")

    pub_data_state = st.session_state.get("selected_pub_data", {})

    c_f1, c_f2 = st.columns(2)
    with c_f1:
        titulo_input = st.text_input("Título de la Publicación (Máx 60 car.)", value=pub_data_state.get("title", "Alacena 120cm 3 Puertas Centro Estant blanco"))
        nombre_cat_sel = st.selectbox("Categoría MeLi", list(CATEGORIAS_MELI.keys()), index=0)
        categoria_id_val = CATEGORIAS_MELI[nombre_cat_sel]
        
    with c_f2:
        precio_val = st.number_input("Precio de Venta Objetivo ($ ARS)", min_value=100.0, value=float(pub_data_state.get("price", 129998.0)), step=500.0)
        stock_val = st.number_input("Stock Inicial", min_value=1, value=5)
        tipo_listado_val = st.selectbox("Modalidad de Listado", ["gold_special", "gold_pro"], format_func=lambda x: "Clásica (gold_special)" if x=="gold_special" else "Premium / Cuotas (gold_pro)")

    st.markdown("---")
    st.subheader("🛠️ Atributos Básicos del Producto")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        marca_val = st.text_input("Marca (BRAND)", value="Centro Estant")
    with col_t2:
        modelo_val = st.text_input("Modelo (MODEL)", value="al120bl")

    payload_base = {
        "title": titulo_input[:60],
        "category_id": categoria_id_val,
        "price": round(float(precio_val), 2),
        "currency_id": "ARS",
        "available_quantity": int(stock_val),
        "buying_mode": "buy_it_now",
        "listing_type_id": tipo_listado_val,
        "condition": "new",
        "site_id": "MLA",
        "attributes": [
            {"id": "BRAND", "value_name": marca_val},
            {"id": "MODEL", "value_name": modelo_val}
        ],
        "pictures": [
            {"source": "https://http2.mlstatic.com/D_NQ_NP_907099-MLA51449852230_092022-F.jpg"}
        ]
    }

    st.markdown("#### 📝 JSON a Enviar:")
    json_editado_raw = st.text_area("JSON enviado a `POST /items`:", value=json.dumps(payload_base, indent=2, ensure_ascii=False), height=260)

    st.markdown("---")
    if st.button("🚀 ENVIAR PUBLICACIÓN A MERCADO LIBRE", type="primary", use_container_width=True):
        with st.spinner("Procesando publicación en Mercado Libre..."):
            try:
                payload_final = json.loads(json_editado_raw)
                exito_pub, msg_pub = publicar_definitivo_multimodo(payload_final, st.session_state.get("access_token"))
                if exito_pub:
                    st.success(msg_pub)
                else:
                    st.error(msg_pub)
            except Exception as json_err:
                st.error(f"❌ JSON inválido: Formato con errores de sintaxis ({str(json_err)})")
