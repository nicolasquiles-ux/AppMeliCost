import streamlit as st
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="MeLi Intelligence Pro", layout="centered")

# =========================================================
# TABLAS MAESTRAS (Tasas según tu pedido)
# =========================================================
LOGISTICA = {
    "📦 Estándar (Colecta/Full)": {
        "XS - Sobres (0.5kg)": 4800.0,
        "S - Pequeño (1-2kg)": 6200.0,
        "M - Mediano (5-10kg)": 10500.0,
        "L - Grande (15-25kg)": 17800.0,
        "XL - Muy Grande (30kg)": 23500.0
    },
    "🚚 Pesados (Centro Estant)": {
        "Nivel 1 (Escritorios)": 29000.0,
        "Nivel 2 (Bibliotecas)": 39500.0,
        "Nivel 3 (Placares)": 48000.0
    },
    "🛵 Flex / Propio": {
        "Local / Corto": 4800.0,
        "GBA / Extendido": 7500.0,
        "Especial": 9500.0
    }
}

FINANCIACION = {
    "1 Pago": 0.0,
    "3 Pagos (7%)": 7.0,
    "6 Pagos (10%)": 10.0,
    "9 Pagos (13.5%)": 13.5,
    "12 Pagos (16%)": 16.0
}

CLAVE_CORRECTA = "MELIPRO_2026"
# =========================================================

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .stNumberInput input { font-size: 1.8rem !important; height: 60px !important; font-weight: bold !important; }
    .stSelectbox div { font-size: 1.3rem !important; font-weight: 600 !important; }
    .card-pvp {
        background-color: #000; color: #ffe600; padding: 25px;
        border-radius: 20px; text-align: center; margin-bottom: 15px;
        border: 2px solid #ffe600;
    }
    .price-xl { font-size: 3.8rem; font-weight: 900; line-height: 1; margin: 10px 0; }
    .data-block {
        background-color: #ffffff; padding: 15px; border-radius: 12px;
        border: 1px solid #e0e0e0; margin-bottom: 8px; font-size: 1.1rem;
    }
    .btn-whatsapp {
        background-color: #25d366; color: white !important; padding: 15px;
        border-radius: 12px; text-align: center; text-decoration: none;
        display: block; font-weight: bold; margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- INICIO / LOGIN FRONTAL ---
st.title("🚀 MeLi QuickCheck")

if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    with st.container():
        st.subheader("🔐 Iniciar Sesión")
        clave_input = st.text_input("Ingresá tu Clave Pro", type="password")
        if st.button("Acceder Ahora", use_container_width=True):
            if clave_input == CLAVE_CORRECTA:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Clave incorrecta. Contactate con soporte.")
        
        st.markdown('<a href="https://wa.me/5491165808113" class="btn-whatsapp">💬 Solicitar Acceso vía WhatsApp</a>', unsafe_allow_html=True)
    st.stop()

# --- APP PRINCIPAL (Solo visible si está autenticado) ---
# Configuraciones de Perfil (ahora en expander para ahorrar espacio móvil)
with st.expander("👤 Configuración de Perfil"):
    repu = st.selectbox("Reputación", ["Verde (50% desc)", "Amarilla (40% desc)", "Roja (0% desc)"])
    tipo_iva = st.radio("Condición IVA", ["Responsable Inscripto", "Monotributista"])
    iibb_perc = st.number_input("% Percepción IIBB", value=3.5)
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

st.divider()

# 1. Costo
costo_in = st.number_input("COSTO DE COMPRA ($)", value=0.0, step=1000.0, help="Precio al que comprás el producto")

# 2. Logística
cat_log = st.selectbox("MÉTODO DE ENVÍO", list(LOGISTICA.keys()))
tipo_bulto = st.selectbox("TAMAÑO / PESO", list(LOGISTICA[cat_log].keys()))

# 3. Comisión y Financiación
comi_val = st.selectbox("% COMISIÓN MELI", [10, 12, 14, 15, 16.5, 28], index=3)
finan_txt = st.selectbox("FINANCIACIÓN (COSTO)", list(FINANCIACION.keys()))

margen_target = st.slider("% MARGEN NETO DESEADO", 5, 40, 15)

# --- LÓGICA DE CÁLCULO ---
bonif_log = 0.5 if "Verde" in repu else 0.6 if "Amarilla" in repu else 1.0
costo_envio = LOGISTICA[cat_log][tipo_bulto] * (1 if "Flex" in cat_log else bonif_log)

# Lógica fiscal Nico Q.
t_iva = 0.1735 if tipo_iva == "Responsable Inscripto" else 0.0
t_iibb = iibb_perc / 100
t_finan = FINANCIACION[finan_txt] / 100

divisor = (1 - (comi_val/100) - (margen_target/100) - t_iibb - t_iva - t_finan)
pvp_sug = (costo_in + costo_envio) / divisor if divisor > 0 else 0

# --- CARD PVP ---
st.markdown(f"""
    <div class="card-pvp">
        <div style="font-size: 1rem; text-transform: uppercase;">Precio Sugerido</div>
        <div class="price-xl">${pvp_sug:,.0f}</div>
        <div style="font-size: 1.1rem; color: #fff;">Margen Neto de Ganancia: {margen_target}%</div>
    </div>
""", unsafe_allow_html=True)

# --- COMPARADOR ---
st.subheader("🏁 ¿Dá o no dá?")
p_comp = st.number_input("PRECIO COMPETENCIA ($)", value=float(round(pvp_sug, 0)))

# Lógica MeLi 2026: > $33.000 envío gratis
e_real = costo_envio if p_comp >= 33000 else 0.0
fijo = 3800.0 if p_comp < 33000 else 0.0

# Desglose Real
c_meli = p_comp * (comi_val/100)
c_finan = p_comp * t_finan
imp_iva = (p_comp - (p_comp / 1.21)) if tipo_iva == "Responsable Inscripto" else 0.0
imp_iibb = (p_comp / (1.21 if tipo_iva == "Responsable Inscripto" else 1)) * t_iibb

neta_real = p_comp - (c_meli + c_finan + imp_iva + imp_iibb + e_real + fijo) - costo_in
margen_real = (neta_real / p_comp) if p_comp > 0 else 0

if neta_real < 0:
    st.error(f"🛑 NO PUBLICAR: Perdida de $ {neta_real:,.0f}")
elif margen_real < (margen_target/100):
    st.warning(f"⚠️ RIESGOSO: Ganancia {margen_real:.1%}")
else:
    st.success(f"✅ RENTABLE: Margen {margen_real:.1%}")

# --- DESGLOSE TOTAL ---
with st.expander("📊 DESGLOSE COMPLETO DE COSTOS"):
    st.markdown(f"""
    <div class="data-block">📦 <b>Envío Real:</b> ${e_real:,.2f}</div>
    <div class="data-block">💸 <b>Comisión MeLi:</b> ${c_meli:,.2f}</div>
    <div class="data-block">🏦 <b>Costo Financiero:</b> ${c_finan:,.2f}</div>
    <div class="data-block">🏛️ <b>IVA (Ajustado):</b> ${imp_iva:,.2f}</div>
    <div class="data-block">📄 <b>IIBB:</b> ${imp_iibb:,.2f}</div>
    <div class="data-block">📌 <b>Costo Fijo Unitario:</b> ${fijo:,.2f}</div>
    <div class="data-block" style="background-color: #f0f4ff; border: 2px solid #007bff;">
        <b>GANANCIA NETA FINAL: $ {neta_real:,.2f}</b>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<a href="https://wa.me/5491165808113" class="btn-whatsapp">💬 ¿Dudas con un producto? WhatsApp</a>', unsafe_allow_html=True)
