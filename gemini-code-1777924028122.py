import streamlit as st
import pandas as pd
import requests
import re
import json
import os
import numpy as np

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

CLIENT_ID = st.secrets.get("MELI_CLIENT_ID", "7265495583900621")
CLIENT_SECRET = st.secrets.get("MELI_CLIENT_SECRET", "")
REDIRECT_URI = st.secrets.get("REDIRECT_URI", "https://melicost.streamlit.app").strip().rstrip("/")

# ------------------------------------------------------------------------------
# PARÁMETROS FISCALES Y LOGÍSTICOS OFICIALES (24.5% Impuestos)
# ------------------------------------------------------------------------------
ALICUOTA_IVA = 0.21       # 21% IVA Real
ALICUOTA_IIBB = 0.035     # 3.5% IIBB
TOTAL_IMPUESTOS = ALICUOTA_IVA + ALICUOTA_IIBB  # 24.5% Total

TASAS_CUOTAS = {
    "1 Pago / Clásica": {"comision_base": 0.145, "tasa_finan": 0.000, "divisor": 1 - 0.145 - TOTAL_IMPUESTOS},
    "3 Cuotas Sin Interés": {"comision_base": 0.145, "tasa_finan": 0.085, "divisor": 1 - 0.230 - TOTAL_IMPUESTOS},
    "6 Cuotas Sin Interés": {"comision_base": 0.145, "tasa_finan": 0.129, "divisor": 1 - 0.274 - TOTAL_IMPUESTOS},
    "9 Cuotas Sin Interés": {"comision_base": 0.145, "tasa_finan": 0.173, "divisor": 1 - 0.318 - TOTAL_IMPUESTOS},
    "12 Cuotas Sin Interés": {"comision_base": 0.145, "tasa_finan": 0.208, "divisor": 1 - 0.353 - TOTAL_IMPUESTOS},
}

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
if "q_costos" not in st.session_state:
    st.session_state["q_costos"] = "7798274755803"
if "search_query_mon" not in st.session_state:
    st.session_state["search_query_mon"] = "7798274755803"

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

def calcular_costo_envio_por_peso_facturable(peso_facturable: float, pvp: float = 208000.0) -> float:
    peso = float(peso_facturable) if pd.notna(peso_facturable) and peso_facturable > 0 else 10.0
    if pvp < 33000:
        col_idx = 0
    elif 33000 <= pvp < 50000:
        col_idx = 1
    else:
        col_idx = 2

    if peso <= 0.3:    costos = (8666, 6190, 6790)
    elif peso <= 0.5:     costos = (9506, 6790, 7290)
    elif peso <= 1.0:     costos = (10906, 7790, 8290)
    elif peso <= 1.5:     costos = (11186, 7990, 8590)
    elif peso <= 2.0:     costos = (11606, 8290, 8790)
    elif peso <= 3.0:     costos = (12446, 8890, 9590)
    elif peso <= 4.0:     costos = (13706, 9790, 10890)
    elif peso <= 5.0:     costos = (15106, 10790, 11890)
    elif peso <= 8.0:     costos = (16506, 11790, 13090)
    elif peso <= 10.0:    costos = (17906, 12790, 14190)
    elif peso <= 13.0:    costos = (19306, 13790, 15190)
    elif peso <= 15.0:    costos = (20706, 14790, 16290)
    elif peso <= 20.0:    costos = (24626, 17590, 19390)
    elif peso <= 25.0:    costos = (29246, 20890, 23390)
    elif peso <= 30.0:    costos = (40026, 28590, 32090)
    elif peso <= 40.0:    costos = (45626, 32590, 36990)
    elif peso <= 50.0:    costos = (48146, 34390, 39090)
    elif peso <= 60.0:    costos = (53326, 38090, 43590)
    elif peso <= 70.0:    costos = (55426, 39590, 45490)
    elif peso <= 80.0:    costos = (64106, 45790, 52690)
    elif peso <= 90.0:    costos = (78946, 56390, 65190)
    elif peso <= 100.0:   costos = (90986, 64990, 75090)
    elif peso <= 120.0:   costos = (99246, 70890, 81990)
    elif peso <= 140.0:   costos = (111706, 79790, 92290)
    elif peso <= 160.0:   costos = (124166, 88690, 102690)
    elif peso <= 180.0:   costos = (136486, 97490, 112990)
    else:                 costos = (148946, 106390, 123290)

    return float(costos[col_idx])

def procesar_matriz_articulos_df(df, pvp_referencia: float = 208000.0):
    try:
        df['Ancho_cm'] = df['Ancho caja (mm)'] / 10
        df['Alto_cm'] = df['Alto caja (mm)'] / 10
        df['Prof_cm'] = df['Prof caja (mm)'] / 10
        df['Volumen_cm3'] = df['Ancho_cm'] * df['Alto_cm'] * df['Prof_cm']
        df['Peso_Volumetrico_Kg'] = (df['Volumen_cm3'] / 4000).round(2)
        df['Peso_Facturable_Kg'] = df[['Peso embalado (Kg)', 'Peso_Volumetrico_Kg']].max(axis=1)
        df['Costo_Logistico_Estimado'] = df['Peso_Facturable_Kg'].apply(lambda x: calcular_costo_envio_por_peso_facturable(x, pvp_referencia))
        return df
    except Exception as e:
        return df

def cargar_matriz_articulos_oficial(pvp_referencia: float = 208000.0):
    if st.session_state["matriz_custom_df"] is not None:
        return procesar_matriz_articulos_df(st.session_state["matriz_custom_df"], pvp_referencia)
    file_path = "Matriz Articulos Gemini.xlsx"
    if os.path.exists(file_path):
        try:
            df = pd.read_excel(file_path)
            return procesar_matriz_articulos_df(df, pvp_referencia)
        except Exception:
            pass
    return None

def buscar_datos_en_matriz(clave_busqueda: str, pvp_referencia: float = 208000.0):
    matriz_df = cargar_matriz_articulos_oficial(pvp_referencia)
    if matriz_df is None:
        return False, 0.0, 0.0, 0.0, 0.0, 1, ""

    q_clean = re.sub(r'\D', '', str(clave_busqueda).strip())
    q_raw = str(clave_busqueda).strip().lower()
    
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
            matches = matriz_df[series_clean == q_clean] if q_clean else pd.DataFrame()
            if matches.empty and q_raw:
                matches = matriz_df[matriz_df[col].astype(str).str.lower().str.contains(q_raw, na=False)]
            
            if not matches.empty:
                row = matches.iloc[0]
                peso_real_total = float(row.get('Peso embalado (Kg)', 0.0))
                cant_cajas = int(row.get('Cantidad Cajas', 1)) if pd.notna(row.get('Cantidad Cajas')) and int(row.get('Cantidad Cajas', 1)) > 0 else 1
                
                peso_unitario = peso_real_total / cant_cajas if cant_cajas > 0 else peso_real_total
                tarifa_unit = calcular_costo_envio_por_peso_facturable(peso_unitario, pvp_referencia)
                costo_env_total = tarifa_unit * cant_cajas
                
                desc = str(row.get('Descripcion', ''))
                return True, costo_env_total, peso_unitario, peso_real_total, tarifa_unit, cant_cajas, desc

    return False, 0.0, 0.0, 0.0, 0.0, 1, ""

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
        if len(val_ean) >= 6:
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
    q_raw = str(clave_busqueda).strip().lower()

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
            matches = df[series_clean == q_clean] if q_clean else pd.DataFrame()
            if matches.empty and q_raw:
                matches = df[df[col].astype(str).str.lower().str.contains(q_raw, na=False)]

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

@st.cache_data(ttl=1800)  # Caching para evitar recargas infinitas (loops)
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
    for r in raw_items[:50]:
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
            "stock": int(r.get("available_quantity", 0)),
            "permalink": url_oficial,
            "sold_quantity": int(r.get("sold_quantity", 0)),
            "category_id": r.get("category_id", "MLA372132")
        })

    return target_catalog_id, product_title, items_procesados

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

st.title("NQ Sales Intelligence Matrix Pro")
st.caption("v103.0 — Monitor de Mercado con Stock Disponible (available_quantity) Integrado")

tabs = st.tabs([
    "1. 🧮 Simulación de Costos MeLi & Rentabilidad",
    "2. ⚡ Monitor & Control de Precios (Análisis Inverso)",
    "3. 📊 Monitor de Mercado (Stock, Ventas & Top 15)",
    "4. 📦 Matriz de Artículos & Costos Logísticos",
    "5. 🤖 Asistente IA (Preguntas & Reclamos)"
])

# ------------------------------------------------------------------------------
# TAB 1: SIMULACIÓN DE COSTOS & RENTABILIDAD
# ------------------------------------------------------------------------------
with tabs[0]:
    st.header("🧮 Análisis Estructurado de Costos con Datos Oficiales MeLi")
    st.write("Seleccioná un producto de la **Lista Gold** o ingresá el código. El sistema calcula los fletes por bulto y los coeficientes con el **24,5% de impuestos** (IVA 21% + IIBB 3.5%):")

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
        pvp_default_sugerido = round(costo_gold_val * 2.0, 2) if found_gold else 208000.0
        
        found_mat, costo_env_tot, peso_unit, peso_real_tot, tarifa_unit, cant_cajas_mat, desc_mat = buscar_datos_en_matriz(query_costos, pvp_default_sugerido)

        st.markdown("---")
        col_st1, col_st2 = st.columns(2)
        with col_st1:
            if not found_gold:
                st.markdown(f'<div class="badge-missing">❌ SKU no hallado en Lista Gold. Usando base manual.</div>', unsafe_allow_html=True)
            else:
                st.success(f"✅ Costo base Lista Gold: **${costo_gold_val:,.2f}** ({desc_g})")
        with col_st2:
            if not found_mat:
                st.warning("⚠️ SKU no hallado en Matriz Logística. Usando costo de envío oficial estándar.")
                costo_env_tot_default = 39090.0
                cant_cajas_mat = 1
                peso_unit = 10.0
            else:
                st.success(f"📦 Flete MeLi (ME2): **${costo_env_tot:,.2f}** total ({cant_cajas_mat} bulto/s de {peso_unit:.1f} kg c/u)")
                costo_env_tot_default = costo_env_tot

        c_p1, c_p2, c_p3 = st.columns(3)
        with c_p1:
            pvp_sim = st.number_input("Precio de Venta Simulado ($ ARS)", min_value=100.0, value=pvp_default_sugerido, step=500.0)
            tipo_pub_sim = st.selectbox(
                "Modalidad de Publicación / Cuotas", 
                list(TASAS_CUOTAS.keys()),
                index=0
            )
            info_cuota = TASAS_CUOTAS[tipo_pub_sim]
            pct_com_sim = (info_cuota["comision_base"] + info_cuota["tasa_finan"]) * 100
        with c_p2:
            costo_envio_sim = st.number_input("Costo Logística Total ($)", min_value=0.0, value=costo_env_tot_default, step=500.0)
            pct_descuento_proveedor = st.number_input("Descuento Proveedor al Costo (%)", min_value=0.0, max_value=100.0, value=20.0, step=0.5)
        with c_p3:
            pct_iibb_sim = st.number_input("Ingresos Brutos IIBB (%)", min_value=0.0, max_value=10.0, value=ALICUOTA_IIBB*100)
            pct_iva_sim = st.number_input("IVA Oficial (%)", min_value=0.0, max_value=30.0, value=ALICUOTA_IVA*100)

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
            st.markdown(f'<div class="card-viable">🟢 <b>OPERACIÓN RENTABLE:</b> Margen positivo de <b>${ganancia_neta:,.2f} ({margen_pct:.1f}%)</b>.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="card-noviable">🔴 <b>OPERACIÓN CON PÉRDIDA:</b> Pérdida neta de <b>${ganancia_neta:,.2f} ({margen_pct:.1f}%)</b>.</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# TAB 2: MONITOR & CONTROL DE PRECIOS (ANÁLISIS INVERSO)
# ------------------------------------------------------------------------------
with tabs[1]:
    st.header("⚡ Monitor de Precios & Control de Precios (Análisis Inverso)")
    st.caption("Monitoreo de competencia con alerta de control de precios mínimos y cálculo del importe y porcentaje de descuento necesario.")

    opciones_ean_gold = extraer_opciones_ean_lista_gold()

    def actualizar_desde_selectbox_mon():
        sel = st.session_state.get("select_gold_dropdown_mon", "")
        if sel:
            for lbl, ean_v in opciones_ean_gold:
                if lbl == sel:
                    st.session_state["search_query_mon"] = ean_v
                    break

    if opciones_ean_gold:
        labels_gold_s2 = [op[0] for op in opciones_ean_gold]
        st.selectbox("📋 Seleccionar Producto desde la Lista Gold", labels_gold_s2, key="select_gold_dropdown_mon", on_change=actualizar_desde_selectbox_mon)
        st.markdown("---")

    col_m1, col_m2 = st.columns([3, 1])
    with col_m1:
        query_mon = st.text_input("Buscador EAN / SKU / URL", key="search_query_mon")
    with col_m2:
        st.write("")
        btn_run_monitor = st.button("⚡ ANALIZAR COMPETENCIA", type="primary", use_container_width=True)

    if btn_run_monitor or query_mon:
        found_gold_m, costo_gold_m, desc_m, art_m = buscar_costo_y_titulo_en_lista_gold(query_mon)
        pvp_ref_mon = costo_gold_m * 2.0 if found_gold_m else 208000.0
        found_mat_m, costo_env_m, _, _, _, _, _ = buscar_datos_en_matriz(query_mon, pvp_ref_mon)

        with st.spinner("Analizando competencia y controlando precios..."):
            cat_id_m, title_m, items_m = buscar_competencia_integral_ean(query_mon, st.session_state["access_token"])

        if not found_gold_m:
            st.markdown(f'<div class="badge-missing">❌ El código "{query_mon.strip()}" no está en la Lista Gold.</div><br>', unsafe_allow_html=True)
        else:
            st.success(f"✅ **Costo Lista Gold Oficial:** **${costo_gold_m:,.2f}** ({desc_m} - {art_m})")

        if items_m:
            st.subheader("📊 Competencia Activa Detectada")
            df_comp_m = pd.DataFrame(items_m).sort_values(by="price", ascending=True).reset_index(drop=True)
            df_comp_m['Cuotas'] = df_comp_m['installments_qty'].apply(lambda x: f"{int(x)} cuotas sin interés" if pd.notna(x) and int(x) > 1 else "1 pago / Sin cuotas")
            st.dataframe(
                df_comp_m[['vendedor_name', 'id', 'title', 'price', 'stock', 'Cuotas', 'permalink']],
                column_config={
                    "price": st.column_config.NumberColumn("Precio ($)", format="$%,.2f"),
                    "stock": st.column_config.NumberColumn("Stock Disp.", format="%d"),
                    "permalink": st.column_config.LinkColumn("Enlace MeLi", display_text="Ver 🔗")
                },
                use_container_width=True,
                hide_index=True
            )

# ------------------------------------------------------------------------------
# TAB 3: MONITOR DE MERCADO (STOCK, VENTAS & TOP 15)
# ------------------------------------------------------------------------------
with tabs[2]:
    st.header("📊 Monitor de Mercado (Stock Disponible, Ventas & Top 15)")
    st.markdown("Análisis competitivo en tiempo real rastreando el **stock disponible (`stock`)**, el volumen acumulado de ventas (`sold_quantity`) y la facturación estimada por categoría.")

    col_mkt1, col_mkt2 = st.columns([3, 1])
    with col_mkt1:
        search_term_mkt = st.text_input("Término de Búsqueda de Mercado / Categoría", value="Ropero placard")
    with col_mkt2:
        st.write("")
        btn_refresh_mkt = st.button("🔄 Actualizar Datos Mercado", type="primary", use_container_width=True)

    if search_term_mkt:
        with st.spinner("Rastreando publicaciones, stock y ventas acumuladas en Mercado Libre..."):
            _, _, items_mkt = buscar_competencia_integral_ean(search_term_mkt, st.session_state["access_token"])

        if items_mkt:
            df_mkt = pd.DataFrame(items_mkt)
            df_mkt["facturacion_estimada"] = df_mkt["price"] * df_mkt["sold_quantity"]

            st.markdown("---")
            st.subheader("1. Resumen de Stock, Ventas y Facturación Estimada por Categoría")

            cat_summary = df_mkt.groupby("category_id").agg(
                Publicaciones=("id", "count"),
                Stock_Total_Disponible=("stock", "sum"),
                Unidades_Vendidas=("sold_quantity", "sum"),
                Facturacion_Total=("facturacion_estimada", "sum"),
                Precio_Promedio=("price", "mean")
            ).reset_index()

            total_mkt_fact = cat_summary["Facturacion_Total"].sum()
            cat_summary["Cuota_Mercado_%"] = (cat_summary["Facturacion_Total"] / total_mkt_fact * 100) if total_mkt_fact > 0 else 0

            st.dataframe(
                cat_summary,
                column_config={
                    "category_id": "ID Categoría MeLi",
                    "Publicaciones": st.column_config.NumberColumn("Publicaciones Activas", format="%d"),
                    "Stock_Total_Disponible": st.column_config.NumberColumn("Stock Total Disp.", format="%d"),
                    "Unidades_Vendidas": st.column_config.NumberColumn("Ventas Acum.", format="%d"),
                    "Facturacion_Total": st.column_config.NumberColumn("Facturación Est. ($)", format="$%.0f"),
                    "Precio_Promedio": st.column_config.NumberColumn("Precio Promedio ($)", format="$%.0f"),
                    "Cuota_Mercado_%": st.column_config.NumberColumn("Cuota de Mercado (%)", format="%.1f%%")
                },
                use_container_width=True,
                hide_index=True
            )

            st.markdown("---")
            st.subheader("2. Ranking Top 15 Productos Más Vendidos del Mercado (con Stock en Vivo)")

            top_15_mkt = df_mkt.sort_values(by="sold_quantity", ascending=False).head(15).reset_index(drop=True)
            top_15_mkt.index += 1  # Ranking desde 1

            st.dataframe(
                top_15_mkt[["vendedor_name", "title", "price", "stock", "sold_quantity", "facturacion_estimada", "permalink"]],
                column_config={
                    "vendedor_name": "Vendedor / Competidor",
                    "title": "Título de la Publicación",
                    "price": st.column_config.NumberColumn("PVP Actual ($)", format="$%.0f"),
                    "stock": st.column_config.NumberColumn("Stock Disp. (`stock`)", format="%d"),
                    "sold_quantity": st.column_config.NumberColumn("Ventas Acum. (`sold_quantity`)", format="%d"),
                    "facturacion_estimada": st.column_config.NumberColumn("Facturación Acum. Est. ($)", format="$%.0f"),
                    "permalink": st.column_config.LinkColumn("Enlace MeLi", display_text="Ver 🔗")
                },
                use_container_width=True
            )
        else:
            st.warning("No se encontraron publicaciones activas para el término ingresado.")

# ------------------------------------------------------------------------------
# TAB 4: MATRIZ DE ARTÍCULOS & COSTOS LOGÍSTICOS
# ------------------------------------------------------------------------------
with tabs[3]:
    st.header("📦 Matriz de Artículos & Costos Logísticos Oficiales")
    st.markdown("Subí tu matriz de artículos personalizada en Excel o utiliza la base interna para auditar pesos, dimensiones y bultos.")
    
    uploaded_matriz = st.file_uploader("Subir Matriz de Artículos Excel", type=["xlsx"], key="uploader_matriz")
    if uploaded_matriz is not None:
        try:
            st.session_state["matriz_custom_df"] = pd.read_excel(uploaded_matriz)
            st.success("✅ Matriz de artículos cargada con éxito.")
        except Exception as e:
            st.error(f"Error al leer matriz: {e}")

    matriz_actual = cargar_matriz_articulos_oficial()
    if matriz_actual is not None:
        st.dataframe(matriz_actual, use_container_width=True)
    else:
        st.info("No hay matriz cargada. Subí el archivo en el uploader superior.")

# ------------------------------------------------------------------------------
# TAB 5: ASISTENTE IA (PREGUNTAS & RECLAMOS)
# ------------------------------------------------------------------------------
with tabs[4]:
    st.header("🤖 Asistente IA para Gestión de Preguntas & Reclamos")
    st.markdown("Simulación y respuesta automática basada en el contexto de tus muebles y políticas de envío (ME2 vs ME1).")

    pregunta_user = st.text_input("Simular consulta de cliente (Ej: '¿Hacen envíos a Córdoba y cuánto pesa la caja?')")
    if pregunta_user:
        st.markdown(f"""
        <div class="ai-bubble">
            <b>Respuesta Sugerida por la IA:</b><br>
            ¡Hola! Gracias por tu interés en nuestros muebles Centro Estant. Hacemos envíos a todo el país. 
            Te recordamos que los productos pesados o de múltiples bultos se despachan mediante transporte especializado (ME1 / Expreso) para garantizar que lleguen en perfecto estado. 
            ¿Te podemos ayudar con las medidas de algún modelo en particular?
        </div>
        """, unsafe_allow_html=True)
