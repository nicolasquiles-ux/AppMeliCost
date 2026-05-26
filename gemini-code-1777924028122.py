import streamlit as st

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Centro Estant | Sales Intelligence V14.2", layout="centered")

# =========================================================
# DATOS MAESTROS ACTUALIZADOS VIGENTES 2026
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
        background-color: #1E293B; color: white; padding: 25px;
        border-radius: 12px; text-align: center;
        border-bottom: 5px solid #10B981; margin-bottom: 25px;
    }
    .dash-label { font-size: 0.9rem; text-transform: uppercase; letter-spacing: 2px; color: #94A3B8; }
    .dash-price { font-size: 3.2rem; font-weight: 900; color: #FFFFFF; margin: 10px 0; }
    .dash-margin { background: #0F172A; display: inline-block; padding: 5px 15px; border-radius: 20px; font-size: 0.9rem; color: #10B981; font-weight: bold; }
    
    .vol-box {
        background-color: #FFFFFF; border: 1px solid #E2E8F0; padding: 20px;
        border-radius: 12px; text-align: center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }

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

# --- SIDEBAR ---
with st.sidebar:
    st.title("Ajustes de Perfil")
    repu = st.selectbox("Reputación", ["Verde (50% desc)", "Amarilla (40% desc)", "Roja (0% desc)"])
    tipo_iva = st.radio("Condición Fiscal", ["Responsable Inscripto", "Monotributista"])
    iibb_perc = st.number_input("% IIBB", value=3.5)
    st.divider()
    if st.button("SALIR DEL SISTEMA"):
        st.session_state.autenticado = False
        st.rerun()

# --- PESTAÑAS ---
tab1, tab2 = st.tabs(["➡️ CALCULAR PVP SUGERIDO", "⬅️ ANALIZAR COSTO OBJETIVO INTELIGENTE"])

bonif = 0.5 if "Verde" in repu else 0.6 if "Amarilla" in repu else 1.0
t_iva = 0.1735 if tipo_iva == "Responsable Inscripto" else 0.0
t_iibb = iibb_perc / 100

# DICCIONARIOS DE PILARES (Declarados globalmente de forma segura)
dict_mercado = {"0% (Precio Estable)": 1.0, "5% (Prevenir Baja)": 0.95, "10% (Precio Inflado Competencia)": 0.90}
dict_proveedor = {"Contado (0% Recargo)": 0.0, "30 días (+3% Recargo)": 0.03, "60 días (+6% Recargo)": 0.06}

# =========================================================
# PESTAÑA 1: CAMINO DIRECTO
# =========================================================
with tab1:
    st.markdown("<h4 style='color: #0F172A;'>¿A cuánto tengo que vender?</h4>", unsafe_allow_html=True)
    costo_in = st.number_input("COSTO UNITARIO DE COMPRA ($)", value=0.0, step=1000.0, key="c_directo")
    tipo_me = st.radio("SISTEMA DE ENVÍO", ["ME2 (Colecta/Full - Comisiona)", "ME1 (Muebles Pesados - No Comisiona)"], horizontal=True, key="me_directo")
    peso_cat = st.selectbox("PESO / AFORADO", list(TABLA_ME1.keys()), key="peso_directo")
    
    col1, col2 = st.columns(2)
    with col1: comi_p = st.selectbox("% COMISIÓN MELI", [10, 12, 14, 15, 16.5, 28], index=2, key='comi_dir')
    with col2: plan_f = st.selectbox("PLAN DE CUOTAS", list(FINANCIACION.keys()), index=3, key='finan_dir')
    margen_obj = st.slider("% MARGEN NETO DESEADO", 5, 40, 15, key='margen_dir')

    envio_v = TABLA_ME1[peso_cat] * bonif
    t_finan = FINANCIACION[plan_f] / 100
    t_comi = comi_p / 100
    t_margen = margen_obj / 100
    divisor = (1 - t_comi - t_margen - t_iibb - t_iva - t_finan)
    
    if "ME2" in tipo_me: pvp_sug = (costo_in + envio_v) / divisor if divisor > 0 else 0
    else: pvp_sug = (costo_in / divisor) + envio_v if divisor > 0 else 0

    st.markdown(f"""
        <div class="dash-main">
            <div class="dash-label">Precio de Venta Sugerido</div>
            <div class="dash-price">${pvp_sug:,.0f}</div>
            <div style="color: #3B82F6; font-weight: bold;">OBJETIVO NETO: {margen_obj}%</div>
        </div>
    """, unsafe_allow_html=True)

# =========================================================
# PESTAÑA 2: CAMINO INVERSO (BLINDADO)
# =========================================================
with tab2:
    st.markdown("<h4 style='color: #0F172A;'>Evaluación Avanzada de Costo Máximo</h4>", unsafe_allow_html=True)
    
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        pvp_target = st.number_input("PVP OBJETIVO (MERCADO) ($)", value=0.0, step=1000.0, key="pvp_inv")
    with col_in2:
        margen_obj_inv = st.slider("% MARGEN NETO EXIGIDO", 5, 40, 15, key='margen_inv')

    # Inicialización de valores por defecto obligatorios antes de cualquier expander
    ajuste_mercado = 1.0
    tasa_proveedor = 0.0
    ocultos_perc = 1.5

    with st.expander("⚙️ AJUSTES DE PILARES (HISTORIAL, PLAZOS Y COSTOS OCULTOS)", expanded=False):
        st.markdown("**Pilar 1 & 2: Elasticidad del Mercado y Plazos del Proveedor**")
        
        opcion_mercado = st.selectbox("Descuento por Fluctuación de Mercado (Historial)", list(dict_mercado.keys()), key="op_mercado")
        ajuste_mercado = dict_mercado[opcion_mercado]
        
        opcion_proveedor = st.selectbox("Financiación del Proveedor (Plazo de pago)", list(dict_proveedor.keys()), key="op_proveedor")
        tasa_proveedor = dict_proveedor[opcion_proveedor]
        
        st.markdown("---")
        st.markdown("**Pilar 3: Costos Ocultos de Estructura**")
        ocultos_perc = st.slider("% Fondo de Cobertura (Roturas, Mermas y Devoluciones)", 0.0, 5.0, 1.5, step=0.5, key="ocultos_slider")

    tipo_me_inv = st.radio("SISTEMA DE ENVÍO", ["ME2 (Colecta/Full - Comisiona)", "ME1 (Muebles Pesados - No Comisiona)"], horizontal=True, key="me_inv")
    peso_cat_inv = st.selectbox("PESO / AFORADO", list(TABLA_ME1.keys()), key="peso_inv")
    
    col3, col4 = st.columns(2)
    with col3: comi_p_inv = st.selectbox("% COMISIÓN MELI", [10, 12, 14, 15, 16.5, 28], index=2, key='comi_inv')
    with col4: plan_f_inv = st.selectbox("PLAN DE CUOTAS", list(FINANCIACION.keys()), index=3, key='finan_inv')

    # --- ENCAPSULAMIENTO SEGURO DEL MOTOR MATEMÁTICO ---
    pvp_ajustado = float(pvp_target) * float(ajuste_mercado)
    
    envio_v_inv = TABLA_ME1[peso_cat_inv] * bonif
    fijo_inv = 3800.0 if pvp_ajustado < 33000 and pvp_ajustado > 0 else 0.0
    envio_real_inv = envio_v_inv if pvp_ajustado >= 33000 else 0.0

    t_finan_inv = FINANCIACION[plan_f_inv] / 100
    t_comi_inv = comi_p_inv / 100
    t_margen_inv = margen_obj_inv / 100

    c_fina_inv = pvp_ajustado * t_finan_inv
    imp_iva_inv = (pvp_ajustado - (pvp_ajustado / 1.21)) if tipo_iva == "Responsable Inscripto" else 0.0
    imp_iibb_inv = (pvp_ajustado / (1.21 if tipo_iva == "Responsable Inscripto" else 1)) * t_iibb
    margen_pesos_inv = pvp_ajustado * t_margen_inv
    costo_oculto_pesos = pvp_ajustado * (ocultos_perc / 100)

    if "ME2" in tipo_me_inv:
        c_meli_inv = pvp_ajustado * t_comi_inv
    else:
        base_comisionable_inv = pvp_ajustado - envio_real_inv
        c_meli_inv = max(0.0, base_comisionable_inv * t_comi_inv)

    costo_max_teorico = pvp_ajustado - (c_meli_inv + c_fina_inv + imp_iva_inv + imp_iibb_inv + envio_real_inv + fijo_inv + margen_pesos_inv + costo_oculto_pesos)
    costo_maximo = costo_max_teorico / (1.0 + float(tasa_proveedor))

    if pvp_target == 0: costo_maximo = 0

    st.markdown(f"""
        <div class="dash-main-inverse">
            <div class="dash-label">Costo Máximo de Compra Admitido</div>
            <div class="dash-price" style="color: #10B981;">${max(0.0, costo_maximo):,.0f}</div>
            <div class="dash-margin">CUIDANDO TU {margen_obj_inv}% NETO + {ocultos_perc}% COBERTURA</div>
        </div>
    """, unsafe_allow_html=True)

    # PILAR 4: VOLUMEN Y PROYECCIÓN DE NEGOCIO
    st.subheader("📊 Pilar de Volumen y Proyección Temporal")
    col_v1, col_v2 = st.columns([1, 2])
    with col_v1:
        q_mensual = st.number_input("Ventas estimadas / mes", value=1, min_value=1, key="q_mes")
    with col_v2:
        costo_real_prov = st.number_input("Costo Real de Fábrica Unitario ($)", value=0.0, step=1000.0, key="c_real_prov")

    if pvp_target > 0 and costo_real_prov > 0:
        inversion_stock = costo_real_prov * q_mensual
        ahorro_o_recargo = costo_maximo - costo_real_prov
        ganancia_un_real = margen_pesos_inv + (ahorro_o_recargo * (1 + tasa_proveedor))
        ganancia_total_mes = ganancia_un_real * q_mensual
        roi_real = (ganancia_total_mes / inversion_stock) * 100 if inversion_stock > 0 else 0
        
        st.markdown(f"""
        <div class="vol-box">
            <p style='margin:0; font-size:0.85rem; color:#64748B; text-transform:uppercase; letter-spacing:1px;'>Proyección Mensual Comercial</p>
            <div style='display:flex; justify-content:space-around; margin-top:15px;'>
                <div>
                    <span style='font-size:0.8rem; color:#64748B;'>Inversión en Stock</span><br>
                    <strong style='font-size:1.4rem; color:#0F172A;'>${inversion_stock:,.0f}</strong>
                </div>
                <div>
                    <span style='font-size:0.8rem; color:#64748B;'>Ganancia Neta Total</span><br>
                    <strong style='font-size:1.4rem; color:#10B981;'>${ganancia_total_mes:,.0f}</strong>
                </div>
                <div>
                    <span style='font-size:0.8rem; color:#64748B;'>Retorno (ROI)</span><br>
                    <strong style='font-size:1.4rem; color:#3B82F6;'>{roi_real:.1f}%</strong>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if costo_real_prov <= costo_maximo:
            st.success(f"💪 El costo real está dentro del límite. El excedente impositivo/comercial va directo a tu billetera.")
        else:
            st.error(f"⚠️ Alerta: Estás pagando por encima del costo máximo. Tu ROI y margen neto se verán reducidos.")

    with st.expander("📥 DESGLOSE COMPLETO POR UNIDAD AJUSTADA"):
        st.write(f"• **PVP Ajustado por Historial:** ${pvp_ajustado:,.2f}")
        st.write(f"• **Comisión Mercado Libre:** ${c_meli_inv:,.2f}")
        st.write(f"• **Costo Financiero (Cuotas):** ${c_fina_inv:,.2f}")
        st.write(f"• **Envío Neto Consolidado:** ${envio_real_inv:,.2f}")
        st.write(f"• **Impuestos Calculados (IVA+IIBB):** ${(imp_iva_inv + imp_iibb_inv):,.2f}")
        st.write(f"• **Fondo Oculto por Roturas ({ocultos_perc}%):** ${costo_oculto_pesos:,.2f}")
        if fijo_inv > 0: st.write(f"• **Costo Fijo Base (<$33k):** ${fijo_inv:,.2f}")

st.markdown('<a href="https://wa.me/5491165808113" class="btn-wa">CONSULTA TÉCNICA WHATSAPP</a>', unsafe_allow_html=True)
