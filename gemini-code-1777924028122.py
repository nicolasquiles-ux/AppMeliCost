import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="MeLi Pro Analytics", layout="wide")

# Estilos CSS para mejorar la UI
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 MeLi Profit Dashboard Pro")
st.caption("Herramienta de análisis de rentabilidad para vendedores avanzados")

# 2. SIDEBAR: CONFIGURACIÓN
with st.sidebar:
    st.header("⚙️ Configuración")
    tipo_vendedor = st.radio("Condición ante el IVA", ["Responsable Inscripto", "Monotributista"])
    iibb = st.number_input("% Ingresos Brutos", value=3.5, step=0.1)
    st.divider()
    st.info("Configurá tus impuestos para cálculos precisos.")

# 3. ENTRADA DE DATOS
col_in1, col_in2, col_in3, col_in4 = st.columns(4)

with col_in1:
    costo_prod = st.number_input("Costo de Compra ($)", min_value=0.0, value=15000.0)
with col_in2:
    pvp = st.number_input("Precio de Venta ($)", min_value=1.0, value=35000.0)
with col_in3:
    comision_meli_pct = st.selectbox("% Comisión MeLi", [10, 11, 13, 15, 27, 29], index=3)
with col_in4:
    costo_envio = st.number_input("Costo Envío ($)", value=4500.0)

# 4. MOTOR DE CÁLCULO (Lógica Corregida)
# Costo Fijo MeLi Argentina 2026
costo_fijo = 0
if pvp < 16000: costo_fijo = 1255
elif pvp < 24000: costo_fijo = 2500
elif pvp < 33000: costo_fijo = 3030

# Ajuste de IVA
if tipo_vendedor == "Responsable Inscripto":
    iva_venta = pvp - (pvp / 1.21)
    pvp_neto_iva = pvp / 1.21
else:
    iva_venta = 0
    pvp_neto_iva = pvp

costo_comision = pvp * (comision_meli_pct / 100)
costo_iibb = pvp_neto_iva * (iibb / 100)

# Resultado Final
total_gastos = costo_comision + costo_fijo + costo_envio + iva_venta + costo_iibb
ganancia_final = pvp - total_gastos - costo_prod
margen_neto = (ganancia_final / pvp) * 100 if pvp > 0 else 0

# 5. VISUALIZACIÓN
st.divider()
m1, m2, m3, m4 = st.columns(4)
m1.metric("Ganancia Neta", f"$ {ganancia_final:,.2f}")
m2.metric("Margen Real", f"{margen_neto:.2f}%")
m3.metric("Costo Fijo MeLi", f"$ {costo_fijo}")
m4.metric("Impuestos totales", f"$ {iva_venta + costo_iibb:,.2f}")

# Alertas Dinámicas
if ganancia_final > 0:
    st.success(f"### ✅ ¡Operación Rentable! Estás ganando ${ganancia_final:,.2f} por venta.")
else:
    st.error(f"### ⚠️ Alerta de Pérdida: ${ganancia_final:,.2f}")
    st.warning("Tu estructura de costos supera el precio de venta.")

# Gráfico de Torta
st.subheader("Distribución de cada peso cobrado")
df_pie = pd.DataFrame({
    "Concepto": ["Costo Producto", "Comisión MeLi", "Envío", "Impuestos", "Ganancia"],
    "Valores": [costo_prod, costo_comision + costo_fijo, costo_envio, iva_venta + costo_iibb, max(0, ganancia_final)]
})
fig = px.pie(df_pie, values='Valores', names='Concepto', hole=.4)
st.plotly_chart(fig, use_container_width=True)
