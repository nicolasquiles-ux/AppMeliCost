import streamlit as st
import pandas as pd

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Centro Estant Pro v7.5", layout="centered")

# =========================================================
# TABLAS MAESTRAS EDITABLES (Valores 2026)
# =========================================================
COSTOS_LOGISTICA = {
    "MeLi Colecta / Full (Estándar)": {
        "Chico (Hasta 2kg)": 5900.0,
        "Mediano (5 a 10kg)": 9800.0,
        "Grande (15 a 25kg)": 16500.0,
        "Extra Grande (25 a 30kg)": 22000.0
    },
    "Envíos Especiales (Muebles Pesados)": {
        "Escritorio / Rack Mediano": 28500.0,
        "Placard / Biblioteca Grande": 38000.0,
        "Multifunción / Combo Pesado": 45000.0
    },
    "Mercado Envío Flex (Promedio)": {
        "Zona Local": 4500.0,
        "Zona Extendida": 7200.0,
        "CABA/GBA Full": 8500.0
    }
}

TASAS_FINANCIACION = {
    "1 Pago": 0.0, "3 Pagos (7%)": 7, 
    "6 Pagos (10%)": 10, "9 Pagos (13.5%)": 13.5, "12 Pagos (16%)": 16
}

CLAVE_CORRECTA = "MELIPRO_2026"
# =========================================================

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .card-sugerido {
        background-color: #000; color: #ffe600; padding: 25px;
        border-radius: 20px; text-align: center; margin-bottom: 20px;
    }
    .big-text { font-size: 3.5rem; font-weight: 900; margin: 0; }
    .stNumberInput input { font-size: 1.5rem !important; }
    .label-logistica { 
        background-color: #e1f5fe; padding: 10px; border-radius: 10px;
        border-left: 5px solid #03a9f4; margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.title("🔐 Acceso")
    clave = st.text_input("Clave", type="password")
    acceso = (clave == CLAVE_CORRECTA)
    st.divider()
    repu = st.selectbox("Tu Reputación", ["Verde (50% desc)", "Amarilla (40% desc)", "Roja (0% desc)"])
    cond_iva = st.radio("Tu IVA", ["Responsable Inscripto", "Monotributista"])
    per_iibb = st.number_input("% IIBB", value=3.5)

if not acceso:
    st.warning("⚠️ Ingresá la clave.")
else:
    st.title("📦 Calculadora Centro Estant")

    # --- ENTRADA DE DATOS ---
    c_fabrica = st.number_input("Costo de Compra ($)", value=35000.0, step=1000.0)
    
    # --- NUEVO SELECTOR DE LOGÍSTICA ---
    st.markdown('<div class="label-logistica"><b>CONFIGURACIÓN DE ENVÍO</b></div>', unsafe_allow_html=True)
    tipo_logistica = st.selectbox("Tipo de Servicio", list(COSTOS_LOGISTICA.keys()))
    categoria_peso = st.selectbox("Categoría de Producto", list(COSTOS_LOGISTICA[tipo_logistica].keys()))
    
    # Obtener costo base de la tabla
    costo_envio_lista = COSTOS_LOGISTICA[tipo_logistica][categoria_peso]
    
    # Aplicar bonificación por reputación (Solo aplica a Mercado Envíos, no a Flex por lo general)
    if "Flex" in tipo_logistica:
        costo_envio_final = costo_envio_lista # Flex se suele pagar completo o negociado
    else:
        bonif = 0.5 if "Verde" in repu else 0.6 if "Amarilla" in repu else 1.0
        costo_envio_final = costo_envio_lista * bonif

    st.info(f"Costo Logístico detectado: ${costo_envio_final:,.2f}")

    # --- PARÁMETROS DE VENTA ---
    col1, col2 = st.columns(2)
    with col1:
        comi_meli = st.selectbox("% Comisión MeLi", [10, 12, 14, 15, 16.5, 28], index=3)
    with col2:
        plan_pago = st.selectbox("Financiación", list(TASAS_FINANCIACION.keys()))

    margen_obj = st.slider("% Margen Neto Deseado", 5, 40, 15)

    # --- LÓGICA DE CÁLCULO ---
    t_iva = 0.1735 if cond_iva == "Responsable Inscripto" else 0.0
    t_iibb = per_iibb / 100
    t_finan = TASAS_FINANCIACION[plan_pago] / 100
    
    divisor = (1 - (comi_meli/100) - (margen_obj/100) - t_iibb - t_iva - t_finan)
    pvp_objetivo = (c_fabrica + costo_envio_final) / divisor if divisor > 0 else 0

    # --- DASHBOARD ---
    st.markdown(f"""
        <div class="card-sugerido">
            <div style="font-size: 1rem; text-transform: uppercase;">Precio de Venta Sugerido</div>
            <div class="big-text">${pvp_objetivo:,.0f}</div>
            <div style="font-weight: bold; margin-top:5px;">Margen Neto: {margen_obj}%</div>
        </div>
    """, unsafe_allow_html=True)

    # --- COMPARADOR ---
    st.divider()
    st.subheader("🏁 Comparar vs Competencia")
    p_comp = st.number_input("Precio a Evaluar ($)", value=float(round(pvp_objetivo,0)))

    # Recálculo con el precio de competencia
    # Si es menor a 33.000 (valor 2026), hay costo fijo
    fijo = 3500.0 if p_comp < 33000 else 0.0
    
    i_iva = (p_comp - (p_comp / 1.21)) if cond_iva == "Responsable Inscripto" else 0.0
    i_iibb = (p_comp / (1.21 if cond_iva == "Responsable Inscripto" else 1)) * t_iibb
    i_comi = p_comp * (comi_meli/100)
    i_fina = p_comp * t_finan
    
    utilidad = p_comp - (i_comi + fijo + costo_envio_final + i_iva + i_iibb + i_fina) - c_fabrica
    margen_r = (utilidad / p_comp) if p_comp > 0 else 0

    col_res1, col_res2 = st.columns(2)
    col_res1.metric("Ganancia Neta", f"$ {utilidad:,.0f}")
    col_res2.metric("Margen Real", f"{margen_r:.1%}")

    if margen_r < 0:
        st.error("⚠️ Estás operando a PERDIDA con este precio.")
    elif margen_r < (margen_obj/100):
        st.warning("⚠️ Ganancia por debajo del objetivo.")
    else:
        st.success("✅ Precio altamente rentable.")

    with st.expander("📊 Desglose de Gastos"):
        st.write(f"• Envio Final: ${costo_envio_final:,.2f}")
        st.write(f"• Comisión: ${i_comi:,.2f}")
        st.write(f"• Financiación: ${i_fina:,.2f}")
        st.write(f"• Impuestos: ${(i_iva + i_iibb):,.2f}")
