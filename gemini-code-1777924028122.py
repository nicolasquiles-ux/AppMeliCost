import streamlit as st
import pandas as pd
import requests
import re
import io

# Versión del sistema
V_NUMBER = "29.1"

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title=f"NQ | Sales Intelligence Dashboard v{V_NUMBER}", layout="wide")

# =========================================================
# DATOS MAESTROS VIGENTES 2026 (NQ Database Oficial)
# =========================================================
TABLA_ME2_BASE = {
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
    "1 Pago / Clásica (0.00%)": 0.0,
    "3 A 12 C/INT — Interés Bajo (5.00%)": 5.00,
    "3 Cuotas Mismo Precio (8.40%)": 8.40,
    "6 Cuotas Mismo Precio (12.30%)": 12.30,
    "9 Cuotas Mismo Precio (15.70%)": 15.70,
    "12 Cuotas Mismo Precio (19.20%)": 19.20,
    "Personalizado (Manual)": -1.0
}

REPUTACION_DESCUENTOS = {
    "Verde / MercadoLíder (50% desc)": 1.0,
    "Amarilla (40% desc)": 1.20,
    "Roja / Sin Reputación (0% desc)": 2.0
}

CLAVE_CORRECTA = "NQ_PRO_2026"
UMBRAL_ENVIO_GRATIS = 33000.0
CARGO_FIJO_MELI = 3800.0

nq_main_color = "#2B3E4F" 
nq_green = "#1E8449"       
nq_gold = "#BFA100"        
gray_bg = "#F8FAFC"        

# =========================================================
# FUNCIÓN API MERCADO LIBRE
# =========================================================
def consultar_api_mercadolibre(link_o_mla):
    match = re.search(r'MLA-?(\d+)', link_o_mla, re.IGNORECASE)
    if not match:
        return None, "Link o ID MLA no válido. Ejemplo: MLA1428593851 o enlace de la publicación."
    
    item_id = f"MLA{match.group(1)}"
    url = f"https://api.mercadolibre.com/items/{item_id}"
    
    try:
        res = requests.get(url, timeout=6)
        if res.status_code == 200:
            data = res.json()
            pvp = data.get("price", 0.0)
            title = data.get("title", "")
            listing_type_id = data.get("listing_type_id", "gold_special")
            shipping = data.get("shipping", {})
            logistic_type = shipping.get("logistic_type", "default")
            
            modalidad = "Mercado Envíos Tradicional (ME2)"
            if logistic_type == "fulfillment":
                modalidad = "Mercado Envíos Full"
            elif logistic_type == "self_service":
                modalidad = "Mercado Envíos Flex"
                
            is_premium = listing_type_id == "gold_pro"
            
            return {
                "item_id": item_id,
                "title": title,
                "pvp": float(pvp),
                "is_premium": is_premium,
                "modalidad": modalidad
            }, None
        else:
            return None, f"No se encontró la publicación en Mercado Libre (Código HTTP {res.status_code})."
    except Exception as e:
        return None, f"Error de conexión con la API de MeLi: {str(e)}"

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
    padding: 18px 25px; background-color: #FFFFFF;
    box-shadow: 0 4px 12px rgba(0,0,0,0.03); margin-bottom: 20px;
    border-radius: 14px; border: 1px solid #E2E8F0;
}}
.nq-branding {{ display: flex; align-items: center; }}
.nq-logo {{
    background: linear-gradient(135deg, #0055A0 0%, #00BFBF 100%);
    color: white; padding: 10px 18px; border-radius: 10px; 
    font-weight: 800; font-size: 1.5rem; margin-right: 15px; letter-spacing: -1px;
}}
.nq-title-group {{ display: flex; flex-direction: column; }}
.nq-title-country {{ color: #64748B; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; }}
.nq-dashboard {{ color: {nq_main_color}; font-weight: 800; font-size: 1.25rem; }}

.tax-bar {{
    background-color: {gray_bg}; padding: 16px 20px; border-radius: 12px;
    margin-bottom: 20px; border: 1px solid #E2E8F0;
}}

.cost-breakdown-card {{
    background: #FFFFFF; padding: 22px; border-radius: 16px;
    border: 1px solid #E2E8F0; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05);
}}
.cost-card-title {{
    font-size: 1.15rem; font-weight: 800; color: {nq_main_color};
    border-bottom: 2px solid #F1F5F9; padding-bottom: 8px; margin-bottom: 14px;
}}
.section-header-tag {{
    font-size: 0.75rem; font-weight: 800; text-transform: uppercase;
    color: #64748B; background: #F1F5F9; padding: 3px 8px; border-radius: 6px;
    margin-top: 10px; margin-bottom: 4px; display: inline-block;
}}
.cost-item {{ 
    display: flex; justify-content: space-between; align-items: center; font-size: 0.88rem; 
    border-bottom: 1px solid #F8FAFC; padding: 6px 0;
}}
.cost-label {{ color: #334155; font-weight: 600; }}
.cost-label-bold {{ color: #0F172A; font-weight: 800; }}
.cost-value {{ color: #0F172A; font-weight: 700; text-align: right; }}
.cost-value-highlight {{ color: #0055A0; font-weight: 800; text-align: right; font-size: 0.95rem; }}

.banner-card {{
    color: white; padding: 18px; display: flex; flex-direction: column;
    justify-content: center; align-items: center; text-align: center; gap: 2px;
    border-radius: 14px; margin-bottom: 15px;
    box-shadow: 0 8px 16px rgba(0,0,0,0.06);
}}
.bg-pvp {{ background-color: {nq_main_color}; }}
.bg-costo {{ background-color: {nq_gold}; }}
.bg-ganancia {{ background-color: {nq_green}; }}
.bg-loss {{ background-color: #C0392B; }}

.label-banner {{ color: rgba(255,255,255,0.85); font-size: 0.75rem; font-weight: 700; text-transform: uppercase; }}
.price-main {{ color: white; font-size: 1.8rem; font-weight: 800; margin: 2px 0; }}
.badge-banner {{
    background: rgba(255,255,255,0.22); color: white;
    padding: 3px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 700;
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
# ENCABEZADO CORPORATIVO Y MÓDULO API MELI
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

# --- BARRA DE IMPORTACIÓN DESDE API MELI ---
with st.expander("🔍 **IMPORTAR PUBLICACIÓN DIRECTO DESDE MERCADO LIBRE (LINK O MLA)**", expanded=False):
    c_api1, c_api2 = st.columns([3, 1])
    with c_api1:
        input_meli_link = st.text_input("Pega el Link o ID MLA (Ej: https://articulo.mercadolibre.com.ar/MLA-1428593851... o MLA1428593851)", key="input_api_meli")
    with c_api2:
        st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
        btn_importar = st.button("🚀 Cargar de MeLi", use_container_width=True)
        
    if btn_importar and input_meli_link:
        data_item, error_msg = consultar_api_mercadolibre(input_meli_link)
        if error_msg:
            st.error(f"❌ {error_msg}")
        else:
            st.session_state['fetched_pvp'] = data_item['pvp']
            st.session_state['fetched_title'] = data_item['title']
            st.session_state['fetched_modalidad'] = data_item['modalidad']
            st.session_state['fetched_is_premium'] = data_item['is_premium']
            st.success(f"✅ Cargado: **{data_item['title']}** | PVP: **${data_item['pvp']:,.2f}** | Logística: **{data_item['modalidad']}**")

# =========================================================
# CONTROL FISCAL Y CONFIGURACIÓN GENERAL
# =========================================================
with st.container():
    st.markdown("<div class='tax-bar'>", unsafe_allow_html=True)
    c_tax1, c_tax2, c_tax3, c_tax4, c_tax5, c_tax6 = st.columns([1.5, 1, 1, 1, 1, 1])
    with c_tax1:
        tipo_iva = st.radio("Configuración Impositiva", ["Responsable Inscripto", "Monotributista"], horizontal=True)
    with c_tax2:
        reputacion_sel = st.selectbox("Reputación Vendedor", list(REPUTACION_DESCUENTOS.keys()), index=0)
    with c_tax3:
        iibb_perc = st.number_input("% Ingresos Brutos (IIBB)", value=3.5, step=0.1)
    with c_tax4:
        comision_vender_input = st.number_input("% Cargo Vender MeLi", value=14.15, step=0.1)
    with c_tax5:
        alicuota_iva_prod = st.selectbox("% IVA Producto", [21.0, 10.5, 0.0], index=0)
    with c_tax6:
        incluir_ganancias_m = st.checkbox("Incluir % Ganancias Anual", value=False, help="Desactivado para P&L operativo directo por unidad")
    st.markdown("</div>", unsafe_allow_html=True)

t_iibb = iibb_perc / 100
t_comi_base = comision_vender_input / 100
t_iva_prod = alicuota_iva_prod / 100
t_ganancias_fijo = 0.05 if incluir_ganancias_m else 0.0
factor_reputacion = REPUTACION_DESCUENTOS[reputacion_sel]

peso_list = list(TABLA_ME2_BASE.keys())

def calcular_flete_segun_modalidad(pvp_evaluado, peso_categoria, modalidad, costo_moto, reembolso_flex, cargo_full_unit, cargo_full_storage):
    if modalidad == "Mercado Envíos Flex":
        return costo_moto - reembolso_flex
    elif modalidad == "Mercado Envíos Full":
        flete_base = 0.0
        if pvp_evaluado >= UMBRAL_ENVIO_GRATIS:
            base = TABLA_ME2_BASE.get(peso_categoria, [0.0, 0.0, 0.0])[2] if pvp_evaluado >= 50000 else TABLA_ME2_BASE.get(peso_categoria, [0.0, 0.0, 0.0])[1]
            flete_base = base * factor_reputacion
        return flete_base + cargo_full_unit + cargo_full_storage
    else:
        # ME2 Tradicional
        if pvp_evaluado < UMBRAL_ENVIO_GRATIS:
            return 0.0
        elif pvp_evaluado < 50000:
            base = TABLA_ME2_BASE.get(peso_categoria, [0.0, 0.0, 0.0])[1]
        else:
            base = TABLA_ME2_BASE.get(peso_categoria, [0.0, 0.0, 0.0])[2]
        return base * factor_reputacion

def calcular_pvp_recomendado_func(costo_f, margen_deseado, t_finan, modalidad_log, peso_cat, costo_moto, reemb_flex, full_unit, full_stor):
    pvp_calc = costo_f * 2.0
    for _ in range(10):
        flete_b = calcular_flete_segun_modalidad(pvp_calc, peso_cat, modalidad_log, costo_moto, reemb_flex, full_unit, full_stor)
        fijo_b = CARGO_FIJO_MELI if pvp_calc < UMBRAL_ENVIO_GRATIS else 0.0

        if tipo_iva == "Monotributista":
            costo_inc = costo_f * (1 + t_iva_prod)
            denom = 1 - (t_comi_base + t_finan + (t_iibb / (1 + t_iva_prod)) + margen_deseado)
            if denom > 0: pvp_calc = (costo_inc + flete_b + fijo_b) / denom
        else:
            factor_neto = 1 / (1 + t_iva_prod)
            comi_f = (t_comi_base + t_finan)
            denom = factor_neto - comi_f - (t_iibb * factor_neto) - (t_ganancias_fijo * factor_neto) - margen_deseado
            if denom > 0: pvp_calc = (costo_f + flete_b + fijo_b) / denom
    return round(pvp_calc, 2)

def render_desglose_html(costo_fabrica_neto, pvp, comi_m_bruta, flete_bruto, cargo_fijo_bruto, iibb_m, gan_m, est_m, ads_m, iva_pagar_m, ganancia_neta, margen_pct, modalidad_log, titulo_costo_prod="Costo Fábrica (Sin IVA)"):
    pvp_neto = pvp / (1 + t_iva_prod)
    costo_total = pvp - ganancia_neta
    
    iva_row_html = ""
    if tipo_iva == "Responsable Inscripto":
        iva_row_html = f"""
        <div class="cost-item" style="background-color: #FEF3C7; padding: 6px 8px; border-radius: 6px; margin: 4px 0;">
            <span class="cost-label-bold" style="color: #92400E;"><b>IVA Neto a Pagar (Posición AFIP)</b></span>
            <span class="cost-value" style="color: #92400E; font-weight: 800;">${iva_pagar_m:,.2f}</span>
        </div>
        """

    flete_label = "Flete Logística" if flete_bruto >= 0 else "Beneficio / Saldo Flex"
    color_bg = '#ECFDF5' if ganancia_neta >= 0 else '#FEF2F2'
    color_txt = '#065F46' if ganancia_neta >= 0 else '#991B1B'

    html = f"""
    <div class="cost-breakdown-card">
        <div class="cost-card-title">
            <span>📋 DESGLOSE ANALÍTICO DE COSTOS</span>
        </div>
        
        <span class="section-header-tag">1. Ingresos y Venta</span>
        <div class="cost-item"><span class="cost-label-bold">PRECIO DE VENTA PÚBLICO (PVP)</span><span class="cost-value-highlight">${pvp:,.2f}</span></div>
        <div class="cost-item"><span class="cost-label">Venta Neta (Sin IVA)</span><span class="cost-value">${pvp_neto:,.2f}</span></div>
        
        <span class="section-header-tag">2. Costo de Producto</span>
        <div class="cost-item"><span class="cost-label-bold">{titulo_costo_prod}</span><span class="cost-value">${costo_fabrica_neto:,.2f}</span></div>
        
        <span class="section-header-tag">3. Gastos Mercado Libre ({modalidad_log})</span>
        <div class="cost-item"><span class="cost-label">Comisión ML + Financiación</span><span class="cost-value">${comi_m_bruta:,.2f}</span></div>
        <div class="cost-item"><span class="cost-label">{flete_label}</span><span class="cost-value">${flete_bruto:,.2f}</span></div>
        <div class="cost-item"><span class="cost-label">Cargo Fijo por Unidad</span><span class="cost-value">${cargo_fijo_bruto:,.2f}</span></div>
        
        <span class="section-header-tag">4. Carga Impositiva & Operativa</span>
        <div class="cost-item"><span class="cost-label">Ingresos Brutos ({iibb_perc:.1f}%)</span><span class="cost-value">${iibb_m:,.2f}</span></div>
        <div class="cost-item"><span class="cost-label">Impuesto a las Ganancias ({'5.0%' if incluir_ganancias_m else '0.0%'})</span><span class="cost-value">${gan_m:,.2f}</span></div>
        <div class="cost-item"><span class="cost-label">Mercado Ads (Publicidad)</span><span class="cost-value">${ads_m:,.2f}</span></div>
        <div class="cost-item"><span class="cost-label">Costo Estructura / Depósito</span><span class="cost-value">${est_m:,.2f}</span></div>
        {iva_row_html}
        
        <div class="cost-item" style="margin-top: 12px; border-top: 2px solid #CBD5E1; padding-top: 8px;">
            <span class="cost-label-bold" style="font-size: 0.95rem;">COSTO TOTAL OPERATIVO</span>
            <span class="cost-value-highlight" style="color: #0F172A;">${costo_total:,.2f}</span>
        </div>
        <div class="cost-item" style="background-color: {color_bg}; padding: 8px 10px; border-radius: 8px; margin-top: 8px;">
            <span class="cost-label-bold" style="color: {color_txt}; font-size: 0.95rem;">GANANCIA NETA FINAL</span>
            <span class="cost-value" style="color: {color_txt}; font-weight: 800; font-size: 1.05rem;">${ganancia_neta:,.2f} ({margen_pct:.2f}%)</span>
        </div>
    </div>
    """
    return "".join([line.strip() for line in html.splitlines()])

def render_indicadores_nativos(costo_fabrica, comi_bruta, flete_bruto, cargo_fijo, iibb, ganancias, est, ads, iva_pagar, ganancia_neta, pvp):
    st.markdown("<h4 style='color:#2B3E4F; font-size:1.05rem; font-weight:800; margin-top:15px;'>📊 Composición Porcentual sobre el PVP</h4>", unsafe_allow_html=True)
    if pvp <= 0: return

    pct_fabrica = (costo_fabrica / pvp) * 100
    pct_meli = ((comi_bruta + max(0.0, flete_bruto) + cargo_fijo) / pvp) * 100
    pct_impuestos = ((iibb + ganancias + (iva_pagar if iva_pagar > 0 else 0)) / pvp) * 100
    pct_operativa = ((est + ads) / pvp) * 100
    pct_ganancia = (ganancia_neta / pvp) * 100 if ganancia_neta > 0 else 0.0

    st.write(f"🏭 **Costo de Producto (Fábrica):** {pct_fabrica:.1f}%")
    st.progress(min(max(pct_fabrica / 100, 0.0), 1.0))

    st.write(f"🟡 **Mercado Libre (Comisión + Logística):** {pct_meli:.1f}%")
    st.progress(min(max(pct_meli / 100, 0.0), 1.0))

    st.write(f"🏛️ **Carga Fiscal (IIBB + Ganancias + IVA):** {pct_impuestos:.1f}%")
    st.progress(min(max(pct_impuestos / 100, 0.0), 1.0))

    st.write(f"📢 **Operativa & Ads:** {pct_operativa:.1f}%")
    st.progress(min(max(pct_operativa / 100, 0.0), 1.0))

    st.write(f"🟢 **Ganancia Neta Limpia:** {pct_ganancia:.1f}%")
    st.progress(min(max(pct_ganancia / 100, 0.0), 1.0))

# --- TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 REALIDAD REAL (Compro a X y Vendo a Y)", 
    "☝️ CALCULAR PVP RECOMENDADO (Fábrica -> Venta)", 
    "🎯 ANALIZAR COSTO OBJETIVO (Venta -> Fábrica)",
    "🕵️ INGENIERÍA INVERSA (Analizar Competidor)",
    "📁 PROCESAMIENTO MASIVO (Upload SKU / Lote)"
])

# =========================================================
# SOLAPA 1: REALIDAD REAL
# =========================================================
with tab1:
    col_left, col_right = st.columns([1.1, 1.1])
    
    with col_left:
        st.markdown(f"<div style='background-color: {gray_bg}; padding: 20px; border-radius: 12px;'>", unsafe_allow_html=True)
        precio_lista_1 = st.number_input("Precio de Lista Fábrica SIN IVA ($)", value=76513.95, step=1000.0, key="plist_1")
        desc_prov_perc_1 = st.number_input("% Descuento / Bonificación Proveedor", value=8.0, step=1.0, key="dprov_1") / 100
        x_costo_fabrica = precio_lista_1 * (1 - desc_prov_perc_1)
        st.caption(f"💡 Costo Real de Compra Neto: **${x_costo_fabrica:,.2f}**")

        default_pvp_1 = st.session_state.get('fetched_pvp', 115000.0)
        y_pvp_venta = st.number_input("PVP Publicado en MeLi (Y) ($)", value=float(default_pvp_1), step=1000.0, key="y_pvp_k")
        
        default_plan_idx = 0
        if st.session_state.get('fetched_is_premium', False):
            default_plan_idx = 2
            
        plan_selected_x = st.selectbox("Plan Financiamiento / Cuotas", list(FINANCIACION_PRESETS.keys()), index=default_plan_idx, key="plan_x_k")
        t_finan_val_x = st.number_input("% Tasa Custom", value=0.0, step=0.1, key="custom_fin_x") / 100 if plan_selected_x == "Personalizado (Manual)" else FINANCIACION_PRESETS[plan_selected_x] / 100
        
        default_log_idx = 0
        fetched_log = st.session_state.get('fetched_modalidad', None)
        if fetched_log == "Mercado Envíos Flex": default_log_idx = 1
        elif fetched_log == "Mercado Envíos Full": default_log_idx = 2
        
        modalidad_log_1 = st.selectbox("Modalidad Logística", ["Mercado Envíos Tradicional (ME2)", "Mercado Envíos Flex", "Mercado Envíos Full"], index=default_log_idx, key="log_1")
        peso_cat_x = st.selectbox("Peso Correo Tabla", peso_list, index=13, key="peso_x_k")
        
        costo_moto_1, reemb_flex_1, full_unit_1, full_stor_1 = 0.0, 0.0, 0.0, 0.0
        if modalidad_log_1 == "Mercado Envíos Flex":
            reemb_flex_1 = st.number_input("Reembolso MeLi Flex ($)", value=5500.0, step=500.0, key="flex_re_1")
            costo_moto_1 = st.number_input("Costo Real Moto/Cadetería ($)", value=3500.0, step=500.0, key="flex_cm_1")
        elif modalidad_log_1 == "Mercado Envíos Full":
            full_unit_1 = st.number_input("Cargo Ingreso/Handling Full ($)", value=800.0, step=100.0, key="full_u_1")
            full_stor_1 = st.number_input("Cargo Almacenamiento Prolongado ($)", value=0.0, step=100.0, key="full_s_1")

        mkt_ads_perc_1 = st.number_input("% Inversión Mercado Ads (ACOS)", value=0.0, step=0.5, key="ads_1") / 100
        costo_est_perc_1 = st.number_input("% Costo Estructura Opcional", value=0.0, step=0.5, key="est_1") / 100
        st.markdown("</div>", unsafe_allow_html=True)

        flete_bruto = calcular_flete_segun_modalidad(y_pvp_venta, peso_cat_x, modalidad_log_1, costo_moto_1, reemb_flex_1, full_unit_1, full_stor_1)
        fijo_bruto = CARGO_FIJO_MELI if y_pvp_venta < UMBRAL_ENVIO_GRATIS else 0.0
        
        comi_bruta = y_pvp_venta * (t_comi_base + t_finan_val_x)
        pvp_neto = y_pvp_venta / (1 + t_iva_prod)
        iibb_m = pvp_neto * t_iibb
        gan_m = pvp_neto * t_ganancias_fijo
        est_m = y_pvp_venta * costo_est_perc_1
        ads_m = y_pvp_venta * mkt_ads_perc_1
        
        if tipo_iva == "Monotributista":
            costo_fabrica_inc = x_costo_fabrica * (1 + t_iva_prod)
            ganancia_real = y_pvp_venta - (costo_fabrica_inc + comi_bruta + flete_bruto + fijo_bruto + iibb_m + est_m + ads_m)
            iva_pagar_m = 0.0
        else:
            iva_venta = y_pvp_venta - pvp_neto
            iva_compra = x_costo_fabrica * t_iva_prod
            iva_comi = comi_bruta - (comi_bruta / 1.21)
            iva_flete = flete_bruto - (flete_bruto / 1.21) if flete_bruto >= 0 else -(abs(flete_bruto) - (abs(flete_bruto)/1.21))
            iva_fijo = fijo_bruto - (fijo_bruto / 1.21)
            iva_ads = ads_m - (ads_m / 1.21)
            
            iva_pagar_m = iva_venta - (iva_compra + iva_comi + iva_flete + iva_fijo + iva_ads)
            ganancia_real = pvp_neto - x_costo_fabrica - (comi_bruta / 1.21) - (flete_bruto / 1.21) - (fijo_bruto / 1.21) - (ads_m / 1.21) - iibb_m - gan_m - est_m - iva_pagar_m

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
        
        render_indicadores_nativos(x_costo_fabrica, comi_bruta, flete_bruto, fijo_bruto, iibb_m, gan_m, est_m, ads_m, iva_pagar_m, ganancia_real, y_pvp_venta)

    with col_right:
        st.markdown(render_desglose_html(x_costo_fabrica, y_pvp_venta, comi_bruta, flete_bruto, fijo_bruto, iibb_m, gan_m, est_m, ads_m, iva_pagar_m, ganancia_real, rendimiento_real, modalidad_log_1, "Mi Costo Fábrica Neto"), unsafe_allow_html=True)

# =========================================================
# SOLAPA 2: PVP RECOMENDADO
# =========================================================
with tab2:
    col_left2, col_right2 = st.columns([1.1, 1.1])
    
    with col_left2:
        st.markdown(f"<div style='background-color: {gray_bg}; padding: 20px; border-radius: 12px;'>", unsafe_allow_html=True)
        precio_lista_2 = st.number_input("Precio de Lista Fábrica SIN IVA ($)", value=76513.95, step=1000.0, key="plist_2")
        desc_prov_perc_2 = st.number_input("% Descuento / Bonificación Proveedor", value=8.0, step=1.0, key="dprov_2") / 100
        costo_f_tab2 = precio_lista_2 * (1 - desc_prov_perc_2)
        st.caption(f"💡 Costo Real de Compra Neto: **${costo_f_tab2:,.2f}**")

        margen_deseado_tab2 = st.number_input("% Margen Neto Deseado", value=10.0, step=0.5, key="m_tab2") / 100
        plan_selected_tab2 = st.selectbox("Plan Financiamiento / Cuotas", list(FINANCIACION_PRESETS.keys()), index=0, key="plan_tab2")
        t_finan_tab2 = st.number_input("% Tasa Custom", value=0.0, step=0.1, key="c_fin_tab2") / 100 if plan_selected_tab2 == "Personalizado (Manual)" else FINANCIACION_PRESETS[plan_selected_tab2] / 100
        
        modalidad_log_2 = st.selectbox("Modalidad Logística", ["Mercado Envíos Tradicional (ME2)", "Mercado Envíos Flex", "Mercado Envíos Full"], index=0, key="log_2")
        peso_cat_tab2 = st.selectbox("Peso Correo Tabla", peso_list, index=13, key="peso_tab2")
        
        costo_moto_2, reemb_flex_2, full_unit_2, full_stor_2 = 0.0, 0.0, 0.0, 0.0
        if modalidad_log_2 == "Mercado Envíos Flex":
            reemb_flex_2 = st.number_input("Reembolso MeLi Flex ($)", value=5500.0, step=500.0, key="flex_re_2")
            costo_moto_2 = st.number_input("Costo Real Moto/Cadetería ($)", value=3500.0, step=500.0, key="flex_cm_2")
        elif modalidad_log_2 == "Mercado Envíos Full":
            full_unit_2 = st.number_input("Cargo Ingreso/Handling Full ($)", value=800.0, step=100.0, key="full_u_2")
            full_stor_2 = st.number_input("Cargo Almacenamiento Prolongado ($)", value=0.0, step=100.0, key="full_s_2")

        mkt_ads_perc_2 = st.number_input("% Inversión Mercado Ads (ACOS)", value=0.0, step=0.5, key="ads_2") / 100
        costo_est_perc_2 = st.number_input("% Costo Estructura Opcional", value=0.0, step=0.5, key="est_2") / 100
        st.markdown("</div>", unsafe_allow_html=True)

        if costo_f_tab2 > 0:
            pvp_calc = calcular_pvp_recomendado_func(costo_f_tab2, margen_deseado_tab2 + mkt_ads_perc_2 + costo_est_perc_2, t_finan_tab2, modalidad_log_2, peso_cat_tab2, costo_moto_2, reemb_flex_2, full_unit_2, full_stor_2)

            flete_bruto2 = calcular_flete_segun_modalidad(pvp_calc, peso_cat_tab2, modalidad_log_2, costo_moto_2, reemb_flex_2, full_unit_2, full_stor_2)
            fijo_bruto2 = CARGO_FIJO_MELI if pvp_calc < UMBRAL_ENVIO_GRATIS else 0.0
            comi_bruta2 = pvp_calc * (t_comi_base + t_finan_tab2)
            pvp_neto2 = pvp_calc / (1 + t_iva_prod)
            iibb_m2 = pvp_neto2 * t_iibb
            gan_m2 = pvp_neto2 * t_ganancias_fijo
            est_m2 = pvp_calc * costo_est_perc_2
            ads_m2 = pvp_calc * mkt_ads_perc_2
            
            iva_v2 = pvp_calc - pvp_neto2
            iva_c2 = costo_f_tab2 * t_iva_prod
            iva_flete_2 = flete_bruto2 - (flete_bruto2 / 1.21) if flete_bruto2 >= 0 else -(abs(flete_bruto2) - (abs(flete_bruto2)/1.21))
            iva_pagar2 = iva_v2 - (iva_c2 + (comi_bruta2 - comi_bruta2/1.21) + iva_flete_2 + (fijo_bruto2 - fijo_bruto2/1.21) + (ads_m2 - ads_m2/1.21)) if tipo_iva == "Responsable Inscripto" else 0.0
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
            
            render_indicadores_nativos(costo_f_tab2, comi_bruta2, flete_bruto2, fijo_bruto2, iibb_m2, gan_m2, est_m2, ads_m2, iva_pagar2, ganancia_neta2, pvp_calc)

    with col_right2:
        if costo_f_tab2 > 0:
            st.markdown(render_desglose_html(costo_f_tab2, pvp_calc, comi_bruta2, flete_bruto2, fijo_bruto2, iibb_m2, gan_m2, est_m2, ads_m2, iva_pagar2, ganancia_neta2, margen_deseado_tab2*100, modalidad_log_2, "Mi Costo Fábrica Neto"), unsafe_allow_html=True)

# =========================================================
# SOLAPA 3: ANALIZAR COSTO OBJETIVO
# =========================================================
with tab3:
    col_left3, col_right3 = st.columns([1.1, 1.1])
    
    with col_left3:
        st.markdown(f"<div style='background-color: {gray_bg}; padding: 20px; border-radius: 12px;'>", unsafe_allow_html=True)
        default_pvp_3 = st.session_state.get('fetched_pvp', 115000.0)
        pvp_target = st.number_input("PVP Mercado Objetivo ($)", value=float(default_pvp_3), step=1000.0, key="pvp_obj")
        margen_target = st.number_input("% Margen Neto Pretendido", value=10.0, step=0.5, key="m_obj") / 100
        plan_selected_obj = st.selectbox("Plan Financiamiento / Cuotas", list(FINANCIACION_PRESETS.keys()), index=0, key="plan_obj")
        t_finan_obj = st.number_input("% Tasa Custom", value=0.0, step=0.1, key="c_fin_obj") / 100 if plan_selected_obj == "Personalizado (Manual)" else FINANCIACION_PRESETS[plan_selected_obj] / 100
        
        modalidad_log_3 = st.selectbox("Modalidad Logística", ["Mercado Envíos Tradicional (ME2)", "Mercado Envíos Flex", "Mercado Envíos Full"], index=0, key="log_3")
        peso_cat_obj = st.selectbox("Peso Correo Tabla", peso_list, index=13, key="peso_obj")
        
        costo_moto_3, reemb_flex_3, full_unit_3, full_stor_3 = 0.0, 0.0, 0.0, 0.0
        if modalidad_log_3 == "Mercado Envíos Flex":
            reemb_flex_3 = st.number_input("Reembolso MeLi Flex ($)", value=5500.0, step=500.0, key="flex_re_3")
            costo_moto_3 = st.number_input("Costo Real Moto/Cadetería ($)", value=3500.0, step=500.0, key="flex_cm_3")
        elif modalidad_log_3 == "Mercado Envíos Full":
            full_unit_3 = st.number_input("Cargo Ingreso/Handling Full ($)", value=800.0, step=100.0, key="full_u_3")
            full_stor_3 = st.number_input("Cargo Almacenamiento Prolongado ($)", value=0.0, step=100.0, key="full_s_3")

        mkt_ads_perc_3 = st.number_input("% Inversión Mercado Ads (ACOS)", value=0.0, step=0.5, key="ads_3") / 100
        costo_est_perc_3 = st.number_input("% Costo Estructura Opcional", value=0.0, step=0.5, key="est_3") / 100
        st.markdown("</div>", unsafe_allow_html=True)

        if pvp_target > 0:
            flete_bruto3 = calcular_flete_segun_modalidad(pvp_target, peso_cat_obj, modalidad_log_3, costo_moto_3, reemb_flex_3, full_unit_3, full_stor_3)
            fijo_bruto3 = CARGO_FIJO_MELI if pvp_target < UMBRAL_ENVIO_GRATIS else 0.0

            comi_bruta3 = pvp_target * (t_comi_base + t_finan_obj)
            pvp_neto3 = pvp_target / (1 + t_iva_prod)
            iibb_m3 = pvp_neto3 * t_iibb
            gan_m3 = pvp_neto3 * t_ganancias_fijo
            est_m3 = pvp_target * costo_est_perc_3
            ads_m3 = pvp_target * mkt_ads_perc_3
            ganancia_neta3 = pvp_target * margen_target

            if tipo_iva == "Monotributista":
                costo_max_inc = pvp_target - (ganancia_neta3 + comi_bruta3 + flete_bruto3 + fijo_bruto3 + iibb_m3 + est_m3 + ads_m3)
                costo_max_neto3 = costo_max_inc / (1 + t_iva_prod)
                iva_pagar3 = 0.0
            else:
                costo_max_neto3 = pvp_neto3 - (comi_bruta3 / 1.21) - (flete_bruto3 / 1.21) - (fijo_bruto3 / 1.21) - (ads_m3 / 1.21) - iibb_m3 - gan_m3 - est_m3 - ganancia_neta3
                iva_v3 = pvp_target - pvp_neto3
                iva_c3 = costo_max_neto3 * t_iva_prod
                iva_flete_3 = flete_bruto3 - (flete_bruto3 / 1.21) if flete_bruto3 >= 0 else -(abs(flete_bruto3) - (abs(flete_bruto3)/1.21))
                iva_pagar3 = iva_v3 - (iva_c3 + (comi_bruta3 - comi_bruta3/1.21) + iva_flete_3 + (fijo_bruto3 - fijo_bruto3/1.21) + (ads_m3 - ads_m3/1.21))

            st.markdown(f"""
            <div style="display: flex; gap: 10px; margin-top: 15px;">
                <div class="banner-card bg-pvp" style="flex:1;">
                    <span class="label-banner">PVP Objetivo</span>
                    <span class="price-main">${pvp_target:,.2f}</span>
                </div>
                <div class="banner-card bg-costo" style="flex:1;">
                    <span class="label-banner">Costo Máximo Fábrica</span>
                    <span class="price-main">${costo_max_neto3:,.2f}</span>
                    <span class="badge-banner">Sin IVA</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            render_indicadores_nativos(costo_max_neto3, comi_bruta3, flete_bruto3, fijo_bruto3, iibb_m3, gan_m3, est_m3, ads_m3, iva_pagar3, ganancia_neta3, pvp_target)

    with col_right3:
        if pvp_target > 0:
            st.markdown(render_desglose_html(costo_max_neto3, pvp_target, comi_bruta3, flete_bruto3, fijo_bruto3, iibb_m3, gan_m3, est_m3, ads_m3, iva_pagar3, ganancia_neta3, margen_target*100, modalidad_log_3, "Costo Máximo Compra Neto"), unsafe_allow_html=True)

# =========================================================
# SOLAPA 4: INGENIERÍA INVERSA (COMPETIDOR)
# =========================================================
with tab4:
    col_left4, col_right4 = st.columns([1.1, 1.1])
    
    with col_left4:
        st.markdown(f"<div style='background-color: {gray_bg}; padding: 20px; border-radius: 12px;'>", unsafe_allow_html=True)
        default_pvp_4 = st.session_state.get('fetched_pvp', 115000.0)
        pvp_comp = st.number_input("PVP Competidor Publicado ($)", value=float(default_pvp_4), step=1000.0, key="pvp_comp_k")
        
        default_plan_comp_idx = 0
        if st.session_state.get('fetched_is_premium', False):
            default_plan_comp_idx = 2
            
        plan_selected_comp = st.selectbox("Plan Financiamiento Competidor", list(FINANCIACION_PRESETS.keys()), index=default_plan_comp_idx, key="plan_comp_k")
        t_finan_comp = st.number_input("% Tasa Custom Competidor", value=0.0, step=0.1, key="c_fin_comp") / 100 if plan_selected_comp == "Personalizado (Manual)" else FINANCIACION_PRESETS[plan_selected_comp] / 100
        
        default_log_comp_idx = 0
        if fetched_log == "Mercado Envíos Flex": default_log_comp_idx = 1
        elif fetched_log == "Mercado Envíos Full": default_log_comp_idx = 2

        modalidad_log_4 = st.selectbox("Modalidad Logística Competidor", ["Mercado Envíos Tradicional (ME2)", "Mercado Envíos Flex", "Mercado Envíos Full"], index=default_log_comp_idx, key="log_4")
        peso_cat_comp = st.selectbox("Peso Correo Tabla Competidor", peso_list, index=13, key="peso_comp")
        
        costo_moto_4, reemb_flex_4, full_unit_4, full_stor_4 = 0.0, 0.0, 0.0, 0.0
        if modalidad_log_4 == "Mercado Envíos Flex":
            reemb_flex_4 = st.number_input("Reembolso MeLi Flex ($)", value=5500.0, step=500.0, key="flex_re_4")
            costo_moto_4 = st.number_input("Costo Real Moto/Cadetería ($)", value=3500.0, step=500.0, key="flex_cm_4")
        elif modalidad_log_4 == "Mercado Envíos Full":
            full_unit_4 = st.number_input("Cargo Ingreso/Handling Full ($)", value=800.0, step=100.0, key="full_u_4")
            full_stor_4 = st.number_input("Cargo Almacenamiento Prolongado ($)", value=0.0, step=100.0, key="full_s_4")

        est_margen_comp = st.number_input("% Margen Neto Estimado del Competidor", value=12.0, step=0.5, key="m_comp") / 100
        mkt_ads_perc_4 = st.number_input("% Inversión Ads Competidor", value=3.0, step=0.5, key="ads_4") / 100
        st.markdown("</div>", unsafe_allow_html=True)

        if pvp_comp > 0:
            flete_bruto4 = calcular_flete_segun_modalidad(pvp_comp, peso_cat_comp, modalidad_log_4, costo_moto_4, reemb_flex_4, full_unit_4, full_stor_4)
            fijo_bruto4 = CARGO_FIJO_MELI if pvp_comp < UMBRAL_ENVIO_GRATIS else 0.0

            comi_bruta4 = pvp_comp * (t_comi_base + t_finan_comp)
            pvp_neto4 = pvp_comp / (1 + t_iva_prod)
            iibb_m4 = pvp_neto4 * t_iibb
            gan_m4 = pvp_neto4 * t_ganancias_fijo
            ads_m4 = pvp_comp * mkt_ads_perc_4
            ganancia_neta4 = pvp_comp * est_margen_comp

            if tipo_iva == "Monotributista":
                costo_est_comp_inc = pvp_comp - (ganancia_neta4 + comi_bruta4 + flete_bruto4 + fijo_bruto4 + iibb_m4 + ads_m4)
                costo_est_comp_neto = costo_est_comp_inc / (1 + t_iva_prod)
                iva_pagar4 = 0.0
            else:
                costo_est_comp_neto = pvp_neto4 - (comi_bruta4 / 1.21) - (flete_bruto4 / 1.21) - (fijo_bruto4 / 1.21) - (ads_m4 / 1.21) - iibb_m4 - gan_m4 - ganancia_neta4
                iva_v4 = pvp_comp - pvp_neto4
                iva_c4 = costo_est_comp_neto * t_iva_prod
                iva_flete_4 = flete_bruto4 - (flete_bruto4 / 1.21) if flete_bruto4 >= 0 else -(abs(flete_bruto4) - (abs(flete_bruto4)/1.21))
                iva_pagar4 = iva_v4 - (iva_c4 + (comi_bruta4 - comi_bruta4/1.21) + iva_flete_4 + (fijo_bruto4 - fijo_bruto4/1.21) + (ads_m4 - ads_m4/1.21))

            st.markdown(f"""
            <div style="display: flex; gap: 10px; margin-top: 15px;">
                <div class="banner-card bg-pvp" style="flex:1;">
                    <span class="label-banner">PVP Competidor</span>
                    <span class="price-main">${pvp_comp:,.2f}</span>
                </div>
                <div class="banner-card bg-costo" style="flex:1;">
                    <span class="label-banner">Costo Fábrica Estimado</span>
                    <span class="price-main">${costo_est_comp_neto:,.2f}</span>
                    <span class="badge-banner">Sin IVA</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            render_indicadores_nativos(costo_est_comp_neto, comi_bruta4, flete_bruto4, fijo_bruto4, iibb_m4, gan_m4, 0.0, ads_m4, iva_pagar4, ganancia_neta4, pvp_comp)

    with col_right4:
        if pvp_comp > 0:
            st.markdown(render_desglose_html(costo_est_comp_neto, pvp_comp, comi_bruta4, flete_bruto4, fijo_bruto4, iibb_m4, gan_m4, 0.0, ads_m4, iva_pagar4, ganancia_neta4, est_margen_comp*100, modalidad_log_4, "Costo Fábrica Estimado Competidor"), unsafe_allow_html=True)

# =========================================================
# SOLAPA 5: PROCESAMIENTO MASIVO (MEJORADO EN V29.1)
# =========================================================
with tab5:
    st.markdown("### 📁 Carga Masiva de SKUs y Cálculo Automático de Matriz de Precios")
    st.markdown("Subí tu archivo Excel (`.xlsx`) o CSV con el catálogo. El sistema procesará los costos y generará los **4 escenarios de PVP sugeridos** para cada producto.")

    col_m1, col_m2 = st.columns([1, 1])
    with col_m1:
        margen_batch = st.number_input("% Margen Neto Objetivo Global", value=10.0, step=0.5, key="m_batch") / 100
        peso_cat_batch = st.selectbox("Peso Correo por Defecto (si no está especificado)", peso_list, index=13, key="peso_batch")
    with col_m2:
        tasa_3cuotas_custom = st.number_input("% Recargo Tasa 3 Cuotas (Premium)", value=8.4, step=0.1, key="t3c_batch") / 100
        tasa_1cuota_custom = 0.0

    uploaded_file = st.file_uploader("Arrastrá tu archivo Excel o CSV aquí", type=["xlsx", "csv"])

    if uploaded_file is not None:
        try:
            df_input = None
            
            # --- LECTURA RUSTICA Y MULTIFORMATO SEGURO ---
            if uploaded_file.name.endswith('.csv'):
                # Intenta auto-detectar separadores comunes (;, , o tab)
                content = uploaded_file.getvalue().decode('utf-8', errors='ignore')
                sep_detected = ';' if ';' in content.split('\n')[0] else (',' if ',' in content.split('\n')[0] else '\t')
                uploaded_file.seek(0)
                df_input = pd.read_csv(uploaded_file, sep=sep_detected)
            else:
                try:
                    df_input = pd.read_excel(uploaded_file)
                except Exception as openpyxl_err:
                    st.error("⚠️ Falta la librería 'openpyxl' en el servidor para leer archivos .xlsx. Por favor guarda/exporta tu archivo como formato **CSV** e intentalo de nuevo.")
                    st.stop()

            if df_input is not None:
                st.write("📋 **Vista previa del archivo cargado:**", df_input.head())

                # Normalizar nombres de columnas
                cols_map = {c: str(c).strip().lower() for c in df_input.columns}
                df_input.rename(columns=cols_map, inplace=True)

                col_sku = next((c for c in df_input.columns if 'sku' in c or 'codigo' in c or 'código' in c or 'articulo' in c), None)
                col_costo = next((c for c in df_input.columns if 'costo' in c or 'precio' in c or 'base' in c), None)
                col_flete = next((c for c in df_input.columns if 'flete' in c or 'envio' in c or 'envío' in c), None)

                if not col_sku or not col_costo:
                    st.error("❌ El archivo debe contener al menos las columnas 'SKU' y 'Costo'.")
                else:
                    if st.button("🚀 PROCESAR MATRIZ DE PRECIOS COMPLETA", use_container_width=True):
                        resultados = []

                        for idx, row in df_input.iterrows():
                            sku_val = str(row[col_sku])
                            
                            # Limpieza y conversión segura a float
                            raw_costo = str(row[col_costo]).replace('$', '').replace('.', '').replace(',', '.').strip()
                            costo_val = float(raw_costo) if raw_costo and raw_costo.lower() != 'nan' else 0.0

                            costo_flete_val = 0.0
                            if col_flete and pd.notnull(row[col_flete]):
                                raw_flete = str(row[col_flete]).replace('$', '').replace('.', '').replace(',', '.').strip()
                                if raw_flete and raw_flete.lower() != 'nan':
                                    costo_flete_val = float(raw_flete)

                            if costo_val > 0:
                                # 1. PVP 1 Cuota - Sin Envío Gratis
                                pvp_1c_sin_envio = calcular_pvp_recomendado_func(costo_val, margen_batch, tasa_1cuota_custom, "Mercado Envíos Tradicional (ME2)", peso_cat_batch, 0, 0, 0, 0)
                                
                                # 2. PVP 1 Cuota - Con Envío Gratis (Incorproando costo de flete)
                                pvp_1c_con_envio = calcular_pvp_recomendado_func(costo_val + costo_flete_val, margen_batch, tasa_1cuota_custom, "Mercado Envíos Tradicional (ME2)", peso_cat_batch, 0, 0, 0, 0)

                                # 3. PVP 3 Cuotas - Sin Envío Gratis
                                pvp_3c_sin_envio = calcular_pvp_recomendado_func(costo_val, margen_batch, tasa_3cuotas_custom, "Mercado Envíos Tradicional (ME2)", peso_cat_batch, 0, 0, 0, 0)

                                # 4. PVP 3 Cuotas - Con Envío Gratis
                                pvp_3c_con_envio = calcular_pvp_recomendado_func(costo_val + costo_flete_val, margen_batch, tasa_3cuotas_custom, "Mercado Envíos Tradicional (ME2)", peso_cat_batch, 0, 0, 0, 0)

                                resultados.append({
                                    "SKU": sku_val,
                                    "Costo Fábrica ($)": costo_val,
                                    "Flete Directo ($)": costo_flete_val,
                                    "PVP 1 Cuota (Sin Envío)": pvp_1c_sin_envio,
                                    "PVP 1 Cuota (Con Envío)": pvp_1c_con_envio,
                                    "PVP 3 Cuotas (Sin Envío)": pvp_3c_sin_envio,
                                    "PVP 3 Cuotas (Con Envío)": pvp_3c_con_envio
                                })

                        df_res = pd.DataFrame(resultados)
                        st.success("✅ ¡Procesamiento completado con éxito!")
                        st.dataframe(df_res, use_container_width=True)

                        # Generar archivo CSV de salida para descarga segura
                        csv_data = df_res.to_csv(index=False, sep=';').encode('utf-8')
                        
                        st.download_button(
                            label="📥 DESCARGAR REPORTES PROCESADOS (CSV)",
                            data=csv_data,
                            file_name=f"Matriz_Precios_NQ_v{V_NUMBER}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )

        except Exception as e:
            st.error(f"Error al procesar el archivo: {str(e)}")
    else:
        st.info("💡 Podés subir tu archivo CSV o Excel con columnas como: `SKU`, `Costo`, `Flete`")
