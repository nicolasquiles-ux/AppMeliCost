import streamlit as st

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="MeLi Intelligence Pro", layout="centered")

# =========================================================
# TABLAS MAESTRAS
# =========================================================
LOGISTICA = {
    "📦 Estándar (Colecta/Full)": {
        "XS - Sobres (0.5kg)": 4800.0, "S - Pequeño (1-2kg)": 6200.0,
        "M - Mediano (5-10kg)": 10500.0, "L - Grande (15-25kg)": 17800.0,
        "XL - Muy Grande (30kg)": 23500.0
    },
    "🚚 Pesados (Centro Estant)": {
        "Nivel 1 (Escritorios)": 29000.0, "Nivel 2 (Bibliotecas)": 39500.0, "Nivel 3 (Placares)": 48000.0
    },
    "🛵 Flex / Propio": {
        "Local / Corto": 4800.0, "GBA / Extendido": 7500.0, "Especial": 9500.0
    }
}

FINANCIACION = {
    "1 Pago": 0.0, "3 Pagos (7%)": 7.0, "6 Pagos (10%)": 10.0,
    "9 Pagos (13.5%)": 13.5, "12 Pagos (16%)": 16.0
}

CLAVE_CORRECTA = "MELIPRO_2026"

# --- CSS REPARADO (Sin forzar fondo de app para evitar pantalla blanca) ---
st.markdown("""
    <style>
    /* Estilo de los inputs - Forzamos que el texto sea visible */
    .stNumberInput input { font-size: 1.5rem !important; font-weight: bold !important; }
    
    /* Tarjeta Principal de Precio Sugerido */
    .card-pvp {
        background-color: #1e1e1e !important; 
        color: #ffe600 !important; 
        padding: 20px;
        border-radius: 15px; 
        text-align: center; 
        margin-bottom: 20px;
        border: 2px solid #ffe600;
    }
    .price-xl { font-size: 3rem; font-weight: 900; color: #ffe600 !important; margin: 5px 0; }
    
    /* Bloques de Datos en el Desglose - USAMOS COLORES NEUTROS */
    .data-block {
        background-color: rgba(128, 128, 128, 0.1); 
        padding: 12px; 
        border-radius: 10px;
        border: 1px solid #888; 
        margin-bottom: 8px; 
        font-size: 1.1rem;
    }
    
    .btn-whatsapp {
        background-color: #25d366; 
        color: white !important; 
        padding: 15px;
        border-radius: 10px; 
        text-align: center; 
        text-decoration: none;
        display: block; 
        font-weight: bold; 
        margin: 15px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SISTEMA DE LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🚀 MeLi QuickCheck")
    st.subheader("🔐 Acceso")
    clave_input = st.text_input("Clave Pro", type="password")
    if st.button("ENTRAR", use_container_width=True):
        if clave_input == CLAVE_CORRECTA:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Clave Incorrecta")
    st.markdown('<a href="https://wa.me/5491165808113" class="btn-whatsapp">💬 Pedir Clave</a>', unsafe_allow_html=True)
    st.stop()

# --- APP PRINCIPAL ---
st.title("📊 Calculador")

with st.expander("⚙️ Ajustes Fiscales"):
    repu = st.selectbox("Reputación", ["Verde (50% desc)", "Amarilla (40% desc)", "Roja (0% desc)"])
    tipo_iva = st.radio("IVA", ["Responsable Inscripto", "Monotributista"])
    iibb_perc = st.number_input("% IIBB", value=3.5)
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

# Inputs Verticales
costo_in = st.number_input("COSTO COMPRA ($)", value=0.0, step=1000.0)
cat_log = st.selectbox("ENVÍO", list(LOGISTICA.keys()))
tipo_bulto = st.selectbox("TAMAÑO", list(LOGISTICA[cat_log].keys()))
comi_val = st.selectbox("% COMISIÓN", [10, 12, 14, 15, 16.5, 28], index=3)
finan_txt = st.selectbox("CUOTAS", list(FINANCIACION.keys()))
margen_target = st.slider("% MARGEN", 5, 40, 15)

# Lógica
bonif_log = 0.5 if "Verde" in repu else 0.6 if "Amarilla" in repu else 1.0
costo_envio = LOGISTICA[cat_log][tipo_bulto] * (1 if "Flex" in cat_log else bonif_log)
t_iva = 0.1735 if tipo_iva == "Responsable Inscripto" else 0.0
t_iibb = iibb_perc / 100
t_finan = FINANCIACION[finan_txt] / 100

divisor = (1 - (comi_val/100) - (margen_target/100) - t_iibb - t_iva - t_finan)
pvp_sug = (costo_in + costo_envio) / divisor if divisor > 0 else 0

st.markdown(f"""
    <div class="card-pvp">
        <div>PRECIO VENTA SUGERIDO</div>
        <div class="price-xl">${pvp_sug:,.0f}</div>
        <div style="color:#fff">Margen: {margen_target}%</div>
    </div>
""", unsafe_allow_html=True)

st.divider()
p_comp = st.number_input("PRECIO COMPETENCIA ($)", value=float(round(pvp_sug, 0)))

# Lógica 2026: > $33.000 envío gratis
e_real = costo_envio if p_comp >= 33000 else 0.0
fijo = 3800.0 if p_comp < 33000 else 0.0

c_meli = p_comp * (comi_val/100)
c_finan = p_comp * t_finan
imp_iva = (p_comp - (p_comp / 1.21)) if tipo_iva == "Responsable Inscripto" else 0.0
imp_iibb = (p_comp / (1.21 if tipo_iva == "Responsable Inscripto" else 1)) * t_iibb
neta_real = p_comp - (c_meli + c_finan + imp_iva + imp_iibb + e_real + fijo) - costo_in
margen_real = (neta_real / p_comp) if p_comp > 0 else 0

if neta_real < 0:
    st.error(f"🛑 PERDIDA: $ {neta_real:,.0f}")
else:
    st.success(f"✅ MARGEN: {margen_real:.1%}")

with st.expander("📊 DETALLE DE COSTOS"):
    st.write(f"• **Envío:** ${e_real:,.2f}")
    st.write(f"• **Comisión:** ${c_meli:,.2f}")
    st.write(f"• **Financiación:** ${c_finan:,.2f}")
    st.write(f"• **IVA:** ${imp_iva:,.2f}")
    st.write(f"• **IIBB:** ${imp_iibb:,.2f}")
    st.write(f"• **Fijo:** ${fijo:,.2f}")
    st.info(f"GANANCIA FINAL: $ {neta_real:,.2f}")

st.markdown('<a href="https://wa.me/5491165808113" class="btn-whatsapp">💬 Consultar WhatsApp</a>', unsafe_allow_html=True)
