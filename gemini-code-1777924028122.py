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
            p_iva = (pvp_sug - (pvp_sug / 1.21)) if tipo_iva == "Responsable Inscripto" else 0.0
            p_iibb = (pvp_sug / (1.21 if tipo_iva == "Responsable Inscripto" else 1)) * t_iibb
            p_margen = pvp_sug * t_margen
            st.write(f"• **Fábrica:** ${costo_in:,.0f} | **Ganancia Neta:** ${p_margen:,.0f}")
            st.write(f"• **Comisión:** ${p_meli:,.0f} | **Financiación:** ${p_finan:,.0f}")
            st.write(f"• **Logística:** ${envio_v:,.0f} | **Impuestos:** ${(p_iva + p_iibb):,.0f}")

# =========================================================
# SOLAPA 2: COSTO OBJETIVO (Inverso)
# =========================================================
with tab2:
    cat_sel = st.selectbox("Categoría Estratégica", list(DICT_CATEGORIAS.keys()))
    info_cat = DICT_CATEGORIAS[cat_sel]
    st.info(f"💡 {info_cat['nota']} | Full: {info_cat['full']}")

    col_inv_a, col_inv_b = st.columns(2)
    with col_inv_a:
        pvp_target = st.number_input("PVP Competencia ($)", value=0.0, step=1000.0)
    with col_inv_b:
        margen_exi = st.slider("% Margen Neto Exigido", 5, 40, 15)

    # DICCIONARIOS EXPLICITOS DE DATOS
    dict_mercado = {"Normal": 1.0, "Baja 5%": 0.95, "Inflado 10%": 0.9}
    dict_proveedor = {"Contado": 0.0, "30 días (+3%)": 0.03, "60 días (+6%)": 0.06}

    with st.expander("🛠️ Pilares Avanzados de Compra"):
        opc_m = st.selectbox("Fluctuación de Mercado", list(dict_mercado.keys()))
        d_merc_val = dict_mercado[opc_m]
        
        opc_p = st.selectbox("Pago a Fábrica", list(dict_proveedor.keys()))
        d_prov_val = dict_proveedor[opc_p]
        
        ocultos = st.slider("% Cobertura Estructura/Roturas", 0.0, 5.0, 1.5)

    tipo_me_inv = st.radio("Envío ", ["ME2", "ME1"], horizontal=True, key="me_inv_i")
    peso_cat_inv = st.selectbox("Categoría Peso ", list(TABLA_ME1.keys()), key="peso_inv_i")
    
    col_inv_c, col_inv_d = st.columns(2)
    with col_inv_c: com_inv = st.selectbox("% Comisión Plataforma", [10, 12, 14, 15, 16.5, 28], index=2, key="c_inv_i")
    with col_inv_d: plan_inv = st.selectbox("Financiación Cliente", list(FINANCIACION.keys()), index=3, key="f_inv_i")

    # --- MOTOR MATEMÁTICO INVERSO SIN ERRORES ---
    pvp_aj = float(pvp_target) * float(d_merc_val)
    env_v_i = TABLA_ME1[peso_cat_inv] * bonif
    fijo_i = 3800.0 if pvp_aj < 33000 and pvp_aj > 0 else 0.0
    env_real_i = env_v_i if pvp_aj >= 33000 else 0.0
    
    t_marg_i = margen_exi / 100
    c_meli_i = pvp_aj * (com_inv/100) if tipo_me_inv == "ME2" else (pvp_aj - env_real_i) * (com_inv/100)
    c_finan_i = pvp_aj * (FINANCIACION[plan_inv]/100)
    iva_i = (pvp_aj - (pvp_aj / 1.21)) if tipo_iva == "Responsable Inscripto" else 0.0
    iibb_i = (pvp_aj / (1.21 if tipo_iva == "Responsable Inscripto" else 1)) * t_iibb
    ocu_i = pvp_aj * (ocultos / 100)
    marg_p_i = pvp_aj * t_marg_i

    costo_max = (pvp_aj - (c_meli_i + c_finan_i + iva_i + iibb_i + env_real_i + fijo_i + marg_p_i + ocu_i)) / (1.0 + float(d_prov_val))

    if pvp_target == 0: costo_max = 0

    st.markdown(f"""
        <div class='card-res-inv'>
            <div class='label-res'>Costo Máximo de Compra Admitido</div>
            <div class='price-res' style='color: #10B981;'>${max(0.0, costo_max):,.0f}</div>
            <span class='badge-res' style='color: #10B981; background: #ECFDF5;'>MARGEN ASEGURADO: {margen_exi}%</span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📊 Simulación de Volumen NQ")
    col_v1, col_v2 = st.columns(2)
    with col_v1: q_mes = st.number_input("Unidades / Mes", value=10, min_value=1)
    with col_v2: c_real = st.number_input("Costo Cotizado por Fábrica ($)", value=0.0, step=1000.0)

    if pvp_target > 0 and c_real > 0:
        inv_tot = c_real * q_mes
        gan_un = marg_p_i + (costo_max - c_real)
        gan_tot = gan_un * q_mes
        roi = (gan_tot / inv_tot) * 100 if inv_tot > 0 else 0
        
        st.markdown(f"""
            <div style='background: white; padding: 20px; border-radius: 12px; border: 1px solid #E5E7EB; display: flex; justify-content: space-around; text-align: center;'>
                <div><span style='color: #6B7280; font-size: 0.8rem;'>Inversión Stock</span><br><strong>${inv_tot:,.0f}</strong></div>
                <div><span style='color: #6B7280; font-size: 0.8rem;'>Ganancia Total</span><br><strong style='color: #10B981;'>${gan_tot:,.0f}</strong></div>
                <div><span style='color: #6B7280; font-size: 0.8rem;'>ROI Bruto</span><br><strong style='color: #4F46E5;'>{roi:.1f}%</strong></div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='text-align:center; padding: 30px;'><p style='color:#94A3B8; font-size:0.8rem;'>NQ Intelligence System v16.1 | Argentina 2026</p></div>", unsafe_allow_html=True)
