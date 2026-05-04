import streamlit as st

# Configuración de página
st.set_page_config(page_title="Calculadora Pro MeLi", layout="centered")

st.title("🚀 MeLi Profit Calculator")
st.markdown("### Calcula tu rentabilidad neta real (Post-Impuestos)")

with st.sidebar:
    st.header("Configuración de Costos")
    iva_tipo = st.selectbox("Tu Condición Fiscal", ["Responsable Inscripto", "Monotributista"])
    iibb_tax = st.slider("% Ingresos Brutos", 0.0, 5.0, 3.5)
    
st.subheader("Datos del Producto")
col1, col2 = st.columns(2)

with col1:
    pvp = st.number_input("Precio de Venta (PVP)", min_value=0.0, value=35000.0)
    costo_prod = st.number_input("Costo del Producto (Sin IVA)", min_value=0.0, value=15000.0)

with col2:
    comision_pct = st.number_input("% Comisión MeLi (Clásica/Premium)", min_value=0.0, value=15.0)
    costo_envio = st.number_input("Costo de Envío (Si aplica)", min_value=0.0, value=4500.0)

# LÓGICA DE CÁLCULO
# 1. Costo Fijo por unidad (MeLi Argentina 2026)
costo_fijo = 0
if pvp < 16000: costo_fijo = 1255
elif pvp < 24000: costo_fijo = 2500
elif pvp < 33000: costo_fijo = 3030

# 2. Cálculo de IVA (Detracción)
if iva_tipo == "Responsable Inscripto":
    pvp_neto_iva = pvp / 1.21
    iva_a_pagar = pvp - pvp_neto_iva
else:
    pvp_neto_iva = pvp
    iva_a_pagar = 0

# 3. Comisiones e Impuestos
costo_comision = pvp * (comision_pct / 100)
costo_iibb = pvp_neto_iva * (iibb_tax / 100)

# 4. Resultado Final
ingreso_limpio = pvp - costo_comision - costo_fijo - costo_envio - iva_a_pagar - costo_iibb
ganancia_final = ingreso_limpio - costo_prod
margen_neto = (ganancia_final / pvp) * 100

# INTERFAZ DE RESULTADOS
st.divider()
c1, c2, c3 = st.columns(3)
c1.metric("Ganancia Neta", f"${ganancia_final:,.2f}")
c2.metric("Margen Real", f"{margen_neto:.1f}%")
c3.metric("Costo Fijo", f"${costo_fijo}")

if ganancia_final > 0:
    st.success(f"Estás ganando ${ganancia_final:,.2f} por cada venta.")
else:
    st.error("¡Cuidado! Esta operación da pérdida.")