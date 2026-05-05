import streamlit as st
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="MeLi Pro Analytics", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #eee; }
    .css-1r6slb0 { background-color: #f1f3f6; border-radius: 10px; padding: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 MeLi Dashboard Pro")
st.caption("Estructura de Costos, Logística y Cuotas - Mayo 2026")

# --- DATA DE REFERENCIA ---
tarifario_envios = {
    "0.5 kg (Sobres)": 4800.0, "1 kg": 5200.0, "2 kg": 5900.0, "5 kg": 7400.0,
    "10 kg": 9800.0, "15 kg": 12500.0, "20 kg": 15200.0, "25 kg": 18400.0,
    "30 kg (Límite)": 22000.0, "Especial (Muebles)": 35000.0
}

# Tasas de Cuota Simple / Financiación (Valores estimados Mayo 2026)
tasas_financiacion = {
    "1 Pago (Sin costo extra)": 0.0,
    "3 Cuotas (Cuota Simple)": 12.5,
    "6 Cuotas (Cuota Simple)": 23.8,
    "9 Cuotas": 35.2,
    "12 Cuotas": 46.5
}

# --- SIDEBAR CONFIG ---
with st.sidebar:
    st.header("⚙️ Configuración Fiscal")
    reputacion = st.selectbox("Tu Reputación", ["Verde (50%)", "Amarilla/Sin Medalla (40%)", "Roja/Naranja (0%)"])
    tipo_vendedor = st.radio("Condición IVA", ["Responsable Inscripto", "Monotributista"])
    iibb_tax = st.number_input("% Ingresos Brutos", value=3.5)
    st.divider()
    st.info("💡 El simulador calcula el retorno neto después de impuestos y comisiones.")

# --- CUERPO PRINCIPAL ---
col_prod, col_envio, col_finan = st.columns([1, 1, 1.2])

with col_prod:
    st.subheader("💰 Producto")
    costo_compra = st.number_input("Costo de Compra ($)", min_value=0.0, value=15000.0)
    precio_venta = st.number_input("Precio de Venta ($)", min_value=0.0, value=35000.0)
    comision_base = st.number_input("% Comisión MeLi (Clásica)", value=15.0)
    otros_costos = st.number_input("Otros Gastos ($)", value=0.0)

with col_envio:
    st.subheader("📦 Envío Visible")
    peso_sel = st.selectbox("Peso del Producto", list(tarifario_envios.keys()))
    costo_lista = tarifario_envios[peso_sel]
    
    ofrece_gratis = st.checkbox("Envío Gratis", value=(precio_venta >= 33000))
    
    # Cálculo subsidio
    dcto = 0.50 if reputacion == "Verde (50%)" else (0.40 if "Amarilla" in reputacion else 0.0)
    costo_envio_final = costo_lista * (1 - dcto) if ofrece_gratis else 0.0
    
    st.metric("Tu Costo de Envío", f"$ {costo_envio_final:,.2f}")
    st.caption(f"Costo de lista: ${costo_lista:,.0f} (Ahorras {dcto*100:.0f}%)")

with col_finan:
    st.subheader("💳 Financiación")
    tipo_pub = st.radio("Publicación", ["Clásica", "Premium (Incluye 6 cuotas)"])
    
    if tipo_pub == "Clásica":
        st.write("¿Ofreces cuotas vos?")
        plan_cuotas = st.selectbox("Plan de Cuotas", list(tasas_financiacion.keys()))
        costo_finan_pct = tasas_financiacion[plan_cuotas]
    else:
        st.info("La publicación Premium ya incluye el costo de 6 cuotas en su comisión (aprox 29-31%).")
        costo_finan_pct = 0.0 # Se asume integrado en la comisión que el usuario ponga a la izquierda

# --- MOTOR DE CÁLCULO ---
costo_fijo_meli = 0.0
if 0 < precio_venta < 16000: costo_fijo_meli = 1255.0
elif 16000 <= precio_venta < 24000: costo_fijo_meli = 2500.0
elif 24000 <= precio_venta < 33000: costo_fijo_meli = 3030.0

# Impuestos
if tipo_vendedor == "Responsable Inscripto":
    iva_venta = precio_venta - (precio_venta / 1.21)
    base_iibb = precio_venta / 1.21
else:
    iva_venta = 0.0
    base_iibb = precio_venta

costo_iibb = base_iibb * (iibb_tax / 100)
costo_comision = precio_venta * (comision_base / 100)
costo_finan_total = precio_venta * (costo_finan_pct / 100)

# TOTALES
gastos_totales = costo_comision + costo_fijo_meli + costo_envio_final + iva_venta + costo_iibb + otros_costos + costo_finan_total
ganancia_neta = precio_venta - gastos_totales - costo_compra
margen_neta = (ganancia_neta / precio_venta) if precio_venta > 0 else 0.0

# --- DASHBOARD DE RESULTADOS ---
st.divider()
res1, res2, res3 = st.columns(3)

res1.metric("GANANCIA NETA", f"$ {ganancia_neta:,.2f}", delta=f"{margen_neta:.2%}")
res2.metric("GASTOS TOTALES", f"$ {gastos_totales:,.2f}")
res3.metric("RETORNO (ROI)", f"{((ganancia_neta/costo_compra)*100 if costo_compra > 0 else 0):,.1f}%")

if ganancia_neta > 0:
    st.success(f"✅ ¡Negocio Saludable! Ganás ${ganancia_neta:,.2f} por unidad.")
else:
    st.error(f"⚠️ Alerta: Estás perdiendo ${abs(ganancia_neta):,.2f}.")

# --- DESGLOSE FINAL ---
with st.expander("📄 Ver Detalle de la Liquidación"):
    df_final = pd.DataFrame({
        "Concepto": ["Costo Mercadería", "Comisión ML", "Cargo Fijo", "Envío", "Financiación (Cuotas)", "IVA", "IIBB", "Otros"],
        "Monto": [costo_compra, costo_comision, costo_fijo_meli, costo_envio_final, costo_finan_total, iva_venta, costo_iibb, otros_costos]
    })
    st.table(df_final.style.format({"Monto": "${:,.2f}"}))
