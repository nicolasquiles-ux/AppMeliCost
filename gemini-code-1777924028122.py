import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Calculadora Meli Profit", layout="centered")

# Estilos de alto contraste optimizados para dispositivos móviles
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; color: #111111; }
    h1, h2, h3 { color: #004b93; font-weight: bold; }
    .stNumberInput, .stSelectbox, .stSlider { border-radius: 6px !important; }
    .metric-box {
        background-color: #ffffff;
        padding: 18px;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.08);
        border-left: 6px solid #004b93;
        margin-bottom: 15px;
    }
    .table { font-size: 16px; }
    </style>
""", unsafe_allow_html=True)

st.title("Calculadora de Rentabilidad")
st.subheader("Mercado Libre Argentina — Sistema Integrado")

st.markdown("---")

# --- SECCIÓN DE ENTRADAS (PANEL LATERAL u ORGANIZADO) ---
st.sidebar.header("1. Costos y Precio del Producto")
precio_venta = st.sidebar.number_input("Precio de Venta Publicado ($)", min_value=0.0, value=50000.0, step=100.0)
costo_producto = st.sidebar.number_input("Costo de Adquisición / Fábrica ($)", min_value=0.0, value=22000.0, step=100.0)
costo_envio = st.sidebar.number_input("Costo de Envío / Logística ($)", min_value=0.0, value=0.0, step=50.0)

st.sidebar.header("2. Cargos de la Plataforma")
cargo_vender_pct = st.sidebar.slider("Cargo por Vender o Comisión Clásica/Premium (%)", min_value=11.62, max_value=17.75, value=15.0, step=0.01)

# Lógica automatizada para productos menores a $33.000
costo_fijo = 0.0
if precio_venta < 33000 and precio_venta > 0:
    costo_fijo = st.sidebar.number_input("Costo Fijo por unidad (< $33.000)", min_value=0.0, value=900.0, step=10.0)
    st.sidebar.info("Aplica costo fijo obligatorio por unidad en productos menores a $33.000.")

st.sidebar.header("3. Estrategia de Financiación")
tipo_cuota = st.sidebar.radio(
    "Seleccioná la opción de cuotas:",
    ["Cuotas con interés bajo", "Cuotas al mismo precio"]
)

costo_financiero_pct = 0.0
detalle_cuotas = ""

if tipo_cuota == "Cuotas con interés bajo":
    costo_financiero_pct = 5.0
    detalle_cuotas = "3 a 12 cuotas (Fijo)"
else:
    opciones_mismo_precio = {
        "3 cuotas | Pagás 8,40%": 8.40,
        "6 cuotas | Pagás 12,30%": 12.30,
        "9 cuotas | Pagás 15,70%": 15.70,
        "12 cuotas | Pagás 19,20%": 19.20
    }
    seleccion = st.sidebar.selectbox("Plazo de cuotas ofrecido:", list(opciones_mismo_precio.keys()))
    costo_financiero_pct = opciones_mismo_precio[seleccion]
    detalle_cuotas = seleccion.split("|")[0].strip()

st.sidebar.header("4. Estructura Impositiva")
descuenta_iva = st.sidebar.checkbox("Descontar IVA (21%) sobre precio de lista", value=True)
descuenta_iibb = st.sidebar.checkbox("Descontar Ingresos Brutos (5.5%)", value=True)

# --- NÚCLEO DE CÁLCULOS FINANCIEROS ---
# 1. Comisiones directas
comision_meli = precio_venta * (cargo_vender_pct / 100)
costo_cuotas = precio_venta * (costo_financiero_pct / 100)

# 2. Impuestos calculados sobre la transacción (Deducción del precio bruto)
iva_monto = (precio_venta - (precio_venta / 1.21)) if descuenta_iva else 0.0
iibb_monto = (precio_venta * 0.055) if descuenta_iibb else 0.0
total_impuestos = iva_monto + iibb_monto

# 3. Retribución final (Mano neta de la plataforma antes del costo del producto)
mano_neta = precio_venta - comision_meli - costo_cuotas - costo_fijo - costo_envio - total_impuestos

# 4. Rentabilidad Absoluta y Relativa
ganancia_neta = mano_neta - costo_producto
margen_neto_pct = (ganancia_neta / precio_venta) * 100 if precio_venta > 0 else 0.0

# --- INTERFAZ DE RESULTADOS PRINCIPALES ---
col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    <div class="metric-box">
        <p style='margin:0; font-size:14px; color:#555555; font-weight:bold;'>Mano Neta (En cuenta)</p>
        <h2 style='margin:0; color:#004b93;'>$ {mano_neta:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)

with col2:
    color_margen = "#2e7d32" if ganancia_neta > 0 else "#c62828"
    st.markdown(f"""
    <div class="metric-box" style="border-left-color: {color_margen};">
        <p style='margin:0; font-size:14px; color:#555555; font-weight:bold;'>Ganancia Neta Final</p>
        <h2 style='margin:0; color:{color_margen};'>$ {ganancia_neta:,.2f} ({margen_neto_pct:.2f}%)</h2>
    </div>
    """, unsafe_allow_html=True)

# --- TABLA DE DESGLOSE COMPLETO ---
st.write("### Desglose de Retenciones y Costos")

desglose_datos = {
    "Concepto / Componente": [
        "Precio de Venta Original",
        f"Cargo por Vender Meli ({cargo_vender_pct}%)",
        f"Costo por Ofrecer Cuotas ({tipo_cuota} - {detalle_cuotas})",
        "Costo Fijo por Unidad (< $33.000)",
        "Logística y Envío",
        "Deducción IVA (21%)",
        "Deducción Ingresos Brutos (5.5%)",
        "Costo de Adquisición del Producto"
    ],
    "Impacto Financiero": [
        f"$ {precio_venta:,.2f}",
        f"- $ {comision_meli:,.2f}",
        f"- $ {costo_cuotas:,.2f}",
        f"- $ {costo_fijo:,.2f}",
        f"- $ {costo_envio:,.2f}",
        f"- $ {iva_monto:,.2f}",
        f"- $ {iibb_monto:,.2f}",
        f"- $ {costo_producto:,.2f}"
    ]
}

df_desglose = pd.DataFrame(desglose_datos)
st.table(df_desglose)

# Alerta condicional en caso de margen negativo
if ganancia_neta < 0:
    st.error("⚠️ Alerta: La configuración actual genera pérdidas financieras. Revisá el precio de lista o el esquema de cuotas.")
elif margen_neto_pct < 15:
    st.warning("⚠️ Atención: El margen neto está por debajo del 15%. Asegurate de que el volumen compense la operación.")
else:
    st.success("✅ Estructura comercial óptima y rentable.")
