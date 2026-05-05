import streamlit as st
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="MeLi Pro Analytics", layout="wide")

# Estilos personalizados para un look profesional
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #eee; }
    div[data-testid="stExpander"] { background-color: #ffffff; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 MeLi Dashboard Rentabilidad")
st.caption("Versión 2.0 - Actualizado Mayo 2026 (Lógica ARCA / MeLi Argentina)")

# --- DATOS DE REFERENCIA (Mayo 2026) ---
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
    st.info("💡 Los Responsables Inscriptos recuperan el IVA de la factura A de MeLi, pero aquí calculamos el neto final de bolsillo.")

# --- PANEL PRINCIPAL: ENTRADA DE DATOS ---
col_in1, col_in2, col_in3 = st.columns([1, 1, 1.2])

with col_in1:
    st.subheader("💰 Precios")
    costo_compra = st.number_input("Costo de Compra ($)", min_value=0.0, value=15000.0, help="Tu costo de adquisición o fabricación.")
    precio_venta = st.number_input("Precio de Venta ($)", min_value=1.0, value=35000.0)
    tipo_pub = st.selectbox("Tipo de Publicación", ["Clásica", "Premium (Cuotas)"])
    comision_pct = st.number_input("% Comisión MeLi", value=15.0 if tipo_pub == "Clásica" else 29.0)

with col_in2:
    st.subheader("📦 Logística")
    categoria_peso = st.selectbox("Peso Facturable", list(tarifario_envios.keys()))
    costo_lista_envio = tarifario_envios[categoria_peso]
    
    envio_gratis_obligatorio = precio_venta >= 33000
    ofrece_envio_gratis = st.checkbox("Ofrecer Envío Gratis", value=envio_gratis_obligatorio)
    
    otros_costos = st.number_input("Otros Gastos ($)", value=0.0, help="Embalaje, cinta, cadetería, etc.")

with col_in3:
    st.subheader("📏 Peso Volumétrico")
    st.caption("Calculá si tu caja paga por tamaño:")
    c_l, c_an, c_al = st.columns(3)
    largo = c_l.number_input("Largo (cm)", value=0)
    ancho = c_an.number_input("Ancho (cm)", value=0)
    alto = c_al.number_input("Alto (cm)", value=0)
    
    if largo > 0 and ancho > 0 and alto > 0:
        volumetrico = (largo * ancho * alto) / 4000
        st.warning(f"Peso Volumétrico: {volumetrico:.2f} kg")
    else:
        st.write("Ingresá medidas para calcular.")

# --- MOTOR DE CÁLCULO ---

# 1. Costo Fijo por unidad
costo_fijo_meli = 0
if precio_venta < 16000: costo_fijo_meli = 1255
elif precio_venta < 24000: costo_fijo_meli = 2500
elif precio_venta < 33000: costo_fijo_meli = 3030

# 2. Descuento de Envío
if ofrece_envio_gratis:
    if reputacion == "Verde (50%)": dcto = 0.50
    elif reputacion == "Amarilla/Sin Medalla (40%)": dcto = 0.40
    else: dcto = 0.0
    gasto_envio = costo_lista_envio * (1 - dcto)
else:
    gasto_envio = 0.0

# 3. Impuestos (Deducción de IVA para RI)
if tipo_vendedor == "Responsable Inscripto":
    iva_sobre_venta = precio_venta - (precio_venta / 1.21)
    base_imponible_iibb = precio_venta / 1.21
else:
    iva_sobre_venta = 0
    base_imponible_iibb = precio_venta

total_iibb = base_imponible_iibb * (iibb_tax / 100)
total_comision_meli = (precio_venta * (comision_pct / 100)) + costo_fijo_meli

# 4. RESULTADO FINAL
gastos_totales = total_comision_meli + gasto_envio + iva_sobre_venta + total_iibb + otros_costos
ganancia_neta = precio_venta - gastos_totales - costo_compra
margen_sobre_venta = (ganancia_neta / precio_venta) * 100 if precio_venta > 0 else 0

# --- MOTOR DE CÁLCULO (Versión Corregida) ---

# ... (todo el cálculo anterior de gastos_totales igual) ...

ganancia_neta = precio_venta - gastos_totales - costo_compra

# Corregimos el cálculo del margen para que sea compatible con el formato %
if precio_venta > 0:
    # Lo dejamos en decimal (ej: 0.15 en vez de 15) para que el formateador :.2% funcione bien
    margen_neto_decimal = ganancia_neta / precio_venta 
else:
    margen_neto_decimal = 0.0

# --- INTERFAZ DE RESULTADOS ---
st.divider()
m1, m2, m3, m4 = st.columns(4)

m1.metric("Ganancia de Bolsillo", f"$ {ganancia_neta:,.2f}")
# Usamos la variable en decimal con el formateador de porcentaje
m2.metric("Margen Neto", f"{margen_neto_decimal:.2%}") 
m3.metric("Gastos Totales", f"$ {gastos_totales:,.2f}")
m4.metric("Punto de Equilibrio", f"$ {(costo_compra + gastos_totales - iva_venta):,.0f}")

