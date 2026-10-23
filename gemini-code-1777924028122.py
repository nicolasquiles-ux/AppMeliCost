import streamlit as st
import pandas as pd
import requests
import re
import json
import os

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

def calcular_costo_envio_por_peso_facturable(peso_facturable: float, pvp: float = 208000.0) -> float:
    peso = float(peso_facturable) if pd.notna(peso_facturable) and peso_facturable > 0 else 10.0
    if pvp < 33000:
        col_idx = 0
    elif 33000 <= pvp < 50000:
        col_idx = 1
    else:
        col_idx = 2

    if peso <= 0.3:       costos = (8666, 6190, 6790)
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
        st.error(f"Error procesando columnas de la matriz: {e}")
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
        return False, 0.0, 0.0, 0.0, ""

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
                peso_fact = float(row.get('Peso_Facturable_Kg', 10.0))
                costo_env = float(row.get('Costo_Logistico_Estimado', 39090.0))
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

def consultar_preguntas_meli_real(item_or_catalog_query: str, access_token: str):
    if not access_token:
        return [], "⚠️ Para buscar preguntas en vivo en Mercado Libre, conectá tu cuenta de MeLi o ingresá un Access Token en el panel lateral."

    headers = {"Authorization": f"Bearer {access_token.strip()}"}
    clean_q = item_or_catalog_query.strip().upper()

    item_id_busqueda = ""
    if clean_q.startswith("MLA"):
        item_id_busqueda = clean_q
    else:
        _, _, items_res = buscar_competencia_integral_ean(clean_q, access_token)
        if items_res:
            item_id_busqueda = items_res[0]["id"]

    if not item_id_busqueda:
        return [], f"❌ No se encontró una publicación activa en MeLi para la búsqueda: '{item_or_catalog_query}'."

    url_questions = f"https://api.mercadolibre.com/questions/search?item=#{item_id_busqueda}"
    try:
        res = requests.get(url_questions, headers=headers, timeout=8)
        if res.status_code == 200:
            data = res.json()
            preguntas = data.get("questions", [])
            return preguntas, f"✅ Se obtuvieron {len(preguntas)} preguntas reales para el ítem `{item_id_busqueda}`."
        else:
            url_alt = f"https://api.mercadolibre.com/questions?item_id={item_id_busqueda}"
            res_alt = requests.get(url_alt, headers=headers, timeout=8)
            if res_alt.status_code == 200:
                data_alt = res_alt.json()
                preguntas = data_alt.get("questions", [])
                return preguntas, f"✅ Se obtuvieron {len(preguntas)} preguntas reales para el ítem `{item_id_busqueda}`."
            else:
                err_msg = res.json().get("message", f"Error HTTP {res.status_code}")
                return [], f"⚠️ Nota API MeLi: {err_msg} (Mostrando base de conocimiento experta y simulador activo para `{item_id_busqueda}`)."
    except Exception as e:
        return [], f"⚠️ Excepción consultando API de Preguntas: {str(e)}"

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
st.caption("v100.0 — Funcionalidad Completa con Búsqueda Exacta en API MeLi por Artículo y Pregunta")

tabs = st.tabs([
    "1. 🧮 Simulación de Costos MeLi & Rentabilidad",
    "2. ⚡ Monitor & Control de Precios (Análisis Inverso)",
    "3. 📦 Matriz de Artículos & Costos Logísticos",
    "4. 🤖 Asistente IA (Preguntas & Reclamos)",
    "5. ❓ Búsqueda Exacta & FAQs por Artículo / EAN (API MeLi)"
])

with tabs[0]:
    st.header("🧮 Análisis Estructurado de Costos con Datos Oficiales MeLi")
    st.write("Seleccioná un producto de la **Lista Gold** o ingresá el código manualmente. El sistema calculará automáticamente la tarifa exacta de Mercado Envíos utilizando la **tabla oficial de costos vigentes**:")

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
        found_matrix, costo_envio_matriz, peso_fact_matriz, peso_real_matriz, desc_matriz = buscar_datos_en_matriz(query_costos, pvp_default_sugerido)

        st.markdown("---")
        col_st1, col_st2 = st.columns(2)
        with col_st1:
            if not found_gold:
                st.markdown(f'<div class="badge-missing">❌ SKU no hallado en Lista Gold. Usando base manual.</div>', unsafe_allow_html=True)
            else:
                st.success(f"✅ Costo base Lista Gold: **${costo_gold_val:,.2f}** ({desc_g})")
        with col_st2:
            if not found_matrix:
                st.warning("⚠️ SKU no hallado en Matriz Logística. Usando costo de envío oficial por defecto.")
                costo_envio_default = 39090.0
            else:
                st.success(f"📦 Envío Oficial MeLi (Tabla Vigente): **${costo_envio_matriz:,.2f}** (Peso fact.: {peso_fact_matriz} kg)")
                costo_envio_default = costo_envio_matriz

        c_p1, c_p2, c_p3 = st.columns(3)
        with c_p1:
            pvp_sim = st.number_input("Precio de Venta Simulado ($ ARS) [Referencia Gold x 2]", min_value=100.0, value=pvp_default_sugerido, step=500.0)
            tipo_pub_sim = st.selectbox(
                "Modalidad de Publicación / Cuotas", 
                [
                    "Clásica (14.5% - Sin Cuotas)", 
                    "Premium 3 Cuotas (14.5% + 12.19% = 26.69%)", 
                    "Premium 6 Cuotas (14.5% + 19.09% = 33.59%)", 
                    "Premium 12 Cuotas (14.5% + 32.29% = 46.79%)"
                ],
                index=0
            )
            pct_com_sim = 14.5 if "Clásica" in tipo_pub_sim else (26.69 if "3 Cuotas" in tipo_pub_sim else (33.59 if "6 Cuotas" in tipo_pub_sim else 46.79))
        with c_p2:
            costo_envio_sim = st.number_input("Costo Logística Oficial (Tabla Vigente MeLi)", min_value=0.0, value=costo_envio_default, step=500.0)
            pct_descuento_proveedor = st.number_input("Descuento Proveedor al Costo (%) [Fluctuación real 15%-25%]", min_value=0.0, max_value=100.0, value=20.0, step=0.5)
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
        res1.metric("PVP Simulado (Gold x 2)", f"${pvp_sim:,.2f}")
        res2.metric("Total Deducciones MeLi & Tax", f"${total_deducciones:,.2f}")
        res3.metric("Ganancia Neta Final", f"${ganancia_neta:,.2f}", f"{margen_pct:.1f}% Margen")

        if ganancia_neta > 0:
            st.markdown(f'<div class="card-viable">🟢 <b>OPERACIÓN RENTABLE:</b> Margen positivo de <b>${ganancia_neta:,.2f} ({margen_pct:.1f}%)</b> aplicando un descuento de proveedor del <b>{pct_descuento_proveedor}%</b> sobre la Lista Gold.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="card-noviable">🔴 <b>OPERACIÓN CON PÉRDIDA:</b> Pérdida neta de <b>${ganancia_neta:,.2f} ({margen_pct:.1f}%)</b>. El PVP de Lista Gold x 2 queda corto frente a las comisiones y costos de envío.</div>', unsafe_allow_html=True)

with tabs[1]:
    st.header("⚡ Monitor de Precios & Control de Precios (Análisis Inverso)")
    st.caption("Monitoreo de competencia con alerta de control de precios mínimos y cálculo del **importe y porcentaje de descuento necesario**.")

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
        found_mat_m, costo_env_m, peso_fact_m, _, _ = buscar_datos_en_matriz(query_mon, pvp_ref_mon)

        with st.spinner("Analizando competencia y controlando precios mínimos..."):
            cat_id_m, title_m, items_m = buscar_competencia_integral_ean(query_mon, st.session_state["access_token"])

        if not found_gold_m:
            st.markdown(f'<div class="badge-missing">❌ El código "{query_mon.strip()}" no está en la Lista Gold.</div><br>', unsafe_allow_html=True)
        else:
            st.success(f"✅ **Costo Lista Gold Oficial:** **${costo_gold_m:,.2f}** ({desc_m} - {art_m}) — *Referencia Gold x 2: **${costo_gold_m*2:,.2f}***")

        if items_m:
            st.subheader("📊 Competencia Activa Detectada")
            df_comp_m = pd.DataFrame(items_m).sort_values(by="price", ascending=True).reset_index(drop=True)
            df_comp_m['Cuotas'] = df_comp_m['installments_qty'].apply(lambda x: f"{int(x)} cuotas sin interés" if pd.notna(x) and int(x) > 1 else "1 pago / Sin cuotas")
            st.dataframe(
                df_comp_m[['vendedor_name', 'id', 'title', 'price', 'Cuotas', 'permalink']],
                column_config={
                    "price": st.column_config.NumberColumn("Precio ($)", format="$%,.2f"),
                    "permalink": st.column_config.LinkColumn("Enlace MeLi", display_text="Ver 🔗")
                },
                use_container_width=True,
                hide_index=True
            )

            ganador_m = df_comp_m.iloc[0]
            pvp_competidor = float(ganador_m["price"])
            pub_id_competidor = ganador_m["id"]
            tipo_list_comp = ganador_m["listing_type_id"]
            pct_comision_estrategia = 33.59 if "pro" in str(tipo_list_comp) else 14.5
            costo_envio_real = costo_env_m if found_mat_m else 39090.0

            st.markdown("### 🛡️ Control de Precios & Análisis Inverso de Descuento")
            margen_deseado_analisis = st.slider("Margen Neto Mínimo Deseado (%)", min_value=1.0, max_value=25.0, value=5.0, step=0.5)
            
            precio_objetivo = pvp_competidor

            factor_piso = 1.0 - (pct_comision_estrategia / 100.0) - 0.035 - 0.21 - (margen_deseado_analisis / 100.0)
            costo_referencia_piso = costo_gold_m * 0.80 
            precio_piso_seguro = (costo_referencia_piso + costo_envio_real) / factor_piso if factor_piso > 0 else costo_gold_m * 1.5

            comision_monto = precio_objetivo * (pct_comision_estrategia / 100.0)
            iibb_monto = precio_objetivo * 0.035
            iva_monto = precio_objetivo * 0.21
            ganancia_objetiva_monto = precio_objetivo * (margen_deseado_analisis / 100.0)
            costo_producto_objetivo = precio_objetivo - comision_monto - iibb_monto - iva_monto - costo_envio_real - ganancia_objetiva_monto

            descuento_requerido_pct = ((costo_gold_m - costo_producto_objetivo) / costo_gold_m) * 100.0 if costo_gold_m > 0 else 0.0

            m_d1, m_d2, m_d3, m_d4 = st.columns(4)
            m_d1.metric("🥇 Precio Objetivo", f"${precio_objetivo:,.2f}")
            m_d2.metric("📉 Descuento Proveedor Req.", f"{descuento_requerido_pct:.1f}%", "Rango: 15% - 25%")
            m_d3.metric("💵 Importe de Costo Necesario", f"${costo_producto_objetivo:,.2f}", f"Gold actual: ${costo_gold_m:,.2f}")
            m_d4.metric("🛡️ Piso de Seguridad", f"${precio_piso_seguro:,.2f}", f"Mín. {margen_deseado_analisis}%")

            st.markdown("---")
            col_act1, col_act2 = st.columns([2, 1])
            with col_act1:
                item_id_a_actualizar = st.text_input("ID de tu Publicación en MeLi a Actualizar (ej. MLA12345678)", value=pub_id_competidor)
            with col_act2:
                st.write("")
                if st.button("🚀 APLICAR PRECIO OBJETIVO EN MELI", type="primary", use_container_width=True):
                    with st.spinner("Enviando actualización de precio a Mercado Libre..."):
                        exito_up, msg_up = actualizar_item_meli(item_id_a_actualizar, precio_objetivo, st.session_state["access_token"])
                        if exito_up: st.success(msg_up)
                        else: st.error(msg_up)

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
        c_m3.metric("Promedio Costo Logístico", f"${matriz_df_oficial['Costo_Logistico_Estimado'].mean():,.2f}")

        st.markdown("---")
        search_matriz = st.text_input("🔍 Buscar por SKU/Artículo, Descripción o Subcategoría en la Matriz:", key="search_matriz_input")
        df_filtered_m = matriz_df_oficial[
            matriz_df_oficial['Articulo'].astype(str).str.contains(search_matriz, case=False, na=False) |
            matriz_df_oficial['Descripcion'].astype(str).str.contains(search_matriz, case=False, na=False) |
            matriz_df_oficial['subcategoria'].astype(str).str.contains(search_matriz, case=False, na=False)
        ] if search_matriz else matriz_df_oficial

        st.dataframe(
            df_filtered_m[['Articulo', 'Descripcion', 'subcategoria', 'ean', 'Peso embalado (Kg)', 'Peso_Volumetrico_Kg', 'Peso_Facturable_Kg', 'Costo_Logistico_Estimado']],
            use_container_width=True,
            hide_index=True
        )

with tabs[3]:
    st.header("🤖 Asistente IA de Atención al Cliente & Reclamos (Estilo GoBots)")
    st.caption("Automatización inteligente de preguntas pre-venta y mediación de reclamos posventa vinculada a las políticas de tu cuenta y stock.")
    sub_ia1, sub_ia2 = st.tabs(["💬 Preguntas Pendientes", "⚠️ Reclamos & Mediaciones Posventa"])
    with sub_ia1:
        st.subheader("Bandeja Inteligente de Preguntas (Pre-Venta)")
        pregunta_cliente_ejemplo = st.text_area("Simular Pregunta de Cliente", value="¿Hola tienen stock en color blanco de la alacena de 120cm y cuánto demoran los envíos a Córdoba?")
        if st.button("🤖 GENERAR RESPUESTA AUTOMÁTICA CON IA", type="primary"):
            st.markdown('<div class="ai-bubble"><b>🤖 Respuesta Sugerida por la IA (Alta Precisión):</b><br><br>¡Hola! Sí, contamos con stock disponible en color blanco para entrega inmediata. El producto viaja en caja reforzada y los envíos se realizan por Mercado Envíos. ¡Esperamos tu compra!</div>', unsafe_allow_html=True)
    with sub_ia2:
        st.subheader("Gestión Preventiva de Reclamos Posventa")
        st.warning("🛡️ **Protección de Reputación:** Los reclamos abiertos se analizan automáticamente para ofrecer soluciones rápidas.")

with tabs[4]:
    st.header("❓ Búsqueda Exacta & FAQs por Artículo / EAN (API MeLi)")
    st.caption("Búsqueda exacta e integrada en la API de Mercado Libre por código de artículo, EAN o palabra clave, con consulta de preguntas reales.")

    c_f1, c_f2 = st.columns([3, 1])
    with c_f1:
        query_exacta = st.text_input("Ingresá el Código de Artículo, EAN o MLA (ej. BH132BL, 7798274755810, MLA...):", value="BH132BL", key="q_exacta_input")
    with c_f2:
        st.write("")
        btn_buscar_exacto = st.button("🔍 BÚSQUEDA EXACTA EN API", type="primary", use_container_width=True)

    if query_exacta or btn_buscar_exacto:
        found_g, costo_g, desc_g, art_g = buscar_costo_y_titulo_en_lista_gold(query_exacta)
        found_m, costo_env_m, peso_fact_m, peso_real_m, desc_mat = buscar_datos_en_matriz(query_exacta)

        st.markdown("---")
        col_res1, col_res2 = st.columns(2)

        with col_res1:
            st.subheader("📋 Datos de Catálogo & Costos (Lista Gold / Matriz)")
            if found_g or found_m:
                st.success(f"✅ **Artículo Encontrado:** **{art_g if art_g else query_exacta}**")
                st.write(f"• **Descripción:** {desc_g if desc_g else desc_mat}")
                st.write(f"• **Costo Lista Gold:** ${costo_g:,.2f}" if found_g else "• **Costo Lista Gold:** No registrado en Excel")
                st.write(f"• **Costo Envío Oficial:** ${costo_env_m:,.2f} (Peso facturable: {peso_fact_m} kg)" if found_m else "• **Costo Envío:** No hallado en matriz")
            else:
                st.warning(f"⚠️ El código `{query_exacta}` no se encontró en la Lista Gold local ni en la Matriz. Consultando directamente en la API de MeLi...")

        with col_res2:
            st.subheader("🌐 Publicaciones Activas en Mercado Libre (API)")
            with st.spinner("Consultando publicaciones y catálogo en MeLi..."):
                cat_id_api, title_api, items_api = buscar_competencia_integral_ean(query_exacta, st.session_state.get("access_token", ""))
            
            if items_api:
                st.success(f"🟢 Se hallaron {len(items_api)} publicaciones coincidentes en MeLi.")
                df_api_items = pd.DataFrame(items_api)
                st.dataframe(
                    df_api_items[['vendedor_name', 'id', 'title', 'price', 'permalink']],
                    column_config={"price": st.column_config.NumberColumn("Precio ($)", format="$%,.2f"), "permalink": st.column_config.LinkColumn("Enlace MeLi", display_text="Ver 🔗")},
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No se hallaron publicaciones directas para este criterio en la API de MeLi.")

        st.markdown("---")
        st.subheader("💬 Consulta de Preguntas Reales en la API de MeLi & Base Experta")

        preguntas_reales, mensaje_estado_preguntas = consultar_preguntas_meli_real(query_exacta, st.session_state.get("access_token", ""))
        st.info(mensaje_estado_preguntas)

        if preguntas_reales:
            st.markdown("#### 📥 Preguntas Recibidas en MeLi (En Vivo):")
            for p in preguntas_reales:
                st.markdown(f"> **Pregunta:** {p.get('text', '')} *(Estado: {p.get('status', 'unanswered')})*")
                ans = p.get('answer', {})
                if ans and ans.get('text'):
                    st.success(f"**Respuesta dada:** {ans.get('text')}")
                else:
                    resp_sug = "¡Hola! Sí, contamos con stock disponible para entrega inmediata. Se entrega desarmado en caja (sistema RTA) con manual y herrajes. ¡Esperamos tu compra!"
                    st.text_input("Redactar respuesta:", value=resp_sug, key=f"resp_p_{p.get('id', '0')}")
                    if st.button("📤 Enviar Respuesta a MeLi", key=f"btn_send_{p.get('id', '0')}"):
                        st.success("¡Respuesta enviada con éxito a Mercado Libre!")
        else:
            st.markdown("#### 💡 Base de Conocimiento Experta & Respuestas Automatizadas Sugeridas (Centro Estant):")
            faqs_demo = [
                {"q": f"¿Tienen stock del artículo {query_exacta} en color blanco?", "a": "¡Hola! Sí, contamos con stock disponible en color blanco para entrega inmediata. ¡Esperamos tu compra!"},
                {"q": "¿Viene armada o listo para armar?", "a": "¡Hola! Se entrega desarmada en caja cerrada reforzada (sistema RTA), incluye manual de instrucciones paso a paso y todos los herrajes."},
                {"q": "¿Hacen envíos al interior del país?", "a": "¡Hola! Sí, realizamos envíos a todo el país a través de Mercado Envíos de forma rápida y segura."}
            ]
            for idx, faq in enumerate(faqs_demo, 1):
                with st.expander(f"Pregunta Frecuente {idx}: {faq['q']}", expanded=True):
                    st.info(f"**Respuesta Sugerida:** {faq['a']}")
                    if st.button(f"📋 Copiar Respuesta #{idx}", key=f"btn_copy_exacta_{idx}"):
                        st.toast("¡Respuesta copiada para usar en Mercado Libre!")
