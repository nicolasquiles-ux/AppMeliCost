import streamlit as st

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="NQ | Sales Intelligence Dashboard", layout="wide")

# =========================================================
# DATOS MAESTROS VIGENTES 2026 (NQ Database)
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

FINANCIACION_PRESETS = {
    "1 Pago (0%)": 0.0,
    "3 Cuotas (8.40%)": 8.40,
    "6 Cuotas (12.30%)": 12.30,
    "9 Cuotas (15.70%)": 15.70,
    "12 Cuotas (19.20%)": 19.20,
    "Personalizado (Manual)": -1.0
}

CLAVE_CORRECTA = "NQ_PRO_2026"

# Colores corporativos NQ / Nubimetrics Style
nq_main_color = "#2B3E4F" 
nq_green = "#1E8449"       
nq_gold = "#BFA100"        
gray_bg = "#F3F5F7"       

# =========================================================
# INYECCIÓN DE CSS SEGURO (Limpio de llaves conflictivas)
# =========================================================
css_template = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');

html, body, [class*="css"] { 
    font-family: 'Plus Jakarta Sans', sans-serif; 
    background-color: #FFFFFF; 
}
.stApp { background-color: #FFFFFF; }

/* --- HEADER NQ REAL-DATA --- */
.nq-header-container {
    display: flex; align-items: center; justify-content: space-between;
    padding: 20px 30px; background-color: #FFFFFF;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 25px;
    border-radius: 12px; border: 1px solid #E5E7EB;
}
.nq-branding { display: flex; align-items: center; }
.nq-logo {
    background: linear-gradient(135deg, #0055A0 0%, #00BFBF 100%);
    color: white; padding: 12px 20px; border-radius: 12px; 
    font-weight: 800; font-size: 1.6rem; margin-right: 18px; letter-spacing: -1px;
}
.nq-title-group { display: flex; flex-direction: column; }
.nq-title-country { color: #7F8C8D; font-size: 0.85rem; font-weight: 600; }
.nq-dashboard { color: NQ_MAIN_COLOR; font-weight: 700; font-size: 1.3rem; margin-top: 2px; }
.nq-title-date { color: #7F8C8D; font-size: 0.8rem; margin-top: 3px; }

/* --- DONUT CHART SYSTEM --- */
.donut-chart-container { display: flex; align-items: center; gap: 12px; margin-top: 8px; }
.donut-block { 
    width: 40px; height: 40px; border-radius: 50%; 
    position: relative; 
}
.donut-block::after { 
    content: ''; width: 24px; height: 24px; border-radius: 50%; 
    position: absolute; top: 8px; left: 8px; 
}
/* Variantes de fondo para dona interna según contenedor */
.banner-strict .donut-block::after { background: NQ_GREEN; }
.banner-dark .donut-block::after { background: NQ_MAIN_COLOR; }

.donut-text-group { display: flex; flex-direction: column; font-size: 0.85rem; }
.donut-main-val { font-weight: 700; }
.donut-sub-val { opacity: 0.85; font-size: 0.75rem; }

/* --- SECCIONES DE CONTROL --- */
.tax-bar {
    background-color: GRAY_BG; padding: 20px; border-radius: 12px;
    margin-bottom: 25px; border: 1px solid #E5E7EB;
}

/* --- BANNER DE RESULTADOS NUBIMETRICS REAL-DATA --- */
.results-main-container {
    display: flex; border-radius: 16px; overflow: hidden;
    margin-top: 25px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05);
    border: 1px solid #E5E7EB;
}
.cost-breakdown-list {
    flex: 1.2; background-color: #FFFFFF; padding: 25px;
    display: flex; flex-direction: column; justify-content: center; gap: 12px;
}
.cost-item { 
    display: flex; justify-content: space-between; font-size: 0.9rem; 
    border-bottom: 1px solid #F3F4F6; padding-bottom: 6px;
}
.cost-label { color: #6B7280; font-weight: 600; }
.cost-value { color: #111827; font-weight: 700; text-align: right; }

.banner-strict {
    flex: 1.4; background-color: NQ_GREEN; color: white; padding: 30px;
    display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; gap: 4px;
}
.banner-loose {
    flex: 1.4; background-color: NQ_GOLD; color: white; padding: 30px;
    display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; gap: 4px;
}
.banner-dark {
    flex: 1.4; background-color: NQ_MAIN_COLOR; color: white; padding: 30px;
    display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; gap: 4px;
}

.label-banner { color: rgba(255,255,255,0.85); font-size: 0.9rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
.price-main { color: white; font-size: 2.4rem; font-weight: 800; margin: 2px 0; }
.badge-banner {
    background: rgba(255,255,255,0.2); color: white;
    padding: 4px 14px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; margin-top: 4px;
}
</style>
""".replace("NQ_MAIN_COLOR", nq_main_color).replace("NQ_GREEN", nq_green).replace("NQ_GOLD", nq_gold).replace("GRAY_BG", gray_bg)

st.markdown(css_template, unsafe_allow_html=True)

# --- SISTEMA DE LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    col_l1, col_l2, col_l3 = st.columns([1,1.5,1])
    with col_l2:
        st.markdown("<div style='text-align:center; margin-top:100px;'><span class='nq-logo'>NQ</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center; padding: 20px 0;'><h2 style='color: {nq_main_color}; font-weight:900;'>NQ INTELLIGENCE LOGIN</h2></div>", unsafe_allow_html=True)
        clave_input = st.text_input("Ingresa Clave Operador", type="password", placeholder="Access Key")
        if st.button("DESBLOQUEAR SISTEMA", use_container_width=True):
            if clave_input == CLAVE_CORRECTA:
                st.session_state.autenticado = True
                st.rerun()
            else: st.error("Clave incorrecta")
    st.stop()

# =========================================================
# ENCABEZADO CORPORATIVO (Limpio y Profesional)
# =========================================================
st.markdown("""
    <div class="nq-header-container">
        <div class="nq-branding">
            <span class="nq-logo">NQ</span>
            <div class="nq-title-group">
                <div class="nq-title-country">NQ Argentina</div>
                <div class="nq-dashboard">NQ | Sales Intelligence Matrix</div>
                <div class="nq-title-date">Operador Autenticado | Simulación de Costos Real-Time</div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# =========================================================
# CONTROL MATRIZ FISCAL (Afecta a Solapa 2 Directa)
# =========================================================
with st.container():
    st.markdown("<div class='tax-bar'>", unsafe_allow_html=True)
    c_tax1, c_tax2, c_tax3 = st.columns([2,1,1])
    with c_tax1:
        tipo_iva = st.radio("Configuración Impositiva Real", ["Responsable Inscripto", "Monotributista"], horizontal=True)
    with c_tax2:
        iibb_perc = st.number_input("% Ingresos Brutos (IIBB)", value=3.5, step=0.1)
    with c_tax3:
        repu = st.selectbox("Nivel de Reputación Cuenta", ["Verde (50% desc)", "Amarilla (40% desc)", "Roja (0% desc)"])
    st.markdown("</div>", unsafe_allow_html=True)

bonif = 0.5 if "Verde" in repu else 0.6 if "Amarilla" in repu else 1.0
t_iva = 0.1735 if tipo_iva == "Responsable Inscripto" else 0.0
t_iibb = iibb_perc / 100

# --- TABS DE OPERACIÓN ---
tab1, tab2 = st.tabs(["📊 ANALIZAR COSTO OBJETIVO (Inverso)", "☝️ CALCULAR PVP SUGERIDO (Directo)"])

# =========================================================
# SOLAPA 1: ANÁLISIS COSTO OBJETIVO (PVP -> FÁBRICA)
# =========================================================
with tab1:
    st.markdown(f"<div style='background-color: {gray_bg}; padding: 25px; border-radius: 12px; margin-bottom: 20px;'>", unsafe_allow_html=True)
    c_inv_1, c_inv_2, c_inv_3, c_inv_4, c_inv_5 = st.columns([1.2, 1.2, 1, 1.5, 1])
    
    with c_inv_1:
        pvp_target = st.number_input("PVP Competencia Mercado ($)", value=0.0, step=1000.0, key="p_target_k")
    with c_inv_2:
        margen_exi = st.slider("% Margen Neto Requerido", 5, 40, 15, key="m_exi_k")
    with c_inv_3:
        tipo_me_inv = st.selectbox("Logística", ["ME2 (Normal/Full)", "ME1 (Pesados)"], key="t_me_inv_k")
    with c_inv_4:
        plan_selected_inv = st.selectbox("Plan de Financiamiento", list(FINANCIACION_PRESETS.keys()), index=2, key="plan_inv_k")
        if plan_selected_inv == "Personalizado (Manual)":
            t_finan_val_inv = st.number_input("% Tasa Custom", value=10.0, step=0.1, key="custom_fin_inv") / 100
        else:
            t_finan_val_inv = FINANCIACION_PRESETS[plan_selected_inv] / 100
    with c_inv_5:
        peso_cat_inv = st.selectbox("Peso Correo", list(TABLA_ME1.keys()), key="peso_inv_k")

    st.markdown("</div>", unsafe_allow_html=True)

    if pvp_target > 0:
        envio_cost_inv = TABLA_ME1[peso_cat_inv] * bonif
        fijo_inv = 3800.0 if pvp_target < 33000 else 0.0
        envio_real_inv = envio_cost_inv if pvp_target >= 33000 else 0.0

        t_comi_inv = 14 / 100 
        p_meli_inv = pvp_target * t_comi_inv
        p_finan_inv = pvp_target * t_finan_val_inv
        
        # Estrategia Nico: Forzamos siempre el IVA de Responsable Inscripto para armar el "colchón impositivo"
        p_iva_inv = (pvp_target - (pvp_target / 1.21))
        p_iibb_inv = (pvp_target / 1.21) * t_iibb
        p_margen_inv = pvp_target * (margen_exi / 100)

        costo_max_admitido = pvp_target - (p_meli_inv + p_finan_inv + p_iva_inv + p_iibb_inv + envio_real_inv + fijo_inv + p_margen_inv)

        st.markdown(f"""
            <div class="results-main-container">
                <div class="cost-breakdown-list">
                    <div class="cost-item"><span class="cost-label">Comisión MeLi (14%)</span><span class="cost-value">${p_meli_inv:,.2f}</span></div>
                    <div class="cost-item"><span class="cost-label">Costo Financiero Plan</span><span class="cost-value">${p_finan_inv:,.2f}</span></div>
                    <div class="cost-item"><span class="cost-label">Reserva IVA (Colchón RI 21%)</span><span class="cost-value">${p_iva_inv:,.2f}</span></div>
                    <div class="cost-item"><span class="cost-label">Ingresos Brutos Simulado</span><span class="cost-value">${p_iibb_inv:,.2f}</span></div>
                    <div class="cost-item"><span class="cost-label">Logística Asignada</span><span class="cost-value">${envio_real_inv:,.2f}</span></div>
                </div>
                <div class="banner-strict">
                    <div class="label-banner">PVP de Referencia</div>
                    <div class="price-main">${pvp_target:,.0f}</div>
                    <div class="donut-chart-container">
                        <div class="donut-block" style="background: conic-gradient(#00BFBF {margen_exi}%, rgba(255,255,255,0.2) 0);"></div>
                        <div class="donut-text-group" style="text-align: left;">
                            <span class="donut-main-val" style="color: white;">Objetivo: {margen_exi}%</span>
                            <span class="donut-sub-val" style="color: rgba(255,255,255,0.85);">${p_margen_inv:,.0f} Neto Protegido</span>
                        </div>
                    </div>
                </div>
                <div class="banner-loose">
                    <div class="label-banner">Costo Máximo Fábrica</div>
                    <div class="price-main" style="color: #FFFFFF;">${max(0.0, costo_max_admitido):,.2f}</div>
                    <div class="badge-banner" style="background-color: rgba(0,0,0,0.2);">Colchón Impositivo Activo 🛡️</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

# =========================================================
# SOLAPA 2: CALCULAR PVP SUGERIDO (FÁBRICA -> VENTA)
# =========================================================
with tab2:
    st.markdown(f"<div style='background-color: {gray_bg}; padding: 25px; border-radius: 12px; margin-bottom: 20px;'>", unsafe_allow_html=True)
    c_dir_1, c_dir_2, c_dir_3, c_dir_4, c_dir_5 = st.columns([1.2, 1.2, 1, 1.5, 1])

    with c_dir_1:
        costo_fabrica = st.number_input("Costo de Lista Fábrica ($)", value=0.0, step=1000.0, key="c_fab_k")
    with c_dir_2:
        margen_deseado = st.slider("% Margen Neto Objetivo", 5, 40, 15, key="m_des_k")
    with c_dir_3:
        tipo_me_dir = st.selectbox("Logística ", ["ME2 (Normal/Full)", "ME1 (Pesados)"], key="t_me_dir_k")
    with c_dir_4:
        plan_selected_dir = st.selectbox("Plan de Financiamiento ", list(FINANCIACION_PRESETS.keys()), index=2, key="plan_dir_k")
        if plan_selected_dir == "Personalizado (Manual)":
            t_finan_val_dir = st.number_input("% Tasa Custom ", value=10.0, step=0.1, key="custom_fin_dir") / 100
        else:
            t_finan_val_dir = FINANCIACION_PRESETS[plan_selected_dir] / 100
    with c_dir_5:
        peso_cat_dir = st.selectbox("Peso Correo ", list(TABLA_ME1.keys()), key="peso_dir_k")

    st.markdown("</div>", unsafe_allow_html=True)

    if costo_fabrica > 0:
        envio_v_dir = TABLA_ME1[peso_cat_dir] * bonif
        t_comi_dir = 14 / 100
        t_marg_dir = margen_deseado / 100
        
        divisor = (1 - t_comi_dir - t_marg_dir - t_iibb - t_iva - t_finan_val_dir)
        
        if divisor > 0:
            pvp_sugerido = (costo_fabrica + envio_v_dir) / divisor if "ME2" in tipo_me_dir else (costo_fabrica / divisor) + envio_v_dir
            
            p_meli_dir = pvp_sugerido * t_comi_dir
            p_finan_dir = pvp_sugerido * t_finan_val_dir
            p_iva_dir = (pvp_sugerido - (pvp_sugerido / 1.21)) if tipo_iva == "Responsable Inscripto" else 0.0
            p_iibb_dir = (pvp_sugerido / (1.21 if tipo_iva == "Responsable Inscripto" else 1)) * t_iibb
            p_neto_dir = pvp_sugerido * t_marg_dir

            st.markdown(f"""
                <div class="results-main-container">
                    <div class="cost-breakdown-list">
                        <div class="cost-item"><span class="cost-label">Costo de Fábrica Base</span><span class="cost-value">${costo_fabrica:,.2f}</span></div>
                        <div class="cost-item"><span class="cost-label">Comisión por Venta</span><span class="cost-value">${p_meli_dir:,.2f}</span></div>
                        <div class="cost-item"><span class="cost-label">Cargo por Financiación</span><span class="cost-value">${p_finan_dir:,.2f}</span></div>
                        <div class="cost-item"><span class="cost-label">IVA Liquidado Real</span><span class="cost-value">${p_iva_dir:,.2f}</span></div>
                        <div class="cost-item"><span class="cost-label">Ingresos Brutos ({tipo_iva})</span><span class="cost-value">${p_iibb_dir:,.2f}</span></div>
                    </div>
                    <div class="banner-dark">
                        <div class="label-banner">Ganancia Líquida Real</div>
                        <div class="price-main">${p_neto_dir:,.2f}</div>
                        <div class="donut-chart-container">
                            <div class="donut-block" style="background: conic-gradient(#00BFBF {margen_deseado}%, rgba(255,255,255,0.15) 0);"></div>
                            <div class="donut-text-group" style="text-align: left;">
                                <span class="donut-main-val" style="color: #00BFBF;">Retorno: {margen_deseado}%</span>
                                <span class="donut-sub-val" style="color: rgba(255,255,255,0.85);">Limpios sobre PVP</span>
                            </div>
                        </div>
                    </div>
                    <div class="banner-strict">
                        <div class="label-banner">Precio Venta Recomendado</div>
                        <div class="price-main">${pvp_sugerido:,.2f}</div>
                        <div class="badge-banner" style="background-color: rgba(255,255,255,0.25);">PVP Sugerido NQ</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

st.markdown("<div style='text-align:center; padding: 30px;'><p style='color:#94A3B8; font-size:0.8rem;'>NQ Intelligence System v17.3 | Argentina 2026</p></div>", unsafe_allow_html=True)
