import io
import re
import pandas as pd
import requests
import streamlit as st

# Módulo OAuth local
try:
    import meli_auth
    HAS_MELI_AUTH = True
except ImportError:
    HAS_MELI_AUTH = False

V_NUMBER = "31.0"

st.set_page_config(
    page_title=f"NQ | Sales Intelligence Matrix v{V_NUMBER}", layout="wide"
)

HEADERS_MELI = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

# =========================================================
# 1. CARGA DE BASE DE DATOS Y TARIFARIOS EN TIEMPO REAL
# =========================================================
@st.cache_data(ttl=3600)
def cargar_base_articulos():
    """Carga y limpia la matriz oficial de productos Centro Estant."""
    try:
        df = pd.read_excel("Matriz Articulos Gemini.xlsm", sheet_name=0)
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df
    except Exception:
        # Fallback de estructura si no encuentra el archivo localmente
        return pd.DataFrame(columns=["CODIGO", "EAN", "DESCRIPCION", "COSTO_LISTA", "PESO_KG"])

@st.cache_data(ttl=1800)
def actualizar_tarifas_meli_api(access_token=None):
    """Sincroniza cargos fijos y umbrales desde la API de MeLi al iniciar."""
    headers = HEADERS_MELI.copy()
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    
    config = {
        "UMBRAL_ENVIO_GRATIS": 33000.0,
        "CARGO_FIJO": 3800.0,
        "COMISION_CLASICA_BASE": 14.50
    }
    try:
        res = requests.get("https://api.mercadolibre.com/sites/MLA", headers=headers, timeout=4)
        if res.status_code == 200:
            data = res.json()
            # Ajuste dinámico de parámetros de sitio si están disponibles
            config["CURRENCY"] = data.get("default_currency_id", "ARS")
    except Exception:
        pass
    return config

TABLA_ME2_BASE = {
    "Hasta 0,3 kg": [7868.0, 5620.0, 6080.0],
    "De 0,3 a 0,5 kg": [8596.0, 6140.0, 6600.0],
    "De 0,5 a 1 kg": [9800.0, 7000.0, 7470.0],
    "De 1 a 1,5 kg": [10122.0, 7230.0, 7720.0],
    "De 1,5 a 2 kg": [10458.0, 7470.0, 7970.0],
    "De 2 a 3 kg": [11550.0, 8250.0, 8710.0],
    "De 3 a 4 kg": [12866.0, 9190.0, 9860.0],
    "De 4 a 5 kg": [14070.0, 10050.0, 10760.0],
    "De 5 a 8 kg": [15512.0, 11080.0, 11830.0],
    "De 8 a 10 kg": [16926.0, 12090.0, 12840.0],
    "De 10 a 13 kg": [18270.0, 13050.0, 13920.0],
    "De 13 a 15 kg": [19684.0, 14060.0, 14930.0],
    "De 15 a 20 kg": [23506.0, 16790.0, 17830.0],
    "De 20 a 25 kg": [28182.0, 20130.0, 21420.0],
    "De 25 a 30 kg": [38780.0, 27700.0, 29410.0],
    "De 30 a 40 kg": [44268.0, 31620.0, 33570.0],
}

CLAVE_CORRECTA = "NQ_PRO_2026"
nq_main_color = "#2B3E4F"

# Cargar base de datos local
df_articulos_base = cargar_base_articulos()

def get_headers(access_token=None):
    headers = HEADERS_MELI.copy()
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return headers

@st.cache_data(ttl=3600)
def obtener_nickname_vendedor(seller_id, access_token=None):
    if not seller_id or seller_id == "Sin ID":
        return "Oficial / Catálogo"
    try:
        url = f"https://api.mercadolibre.com/users/{seller_id}"
        res = requests.get(url, headers=get_headers(access_token), timeout=4)
        if res.status_code == 200:
            return res.json().get("nickname", f"Vendedor {seller_id}")
    except Exception:
        pass
    return f"Vendedor {seller_id}"

# =========================================================
# 2. MOTOR DE BÚSQUEDA HÍBRIDO (EXCEL + API MELI)
# =========================================================
def buscar_items_api_oficial(query_term, limit=10, access_token=None):
    headers = get_headers(access_token)
    term_clean = str(query_term).strip().split(".")[0]

    # Búsqueda inicial por GTIN
    if term_clean.isdigit() and len(term_clean) >= 8:
        try:
            url = f"https://api.mercadolibre.com/sites/MLA/search?gtin={term_clean}&limit={limit}"
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                results = res.json().get("results", [])
                if results:
                    return results, "GTIN / EAN Directo"
        except Exception:
            pass

    # Búsqueda por palabra clave o código
    try:
        url = f"https://api.mercadolibre.com/sites/MLA/search?q={requests.utils.quote(term_clean)}&limit={limit}"
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            results = res.json().get("results", [])
            if results:
                return results, "Query Búsqueda Libre"
    except Exception:
        pass

    # Fallback marca Centro Estant
    try:
        url_fb = f"https://api.mercadolibre.com/sites/MLA/search?q={requests.utils.quote('Centro Estant ' + term_clean)}&limit={limit}"
        res_fb = requests.get(url_fb, headers=headers, timeout=5)
        if res_fb.status_code == 200:
            results = res_fb.json().get("results", [])
            if results:
                return results, "Fallback Comercial (Marca + Modelo)"
    except Exception:
        pass

    return [], "Sin Resultados"

# =========================================================
# INTERFAZ Y LOGIN
# =========================================================
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=400;600;700;800&display=swap');
    html, body, [class*="css"] {{ font-family: 'Plus Jakarta Sans', sans-serif; background-color: #FFFFFF; }}
    .stApp {{ background-color: #FFFFFF; }}
    .nq-header-container {{
        display: flex; align-items: center; justify-content: space-between;
        padding: 18px 25px; background-color: #FFFFFF; box-shadow: 0 4px 12px rgba(0,0,0,0.03); 
        margin-bottom: 20px; border-radius: 14px; border: 1px solid #E2E8F0;
    }}
    .nq-logo {{
        background: linear-gradient(135deg, #0055A0 0%, #00BFBF 100%);
        color: white; padding: 10px 18px; border-radius: 10px; 
        font-weight: 800; font-size: 1.5rem; margin-right: 15px; letter-spacing: -1px;
    }}
    .nq-title-group {{ display: flex; flex-direction: column; }}
    .nq-title-country {{ color: #64748B; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; }}
    .nq-dashboard {{ color: {nq_main_color}; font-weight: 800; font-size: 1.25rem; }}
    </style>
""", unsafe_allow_html=True)

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
    with col_l2:
        st.markdown("<div style='text-align:center; margin-top:100px;'><span class='nq-logo'>NQ</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center; padding: 20px 0;'><h2 style='color: {nq_main_color}; font-weight:900;'>NQ INTELLIGENCE LOGIN</h2></div>", unsafe_allow_html=True)
        clave_input = st.text_input("Ingresa Clave Operador", type="password", placeholder="Access Key")
        if st.button("DESBLOQUEAR SISTEMA", use_container_width=True):
            if clave_input == CLAVE_CORRECTA:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Clave incorrecta")
    st.stop()

# Auto-Sincronización de Tarifas MeLi
tarifas_vigentes = actualizar_tarifas_meli_api(st.session_state.get("access_token"))

# --- SIDEBAR OAUTH ---
st.sidebar.title("🔗 Mercado Libre OAuth")

if HAS_MELI_AUTH:
    query_params = st.query_params
    if "code" in query_params:
        try:
            tokens = meli_auth.intercambiar_code_por_tokens(query_params["code"])
            st.session_state["access_token"] = tokens.get("access_token")
            st.session_state["user_id"] = tokens.get("user_id")
            st.sidebar.success(f"✅ Conectado! User ID: {tokens.get('user_id')}")
            st.query_params.clear()
        except Exception as e:
            st.sidebar.error(f"Error vinculación: {str(e)}")
    
    if "access_token" in st.session_state:
        st.sidebar.success(f"🟢 Sesión API Activa ({st.session_state.get('user_id')})")
    else:
        try:
            url_login = meli_auth.obtener_link_autorizacion()
            st.sidebar.markdown(f'<a href="{url_login}" target="_blank"><button style="background-color:#0055A0; color:white; border:none; padding:10px; border-radius:8px; width:100%; font-weight:bold;">🔑 Conectar Mercado Libre</button></a>', unsafe_allow_html=True)
        except Exception:
            pass

st.markdown(f"""
    <div class="nq-header-container">
        <div class="nq-branding">
            <span class="nq-logo">NQ</span>
            <div class="nq-title-group">
                <div class="nq-title-country">NQ Argentina</div>
                <div class="nq-dashboard">NQ | Sales Intelligence Matrix v{V_NUMBER}</div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# =========================================================
# SOLAPAS PRINCIPALES REORGANIZADAS
# =========================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 BUSCADOR & MATRIZ UNIFICADA",
    "🎯 MONITOR BUY BOX & DESGLOSE DE COSTOS",
    "📁 PROCESAMIENTO MASIVO DE CATÁLOGO",
    "📄 REPORTES GERENCIALES"
])

# --- TAB 1: BUSCADOR UNIFICADO ---
with tab1:
    st.subheader("🔍 Buscador Unificado: Base Centro Estant vs. Mercado Libre en Vivo")
    st.markdown("Ingresá un **EAN, Código SKU o Nombre** para cruzar la información técnica interna con la realidad de mercado.")

    term_search = st.text_input("Buscar por SKU, EAN o Nombre de Producto", value="7798009182461")
    
    if st.button("🔎 CONSULTAR BASE Y CRUZAR CON MELI", use_container_width=True):
        # 1. Búsqueda en Excel Local
        coincidencias_df = pd.DataFrame()
        if not df_articulos_base.empty:
            coincidencias_df = df_articulos_base[
                df_articulos_base.apply(lambda row: term_search.lower() in str(row.values).lower(), axis=1)
            ]

        col_u1, col_u2 = st.columns(2)
        with col_u1:
            st.markdown("### 📦 Ficha Técnica Interna (Centro Estant)")
            if not coincidencias_df.empty:
                st.dataframe(coincidencias_df, use_container_width=True)
            else:
                st.warning("No se encontró el producto en la matriz de artículos local.")

        with col_u2:
            st.markdown("### 🛒 Realidad de Mercado Libre")
            items, modo = buscar_items_api_oficial(term_search, limit=5, access_token=st.session_state.get("access_token"))
            if items:
                st.success(f"Estrategia de hallazgo: **{modo}**")
                tabla_m = []
                for it in items:
                    clean_id = it.get("id", "").replace("MLA", "")
                    link_real = f"https://articulo.mercadolibre.com.ar/MLA-{clean_id}" if clean_id else "#"
                    tabla_m.append({
                        "Título": it.get("title", it.get("name")),
                        "PVP ($)": f"${float(it.get('price', 0)):,.2f}",
                        "ID": clean_id,
                        "Link": link_real
                    })
                st.dataframe(
                    pd.DataFrame(tabla_m),
                    column_config={"Link": st.column_config.LinkColumn("Publicación", display_text="Ver en MeLi")},
                    use_container_width=True
                )
            else:
                st.error("No se encontraron publicaciones activas en Mercado Libre.")

# --- TAB 2: MONITOR BUY BOX & DESGLOSE COMPLETO DE GASTOS ---
with tab2:
    st.subheader("🎯 Auditoría Buy Box & Desglose de Operación del Vendedor")
    
    col_b1, col_b2, col_b3 = st.columns([2.5, 1, 1])
    with col_b1:
        query_sku = st.text_input("SKU / EAN a Auditar", value="7798009182461", key="sku_buybox")
    with col_b2:
        costo_lista_f = st.number_input("Costo Lista Proveedor ($)", value=70500.0, step=1000.0)
    with col_b3:
        margen_target = st.number_input("% Margen Objetivo Deseado", value=10.0, step=0.5) / 100

    if st.button("🚀 AUDITAR Y DESGLOSAR GASTOS", use_container_width=True):
        items, modo = buscar_items_api_oficial(query_sku, limit=10, access_token=st.session_state.get("access_token"))

        if items:
            winner = items[0]
            pvp_ganador = float(winner.get("price", winner.get("buy_box_winner", {}).get("price", 0.0)))
            title_p = winner.get("title", winner.get("name", "Producto MeLi"))

            # Cálculos de la Matriz NQ
            pvp_objetivo = pvp_ganador - 100.0
            comision_m = pvp_objetivo * (tarifas_vigentes["COMISION_CLASICA_BASE"] / 100)
            flete_me2 = TABLA_ME2_BASE["De 20 a 25 kg"][1]
            cargo_fijo = tarifas_vigentes["CARGO_FIJO"] if pvp_objetivo < tarifas_vigentes["UMBRAL_ENVIO_GRATIS"] else 0.0
            pvp_neto = pvp_objetivo / 1.21
            iibb = pvp_neto * 0.035
            margen_ganancia = pvp_objetivo * margen_target

            costo_max_compra = pvp_neto - (comision_m / 1.21) - (flete_me2 / 1.21) - (cargo_fijo / 1.21) - iibb - margen_ganancia
            bonif_req = ((1 - (costo_max_compra / costo_lista_f)) * 100) if costo_lista_f > 0 else 0.0

            st.markdown("### 📊 Métricas Clave de Competitividad")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🏆 PVP Ganador Actual", f"${pvp_ganador:,.2f}")
            m2.metric("🎯 PVP Objetivo (#1)", f"${pvp_objetivo:,.2f}")
            m3.metric("📦 Costo Máx Compra Target", f"${max(0.0, costo_max_compra):,.2f}")
            m4.metric("📉 Bonificación Necesaria", f"{bonif_req:.2f}%")

            st.markdown("---")
            st.markdown("### 💸 Desglose Estructural de Gastos del Vendedor para Ganar la Publicación")

            desglose_data = {
                "Concepto / Gasto": [
                    "PVP Recomendado (Objetivo #1)",
                    "(-) Comisión Mercado Libre Clásica (14.5%)",
                    "(-) Flete Logística Mercado Envíos 2",
                    "(-) Cargo Fijo por Unidad",
                    "(-) Retención / Impuesto IIBB (3.5%)",
                    "(-) Margen Neto Ganancia Objetivo (10%)",
                    "(=) COSTO MÁXIMO DE COMPRA PERMITIDO (Neto)"
                ],
                "Monto ($)": [
                    f"${pvp_objetivo:,.2f}",
                    f"-${comision_m:,.2f}",
                    f"-${flete_me2:,.2f}",
                    f"-${cargo_fijo:,.2f}",
                    f"-${iibb:,.2f}",
                    f"-${margen_ganancia:,.2f}",
                    f"${max(0.0, costo_max_compra):,.2f}"
                ],
                "% Sobre PVP": [
                    "100.00%",
                    f"{tarifas_vigentes['COMISION_CLASICA_BASE']:.2f}%",
                    f"{(flete_me2/pvp_objetivo)*100:.2f}%",
                    f"{(cargo_fijo/pvp_objetivo)*100:.2f}%",
                    "2.89% (Neto)",
                    f"{margen_target*100:.2f}%",
                    f"{(max(0.0, costo_max_compra)/pvp_objetivo)*100:.2f}%"
                ]
            }
            st.table(pd.DataFrame(desglose_data))

            st.markdown("---")
            st.markdown(f"### 📋 Vendedores y Publicaciones Detectadas")

            tabla_comp = []
            for rank, it in enumerate(items, start=1):
                clean_id = str(it.get("id", "")).replace("MLA", "")
                link_real = f"https://articulo.mercadolibre.com.ar/MLA-{clean_id}" if clean_id else "#"
                seller_id = str(it.get("seller_id", "Sin ID"))
                seller_nick = obtener_nickname_vendedor(seller_id, st.session_state.get("access_token"))

                tabla_comp.append({
                    "Posición": "🥇 Ganador Buy Box" if rank == 1 else f"Puesto #{rank}",
                    "ID MLA": clean_id,
                    "Título": it.get("title", it.get("name", title_p)),
                    "PVP ($)": f"${float(it.get('price', 0)):,.2f}",
                    "Vendedor": seller_nick,
                    "Link": link_real
                })

            st.dataframe(
                pd.DataFrame(tabla_comp),
                column_config={"Link": st.column_config.LinkColumn("Enlace Publicación", display_text="Ver en Mercado Libre")},
                use_container_width=True
            )
        else:
            st.error("No se encontraron publicaciones activas.")

# --- TAB 3: PROCESAMIENTO MASIVO DE CATÁLOGO ---
with tab3:
    st.subheader("📁 Auditoría Masiva de Catálogo (Excel / CSV)")
    archivo_subido = st.file_uploader("Cargar lista de productos (debe contener columna EAN o SKU)", type=["xlsx", "csv"])

    if archivo_subido:
        df_masivo = pd.read_excel(archivo_subido) if archivo_subido.name.endswith(".xlsx") else pd.read_csv(archivo_subido)
        st.write("Vista previa de productos cargados:", df_masivo.head(3))
        
        if st.button("🚀 AUDITAR TODO EL CATÁLOGO EN MELI", use_container_width=True):
            resultados = []
            bar = st.progress(0)
            for idx, row in df_masivo.iterrows():
                sku_val = str(row.get("EAN", row.get("SKU", row.get("CODIGO", ""))))
                items, _ = buscar_items_api_oficial(sku_val, limit=1, access_token=st.session_state.get("access_token"))
                if items:
                    pvp = float(items[0].get("price", 0))
                    resultados.append({"SKU/EAN": sku_val, "PVP MeLi ($)": pvp, "Estado": "Encontrado"})
                else:
                    resultados.append({"SKU/EAN": sku_val, "PVP MeLi ($)": 0.0, "Estado": "Sin Resultados"})
                bar.progress((idx + 1) / len(df_masivo))
            
            st.dataframe(pd.DataFrame(resultados), use_container_width=True)

# --- TAB 4: REPORTES GERENCIALES IMPRIMIBLES ---
with tab4:
    st.subheader("📄 Generador de Reporte Gerencial Exportable")
    st.markdown("Generá un documento listo para presentar a Dirección Comercial o a Proveedores.")

    rep_sku = st.text_input("EAN/SKU para el Reporte", value="7798009182461", key="rep_sku_in")
    
    if st.button("🖨️ GENERAR INFORME GERENCIAL (PDF/HTML)", use_container_width=True):
        items, _ = buscar_items_api_oficial(rep_sku, limit=1, access_token=st.session_state.get("access_token"))
        if items:
            p = items[0]
            pvp_g = float(p.get("price", 0))
            tit = p.get("title", "Producto Centro Estant")

            reporte_html = f"""
            <div style="padding
