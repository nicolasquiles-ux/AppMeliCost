import streamlit as st

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Centro Estant | Sales Intelligence V15", layout="centered")

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

# Diccionario de análisis estratégico de categorías
DICT_CATEGORIAS = {
    "Muebles listos para armar (RTA)": {"tipo": "Estratégico / Volumen", "full": "Altamente Recomendado", "nota": "Alta rotación, bulto optimizado para Full. Competencia firme pero leal."},
    "Muebles pesados a medida / Armados": {"tipo": "Logística Compleja", "full": "No aplica (Solo ME1)", "nota": "Margen alto pero requiere flete especial. Nicho protegido de revendedores chicos."},
    "Bazar y Organización de Hogar": {"tipo": "Multirrubro de Alta Rotación", "full": "Obligatorio (Full)", "nota": "Ticket bajo/medio. Ideal para meter volumen y romper estacionalidad."},
    "Herramientas y Jardín": {"tipo": "Estacional / Técnico", "full": "Recomendado", "nota": "Márgenes estables. Muy interesante para compras mayoristas cerradas."},
    "Categoría General (Genérico / Trillado)": {"tipo": "Riesgo de Margen Quemado", "full": "Opcional", "nota": "Guerra de precios agresiva. Evaluar con slider de margen estricto."}
}

CLAVE_CORRECTA = "CENTRO_PRO_2026"

# --- CSS: DISEÑO MODERNO Y CONTROL DE COMPONENTES ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F8FAFC; }

    /* Encabezado */
    .header-app {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        color: white; padding: 20px; border-radius: 12px; margin-bottom: 20px;
        text-align: center; border-left: 6px solid #3B82F6;
    }
    .header-app h2 { margin: 0; font-weight: 900; letter-spacing: -1px; color: white !important; }
    .header-app p { margin: 5px 0 0 0; font-size: 0.9rem; color: #94A3B8; }

    /* Inputs estilizados */
    .stNumberInput input, .stSelectbox div, .stMultiSelect div {
        background-color: white !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        color: #1E293B !important;
    }

    /* Tarjetas de resultados */
    .dash-main {
        background-color: #0F172A; color: white; padding: 25px;
        border-radius: 12px; text-align: center;
        border-bottom: 5px solid #3B82F6; margin-top: 15px; margin-bottom: 15px;
    }
    .dash-main-inverse {
        background-color: #0F172A; color: white; padding: 25px;
        border-radius: 12px; text-align: center;
        border-bottom: 5px solid #10B981; margin-top: 15px; margin-bottom: 15px;
    }
    .dash-label { font-size: 0.85rem; text-transform: uppercase; letter-spacing: 2px; color: #94A3B8; font-weight: 600; }
    .dash-price { font-size: 3rem; font-weight: 900; color: #FFFFFF; margin: 8px 0; }
    .dash-margin { background: #1E293B; display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; color: #10B981; font-weight: bold; }
    
    /* Caja de Volumen */
    .vol-box {
        background-color: #FFFFFF; border: 1px solid #E2E8F0; padding: 20px;
        border-radius: 12px; text-align: center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-top: 10px;
    }
    
    /* Caja de Categoría */
    .cat-box {
        background-color: #EFF6FF; border: 1px solid #BFDBFE; padding: 15px;
        border-radius: 8px; margin-bottom: 15px;
    }

    /* Botones Controlados */
    .stButton button {
        background-color: #1E293B !important; color: white !important;
        border-radius: 8px !important; font-weight: bold !important;
        border: none !important; padding: 8px 16px !important;
    }
    .stButton button:hover { background-color: #334155 !important; }

    /* Botón WhatsApp de tamaño mediano controlado */
    .btn-wa-container { text-align: center; margin-top: 25px; }
    .btn-wa {
        background-color: #0F172A; color: white !important; padding: 10px 20px;
        border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 0.9rem;
        border: 1px solid #334155; display: inline-block;
    }
    .btn-wa:hover { background-color: #1E293B; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("<div style='text-align: center; padding: 40px 0;'><h2 style='color: #0F172A; font-weight:900;'>CONTROL DE GESTIÓN</h2></div>", unsafe_allow_html=True)
    with st.container():
        col_log1, col_log2, col_log3 = st.columns([1,2,1])
        with col_log2:
            clave_input = st.text_input("Acceso Protegido", type="password", placeholder="Clave de Operador")
            if st.button("INGRESAR AL SISTEMA", use_container_width=True):
                if clave_input == CLAVE_CORRECTA:
                    st.session_state.autenticado = True
                    st.rerun()
                else: st.error("Acceso Denegado")
    st.stop()

# =========================================================
# ENCABEZADO DE LA APLICACIÓN (SIEMPRE VISIBLE)
# =========================================================
st.markdown("""
    <div class="header-app">
        <h2>CENTRO ESTANT | Sales Intelligence</h2>
        <p>Consola de Gestión Comercial e Ingeniería de Costos para Mercado Libre</p>
    </div>
""", unsafe_allow_html=True)

# =========================================================
# SECCIÓN CRÍTICA FISCAL Y REPUTACIÓN (SIEMPRE VISIBLE ARRIBA)
# =========================================================
st.markdown("<h5 style='color: #0F172A; margin-bottom: 5px;'>📌 Configuración Impositiva y Cuenta</h5>", unsafe_allow_html=True)
col_top1, col_top2, col_top3 = st.columns(3)
with col_top1:
    tipo_iva = st.radio("Condición Fiscal:", ["Responsable Inscripto", "Monotributista"], horizontal=True)
with col_top2:
    iibb_perc = st.number_input("% Ingresos Brutos", value=3.5, step=0.5)
with col_top3:
    repu = st.selectbox("Reputación de Cuenta", ["Verde (50% desc)", "Amarilla (40% desc)", "Roja (0% desc)"])

st.markdown("---")

# Factores de impacto impositivo directo
bonif = 0.5 if "Verde" in repu else 0.6 if "Amarilla" in repu else 1.0
t_iva = 0.1735 if tipo_iva == "Responsable Inscripto" else 0.0
t_iibb = iibb_perc / 100

# --- PESTAÑAS PRINCIPALES DE OPERACIÓN ---
tab1, tab2 = st.tabs(["➡️ DIRECTO: CALCULAR PVP SUGERIDO", "⬅️ INVERSO: ANALIZAR COSTO REAL DE COMPRA"])

# =========================================================
# SOLAPA 1: PRECIO DE VENTA SUGERIDO (CON DESGLOSE)
# =========================================================
with tab1:
    st.markdown("<h4 style='color: #0F172A; font-weight:700;'>¿A cuánto tengo que vender para cubrir todo?</h4>", unsafe_allow_html=True)
    
    col_s1_1, col_s1_2 = st.columns(2)
    with col_s1_1:
        costo_in = st.number_input("COSTO UNITARIO DE COMPRA ($)", value=0.0, step=1000.0, key="c_directo")
        tipo_me = st.radio("SISTEMA DE ENVÍO", ["ME2 (Colecta/Full - Comisiona)", "ME1 (Muebles Pesados - No Comisiona)"], horizontal=True, key="me_directo")
    with col_s1_2:
        peso_cat = st.selectbox("PESO / AFORADO DEL PRODUCTO", list(TABLA_ME1.keys()), key="peso_directo")
        margen_obj = st.slider("% MARGEN NETO QUE QUERÉS LIMPIO", 5, 40, 15, key='margen_dir')

    col1, col2 = st.columns(2)
    with col1: comi_p = st.selectbox("% COMISIÓN PLATAFORMA", [10, 12, 14, 15, 16.5, 28], index=2, key='comi_dir')
    with col2: plan_f = st.selectbox("FINANCIACIÓN AL CLIENTE", list(FINANCIACION.keys()), index=3, key='finan_dir')

    # Cálculos base
    envio_v = TABLA_ME1[peso_cat] * bonif
    t_finan = FINANCIACION[plan_f] / 100
    t_comi = comi_p / 100
    t_margen = margen_obj / 100
    divisor = (1 - t_comi - t_margen - t_iibb - t_iva - t_finan)
    
    if "ME2" in tipo_me: pvp_sug = (costo_in + envio_v) / divisor if divisor > 0 else 0
    else: pvp_sug = (costo_in / divisor) + envio_v if divisor > 0 else 0

    st.markdown(f"""
        <div class="dash-main">
            <div class="dash-label">Precio de Venta al Público Sugerido</div>
            <div class="dash-price">${pvp_sug:,.0f}</div>
            <div class="dash-margin">Margen Neto Asegurado: {margen_obj}%</div>
        </div>
    """, unsafe_allow_html=True)

    # NUEVO DESGLOSE COMPLETO EN PESOS PARA SOLAPA 1
    if pvp_sug > 0:
        with st.expander("📥 VER DESGLOSE DETALLADO DE ESTE PVP", expanded=True):
            p_meli = pvp_sug * t_comi if "ME2" in tipo_me else (pvp_sug - envio_v) * t_comi
            p_finan = pvp_sug * t_finan
            p_iva = (pvp_sug - (pvp_sug / 1.21)) if tipo_iva == "Responsable Inscripto" else 0.0
            p_iibb = (pvp_sug / (1.21 if tipo_iva == "Responsable Inscripto" else 1)) * t_iibb
            p_margen = pvp_sug * t_margen
            
            st.write(f"• **Costo del Producto (Fábrica):** ${costo_in:,.2f}")
            st.write(f"• **Tu Ganancia Neta Limpia ({margen_obj}%):** ${p_margen:,.2f}")
            st.write(f"• **Comisión Mercado Libre ({comi_p}%):** ${p_meli:,.2f}")
            st.write(f"• **Costo de Financiación Escogido:** ${p_finan:,.2f}")
            st.write(f"• **Envío Neto de Correo:** ${envio_v:,.2f}")
            st.write(f"• **Impuestos Retenidos (IVA + IIBB):** ${(p_iva + p_iibb):,.2f}")

# =========================================================
# SOLAPA 2: CAMINO INVERSO CON ANÁLISIS DE CATEGORÍA
# =========================================================
with tab2:
    st.markdown("<h4 style='color: #0F172A; font-weight:700;'>¿Cuánto es lo MÁXIMO que puedo pagarle al proveedor?</h4>", unsafe_allow_html=True)
    
    # NUEVO EVALUADOR DE CATEGORÍA ANTES DE EMPEZAR
    cat_seleccionada = st.selectbox("📂 CATEGORÍA DE PRODUCTO A EVALUAR", list(DICT_CATEGORIAS.keys()))
    info_cat = DICT_CATEGORIAS[cat_seleccionada]
    
    st.markdown(f"""
        <div class="cat-box">
            <strong>Tipo de Nicho:</strong> {info_cat['tipo']} | <strong>Logística Full:</strong> {info_cat['full']}<br>
            <span style='font-size:0.85rem; color:#1E3A8A;'>💡 <em>{info_cat['nota']}</em></span>
        </div>
    """, unsafe_allow_html=True)

    col_in1, col_in2 = st.columns(2)
    with col_in1:
        pvp_target = st.number_input("PVP OBJETIVO DE LA COMPETENCIA ($)", value=0.0, step=1000.0, key="pvp_inv")
    with col_in2:
        margen_obj_inv = st.slider("% MARGEN NETO MINIMO REQUERIDO", 5, 40, 15, key='margen_inv')

    # Valores por defecto automáticos para evitar errores en renderizado
    ajuste_mercado = 1.0
    tasa_proveedor = 0.0
    ocultos_perc = 1.5

    dict_mercado = {"0% (Precio Estable)": 1.0, "5% (Prevenir Baja)": 0.95, "10% (Precio Inflado Competencia)": 0.90}
    dict_proveedor = {"Contado (0% Recargo)": 0.0, "30 días (+3% Recargo)": 0.03, "60 días (+6% Recargo)": 0.06}

    with st.expander("⚙️ PILARES AVANZADOS (HISTORIAL Y GASTOS OCULTOS)", expanded=False):
        opcion_mercado = st.selectbox("Fluctuación de Mercado / Competencia", list(dict_mercado.keys()), key="op_mercado")
        ajuste_mercado = dict_mercado[opcion_mercado]
        
        opcion_proveedor = st.selectbox("Condición de Pago a Fábrica", list(dict_proveedor.keys()), key="op_proveedor")
        tasa_proveedor = dict_proveedor[opcion_proveedor]
        
        ocultos_perc = st.slider("% Cobertura de Estructura (Roturas / Mermas)", 0.0, 5.0, 1.5, step=0.5, key="ocultos_slider")

    tipo_me_inv = st.radio("SISTEMA DE ENVÍO", ["ME2 (Colecta/Full - Comisiona)", "ME1 (Muebles Pesados - No Comisiona)"], horizontal=True, key="me_inv")
    peso_cat_inv = st.selectbox("PESO / AFORADO DEL PRODUCTO", list(TABLA_ME1.keys()), key="peso_inv")
    
    col3, col4 = st.columns(2)
    with col3: comi_p_inv = st.selectbox("% COMISIÓN PLATAFORMA", [10, 12, 14, 15, 16.5, 28], index=2, key='comi_inv')
    with col4: plan_f_inv = st.selectbox("FINANCIACIÓN AL CLIENTE", list(FINANCIACION.keys()), index=3, key='finan_inv')

    # --- MOTOR MATEMÁTICO INVERSO ---
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
            <div class="dash-label">Costo Máximo Admisible en Fábrica</div>
            <div class="dash-price" style="color: #10B981;">${max(0.0, costo_maximo):,.0f}</div>
            <div class="dash-margin">Asegurando Ganancia del {margen_obj_inv}%</div>
        </div>
    """, unsafe_allow_html=True)

    # PILAR DE PROYECCIÓN POR VOLUMEN Y COMPARATIVA REAL
    st.subheader("📊 Simulación de Lote y Retorno de Inversión")
    col_v1, col_v2 = st.columns([1, 2])
    with col_v1:
        q_mensual = st.number_input("Ventas proyectadas / mes", value=1, min_value=1, key="q_mes")
    with col_v2:
        costo_real_prov = st.number_input("Costo Real Cotizado por Fábrica ($)", value=0.0, step=1000.0, key="c_real_prov")

    if pvp_target > 0 and costo_real_prov > 0:
        inversion_stock = costo_real_prov * q_mensual
        ahorro_o_recargo = costo_maximo - costo_real_prov
        ganancia_un_real = margen_pesos_inv + (ahorro_o_recargo * (1 + tasa_proveedor))
        ganancia_total_mes = ganancia_un_real * q_mensual
        roi_real = (ganancia_total_mes / inversion_stock) * 100 if inversion_stock > 0 else 0
        
        st.markdown(f"""
        <div class="vol-box">
            <p style='margin:0; font-size:0.85rem; color:#64748B; text-transform:uppercase; letter-spacing:1px;'>Balance Mensual de Compra</p>
            <div style='display:flex; justify-content:space-around; margin-top:15px;'>
                <div>
                    <span style='font-size:0.8rem; color:#64748B;'>Capital a Invertir</span><br>
                    <strong style='font-size:1.3rem; color:#0F172A;'>${inversion_stock:,.0f}</strong>
                </div>
                <div>
                    <span style='font-size:0.8rem; color:#64748B;'>Ganancia Neta Total</span><br>
                    <strong style='font-size:1.3rem; color:#10B981;'>${ganancia_total_mes:,.0f}</strong>
                </div>
                <div>
                    <span style='font-size:0.8rem; color:#64748B;'>ROI del Lote</span><br>
                    <strong style='font-size:1.3rem; color:#3B82F6;'>{roi_real:.1f}%</strong>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if costo_real_prov <= costo_maximo:
            st.success(f"💪 Viable: Estás comprando por debajo del límite teórico.")
        else:
            st.error(f"⚠️ Alerta: Costo excesivo. La ganancia real caerá por debajo de tu objetivo neto.")

    with st.expander("📥 VER REPARTO COMPLETO DE LA COMPRA INVERSA"):
        st.write(f"• **PVP del Competidor (Base de cálculo):** ${pvp_ajustado:,.2f}")
        st.write(f"• **Retención de IVA e IIBB:** ${(imp_iva_inv + imp_iibb_inv):,.2f}")
        st.write(f"• **Margen Fijo Reservado:** ${margen_pesos_inv:,.2f}")
        st.write(f"• **Logística de Correo Unificada:** ${envio_real_inv:,.2f}")
        st.write(f"• **Comisiones por Venta:** ${c_meli_inv:,.2f}")
        st.write(f"• **Amortización de Roturas/Devoluciones:** ${costo_oculto_pesos:,.2f}")

# Botón técnico mediano y centrado
st.markdown("""
    <div class="btn-wa-container">
        <a href="https://wa.me/5491165808113" class="btn-wa">⚙️ SOPORTE TÉCNICO INTERNO</a>
    </div>
""", unsafe_allow_html=True)
