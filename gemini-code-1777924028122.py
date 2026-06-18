import streamlit as st
import pandas as pd

# Incrementamos a v21.0: Blindaje de Matriz Logística y unificación de textos
V_NUMBER = "21.0"

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title=f"NQ | Sales Intelligence Dashboard v{V_NUMBER}", layout="wide")

# =========================================================
# DATOS MAESTROS VIGENTES 2026 - MATRIZ LOGÍSTICA OFICIAL ME2
# =========================================================
CLAVE_CORRECTA = "NQ_PRO_2026"
CARGO_FIJO_MELI = 3800.0
UMBRAL_ENVIO_GRATIS = 33000.0

# Matriz limpia indexada idéntica a tu documento original
NEW_SHIPPING_DATA = {
    "under_33k": {
        "Hasta 0,3 kg": 7868.0, "De 0,3 a 0,5 kg": 8596.0, "De 0,5 a 1 kg": 9800.0,
        "De 1 a 1,5 kg": 10122.0, "De 1,5 a 2 kg": 10458.0, "De 2 a 3 kg": 11550.0,
        "De 3 a 4 kg": 12866.0, "De 4 a 5 kg": 14070.0, "De 5 a 8 kg": 15512.0,
        "De 8 a 10 kg": 16926.0, "De 10 a 13 kg": 18270.0, "De 13 a 15 kg": 19684.0,
        "De 15 a 20 kg": 23506.0, "De 20 a 25 kg": 28182.0, "De 25 a 30 kg": 38780.0,
        "De 30 a 40 kg": 44268.0, "De 40 a 50 kg": 46802.0, "De 50 a 60 kg": 51996.0,
        "De 60 a 70 kg": 54068.0, "De 70 a 80 kg": 62524.0, "De 80 a 90 kg": 77308.0,
        "De 90 a 100 kg": 89152.0, "De 100 a 120 kg": 97328.0, "De 120 a 140 kg": 109592.0,
        "De 140 a 160 kg": 121870.0, "De 160 a 180 kg": 134120.0, "Más de 180 kg": 146398.0
    },
    "33k_to_50k": {
        "Hasta 0,3 kg": 5620.0, "De 0,3 a 0,5 kg": 6140.0, "De 0,5 a 1 kg": 7000.0,
        "De 1 a 1,5 kg": 7230.0, "De 1,5 a 2 kg": 7470.0, "De 2 a 3 kg": 8250.0,
        "De 3 a 4 kg": 9190.0, "De 4 a 5 kg": 10050.0, "De 5 a 8 kg": 11080.0,
        "De 8 a 10 kg": 12090.0, "De 10 a 13 kg": 13050.0, "De 13 a 15 kg": 14060.0,
        "De 15 a 20 kg": 16790.0, "De 20 a 25 kg": 20130.0, "De 25 a 30 kg": 27700.0,
        "De 30 a 40 kg": 31620.0, "De 40 a 50 kg": 33430.0, "De 50 a 60 kg": 37140.0,
        "De 60 a 70 kg": 38620.0, "De 70 a 80 kg": 44660.0, "De 80 a 90 kg": 55220.0,
        "De 90 a 100 kg": 63680.0, "De 100 a 120 kg": 69520.0, "De 120 a 140 kg": 78280.0,
        "De 140 a 160 kg": 87050.0, "De 160 a 180 kg": 95800.0, "Más de 180 kg": 104570.0
    },
    "over_50k": {
        "Hasta 0,3 kg": 6080.0, "De 0,3 a 0,5 kg": 6600.0, "De 0,5 a 1 kg": 7470.0,
        "De 1 a 1,5 kg": 7720.0, "De 1,5 a 2 kg": 7970.0, "De 2 a 3 kg": 8710.0,
        "De 3 a 4 kg": 9860.0, "De 4 a 5 kg": 10760.0, "De 5 a 8 kg": 11830.0,
        "De 8 a 10 kg": 12840.0, "De 10 a 13 kg": 13920.0, "De 13 a 15 kg": 14930.0,
        "De 15 a 20 kg": 17830.0, "De 20 a 25 kg": 21420.0, "De 25 a 30 kg": 29410.0,
        "De 30 a 40 kg": 33570.0, "De 40 a 50 kg": 35490.0, "De 50 a 60 kg": 39610.0,
        "De 60 a 70 kg": 41290.0, "De 70 a 80 kg": 47850.0, "De 80 a 90 kg": 59180.0,
        "De 90 a 100 kg": 68230.0, "De 100 a 120 kg": 74490.0, "De 120 a 140 kg": 83890.0,
        "De 140 a 160 kg": 93280.0, "De 160 a 180 kg": 102660.0, "Más de 180 kg": 112060.0
    }
}

FINANCIACION_OPCIONES = {
    "1 Pago (0%)": 0.0,
    "Cuotas Interés Bajo (5.00% fijo)": 5.0,
    "Mismo Precio — 3 cuotas (8.40%)": 8.40,
    "Mismo Precio — 6 cuotas (12.30%)": 12.30,
    "Mismo Precio — 9 cuotas (15.70%)": 15.70,
    "Mismo Precio — 12 cuotas (19.20%)": 19.20,
    "Personalizado (Manual)": -1.0
}

nq_main_color = "#2B3E4F"
nq_green = "#1E8449"
nq_gold = "#BFA100"
gray_bg = "#F3F5F7"

# =========================================================
# INYECCIÓN DE CSS SEGURO NQ FORMATO ORIGINAL
# =========================================================
css_template = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #FFFFFF; }
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
    color: white; padding: 12px 20px; border-radius: 12px; font-weight: 800; font-size: 1.6rem; margin-right: 18px; letter-spacing: -1px;
}
.nq-title-group { display: flex; flex-direction: column; }
.nq-title-country { color: #7F8C8D; font-size: 0.85rem; font-weight: 600; }
.nq-dashboard { color: NQ_MAIN_COLOR; font-weight: 700; font-size: 1.3rem; margin-top: 2px; }
.tax-bar { background-color: GRAY_BG; padding: 20px; border-radius: 12px; margin-bottom: 25px; border: 1px solid #E5E7EB; }
.results-main-container { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 25px; width: 100%; }
.cost-breakdown-list {
    flex: 1 1 320px; background-color: #FFFFFF; padding: 25px;
    display: flex; flex-direction: column; justify-content: center; gap: 10px;
    border: 1px solid #E5E7EB; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
}
.cost-item { display: flex; justify-content: space-between; font-size: 0.95rem; border-bottom: 1px solid #F3F4F6; padding-bottom: 6px; }
.cost-label { color: #4B5563; font-weight: 600; }
.cost-value { color: #111827; font-weight: 700; text-align: right; }
.banner-card {
    flex: 1 1 260px; color: white; padding: 25px; display: flex; flex-direction: column; justify-content: center;
    align-items: center; text-align: center; gap: 6px; border-radius: 16px; min-height: 160px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05);
}
.bg-pvp { background-color: NQ_MAIN_COLOR; }
.bg-costo { background-color: NQ_GOLD; }
.bg-ganancia { background-color: #1E8449; }
.bg-loss { background-color: #C0392B; }
.label-banner { color: rgba(255,255,255,0.9); font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
.price-main { color: white; font-size: 2.2rem; font-weight: 800; margin: 2px 0; }
.badge-banner { background: rgba(255,255,255,0.25); color: white; padding: 5px 14px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; margin-top: 4px; }
.donut-chart-container { display: flex; align-items: center; gap: 10px; margin-top: 6px; }
.donut-block { width: 35px; height: 35px; border-radius: 50%; position: relative; }
.donut-block::after { content: ''; width: 21px; height: 21px; border-radius: 50%; position: absolute; top: 7px; left: 7px; background: #1E8449; }
.donut-block.loss-chart::after { background: #C0392B; }
.donut-text-group { display: flex; flex-direction: column; font-size: 0.8rem; text-align: left; }
.donut-main-val { font-weight: 700; color: white; }
</style>
""".replace("NQ_MAIN_COLOR", nq_main_color).replace("NQ_GREEN", nq_green).replace("NQ_GOLD", nq_gold).replace("GRAY_BG", gray_bg)

st.markdown(css_template, unsafe_allow_html=True)

# --- ACCESO OPERADOR ---
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

# --- MATRIZ CONFIGURACIÓN GLOBAL ---
with st.container():
    st.markdown("<div class='tax-bar'>", unsafe_allow_html=True)
    c_tax1, c_tax2, c_tax3 = st.columns([2,1,1])
    with c_tax1:
        tipo_iva = st.radio("Régimen Fiscal Impositivo", ["Responsable Inscripto", "Monotributista"], horizontal=True)
    with c_tax2:
        comision_clasica_pct = st.slider("% Comisión Venta Clásica", min_value=11.62, max_value=17.75, value=14.0, step=0.01)
    with c_tax3:
        iibb_perc = st.number_input("% Ingresos Brutos (IIBB)", value=5.5, step=0.1)
    st.markdown("</div>", unsafe_allow_html=True)

t_iibb = iibb_perc / 100
t_comi = comision_clasica_pct / 100
t_ganancias_fijo = 0.05
t_estructura_fijo = 0.02

# Cargamos el listado de pesos estandarizado
peso_list = list(NEW_SHIPPING_DATA["under_33k"].keys())

tab1, tab2, tab3 = st.tabs([
    "📊 REALIDAD REAL (Compro a X vs Vendo a Y)", 
    "☝️ CALCULAR PVP RECOMENDADO (Fábrica -> Venta)", 
    "🎯 ANALIZAR COSTO OBJETIVO (Venta -> Fábrica)"
])

# =========================================================
# SOLAPA 1: REALIDAD REAL (DETERMINAR RENTA EXACTA)
# =========================================================
with tab1:
    st.markdown(f"<div style='background-color: {gray_bg}; padding: 25px; border-radius: 12px; margin-bottom: 20px;'>", unsafe_allow_html=True)
    c_x1, c_x2, c_x3, c_x4, c_x5 = st.columns([1.5, 1.5, 1.5, 1.5, 1.5])
    with c_x1:
        x_costo_fabrica = st.number_input("Costo Fábrica SIN IVA (X) ($)", value=54200.0, step=1000.0, key="x_cost")
    with c_x2:
        y_pvp_venta = st.number_input("PVP Publicado en MeLi (Y) ($)", value=123000.0, step=1000.0, key="y_pvp")
    with c_x3:
        plan_selected_x = st.selectbox("Estrategia de Cuotas", list(FINANCIACION_OPCIONES.keys()), index=3, key="plan_x")
        t_finan_x = st.number_input("% Tasa Manual", value=10.0, step=0.1, key="c_fin_x") / 100 if plan_selected_x == "Personalizado (Manual)" else FINANCIACION_OPCIONES[plan_selected_x] / 100
    with c_x4:
        peso_cat_x = st.selectbox("Peso Correo (Tabla)", peso_list, index=13, key="peso_x")
    with c_x5:
        banda_lookup_x = "under_33k" if y_pvp_venta < UMBRAL_ENVIO_GRATIS else ("33k_to_50k" if y_pvp_venta < 50000 else "over_50k")
        envio_tabla_x = NEW_SHIPPING_DATA.get(banda_lookup_x, {}).get(peso_cat_x, 0.0)
        flete_real_x = st.number_input("Flete Cobrado Real ($)", value=float(envio_tabla_x), step=500.0, key="flete_x")
    st.markdown("</div>", unsafe_allow_html=True)

    if x_costo_fabrica > 0 and y_pvp_venta > 0:
        envio_aplicado_x = flete_real_x if y_pvp_venta >= UMBRAL_ENVIO_GRATIS else 0.0
        fijo_aplicado_x = CARGO_FIJO_MELI if y_pvp_venta < UMBRAL_ENVIO_GRATIS else 0.0
        
        p_meli = y_pvp_venta * t_comi
        p_finan = y_pvp_venta * t_finan_x
        p_estructura = y_pvp_venta * t_estructura_fijo
        p_iibb = (y_pvp_venta / 1.21) * t_iibb

        if tipo_iva == "Monotributista":
            total_egresos = (x_costo_fabrica * 1.21) + p_meli + p_finan + envio_aplicado_x + fijo_aplicado_x + p_iibb + p_estructura
            ganancia_real = y_pvp_venta - total_egresos
            rendimiento = (ganancia_real / y_pvp_venta) * 100
            badge_style, cond_text = ("bg-ganancia" if rendimiento >= 0 else "bg-loss"), "Monotributo (Absorbe IVA)"
            ext_html = f"<div class='cost-item'><span class='cost-label'>IVA Compra No Recuperable</span><span class='cost-value'>${x_costo_fabrica * 0.21:,.2f}</span></div>"
        else:
            pvp_neto = y_pvp_venta / 1.21
            p_meli_neto = p_meli / 1.21
            p_finan_neto = p_finan / 1.21
            envio_neto = envio_aplicado_x / 1.21
            fijo_neto = fijo_aplicado_x / 1.21
            p_ganancias = pvp_neto * t_ganancias_fijo
            
            ganancia_real = pvp_neto - (x_costo_fabrica + p_meli_neto + p_finan_neto + envio_neto + fijo_neto + p_iibb + p_ganancias + p_estructura)
            rendimiento = (ganancia_real / y_pvp_venta) * 100
            badge_style, cond_text = ("bg-ganancia" if rendimiento >= 0 else "bg-loss"), "RI (Esquema Neto Puro)"
            ext_html = f"<div class='cost-item'><span class='cost-label'>Reserva Ganancias (5% s/Neto)</span><span class='cost-value'>${p_ganancias:,.2f}</span></div>"

        st.markdown(f"""
            <div class="results-main-container">
                <div class="cost-breakdown-list">
                    <div class="cost-item"><span class="cost-label">Comisión Meli Base ({comision_clasica_pct}%)</span><span class="cost-value">${p_meli:,.2f}</span></div>
                    <div class="cost-item"><span class="cost-label">Costo Plan Financiero ({plan_selected_x.split("—")[0]})</span><span class="cost-value">${p_finan:,.2f}</span></div>
                    <div class="cost-item" style="background-color:#EFF6FF;"><span class="cost-label" style="color:#1E40AF; font-weight:700;">Flete Asignado 🚚</span><span class="cost-value" style="color:#1E40AF; font-weight:700;">${envio_aplicado_x:,.2f}</span></div>
                    {f"<div class='cost-item'><span class='cost-label'>Cargo Fijo (<${UMBRAL_ENVIO_GRATIS:,.0f})</span><span class='cost-value'>${fijo_aplicado_x:,.2f}</span></div>" if fijo_aplicado_x > 0 else ""}
                    <div class="cost-item"><span class="cost-label">Ingresos Brutos ({iibb_perc}%)</span><span class="cost-value">${p_iibb:,.2f}</span></div>
                    <div class="cost-item"><span class="cost-label">Costo Estructura (2%)</span><span class="cost-value">${p_estructura:,.2f}</span></div>
                    {ext_html}
                </div>
                <div class="banner-card bg-pvp"><div class="label-banner">COSTO FÁBRICA COMPRA</div><div class="price-main">${x_costo_fabrica:,.0f}</div><div class="badge-banner">Neto ingresado</div></div>
                <div class="banner-card bg-costo"><div class="label-banner">PRECIO DE PUBLICACIÓN</div><div class="price-main">${y_pvp_venta:,.0f}</div><div class="badge-banner">PVP en Cuenta</div></div>
                <div class="banner-card {badge_style}">
                    <div class="label-banner">RENTA DE BOLSILLO</div>
                    <div class="price-main">${ganancia_real:,.2f}</div>
                    <div class="donut-chart-container">
                        <div class="donut-block {'' if rendimiento >= 0 else 'loss-chart'}" style="background: conic-gradient({'#00BFBF' if rendimiento >= 0 else '#FFFFFF'} {max(0.0, rendimiento)}%, rgba(255,255,255,0.2) 0);"></div>
                        <div class="donut-text-group"><span class="donut-main-val">Renta: {rendimiento:.2f}%</span><span style="color:white; font-size:11px;">{cond_text}</span></div>
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
        costo_fabrica_neto = st.number_input("Costo Fábrica (SIN IVA) ($)", value=54200.0, step=1000.0, key="c_fab")
    with c_dir_2:
        margen_deseado = st.slider("% Margen Objetivo", 5, 40, 12, key="m_des")
    with c_dir_3:
        plan_selected_dir = st.selectbox("Estrategia de Cuotas Proyectada", list(FINANCIACION_OPCIONES.keys()), index=3, key="plan_dir")
        t_finan_dir = st.number_input("% Tasa Manual", value=10.0, step=0.1, key="c_fin_dir") / 100 if plan_selected_dir == "Personalizado (Manual)" else FINANCIACION_OPCIONES[plan_selected_dir] / 100
    with c_dir_4:
        peso_cat_dir = st.selectbox("Peso Correo (Tabla)", peso_list, index=13, key="peso_dir")
    st.markdown("</div>", unsafe_allow_html=True)

    if costo_fabrica_neto > 0:
        t_marg = margen_deseado / 100
        divisor_bruto = (1 - t_comi - t_marg - (t_iibb / 1.21) - t_finan_dir - t_estructura_fijo)
        divisor_neto = (1 - t_comi - t_marg - t_iibb - t_ganancias_fijo - t_finan_dir - (t_estructura_fijo * 1.21))

        final_pvp = 0.0
        applied_flete = 0.0
        txt_cond = ""

        # BLINDAJE DE BÚSQUEDA ITERATIVA (Evita KeyErrors usando .get secuencial)
        bandas_ordenadas = ["under_33k", "33k_to_50k", "over_50k"]

        if tipo_iva == "Monotributista":
            costo_compra_bruto = costo_fabrica_neto * 1.21
            for band in bandas_ordenadas:
                flete_test = NEW_SHIPPING_DATA.get(band, {}).get(peso_cat_dir, 0.0)
                fijo_test = CARGO_FIJO_MELI if band == "under_33k" else 0.0
                flete_test_aplicado = flete_test if band != "under_33k" else 0.0
                
                pvp_calc = (costo_compra_bruto + flete_test_aplicado + fijo_test) / divisor_bruto if divisor_bruto > 0 else 0
                if (band == "under_33k" and pvp_calc < UMBRAL_ENVIO_GRATIS) or \
                   (band == "33k_to_50k" and UMBRAL_ENVIO_GRATIS <= pvp_calc < 50000) or \
                   (band == "over_50k" and pvp_calc >= 50000):
                    final_pvp = pvp_calc
                    applied_flete = flete_test_aplicado
                    txt_cond = f"Convergencia {band}"
                    break
        else:
            # Responsable Inscripto (Cálculo Seguro)
            for band in bandas_ordenadas:
                fijo_neto_test = (CARGO_FIJO_MELI / 1.21) if band == "under_33k" else 0.0
                flete_test = NEW_SHIPPING_DATA.get(band, {}).get(peso_cat_dir, 0.0)
                flete_neto_test = (flete_test / 1.21) if band != "under_33k" else 0.0
                
                pvp_neto_calc = (costo_fabrica_neto + flete_neto_test + fijo_neto_test) / divisor_neto if divisor_neto > 0 else 0
                pvp_calc = pvp_neto_calc * 1.21
                if (band == "under_33k" and pvp_calc < UMBRAL_ENVIO_GRATIS) or \
                   (band == "33k_to_50k" and UMBRAL_ENVIO_GRATIS <= pvp_calc < 50000) or \
                   (band == "over_50k" and pvp_calc >= 50000):
                    final_pvp = pvp_calc
                    applied_flete = flete_neto_test * 1.21 if band != "under_33k" else 0.0
                    txt_cond = f"Convergencia {band}"
                    break

        # Fallback de seguridad si hay brechas de redondeo
        if final_pvp == 0.0:
            flete_test = NEW_SHIPPING_DATA.get("over_50k", {}).get(peso_cat_dir, 0.0)
            if tipo_iva == "Monotributista":
                final_pvp = (costo_compra_bruto + flete_test) / divisor_bruto if divisor_bruto > 0 else 0
            else:
                final_pvp = ((costo_fabrica_neto + (flete_test / 1.21)) / divisor_neto) * 1.21 if divisor_neto > 0 else 0
            applied_flete = flete_test
            txt_cond = "Estimación Escala >50k"

        p_meli_dir = final_pvp * t_comi
        p_finan_dir = final_pvp * t_finan_dir
        p_iibb_dir = (final_pvp / 1.21) * t_iibb
        p_estructura_dir = final_pvp * t_estructura_fijo
        fijo_real_dir = CARGO_FIJO_MELI if final_pvp < UMBRAL_ENVIO_GRATIS else 0.0
        ganancia_real_dir = (final_pvp / 1.21) * t_marg if tipo_iva == "Responsable Inscripto" else final_pvp * t_marg

        st.markdown(f"""
            <div class="results-main-container">
                <div class="cost-breakdown-list">
                    <div class="cost-item"><span class="cost-label">Comisión Requerida ({comision_clasica_pct}%)</span><span class="cost-value">${p_meli_dir:,.2f}</span></div>
                    <div class="cost-item"><span class="cost-label">Costo de Cuotas Activado</span><span class="cost-value">${p_finan_dir:,.2f}</span></div>
                    <div class="cost-item" style="background-color:#EFF6FF;"><span class="cost-label" style="color:#1E40AF; font-weight:700;">Flete Mercado Envíos Determinado🚚</span><span class="cost-value" style="color:#1E40AF; font-weight:700;">${applied_flete:,.2f}</span></div>
                    {f"<div class='cost-item'><span class='cost-label'>Cargo Fijo Asignado</span><span class='cost-value'>${fijo_real_dir:,.2f}</span></div>" if fijo_real_dir > 0 else ""}
                    <div class="cost-item"><span class="cost-label">Ingresos Brutos ({iibb_perc}%)</span><span class="cost-value">${p_iibb_dir:,.2f}</span></div>
                    <div class="cost-item"><span class="cost-label">Estructura Interna (2%)</span><span class="cost-value">${p_estructura_dir:,.2f}</span></div>
                </div>
                <div class="banner-card bg-pvp"><div class="label-banner">COSTO BASE PROVEEDOR</div><div class="price-main">${costo_fabrica_neto:,.0f}</div><div class="badge-banner">Sin IVA</div></div>
                <div class="banner-card bg-costo"><div class="label-banner">PVP RECOMENDADO</div><div class="price-main">${final_pvp:,.2f}</div><div class="badge-banner">{txt_cond} 🛡️</div></div>
                <div class="banner-card bg-ganancia">
                    <div class="label-banner">MARGINALIDAD PREVISTA</div><div class="price-main">${ganancia_real_dir:,.2f}</div>
                    <div class="donut-chart-container">
                        <div class="donut-block" style="background: conic-gradient(#00BFBF {margen_deseado}%, rgba(255,255,255,0.2) 0);"></div>
                        <div class="donut-text-group"><span class="donut-main-val">Objetivo: {margen_deseado}%</span><span style="color:white; font-size:11px;">Estructura limpia</span></div>
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
        pvp_target = st.number_input("PVP Competencia Mercado ($)", value=123000.0, step=1000.0, key="p_target")
    with c_inv_2:
        margen_exi = st.slider("% Margen Neto Requerido", 5, 40, 12, key="m_exi")
    with c_inv_3:
        plan_selected_inv = st.selectbox("Estrategia de Cuotas Competencia", list(FINANCIACION_OPCIONES.keys()), index=3, key="plan_inv")
        t_finan_inv = st.number_input("% Tasa Manual", value=10.0, step=0.1, key="c_fin_inv") / 100 if plan_selected_inv == "Personalizado (Manual)" else FINANCIACION_OPCIONES[plan_selected_inv] / 100
    with c_inv_4:
        peso_cat_inv = st.selectbox("Peso Correo (Tabla)", peso_list, index=13, key="peso_inv")
    st.markdown("</div>", unsafe_allow_html=True)

    if pvp_target > 0:
        banda_lookup_inv = "under_33k" if pvp_target < UMBRAL_ENVIO_GRATIS else ("33k_to_50k" if pvp_target < 50000 else "over_50k")
        envio_real_inv = NEW_SHIPPING_DATA.get(banda_lookup_inv, {}).get(peso_cat_inv, 0.0) if pvp_target >= UMBRAL_ENVIO_GRATIS else 0.0
        fijo_inv = CARGO_FIJO_MELI if pvp_target < UMBRAL_ENVIO_GRATIS else 0.0

        p_meli_inv = pvp_target * t_comi
        p_finan_inv = pvp_target * t_finan_inv
        p_iibb_inv = (pvp_target / 1.21) * t_iibb
        p_estructura_inv = pvp_target * t_estructura_fijo

        if tipo_iva == "Monotributista":
            p_margen = pvp_target * (margen_exi / 100)
            costo_max_admitido_con_iva = pvp_target - (p_meli_inv + p_finan_inv + p_iibb_inv + p_estructura_inv + envio_real_inv + fijo_inv + p_margen)
            costo_max_admitido_neto = costo_max_admitido_con_iva / 1.21
            sub_lbl = "Mono - Base Bruta"
        else:
            pvp_neto = pvp_target / 1.21
            p_ganancias_inv = pvp_neto * t_ganancias_fijo
            p_margen = pvp_neto * (margen_exi / 100)
            costo_max_admitido_neto = pvp_neto - ((p_meli_inv / 1.21) + (p_finan_inv / 1.21) + p_iibb_inv + p_ganancias_inv + p_estructura_inv + (envio_real_inv / 1.21) + (fijo_inv / 1.21) + p_margen)
            sub_lbl = "RI - Neto Puro"

        st.markdown(f"""
            <div class="results-main-container">
                <div class="cost-breakdown-list">
                    <div class="cost-item"><span class="cost-label">Comisión Clásica ({comision_clasica_pct}%)</span><span class="cost-value">${p_meli_inv:,.2f}</span></div>
                    <div class="cost-item"><span class="cost-label">Costo Financiación Plan</span><span class="cost-value">${p_finan_inv:,.2f}</span></div>
                    <div class="cost-item" style="background-color:#EFF6FF;"><span class="cost-label" style="color:#1E40AF; font-weight:700;">Flete Mercado Envíos Requerido🚚</span><span class="cost-value" style="color:#1E40AF; font-weight:700;">${envio_real_inv:,.2f}</span></div>
                    {f"<div class='cost-item'><span class='cost-label'>Cargo Fijo Detrás</span><span class='cost-value'>${fijo_inv:,.2f}</span></div>" if fijo_inv > 0 else ""}
                    <div class="cost-item"><span class="cost-label">Ingresos Brutos ({iibb_perc}%)</span><span class="cost-value">${p_iibb_inv:,.2f}</span></div>
                    <div class="cost-item"><span class="cost-label">Margen Objetivo Reservado ({margen_exi}%)</span><span class="cost-value">${p_margen:,.2f}</span></div>
                </div>
                <div class="banner-card bg-pvp"><div class="label-banner">PVP BLANCO DE COMPETENCIA</div><div class="price-main">${pvp_target:,.0f}</div><div class="badge-banner">Precio en góndola</div></div>
                <div class="banner-card bg-costo"><div class="label-banner">COSTO LÍMITE FÁBRICA</div><div class="price-main">${max(0.0, costo_max_admitido_neto):,.2f}</div><div class="badge-banner">Máximo Neto a pagar 🛡️</div></div>
                <div class="banner-card bg-ganancia">
                    <div class="label-banner">GANANCIA OBJETIVO MÍNIMA</div><div class="price-main">${p_margen:,.2f}</div>
                    <div class="badge-banner">{sub_lbl}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

st.markdown(f"<div style='text-align:center; padding:30px;'><p style='color:#94A3B8; font-size:0.8rem;'>NQ Intelligence System v{V_NUMBER} | Argentina 2026</p></div>", unsafe_allow_html=True)
