import streamlit as st

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Centro Estant | Intelligence V10", layout="centered")

# =========================================================
# NUEVA TABLA DE ENVÍOS (image_41c7fd.png)
# =========================================================
TABLA_ME1 = {
    "Hasta 0,3 Kg": 6080.0, "0,3 a 0,5 Kg": 6600.0, "0,5 a 1 Kg": 7470.0,
    "1 a 2 Kg": 7970.0, "2 a 5 Kg": 10760.0, "5 a 10 Kg": 12840.0,
    "10 a 15 Kg": 14930.0, "15 a 20 Kg": 17830.0, "20 a 25 Kg": 21420.0,
    "25 a 30 Kg": 29410.0, "30 a 40 Kg": 33570.0, "40 a 50 Kg": 35490.0,
    "50 a 60 Kg": 39610.0, "60 a 70 Kg": 41290.0, "70 a 80 Kg": 47850.0,
    "80 a 90 Kg": 59180.0, "90 a 100 Kg": 68230.0, "100 a 120 Kg": 74490.0,
    "120 a 140 Kg": 83890.0, "140 a 160 Kg": 93280.0, "160 a 180 Kg": 102660.0,
    "Mas de 180 Kg": 112060.0
}

# Actualización cuotas (Imagen 2 + Cuota 5%)
FINANCIACION = {
    "1 Pago": 0.0,
    "3 Pagos CON Interes Bajo (5%)": 5.0,
    "3 Pagos (7%)": 7.0,
    "6 Pagos (10%)": 10.0,
    "9 Pagos (13.5%)": 13.5,
    "12 Pagos (16%)": 16.0
}

CLAVE_CORRECTA = "MELIPRO_2026"

# --- CSS PROFESIONAL ---
st.markdown("""
    <style>
    .stApp { background-color: #F4F7F9; }
    .dash-main {
        background-color: #0F172A; color: white; padding: 25px;
        border-radius: 15px; text-align: center; border-bottom: 5px solid #3B82F6;
    }
    .dash-price { font-size: 3.2rem; font-weight: 900; color: #FFFFFF; }
    .metric-card {
        background-color: white; padding: 15px; border-radius: 10px;
        border: 1px solid #E2E8F0; text-align: center;
    }
    .stNumberInput input { font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔐 Acceso Sistema")
    clave_input = st.text_input("Clave Operador", type="password")
    if st.button("INGRESAR"):
        if clave_input == CLAVE_CORRECTA:
            st.session_state.autenticado = True
            st.rerun()
    st.stop()

# --- PANEL ---
with st.sidebar:
    st.header("Configuración")
    repu = st.selectbox("Reputación", ["Verde (50% desc)", "Amarilla (40% desc)", "Roja (0% desc)"])
    tipo_iva = st.radio("IVA", ["Responsable Inscripto", "Monotributista"])
    iibb_perc = st.number_input("% IIBB", value=3.5)
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

st.subheader("📊 Simulador de Rentabilidad Real")

# Inputs
costo_in = st.number_input("COSTO PRODUCTO ($)", value=0.0, step=1000.0)
tipo_me = st.radio("SISTEMA DE ENVÍO", ["ME2 (Colecta/Full - Comisiona)", "ME1 (Muebles Pesados - No Comisiona)"], horizontal=True)
peso_cat = st.selectbox("PESO / AFORADO", list(TABLA_ME1.keys()))
comi_p = st.selectbox("% COMISIÓN MELI", [10, 12, 14, 15, 16.5, 28], index=2)
plan_f = st.selectbox("PLAN DE CUOTAS", list(FINANCIACION.keys()))
margen_obj = st.slider("% MARGEN NETO DESEADO", 5, 40, 15)

# --- MOTOR DE CÁLCULO ---
bonif = 0.5 if "Verde" in repu else 0.6 if "Amarilla" in repu else 1.0
envio_v = TABLA_ME1[peso_cat] * bonif

t_iva = 0.1735 if tipo_iva == "Responsable Inscripto" else 0.0
t_iibb = iibb_perc / 100
t_finan = FINANCIACION[plan_f] / 100
t_comi = comi_p / 100
t_margen = margen_obj / 100

if "ME2" in tipo_me:
    # ME2: El envío está dentro del PVP que comisiona
    # PVP = (Costo + Envio) / (1 - Comi - Margen - IIBB - IVA - Finan)
    divisor = (1 - t_comi - t_margen - t_iibb - t_iva - t_finan)
    pvp_sug = (costo_in + envio_v) / divisor if divisor > 0 else 0
else:
    # ME1: El envío NO comisiona. Se suma al final del cálculo de base.
    # PVP_Base = Costo / (1 - Comi - Margen - IIBB - IVA - Finan)
    # PVP_Total = PVP_Base + Envio
    divisor = (1 - t_comi - t_margen - t_iibb - t_iva - t_finan)
    pvp_sug = (costo_in / divisor) + envio_v if divisor > 0 else 0

# --- DASHBOARD ---
st.markdown(f"""
    <div class="dash-main">
        <div style="font-size: 0.8rem; letter-spacing: 2px;">PVP SUGERIDO FINAL</div>
        <div class="dash-price">${pvp_sug:,.0f}</div>
        <div style="color: #3B82F6; font-weight: bold;">OBJETIVO: {margen_obj}% NETO</div>
    </div>
""", unsafe_allow_html=True)

st.divider()

# --- EVALUADOR ---
p_comp = st.number_input("PRECIO COMPETENCIA A EVALUAR ($)", value=float(round(pvp_sug, 0)))

# Lógica de costos según sistema
e_real = envio_v if p_comp >= 33000 else 0.0
fijo = 3800.0 if p_comp < 33000 else 0.0

# Base imponible para comisión
base_comisionable = p_comp if "ME2" in tipo_me else (p_comp - e_real)

c_meli = base_comisionable * t_comi
c_fina = p_comp * t_finan
imp_iva = (p_comp - (p_comp / 1.21)) if tipo_iva == "Responsable Inscripto" else 0.0
imp_iibb = (p_comp / (1.21 if tipo_iva == "Responsable Inscripto" else 1)) * t_iibb

utilidad = p_comp - (c_meli + c_fina + imp_iva + imp_iibb + e_real + fijo) - costo_in
m_real = (utilidad / p_comp) if p_comp > 0 else 0

c1, c2 = st.columns(2)
with c1:
    st.markdown(f"""<div class="metric-card"><div style="font-size:0.7rem; color:gray;">GANANCIA NETA</div><div style="font-size:1.5rem; font-weight:bold; color:{'#10B981' if utilidad > 0 else '#EF4444'};">${utilidad:,.0f}</div></div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="metric-card"><div style="font-size:0.7rem; color:gray;">MARGEN REAL</div><div style="font-size:1.5rem; font-weight:bold; color:{'#10B981' if m_real >= t_margen else '#F59E0B'};">{m_real:.1%}</div></div>""", unsafe_allow_html=True)

with st.expander("📝 Desglose de Costos Detallado"):
    st.write(f"• **Envío:** ${e_real:,.2f} ({'No comisiona' if 'ME1' in tipo_me else 'Comisiona'})")
    st.write(f"• **Comisión MeLi:** ${c_meli:,.2f}")
    st.write(f"• **Carga Financiera:** ${c_fina:,.2f}")
    st.write(f"• **IVA + IIBB:** ${(imp_iva + imp_iibb):,.2f}")
    st.info(f"Total Gastos: ${(c_meli + c_fina + imp_iva + imp_iibb + e_real + fijo):,.2f}")

st.markdown('<a href="https://wa.me/5491165808113" style="display:block; background:#1E293B; color:white; text-align:center; padding:12px; border-radius:10px; text-decoration:none; font-weight:bold; margin-top:20px;">CONSULTA WHATSAPP</a>', unsafe_allow_html=True)
