import streamlit as st
import pandas as pd

# CONFIGURACIÓN
st.set_page_config(page_title="MeLi Pro Analytics", layout="wide")

st.title("📊 MeLi Profit Dashboard Pro")
st.caption("Estructura de costos actualizada - Mayo 2026")

# --- SIDEBAR: CONFIGURACIÓN FISCAL Y REPUTACIÓN ---
with st.sidebar:
    st.header("⚙️ Configuración del Vendedor")
    reputacion = st.selectbox("Tu Reputación (Descuento Envío)", 
                              ["Verde (50%)", "Amarilla/Sin Medalla (40%)", "Roja/Naranja (0%)"])
    tipo_vendedor = st.radio("Condición Fiscal", ["Responsable Inscripto", "Monotributista"])
    iibb = st.number_input("% Ingresos Brutos", value=3.5)
    st.divider()
    st.info("El descuento de envío se aplica automáticamente si el producto supera los $33.000.")

# --- ENTRADA DE DATOS ---
col1, col2, col3 = st.columns(3)

with col1:
    costo_prod = st.number_input("Costo de Compra ($)", min_value=0.0, value=15000.0)
    precio_venta = st.number_input("Precio de Venta ($)", min_value=1.0, value=35000.0)

with col2:
    tipo_pub = st.selectbox("Tipo de Publicación", ["Clásica", "Premium (Cuotas)"])
    if tipo_pub == "Clásica":
        comision_pct = st.number_input("% Comisión", value=15.0)
        costo_financiacion = 0.0
    else:
        comision_pct = st.number_input("% Comisión", value=29.0) # Promedio Premium
        st.caption("La publicación Premium ya incluye financiación.")
        costo_financiacion = 0.0 # Ya está en la comisión

    # Nuevo Campo: Otros Costos
    otros_costos = st.number_input("Otros Costos (Embalaje, Impuestos extra, etc.)", value=0.0, help="Suma aquí cualquier gasto adicional por unidad.")

with col3:
    # Lógica de Envío Pro
    envio_gratis = st.checkbox("Ofrecer Envío Gratis", value=(precio_venta >= 33000))
    costo_base_envio = st.number_input("Costo de Envío de Lista ($)", value=6500.0 if envio_gratis else 0.0)
    
    # Aplicar subsidio por reputación
    if envio_gratis:
        if reputacion == "Verde (50%)": dcto = 0.50
        elif reputacion == "Amarilla/Sin Medalla (40%)": dcto = 0.40
        else: dcto = 0.0
        envio_final = costo_base_envio * (1 - dcto)
    else:
        envio_final = 0.0
    
    st.write(f"**Envío a cargo del vendedor:** ${envio_final:,.2f}")

# --- MOTOR DE CÁLCULO ---

# 1. Costo Fijo (Ventas < $33.000)
costo_fijo = 0
if precio_venta < 16000: costo_fijo = 1255
elif precio_venta < 24000: costo_fijo = 2500
elif precio_venta < 33000: costo_fijo = 3030

# 2. Impuestos
if tipo_vendedor == "Responsable Inscripto":
    iva_venta = precio_venta - (precio_venta / 1.21)
    base_iibb = precio_venta / 1.21
else:
    iva_venta = 0
    base_iibb = precio_venta

total_iibb = base_iibb * (iibb / 100)
comision_pesos = precio_venta * (comision_pct / 100)

# 3. Resultado Final
total_gastos = comision_pesos + costo_fijo + envio_final + iva_venta + total_iibb + otros_costos
ganancia_neta = precio_venta - total_gastos - costo_prod
margen_neto = (ganancia_neta / precio_venta) * 100

# --- RESULTADOS VISUALES ---
st.divider()
c1, c2, c3 = st.columns(3)
c1.metric("Ganancia Neta", f"$ {ganancia_neta:,.2f}")
c2.metric("Margen Real", f"{margen_neto:.2f}%")
c3.metric("Gastos Totales", f"$ {total_gastos:,.2f}")

if ganancia_neta > 0:
    st.success(f"### Rentable: Ganas ${ganancia_neta:,.2f} por unidad.")
else:
    st.error(f"### Pérdida: Pierdes ${abs(ganancia_neta):,.2f}. Revisa tus costos.")

# --- DESGLOSE PARA EL CLIENTE ---
with st.expander("Ver desglose de costos detallado"):
    items = {
        "Costo Producto": costo_prod,
        "Comisión MeLi": comision_pesos,
        "Costo Fijo": costo_fijo,
        "Envío Final (con descuento)": envio_final,
        "IVA": iva_venta,
        "Ingresos Brutos": total_iibb,
        "Otros Costos": otros_costos
    }
    st.table(pd.DataFrame(items.items(), columns=["Concepto", "Monto ($)"]))
