import streamlit as st
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="MeLi Intelligence Pro", layout="centered")

# =========================================================
# TABLAS MAESTRAS
# =========================================================
LOGISTICA = {
    "📦 Estándar (Colecta/Full)": {
        "XS - Sobres (0.5kg)": 4800.0, "S - Pequeño (1-2kg)": 6200.0,
        "M - Mediano (5-10kg)": 10500.0, "L - Grande (15-25kg)": 17800.0,
        "XL - Muy Grande (30kg)": 23500.0
    },
    "🚚 Pesados (Centro Estant)": {
        "Nivel 1 (Escritorios)": 29000.0, "Nivel 2 (Bibliotecas)": 39500.0, "Nivel 3 (Placares)": 48000.0
    },
    "🛵 Flex / Propio": {
        "Local / Corto": 4800.0, "GBA / Extendido": 7500.0, "Especial": 9500.0
    }
}

FINANCIACION = {
    "1 Pago": 0.0, "3 Pagos (7%)": 7.0, "6 Pagos (10%)": 10.0,
    "9 Pagos (13.5%)": 13.5, "12 Pagos (16%)": 16.0
}

CLAVE_CORRECTA = "MELIPRO_2026"

# --- ESTILOS CSS REFORZADOS (Para evitar pantalla negra/texto invisible) ---
st.markdown("""
    <style>
    /* Forzar fondo claro en la app para evitar problemas de modo oscuro */
    .stApp { background-color: #f8f9fa; }
    
    /* Inputs con números grandes y negros */
    .stNumberInput input { font-size: 1.8rem !important; height: 60px !important; font-weight: bold !important; color: #000 !important; }
    
    /* Tarjeta de PVP Principal (Negro y Amarillo) */
    .card-pvp {
        background-color: #000000 !important; color: #ffe600 !important; padding: 25px;
        border-radius: 20px; text-align: center; margin-bottom: 15px;
        border: 3px solid #ffe600;
    }
    .price-xl { font-size: 3.5rem; font-weight: 900; line-height: 1; margin: 10px 0; color: #ffe600 !important; }
    
    /* Bloques de Datos del Desglose (Forzar fondo blanco y texto negro) */
    .data-block {
        background-color: #ffffff !important; 
        color: #1a1a1a !important; 
        padding: 15px; 
        border-radius: 12px;
        border: 2px solid #dddddd !important; 
        margin-bottom: 8px; 
        font-size: 1.2rem;
        font-weight: 600;
    }
    .data-block b { color: #000 !important; }

    .btn-whatsapp {
        background-color: #25d366; color: white !important; padding: 18px;
        border-radius: 15px; text-align: center; text-decoration: none;
        display: block; font-weight: bold; margin-top: 20px; font-size: 1.2rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🚀 MeLi QuickCheck")
    st.subheader("🔐 Acceso Profesionales")
    clave_input = st.text_input("Clave Pro", type="password")
    if st.button("ACCEDER", use_container_width=True):
        if clave_input == CLAVE_CORRECTA:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Clave Incorrecta")
    st.markdown('<a href="https://wa.me/5491165808113" class="btn-whatsapp">💬 Solicitar Acceso</a>', unsafe_allow_html=True)
    st.stop()

# --- APP ---
with st.expander("👤 Configuración de Cuenta"):
    repu = st.selectbox("Reputación", ["Verde (50% desc)", "Amarilla (40% desc)", "Roja (0% desc)"])
    tipo_iva = st.radio("Tu IVA", ["Responsable Inscripto", "Monotributista"])
    iibb_perc = st.number_input("% IIBB", value=3.5)

st.title("📊 Calculador Express")

costo_in = st.number_input("COSTO DE COMPRA ($)", value=0.0, step=1000.0)

cat_log = st.selectbox("LOGÍSTICA", list(LOGISTICA.keys()))
tipo_bulto = st.selectbox("PESO / TAMAÑO", list(LOGISTICA[cat_log].keys()))
comi_val = st.selectbox("% COMISIÓN MELI", [10, 12, 14, 15, 16.5, 28], index=3)
finan_txt = st.selectbox("FINANCIACIÓN", list(FINANCIACION.keys()))
margen_target = st.slider("% MARGEN OBJETIVO", 5, 40, 15)

# CÁLCULOS
bonif_log = 0.5 if "Verde" in repu else 0.6 if "Amarilla" in repu else 1.0
costo_envio = LOGISTICA[cat_log][tipo_bulto] * (1 if "Flex" in cat_log else bonif_log)
t_iva = 0.1735 if tipo_iva == "Responsable Inscripto" else 0.0
t_iibb = iibb_perc / 100
t_finan = FINANCIACION[finan_txt] / 100

divisor = (1 - (comi_val/100) - (margen_target/100) - t_iibb - t_iva - t_finan)
pvp_sug = (costo_in + costo_envio) / divisor if divisor > 0 else 0

st.markdown(f"""
    <div class="card-pvp">
        <div style="text-transform: uppercase; font-weight: bold;">Precio Venta Sugerido</div>
        <div class="price-xl">${pvp_sug:,.0f}</div>
        <div style="font-size: 1.2rem;">Ganancia Neta Esperada: {margen_target}%</div>
    </div>
""", unsafe_allow_html=True)

st.divider()
st.subheader("🏁 Evaluador de Mercado")
p_comp = st.number_input("PRECIO DE LA COMPETENCIA ($)", value=float(round(pvp_sug, 0)))

# Lógica 2026: > $33.000 envío gratis
e_real = costo_envio if p_comp >= 33000 else 0.0
fijo = 3800.0 if p_comp < 33000 else 0.0

# Desglose Final
c_meli = p_comp * (comi_val/100)
c_finan = p_comp * t_finan
imp_iva = (p_comp - (p_comp / 1.21)) if tipo_iva == "Responsable Inscripto" else 0.0
imp_iibb = (p_comp / (1.21 if tipo_iva == "Responsable Inscripto" else 1)) * t_iibb
neta_real = p_comp - (c_meli + c_finan + imp_iva + imp_iibb + e_real + fijo) - costo_in
margen_real = (neta_real / p_comp) if p_comp > 0 else 0

if neta_real < 0:
    st.error(f"🛑 PERDÉS DINERO: $ {neta_real:,.0f}")
else:
    st.success(f"✅ RENTABLE: {margen_real:.1%} de margen")

with st.expander("📊 VER DESGLOSE DE COSTOS"):
    st.markdown(f"""
    <div class="data-block">📦 <b>Envío Real:</b> ${e_real:,.2f}</div>
    <div class="data-block">💸 <b>Comisión MeLi:</b> ${c_meli:,.2f}</div>
    <div class="data-block">🏦 <b>Costo Financiero:</b> ${c_finan:,.2f}</div>
    <div class="data-block">🏛️ <b>IVA:</b> ${imp_iva:,.2f}</div>
    <div class="data-block">📄 <b>IIBB:</b> ${imp_iibb:,.2f}</div>
    <div class="data-block">📌 <b>Costo Fijo:</b> ${fijo:,.2f}</div>
    <div class="data-block" style="background-color: #ffe600 !important; border: 2px solid #000 !important;">
        <b>GANANCIA NETA: $ {neta_real:,.2f}</b>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<a href="https://wa.me/5491165808113" class="btn-whatsapp">💬 Consultar por WhatsApp</a>', unsafe_allow_html=True)
