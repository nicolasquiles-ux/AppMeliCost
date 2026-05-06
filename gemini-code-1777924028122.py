import streamlit as st
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="MeLi Intelligence", layout="centered")

# =========================================================
# TABLAS MAESTRAS (Actualizadas 2026)
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

CLAVE_CORRECTA = "CENTRO_PRO_2026"
# =========================================================

# --- ESTILOS CSS PARA MÓVIL (FUENTES XL) ---
st.markdown("""
    <style>
    /* Forzar fuentes grandes en inputs */
    .stNumberInput input { font-size: 1.8rem !important; height: 60px !important; font-weight: bold !important; }
    .stSelectbox div { font-size: 1.3rem !important; font-weight: 600 !important; }
    
    /* Tarjeta de PVP Principal */
    .card-pvp {
        background-color: #000; color: #ffe600; padding: 25px;
        border-radius: 20px; text-align: center; margin-bottom: 15px;
    }
    .price-xl { font-size: 3.8rem; font-weight: 900; line-height: 1; margin: 10px 0; }
    
    /* Bloques de Datos */
    .data-block {
        background-color: #ffffff; padding: 15px; border-radius: 12px;
        border: 1px solid #e0e0e0; margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
with st.sidebar:
    st.title("👤 Perfil")
    clave = st.text_input("Clave", type="password")
    if clave != CLAVE_CORRECTA:
        st.stop()
    
    st.success("Acceso Ok")
    st.divider()
    repu = st.selectbox("Reputación", ["Verde (50% desc)", "Amarilla (40% desc)", "Roja (0% desc)"])
    tipo_iva = st.radio("IVA", ["Responsable Inscripto", "Monotributista"])
    iibb_perc = st.number_input("% IIBB", value=3.5)

# --- CUERPO DE LA APP (TODO VERTICAL) ---
st.title("🚀 MeLi QuickCheck")

# 1. Costo
costo_in = st.number_input("COSTO DE COMPRA ($)", value=0.0, step=1000.0)

# 2. Logística (Selectores anchos)
cat_log = st.selectbox("MÉTODO DE ENVÍO", list(LOGISTICA.keys()))
tipo_bulto = st.selectbox("TAMAÑO / PESO", list(LOGISTICA[cat_log].keys()))

# 3. Comisión y Financiación
comi_val = st.selectbox("% COMISIÓN MELI", [10, 12, 14, 15, 16.5, 28], index=3)
finan_opciones = {"1 Pago": 0.0, "3 Pagos (7%)": 7, 
    "6 Pagos (10%)": 10, "9 Pagos (13.5%)": 13.5, "12 Pagos (16%)": 16}
finan_txt = st.selectbox("FINANCIACIÓN", list(finan_opciones.keys()))

margen_target = st.slider("% MARGEN NETO DESEADO", 5, 40, 15)

# --- CÁLCULOS ---
bonif_log = 0.5 if "Verde" in repu else 0.6 if "Amarilla" in repu else 1.0
costo_envio = LOGISTICA[cat_log][tipo_bulto] * (1 if "Flex" in cat_log else bonif_log)

t_iva = 0.1735 if tipo_iva == "Responsable Inscripto" else 0.0
t_iibb = iibb_perc / 100
t_finan = finan_opciones[finan_txt] / 100

divisor = (1 - (comi_val/100) - (margen_target/100) - t_iibb - t_iva - t_finan)
pvp_sug = (costo_in + costo_envio) / divisor if divisor > 0 else 0

# --- RESULTADO PRINCIPAL ---
st.markdown(f"""
    <div class="card-pvp">
        <div style="font-size: 1.1rem; text-transform: uppercase; font-weight: bold;">Precio Venta Sugerido</div>
        <div class="price-xl">${pvp_sug:,.0f}</div>
        <div style="font-size: 1.2rem;">Ganancia Neta: ${(pvp_sug * margen_target/100):,.0f}</div>
    </div>
""", unsafe_allow_html=True)

# --- COMPARADOR Y DATOS COMPLETOS ---
st.divider()
st.subheader("🏁 Comparar vs Competencia")
p_comp = st.number_input("PRECIO COMPETENCIA ($)", value=float(round(pvp_sug, 0)))

# Lógica MeLi 2026: > $33.000 envío gratis
e_real = costo_envio if p_comp >= 33000 else 0.0
fijo = 3800.0 if p_comp < 33000 else 0.0

# Desglose de todos los datos
c_meli = p_comp * (comi_val/100)
c_finan = p_comp * t_finan
imp_iva = (p_comp - (p_comp / 1.21)) if tipo_iva == "Responsable Inscripto" else 0.0
imp_iibb = (p_comp / (1.21 if tipo_iva == "Responsable Inscripto" else 1)) * t_iibb

neta_real = p_comp - (c_meli + c_finan + imp_iva + imp_iibb + e_real + fijo) - costo_in
margen_real = (neta_real / p_comp) if p_comp > 0 else 0

# Semáforo Visual
if neta_real < 0:
    st.error(f"🛑 PERDÉS DINERO: $ {neta_real:,.0f}")
elif margen_real < (margen_target/100):
    st.warning(f"⚠️ RENTABILIDAD BAJA: {margen_real:.1%}")
else:
    st.success(f"✅ RENTABLE: {margen_real:.1%}")

# --- TABLA DE DATOS TOTALES (Scannable para móvil) ---
with st.expander("📊 DESGLOSE DE TODOS LOS DATOS"):
    st.markdown(f"""
    <div class="data-block">📦 <b>Envío:</b> ${e_real:,.2f}</div>
    <div class="data-block">💵 <b>Comisión MeLi:</b> ${c_meli:,.2f}</div>
    <div class="data-block">🏦 <b>Costo Financiero:</b> ${c_finan:,.2f}</div>
    <div class="data-block">🏛️ <b>IVA (RI):</b> ${imp_iva:,.2f}</div>
    <div class="data-block">📄 <b>IIBB:</b> ${imp_iibb:,.2f}</div>
    <div class="data-block">📌 <b>Costo Fijo:</b> ${fijo:,.2f}</div>
    <div class="data-block" style="background-color: #e3f2fd;">💰 <b>Gastos Totales:</b> ${(c_meli + c_finan + imp_iva + imp_iibb + e_real + fijo):,.2f}</div>
    """, unsafe_allow_html=True)
