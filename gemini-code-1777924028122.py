import streamlit as st
import pandas as pd
import requests
import re

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="MeLi Intelligence Pro", layout="wide", page_icon="🚀")

# =========================================================
# TABLAS EDITABLES (Modificá estos valores si cambian los costos)
# =========================================================

TARIFARIO_ENVIOS = {
    "0.5 kg (Sobres)": 4800.0,
    "1 kg": 5200.0,
    "2 kg": 5900.0,
    "5 kg": 7400.0,
    "10 kg": 9800.0,
    "15 kg": 12500.0,
    "20 kg": 15200.0,
    "25 kg": 18400.0,
    "30 kg (Límite)": 22000.0,
    "Especial (Muebles)": 35000.0
}

TASAS_FINANCIACION = {
    "1 Pago": 0.0,
    "3 Pagos (Cuota Simple)": 12.5,
    "6 Pagos (Cuota Simple)": 23.8,
    "9 Pagos": 35.0,
    "12 Pagos": 45.0
}

CLAVE_CORRECTA = "CENTRO_PRO_2026"

# =========================================================

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .pvp-box {
        background-color: #ffe600;
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        border: 3px solid #000;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    .pvp-value { font-size: 3.5rem; font-weight: 900; color: #000; line-height: 1; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 12px; border: 1px solid #eee; }
    .whatsapp-button { background-color: #25d366 !important; color: white !important; padding: 12px; border-radius: 8px; text-decoration: none; font-weight: bold; display: block; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIÓN DE BÚSQUEDA CORREGIDA ---
def buscar_precio_meli_final(query):
    id_numerico = re.sub(r'\D', '', str(query))
    if not id_numerico: return None
    
    # Probamos primero la API de Productos (Catálogo) que es la que fallaba
    url_prod = f"https://api.mercadolibre.com/products/MLA{id_numerico}"
    try:
        res = requests.get(url_prod, timeout=5)
        if res.status_code == 200:
            data = res.json()
            return {
                "titulo": data.get("name"),
                "precio": float(data.get("buy_box_winner", {}).get("price", 0)),
                "status": "ok"
            }
    except: pass

    # Si falla, probamos la API de Items (Publicación común)
    url_item = f"https://api.mercadolibre.com/items/MLA{id_numerico}"
    try:
        res = requests.get(url_item, timeout=5)
        if res.status_code == 200:
            data = res.json()
            return {
                "titulo": data.get("title"),
                "precio": float(data.get("price")),
                "status": "ok"
            }
    except: pass

    return None

# --- SIDEBAR ---
with st.sidebar:
    st.title("👤 Mi Perfil")
    clave = st.text_input("Clave Pro", type="password")
    es_pro = (clave == CLAVE_CORRECTA)
    
    if not es_pro:
        st.markdown(f'<a href="https://wa.me/5491165808113" target="_blank" class="whatsapp-button">Pedir Clave Pro</a>', unsafe_allow_html=True)
    
    st.divider()
    reputacion = st.selectbox("Reputación", ["Verde (50% desc)", "Amarilla (40% desc)", "Roja (0% desc)"])
    tipo_vend = st.radio("Condición IVA", ["Responsable Inscripto", "Monotributista"])
    iibb_tax = st.number_input("% IIBB", value=3.5)

# --- APP ---
st.title("🚀 MeLi Intelligence Pro")

tab_calc, tab_mla = st.tabs(["🧮 Calculadora", "🔍 Espiar Competencia"])

if 'precio_meli' not in st.session_state: st.session_state.precio_meli = 0.0

with tab_mla:
    st.subheader("Buscador de Precios (MLA / Catálogo)")
    input_busqueda = st.text_input("Ingresá el código", placeholder="Ej: 27392194")
    
    if st.button("Buscar en MeLi", use_container_width=True):
        if not es_pro:
            st.error("🔒 Función Pro bloqueada.")
        else:
            with st.spinner('Buscando...'):
                resultado = buscar_precio_meli_final(input_busqueda)
                if resultado and resultado['precio'] > 0:
                    st.session_state.precio_meli = resultado['precio']
                    st.success(f"✅ Encontrado: {resultado['titulo']}")
                    st.metric("Precio Competencia", f"$ {resultado['precio']:,.2f}")
                else:
                    st.error("No se encontró el precio. Intentá con el ID numérico solo.")

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

    # Lógica de cálculo PVP Sugerido
    t_iva = 0.1735 if tipo_vend == "Responsable Inscripto" else 0.0
    t_iibb = iibb_tax / 100
    t_finan = TASAS_FINANCIACION[plan] / 100
    div = (1 - (comision_meli/100) - (margen_deseado/100) - t_iibb - t_iva - t_finan)
    
    # Costo envío default para sugerencia (10kg)
    envio_sug = TARIFARIO_ENVIOS["10 kg"] * (0.5 if "Verde" in reputacion else 0.6 if "Amarilla" in reputacion else 1)
    pvp_sug = (costo_c + envio_sug) / div if div > 0 else 0

    with col_izq:
        st.markdown(f"""
            <div class="pvp-box">
                <div style="font-weight:bold; color:#333;">PVP SUGERIDO</div>
                <div class="pvp-value">${pvp_sug:,.0f}</div>
                <p style="margin-top:10px; font-weight:bold; color:#555;">MARGEN NETO: {margen_deseado}%</p>
            </div>
        """, unsafe_allow_html=True)

    st.divider()

    col_final, col_res1, col_res2 = st.columns([1.2, 1, 1])
    
    with col_final:
        base_pvp = st.session_state.precio_meli if st.session_state.precio_meli > 0 else pvp_sug
        pvp_final = st.number_input("Precio Final a Evaluar ($)", value=float(round(base_pvp, 0)))

    # Desglose Real
    c_fijo = 3030.0 if pvp_final < 33000 else 0.0
    peso_c = st.selectbox("Peso del bulto (Envío)", list(TARIFARIO_ENVIOS.keys()), index=4)
    dcto_e = 0.5 if "Verde" in reputacion else 0.6 if "Amarilla" in reputacion else 1
    envio_r = TARIFARIO_ENVIOS[peso_c] * dcto_e if pvp_final >= 33000 else 0.0
    
    iva_r = (pvp_final - (pvp_final / 1.21)) if tipo_vend == "Responsable Inscripto" else 0.0
    iibb_r = (pvp_final / (1.21 if tipo_vend == "Responsable Inscripto" else 1)) * t_iibb
    comm_r = pvp_final * (comision_meli/100)
    finan_r = pvp_final * t_finan
    
    gastos_totales = comm_r + c_fijo + envio_r + iva_r + iibb_r + finan_r
    ganancia = pvp_final - gastos_totales - costo_c
    margen_r = (ganancia / pvp_final) if pvp_final > 0 else 0

    with col_res1: st.metric("Ganancia Neta", f"$ {ganancia:,.2f}")
    with col_res2: st.metric("Margen Real", f"{margen_r:.2%}")

    with st.expander("📄 Ver Desglose Detallado"):
        df_gastos = pd.DataFrame({
            "Concepto": ["Compra", "Comisión MeLi", "Costo Fijo", "Envío", "IVA", "IIBB", "Financiación"],
            "Monto": [costo_c, comm_r, c_fijo, envio_r, iva_r, iibb_r, finan_r]
        })
        st.table(df_gastos.style.format({"Monto": "${:,.2f}"}))
