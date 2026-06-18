import streamlit as st

# =====================================================================
# 1. CONFIGURACIÓN DE LA PÁGINA Y ESTILOS
# =====================================================================
st.set_page_config(
    page_title="Calculadora de Rentabilidad - Mercado Libre",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Forzar contraste y diseño limpio
st.markdown("""
    <style>
    .reportview-container { background: #f0f2f6; }
    .metric-box {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# 2. ESTRUCTURA DE DATOS: TABLA DE LOGÍSTICA (Vigente)
# =====================================================================
# Formato: (peso_min, peso_max): [costo_menos_33k, costo_33k_a_50k, costo_mas_50k]
TABLA_LOGISTICA = {
    (0.0, 0.3): [7868, 5620, 6080],
    (0.3, 0.5): [8596, 6140, 6600],
    (0.5, 1.0): [9800, 7000, 7470],
    (1.0, 1.5): [10122, 7230, 7720],
    (1.5, 2.0): [10458, 7470, 7970],
    (2.0, 3.0): [11550, 8250, 8710],
    (3.0, 4.0): [12866, 9190, 9860],
    (4.0, 5.0): [14070, 10050, 10760],
    (5.0, 8.0): [15512, 11080, 11830],
    (8.0, 10.0): [16926, 12090, 12840],
    (10.0, 13.0): [18270, 13050, 13920],
    (13.0, 15.0): [19684, 14060, 14930],
    (15.0, 20.0): [23506, 16790, 17830],
    (20.0, 25.0): [28182, 20130, 21420],
    (25.0, 30.0): [38780, 27700, 29410],
    (30.0, 40.0): [44268, 31620, 33570],
    (40.0, 50.0): [46802, 33430, 35490],
    (50.0, 60.0): [51996, 37140, 39610],
    (60.0, 70.0): [54068, 38620, 41290],
    (70.0, 80.0): [62524, 44660, 47850],
    (80.0, 90.0): [77308, 55220, 59180],
    (90.0, 100.0): [89152, 63680, 68230],
    (100.0, 120.0): [97328, 69520, 74490],
    (120.0, 140.0): [109592, 78280, 83890],
    (140.0, 160.0): [121870, 87050, 93280],
    (160.0, 180.0): [134120, 95800, 102660],
    (180.0, float('inf')): [146398, 104570, 112060]
}

def calcular_costo_envio(precio_venta, peso):
    if precio_venta < 33000:
        columna_idx = 0  # Menos de $33.000 (30% OFF aplicado)
    elif 33000 <= precio_venta < 50000:
        columna_idx = 1  # De $33.000 a $49.999 (50% OFF aplicado)
    else:
        columna_idx = 2  # Más de $50.000 (50% OFF aplicado)
        
    for (peso_min, peso_max), costos in TABLA_LOGISTICA.items():
        if peso_min < peso <= peso_max:
            return costos[columna_idx]
    return 0

# =====================================================================
# 3. INTERFAZ DE USUARIO (INGRESOS DE DATOS)
# =====================================================================
st.title("📊 Simulador de Rentabilidad Meli")

st.sidebar.header("🔧 Costos del Producto")
costo_producto = st.sidebar.number_input("Costo del Producto ($)", min_value=0.0, value=10000.0, step=500.0)
peso_producto = st.sidebar.number_input("Peso del Producto (kg)", min_value=0.0, value=1.5, step=0.1)

st.sidebar.header("📈 Configuración de Venta")
precio_venta = st.sidebar.number_input("Precio de Venta Final ($)", min_value=0.0, value=35000.0, step=1000.0)

# Tipo de publicación
tipo_publicacion = st.sidebar.selectbox("Tipo de Publicación", ["Clásica", "Premium"])
comision_base_pct = 13.0 if tipo_publicacion == "Clásica" else 28.0
comision_plataforma = st.sidebar.number_input("Comisión de Plataforma (%)", min_value=0.0, max_value=100.0, value=comision_base_pct)

# Financiación / Cuotas fijas (Modificable manualmente)
st.sidebar.header("💳 Financiación")
aplicar_financiacion = st.sidebar.checkbox("Incluye costo de cuotas fijas (Ahora/Meli)")
pct_financiacion = 0.0
if aplicar_financiacion:
    pct_financiacion = st.sidebar.number_input("Porcentaje de costo financiero (%)", min_value=0.0, max_value=100.0, value=12.0, step=0.5)

# Impuestos
st.sidebar.header("🏛️ Impuestos y Retenciones")
pct_iibb = st.sidebar.number_input("Ingresos Brutos (%)", min_value=0.0, max_value=100.0, value=5.5, step=0.1)
incluye_iva = st.sidebar.checkbox("Descontar IVA (21%)", value=True)

# =====================================================================
# 4. CÁLCULOS FINANCIEROS
# =====================================================================
# 1. Envío
costo_envio = calcular_costo_envio(precio_venta, peso_producto)

# En Mercado Libre, si el producto vale menos de $33.000, el envío lo paga el comprador o se suma un cargo fijo.
# Si es >= $33.000 el envío es obligatorio gratuito para el comprador (lo absorbe el vendedor).
envio_gratis = precio_venta >= 33000

# Cargo fijo por unidad si aplica (habitual en productos de bajo precio)
cargo_fijo = 0.0
if precio_venta < 33000:
    cargo_fijo = 1200.0  # Valor de referencia estándar para cargos fijos menores a 33k

# Descuentos de plataforma y financieros
monto_comision = precio_venta * (comision_plataforma / 100.0)
monto_financiacion = precio_venta * (pct_financiacion / 100.0)

# Base imponible y retenciones
monto_iibb = precio_venta * (pct_iibb / 100.0)
monto_iva = 0.0
if incluye_iva:
    # El IVA se calcula sobre el precio de venta neto de IVA
    monto_iva = precio_venta - (precio_venta / 1.21)

# Egreso Total de Operación
total_costos_plataforma = monto_comision + monto_financiacion + cargo_fijo
if envio_gratis:
    total_costos_plataforma += costo_envio

total_impuestos = monto_iibb + monto_iva

# Neto recibido de la venta
ingreso_neto_plataforma = precio_venta - total_costos_plataforma - total_impuestos

# Rentabilidad Absoluta y Margen
ganancia_neta = ingreso_neto_plataforma - costo_producto
margen_neto = (ganancia_neta / precio_venta) * 100 if precio_venta > 0 else 0.0

# =====================================================================
# 5. RETORNO VISUAL EN LA APP
# =====================================================================
# Panel Principal de Métricas
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Ganancia Neta", value=f"${ganancia_neta:,.2f}", delta=f"{margen_neto:.2f}% Margen")
with col2:
    st.metric(label="Costo de Envío", value=f"${costo_envio:,.2f}", delta="Obligatorio" if envio_gratis else "A cargo comprador")
with col3:
    st.metric(label="Neto a Cobrar", value=f"${ingreso_neto_plataforma:,.2f}")

# Desglose de Gastos
st.subheader("📋 Desglose del Análisis de Costos")

A, B = st.columns(2)
with A:
    st.markdown("**Plataforma y Logística:**")
    st.write(f"- Comisión Meli ({comision_plataforma}%): `${monto_comision:,.2f}`")
    st.write(f"- Costo Financiero ({pct_financiacion}%): `${monto_financiacion:,.2f}`")
    st.write(f"- Cargo fijo por unidad: `${cargo_fijo:,.2f}`")
    st.write(f"- Costo Logístico asignado: `${costo_envio:,.2f}`")

with B:
    st.markdown("**Estructura Fiscal:**")
    st.write(f"- IVA (21%): `${monto_iva:,.2f}`")
    st.write(f"- Ingresos Brutos ({pct_iibb}%): `${monto_iibb:,.2f}`")
    st.write(f"- Total impuestos retenidos: `${total_impuestos:,.2f}`")

# Botón de monetización / Contacto comercial
st.markdown("---")
col_btn1, col_btn2 = st.columns([2, 1])
with col_btn1:
    st.caption("¿Necesitás agregar integraciones masivas, actualización automática de costos por lista o CRM?")
with col_btn2:
    st.link_button("💬 Hablar con Soporte", "https://wa.me/tu_numero_de_whatsapp")
