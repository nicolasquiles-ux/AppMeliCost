import streamlit as st

# Versión del sistema actualizada con parches de convergencia de fletes
V_NUMBER = "19.0"

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title=f"NQ | Sales Intelligence Dashboard v{V_NUMBER}", layout="wide")

# =========================================================
# DATOS MAESTROS VIGENTES 2026 (NQ Database Oficial)
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
    "Mismo Precio — 3 Cuotas (8.40%)": 8.40,
    "Mismo Precio — 6 Cuotas (12.30%)": 12.30,
    "Mismo Precio — 9 Cuotas (15.70%)": 15.70,
    "Mismo Precio — 12 Cuotas (19.20%)": 19.20,
    "Personalizado (Manual)": -1.0
}

CLAVE_CORRECTA = "NQ_PRO_2026"
UMBRAL_ENVIO_GRATIS = 33000.0
CARGO_FIJO_MELI = 3800.0

# Estética corporativa NQ
nq_main_color = "#2B3E4F" 
nq_green = "#1E8449"       
nq_gold = "#BFA100"        
gray_bg = "#F3F5F7"       

# =========================================================
# INYECCIÓN DE CSS SEGURO
# =========================================================
css_template = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=400;600;700;800&display=swap');

html, body, [class*="css"] {{ 
    font-family: 'Plus Jakarta Sans', sans-serif; 
    background-color: #FFFFFF; 
}}
.stApp {{ background-color: #FFFFFF; }}

.nq-header-container {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 20px 30px; background-color: #FFFFFF;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 25px;
    border-radius: 12px; border: 1px solid #E5E7EB;
}}
.nq-branding {{ display: flex; align-items: center; }}
.nq-logo {{
    background: linear-gradient(135deg, #0055A0 0%, #00BFBF 100%);
    color: white; padding: 12px 20px; border-radius: 12px; 
    font-weight: 800; font-size: 1.6rem; margin-right: 18px; letter-spacing: -1px;
}}
.nq-title-group {{ display: flex; flex-direction: column; }}
.nq-title-country {{ color: #7F8C8D; font-size: 0.85rem; font-weight: 600; }}
.nq-dashboard {{ color: {nq_main_color}; font-weight: 700; font-size: 1.3rem; margin-top: 2px; }}

.tax-bar {{
    background-color: {gray_bg}; padding: 20px; border-radius: 12px;
    margin-bottom: 25px; border: 1px solid #E5E7EB;
}}

.results-main-container {{
    display: flex; flex-wrap: wrap; gap: 12px; margin-top: 25px; width: 100%;
}}
.cost-breakdown-list {{
    flex: 1 1 320px; background-color: #FFFFFF; padding: 25px;
    display: flex; flex-direction: column; justify-content: center; gap: 10px;
    border: 1px solid #E5E7EB; border-radius: 16px;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
}}
.cost-item {{ 
    display: flex; justify-content: space-between; font-size: 0.95rem; 
    border-bottom: 1px solid #F3F4F6; padding-bottom: 6px;
}}
.cost-label {{ color: #4B5563; font-weight: 600; }}
.cost-value {{ color: #111827; font-weight: 700; text-align: right; }}

.banner-card {{
    flex: 1 1 260px; color: white; padding: 25px;
    display: flex; flex-direction: column; justify-content: center;
    align-items: center; text-align: center; gap: 6px;
    border-radius: 16px; min-height: 160px;
    box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05);
}}
.bg-pvp {{ background-color: {nq_main_color}; }}
.bg-costo {{ background-color: {nq_gold}; }}
.bg-ganancia {{ background-color: #1E8449; }}
.bg-loss {{ background-color: #C0392B; }}

.label-banner {{ color: rgba(255,255,255,0.9); font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }}
.price-main {{ color: white; font-size: 2.2rem; font-weight: 800; margin: 2px 0; }}
.badge-banner {{
    background: rgba(255,255,255,0.25); color: white;
    padding: 5px 14px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; margin-top: 4px;
}}

.donut-chart-container {{ display: flex; align-items: center; gap: 10px; margin-top: 6px; }}
.donut-block {{ width: 35px; height: 35px; border-radius: 50%; position: relative; }}
.donut-block::after {{ content: ''; width: 21px; height: 21px; border-radius: 50%; position: absolute; top: 7px; left: 7px; background: #1E8449; }}
.donut-block.loss-chart::after {{ background: #C0392B; }}
.donut-text-group {{ display: flex; flex-direction: column; font-size: 0.8rem; text-align: left; }}
.donut-main-val {{ font-weight: 700; color: white; }}
</style>
"""

st.markdown(css_template, unsafe_allow_html=True)

# --- LOGIN ---
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
st.markdown(f"""
    <div class="nq-header-container">
        <div class="nq-branding">
            <span class="nq-logo">NQ</span>
            <div class="nq-title-group">
                <div class="nq-title-country">NQ Argentina</div>
                <div class="nq-dashboard">NQ | Sales Intelligence Matrix v{V_NUMBER}</div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# =========================================================
# CONTROL FISCAL
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

# Parámetros estructurales
t_ganancias_fijo = 0.05
t_estructura_fijo = 0.02

# --- TABS ---
tab1, tab2, tab3 = st.tabs([
    "📊 REALIDAD REAL (Si compro a X y vendo a Y)", 
    "☝️ CALCULAR PVP RECOMENDADO (Fábrica -> Venta)", 
    "🎯 ANALIZAR COSTO OBJETIVO (Venta -> Fábrica)"
])

peso_list = list(TABLA_ME2_2026.keys())

def buscar_flete_dinamico(pvp_evaluado, peso_categoria):
    if pvp_evaluado < UMBRAL_ENVIO_GRATIS:
        return 0.0  # Menos de $33.000 lo paga el comprador
    elif pvp_evaluado < 50000:
        return TABLA_ME2_2026.get(peso_categoria, [0.0, 0.0, 0.0])[1]
    else:
        return TABLA_ME2_2026.get(peso_categoria, [0.0, 0.0, 0.0])[2]

# =========================================================
# SOLAPA 1: SI COMPRO A X Y VENDO A Y
# =========================================================
with tab1:
    st.markdown(f"<div style='background-color: {gray_bg}; padding: 25px; border-radius: 12px; margin-bottom: 20px;'>", unsafe_allow_html=True)
    c_x1, c_x2, c_x3, c_x4 = st.columns([1.5, 1.5, 1.5, 1.5])
    
    with c_x1:
        x_costo_fabrica = st.number_input("Costo Fábrica SIN IVA (X) ($)", value=54200.0, step=1000.0, key="x_cost_k")
    with c_x2:
        y_pvp_venta = st.number_input("PVP Publicado en MeLi (Y) ($)", value=123000.0, step=1000.0, key="y_pvp_k")
    with c_x3:
        plan_selected_x = st.selectbox("Plan Financiamiento", list(FINANCIACION_PRESETS.keys()), index=2, key="plan_x_k")
        t_finan_val_x = st.number_input("% Tasa Custom", value=10.0, step=0.1, key="custom_fin_x") / 100 if plan_selected_x == "Personalizado (Manual)" else FINANCIACION_PRESETS[plan_selected_x] / 100
    with c_x4:
        peso_cat_x = st.selectbox("Peso Correo Tabla", peso_list, index=13, key="peso_x_k")

    st.markdown("</div>", unsafe_allow_html=True)

    if x_costo_fabrica > 0 and y_pvp_venta > 0:
        envio_aplicado_x = buscar_flete_dinamico(y_pvp_venta, peso_cat_x)
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
            ext_html = f"<div class='cost-item'><span class='cost-label'>IVA Fábrica No Recuperable</span><span class='cost-value'>${x_costo_fabrica * 0.21:,.2f}</span></div>"
        else:
            pvp_neto = y_pvp_venta / 1.21
            p_meli_neto = p_meli
