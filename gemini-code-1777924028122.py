import streamlit as st
import pandas as pd
import requests
import re

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="MeLi Intelligence Pro", layout="wide", page_icon="🚀")

# =========================================================
# TABLAS EDITABLES (Modificá aquí los costos)
# =========================================================
TARIFARIO_ENVIOS = {
    "0.5 kg": 4800.0, "1 kg": 5200.0, "2 kg": 5900.0, 
    "5 kg": 7400.0, "10 kg": 9800.0, "15 kg": 12500.0, 
    "20 kg": 15200.0, "25 kg": 18400.0, "30 kg": 22000.0
}

TASAS_FINANCIACION = {
    "1 Pago": 0.0, "3 Pagos (Cuota Simple)": 12.5, 
    "6 Pagos (Cuota Simple)": 23.8, "9 Pagos": 35.0, "12 Pagos": 45.0
}

CLAVE_CORRECTA = "CENTRO_PRO_2026"
# =========================================================

# --- FUNCIÓN DE BÚSQUEDA MULTI-CAPA ---
def buscar_precio_meli_definitivo(query):
    # Extraer solo el número
    id_num = re.sub(r'\D', '', str(query))
    if not id_num: return None

    # CAPA 1: Búsqueda por palabra clave (La más resistente a bloqueos)
    # Buscamos el ID como si fuera un término de búsqueda
    url_search = f"https://api.mercadolibre.com/sites/MLA/search?q={id_num}"
    try:
        res = requests.get(url_search, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data.get("results"):
                # Filtramos para encontrar el que mejor coincida con el ID
                for prod in data["results"]:
                    if id_num in prod.get("id", "") or id_num in prod.get("catalog_product_id", "") or id_num in str(prod.get("title")):
                        return {"titulo": prod.get("title"), "precio": float(prod.get("price"))}
                # Si no hay coincidencia exacta, devolvemos el primero
                return {"titulo": data["results"][0].get("title"), "precio": float(data["results"][0].get("price"))}
    except: pass

    # CAPA 2: API de Ítems (MLA directo)
    url_item = f"https://api.mercadolibre.com/items/MLA{id_num}"
    try:
        res = requests.get(url_item, timeout=5)
        if res.status_code == 200:
            data = res.json()
            return {"titulo": data.get("title"), "precio": float(data.get("price"))}
    except: pass

    return None

# --- SIDEBAR ---
with st.sidebar:
    st.title("👤 Mi Perfil")
    clave = st.text_input("Clave Pro", type="password")
    es_pro = (clave == CLAVE_CORRECTA)
    if not es_pro:
        st.markdown(f'<a href="https://wa.me/5491165808113" class="whatsapp-button" style="background-color:#25d366; color:white; padding:10px; border-radius:5px; text-decoration:none; display:block; text-align:center;">Pedir Clave</a>', unsafe_allow_html=True)
    
    st.divider()
    reputacion = st.selectbox("Reputación", ["Verde (50% desc)", "Amarilla (40% desc)", "Roja (0% desc)"])
    tipo_vend = st.radio("Condición IVA", ["Responsable Inscripto", "Monotributista"])
    iibb_tax = st.number_input("% IIBB", value=3.5)

# --- APP ---
st.title("🚀 MeLi Intelligence Pro")
tab_calc, tab_mla = st.tabs(["🧮 Calculadora", "🔍 Espiar Competencia"])

if 'precio_meli' not in st.session_state: st.session_state.precio_meli = 0.0

with tab_mla:
    st.subheader("Buscador de Competencia")
    input_busqueda = st.text_input("Ingresá el código (Ej: 27392194)")
    
    if st.button("Buscar en MeLi", use_container_width=True):
        if not es_pro:
            st.error("🔒 Función Pro bloqueada.")
        else:
            with st.spinner('Rastreando precio...'):
                res = buscar_precio_meli_definitivo(input_busqueda)
                if res:
                    st.session_state.precio_meli = res['precio']
                    st.success(f"✅ ¡Éxito! {res['titulo']}")
                    st.metric("Precio en Mercado Libre", f"$ {res['precio']:,.2f}")
                else:
                    st.error("MeLi no devolvió datos. Intentá con el link de la publicación.")

with tab_calc:
    col_izq, col_der = st.columns([1.3, 2])
    
    with col_der:
        c1, c2 = st.columns(2)
        with c1:
            costo_c = st.number_input("Costo Compra ($)", value=15000.0)
            plan = st.selectbox("Financiación", list(TASAS_FINANCIACION.keys()))
        with c2:
            margen_deseado = st.slider("% Margen Neto", 5, 50, 20)
            comision_meli = st.number_input("% Comisión MeLi", value=15.0)

    # Cálculo PVP Sugerido
    t_iva = 0.1735 if tipo_vend == "Responsable Inscripto" else 0.0
    t_iibb = iibb_tax / 100
    t_finan = TASAS_FINANCIACION[plan] / 100
    div = (1 - (comision_meli/100) - (margen_deseado/100) - t_iibb - t_iva - t_finan)
    
    dcto_e = 0.5 if "Verde" in reputacion else 0.6 if "Amarilla" in reputacion else 1
    envio_sug = TARIFARIO_ENVIOS["10 kg"] * dcto_e
    pvp_sug = (costo_c + envio_sug) / div if div > 0 else 0

    with col_izq:
        st.markdown(f"""
            <div style="background-color:#ffe600; padding:30px; border-radius:20px; text-align:center; border:3px solid #000;">
                <div style="font-weight:bold; color:#333;">PVP SUGERIDO</div>
                <div style="font-size:3.5rem; font-weight:900; color:#000;">${pvp_sug:,.0f}</div>
                <div style="font-weight:bold; color:#555;">MARGEN: {margen_deseado}%</div>
            </div>
        """, unsafe_allow_html=True)

    st.divider()
    
    col_f, col_r1, col_r2 = st.columns([1.2, 1, 1])
    with col_f:
        base = st.session_state.precio_meli if st.session_state.precio_meli > 0 else pvp_sug
        pvp_final = st.number_input("Precio Final a Evaluar ($)", value=float(round(base, 0)))

    # Desglose Final
    c_fijo = 3030.0 if pvp_final < 33000 else 0.0
    peso_c = st.selectbox("Peso para Envío Real", list(TARIFARIO_ENVIOS.keys()), index=4)
    envio_r = TARIFARIO_ENVIOS[peso_c] * dcto_e if pvp_final >= 33000 else 0.0
    
    iva_r = (pvp_final - (pvp_final / 1.21)) if tipo_vend == "Responsable Inscripto" else 0.0
    iibb_r = (pvp_final / (1.21 if tipo_vend == "Responsable Inscripto" else 1)) * t_iibb
    comm_r = pvp_final * (comision_meli/100)
    finan_r = pvp_final * t_finan
    
    ganancia = pvp_final - (comm_r + c_fijo + envio_r + iva_r + iibb_r + finan_r) - costo_c
    margen_r = (ganancia / pvp_final) if pvp_final > 0 else 0

    with col_r1: st.metric("Ganancia Neta", f"$ {ganancia:,.2f}")
    with col_r2: st.metric("Margen Real", f"{margen_r:.2%}")
