import streamlit as st

# Versión del sistema
V_NUMBER = "20.0"

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
    "Clásica / 1 Pago (0%)": 0.0,
    "3 Cuotas Premium (8.40%)": 8.40,
    "6 Cuotas Premium (12.30%)": 12.30,
    "9 Cuotas Premium (15.70%)": 15.70,
    "12 Cuotas Premium (19.20%)": 19.20,
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
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 20px;
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
    background-color: {gray_bg}; padding: 18px 25px; border-radius: 12px;
    margin-bottom: 20px; border: 1px solid #E5E7EB;
}}

.cost-breakdown-card {{
    background-color: #FFFFFF; padding: 22px; border-radius: 16px;
    border: 1px solid #E5E7EB; box-shadow: 0 4px 12px rgba(0,0,0,0.03);
}}
.cost-card-header {{
    font-size: 1.1rem; font-weight: 800; color: {nq_main_color};
    border-bottom: 2px solid {gray_bg}; padding-bottom: 10px; margin-bottom: 12px;
}}
.cost-item {{ 
    display: flex; justify-content: space-between; font-size: 0.90rem; 
    border-bottom: 1px solid #F3F4F6; padding: 6px 0;
}}
.cost-label {{ color: #4B5563; font-weight: 600; }}
.cost-value {{ color: #111827; font-weight: 700; text-align: right; }}

.banner-card {{
    color: white; padding: 20px; display: flex; flex-direction: column;
    justify-content: center; align-items: center; text-align: center; gap: 4px;
    border-radius: 16px; margin-bottom: 15px;
    box-shadow: 0 8px 16px rgba(0,0,0,0.06);
}}
.bg-pvp {{ background-color: {nq_main_color}; }}
.bg-costo {{ background-color: {nq_gold}; }}
.bg-ganancia {{ background-color: {nq_green}; }}
.bg-loss {{ background-color: #C0392B; }}

.label-banner {{ color: rgba(255,255,255,0.9); font-size: 0.8rem; font-weight: 700; text-transform: uppercase; }}
.price-main {{ color: white; font-size: 2rem; font-weight: 800; margin: 2px 0; }}
.badge-banner {{
    background: rgba(255,255,255,0.25); color: white;
    padding: 4px 12px; border-radius: 20px; font-size: 0.78rem; font-weight: 700;
}}
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
# CONTROL FISCAL GENERAL
# =========================================================
with st.container():
    st.markdown("<div class='tax-bar'>", unsafe_allow_html=True)
    c_tax1, c_tax2, c_tax3, c_tax4 = st.columns([1.5, 1, 1, 1])
    with c_tax1:
        tipo_iva = st.radio("Configuración Impositiva", ["Responsable Inscripto", "Monotributista"], horizontal=True)
    with c_tax2:
        iibb_perc = st.number_input("% Ingresos Brutos (IIBB)", value=5.0, step=0.1)
    with c_tax3:
        comision_vender_input = st.number_input("% Cargo Vender MeLi (Neto)", value=14.15, step=0.1)
    with c_tax4:
        alicuota_iva_prod = st.selectbox("% IVA Producto", [21.0, 10.5, 0.0], index=0)
    st.markdown("</div>", unsafe_allow_html=True)

t_iibb = iibb_perc / 100
t_comi_base = comision_vender_input / 100
t_iva_prod = alicuota_iva_prod / 100
t_ganancias_fijo = 0.05
t_estructura_fijo = 0.02

peso_list = list(TABLA_ME2_2026.keys())

def buscar_flete_dinamico(pvp_evaluado, peso_categoria):
    if pvp_evaluado < UMBRAL_ENVIO_GRATIS:
        return 0.0
    elif pvp_evaluado < 50000:
        return TABLA_ME2_2026.get(peso_categoria, [0.0, 0.0, 0.0])[1]
    else:
        return TABLA_ME2_2026.get(peso_categoria, [0.0, 0.0, 0.0])[2]

def render_desglose_html(costo_fabrica_neto, pvp, comi_m_bruta, flete_bruto, cargo_fijo_bruto, iibb_m, gan_m, est_m, iva_pagar_m, ganancia_neta, margen_pct):
    pvp_neto = pvp / (1 + t_iva_prod)
    costo_total = pvp - ganancia_neta
    
    # Fila de IVA si es Responsable Inscripto
    iva_row_html = ""
    if tipo_iva == "Responsable Inscripto":
        iva_row_html = f"""
        <div class="cost-item" style="background-color: #FEF3C7; padding: 4px 6px; border-radius: 4px;">
            <span class="cost-label" style="color: #92400E;">IVA Neto a Pagar (Posición)</span>
            <span class="cost-value" style="color: #92400E;">${iva_pagar_m:,.2f}</span>
        </div>
        """

    # Estilos dinámicos para la ganancia
    color_bg = '#ECFDF5' if ganancia_neta >= 0 else '#FEF2F2'
    color_txt = '#065F46' if ganancia_neta >= 0 else '#991B1B'

    html = f"""
    <div class="cost-breakdown-card">
        <div class="cost-card-header">📋 Desglose Analítico de Costos</div>
        <div class="cost-item"><span class="cost-label">Precio de Venta Público (PVP)</span><span class="cost-value">${pvp:,.2f}</span></div>
        <div class="cost-item"><span class="cost-label">Venta Neta (Sin IVA)</span><span class="cost-value">${pvp_neto:,.2f}</span></div>
        <div class="cost-item"><span class="cost-label">Costo Fábrica (Sin IVA)</span><span class="cost-value">${costo_fabrica_neto:,.2f}</span></div>
        <div class="cost-item"><span class="cost-label">Comisión ML Bruta</span><span class="cost-value">${comi_m_bruta:,.2f}</span></div>
        <div class="cost-item"><span class="cost-label">Flete ML Bruto</span><span class="cost-value">${flete_bruto:,.2f}</span></div>
        <div class="cost-item"><span class="cost-label">Cargo Fijo ML</span><span class="cost-value">${cargo_fijo_bruto:,.2f}</span></div>
        <div class="cost-item"><span class="cost-label">IIBB ({iibb_perc:.1f}%)</span><span class="cost-value">${iibb_m:,.2f}</span></div>
        <div class="cost-item"><span class="cost-label">Imp. a las Ganancias (5%)</span><span class="cost-value">${gan_m:,.2f}</span></div>
        <div class="cost-item"><span class="cost-label">Costo Estructura (2%)</span><span class="cost-value">${est_m:,.2f}</span></div>
        {iva_row_html}
        <div class="cost-item" style="margin-top: 10px; border-top: 2px solid #E5E7EB; padding-top: 8px;">
            <span class="cost-label" style="font-weight: 800; color: #111827;">COSTO TOTAL OPERATIVO</span>
            <span class="cost-value" style="font-weight: 800; color: #111827;">${costo_total:,.2f}</span>
        </div>
        <div class="cost-item" style="background-color: {color_bg}; padding: 6px; border-radius: 6px; margin-top: 6px;">
            <span class="cost-label" style="font-weight: 800; color: {color_txt};">GANANCIA NETO FINAL</span>
            <span class="cost-value" style="font-weight: 800; color: {color_txt};">${ganancia_neta:,.2f} ({margen_pct:.2f}%)</span>
        </div>
    </div>
    """
    
    # Limpiamos los saltos de línea para evitar que Streamlit lo interprete como código plano
    return "".join([line.strip() for line in html.splitlines()])
# --- TABS ---
tab1, tab2, tab3 = st.tabs([
    "📊 REALIDAD REAL (Compro a X y Vendo a Y)", 
    "☝️ CALCULAR PVP RECOMENDADO (Fábrica -> Venta)", 
    "🎯 ANALIZAR COSTO OBJETIVO (Venta -> Fábrica)"
])

# =========================================================
# SOLAPA 1: REALIDAD REAL
# =========================================================
with tab1:
    col_left, col_right = st.columns([1.2, 1])
    
    with col_left:
        st.markdown(f"<div style='background-color: {gray_bg}; padding: 20px; border-radius: 12px;'>", unsafe_allow_html=True)
        x_costo_fabrica = st.number_input("Costo Fábrica SIN IVA (X) ($)", value=70392.83, step=1000.0, key="x_cost_k")
        y_pvp_venta = st.number_input("PVP Publicado en MeLi (Y) ($)", value=115000.0, step=1000.0, key="y_pvp_k")
        plan_selected_x = st.selectbox("Plan Financiamiento / Cuotas", list(FINANCIACION_PRESETS.keys()), index=0, key="plan_x_k")
        t_finan_val_x = st.number_input("% Tasa Custom", value=0.0, step=0.1, key="custom_fin_x") / 100 if plan_selected_x == "Personalizado (Manual)" else FINANCIACION_PRESETS[plan_selected_x] / 100
        peso_cat_x = st.selectbox("Peso Correo Tabla", peso_list, index=13, key="peso_x_k")
        st.markdown("</div>", unsafe_allow_html=True)

        # Cálculos de Solapa 1
        flete_bruto = buscar_flete_dinamico(y_pvp_venta, peso_cat_x)
        fijo_bruto = CARGO_FIJO_MELI if y_pvp_venta < UMBRAL_ENVIO_GRATIS else 0.0
        
        comi_bruta = y_pvp_venta * (t_comi_base + t_finan_val_x)
        pvp_neto = y_pvp_venta / (1 + t_iva_prod)
        iibb_m = pvp_neto * t_iibb
        gan_m = pvp_neto * t_ganancias_fijo
        est_m = y_pvp_venta * t_estructura_fijo
        
        if tipo_iva == "Monotributista":
            costo_fabrica_inc = x_costo_fabrica * (1 + t_iva_prod)
            ganancia_real = y_pvp_venta - (costo_fabrica_inc + comi_bruta + flete_bruto + fijo_bruto + iibb_m + est_m)
            iva_pagar_m = 0.0
        else:
            # Modelo Exacto del Archivo Excel (Responsable Inscripto)
            iva_venta = y_pvp_venta - pvp_neto
            iva_compra = x_costo_fabrica * t_iva_prod
            iva_comi = comi_bruta - (comi_bruta / 1.21)
            iva_flete = flete_bruto - (flete_bruto / 1.21)
            iva_fijo = fijo_bruto - (fijo_bruto / 1.21)
            
            iva_pagar_m = iva_venta - (iva_compra + iva_comi + iva_flete + iva_fijo)
            ganancia_real = pvp_neto - x_costo_fabrica - (comi_bruta / 1.21) - (flete_bruto / 1.21) - (fijo_bruto / 1.21) - iibb_m - gan_m - est_m - iva_pagar_m

        rendimiento_real = (ganancia_real / y_pvp_venta) * 100
        card_style = "bg-ganancia" if ganancia_real >= 0 else "bg-loss"

        st.markdown(f"""
        <div style="display: flex; gap: 10px; margin-top: 15px;">
            <div class="banner-card bg-pvp" style="flex:1;">
                <span class="label-banner">PVP Venta</span>
                <span class="price-main">${y_pvp_venta:,.2f}</span>
            </div>
            <div class="banner-card {card_style}" style="flex:1;">
                <span class="label-banner">Ganancia Neta</span>
                <span class="price-main">${ganancia_real:,.2f}</span>
                <span class="badge-banner">Margen: {rendimiento_real:.2f}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown(render_desglose_html(x_costo_fabrica, y_pvp_venta, comi_bruta, flete_bruto, fijo_bruto, iibb_m, gan_m, est_m, iva_pagar_m, ganancia_real, rendimiento_real), unsafe_allow_html=True)

# =========================================================
# SOLAPA 2: PVP RECOMENDADO
# =========================================================
with tab2:
    col_left2, col_right2 = st.columns([1.2, 1])
    
    with col_left2:
        st.markdown(f"<div style='background-color: {gray_bg}; padding: 20px; border-radius: 12px;'>", unsafe_allow_html=True)
        costo_f_tab2 = st.number_input("Costo Fábrica SIN IVA ($)", value=70392.83, step=1000.0, key="c_tab2")
        margen_deseado_tab2 = st.number_input("% Margen Neto Deseado", value=10.0, step=0.5, key="m_tab2") / 100
        plan_selected_tab2 = st.selectbox("Plan Financiamiento / Cuotas", list(FINANCIACION_PRESETS.keys()), index=0, key="plan_tab2")
        t_finan_tab2 = st.number_input("% Tasa Custom", value=0.0, step=0.1, key="c_fin_tab2") / 100 if plan_selected_tab2 == "Personalizado (Manual)" else FINANCIACION_PRESETS[plan_selected_tab2] / 100
        peso_cat_tab2 = st.selectbox("Peso Correo Tabla", peso_list, index=13, key="peso_tab2")
        st.markdown("</div>", unsafe_allow_html=True)

        if costo_f_tab2 > 0:
            pvp_calc = costo_f_tab2 * 2.0
            for _ in range(10):
                flete_bruto2 = buscar_flete_dinamico(pvp_calc, peso_cat_tab2)
                fijo_bruto2 = CARGO_FIJO_MELI if pvp_calc < UMBRAL_ENVIO_GRATIS else 0.0

                if tipo_iva == "Monotributista":
                    costo_inc = costo_f_tab2 * (1 + t_iva_prod)
                    denom = 1 - (t_comi_base + t_finan_tab2 + (t_iibb / (1 + t_iva_prod)) + t_estructura_fijo + margen_deseado_tab2)
                    if denom > 0: pvp_calc = (costo_inc + flete_bruto2 + fijo_bruto2) / denom
                else:
                    # Derivación despejada RI según planilla Excel
                    factor_neto = 1 / (1 + t_iva_prod)
                    comi_f = (t_comi_base + t_finan_tab2)
                    denom = factor_neto - comi_f - (t_iibb * factor_neto) - (t_ganancias_fijo * factor_neto) - t_estructura_fijo - margen_deseado_tab2
                    if denom > 0: pvp_calc = (costo_f_tab2 + flete_bruto2 + fijo_bruto2) / denom

            comi_bruta2 = pvp_calc * (t_comi_base + t_finan_tab2)
            pvp_neto2 = pvp_calc / (1 + t_iva_prod)
            iibb_m2 = pvp_neto2 * t_iibb
            gan_m2 = pvp_neto2 * t_ganancias_fijo
            est_m2 = pvp_calc * t_estructura_fijo
            
            iva_v2 = pvp_calc - pvp_neto2
            iva_c2 = costo_f_tab2 * t_iva_prod
            iva_pagar2 = iva_v2 - (iva_c2 + (comi_bruta2 - comi_bruta2/1.21) + (flete_bruto2 - flete_bruto2/1.21) + (fijo_bruto2 - fijo_bruto2/1.21)) if tipo_iva == "Responsable Inscripto" else 0.0
            ganancia_neta2 = pvp_calc * margen_deseado_tab2

            st.markdown(f"""
            <div style="display: flex; gap: 10px; margin-top: 15px;">
                <div class="banner-card bg-pvp" style="flex:1;">
                    <span class="label-banner">PVP Recomendado</span>
                    <span class="price-main">${pvp_calc:,.2f}</span>
                </div>
                <div class="banner-card bg-ganancia" style="flex:1;">
                    <span class="label-banner">Ganancia Proyectada</span>
                    <span class="price-main">${ganancia_neta2:,.2f}</span>
                    <span class="badge-banner">Margen: {margen_deseado_tab2 * 100:.1f}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_right2:
        if costo_f_tab2 > 0:
            st.markdown(render_desglose_html(costo_f_tab2, pvp_calc, comi_bruta2, flete_bruto2, fijo_bruto2, iibb_m2, gan_m2, est_m2, iva_pagar2, ganancia_neta2, margen_deseado_tab2*100), unsafe_allow_html=True)

# =========================================================
# SOLAPA 3: ANALIZAR COSTO OBJETIVO
# =========================================================
with tab3:
    col_left3, col_right3 = st.columns([1.2, 1])
    
    with col_left3:
        st.markdown(f"<div style='background-color: {gray_bg}; padding: 20px; border-radius: 12px;'>", unsafe_allow_html=True)
        pvp_target = st.number_input("PVP Mercado Objetivo ($)", value=115000.0, step=1000.0, key="pvp_obj")
        margen_target = st.number_input("% Margen Neto Pretendido", value=10.0, step=0.5, key="m_obj") / 100
        plan_selected_obj = st.selectbox("Plan Financiamiento / Cuotas", list(FINANCIACION_PRESETS.keys()), index=0, key="plan_obj")
        t_finan_obj = st.number_input("% Tasa Custom", value=0.0, step=0.1, key="c_fin_obj") / 100 if plan_selected_obj == "Personalizado (Manual)" else FINANCIACION_PRESETS[plan_selected_obj] / 100
        peso_cat_obj = st.selectbox("Peso Correo Tabla", peso_list, index=13, key="peso_obj")
        st.markdown("</div>", unsafe_allow_html=True)

        if pvp_target > 0:
            flete_bruto3 = buscar_flete_dinamico(pvp_target, peso_cat_obj)
            fijo_bruto3 = CARGO_FIJO_MELI if pvp_target < UMBRAL_ENVIO_GRATIS else 0.0

            comi_bruta3 = pvp_target * (t_comi_base + t_finan_obj)
            pvp_neto3 = pvp_target / (1 + t_iva_prod)
            iibb_m3 = pvp_neto3 * t_iibb
            gan_m3 = pvp_neto3 * t_ganancias_fijo
            est_m3 = pvp_target * t_estructura_fijo
            ganancia_neta3 = pvp_target * margen_target

            if tipo_iva == "Monotributista":
                costo_max_inc = pvp_target - (ganancia_neta3 + comi_bruta3 + flete_bruto3 + fijo_bruto3 + iibb_m3 + est_m3)
                costo_max_fabrica = costo_max_inc / (1 + t_iva_prod)
                iva_pagar3 = 0.0
            else:
                # Inversión matemática exacta basada en planilla de Responsable Inscripto
                costo_max_fabrica = pvp_neto3 - comi_bruta3 - flete_bruto3 - fijo_bruto3 - iibb_m3 - gan_m3 - est_m3 - ganancia_neta3
                iva_v3 = pvp_target - pvp_neto3
                iva_c3 = costo_max_fabrica * t_iva_prod
                iva_pagar3 = iva_v3 - (iva_c3 + (comi_bruta3 - comi_bruta3/1.21) + (flete_bruto3 - flete_bruto3/1.21) + (fijo_bruto3 - fijo_bruto3/1.21))

            st.markdown(f"""
            <div style="display: flex; gap: 10px; margin-top: 15px;">
                <div class="banner-card bg-costo" style="flex:1;">
                    <span class="label-banner">Costo Máximo Compra</span>
                    <span class="price-main">${costo_max_fabrica:,.2f}</span>
                    <span class="badge-banner">Límite Fábrica SIN IVA</span>
                </div>
                <div class="banner-card bg-pvp" style="flex:1;">
                    <span class="label-banner">PVP Competición</span>
                    <span class="price-main">${pvp_target:,.2f}</span>
                    <span class="badge-banner">Precio Objetivo Mercado</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_right3:
        if pvp_target > 0:
            st.markdown(render_desglose_html(costo_max_fabrica, pvp_target, comi_bruta3, flete_bruto3, fijo_bruto3, iibb_m3, gan_m3, est_m3, iva_pagar3, ganancia_neta3, margen_target*100), unsafe_allow_html=True)
