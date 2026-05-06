import streamlit as st
import pandas as pd

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="MeLi Dashboard", layout="centered", page_icon="📈")

# =========================================================
# TABLAS EDITABLES (Modificá acá y se actualiza todo)
# =========================================================
TARIFARIO_ENVIOS = {
    "0.5 kg": 4800.0, "1 kg": 5200.0, "2 kg": 5900.0, 
    "5 kg": 7400.0, "10 kg": 9800.0, "15 kg": 12500.0, 
    "20 kg": 15200.0, "25 kg": 18400.0, "30 kg": 22000.0
}

TASAS_FINANCIACION = {
    "1 Pago": 0.0, "3 Pagos (7%)": 7, 
    "6 Pagos (10%)": 10, "9 Pagos (13.5%)": 13.5, "12 Pagos (16%)": 16
}

CLAVE_CORRECTA = "CENTRO_PRO_2026"
# =========================================================

# --- ESTILOS CSS PARA MÓVIL Y DISEÑO ---
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: 800; }
    .main-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        border-left: 10px solid #ffe600;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .stButton>button {
        width: 100%;
        height: 60px;
        font-size: 1.2rem !important;
        font-weight: bold !important;
        border-radius: 12px !important;
    }
    .big-price {
        font-size: 3.2rem;
        font-weight: 900;
        text-align: center;
        color: #1d1d1d;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR (Configuración fija) ---
with st.sidebar:
    st.title("⚙️ Ajustes")
    clave = st.text_input("Clave Pro", type="password")
    es_pro = (clave == CLAVE_CORRECTA)
    st.divider()
    repu = st.selectbox("Reputación", ["Verde (50% desc)", "Amarilla (40% desc)", "Roja (0% desc)"])
    condicion_iva = st.radio("IVA", ["Responsable Inscripto", "Monotributista"])
    iibb_percep = st.number_input("% IIBB", value=3.5)

# --- APP PRINCIPAL ---
if not es_pro:
    st.warning("🔒 Ingresá la clave para operar.")
else:
    st.title("📊 Simulador Centro Estant")

    # SECCIÓN 1: DATOS DE ENTRADA (Grandes para dedos)
    with st.container():
        st.markdown('<div class="main-card"><b>1. COSTOS Y OBJETIVOS</b></div>', unsafe_allow_html=True)
        costo_f = st.number_input("Costo de Fábrica ($)", value=25000.0, step=1000.0)
        margen_obj = st.slider("% Margen Neto Deseado", 5, 40, 15)
        comi_meli = st.selectbox("% Comisión MeLi", [10.0, 12.0, 14.0, 15.0, 16.5, 28.0], index=3)
        cuotas = st.selectbox("Financiación", list(TASAS_FINANCIACION.keys()))

    # CÁLCULO DINÁMICO
    t_iva = 0.1735 if condicion_iva == "Responsable Inscripto" else 0.0
    t_iibb = iibb_percep / 100
    t_finan = TASAS_FINANCIACION[cuotas] / 100
    divisor = (1 - (comi_meli/100) - (margen_obj/100) - t_iibb - t_iva - t_finan)
    
    bonif = 0.5 if "Verde" in repu else 0.6 if "Amarilla" in repu else 1
    envio_sug = TARIFARIO_ENVIOS["10 kg"] * bonif
    pvp_sug = (costo_f + envio_sug) / divisor if divisor > 0 else 0

    # SECCIÓN 2: RESULTADO PRINCIPAL (PVP SUGERIDO)
    st.markdown('<div style="text-align:center; margin-top:20px;"><b>VENTA SUGERIDA</b></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="big-price">${pvp_sug:,.0f}</div>', unsafe_allow_html=True)

    st.divider()

    # SECCIÓN 3: COMPARADOR REAL (MÓVIL FRIENDLY)
    st.subheader("🏁 Comparar vs Competencia")
    precio_comp = st.number_input("Precio del competidor ($)", value=float(round(pvp_sug,0)))
    peso_real = st.select_slider("Peso del bulto", options=list(TARIFARIO_ENVIOS.keys()), value="10 kg")

    # Cálculos Finales
    envio_r = TARIFARIO_ENVIOS[peso_real] * bonif if precio_comp >= 33000 else 0.0
    c_fijo = 3030.0 if precio_comp < 33000 else 0.0
    
    iva_r = (precio_comp - (precio_comp / 1.21)) if condicion_iva == "Responsable Inscripto" else 0.0
    iibb_r = (precio_comp / (1.21 if condicion_iva == "Responsable Inscripto" else 1)) * t_iibb
    comi_r = precio_comp * (comi_meli/100)
    fina_r = precio_comp * t_finan
    
    ganancia = precio_comp - (comi_r + c_fijo + envio_r + iva_r + iibb_r + fina_r) - costo_f
    margen_r = (ganancia / precio_comp) if precio_comp > 0 else 0

    # DASHBOARD DE RESULTADOS (TARJETAS)
    color_neta = "#d4edda" if ganancia > 0 else "#f8d7da"
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Ganancia Neta", f"$ {ganancia:,.0f}")
    with col2:
        st.metric("Margen Real", f"{margen_r:.1%}")

    if ganancia < 0:
        st.error(f"⚠️ Estás perdiendo ${abs(ganancia):,.0f} por unidad.")
    elif ganancia > 0 and margen_r < (margen_obj/100):
        st.warning("⚠️ Margen positivo pero por debajo del objetivo.")
    else:
        st.success("✅ ¡Operación Rentable!")

    with st.expander("📝 Ver detalle de gastos"):
        st.write(f"• **Envío:** ${envio_r:,.2f}")
        st.write(f"• **Comisión MeLi:** ${comi_r:,.2f}")
        st.write(f"• **Impuestos (IVA+IIBB):** ${(iva_r + iibb_r):,.2f}")
        st.write(f"• **Costo Financiero:** ${fina_r:,.2f}")
