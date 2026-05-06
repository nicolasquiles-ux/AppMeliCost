import streamlit as st
import pandas as pd

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="MeLi QuickCheck Pro", layout="centered")

# =========================================================
# TABLAS MAESTRAS (Ajustadas a Mayo 2026)
# =========================================================
LOGISTICA_UNIV = {
    "📦 Estándar (Colecta/Full)": {
        "Sobres / XS (0.5kg)": 4800.0,
        "Pequeño / S (1-2kg)": 6200.0,
        "Mediano / M (5-10kg)": 10500.0,
        "Grande / L (15-25kg)": 17800.0,
        "Muy Grande / XL (30kg)": 23500.0
    },
    "🚚 Especiales (Muebles/Pesados)": {
        "Bulto Pesado Nivel 1": 29000.0,
        "Bulto Pesado Nivel 2": 39500.0,
        "Bulto Pesado Nivel 3": 48000.0
    },
    "🛵 Rápido (Flex / Propio)": {
        "Rango Local": 4800.0,
        "Rango Extendido": 7500.0,
        "Rango Especial": 9200.0
    }
}

FINANCIACION = {
    "1 Pago": 0.0, "3 Pagos (7%)": 7, 
    "6 Pagos (10%)": 10, "9 Pagos (13.5%)": 13.5, "12 Pagos (16%)": 16
}

CLAVE_CORRECTA = "MELIPRO_2026"

# --- ESTILOS ---
st.markdown("""
    <style>
    .stApp { background-color: #f7f9fb; }
    .main-card {
        background-color: #000; color: #ffe600; padding: 25px;
        border-radius: 20px; text-align: center; margin-bottom: 20px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    .big-price { font-size: 4rem; font-weight: 900; line-height: 1; margin: 10px 0; }
    .stNumberInput input { font-size: 1.6rem !important; font-weight: bold !important; color: #1e1e1e !important; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("👤 Configuración")
    pass_input = st.text_input("Clave Pro", type="password")
    if pass_input != CLAVE_CORRECTA:
        st.error("Clave Incorrecta")
        st.stop()
    
    st.success("Acceso Concedido")
    st.divider()
    repu = st.selectbox("Tu Reputación", ["Verde (50% desc)", "Amarilla (40% desc)", "Roja (0% desc)"])
    cond_iva = st.radio("Tu IVA", ["Responsable Inscripto", "Monotributista"])
    iibb_tax = st.number_input("% IIBB", value=3.5)

# --- APP PRINCIPAL ---
st.title("🚀 MeLi QuickCheck")
st.caption("Evaluación de rentabilidad instantánea")

# SECCIÓN 1: COSTO BASE
costo_compra = st.number_input("¿Cuánto te costó el producto? ($)", value=0.0, step=500.0)

# SECCIÓN 2: LOGÍSTICA RÁPIDA
col_a, col_b = st.columns(2)
with col_a:
    tipo_envio = st.selectbox("Tipo de Envío", list(LOGISTICA_UNIV.keys()))
with col_b:
    tamanio = st.selectbox("Tamaño del Bulto", list(LOGISTICA_UNIV[tipo_envio].keys()))

# Cálculo de envío con descuento
costo_envio_lista = LOGISTICA_UNIV[tipo_envio][tamanio]
bonif = 0.5 if "Verde" in repu else 0.6 if "Amarilla" in repu else 1.0
envio_final = costo_envio_lista * (1 if "Flex" in tipo_envio else bonif)

# SECCIÓN 3: COMISIÓN Y CUOTAS
col_c, col_d = st.columns(2)
with col_c:
    comi_meli = st.selectbox("% Comisión MeLi", [10, 12, 14, 15, 16.5, 28], index=3)
with col_d:
    plan_cuotas = st.selectbox("Financiación", list(FINANCIACION.keys()))

margen_neto_obj = st.slider("% Margen Neto Deseado", 5, 40, 15)

# --- LÓGICA DE CÁLCULO MAESTRA ---
t_iva = 0.1735 if cond_iva == "Responsable Inscripto" else 0.0
t_iibb = iibb_tax / 100
t_finan = FINANCIACION[plan_cuotas] / 100

divisor = (1 - (comi_meli/100) - (margen_neto_obj/100) - t_iibb - t_iva - t_finan)
pvp_sugerido = (costo_compra + envio_final) / divisor if divisor > 0 else 0

# --- DASHBOARD VISUAL ---
st.markdown(f"""
    <div class="main-card">
        <div style="font-size: 1.1rem; text-transform: uppercase; font-weight: bold;">Precio Sugerido de Venta</div>
        <div class="big-price">${pvp_sugerido:,.0f}</div>
        <div style="font-size: 1.2rem;">Ganás el {margen_neto_obj}% Neto (${(pvp_sugerido * margen_neto_obj/100):,.0f})</div>
    </div>
""", unsafe_allow_html=True)

# --- EVALUADOR DE PRECIO REAL ---
st.divider()
st.subheader("🏁 ¿Dá o no dá?")
precio_mercado = st.number_input("Precio al que vende la competencia ($)", value=float(round(pvp_sugerido, 0)))

# Cálculos sobre el precio del mercado
# Valor 2026 para Envío Gratis: $33.000. Si es menos, se paga costo fijo.
costo_fijo = 3800.0 if precio_mercado < 33000 else 0.0
envio_real = envio_final if precio_mercado >= 33000 else 0.0

i_iva = (precio_mercado - (precio_mercado / 1.21)) if cond_iva == "Responsable Inscripto" else 0.0
i_iibb = (precio_mercado / (1.21 if cond_iva == "Responsable Inscripto" else 1)) * t_iibb
i_comi = precio_mercado * (comi_meli/100)
i_fina = precio_mercado * t_finan

ganancia_neta = precio_mercado - (i_comi + costo_fijo + envio_real + i_iva + i_iibb + i_fina) - costo_compra
margen_real = (ganancia_neta / precio_mercado) if precio_mercado > 0 else 0

# Tarjetas de decisión
c1, c2 = st.columns(2)
with c1:
    st.metric("Tu Ganancia", f"$ {ganancia_neta:,.0f}")
with c2:
    st.metric("Margen Real", f"{margen_real:.1%}")

if ganancia_neta < 0:
    st.error("🛑 NO PUBLICAR: Estás perdiendo dinero.")
elif margen_real < (margen_neto_obj/100):
    st.warning("⚠️ RIESGOSO: Margen por debajo de tu objetivo.")
else:
    st.success("✅ RENTABLE: Supera tu objetivo. ¡Dale para adelante!")

with st.expander("📊 Ver Desglose de Costos"):
    df_gastos = pd.DataFrame({
        "Concepto": ["Costo Compra", "Comisión MeLi", "Envío / Fijo", "Impuestos (IVA+IIBB)", "Financiación"],
        "Monto": [costo_compra, i_comi, (envio_real + costo_fijo), (i_iva + i_iibb), i_fina]
    })
    st.table(df_gastos.style.format({"Monto": "${:,.2f}"}))
