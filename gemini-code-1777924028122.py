import streamlit as st

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="NQ | Sales Intelligence Dashboard", layout="wide")

# =========================================================
# DATOS MAESTROS VIGENTES 2026 (NQ Database - Sincerada para Pesados)
# =========================================================
TABLA_ME2_2026 = {
    "Hasta 0,3 kg": [7868.0, 5620.0, 6080.0],
    "De 0,3 a 0,5 kg": [8596.0, 6140.0, 6600.0],
    "De 0,5 a 1 kg": [9800.0, 7000.0, 7470.0],
    "De 1 a 1,5 kg": [10122.0, 7230.0, 7720.0],
    "De 1,5 a 2 kg": [10458.0, 7470.0, 7970.0],
    "De 2 a 3 kg": [11550.0, 8250.0, 8710.0],
    "De 3 a 4 kg": [12866.0, 9190.0, 9860.0],
    "De 4 a 5 kg": [14070.0, 10050.0, 10760.0],
    "De 5 a 8 kg": [15512.0, 11080.0, 11830.0],
    "De 8 a 10 kg": [16926.0, 12090.0, 12840.0],
    "De 10 a 13 kg": [18270.0, 13050.0, 13920.0],
    "De 13 a 15 kg": [19684.0, 14060.0, 14930.0],
    "De 15 a 20 kg": [23506.0, 16790.0, 17830.0],
    "De 20 a 25 kg": [28182.0, 20130.0, 21420.0],
    "De 25 a 30 kg": [38780.0, 27700.0, 29410.0],
    "De 30 a 40 kg": [44268.0, 31620.0, 33570.0],
    "De 40 a 50 kg": [46802.0, 33430.0, 35490.0],
    "De 50 a 60 kg": [51996.0, 37140.0, 39610.0],
    "De 60 a 70 kg": [54068.0, 38620.0, 41290.0],
    "De 70 a 80 kg": [62524.0, 44660.0, 47850.0],
    "De 80 a 90 kg": [77308.0, 55220.0, 59180.0],
    "De 90 a 100 kg": [89152.0, 63680.0, 68230.0],
    "De 100 a 120 kg": [97328.0, 69520.0, 74490.0],
    "De 120 a 140 kg": [109592.0, 78280.0, 83890.0],
    "De 140 a 160 kg": [121870.0, 87050.0, 93280.0],
    "De 160 a 180 kg": [134120.0, 95800.0, 102660.0],
    "Más de 180 kg": [146398.0, 104570.0, 112060.0]
}

FINANCIACION_PRESETS = {
    "1 Pago (0%)": 0.0,
    "Cuotas Interés Bajo (3 a 12 C. - 5.00%)": 5.0,
    "Mismo Precio — 3 Cuotas (8.40%)": 8.40,
    "Mismo Precio — 6 Cuotas (12.30%)": 12.30,
    "Mismo Precio — 9 Cuotas (15.70%)": 15.70,
    "Mismo Precio — 12 Cuotas (19.20%)": 19.20,
    "Personalizado (Manual)": -1.0
}

CLAVE_CORRECTA = "NQ_PRO_2026"
UMBRAL_ENVIO_GRATIS = 33000.0
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
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=400;600;700;800&display=swap');

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
.bg-ganancia { background-color: #1E8449; }
.bg-loss { background-color: #C0392B; }

.label-banner { color: rgba(255,255,255,0.9); font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
.price-main { color: white; font-size: 2.2rem; font-weight: 800; margin: 2px 0; }
.badge-banner {
    background: rgba(255,255,255,0.25); color: white;
    padding: 5px 14px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; margin-top: 4px;
}

.donut-chart-container { display: flex; align-items: center; gap: 10px; margin-top: 6px; }
.donut-block { width: 35px; height: 35px; border-radius: 50%; position: relative; }
.donut-block::after { content: ''; width: 21px; height: 21px; border-radius: 50%; position: absolute; top: 7px; left: 7px; background: #1E8449; }
.donut-block.loss-chart::after { background: #C0392B; }
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
                <div class="nq-dashboard">NQ | Sales Intelligence Matrix v18.0</div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# =========================================================
# CONTROL MATRIZ FISCAL GLOBAL
# =========================================================
with st.container():
    st.markdown("<div class='tax-bar'>", unsafe_allow_html=True)
    c_tax1, c_tax2, c_tax3 = st.columns([2,1,1])
    with c_tax1:
        tipo_iva = st.radio("Configuración Impositiva Real", ["Responsable Inscripto", "Monotributista"], horizontal=True)
    with c_tax2:
        iibb_perc = st.number_input("% Ingresos Brutos (IIBB)", value=5.5, step=0.1)
    with c_tax3:
        comision_vender_input = st.slider("% Cargo por Vender MeLi", min_value=11.62, max_value=17.75, value=14.0, step=0.01)
    st.markdown("</div>", unsafe_allow_html=True)

t_iibb = iibb_perc / 100
t_comi_base = comision_vender_input / 100

# Variables fijas estructurales
t_ganancias_fijo = 0.05
t_estructura_fijo = 0.02

# --- TABS DE OPERACIÓN ---
tab1, tab2, tab3 = st.tabs([
    "📊 REALIDAD REAL (Si compro a X y vendo a Y)", 
    "☝️ CALCULAR PVP RECOMENDADO (Fábrica -> Venta)", 
    "🎯 ANALIZAR COSTO OBJETIVO (Venta -> Fábrica)"
])

peso_list = list(TABLA_ME2_2026.keys())

# Función para extraer flete dinámico basado en el precio real de venta
def buscar_flete_dinamico(pvp_evaluado, peso_categoria):
    if pvp_evaluado < UMBRAL_ENVIO_GRATIS:
        col_idx = 0  # Menos de $33.000 (30% desc)
    elif pvp_evaluado < 50000:
        col_idx = 1  # De $33.000 a $49.999 (50% desc)
    else:
        col_idx = 2  # Más de $50.000 (50% desc)
    return TABLA_ME2_2026.get(peso_categoria, [0.0, 0.0, 0.0])[col_idx]

# =========================================================
# SOLAPA 1: SI COMPRO A X Y VENDO A Y (DETERMINAR RENTA EXACTA)
# =========================================================
with tab1:
    st.markdown(f"<div style='background-color: {gray_bg}; padding: 25px; border-radius: 12px; margin-bottom: 20px;'>", unsafe_allow_html=True)
    c_x1, c_x2, c_x3, c_x4 = st.columns([1.5, 1.5, 1.5, 1.5])
    
    with c_x1:
        x_costo_fabrica = st.number_input("Costo Fábrica SIN IVA (X) ($)", value=54200.0, step=1000.0, key="x_cost_k")
    with c_x2:
        y_pvp_venta = st.number_input("PVP Publicado en MeLi (Y) ($)", value=123000.0, step=1000.0, key="y_pvp_k")
    with c_x3:
        plan_selected_x = st.selectbox("Plan Financiamiento", list(FINANCIACION_PRESETS.keys()), index=3, key="plan_x_k")
        t_finan_val_x = st.number_input("% Tasa Custom", value=10.0, step=0.1, key="custom_fin_x") / 100 if plan_selected_x == "Personalizado (Manual)" else FINANCIACION_PRESETS[plan_selected_x] / 100
    with c_x4:
        peso_cat_x = st.selectbox("Peso Correo Tabla", peso_list, index=3, key="peso_x_k")

    st.markdown("</div>", unsafe_allow_html=True)

    if x_costo_fabrica > 0 and y_pvp_venta > 0:
        envio_aplicado_x = buscar_flete_dinamico(y_pvp_venta, peso_cat_x) if y_pvp_venta >= UMBRAL_ENVIO_GRATIS else 0.0
        fijo_aplicado_x = CARGO_FIJO_MELI if y_pvp_venta < UMBRAL_ENVIO_GRATIS else 0.0
        
        p_meli = y_pvp_venta * t_comi_base
        p_finan = y_pvp_venta * t_finan_val_x
        p_estructura = y_pvp_venta * t_estructura_fijo
        p_iibb = (y_pvp_venta / 1.21) * t_iibb

        if tipo_iva == "Monotributista":
            costo_fabrica_con_iva = x_costo_fabrica * 1.21
            total_egresos = costo_fabrica_con_iva + p_meli + p_finan + envio_aplicado_x + fijo_aplicado_x + p_iibb + p_estructura
            ganancia_real = y_pvp_venta - total_egresos
            rendimiento_real = (ganancia_real / y_pvp_venta) * 100
            badge_card_style = "bg-ganancia" if rendimiento_real >= 0 else "bg-loss"
            txt_condicion = "Monotributista absorbe IVA"
            ext_html = f"<div class='cost-item'><span class='cost-label'>Mochila IVA Fábrica No Recuperable</span><span class='cost-value'>${x_costo_fabrica * 0.21:,.2f}</span></div>"
        else:
            pvp_neto = y_pvp_venta / 1.21
            p_meli_neto = p_meli / 1.21
            p_finan_neto = p_finan / 1.21
            envio_neto = envio_aplicado_x / 1.21
            p_ganancias = pvp_neto * t_ganancias_fijo
            
            ganancia_real = pvp_neto - (x_costo_fabrica + p_meli_neto + p_finan_neto + envio_neto + fijo_aplicado_x + p_iibb + p_ganancias + p_estructura)
            rendimiento_real = (ganancia_real / y_pvp_venta) * 100
            badge_card_style = "bg-ganancia" if rendimiento_real >= 0 else "bg-loss"
            txt_condicion = "Esquema RI Neto Puro"
            ext_html = f"<div class='cost-item'><span class='cost-label'>Reserva Ganancias RI (5%)</span><span class='cost-value'>${pvp_neto * t_ganancias_fijo:,.2f}</span></div>"

        st.markdown(f"""
            <div class="results-main-container">
                <div class="cost-breakdown-list">
                    <div class="cost-item"><span class="cost-label">Costo Fábrica Ingresado (Neto)</span><span class="cost-value">${x_costo_fabrica:,.2f}</span></div>
                    <div class="cost-item"><span class="cost-label">Comisión MeLi Seleccionada ({comision_vender_input}%)</span><span class="cost-value">${p_meli:,.2f}</span></div>
                    <div class="cost-item"><span class="cost-label">Cargo Financiero Plan</span><span class="cost-value">${p_finan:,.2f}</span></div>
                    <div class="cost-item" style="background-color: #EFF6FF; padding: 4px; border-radius:6px;"><span class="cost-label" style="color: #1E40AF; font-weight:700;">Costo Flete Mercado Envíos 🚚</span><span class="cost-value" style="color: #1E40AF; font-weight:700;">${envio_aplicado_x:,.2f}</span></div>
                    {f"<div class='cost-item'><span class='cost-label'>Costo Fijo Unidad (<${UMBRAL_ENVIO_GRATIS:,.0f})</span><span class='cost-value'>${fijo_aplicado_x:,.2f}</span></div>" if fijo_aplicado_x > 0 else ""}
                    <div class="cost-item"><span class="cost-label">Ingresos Brutos ({iibb_perc}%)</span><span class="cost-value">${p_iibb:,.2f}</span></div>
                    <div class="cost-item"><span class="cost-label">Costo Estructura Asignado (2%)</span><span class="cost-value">${p_estructura:,.2f}</span></div>
                    {ext_html}
                </div>
                <div class="banner-card bg-pvp">
                    <div class="label-banner">COSTO FÁBRICA COMPRA (X)</div>
                    <div class="price-main">${x_costo_fabrica:,.0f}</div>
                    <div class="badge-banner">Sin IVA Siempre</div>
                </div>
                <div class="banner-card bg-costo">
                    <div class="label-banner">PRECIO PUBLICACIÓN VENTA (Y)</div>
                    <div class="price-main">${y_pvp_venta:,.0f}</div>
                    <div class="badge-banner">PVP en Mercado Libre</div>
                </div>
                <div class="banner-card {badge_card_style}">
                    <div class="label-banner">RENTA REAL DE BOLSILLO</div>
                    <div class="price-main">${ganancia_real:,.2f}</div>
                    <div class="donut-chart-container">
                        <div class="donut-block {'' if rendimiento_real >= 0 else 'loss-chart'}" style="background: conic-gradient({'#00BFBF' if rendimiento_real >= 0 else '#FFFFFF'} {max(0.0, rendimiento_real)}%, rgba(255,255,255,0.2) 0);"></div>
                        <div class="donut-text-group">
                            <span class="donut-main-val">Renta: {rendimiento_real:.2f}%</span>
                            <span class="donut-sub-val" style="color: white;">{txt_condicion}</span>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

# =========================================================
# SOLAPA 2: CALCULAR PVP SUGERIDO MÁXIMO (FÁBRICA -> VENTA)
# =========================================================
with tab2:
    st.markdown(f"<div style='background-color: {gray_bg}; padding: 25px; border-radius: 12px; margin-bottom: 20px;'>", unsafe_allow_html=True)
    c_dir_1, c_dir_2, c_dir_3, c_dir_4 = st.columns([1.5, 1.5, 1.5, 1.5])

    with c_dir_1:
        costo_fabrica_neto = st.number_input("Costo Fábrica (SIN IVA) ($)", value=54200.0, step=1000.0, key="c_fab_k")
    with c_dir_2:
        margen_deseado = st.slider("% Margen Objetivo", 5, 40, 12, key="m_des_k")
    with c_dir_3:
        plan_selected_dir = st.selectbox("Plan Financiamiento Proyectado", list(FINANCIACION_PRESETS.keys()), index=3, key="plan_dir_k")
        t_finan_val_dir = st.number_input("% Tasa Custom Proy.", value=10.0, step=0.1, key="custom_fin_dir") / 100 if plan_selected_dir == "Personalizado (Manual)" else FINANCIACION_PRESETS[plan_selected_dir] / 100
    with c_dir_4:
        peso_cat_dir = st.selectbox("Peso Correo Tabla Proy.", peso_list, index=3, key="peso_dir_k")

    st.markdown("</div>", unsafe_allow_html=True)

    if costo_fabrica_neto > 0:
        t_marg_dir = margen_deseado / 100
        
        # Divisores porcentuales fijos
        divisor_bruto = (1 - t_comi_base - t_marg_dir - (t_iibb/1.21) - t_finan_val_dir - t_estructura_fijo)
        divisor_neto = (1 - t_comi_base - t_marg_dir - t_iibb - t_ganancias_fijo - t_finan_val_dir - (t_estructura_fijo * 1.21))

        pvp_sugerido = 0.0
        flete_final_dir = 0.0
        txt_condition_dir = ""

        # Evaluamos secuencialmente los 3 tramos de flete posibles
        for idx, band_lbl in [(0, "Escala <33k"), (1, "Escala 33k-50k"), (2, "Escala >50k")]:
            flete_test = TABLA_ME2_2026.get(peso_cat_dir, [0.0, 0.0, 0.0])[idx]
            
            if tipo_iva == "Monotributista":
                costo_base_compra = costo_fabrica_neto * 1.21
                fijo_test = CARGO_FIJO_MELI if idx == 0 else 0.0
                flete_test_aplicado = flete_test if idx != 0 else 0.0
                
                pvp_calc = (costo_base_compra + flete_test_aplicado + fijo_test) / divisor_bruto if divisor_bruto > 0 else 0.0
                # Validamos si el resultado cae dentro del rango de la columna evaluada
                if (idx == 0 and pvp_calc < UMBRAL_ENVIO_GRATIS) or \
                   (idx == 1 and UMBRAL_ENVIO_GRATIS <= pvp_calc < 50000) or \
                   (idx == 2 and pvp_calc >= 50000):
                    pvp_sugerido = pvp_calc
                    flete_final_dir = flete_test_aplicado
                    txt_condition_dir = band_lbl
                    break
            else:
                fijo_neto_test = (CARGO_FIJO_MELI / 1.21) if idx == 0 else 0.0
                flete_neto_test = (flete_test / 1.21) if idx != 0 else 0.0
                
                pvp_neto_calc = (costo_fabrica_neto + flete_neto_test + fijo_neto_test) / divisor_neto if divisor_neto > 0 else 0.0
                pvp_calc = pvp_neto_calc * 1.21
                if (idx == 0 and pvp_calc < UMBRAL_ENVIO_GRATIS) or \
                   (idx == 1 and UMBRAL_ENVIO_GRATIS <= pvp_calc < 50000) or \
                   (idx == 2 and pvp_calc >= 50000):
                    pvp_sugerido = pvp_calc
                    flete_final_dir = flete_test if idx != 0 else 0.0
                    txt_condition_dir = band_lbl
                    break

        # Si por asimetría matemática no cae exactamente en ninguna, forzamos el escenario de envío completo (>50k)
        if pvp_sugerido == 0.0:
            flete_fallback = TABLA_ME2_2026.get(peso_cat_dir, [0.0, 0.0, 0.0])[2]
            if tipo_iva == "Monotributista":
                pvp_sugerido = (costo_base_compra + flete_fallback) / divisor_bruto
            else:
                pvp_sugerido = ((costo_fabrica_neto + (flete_fallback / 1.21)) / divisor_neto) * 1.21
            flete_final_dir = flete_fallback
            txt_condition_dir = "Escala >50k (Forzado)"

        p_meli_dir = pvp_sugerido * t_comi_base
        p_finan_dir = pvp_sugerido * t_finan_val_dir
        p_iibb_dir = (pvp_sugerido / 1.21) * t_iibb
        p_estructura_dir = pvp_sugerido * t_estructura_fijo
        fijo_real_dir = CARGO_FIJO_MELI if pvp_sugerido < UMBRAL_ENVIO_GRATIS else 0.0
        ganancia_real_dir = (pvp_sugerido / 1.21) * t_marg_dir if tipo_iva == "Responsable Inscripto" else pvp_sugerido * t_marg_dir

        st.markdown(f"""
            <div class="results-main-container">
                <div class="cost-breakdown-list">
                    <div class="cost-item"><span class="cost-label">Costo Fábrica Base Puro (Sin IVA)</span><span class="cost-value">${costo_fabrica_neto:,.2f}</span></div>
                    <div class="cost-item" style="background-color: #EFF6FF; padding: 4px; border-radius:6px;"><span class="cost-label" style="color: #1E40AF; font-weight:700;">Flete Mercado Envíos Determinado 🚚</span><span class="cost-value" style="color: #1E40AF; font-weight:700;">${flete_final_dir:,.2f}</span></div>
                    {f"<div class='cost-item'><span class='cost-label'>Costo Fijo MeLi (<${UMBRAL_ENVIO_GRATIS:,.0f})</span><span class='cost-value'>${fijo_real_dir:,.2f}</span></div>" if fijo_real_dir > 0 else ""}
                    <div class="cost-item"><span class="cost-label">Comisión MeLi Sugerida ({comision_vender_input}%)</span><span class="cost-value">${p_meli_dir:,.2f}</span></div>
                    <div class="cost-item"><span class="cost-label">Cargo Financiero Plan</span><span class="cost-value">${p_finan_dir:,.2f}</span></div>
                    <div class="cost-item"><span class="cost-label">Ingresos Brutos Asignados ({iibb_perc}%)</span><span class="cost-value">${p_iibb_dir:,.2f}</span></div>
                    <div class="cost-item"><span class="cost-label">Costo Estructura Depósito (2%)</span><span class="cost-value">${p_estructura_dir:,.2f}</span></div>
                </div>
                <div class="banner-card bg-pvp">
                    <div class="label-banner">Costo de Entrada Neto</div>
                    <div class="price-main">${costo_fabrica_neto:,.0f}</div>
                    <div class="badge-banner">Puro Sin IVA</div>
                </div>
                <div class="banner-card bg-costo">
                    <div class="label-banner">PVP RECOMENDADO</div>
                    <div class="price-main">${pvp_sugerido:,.2f}</div>
                    <div class="badge-banner">{txt_condition_dir} 🛡️</div>
                </div>
                <div class="banner-card bg-ganancia">
                    <div class="label-banner">Ganancia Real Bolsillo</div>
                    <div class="price-main">${ganancia_real_dir:,.2f}</div>
                    <div class="donut-chart-container">
                        <div class="donut-block" style="background: conic-gradient(#00BFBF {margen_deseado}%, rgba(255,255,255,0.2) 0);"></div>
                        <div class="donut-text-group">
                            <span class="donut-main-val">Objetivo: {margen_deseado}%</span>
                            <span class="donut-sub-val" style="color: white;">Estructura Limpia</span>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

# =========================================================
# SOLAPA 3: ANÁLISIS COSTO OBJETIVO (PVP -> FÁBRICA)
# =========================================================
with tab3:
    st.markdown(f"<div style='background-color: {gray_bg}; padding: 25px; border-radius: 12px; margin-bottom: 20px;'>", unsafe_allow_html=True)
    c_inv_1, c_inv_2, c_inv_3, c_inv_4 = st.columns([1.5, 1.5, 1.5, 1.5])
    
    with c_inv_1:
        pvp_target = st.number_input("PVP Competencia Mercado ($)", value=123000.0, step=1000.0, key="p_target_k")
    with c_inv_2:
        margen_exi = st.slider("% Margen Neto Requerido", 5, 40, 12, key="m_exi_k")
    with c_inv_3:
        plan_selected_inv = st.selectbox("Plan de Financiamiento Competencia", list(FINANCIACION_PRESETS.keys()), index=3, key="plan_inv_k")
        t_finan_val_inv = st.number_input("% Tasa Custom Comp.", value=10.0, step=0.1, key="custom_fin_inv") / 100 if plan_selected_inv == "Personalizado (Manual)" else FINANCIACION_PRESETS[plan_selected_inv] / 100
    with c_inv_4:
        peso_cat_inv = st.selectbox("Peso Correo Tabla Comp.", peso_list, index=3, key="peso_inv_k")

    st.markdown("</div>", unsafe_allow_html=True)

    if pvp_target > 0:
        envio_real_inv = buscar_flete_dinamico(pvp_target, peso_cat_inv) if pvp_target >= UMBRAL_ENVIO_GRATIS else 0.0
        fijo_inv = CARGO_FIJO_MELI if pvp_target < UMBRAL_ENVIO_GRATIS else 0.0

        p_meli_inv = pvp_target * t_comi_base
        p_finan_inv = pvp_target * t_finan_val_inv
        p_iibb_inv = (pvp_target / 1.21) * t_iibb
        p_estructura_inv = pvp_target * t_estructura_fijo

        if tipo_iva == "Monotributista":
            p_margen_inv = pvp_target * (margen_exi / 100)
            costo_max_admitido_con_iva = pvp_target - (p_meli_inv + p_finan_inv + p_iibb_inv + p_estructura_inv + envio_real_inv + fijo_inv + p_margen_inv)
            costo_max_admitido_neto = costo_max_admitido_con_iva / 1.21
            badge_inv = "Mono - Base s/PVP Bruto"
        else:
            pvp_neto = pvp_target / 1.21
            p_ganancias_inv = pvp_neto * t_ganancias_fijo
            p_margen_inv = pvp_neto * (margen_exi / 100)
            costo_max_admitido_neto = pvp_neto - ((p_meli_inv/1.21) + (p_finan_inv/1.21) + p_iibb_inv + p_ganancias_inv + p_estructura_inv + (envio_real_inv/1.21) + (fijo_inv/1.21) + p_margen_inv)
            badge_inv = "RI - Base s/PVP Neto"

        st.markdown(f"""
            <div class="results-main-container">
                <div class="cost-breakdown-list">
                    <div class="cost-item"><span class="cost-label">Comisión MeLi Seleccionada ({comision_vender_input}%)</span><span class="cost-value">${p_meli_inv:,.2f}</span></div>
                    <div class="cost-item"><span class="cost-label">Cargo Financiero Plan</span><span class="cost-value">${p_finan_inv:,.2f}</span></div>
                    <div class="cost-item" style="background-color: #EFF6FF; padding: 4px; border-radius:6px;"><span class="cost-label" style="color: #1E40AF; font-weight:700;">Costo Flete Mercado Envíos 🚚</span><span class="cost-value" style="color: #1E40AF; font-weight:700;">${envio_real_inv:,.2f}</span></div>
                    {f"<div class='cost-item'><span class='cost-label'>Costo Fijo MeLi (<${UMBRAL_ENVIO_GRATIS:,.0f})</span><span class='cost-value'>${fijo_inv:,.2f}</span></div>" if fijo_inv > 0 else ""}
                    <div class="cost-item"><span class="cost-label">Ingresos Brutos ({iibb_perc}%)</span><span class="cost-value">${p_iibb_inv:,.2f}</span></div>
                    <div class="cost-item"><span class="cost-label">Margen Interno Requerido ({margen_exi}%)</span><span class="cost-value">${p_margen_inv:,.2f}</span></div>
                </div>
                <div class="banner-card bg-pvp">
                    <div class="label-banner">PRECIO PUBLICACIÓN VENTA (Y)</div>
                    <div class="price-main">${pvp_target:,.0f}</div>
                    <div class="badge-banner">PVP Mercado</div>
                </div>
                <div class="banner-card bg-costo">
                    <div class="label-banner">COSTO MÁX FÁBRICA ADMITIDO (X)</div>
                    <div class="price-main">${max(0.0, costo_max_admitido_neto):,.2f}</div>
                    <div class="badge-banner">Límite Neto Proveedor 🛡️</div>
                </div>
                <div class="banner-card bg-ganancia">
                    <div class="label-banner">Ganancia Requerida Bolsillo</div>
                    <div class="price-main">${p_margen_inv:,.2f}</div>
                    <div class="badge-banner">{badge_inv}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='text-align:center; padding: 30px;'><p style='color:#94A3B8; font-size:0.8rem;'>NQ Intelligence System v18.0 | Argentina 2026</p></div>", unsafe_allow_html=True)
