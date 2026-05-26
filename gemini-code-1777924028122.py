import streamlit as st

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="NQ | Intelligence Dashboard", layout="centered")

# =========================================================
# DATOS MAESTROS VIGENTES 2026
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

FINANCIACION = {
    "1 Pago": 0.0,
    "3 Cuotas (5% Promo)": 5.0,
    "3 Cuotas (8.40% Actual)": 8.40,
    "6 Cuotas (12.30% Actual)": 12.30,
    "9 Cuotas (15.70% Actual)": 15.70,
    "12 Cuotas (19.20% Actual)": 19.20
}

DICT_CATEGORIAS = {
    "Muebles RTA (Cajas optimizadas)": {"tipo": "Volumen", "full": "Recomendado", "nota": "NQ Score: Alta rotación."},
    "Muebles Pesados (ME1)": {"tipo": "Especialista", "full": "No", "nota": "NQ Score: Margen protegido."},
    "Bazar y Organización": {"tipo": "Multirrubro", "full": "Obligatorio", "nota": "NQ Score: Competencia alta."},
    "Herramientas / Jardín": {"tipo": "Técnico", "full": "Opcional", "nota": "NQ Score: Estacional."},
    "Categoría General": {"tipo": "Genérico", "full": "Variable", "nota": "NQ Score: Evaluar margen."}
}

CLAVE_CORRECTA = "NQ_PRO_2026"

# --- CSS: ESTÉTICA NUBIMETRICS / NQ ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background-color: #F9FAFB; }

    /* Header NQ */
    .nq-header {
        display: flex; align-items: center; justify-content: center;
        padding: 25px; background: white; border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 30px;
    }
    .nq-logo {
        background: #4F46E5; color: white; padding: 10px 18px;
        border-radius: 12px; font-weight: 800; font-size: 1.5rem;
        margin-right: 15px; letter-spacing: -1px;
    }
    .nq-title { color: #111827; font-weight: 700; font-size: 1.2rem; margin: 0; }
    
    /* Píldoras de Impuestos */
    .tax-bar {
        background: #F3F4F6; padding: 15px; border-radius: 12px;
        margin-bottom: 25px; border: 1px solid #E5E7EB;
    }

    /* Cards de Resultados Estilo Nubimetrics */
    .card-res {
        background: white; border-radius: 16px; padding: 30px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); text-align: center;
        border-top: 4px solid #4F46E5; margin: 20px 0;
    }
    .card-res-inv {
        background: white; border-radius: 16px; padding: 30px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); text-align: center;
        border-top: 4px solid #10B981; margin: 20px 0;
    }
    .label-res { color: #6B7280; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
    .price-res { color: #111827; font-size: 3.5rem; font-weight: 800; margin: 10px 0; }
    .badge-res { background: #EEF2FF; color: #4F46E5; padding: 5px 15px; border-radius: 99px; font-size: 0.9rem; font-weight: 700; }

    /* Inputs */
    .stNumberInput input, .stSelectbox div {
        border-radius: 10px !important; border: 1px solid #D1D5DB !important;
    }
    
    /* Botones */
    .stButton button {
        background: #4F46E5 !important; color: white !important;
        border-radius: 10px !important; width: 100%; border: none !important;
        padding: 10px !important; font-weight: 700 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("<div style='text-align:center; margin-top:100px;'><span class='nq-logo'>NQ</span></div>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1,2,1])
    with col_l2:
        clave = st.text_input("Access Key", type="password", placeholder="Operador NQ")
        if st.button("UNLOCK DASHBOARD"):
            if clave == CLAVE_CORRECTA:
                st.session_state.autenticado = True
                st.rerun()
            else: st.error("Acceso denegado")
    st.stop()

# --- HEADER NQ ---
st.markdown("""
    <div class='nq-header'>
        <span class='nq-logo'>NQ</span>
        <div class='nq-title'>INTELLIGENCE | Sales & Market Analysis</div>
    </div>
""", unsafe_allow_html=True)

# --- MATRIZ FISCAL SIEMPRE VISIBLE ---
with st.container():
    st.markdown("<div class='tax-bar'>", unsafe_allow_html=True)
    c_tax1, c_tax2, c_tax3 = st.columns([2,1,1])
    with c_tax1:
        tipo_iva = st.radio("Condición Fiscal del Vendedor", ["Responsable Inscripto", "Monotributista"], horizontal=True)
    with c_tax2:
        iibb_perc = st.number_input("% IIBB", value=3.5, step=0.1)
    with c_tax3:
        repu = st.selectbox("Reputación", ["Verde (50% desc)", "Amarilla (40% desc)", "Roja (0% desc)"])
    st.markdown("</div>", unsafe_allow_html=True)

bonif = 0.5 if "Verde" in repu else 0.6 if "Amarilla" in repu else 1.0
t_iva = 0.1735 if tipo_iva == "Responsable Inscripto" else 0.0
t_iibb = iibb_perc / 100

# --- TABS ---
tab1, tab2 = st.tabs(["📊 CALCULAR PVP SUGERIDO", "🔍 ANALIZAR COSTO OBJETIVO"])

# =========================================================
# SOLAPA 1: PVP (Directo)
# =========================================================
with tab1:
    col_s1_a, col_s1_b = st.columns(2)
    with col_s1_a:
        costo_in = st.number_input("Costo de Fábrica ($)", value=0.0, step=1000.0)
        tipo_me = st.radio("Envío", ["ME2 (Normal/Full)", "ME1 (Pesados)"], horizontal=True)
    with col_s1_b:
        peso_cat = st.selectbox("Categoría Peso Correo", list(TABLA_ME1.keys()))
        margen_obj = st.slider("% Margen Neto Deseado", 5, 40, 15)

    col_s1_c, col_s1_d = st.columns(2)
    with col_s1_c: comi_p = st.selectbox("% Comisión MeLi", [10, 12, 14, 15, 16.5, 28], index=2)
    with col_s1_d: plan_f = st.selectbox("Cuotas al Cliente", list(FINANCIACION.keys()), index=3)

    envio_v = TABLA_ME1[peso_cat] * bonif
    t_finan = FINANCIACION[plan_f] / 100
    t_comi = comi_p / 100
    t_margen = margen_obj / 100
    divisor = (1 - t_comi - t_margen - t_iibb - t_iva - t_finan)
    
    pvp_sug = (costo_in + envio_v) / divisor if "ME2" in tipo_me else (costo_in / divisor) + envio_v if divisor > 0 else 0

    st.markdown(f"""
        <div class='card-res'>
            <div class='label-res'>Precio de Venta Sugerido</div>
            <div class='price-res'>${pvp_sug:,.0f}</div>
            <span class='badge-res'>OBJETIVO NETO: {margen_obj}%</span>
        </div>
    """, unsafe_allow_html=True)

    if pvp_sug > 0:
        with st.expander("📊 Ver Desglose NQ de Rentabilidad"):
            p_meli = pvp_sug * t_comi if "ME2" in tipo_me else (pvp_sug - envio_v) * t_comi
            p_finan = pvp_sug * t_finan
            p_iva = (pvp_sug - (pvp
