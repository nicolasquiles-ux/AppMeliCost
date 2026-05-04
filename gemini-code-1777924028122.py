import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURACIÓN ESTÉTICA ---
st.set_page_config(page_title="MeLi Pro Analytics", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 MeLi Profit Dashboard Pro")
st.caption("Herramienta de análisis de rentabilidad para vendedores avanzados")

# --- SIDEBAR: CONFIGURACIÓN GLOBAL ---
with st.sidebar:
    st.header("⚙️ Configuración")
    tipo_vendedor = st.radio("Condición ante el IVA", ["Responsable Inscripto", "Monotributista"])
    iibb = st.number_input("% Ingresos Brutos", value=3.5, step=0.1)
    costos_fijos_mensuales = st.number_input("Costos Fijos Mensuales (Sueldos, Alquiler, etc)", value=0)
    st.divider()
    st.info("Esta configuración se aplica a todos los cálculos.")

# --- PANEL PRINCIPAL: ENTRADA DE DATOS ---
col_in1, col_in2, col_in3, col_in4 = st.columns(4)

with col_in1:
    costo_articulo = st.number_input("Costo de Compra ($)", min_value=1.0, value=15000.0)
with col_in2:
    precio_venta = st.number_input("Precio de Venta ($)", min_value=1.0, value=35000.0)
with col_in3:
    comision_meli = st.selectbox("% Comisión MeLi", [10, 11, 13, 15, 27, 29], index=3)
with col_in4:
    envio_costo = st.number_input("Costo Envío ($)", value=4500.0)

# --- MOTOR DE CÁLCULO PRO ---
# 1. Ajuste de IVA
if tipo_vendedor == "Responsable Inscripto":
    iva_venta = precio_venta - (precio_venta / 1.21)
    precio_neto_iva = precio_venta / 1.21
    # Asumimos que el costo_articulo que ingresó ya es sin IVA
else:
    iva_venta = 0
    precio_neto_iva = precio_venta

# 2. Cargos MeLi (Actualizados Mayo 2026)
cargo_fijo = 0
if precio_venta < 16000: cargo_fijo = 1255
elif precio_venta < 24000: cargo_fijo = 2500
elif precio_venta < 33000: cargo_fijo = 3030

comision_pesos = precio_venta * (comision_meli / 100)
impuestos_iibb = precio_neto_iva * (iibb / 100)

# 3. Resultado Final
total_gastos = comision_pesos + cargo_fijo + envio_costo + iva_venta + impuestos_iibb
ganancia_neta = precio_venta - total_gastos - costo_articulo
margen_pro = (ganancia_neta / precio_venta) * 100

# --- VISUALIZACIÓN DE RESULTADOS ---
st.divider()
m1, m2, m3, m4 = st.columns(4)
m1.metric("Ganancia Neta", f"$ {ganancia_neta:,.2f}")
m2.metric("Margen sobre Venta", f"{margen_pro:.2f}%")
m3.metric("Punto de Equilibrio", f"$ {costo_articulo + total_gastos:,.0f}")
m4.metric("Markup", f"{((precio_venta/costo_articulo)-1)*100:.1f}%")

# --- GRÁFICOS ---
col_chart1, col_chart2 = st.columns([1, 1])

with col_chart1:
    st.subheader("Distribución del Ingreso")
    df_pie = pd.DataFrame({
        "Concepto": ["Costo Producto", "Comisión MeLi", "Envío", "Impuestos (IVA/IIBB)", "Ganancia Neta"],
        "Valores": [costo_articulo, comision_pesos + cargo_fijo, envio_costo, iva_venta + impuestos_iibb, max(0, ganancia_neta)]
    })
    fig = px.pie(df_pie, values='Valores', names='Concepto', hole=.4, 
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig, use_container_width=True)

with col_chart2:
    st.subheader("Análisis de Sensibilidad")
    st.write("¿Qué pasa si cambiás el precio?")
    precios_sim = [precio_venta * 0.9, precio_venta, precio_venta * 1.1, precio_venta * 1.2]
    ganancias_sim = [p - (total_gastos * (p/precio_venta)) - costo_articulo for p in precios_sim]
    df_line = pd.DataFrame({"Precio": precios_sim, "Ganancia": ganancias_sim})
    st.line_chart(df_line.set_index("Precio"))
    st.success(f"Estás ganando ${ganancia_final:,.2f} por cada venta.")
else:
    st.error("¡Cuidado! Esta operación da pérdida.")
