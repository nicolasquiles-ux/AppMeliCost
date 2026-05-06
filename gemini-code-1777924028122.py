import streamlit as st
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Centro Estant Pro", layout="wide", page_icon="🚀")

# =========================================================
# TABLAS MAESTRAS (Editá estos valores cuando cambien los costos)
# =========================================================
TARIFARIO_ENVIOS = {
    "0.5 kg": 4800.0, "1 kg": 5200.0, "2 kg": 5900.0, 
    "5 kg": 7400.0, "10 kg": 9800.0, "15 kg": 12500.0, 
    "20 kg": 15200.0, "25 kg": 18400.0, "30 kg": 22000.0
}

TASAS_FINANCIACION = {
    "1 Pago": 0.0, "3 Pagos (Cuota Simple)": 12.5, 
    "6 Pagos (Cuota Simple)": 23.8, "9 Pagos": 35.0, "12 Pagos": 45.0
}

CLAVE_CORRECTA = "CENTRO_PRO_2026"
# =========================================================

# --- ESTILOS ---
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    .pvp-box {
        background-color: #ffe600;
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        border: 2px solid #000;
    }
    .pvp-value { font-size: 3rem; font-weight: 900; color: #000; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("👤 Configuración")
    clave = st.text_input("Clave de Acceso", type="password")
    es_pro = (clave == CLAVE_CORRECTA)
    
    st.divider()
    reputacion = st.selectbox("Tu Reputación", ["Verde (50% desc)", "Amarilla (40% desc)", "Roja (0% desc)"])
    tipo_vend = st.radio("Condición IVA", ["Responsable Inscripto", "Monotributista"])
    iibb_tax = st.number_input("% Percepción IIBB", value=3.5)

# --- CUERPO PRINCIPAL ---
st.title("🚀 MeLi Intelligence")

if not es_pro:
    st.warning("⚠️ Por favor, ingresá la clave en el panel lateral para operar.")
else:
    # FILA DE INPUTS PRINCIPALES
    col_input1, col_input2, col_input3 = st.columns(3)
    
    with col_input1:
        costo_mueble = st.number_input("Costo de Fábrica ($)", value=15000.0, step=500.0)
    with col_input2:
        precio_meli = st.number_input("Precio Competencia MeLi ($)", value=0.0, help="Mirá el precio en la web de MeLi y pegalo acá")
    with col_input3:
        margen_objetivo = st.slider("% Margen Neto Deseado", 5, 50, 20)

    st.divider()

    # CÁLCULOS DE LÓGICA (DIVISOR)
    plan_cuotas = st.selectbox("Plan de Financiación", list(TASAS_FINANCIACION.keys()))
    comision_cat = st.number_input("% Comisión Categoría (Clásica/Premium)", value=15.0)

    t_iva = 0.1735 if tipo_vend == "Responsable Inscripto" else 0.0
    t_iibb = iibb_tax / 100
    t_finan = TASAS_FINANCIACION[plan_cuotas] / 100
    divisor = (1 - (comision_cat/100) - (margen_objetivo/100) - t_iibb - t_iva - t_finan)
    
    dcto_e = 0.5 if "Verde" in reputacion else 0.6 if "Amarilla" in reputacion else 1
    costo_envio_base = TARIFARIO_ENVIOS["10 kg"] * dcto_e
    
    # PVP SUGERIDO
    pvp_sugerido = (costo_mueble + costo_envio_base) / divisor if divisor > 0 else 0

    col_res_izq, col_res_der = st.columns([1, 2])

    with col_res_izq:
        st.markdown(f"""
            <div class="pvp-box">
                <div style="font-weight:bold; color:#333;">PVP SUGERIDO</div>
                <div class="pvp-value">${pvp_sugerido:,.0f}</div>
                <div style="color:#555;">Para ganar el {margen_objetivo}%</div>
            </div>
        """, unsafe_allow_html=True)

    with col_res_der:
        st.subheader("📊 Análisis de Rentabilidad Real")
        precio_a_evaluar = st.number_input("Evaluar este precio final ($)", value=float(round(precio_meli if precio_meli > 0 else pvp_sugerido, 0)))
        
        # Selección de peso real
        peso_real = st.select_slider("Peso para logística real", options=list(TARIFARIO_ENVIOS.keys()), value="10 kg")
        
        # Cálculos finales
        envio_final = TARIFARIO_ENVIOS[peso_real] * dcto_e if precio_a_evaluar >= 33000 else 0.0
        c_fijo = 3030.0 if precio_a_evaluar < 33000 else 0.0
        
        iva_final = (precio_a_evaluar - (precio_a_evaluar / 1.21)) if tipo_vend == "Responsable Inscripto" else 0.0
        iibb_final = (precio_a_evaluar / (1.21 if tipo_vend == "Responsable Inscripto" else 1)) * t_iibb
        comi_final = precio_a_evaluar * (comision_cat/100)
        finan_final = precio_a_evaluar * t_finan
        
        total_gastos = comi_final + c_fijo + envio_final + iva_final + iibb_final + finan_final
        ganancia_neta = precio_a_evaluar - total_gastos - costo_mueble
        margen_real = (ganancia_neta / precio_a_evaluar) if precio_a_evaluar > 0 else 0

        c1, c2 = st.columns(2)
        c1.metric("Ganancia Neta", f"$ {ganancia_neta:,.2f}", delta=f"{margen_real:.1%}")
        c2.metric("Margen Real", f"{margen_real:.2%}")

    with st.expander("🔍 Ver Desglose de Costos (Tabla)"):
        data = {
            "Concepto": ["Costo Mueble", "Comisión MeLi", "Costo Fijo", "Envío", "IVA (ARCA)", "IIBB", "Costo Finan."],
            "Monto": [costo_mueble, comi_final, c_fijo, envio_final, iva_final, iibb_final, finan_final]
        }
        st.table(pd.DataFrame(data).style.format({"Monto": "${:,.2f}"}))
