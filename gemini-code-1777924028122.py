import streamlit as st

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="NQ | Sales Intelligence", layout="centered")

# =========================================================
# DATOS MAESTROS
# =========================================================
LOGISTICA = {
    "📦 Mercado Envíos": {
        "XS - Sobres (0.5kg)": 4800.0, "S - Pequeño (1-2kg)": 6200.0,
        "M - Mediano (5-10kg)": 10500.0, "L - Grande (15-25kg)": 17800.0,
        "XL - Muy Grande (30kg)": 23500.0
    },
    "🚚 Logística M1": {
        "Nivel 1 (chicos)": 29000.0, "Nivel 2 (Medianos)": 39500.0, "Nivel 3 (Pesados)": 48000.0
    },
    "🛵 Flex / Entregas Propias": {
        "Rango Local": 4800.0, "Rango GBA": 7500.0, "Rango Especial": 9500.0
    }
}

FINANCIACION = {
    "1 Pago": 0.0, "3 Pagos (7%)": 7.0, "6 Pagos (10%)": 10.0,
    "9 Pagos (13.5%)": 13.5, "12 Pagos (16%)": 16.0
}

CLAVE_CORRECTA = "MELIPRO_2026"

# --- CSS: DISEÑO SOBRIO Y PROFESIONAL ---
st.markdown("""
    <style>
    /* Tipografía y Fondo General */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .stApp { background-color: #F4F7F9; }

    /* Estilo de Inputs */
    .stNumberInput input, .stSelectbox div {
        background-color: white !important;
        border: 1px solid #D1D9E0 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        color: #1A202C !important;
    }

    /* Dashboard: Tarjeta Principal PVP */
    .dash-main {
        background-color: #0F172A; /* Azul Naval Oscuro */
        color: white;
        padding: 20px;
        border-radius: 8px;
        text-align: center;
        border-bottom: 5px solid #3B82F6;
        margin-bottom: 15px;
    }
    .dash-label { font-size: 0.9rem; text-transform: uppercase; letter-spacing: 2px; color: #94A3B8; }
    .dash-price { font-size: 3.5rem; font-weight: 900; color: #FFFFFF; margin: 10px 0; }
    .dash-margin { background: #1E293B; display: inline-block; padding: 5px 15px; border-radius: 20px; font-size: 0.9rem; color: #3B82F6; font-weight: bold; }

    /* Bloques de Datos Secundarios */
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-val { font-size: 1.5rem; font-weight: 700; color: #1E293B; }
    .metric-label { font-size: 0.75rem; color: #64748B; text-transform: uppercase; font-weight: bold; }

    /* Botón WhatsApp Sobrio */
    .btn-wa {
        background-color: #1E293B;
        color: white !important;
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        text-decoration: none;
        display: block;
        font-weight: bold;
        margin-top: 20px;
        border: 1px solid #334155;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("<h2 style='text-align: center; color: #0F172A;'>Control de Gestión</h2>", unsafe_allow_html=True)
    with st.container():
        clave_input = st.text_input("Acceso Protegido", type="password", placeholder="Ingrese Clave de Operador")
        if st.button("AUTENTICAR", use_container_width=True):
            if clave_input == CLAVE_CORRECTA:
                st.session_state.autenticado = True
                st.rerun()
            else: st.error("Acceso Denegado")
    st.stop()

# --- INTERFAZ DE TRABAJO ---
st.markdown("<h3 style='color: #0F172A;'>Panel de Rentabilidad</h3>", unsafe_allow_html=True)

# Sidebar para ajustes de fondo
with st.sidebar:
    st.title("Ajustes de Perfil")
    repu = st.selectbox("Reputación", ["Verde (50% desc)", "Amarilla (40% desc)", "Roja (0% desc)"])
    tipo_iva = st.radio("Condición Fiscal", ["Responsable Inscripto", "Monotributista"])
    iibb_perc = st.number_input("% IIBB", value=3.5)
    st.divider()
    if st.button("SALIR DEL SISTEMA"):
        st.session_state.autenticado = False
        st.rerun()

# --- BLOQUE DE ENTRADA ---
col_costo = st.container()
with col_costo:
    costo_in = st.number_input("COSTO UNITARIO DE COMPRA ($)", value=0.0, step=1000.0)

col1, col2 = st.columns(2)
with col1:
    cat_log = st.selectbox("LOGÍSTICA", list(LOGISTICA.keys()))
    comi_val = st.selectbox("% COMISIÓN", [10, 12, 14, 15, 16.5, 28], index=3)
with col2:
    tipo_bulto = st.selectbox("CATEGORÍA PESO", list(LOGISTICA[cat_log].keys()))
    finan_txt = st.selectbox("PLAN DE CUOTAS", list(FINANCIACION.keys()))

margen_target = st.slider("MARGEN NETO OBJETIVO (%)", 5, 40, 15)

# --- MOTOR DE CÁLCULO ---
bonif_log = 0.5 if "Verde" in repu else 0.6 if "Amarilla" in repu else 1.0
costo_envio = LOGISTICA[cat_log][tipo_bulto] * (1 if "Flex" in cat_log else bonif_log)
t_iva = 0.1735 if tipo_iva == "Responsable Inscripto" else 0.0
t_iibb = iibb_perc / 100
t_finan = FINANCIACION[finan_txt] / 100

divisor = (1 - (comi_val/100) - (margen_target/100) - t_iibb - t_iva - t_finan)
pvp_sug = (costo_in + costo_envio) / divisor if divisor > 0 else 0

# --- DASHBOARD PVP ---
st.markdown(f"""
    <div class="dash-main">
        <div class="dash-label">Precio de Venta Sugerido</div>
        <div class="dash-price">${pvp_sug:,.0f}</div>
        <div class="dash-margin">RENTABILIDAD FIJADA: {margen_target}%</div>
    </div>
""", unsafe_allow_html=True)

# --- EVALUACIÓN DE COMPETENCIA ---
st.divider()
p_comp = st.number_input("ANALIZAR PRECIO COMPETENCIA ($)", value=float(round(pvp_sug, 0)))

e_real = costo_envio if p_comp >= 33000 else 0.0
fijo = 3800.0 if p_comp < 33000 else 0.0
c_meli = p_comp * (comi_val/100)
c_finan = p_comp * t_finan
imp_iva = (p_comp - (p_comp / 1.21)) if tipo_iva == "Responsable Inscripto" else 0.0
imp_iibb = (p_comp / (1.21 if tipo_iva == "Responsable Inscripto" else 1)) * t_iibb

utilidad_neta = p_comp - (c_meli + c_finan + imp_iva + imp_iibb + e_real + fijo) - costo_in
margen_real = (utilidad_neta / p_comp) if p_comp > 0 else 0

# KPIs Secundarios
c1, c2 = st.columns(2)
with c1:
    st.markdown(f"""<div class="metric-card"><div class="metric-label">Ganancia Neta</div><div class="metric-val" style="color:{'#10B981' if utilidad_neta > 0 else '#EF4444'};">${utilidad_neta:,.0f}</div></div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="metric-card"><div class="metric-label">Margen Real</div><div class="metric-val" style="color:{'#10B981' if margen_real >= (margen_target/100) else '#F59E0B'};">{margen_real:.1%}</div></div>""", unsafe_allow_html=True)

# --- DESGLOSE TÉCNICO ---
with st.expander("📥 DETALLE TÉCNICO DE LA OPERACIÓN"):
    st.write(f"**Logística Final:** ${e_real:,.2f}")
    st.write(f"**Comisiones:** ${c_meli:,.2f}")
    st.write(f"**Carga Financiera:** ${c_finan:,.2f}")
    st.write(f"**Carga Impositiva (IVA+IIBB):** ${(imp_iva + imp_iibb):,.2f}")
    st.write(f"**Costo Fijo Unitario:** ${fijo:,.2f}")
    st.info(f"Capital de Compra: ${costo_in:,.2f}")

st.markdown('<a href="https://wa.me/5491165808113" class="btn-wa">CONSULTA TÉCNICA WHATSAPP</a>', unsafe_allow_html=True)
