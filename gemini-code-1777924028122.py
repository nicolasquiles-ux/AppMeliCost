import streamlit as st

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Centro Estant | Sales Intelligence V12", layout="centered")

# =========================================================
# DATOS MAESTROS ACTUALIZADOS (image_433f6d.png)
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

# Nuevas tasas vigentes de Mercado Libre
FINANCIACION = {
    "1 Pago": 0.0,
    "3 Cuotas (5% Promo)": 5.0,
    "3 Cuotas (8.40% Actual)": 8.40,
    "6 Cuotas (12.30% Actual)": 12.30,
    "9 Cuotas (15.70% Actual)": 15.70,
    "12 Cuotas (19.20% Actual)": 19.20
}

CLAVE_CORRECTA = "CENTRO_PRO_2026"

# --- CSS: DISEÑO SOBRIO Y PROFESIONAL ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F4F7F9; }

    .stNumberInput input, .stSelectbox div {
        background-color: white !important;
        border: 1px solid #D1D9E0 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        color: #1A202C !important;
    }

    /* Estructura del Dashboard */
    .dash-main {
        background-color: #0F172A; color: white; padding: 30px;
        border-radius: 12px; text-align: center;
        border-bottom: 5px solid #3B82F6; margin-bottom: 25px;
    }
    .dash-main-inverse {
        background-color: #1E293B; color: white; padding: 30px;
        border-radius: 12px; text-align: center;
        border-bottom: 5px solid #10B981; margin-bottom: 25px;
    }
    .dash-label { font-size: 0.9rem; text-transform: uppercase; letter-spacing: 2px; color: #94A3B8; }
    .dash-price { font-size: 3.5rem; font-weight: 900; color: #FFFFFF; margin: 10px 0; }
    .dash-margin { background: #0F172A; display: inline-block; padding: 5px 15px; border-radius: 20px; font-size: 0.9rem; color: #10B981; font-weight: bold; }

    .btn-wa {
        background-color: #1E293B; color: white !important; padding: 12px;
        border-radius: 8px; text-align: center; text-decoration: none;
        display: block; font-weight: bold; margin-top: 20px; border: 1px solid #334155;
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

# --- SIDEBAR (Ajustes fiscales fijos) ---
with st.sidebar:
    st.title("Ajustes de Perfil")
    repu = st.selectbox("Reputación", ["Verde (50% desc)", "Amarilla (40% desc)", "Roja (0% desc)"])
    tipo_iva = st.radio("Condición Fiscal", ["Responsable Inscripto", "Monotributista"])
    iibb_perc = st.number_input("% IIBB", value=3.5)
    st.divider()
    if st.button("SALIR DEL SISTEMA"):
        st.session_state.autenticado = False
        st.rerun()

# --- PESTAÑAS DE NAVEGACIÓN DUAL ---
tab1, tab2 = st.tabs(["➡️ CALCULAR PVP SUGERIDO", "⬅️ ANALIZAR COSTO OBJETIVO"])

bonif = 0.5 if "Verde" in repu else 0.6 if "Amarilla" in repu else 1.0
t_iva = 0.1735 if tipo_iva == "Responsable Inscripto" else 0.0
t_iibb = iibb_perc / 100

# =========================================================
# PESTAÑA 1: CAMINO DIRECTO (Costo -> PVP)
# =========================================================
with tab1:
    st.markdown("<h4 style='color: #0F172A;'>¿A cuánto tengo que vender con las nuevas tasas?</h4>", unsafe_allow_html=True)
    
    costo_in = st.number_input("COSTO UNITARIO DE COMPRA ($)", value=0.0, step=1000.0, key="c_directo")
    tipo_me = st.radio("SISTEMA DE ENVÍO", ["ME2 (Colecta/Full - Comisiona)", "ME1 (Muebles Pesados - No Comisiona)"], horizontal=True, key="me_directo")
    peso_cat = st.selectbox("PESO / AFORADO", list(TABLA_ME1.keys()), key="peso_directo")
    
    col1, col2 = st.columns(2)
    with col1:
        comi_p = st.selectbox("% COMISIÓN MELI", [10, 12, 14, 15, 16.5, 28], index=2, key='comi_dir')
    with col2:
        plan_f = st.selectbox("PLAN DE CUOTAS (NUEVAS TASAS)", list(FINANCIACION.keys()), index=3, key='finan_dir') # Index 3 apunta a 6 cuotas por defecto
        
    margen_obj = st.slider("% MARGEN NETO DESEADO", 5, 40, 15, key='margen_dir')

    envio_v = TABLA_ME1[peso_cat] * bonif
    t_finan = FINANCIACION[plan_f] / 100
    t_comi = comi_p / 100
    t_margen = margen_obj / 100

    divisor = (1 - t_comi - t_margen - t_iibb - t_iva - t_finan)
    
    if "ME2" in tipo_me:
        pvp_sug = (costo_in + envio_v) / divisor if divisor > 0 else 0
    else:
        pvp_sug = (costo_in / divisor) + envio_v if divisor > 0 else 0

    st.markdown(f"""
        <div class="dash-main">
            <div class="dash-label">Precio de Venta Sugerido</div>
            <div class="dash-price">${pvp_sug:,.0f}</div>
            <div style="color: #3B82F6; font-weight: bold;">OBJETIVO NETO: {margen_obj}%</div>
        </div>
    """, unsafe_allow_html=True)

# =========================================================
# PESTAÑA 2: CAMINO INVERSO (PVP -> Costo Máximo de Compra)
# =========================================================
with tab2:
    st.markdown("<h4 style='color: #0F172A;'>¿Cuánto puedo pagar este producto con la baja de tasas?</h4>", unsafe_allow_html=True)
    
    pvp_target = st.number_input("PRECIO DE VENTA OBJETIVO / COMPETENCIA ($)", value=0.0, step=1000.0, key="pvp_inverso")
    tipo_me_inv = st.radio("SISTEMA DE ENVÍO", ["ME2 (Colecta/Full - Comisiona)", "ME1 (Muebles Pesados - No Comisiona)"], horizontal=True, key="me_inverso")
    peso_cat_inv = st.selectbox("PESO / AFORADO", list(TABLA_ME1.keys()), key="peso_inverso")
    
    col3, col4 = st.columns(2)
    with col3:
        comi_p_inv = st.selectbox("% COMISIÓN MELI", [10, 12, 14, 15, 16.5, 28], index=2, key='comi_inv')
    with col4:
        plan_f_inv = st.selectbox("PLAN DE CUOTAS (NUEVAS TASAS)", list(FINANCIACION.keys()), index=3, key='finan_inv')
        
    margen_obj_inv = st.slider("% MARGEN NETO QUE QUIERO GANAR", 5, 40, 15, key='margen_inv')

    envio_v_inv = TABLA_ME1[peso_cat_inv] * bonif
    fijo_inv = 3800.0 if pvp_target < 33000 and pvp_target > 0 else 0.0
    envio_real_inv = envio_v_inv if pvp_target >= 33000 else 0.0

    t_finan_inv = FINANCIACION[plan_f_inv] / 100
    t_comi_inv = comi_p_inv / 100
    t_margen_inv = margen_obj_inv / 100

    c_fina_inv = pvp_target * t_finan_inv
    imp_iva_inv = (pvp_target - (pvp_target / 1.21)) if tipo_iva == "Responsable Inscripto" else 0.0
    imp_iibb_inv = (pvp_target / (1.21 if tipo_iva == "Responsable Inscripto" else 1)) * t_iibb
    margen_pesos_inv = pvp_target * t_margen_inv

    if "ME2" in tipo_me_inv:
        c_meli_inv = pvp_target * t_comi_inv
    else:
        base_comisionable_inv = pvp_target - envio_real_inv
        c_meli_inv = max(0.0, base_comisionable_inv * t_comi_inv)

    costo_maximo = pvp_target - (c_meli_inv + c_fina_inv + imp_iva_inv + imp_iibb_inv + envio_real_inv + fijo_inv + margen_pesos_inv)

    if pvp_target == 0: costo_maximo = 0

    st.markdown(f"""
        <div class="dash-main-inverse">
            <div class="dash-label">Costo Máximo de Compra Admitido</div>
            <div class="dash-price" style="color: #10B981;">${max(0.0, costo_maximo):,.0f}</div>
            <div class="dash-margin">CUIDANDO TU MARGEN DEL: {margen_obj_inv}%</div>
        </div>
    """, unsafe_allow_html=True)

    with st.expander("📥 DESGLOSE DE COSTOS CON LA NUEVA FINANCIACIÓN"):
        st.write(f"• **Tu Margen Neto en Pesos:** ${margen_pesos_inv:,.2f}")
        st.write(f"• **Costo Financiero (Bajo al {FINANCIACION[plan_f_inv]}%):** ${c_fina_inv:,.2f}")
        st.write(f"• **Envío Neto:** ${envio_real_inv:,.2f}")
        st.write(f"• **Comisión MeLi:** ${c_meli_inv:,.2f}")
        st.write(f"• **Impuestos consolidados (IVA+IIBB):** ${(imp_iva_inv + imp_iibb_inv):,.2f}")

st.markdown('<a href="https://wa.me/5491165808113" class="btn-wa">CONSULTA TÉCNICA WHATSAPP</a>', unsafe_allow_html=True)
import streamlit as st

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Centro Estant | Sales Intelligence V13", layout="centered")

# =========================================================
# DATOS MAESTROS
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

CLAVE_CORRECTA = "CENTRO_PRO_2026"

# --- CSS: DISEÑO SOBRIO Y PROFESIONAL ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F4F7F9; }

    .stNumberInput input, .stSelectbox div {
        background-color: white !important;
        border: 1px solid #D1D9E0 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        color: #1A202C !important;
    }

    .dash-main {
        background-color: #0F172A; color: white; padding: 30px;
        border-radius: 12px; text-align: center;
        border-bottom: 5px solid #3B82F6; margin-bottom: 25px;
    }
    .dash-main-inverse {
        background-color: #1E293B; color: white; padding: 30px;
        border-radius: 12px; text-align: center;
        border-bottom: 5px solid #10B981; margin-bottom: 25px;
    }
    .dash-label { font-size: 0.9rem; text-transform: uppercase; letter-spacing: 2px; color: #94A3B8; }
    .dash-price { font-size: 3.5rem; font-weight: 900; color: #FFFFFF; margin: 10px 0; }
    .dash-margin { background: #0F172A; display: inline-block; padding: 5px 15px; border-radius: 20px; font-size: 0.9rem; color: #10B981; font-weight: bold; }

    .btn-wa {
        background-color: #1E293B; color: white !important; padding: 12px;
        border-radius: 8px; text-align: center; text-decoration: none;
        display: block; font-weight: bold; margin-top: 20px; border: 1px solid #334155;
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
            if clave_input == CLRECTA := CLAVE_CORRECTA:
                st.session_state.autenticado = True
                st.rerun()
            else: st.error("Acceso Denegado")
    st.stop()

# --- SIDEBAR (Ajustes de Perfil) ---
with st.sidebar:
    st.title("Ajustes de Perfil")
    repu = st.selectbox("Reputación", ["Verde (50% desc)", "Amarilla (40% desc)", "Roja (0% desc)"])
    tipo_iva = st.radio("Condición Fiscal", ["Responsable Inscripto", "Monotributista"])
    iibb_perc = st.number_input("% IIBB", value=3.5)
    st.divider()
    if st.button("SALIR DEL SISTEMA"):
        st.session_state.autenticado = False
        st.rerun()

# --- PESTAÑAS DUALES ---
tab1, tab2 = st.tabs(["➡️ CALCULAR PVP SUGERIDO", "⬅️ CALCULAR COSTO MÁXIMO ADMITIDO"])

bonif = 0.5 if "Verde" in repu else 0.6 if "Amarilla" in repu else 1.0
t_iva = 0.1735 if tipo_iva == "Responsable Inscripto" else 0.0
t
