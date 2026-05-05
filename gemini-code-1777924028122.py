import streamlit as st
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="MeLi Pricing Pro", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #eee; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 MeLi Smart Pricing Dashboard")
st.caption("Cálculo automático de PVP basado en margen objetivo - Mayo 2026")

# --- DATA DE REFERENCIA ---
tarifario_envios = {
    "0.5 kg (Sobres)": 4800.0, "1 kg": 5200.0, "2 kg": 5900.0, "5 kg": 7400.0,
    "10 kg": 9800.0, "15 kg": 12500.0, "20 kg": 15200.0, "25 kg": 18400.0,
    "30 kg (Límite)": 22000.0, "Especial (Muebles)": 35000.0
}

# --- SIDEBAR CONFIG ---
with st.sidebar:
    st.header("⚙️ Configuración")
    reputacion = st.selectbox("Tu Reputación", ["Verde (50%)", "Amarilla (40%)", "Roja (0%)"])
    tipo_vendedor = st.radio("Condición IVA", ["Responsable Inscripto", "Monotributista"])
    iibb_tax = st.number_input("% Ingresos Brutos", value=3.5)
    st.divider()
    margen_objetivo = st.slider("% Margen Neto Deseado", 5, 50, 20)
    st.info(f"La App sugerirá un precio para ganar el {margen_objetivo}% neto.")

# --- ENTRADA DE DATOS ---
col_prod, col_envio, col_finan = st.columns([1, 1, 1.2])

with col_prod:
    st.subheader("💰 Costos Base")
    costo_compra = st.number_input("Costo de Compra ($)", min_value=0.0, value=15000.0)
    otros_costos = st.number_input("Otros Gastos ($)", value=0.0)
    comision_base = st.number_input("% Comisión MeLi", value=15.0)

with col_envio:
    st.subheader("📦 Logística")
    peso_sel = st.selectbox("Peso del Producto", list(tarifario_envios.keys()))
    costo_lista = tarifario_envios[peso_sel]
    
    # Determinamos descuento de envío
    dcto = 0.50 if "Verde" in reputacion else (0.40 if "Amarilla" in reputacion else 0.0)
    
    # El envío es obligatorio > $33.000, pero para el cálculo inicial asumimos que se ofrece
    costo_envio_final = costo_lista * (1 - dcto)
    st.write(f"Costo Envío estimado: **${costo_envio_final:,.2f}**")

with col_finan:
    st.subheader("💳 Financiación")
    plan_cuotas = st.selectbox("Plan de Cuotas (Publicación Clásica)", 
                               ["1 Pago", "3 Cuotas (7%)", "6 Cuotas (10%)","9 Cuotas (13,5%)", "12 Cuotas (16%)"])
    tasa_finan = 0.0 if "1 Pago" in plan_cuotas else (12.5 if "3 Cuotas" in plan_cuotas else 23.8)

# --- LÓGICA DE PRICING INTELIGENTE ---
# Intentamos despejar el PVP: 
# PVP = (Costo + Otros + Envío + CargoFijo) / (1 - %Comisión - %Margen - %IIBB - %IVA - %Finan)

# 1. Parámetros de la fórmula
tax_iva = 0.1735 if tipo_vendedor == "Responsable Inscripto" else 0.0 # IVA efectivo sobre PVP (21/121)
tax_iibb = iibb_tax / 100
comm = comision_base / 100
finan = tasa_finan / 100
margen = margen_objetivo / 100

# Estimamos cargo fijo (asumimos que el PVP será > 33000 para muebles de Centro Estant, si no, lo sumamos)
c_fijo = 0.0 if costo_compra > 20000 else 3030.0 

divisor = (1 - comm - margen - tax_iibb - tax_iva - finan)

if divisor > 0:
    pvp_sugerido = (costo_compra + otros_costos + costo_envio_final + c_fijo) / divisor
else:
    pvp_sugerido = costo_compra * 2 # Resguardo matemático

# --- CAMPO PVP MANUAL (Sugerido por defecto) ---
st.divider()
st.subheader("🚀 Ajuste Final de Venta")
precio_venta = st.number_input("Precio de Venta Final (PVP)", value=float(round(pvp_sugerido, 0)))
st.caption(f"Sugerencia inicial basada en tu margen objetivo del {margen_objetivo}%")

# --- RE-CÁLCULO REAL ---
if 0 < precio_venta < 33000:
    costo_fijo_real = 3030.0 # Promedio para el rango
elif precio_venta >= 33000:
    costo_fijo_real = 0.0
else:
    costo_fijo_real = 0.0

iva_real = (precio_venta - (precio_venta / 1.21)) if tipo_vendedor == "Responsable Inscripto" else 0.0
iibb_real = (precio_venta / (1.21 if tipo_vendedor == "Responsable Inscripto" else 1)) * (iibb_tax / 100)
comision_real = precio_venta * (comision_base / 100)
finan_real = precio_venta * (tasa_finan / 100)

gastos_totales = comision_real + costo_fijo_real + costo_envio_final + iva_real + iibb_real + otros_costos + finan_real
ganancia_neta = precio_venta - gastos_totales - costo_compra
margen_real = (ganancia_neta / precio_venta) if precio_venta > 0 else 0.0

# --- DASHBOARD ---
res1, res2, res3 = st.columns(3)
res1.metric("GANANCIA NETA", f"$ {ganancia_neta:,.2f}")
res2.metric("MARGEN REAL", f"{margen_real:.2%}")
res3.metric("PVP SUGERIDO", f"$ {pvp_sugerido:,.0f}")

if margen_real < (margen_objetivo/100):
    st.warning(f"Tu margen actual ({margen_real:.1%}) es menor al objetivo del {margen_objetivo}%.")
else:
    st.success(f"¡Excelente! Superas el margen objetivo.")

with st.expander("📄 Detalle de Gastos"):
    df = pd.DataFrame({
        "Concepto": ["Costo Mercadería", "Comisión MeLi", "Costo Fijo", "Envío", "Impuestos (IVA/IIBB)", "Financiación", "Otros"],
        "Monto": [costo_compra, comision_real, costo_fijo_real, costo_envio_final, iva_real + iibb_real, finan_real, otros_costos]
    })
    st.table(df.style.format({"Monto": "${:,.2f}"}))
