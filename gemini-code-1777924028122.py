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

# --- DICCIONARIO DE COSTOS DE ENVÍO (Precios de Lista Mayo 2026) ---
# Estos valores son los que cobra MeLi antes de aplicar descuentos por reputación.
tarifario_envios = {
    "0.5 kg (Sobres/Pequeños)": 4800.0,
    "1 kg": 5200.0,
    "2 kg": 5900.0,
    "5 kg": 7400.0,
    "10 kg": 9800.0,
    "15 kg": 12500.0,
    "20 kg": 15200.0,
    "25 kg": 18400.0,
    "30 kg (Límite Máximo)": 22000.0,
    "Especial (Muebles/Línea Blanca)": 35000.0
}

with col3:
    st.subheader("📦 Logística y Peso")
    # Selector de peso basado en información pública de MeLi
    categoria_peso = st.selectbox("Peso Facturable (Real o Volumétrico)", list(tarifario_envios.keys()))
    costo_lista_envio = tarifario_envios[categoria_peso]
    
    # Checkbox automático para envío gratis (Obligatorio > $33.000)
    envio_gratis_req = precio_venta >= 33000
    ofrece_envio_gratis = st.checkbox("Ofrecer Envío Gratis", value=envio_gratis_req)
    
    # Cálculo del subsidio según reputación
    if ofrece_envio_gratis:
        if reputacion == "Verde (50%)": 
            descuento = 0.50
        elif reputacion == "Amarilla/Sin Medalla (40%)": 
            descuento = 0.40
        else: 
            descuento = 0.0
            
        envio_final = costo_lista_envio * (1 - descuento)
        st.caption(f"Costo de lista: ${costo_lista_envio:,.0f}")
        st.write(f"**Tu costo de envío:** ${envio_final:,.2f}")
    else:
        envio_final = 0.0
        st.info("El envío lo paga el comprador.")

# --- LÓGICA DE PESO VOLUMÉTRICO (Ayuda para el usuario) ---
with st.expander("¿Cómo calcular el peso volumétrico?"):
    st.write("Si el producto es liviano pero grande, MeLi aplica esta fórmula:")
    col_dim1, col_dim2, col_dim3 = st.columns(3)
    largo = col_dim1.number_input("Largo (cm)", value=50)
    ancho = col_dim2.number_input("Ancho (cm)", value=40)
    alto = col_dim3.number_input("Alto (cm)", value=30)
    
    volumetrico = (largo * ancho * alto) / 4000 # Coeficiente estándar MeLi
    st.info(f"Peso Volumétrico: **{volumetrico:.2f} kg**. Usá el mayor entre este y el peso real.")


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
