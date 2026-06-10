import streamlit as st

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="NQ | Sales Intelligence Dashboard", layout="wide")

# =========================================================
# DATOS MAESTROS VIGENTES 2026 (NQ Database - Sincerada para Pesados)
# =========================================================
TABLA_ME1 = {
    "Hasta 0,3 Kg": 6080.0, "0,3 a 0,5 Kg": 6600.0, "0,5 a 1 Kg": 7470.0,
    "1 a 2 Kg": 7970.0, "2 a 5 Kg": 10760.0, "5 a 10 Kg": 12840.0,
    "10 a 15 Kg": 14930.0, "15 a 20 Kg": 17830.0, 
    # Sinceramiento NQ: Ajustados para que el neto con descuento supere los $17.000 en adelante
    "20 a 25 Kg (Muebles/Racks)": 35400.0, 
    "25 a 30 Kg (Muebles/Racks)": 42800.0, 
    "30 a 40 Kg (Muebles/Racks)": 49500.0, 
    "40 a 50 Kg (Muebles/Racks)": 56000.0, 
    "50 a 60 Kg": 61000.0, "60 a 70 Kg": 68000.0, "70 a 80 Kg": 75000.0,
    "80 a 90 Kg": 89000.0, "90 a 100 Kg": 98000.0, "Mas de 100 Kg": 115000.0
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
UMBRAL_ENVIO_GRATIS = 35000.0
CARGO_FIJO_MELI = 3800.0

# Colores corporativos NQ
nq_main_color = "#2B3E4F" 
nq_green = "#1E8449"       
nq_gold = "#BFA100"        
gray_bg = "#F3F5F7"       

# =========================================================
# INYECCIÓN DE CSS SEGURO Y RESPONSIVO REFORZADO
# =========================================================
css_template = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');

html, body, [class*="css"] { 
    font-family: 'Plus Jakarta Sans', sans-serif; 
    background-color: #FFFFFF; 
}
.stApp { background-color: #FFFFFF; }

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

.tax-bar {
    background-color: GRAY_BG; padding: 20px; border-radius: 12px;
    margin-bottom: 25px; border: 1px solid #E5E7EB;
}

.results-main-container {
    display: flex; flex-wrap: wrap; gap: 12px; margin-top: 25px; width: 100%;
}
.cost-breakdown-list {
    flex: 1 1 320px; background-color: #FFFFFF; padding: 25px;
    display: flex; flex-direction: column; justify-content: center; gap: 10px;
    border: 1px solid #E5E7EB; border-radius: 16px;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
}
.cost-item { 
    display: flex; justify-content: space-between; font-size: 0.95rem; 
    border-bottom: 1px solid #F3F4F6; padding-bottom: 6px;
}
.cost-label { color: #4B5563; font-weight: 600; }
.cost-value { color: #111827; font-weight: 700; text-align: right; }

.banner-card {
    flex: 1 1 260px; color: white; padding: 25px;
    display: flex; flex-direction: column; justify-content: center;
    align-items: center; text-align: center; gap: 6px;
    border-radius: 16px; min-height: 160px;
    box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05);
}
.bg-pvp { background-color: NQ_MAIN_COLOR; }
.bg-costo { background-color: NQ_GOLD; }
.bg-ganancia { background-color: NQ_GREEN; }

.label-banner { color: rgba(255,255,255,0.9); font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
.price-main { color: white; font-size: 2.2rem; font-weight: 800; margin: 2px 0; }
.badge-banner {
    background: rgba(255,255,255,0.25); color: white;
    padding: 5px 14px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; margin-top: 4px;
}

.donut-chart-container { display: flex; align-items: center; gap: 10px; margin-top: 6px; }
.donut-block { width: 35px; height: 35px; border-radius: 50%; position: relative; }
.donut-block::after { content: ''; width: 21px; height: 21px; border-radius: 50%; position: absolute; top: 7px; left: 7px; background: NQ_GREEN; }
.donut-text-group { display: flex; flex-direction: column; font-size: 0.8rem; text-align: left; }
.donut-main-val { font-weight: 700; color: white; }
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
# ENCABEZADO CORPORATIVO
# =========================================================
st.markdown("""
    <div class="nq-header-container">
        <div class="nq-branding">
            <span class="nq-logo">NQ</span>
            <div class="nq-title-group">
                <div class="nq-title-country">NQ Argentina</div>
                <div class="nq-dashboard">NQ | Sales Intelligence Matrix v17.8</div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# =========================================================
# CONTROL MATRIZ FISCAL
# =========================================================
with st.container():
    st.markdown("<div class='tax-bar'>", unsafe_allow_html=True)
    c_tax1, c_tax2, c_tax3 = st.columns([2,1,1])
    with c_tax1:
        tipo_iva = st.radio("Configuración Impositiva Real", ["Responsable Inscripto", "Monotributista"], horizontal=True)
    with c_tax2:
        iibb_perc = st.number_input("% Ingresos Brutos (IIBB)", value=5.0, step=0.1)
    with c_tax3:
        repu = st.selectbox("Nivel de Reputación Cuenta", ["Verde (50% desc)", "Amarilla (40% desc)", "Roja (0% desc)"])
    st.markdown("</div>", unsafe_allow_html=True)

bonif = 0.5 if "Verde" in repu else 0.6 if "Amarilla" in repu else 1.0
t_iibb = iibb_perc / 100

# Variables fijas estructurales
t_ganancias_fijo = 0.05
t_estructura_fijo = 0.02
t_iva_cushion = 0.17355

# --- TABS DE OPERACIÓN ---
tab1, tab2 = st.tabs(["☝️ CALCULAR PVP RECOMENDADO (Directo)", "📊 ANALIZAR COSTO OBJETIVO (Inverso)"])

# =========================================================
# SOLAPA 1: CALCULAR PVP SUGERIDO MÁXIMO (FÁBRICA -> VENTA)
# =========================================================
with tab1:
    st.markdown(f"<div style='background-color: {gray_bg}; padding: 25px; border-radius: 12px; margin-bottom: 20px;'>", unsafe_allow_html=True)
    c_dir_1, c_dir_2, c_dir_3, c_dir_4, c_dir_5, c_dir_6 = st.columns([1.2, 1.0, 1.0, 1.3, 1.2, 1.0])

    with c_dir_1:
        costo_fabrica_neto = st.number_input("Costo Fábrica (SIN IVA) ($)", value=0.0, step=1000.0, key="c_fab_k")
    with c_dir_2:
        margen_deseado = st.slider("% Margen Objetivo", 5, 40, 15, key="m_des_k")
    with c_dir_3:
        tipo_me_dir = st.selectbox("Logística", ["ME2 (Normal/Full)", "ME1 (Pesados)"], key="t_me_dir_k")
    with c_dir_4:
        plan_selected_dir = st.selectbox("Plan Financiamiento", list(FINANCIACION_PRESETS.keys()), index=2, key="plan_dir_k")
        if plan_selected_dir == "Personalizado (Manual)":
            t_finan_val_dir = st.number_input("% Tasa Custom", value=10.0, step=0.1, key="custom_fin_dir") / 100
        else:
            t_finan_val_dir = FINANCIACION_PRESETS[plan_selected_dir] / 100
    with c_dir_5:
        peso_cat_dir = st.selectbox("Peso Correo Tabla", list(TABLA_ME1.keys()), key="peso_dir_k")
    with c_dir_6:
        # Flete sugerido por sistema según tabla e impuestos
        flete_sugerido_base = TABLA_ME1[peso_cat_dir] * bonif
        flete_real_dir = st.number_input("Flete Real Forzado ($)", value=float(flete_sugerido_base), step=500.0, key="flete_real_dir_k", help="Modificá este valor si MeLi te cobra un monto diferente en la realidad.")

    st.markdown("</div>", unsafe_allow_html=True)

    if costo_fabrica_neto > 0:
        t_comi_dir = 14 / 100
        t_marg_dir = margen_deseado / 100
        costo_fabrica_con_iva = costo_fabrica_neto * 1.21
        
        divisor = (1 - t_comi_dir - t_marg_dir - t_iibb - t_iva_cushion - t_finan_val_dir - t_ganancias_fijo - t_estructura_fijo)
        
        if divisor > 0:
            # El cálculo dinámico usa el flete_real_dir (forzado o sugerido)
            if "ME2" in tipo_me_dir:
                pvp_test = (costo_fabrica_neto + flete_real_dir) / divisor
                if pvp_test >= UMBRAL_ENVIO_GRATIS:
                    pvp_sugerido = pvp_test
                    envio_aplicado_dir = flete_real_dir
                    fijo_aplicado_dir = 0.0
                else:
                    pvp_sugerido = (costo_fabrica_neto + CARGO_FIJO_MELI) / divisor
                    envio_aplicado_dir = 0.0
                    fijo_aplicado_dir = CARGO_FIJO_MELI
            else:
                pvp_test = (costo_fabrica_neto / divisor) + flete_real_dir
                if pvp_test >= UMBRAL_ENVIO_GRATIS:
                    pvp_sugerido = pvp_test
                    envio_aplicado_dir = flete_real_dir
                    fijo_aplicado_dir = 0.0
                else:
                    pvp_sugerido = ((costo_fabrica_neto + CARGO_FIJO_MELI) / divisor)
                    envio_aplicado_dir = 0.0
                    fijo_aplicado_dir = CARGO_FIJO_MELI

            p_meli_dir = pvp_sugerido * t_comi_dir
            p_finan_dir = pvp_sugerido * t_finan_val_dir
            p_iva_dir = (pvp_sugerido - (pvp_sugerido / 1.21)) 
            p_iibb_dir = (pvp_sugerido / 1.21) * t_iibb
            p_ganancias_dir = (pvp_sugerido / 1.21) * t_ganancias_fijo
            p_estructura_dir = pvp_sugerido * t_estructura_fijo
            p_neto_dir = pvp_sugerido * t_marg_dir

            if tipo_iva == "Monotributista":
                ganancia_real_dir = p_neto_dir + p_iva_dir + p_ganancias_dir
                rendimiento_real_dir = (ganancia_real_dir / pvp_sugerido) * 100
                badge_dir = "Margen + Exenciones Retenidas 🎉"
            else:
                ganancia_real_dir = p_neto_dir
                rendimiento_real_dir = float(margen_deseado)
                badge_dir = "Estructura RI Standard"

            st.markdown(f"""
                <div class="results-main-container">
                    <div class="cost-breakdown-list">
                        <div class="cost-item"><span class="cost-label">Costo Proveedor Neto (Sin IVA)</span><span class="cost-value">${costo_fabrica_neto:,.2f}</span></div>
                        <div class="cost-item"><span class="cost-label">Costo Proveedor Facturado (Con IVA)</span><span class="cost-value">${costo_fabrica_con_iva:,.2f}</span></div>
                        <div class="cost-item" style="background-color: #EFF6FF; padding: 4px; border-radius:6px;"><span class="cost-label" style="color: #1E40AF; font-weight:700;">Costo Flete Real Aplicado 🚚</span><span class="cost-value" style="color: #1E40AF; font-weight:700;">${envio_aplicado_dir:,.2f}</span></div>
                        <div class="cost-item"><span class="cost-label">Costo Fijo MeLi (Menor a $35k)</span><span class="cost-value">${fijo_aplicado_dir:,.2f}</span></div>
                        <div class="cost-item"><span class="cost-label">Comisión MeLi (14%)</span><span class="cost-value">${p_meli_dir:,.2f}</span></div>
                        <div class="cost-item"><span class="cost-label">Cargo Financiero Plan</span><span class="cost-value">${p_finan_dir:,.2f}</span></div>
                        <div class="cost-item"><span class="cost-label">Impacto IVA Publicación</span><span class="cost-value">${p_iva_dir:,.2f}</span></div>
                        <div class="cost-item"><span class="cost-label">Ingresos Brutos ({iibb_perc}%)</span><span class="cost-value">${p_iibb_dir:,.2f}</span></div>
                        <div class="cost-item"><span class="cost-label">Reserva Ganancias (5%)</span><span class="cost-value">${p_ganancias_dir:,.2f}</span></div>
                        <div class="cost-item"><span class="cost-label">Costo Estructura Depósito (2%)</span><span class="cost-value">${p_estructura_dir:,.2f}</span></div>
                    </div>
                    <div class="banner-card bg-pvp">
                        <div class="label-banner">Costo Fábrica Base</div>
                        <div class="price-main">${costo_fabrica_neto:,.0f}</div>
                        <div class="badge-banner">Neto Ingresado</div>
                    </div>
                    <div class="banner-card bg-costo">
                        <div class="label-banner">PVP MÁXIMO SUGERIDO</div>
                        <div class="price-main">${pvp_sugerido:,.2f}</div>
                        <div class="badge-banner">Precio Publicación NQ</div>
                    </div>
                    <div class="banner-card bg-ganancia">
                        <div class="label-banner">Ganancia Real Bolsillo</div>
                        <div class="price-main">${ganancia_real_dir:,.2f}</div>
                        <div class="donut-chart-container">
                            <div class="donut-block" style="background: conic-gradient(#00BFBF {rendimiento_real_dir}%, rgba(255,255,255,0.2) 0);"></div>
                            <div class="donut-text-group">
                                <span class="donut-main-val">Rendimiento: {rendimiento_real_dir:.1f}%</span>
                                <span class="donut-sub-val" style="color: white;">{badge_dir}</span>
                            </div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

# =========================================================
# SOLAPA 2: ANÁLISIS COSTO OBJETIVO (PVP -> FÁBRICA)
# =========================================================
with tab2:
    st.markdown(f"<div style='background-color: {gray_bg}; padding: 25px; border-radius: 12px; margin-bottom: 20px;'>", unsafe_allow_html=True)
    c_inv_1, c_inv_2, c_inv_3, c_inv_4, c_inv_5, c_inv_6 = st.columns([1.2, 1.0, 1.0, 1.3, 1.2, 1.0])
    
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
    with c_inv_6:
        flete_sugerido_base_inv = (TABLA_ME1[peso_cat_inv] * bonif) if pvp_target >= UMBRAL_ENVIO_GRATIS else 0.0
        flete_real_inv = st.number_input("Flete Real Forzado ($)", value=float(flete_sugerido_base_inv), step=500.0, key="flete_real_inv_k")

    st.markdown("</div>", unsafe_allow_html=True)

    if pvp_target > 0:
        envio_real_inv = flete_real_inv if pvp_target >= UMBRAL_ENVIO_GRATIS else 0.0
        fijo_inv = CARGO_FIJO_MELI if pvp_target < UMBRAL_ENVIO_GRATIS else 0.0

        t_comi_inv = 14 / 100 
        p_meli_inv = pvp_target * t_comi_inv
        p_finan_inv = pvp_target * t_finan_val_inv
        
        p_iva_inv = (pvp_target - (pvp_target / 1.21))
        p_iibb_inv = (pvp_target / 1.21) * t_iibb
        p_ganancias_inv = (pvp_target / 1.21) * t_ganancias_fijo
        p_estructura_inv = pvp_target * t_estructura_fijo
        p_margen_inv = pvp_target * (margen_exi / 100)

        costo_max_admitido_neto = pvp_target - (p_meli_inv + p_finan_inv + p_iva_inv + p_iibb_inv + p_ganancias_inv + p_estructura_inv + envio_real_inv + fijo_inv + p_margen_inv)

        if tipo_iva == "Monotributista":
            ganancia_real_pesos = p_margen_inv + p_iva_inv + p_ganancias_inv
            margen_real_porcentaje = (ganancia_real_pesos / pvp_target) * 100
            badge_ganancia = "Margen + Exenciones IVA/Gan 🎉"
        else:
            ganancia_real_pesos = p_margen_inv
            margen_real_porcentaje = float(margen_exi)
            badge_ganancia = "Esquema RI Puro"

        st.markdown(f"""
            <div class="results-main-container">
                <div class="cost-breakdown-list">
                    <div class="cost-item"><span class="cost-label">Comisión MeLi (14%)</span><span class="cost-value">${p_meli_inv:,.2f}</span></div>
                    <div class="cost-item"><span class="cost-label">Costo Financiero Plan</span><span class="cost-value">${p_finan_inv:,.2f}</span></div>
                    <div class="cost-item"><span class="cost-label">Reserva IVA (Colchón RI 21%)</span><span class="cost-value">${p_iva_inv:,.2f}</span></div>
                    <div class="cost-item"><span class="cost-label">Ingresos Brutos ({iibb_perc}%)</span><span class="cost-value">${p_iibb_inv:,.2f}</span></div>
                    <div class="cost-item"><span class="cost-label">Impuesto Ganancias (5%)</span><span class="cost-value">${p_ganancias_inv:,.2f}</span></div>
                    <div class="cost-item"><span class="cost-label">Estructura Depósito (2%)</span><span class="cost-value">${p_estructura_inv:,.2f}</span></div>
                    <div class="cost-item" style="background-color: #EFF6FF; padding: 4px; border-radius:6px;"><span class="cost-label" style="color: #1E40AF; font-weight:700;">Costo Flete Real Aplicado 🚚</span><span class="cost-value" style="color: #1E40AF; font-weight:700;">${envio_real_inv:,.2f}</span></div>
                    <div class="cost-item"><span class="cost-label">Costo Fijo MeLi (Menor a $35k)</span><span class="cost-value">${fijo_inv:,.2f}</span></div>
                </div>
                <div class="banner-card bg-pvp">
                    <div class="label-banner">PVP Mercado</div>
                    <div class="price-main">${pvp_target:,.0f}</div>
                    <div class="badge-banner">Precio Comp.</div>
                </div>
                <div class="banner-card bg-costo">
                    <div class="label-banner">Costo Máx Fábrica (SIN IVA)</div>
                    <div class="price-main">${max(0.0, costo_max_admitido_neto):,.2f}</div>
                    <div class="badge-banner">Límite Compra Neto 🛡️</div>
                </div>
                <div class="banner-card bg-ganancia">
                    <div class="label-banner">Ganancia Real Bolsillo</div>
                    <div class="price-main">${ganancia_real_pesos:,.2f}</div>
                    <div class="donut-chart-container">
                        <div class="donut-block" style="background: conic-gradient(#00BFBF {margen_real_porcentaje}%, rgba(255,255,255,0.2) 0);"></div>
                        <div class="donut-text-group">
                            <span class="donut-main-val">Rendimiento: {margen_real_porcentaje:.1f}%</span>
                            <span class="donut-sub-val" style="color: white;">{badge_ganancia}</span>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='text-align:center; padding: 30px;'><p style='color:#94A3B8; font-size:0.8rem;'>NQ Intelligence System v17.8 | Argentina 2026</p></div>", unsafe_allow_html=True)
