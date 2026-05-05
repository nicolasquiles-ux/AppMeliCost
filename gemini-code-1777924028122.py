import streamlit as st
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="MeLi Pro Costos", layout="wide")

# Estilos CSS para un look profesional
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #eee; }
    div[data-testid="stExpander"] { background-color: #ffffff; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 MeLi Pro Costos")
st.caption("Versión 2.1 Final - Mayo 2026 (NQ)")

# --- DATOS DE REFERENCIA (Tarifario Mayo 2026) ---
tarifario_envios = {
    "0.5 kg (Sobres)": 4800.0,
    "1 kg": 5200.0,
    "2 kg": 5900.0,
    "5 kg": 7400.0,
    "10 kg": 9800.0,
    "15 kg": 12500.0,
    "20 kg": 15200.0,
    "25 kg": 18400.0,
    "30 kg (Límite)": 22000.0,
    "Especial (Muebles)": 35000.0
}

# --- SIDEBAR: CONFIGURACIÓN FISCAL ---
with st.sidebar:
    st.header("⚙️ Configuración")
    reputacion = st.selectbox("Tu Reputación", ["Verde (50%)", "Amarilla/Sin Medalla (40%)", "Roja/Naranja (0%)"])
    tipo_vendedor = st.radio("Condición ante el IVA", ["Responsable Inscripto", "Monotributista"])
    iibb_tax = st.number_input("% Ingresos Brutos", value=3.5, step=0.1)
    st.divider()
    st.info("💡 Este simulador detrae el IVA del precio de venta para calcular la rentabilidad real de bolsillo.")

# --- PANEL PRINCIPAL: ENTRADA DE DATOS ---
col_in1, col_in2, col_in3 = st.columns([1, 1, 1.2])

with col_in1:
    st.subheader("💰 Precios")
    costo_compra = st.number_input("Costo de Compra ($)", min_value=0.0, value=15000.0)
    precio_venta = st.number_input("Precio de Venta ($)", min_value=0.0, value=35000.0)
    tipo_pub = st.selectbox("Tipo de Publicación", ["Clásica", "Premium (Cuotas)"])
    comision_pct = st.number_input("% Comisión MeLi", value=15.0 if tipo_pub == "Clásica" else 29.0)

with col_in2:
    st.subheader("📦 Logística")
    categoria_peso = st.selectbox("Peso Facturable", list(tarifario_envios.keys()))
    costo_lista_envio = tarifario_envios[categoria_peso]
    
    ofrece_envio_gratis = st.checkbox("Ofrecer Envío Gratis", value=(precio_venta >= 33000))
    otros_costos = st.number_input("Otros Gastos ($)", value=0.0)

with col_in3:
    st.subheader("📏 Peso Volumétrico")
    st.caption("Cálculo de caja (Largo x Ancho x Alto / 4000)")
    c_l, c_an, c_al = st.columns(3)
    largo = c_l.number_input("Largo (cm)", value=0)
    ancho = c_an.number_input("Ancho (cm)", value=0)
    alto = c_al.number_input("Alto (cm)", value=0)
    
    if largo > 0 and ancho > 0 and alto > 0:
        volumetrico = (largo * ancho * alto) / 4000
        st.warning(f"Peso Volumétrico: {volumetrico:.2f} kg")

# --- MOTOR DE CÁLCULO ---

# Inicialización de variables críticas para evitar NameError
costo_fijo_meli = 0.0
iva_venta = 0.0
total_iibb = 0.0
gasto_envio = 0.0

# 1. Costo Fijo MeLi
if 0 < precio_venta < 16000: costo_fijo_meli = 1255.0
elif 16000 <= precio_venta < 24000: costo_fijo_meli = 2500.0
elif 24000 <= precio_venta < 33000: costo_fijo_meli = 3030.0

# 2. Descuento de Envío
if ofrece_envio_gratis:
    if reputacion == "Verde (50%)": dcto = 0.50
    elif reputacion == "Amarilla/Sin Medalla (40%)": dcto = 0.40
    else: dcto = 0.0
    gasto_envio = costo_lista_envio * (1 - dcto)

# 3. Impuestos
if tipo_vendedor == "Responsable Inscripto":
    iva_venta = precio_venta - (precio_venta / 1.21)
    base_imponible_iibb = precio_venta / 1.21
else:
    iva_venta = 0.0
    base_imponible_iibb = precio_venta

total_iibb = base_imponible_iibb * (iibb_tax / 100)
total_comision_meli = (precio_venta * (comision_pct / 100)) + costo_fijo_meli

# 4. Cálculo Final
gastos_totales = total_comision_meli + gasto_envio + iva_venta + total_iibb + otros_costos
ganancia_neta = precio_venta - gastos_totales - costo_compra

if precio_venta > 0:
    margen_neto_decimal = ganancia_neta / precio_venta
else:
    margen_neto_decimal = 0.0

# --- INTERFAZ DE RESULTADOS ---
st.divider()
m1, m2, m3, m4 = st.columns(4)

m1.metric("Ganancia Neta", f"$ {ganancia_neta:,.2f}")
m2.metric("Margen Real", f"{margen_neto_decimal:.2%}")
m3.metric("Gastos Totales", f"$ {gastos_totales:,.2f}")
m4.metric("Punto de Equilibrio", f"$ {(costo_compra + gastos_totales - iva_venta):,.0f}")

if ganancia_neta > 0:
    st.success(f"✅ Operación rentable. Ganas ${ganancia_neta:,.2f} por unidad.")
elif precio_venta > 0:
    st.error(f"⚠️ Operación en pérdida. Pierdes ${abs(ganancia_neta):,.2f}.")

with st.expander("🔍 Ver detalle de costos"):
    data_desglose = {
        "Concepto": ["Costo Producto", "Comisión MeLi", "Costo Fijo MeLi", "Envío", "IVA", "IIBB", "Otros"],
        "Monto ($)": [costo_compra, precio_venta * (comision_pct/100), costo_fijo_meli, gasto_envio, iva_venta, total_iibb, otros_costos]
    }
    st.table(pd.DataFrame(data_desglose))
