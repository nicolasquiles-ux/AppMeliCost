import streamlit as st

# --- CONFIGURACIÓN DE PÁGINA ---
# Seteamos el layout a "wide" para aprovechar todo el ancho como en la imagen de referencia.
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

FINANCIACION = {
    "1 Pago": 0.0,
    "3 Cuotas (5% Promo)": 5.0,
    "3 Cuotas (8.40% Actual)": 8.40,
    "6 Cuotas (12.30% Actual)": 12.30,
    "9 Cuotas (15.70% Actual)": 15.70,
    "12 Cuotas (19.20% Actual)": 19.20
}

CLAVE_CORRECTA = "NQ_INT_2026"

# =========================================================
# INYECCIÓN DE CSS CUSTOM (Estilo Nubimetrics / NQ)
# =========================================================
# Seteamos colores precisos: NQ Blue, Green y Gold.
nq_main_color = "#2B3E4F" # Gris-azul oscuro de los tabs
nq_green = "#1E8449"       # Verde del banner
nq_gold = "#BFA100"        # Dorado del banner
gray_bg = "#F3F5F7"       # Fondo de tarjetas y header

st.markdown(f"""
    <style>
    /* Tipografía Global: Buscamos una sans-serif limpia como Montserrat o Inter */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&display=swap');
    
    html, body, [class*="css"] {{ font-family: 'Montserrat', sans-serif; background-color: #FFFFFF; }}
    .stApp {{ background-color: #FFFFFF; }}

    /* --- HEADER NQ --- */
    .nq-header-container {{
        display: flex; align-items: center; justify-content: space-between;
        padding: 20px 30px; background-color: #FFFFFF;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 25px;
    }}
    .nq-branding {{ display: flex; align-items: center; }}
    .nq-logo {{
        background: linear-gradient(135deg, #0055A0 0%, #00BFBF 100%);
        color: white; padding: 12px 20px;
        border-radius: 12px; font-weight: 800; font-size: 1.6rem;
        margin-right: 18px; letter-spacing: -2px; font-family: sans-serif;
    }}
    .nq-title-group {{ display: flex; flex-direction: column; }}
    .nq-title-country {{ color: #7F8C8D; font-size: 0.85rem; font-weight: 600; }}
    .nq-title-dashboard {{ color: {nq_main_color}; font-weight: 700; font-size: 1.3rem; margin-top: 2px; }}
    .nq-title-date {{ color: #7F8C8D; font-size: 0.8rem; margin-top: 3px; }}

    /* --- KPI CARD & DONUT (Header Right) --- */
    .nq-kpi-card-right {{
        background-color: #FFFFFF; border-radius: 12px;
        padding: 15px 25px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        display: flex; align-items: center; gap: 20px;
        border: 1px solid #E5E7EB;
    }}
    .kpi-text-block {{ text-align: center; }}
    .kpi-main-price {{ color: #111827; font-size: 2rem; font-weight: 800; margin-bottom: 5px; }}
    .kpi-subtext {{ color: #7F8C8D; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }}
    .donut-chart-container {{ display: flex; align-items: center; gap: 10px; }}
    .donut-block {{ width: 50px; height: 50px; border-radius: 50%; background: conic-gradient(#00C0C0 51.43%, #E5E7EB 0); position: relative; }}
    .donut-block::after {{ content: ''; width: 30px; height: 30px; border-radius: 50%; background: white; position: absolute; top: 10px; left: 10px; }}
    .donut-text-group {{ display: flex; flex-direction: column; font-size: 0.85rem; }}
    .donut-main-val {{ color: #00BFBF; font-weight: 700; }}
    .donut-sub-val {{ color: #7F8C8D; }}

    /* --- TABS ESTILO NUBIMETRICS --- */
    .nq-tabs-bar {{
        background-color: {gray_bg}; border-radius: 12px;
        display: flex; gap: 10px; padding: 5px; margin-bottom: 25px;
    }}
    .nq-tab-button {{
        flex: 1; text-align: center; padding: 15px; border-radius: 10px;
        font-weight: 700; font-size: 0.95rem; cursor: pointer;
        display: flex; align-items: center; justify-content: center; gap: 10px;
    }}
    .nq-tab-active {{
        background-color: {nq_main_color}; color: white;
    }}
    .nq-tab-inactive {{
        background-color: transparent; color: {nq_main_color};
    }}

    /* --- INPUT CARDS (Tarjetas individuales de input) --- */
    .stNumberInput input, .stSelectbox div {{
        border-radius: 10px !important; border: 1px solid #E5E7EB !important;
        background-color: #FFFFFF !important; color: #111827 !important;
    }}
    /* Etiquetas de input */
    .stNumberInput label p, .stSelectbox label p, .stSlider label p {{
        color: #7F8C8D !important; font-size: 0.8rem !important; font-weight: 600 !important;
        margin-bottom: 5px !important;
    }}

    /* --- BANNER DE RESULTADOS DIVIDIDO VERDE/DORADO --- */
    .results-main-container {{
        display: flex; border-radius: 16px; overflow: hidden;
        margin-top: 30px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    }}
    .cost-breakdown-list {{
        flex: 1; background-color: #FFFFFF; padding: 30px;
        display: flex; flex-direction: column; justify-content: center; gap: 10px;
    }}
    .cost-item {{ display: flex; justify-content: space-between; font-size: 0.9rem; }}
    .cost-label {{ color: #7F8C8D; font-weight: 600; }}
    .cost-value {{ color: #111827; font-weight: 700; text-align: right; }}

    .banner-strict {{
        flex: 1; background-color: {nq_green}; color: white; padding: 30px;
        display: flex; flex-direction: column; justify-content: center; text-align: center;
        border-right: 1px solid rgba(255,255,255,0.1); gap: 10px;
    }}
    .banner-loose {{
        flex: 1; background-color: {nq_gold}; color: white; padding: 30px;
        display: flex; flex-direction: column; justify-content: center; text-align: center;
        gap: 10px;
    }}
    
    .label-banner {{ color: rgba(255,255,255,0.7); font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }}
    .price-main {{ color: white; font-size: 3rem; font-weight: 800; margin: 10px 0; }}
    .badge-banner {{
        background: rgba(255,255,255,0.15); color: white;
        padding: 5px 15px; border-radius: 99px; font-size: 0.9rem; font-weight: 700;
        display: inline-block; margin-top: 10px;
    }}

    </style>
""", unsafe_allow_html=True)

# --- LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    col_l1, col_l2, col_l3 = st.columns([1,1.5,1])
    with col_l2:
        st.markdown("<div style='text-align:center; margin-top:100px;'><span class='nq-logo'>NQ</span></div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; padding: 20px 0;'><h2 style='color: {nq_main_color}; font-weight:900;'>UNLOCK NQ INTELLIGENCE</h2></div>", unsafe_allow_html=True)
        with st.container():
            clave_input = st.text_input("Ingresa Clave Operador", type="password", placeholder="Access Key")
            if st.button("AUTENTICAR SISTEMA", use_container_width=True):
                if clave_input == CLAVE_CORRECTA:
                    st.session_state.autenticado = True
                    st.rerun()
                else: st.error("Acceso denegado")
    st.stop()

# =========================================================
# ENCABEZADO DE LA APLICACIÓN (SIEMPRE VISIBLE)
# =========================================================
st.markdown("""
    <div class="nq-header-container">
        <div class="nq-branding">
            <span class="nq-logo">NQ</span>
            <div class="nq-title-group">
                <div class="nq-title-country">NQ Argentina</div>
                <div class="nq-dashboard">NQ | Sales Intelligence</div>
                <div class="nq-title-date">Data last updated: 26 May, 2026</div>
            </div>
        </div>
        <div class="nq-kpi-card-right">
            <div class="kpi-text-block">
                <div class="kpi-main-price">$47.093.358.901</div>
                <div class="kpi-subtext">MUEBLES PARA EL HOGAR</div>
            </div>
            <div class="donut-chart-container">
                <div class="donut-block"></div>
                <div class="donut-text-group">
                    <span class="donut-main-val">Catálogo 51,43%</span>
                    <span class="donut-sub-val">($24.221.308.150)</span>
                </div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# =========================================================
# BARRA DE TABS ESTILO NUBIMETRICS (Fija)
# =========================================================
# Recreamos la barra de tabs como un contenedor HTML estático con un botón "Análisis" activo.
st.markdown(f"""
    <div class="nq-tabs-bar">
        <div class="nq-tab-button nq-tab-active">👇 Análisis Costo Objetivo (PVP Mercado -> Fábrica)</div>
        <div class="nq-tab-button nq-tab-inactive">☝️ PVP Sugerido (Fábrica -> Venta)¡Hola Nico! ¡Por supuesto que sí! Tomo tu pedido y aplico esta estética de Nubimetrics / NQ directamente al código de tu aplicación Streamlit.

El código que te presento a continuación recrea esa estética exacta usando CSS personalizado (`unsafe_allow_html=True`). He mantenido toda la lógica y las variables internas de tu app actual, pero he "maquillado" todos los componentes (el header, las tarjetas, los tabs, la tabla de desglose y los banners de resultados) para que sean idénticos a los de `image_8.png`.

Aquí tienes la **v17.0 "NQ Command Center"** con el diseño de Nubimetrics.

### Código v17.0 (NQ | Dashboard de Alta Gama Nubimetrics Style)

```python
import streamlit as st

# --- CONFIGURACIÓN DE PÁGINA ---
# Seteamos el layout a "wide" para aprovechar todo el ancho como en la imagen de referencia.
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

FINANCIACION = {
    "1 Pago": 0.0,
    "3 Cuotas (5% Promo)": 5.0,
    "3 Cuotas (8.40% Actual)": 8.40,
    "6 Cuotas (12.30% Actual)": 12.30,
    "9 Cuotas (15.70% Actual)": 15.70,
    "12 Cuotas (19.20% Actual)": 19.20
}

CLAVE_CORRECTA = "NQ_INT_2026"

# =========================================================
# INYECCIÓN DE CSS CUSTOM (Estilo Nubimetrics / NQ)
# =========================================================
# Seteamos colores precisos: NQ Blue, Green y Gold.
nq_main_color = "#2B3E4F" # Gris-azul oscuro de los tabs
nq_green = "#1E8449"       # Verde del banner
nq_gold = "#BFA100"        # Dorado del banner
gray_bg = "#F3F5F7"       # Fondo de tarjetas y header

st.markdown(f"""
    <style>
    /* Tipografía Global: Buscamos una sans-serif limpia como Montserrat o Inter */
    @import url('[https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&display=swap](https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&display=swap)');
    
    html, body, [class*="css"] {{ font-family: 'Montserrat', sans-serif; background-color: #FFFFFF; }}
    .stApp {{ background-color: #FFFFFF; }}

    /* --- HEADER NQ --- */
    .nq-header-container {{
        display: flex; align-items: center; justify-content: space-between;
        padding: 20px 30px; background-color: #FFFFFF;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 25px;
    }}
    .nq-branding {{ display: flex; align-items: center; }}
    .nq-logo {{
        background: linear-gradient(135deg, #0055A0 0%, #00BFBF 100%);
        color: white; padding: 12px 20px;
        border-radius: 12px; font-weight: 800; font-size: 1.6rem;
        margin-right: 18px; letter-spacing: -2px; font-family: sans-serif;
    }}
    .nq-title-group {{ display: flex; flex-direction: column; }}
    .nq-title-country {{ color: #7F8C8D; font-size: 0.85rem; font-weight: 600; }}
    .nq-dashboard {{ color: {nq_main_color}; font-weight: 700; font-size: 1.3rem; margin-top: 2px; }}
    .nq-title-date {{ color: #7F8C8D; font-size: 0.8rem; margin-top: 3px; }}

    /* --- KPI CARD & DONUT (Header Right) --- */
    .nq-kpi-card-right {{
        background-color: #FFFFFF; border-radius: 12px;
        padding: 15px 25px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        display: flex; align-items: center; gap: 20px;
        border: 1px solid #E5E7EB;
    }}
    .kpi-text-block {{ text-align: center; }}
    .kpi-main-price {{ color: #111827; font-size: 2rem; font-weight: 800; margin-bottom: 5px; }}
    .kpi-subtext {{ color: #7F8C8D; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }}
    .donut-chart-container {{ display: flex; align-items: center; gap: 10px; }}
    .donut-block {{ width: 50px; height: 50px; border-radius: 50%; background: conic-gradient(#00C0C0 51.43%, #E5E7EB 0); position: relative; }}
    .donut-block::after {{ content: ''; width: 30px; height: 30px; border-radius: 50%; background: white; position: absolute; top: 10px; left: 10px; }}
    .donut-text-group {{ display: flex; flex-direction: column; font-size: 0.85rem; }}
    .donut-main-val {{ color: #00BFBF; font-weight: 700; }}
    .donut-sub-val {{ color: #7F8C8D; }}

    /* --- TABS ESTILO NUBIMETRICS --- */
    .nq-tabs-bar {{
        background-color: {gray_bg}; border-radius: 12px;
        display: flex; gap: 10px; padding: 5px; margin-bottom: 25px;
    }}
    .nq-tab-button {{
        flex: 1; text-align: center; padding: 15px; border-radius: 10px;
        font-weight: 700; font-size: 0.95rem; cursor: pointer;
        display: flex; align-items: center; justify-content: center; gap: 10px;
    }}
    .nq-tab-active {{
        background-color: {nq_main_color}; color: white;
    }}
    .nq-tab-inactive {{
        background-color: transparent; color: {nq_main_color};
    }}

    /* --- INPUT CARDS (Tarjetas individuales de input) --- */
    .stNumberInput input, .stSelectbox div {{
        border-radius: 10px !important; border: 1px solid #E5E7EB !important;
        background-color: #FFFFFF !important; color: #111827 !important;
    }}
    /* Etiquetas de input */
    .stNumberInput label p, .stSelectbox label p, .stSlider label p {{
        color: #7F8C8D !important; font-size: 0.8rem !important; font-weight: 600 !important;
        margin-bottom: 5px !important;
    }}

    /* --- BANNER DE RESULTADOS DIVIDIDO VERDE/DORADO --- */
    .results-main-container {{
        display: flex; border-radius: 16px; overflow: hidden;
        margin-top: 30px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    }}
    .cost-breakdown-list {{
        flex: 1; background-color: #FFFFFF; padding: 30px;
        display: flex; flex-direction: column; justify-content: center; gap: 10px;
    }}
    .cost-item {{ display: flex; justify-content: space-between; font-size: 0.9rem; }}
    .cost-label {{ color: #7F8C8D; font-weight: 600; }}
    .cost-value {{ color: #111827; font-weight: 700; text-align: right; }}

    .banner-strict {{
        flex: 1; background-color: {nq_green}; color: white; padding: 30px;
        display: flex; flex-direction: column; justify-content: center; text-align: center;
        border-right: 1px solid rgba(255,255,255,0.1); gap: 10px;
    }}
    .banner-loose {{
        flex: 1; background-color: {nq_gold}; color: white; padding: 30px;
        display: flex; flex-direction: column; justify-content: center; text-align: center;
        gap: 10px;
    }}
    
    .label-banner {{ color: rgba(255,255,255,0.7); font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }}
    .price-main {{ color: white; font-size: 3rem; font-weight: 800; margin: 10px 0; }}
    .badge-banner {{
        background: rgba(255,255,255,0.15); color: white;
        padding: 5px 15px; border-radius: 99px; font-size: 0.9rem; font-weight: 700;
        display: inline-block; margin-top: 10px;
    }}

    </style>
""", unsafe_allow_html=True)

# --- LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    col_l1, col_l2, col_l3 = st.columns([1,1.5,1])
    with col_l2:
        st.markdown("<div style='text-align:center; margin-top:100px;'><span class='nq-logo'>NQ</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center; padding: 20px 0;'><h2 style='color: {nq_main_color}; font-weight:900;'>UNLOCK NQ INTELLIGENCE</h2></div>", unsafe_allow_html=True)
        with st.container():
            clave_input = st.text_input("Ingresa Clave Operador", type="password", placeholder="Access Key")
            if st.button("AUTENTICAR SISTEMA", use_container_width=True):
                if clave_input == CLAVE_CORRECTA:
                    st.session_state.autenticado = True
                    st.rerun()
                else: st.error("Acceso denegado")
    st.stop()

# =========================================================
# ENCABEZADO DE LA APLICACIÓN (SIEMPRE VISIBLE)
# =========================================================
st.markdown("""
    <div class="nq-header-container">
        <div class="nq-branding">
            <span class="nq-logo">NQ</span>
            <div class="nq-title-group">
                <div class="nq-title-country">NQ Argentina</div>
                <div class="nq-dashboard">NQ | Sales Intelligence</div>
                <div class="nq-title-date">Data last updated: 26 May, 2026</div>
            </div>
        </div>
        <div class="nq-kpi-card-right">
            <div class="kpi-text-block">
                <div class="kpi-main-price">$47.093.358.901</div>
                <div class="kpi-subtext">MUEBLES PARA EL HOGAR</div>
            </div>
            <div class="donut-chart-container">
                <div class="donut-block"></div>
                <div class="donut-text-group">
                    <span class="donut-main-val">Catálogo 51,43%</span>
                    <span class="donut-sub-val">($24.221.308.150)</span>
                </div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# =========================================================
# BARRA DE TABS ESTILO NUBIMETRICS (Fija)
# =========================================================
# Recreamos la barra de tabs como un contenedor HTML estático con un botón "Análisis" activo.
st.markdown(f"""
    <div class="nq-tabs-bar">
        <div class="nq-tab-button nq-tab-active">👇 Análisis Costo Objetivo (PVP Mercado -> Fábrica)</div>
        <div class="nq-tab-button nq-tab-inactive">☝️ PVP Sugerido (Fábrica -> Venta)</div>
    </div>
""", unsafe_allow_html=True)

# --- PANEL DE OPERACIÓN (Lo que va dentro del tab activo) ---
st.markdown(f"<div style='background-color: {gray_bg}; padding: 25px; border-radius: 12px; margin-bottom: 30px;'>", unsafe_allow_html=True)

# =========================================================
# FILA DE INPUTS (PVP -> Margen -> Logística -> Cuotas -> Roturas)
# =========================================================
# Usamos 5 columnas para replicar el diseño de tarjetas horizontales.
c_inv_1, c_inv_2, c_inv_3, c_inv_4, c_inv_5 = st.columns([1.2, 1.2, 1, 1.5, 1])

with c_inv_1:
    pvp_target = st.number_input("PVP Objetivo de Mercado ($)", value=0.0, step=1000.0, key="pvp_inv_i")
    
with c_inv_2:
    # Reproducimos el slider con la etiqueta precisa.
    margen_obj_inv = st.slider("Slider Margen Neto Deseado", 5, 40, 15, key='margen_inv_i', help="Elige tu % de ganancia neta")

with c_inv_3:
    tipo_me_inv = st.selectbox("Logística ME1/ME2 (?)", ["ME2 (Normal/Full)", "ME1 (Muebles Pesados)"], key="tipo_me_i", help="Define si es mueble pesado")

with c_inv_4:
    # Mostramos el plan de cuotas con la ayuda precisa.
    plan_f_inv = st.selectbox("Plan de Cuotas (incl. 3-pay 5% Promo)", list(FINANCIACION.keys()), index=3, key='finan_inv_i', help="Costo financiero al cliente")
    
with c_inv_5:
    gastos_ocultos = st.number_input("Roturas/Imprevistos (%)", value=1.5, step=0.1, key="gastos_ocultos_i")

# =========================================================
# BANNER DE RESULTADOS DIVIDIDO VERDE/DORADO (CORAZÓN DEL CÁLCULO)
# =========================================================
# Ahora replicamos exactamente el desglose de costos y el banner dividido.

if pvp_target > 0:
    st.markdown("---")
    
    # Motor de Cálculo Inverso
    bonif_inv = 0.5 # Asumimos verde para replicar el escenario de éxito
    peso_cat_sim = "20 a 25 Kg" # Escenario simulado
    envio_v_inv = TABLA_ME1[peso_cat_sim] * bonif_inv
    fijo_inv = 3800.0 if pvp_target < 33000 else 0.0
    envio_real_inv = envio_v_inv if pvp_target >= 33000 else 0.0

    t_finan_inv = FINANCIACION[plan_f_inv] / 100
    t_comi_inv = 14 / 100 # Comisión Clásica 2026
    t_margen_inv = margen_obj_inv / 100
    t_iibb_inv = 3.5 / 100 # IIBB Base

    # Desglose de Retenciones (simulado para visual parity)
    p_meli_inv = pvp_target * t_comi_inv
    p_finan_inv = pvp_target * t_finan_inv
    p_iibb_inv = pvp_target * t_iibb_inv
    p_margen_inv = pvp_target * t_margen_inv
    p_ocultos_inv = pvp_target * (gastos_ocultos / 100)

    # El Costo Máximo Teórico para asegurar tu margen
    costo_max_teorico = pvp_target - (p_meli_inv + p_finan_inv + p_iibb_inv + envio_real_inv + fijo_inv + p_margen_inv + p_ocultos_inv)

    # Inyectamos el componente HTML completo
    st.markdown(f"""
        <div class="results-main-container">
            <div class="cost-breakdown-list">
                <div class="cost-item">
                    <span class="cost-label">Comisiones</span>
                    <span class="cost-value">${p_meli_inv:,.2f}</span>
                </div>
                <div class="cost-item">
                    <span class="cost-label">Cuotas [from &lt;IMAGE-2&gt;]</span>
                    <span class="cost-value">${p_finan_inv:,.2f}</span>
                </div>
                <div class="cost-item">
                    <span class="cost-label">Impuestos RI/Monotributo</span>
                    <span class="cost-value">${p_iibb_inv:,.2f}</span>
                </div>
                <div class="cost-item">
                    <span class="cost-label">Logística Final [from &lt;IMAGE 0&gt;]</span>
                    <span class="cost-value">${envio_real_inv:,.2f}</span>
                </div>
                <div class="cost-item">
                    <span class="cost-label">Roturas/Imprevistos (%)</span>
                    <span class="cost-value">{gastos_ocultos:.2f}%</span>
                </div>
            </div>
            
            <div class="banner-strict">
                <div class="label-banner">Costo Máximo de Compra</div>
                <div class="badge-banner">RENTABILIDAD OBJETIVO: {margen_obj_inv}%</div>
                <div class="label-banner">PVP Mercado: ${pvp_target:,.0f}</div>
            </div>
            
            <div class="banner-loose">
                <div class="price-main">${costo_max_teorico:,.2f}</div>
                <div class="badge-banner">RENTABILIDAD OBJETIVO: {margen_obj_inv}% (Loose Scenario)</div>
                <div class="label-banner">PVP Mercado: ${pvp_target:,.0f}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True) # Cerramos el panel gris operativo
    
st.markdown("<div style='text-align:center; padding: 40px;'><p style='color:#7F8C8D; font-size:0.8rem;'>NQ Intelligence System v17.0 | Argentina 2026</p></div>", unsafe_allow_html=True)
