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
# 4. FUNCIONES DE API Y PROCESAMIENTO
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

def obtener_nombre_vendedor(seller_id, headers):
    if not seller_id or seller_id == "N/A":
        return "Desconocido"
    url = f"https://api.mercadolibre.com/users/{seller_id}"
    try:
        res = requests.get(url, headers=headers, timeout=3)
        if res.status_code == 200:
            data = res.json()
            return data.get("nickname", f"ID: {seller_id}")
    except Exception:
        pass
    return f"ID: {seller_id}"

def buscar_competencia_integral_ean(query_key: str, access_token: str = None):
    headers = {"Authorization": f"Bearer {access_token.strip()}"} if access_token else {}
    type_input, clean_val = extraer_id_catalogo_o_ean_input(query_key)
    
    results = []
    catalog_id = clean_val if type_input == "CATALOG_ID" else ""
    product_title = ""

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

    if catalog_id:
        url_prod_items = f"https://api.mercadolibre.com/products/{catalog_id}/items"
        try:
            res_pi = requests.get(url_prod_items, headers=headers, timeout=8)
            if res_pi.status_code == 200:
                results = res_pi.json().get("results", [])
        except Exception:
            pass

        if not results:
            url_c_items = f"https://api.mercadolibre.com/sites/MLA/search?catalog_product_id={catalog_id}"
            try:
                res_ci = requests.get(url_c_items, headers=headers, timeout=8)
                if res_ci.status_code == 200:
                    results = res_ci.json().get("results", [])
            except Exception:
                pass

    if not results and clean_val:
        url_q = f"https://api.mercadolibre.com/sites/MLA/search?q={clean_val}"
        try:
            res_q = requests.get(url_q, headers=headers, timeout=8)
            if res_q.status_code == 200:
                results = res_q.json().get("results", [])
        except Exception:
            pass

    if not results:
        found_g, _, desc_g, art_g = buscar_costo_y_titulo_en_lista_gold(query_key)
        term_search = f"{desc_g} {art_g}".strip() if desc_g else art_g
        if term_search:
            query_clean = requests.utils.quote(term_search[:35])
            url_g_search = f"https://api.mercadolibre.com/sites/MLA/search?q={query_clean}"
            try:
                res_gs = requests.get(url_g_search, headers=headers, timeout=8)
                if res_gs.status_code == 200:
                    results = res_gs.json().get("results", [])
            except Exception:
                pass

    return catalog_id if catalog_id else "N/A", product_title, results

def publicar_en_mercado_libre(catalog_id: str, titulo: str, categoria: str, precio: float, stock: int, tipo_listado: str, access_token: str):
    if not access_token:
        return False, "⚠️ Debés conectar Mercado Libre o ingresar un Access Token directo."

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
            return True, f"✅ ¡Publicación creada con éxito! ID: **{data.get('id')}** — [Abrir en Mercado Libre]({data.get('permalink')})"
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
st.caption("v75.0 — Panel Operativo de Costos, Competencia por EAN y Publicación")

tabs = st.tabs([
    "1. 🧮 Simulación de Costos MeLi & Rentabilidad",
    "2. 🏆 Competencia por EAN en Catálogo",
    "3. 🚀 Publicador Directo Mercado Libre"
])

# ------------------------------------------
# SOLAPA 1: COSTOS Y RENTABILIDAD CON DESCUENTO
# ------------------------------------------
with tabs[0]:
    st.header("🧮 Análisis Estructurado de Costos y Rentabilidad")
    st.write("Ingresá un **SKU, EAN, MLA o URL** para evaluar la rentabilidad:")

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
                f'<div class="badge-missing">❌ El código "{query_costos.strip()}" NO existe en la Lista Gold cargada. Cargar costo manualmente para simular.</div><br>',
                unsafe_allow_html=True
            )
        else:
            st.success(f"✅ Costo base en Lista Gold: **${costo_gold_val:,.2f}** ({desc_g} - {art_g})")

        c_p1, c_p2, c_p3 = st.columns(3)
        with c_p1:
            pvp_sim = st.number_input("Precio de Venta Simulado ($ ARS)", min_value=100.0, value=173436.0, step=500.0)
            tipo_pub_sim = st.selectbox("Modalidad de Publicación", ["gold_pro (Premium / Cuotas)", "gold_special (Clásica)"])
            pct_com_sim = 28.0 if "gold_pro" in tipo_pub_sim else 14.0

        with c_p2:
            costo_envio_sim = st.number_input("Costo Envío / Logística ($ ARS)", min_value=0.0, value=5500.0, step=100.0)
            pct_descuento_proveedor = st.number_input("Descuento Proveedor al Costo (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.5, help="Porcentaje de descuento negociado con la empresa sobre la Lista Gold")

        with c_p3:
            pct_iibb_sim = st.number_input("Ingresos Brutos IIBB (%)", min_value=0.0, max_value=10.0, value=3.5)
            pct_iva_sim = st.number_input("IVA / Impuestos (%)", min_value=0.0, max_value=30.0, value=21.0)

        # Cálculo del costo aplicando el descuento del proveedor
        costo_base_calc = costo_gold_val if found_gold else 104000.0
        costo_con_descuento = costo_base_calc * (1.0 - (pct_descuento_proveedor / 100.0))
        
        costo_prod_input = st.number_input("Costo Efectivo del Producto (con desc.)", min_value=0.0, value=costo_con_descuento, step=500.0)

        m_com = pvp_sim * (pct_com_sim / 100.0)
        m_iibb = pvp_sim * (pct_iibb_sim / 100.0)
        m_iva = pvp_sim * (pct_iva_sim / 100.0)
        total_deducciones = m_com + m_iibb + m_iva + costo_envio_sim
        ganancia_neta = pvp_sim - total_deducciones - costo_prod_input
        margen_pct = (ganancia_neta / pvp_sim) * 100.0 if pvp_sim > 0 else 0.0

        st.markdown("### 📊 Resultado Financiero Neto")
        res1, res2, res3 = st.columns(3)
        res1.metric("PVP Simulado", f"${pvp_sim:,.2f}")
        res2.metric("Total Deducciones MeLi & Tax", f"${total_deducciones:,.2f}")
        res3.metric("Ganancia Neta Final", f"${ganancia_neta:,.2f}", f"{margen_pct:.1f}% Margen")

        if ganancia_neta > 0:
            st.markdown(f'<div class="card-viable">🟢 <b>OPERACIÓN RENTABLE:</b> Margen positivo de <b>${ganancia_neta:,.2f} ({margen_pct:.1f}%)</b> con un descuento de proveedor del <b>{pct_descuento_proveedor}%</b>.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="card-noviable">🔴 <b>OPERACIÓN CON PÉRDIDA:</b> Pérdida neta de <b>${ganancia_neta:,.2f} ({margen_pct:.1f}%)</b>. Requerís mayor descuento de proveedor.</div>', unsafe_allow_html=True)

        st.markdown("#### 🧾 Desglose Detallado de Deducciones")
        df_desglose = pd.DataFrame([
            {"Concepto": "PVP Venta Objetivo", "Monto ($)": pvp_sim, "Porcentaje": "100.0%"},
            {"Concepto": f"Comisión MeLi ({pct_com_sim}%)", "Monto ($)": -m_com, "Porcentaje": f"-{pct_com_sim}%"},
            {"Concepto": "Costo Envío / Logística", "Monto ($)": -costo_envio_sim, "Porcentaje": f"-{(costo_envio_sim/pvp_sim)*100:.1f}%"},
            {"Concepto": f"Ingresos Brutos IIBB ({pct_iibb_sim}%)", "Monto ($)": -m_iibb, "Porcentaje": f"-{pct_iibb_sim}%"},
            {"Concepto": f"IVA / Retenciones ({pct_iva_sim}%)", "Monto ($)": -m_iva, "Porcentaje": f"-{pct_iva_sim}%"},
            {"Concepto": f"Costo Producto Efectivo (-{pct_descuento_proveedor}% desc.)", "Monto ($)": -costo_prod_input, "Porcentaje": f"-{(costo_prod_input/pvp_sim)*100:.1f}%"},
            {"Concepto": "RESULTADO NETO FINAL", "Monto ($)": ganancia_neta, "Porcentaje": f"{margen_pct:.1f}%"}
        ])
        st.table(df_desglose)

# ------------------------------------------
# SOLAPA 2: COMPETENCIA POR EAN EN CATÁLOGO (MEJORADA)
# ------------------------------------------
with tabs[1]:
    st.header("🏆 Analizador de Competencia por Código EAN / Catálogo")
    st.write("Ingresá un código **EAN, Catalog Product ID (ej: MLA27235683) o URL de MeLi**:")

    col_e1, col_e2 = st.columns([3, 1])
    with col_e1:
        query_ean_comp = st.text_input("Buscador EAN / Catálogo / URL", value="7798274755803")
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
            st.subheader(f"📊 Vendedores Competidores ({len(items_comp)} publicaciones)")
            
            headers_api = {"Authorization": f"Bearer {st.session_state.get('access_token', '').strip()}"} if st.session_state.get('access_token') else {}
            data_t = []
            
            for item in items_comp[:25]:
                seller_info = item.get("seller", {})
                seller_id = seller_info.get("id", "N/A")
                nickname_vendedor = obtener_nombre_vendedor(seller_id, headers_api)
                
                inst = item.get("installments", {})
                q_c = inst.get("quantity", 1) if inst else 1
                
                # Traducir o formatear tipo de listado
                raw_tipo = item.get("listing_type_id", "gold_pro")
                tipo_formateado = "Premium (Cuotas)" if "pro" in raw_tipo else ("Clásica" if "special" in raw_tipo else raw_tipo)

                data_t.append({
                    "Vendedor": nickname_vendedor,
                    "ID Publicación": item.get("id"),
                    "Título Publicación": item.get("title", ""),
                    "Precio ($ ARS)": item.get("price", 0.0),
                    "Cuotas": f"{q_c}x sin interés" if q_c > 1 else "1 pago / Contado",
                    "Tipo Listado": tipo_formateado,
                    "Stock": item.get("available_quantity", 0),
                    "Link Publicación": item.get("permalink", "#")
                })

            df_comp = pd.DataFrame(data_t).sort_values(by="Precio ($ ARS)", ascending=True).reset_index(drop=True)
            
            # Mostrar tabla interactiva con links clickeables de MeLi
            st.dataframe(
                df_comp,
                column_config={
                    "Link Publicación": st.column_config.LinkColumn("Enlace a MeLi", display_text="Abrir Publicación 🔗")
                },
                use_container_width=True
            )

            ganador_bb = df_comp.iloc[0]
            pvp_ganador_bb = float(ganador_bb["Precio ($ ARS)"])
            link_ganador_bb = ganador_bb["Link Publicación"]
            pub_id_win = ganador_bb["ID Publicación"]

            st.session_state["selected_pub_data"] = {
                "catalog_id": cat_id_comp,
                "title": ganador_bb["Título Publicación"],
                "price": pvp_ganador_bb
            }

            deducciones_estimadas = (pvp_ganador_bb * 0.28) + (pvp_ganador_bb * 0.035) + (pvp_ganador_bb * 0.21) + 5500.0
            costo_max_necesario_win = pvp_ganador_bb - deducciones_estimadas - (pvp_ganador_bb * 0.15)
            
            pct_desc_requerido = 0.0
            if found_gold_comp and costo_gold_comp > costo_max_necesario_win and costo_gold_comp > 0:
                pct_desc_requerido = ((costo_gold_comp - costo_max_necesario_win) / costo_gold_comp) * 100.0

            st.markdown("### 🎯 Estrategia para Ganar el Buy Box")
            mb1, mb2, mb3 = st.columns(3)
            mb1.metric("🥇 PVP Ganador Buy Box", f"${pvp_ganador_bb:,.2f}", f"ID: {pub_id_win}")
            mb2.metric("🎯 Costo Máximo Necesario en Gold", f"${costo_max_necesario_win:,.2f}")
            mb3.metric("📉 % Descuento Necesario en Lista Gold", f"{pct_desc_requerido:.1f}%" if pct_desc_requerido > 0 else "0.0% (Viable)")

            st.markdown(f"👉 **Enlace directo a la publicación del líder:** [{ganador_bb['Título Publicación']}]({link_ganador_bb})")
        else:
            st.warning("No se encontraron publicaciones competidoras activas para este código EAN o Catalog ID.")

# ------------------------------------------
# SOLAPA 3: PUBLICADOR DIRECTO MERCADO LIBRE
# ------------------------------------------
with tabs[2]:
    st.header("🚀 Publicador Directo en Mercado Libre (`POST /items`)")
    st.write("Creá la publicación directamente en tu cuenta de Mercado Libre:")

    pub_data_state = st.session_state.get("selected_pub_data", {})

    col_pub1, col_pub2 = st.columns(2)
    with col_pub1:
        p_titulo = st.text_input("Título de la Publicación", value=pub_data_state.get("title", "Escritorio Milan SC1260 Negro Paraiso Centro Estant"))
        p_cat_id = st.text_input("Catalog Product ID (MLA...)", value=pub_data_state.get("catalog_id", "MLA27235683"))
        p_categoria = st.text_input("Categoría MeLi", value="MLA35254")

    with col_pub2:
        p_precio = st.number_input("Precio de Venta Objetivo ($ ARS)", min_value=100.0, value=float(pub_data_state.get("price", 173436.0)), step=500.0)
        p_stock = st.number_input("Stock Inicial", min_value=1, value=5)
        p_tipo = st.selectbox("Modalidad de Listado", ["gold_pro", "gold_special"], format_func=lambda x: "Premium / Cuotas (gold_pro)" if x=="gold_pro" else "Clásica (gold_special)")

    st.markdown("---")
    if st.button("🚀 CREAR PUBLICACIÓN EN MERCADO LIBRE", type="primary", use_container_width=True):
        with st.spinner("Enviando publicación a Mercado Libre..."):
            exito_pub, msg_pub = publicar_en_mercado_libre(
                catalog_id=p_cat_id,
                titulo=p_titulo,
                categoria=p_categoria,
                precio=p_precio,
                stock=p_stock,
                tipo_listado=p_tipo,
                access_token=st.session_state.get("access_token")
            )
            if exito_pub:
                st.success(msg_pub)
            else:
                st.error(msg_pub)
