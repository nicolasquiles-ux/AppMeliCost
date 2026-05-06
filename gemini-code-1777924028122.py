import streamlit as st
import pandas as pd

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Meli Price Pro", layout="centered")

# =========================================================
# TABLAS MAESTRAS EDITABLES
# =========================================================
TARIFARIO_ENVIOS = {
    "Sobres/0.5kg": 4800.0, "Hasta 1kg": 5200.0, "Hasta 2kg": 5900.0, 
    "Hasta 5kg": 7400.0, "Hasta 10kg": 9800.0, "Hasta 15kg": 12500.0, 
    "Hasta 20kg": 15200.0, "Hasta 25kg": 18400.0, "Mueble Pesado 30kg": 22000.0
}

TASAS_FINANCIACION = {
    "1 Pago (Contado)": 0.0, "3 Pagos (Cuota Simple)": 7, 
    "6 Pagos (Cuota Simple)": 10, "9 Pagos": 13.5, "12 Pagos": 16
}

CLAVE_CORRECTA = "MELIPRO_2026"
# =========================================================

# --- ESTILOS CSS PARA MÓVIL (FUENTES GRANDES) ---
st.markdown("""
    <style>
    body { background-color: #f0f2f6; }
    .stNumberInput input { font-size: 1.5rem !important; font-weight: bold !important; height: 50px !important; }
    .stSelectbox div { font-size: 1.2rem !important; font-weight: 600 !important; }
    
    .card-sugerido {
        background-color: #000000;
        color: #ffe600;
        padding: 25px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    .big-text { font-size: 3.5rem; font-weight: 900; margin: 0; line-height: 1; }
    .label-text { font-size: 1.1rem; text-transform: uppercase; letter-spacing: 1px; }
    
    .metric-container {
        background-color: white;
        padding: 15px;
        border-radius: 15px;
        border: 1px solid #ddd;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- PANEL DE CONTROL ---
with st.sidebar:
    st.title("🔐 Acceso")
    clave = st.text_input("Clave", type="password")
    acceso = (clave == CLAVE_CORRECTA)
    st.divider()
    repu = st.selectbox("Reputación", ["Verde (50% desc)", "Amarilla (40% desc)", "Roja (0% desc)"])
    cond_iva = st.radio("Tu IVA", ["Responsable Inscripto", "Monotributista"])
    per_iibb = st.number_input("% IIBB", value=3.5)

if not acceso:
    st.warning("⚠️ Ingresá la clave para ver el Dashboard.")
else:
    st.title("📦 Calculadora de Precios")

    # --- ENTRADA DE DATOS ---
    with st.container():
        c_fabrica = st.number_input("Costo de Compra / Fábrica ($)", value=30000.0, step=1000.0)
        margen_deseado = st.slider("% Margen Neto que querés ganar", 5, 40, 15)
        
        col_a, col_b = st.columns(2)
        with col_a:
            comi_meli = st.selectbox("% Comi MeLi", [10, 12, 14, 15, 16.5, 28], index=3)
        with col_b:
            plan_cuotas = st.selectbox("Financiación", list(TASAS_FINANCIACION.keys()))

    # --- LÓGICA DE CÁLCULO (PVP DESDE RENTABILIDAD) ---
    t_iva = 0.1735 if cond_iva == "Responsable Inscripto" else 0.0
    t_iibb = per_iibb / 100
    t_finan = TASAS_FINANCIACION[plan_cuotas] / 100
    
    # El divisor asegura que el precio cubra TODO y te deje el margen neto
    divisor = (1 - (comi_meli/100) - (margen_deseado/100) - t_iibb - t_iva - t_finan)
    
    # Costo logístico base para el cálculo inicial
    bonif = 0.5 if "Verde" in repu else 0.6 if "Amarilla" in repu else 1
    envio_base = TARIFARIO_ENVIOS["Hasta 10kg"] * bonif
    
    pvp_objetivo = (c_fabrica + envio_base) / divisor if divisor > 0 else 0

    # --- DASHBOARD PRINCIPAL ---
    st.markdown(f"""
        <div class="card-sugerido">
            <div class="label-text">Precio de Venta Sugerido</div>
            <div class="big-text">${pvp_objetivo:,.0f}</div>
            <div style="font-weight: bold; margin-top:10px;">Margen Neto Asegurado: {margen_deseado}%</div>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    # --- SECCIÓN COMPARATIVA ---
    st.subheader("📋 Análisis de Competencia")
    p_competencia = st.number_input("Precio Competencia / Evaluar ($)", value=float(round(pvp_objetivo,0)))
    peso_mueble = st.select_slider("Peso para Logística Real", options=list(TARIFARIO_ENVIOS.keys()), value="Hasta 10kg")

    # Cálculos Reales sobre el precio ingresado
    e_real = TARIFARIO_ENVIOS[peso_mueble] * bonif if p_competencia >= 33000 else 0.0
    fijo = 3030.0 if p_competencia < 33000 else 0.0
    
    i_iva = (p_competencia - (p_competencia / 1.21)) if cond_iva == "Responsable Inscripto" else 0.0
    i_iibb = (p_competencia / (1.21 if cond_iva == "Responsable Inscripto" else 1)) * t_iibb
    i_comi = p_competencia * (comi_meli/100)
    i_fina = p_competencia * t_finan
    
    utilidad = p_competencia - (i_comi + fijo + e_real + i_iva + i_iibb + i_fina) - c_fabrica
    margen_real = (utilidad / p_competencia) if p_competencia > 0 else 0

    # Tarjetas de Resultado Real
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
            <div class="metric-container">
                <div style="color:gray; font-size:0.9rem;">GANANCIA NETA</div>
                <div style="font-size:1.8rem; font-weight:bold; color:{'#28a745' if utilidad > 0 else '#dc3545'};">
                    $ {utilidad:,.0f}
                </div>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
            <div class="metric-container">
                <div style="color:gray; font-size:0.9rem;">MARGEN REAL</div>
                <div style="font-size:1.8rem; font-weight:bold; color:{'#28a745' if margen_real > (margen_deseado/100) else '#ffc107'};">
                    {margen_real:.1%}
                </div>
            </div>
        """, unsafe_allow_html=True)

    # --- DESGLOSE LOGÍSTICO CLARO ---
    with st.expander("🚚 Ver Detalle Logístico e Impuestos"):
        st.write(f"**Costo de Envío (con dto):** ${e_real:,.2f}")
        st.write(f"**Costo Fijo (si aplica):** ${fijo:,.2f}")
        st.write(f"**Comisión MeLi:** ${i_comi:,.2f}")
        st.write(f"**Impuestos (IVA + IIBB):** ${(i_iva + i_iibb):,.2f}")
        st.write(f"**Costo Financiero:** ${i_fina:,.2f}")
        st.info(f"Costo Total de Venta: ${(i_comi + fijo + e_real + i_iva + i_iibb + i_fina):,.2f}")
