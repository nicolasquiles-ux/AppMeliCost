import streamlit as st
import requests
import pandas as pd
import numpy as np

# ==============================================================================
# CONFIGURACIÓN GENERAL DE LA APLICACIÓN
# ==============================================================================
st.set_page_config(
    page_title="Centro Estant - Intelligence & Pricing App",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 24px;
        font-weight: bold;
        color: #1F497D;
    }
    .sub-header {
        font-size: 14px;
        color: #595959;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# DATOS MAESTROS Y PARÁMETROS FISCALES / LOGÍSTICOS
# ==============================================================================
ALICUOTA_IVA = 0.21
ALICUOTA_IIBB = 0.035
TOTAL_IMPUESTOS = ALICUOTA_IVA + ALICUOTA_IIBB  # 24.5%

# Comisiones y Tasas de Financiación Mercado Libre
TASAS_CUOTAS = {
    "1 Pago / Clásica": {"comision_base": 0.145, "tasa_finan": 0.000, "divisor": 1 - 0.145 - TOTAL_IMPUESTOS},
    "3 Cuotas Sin Interés": {"comision_base": 0.145, "tasa_finan": 0.085, "divisor": 1 - 0.230 - TOTAL_IMPUESTOS},
    "6 Cuotas Sin Interés": {"comision_base": 0.145, "tasa_finan": 0.129, "divisor": 1 - 0.274 - TOTAL_IMPUESTOS},
    "9 Cuotas Sin Interés": {"comision_base": 0.145, "tasa_finan": 0.173, "divisor": 1 - 0.318 - TOTAL_IMPUESTOS},
    "12 Cuotas Sin Interés": {"comision_base": 0.145, "tasa_finan": 0.208, "divisor": 1 - 0.353 - TOTAL_IMPUESTOS},
}

# Tabla de Tarifas de Mercado Envíos (Costo por bulto según peso y rango de PVP)
TARIFARIO_ME2 = [
    (0.3, 6790), (0.5, 7290), (1.0, 8290), (1.5, 8590), (2.0, 8790),
    (3.0, 9590), (4.0, 10890), (5.0, 11890), (8.0, 13090), (10.0, 14190),
    (13.0, 15190), (15.0, 16290), (20.0, 19390), (25.0, 23390), (30.0, 32090),
    (40.0, 36990), (50.0, 39090), (60.0, 43590), (70.0, 45490), (80.0, 52690),
    (90.0, 65190), (100.0, 75090), (120.0, 81990), (140.0, 92290), (160.0, 102690),
    (180.0, 112990), (999.0, 123290)
]

def obtener_costo_flete_unitario(peso_bulto_kg):
    for limite_peso, tarifa in TARIFARIO_ME2:
        if peso_bulto_kg <= limite_peso:
            return tarifa
    return 123290

# ==============================================================================
# FUNCIONES AUXILIARES DE API (CON CACHE CONTRA RECARGAS INFINITAS)
# ==============================================================================
@st.cache_data(ttl=1800)  # Evita loops de ejecución manteniendo datos 30 min en memoria
def consultar_api_publica_meli(query, seller_id, limit=50):
    url = "https://api.mercadolibre.com/sites/MLA/search"
    params = {"limit": limit}
    if query:
        params["q"] = query
    if seller_id:
        params["seller_id"] = seller_id
        
    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code == 200:
            data = res.json()
            results = data.get("results", [])
            parsed = []
            for item in results:
                parsed.append({
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "price": item.get("price", 0),
                    "sold_quantity": item.get("sold_quantity", 0),
                    "available_quantity": item.get("available_quantity", 0),
                    "seller_name": item.get("seller", {}).get("nickname", "N/D"),
                    "seller_id": item.get("seller", {}).get("id"),
                    "category_id": item.get("category_id"),
                    "listing_type_id": item.get("listing_type_id"),
                    "permalink": item.get("permalink")
                })
            return pd.DataFrame(parsed)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error de conexión con la API: {e}")
        return pd.DataFrame()

# ==============================================================================
# BARRA LATERAL (SIDEBAR)
# ==============================================================================
st.sidebar.image("https://www.mercadolibre.com.ar/pressed-logo/MLA/3.0.0", width=160)
st.sidebar.title("Centro Estant Control")
st.sidebar.markdown("---")

access_token = st.sidebar.text_input("🔑 Access Token MeLi (Opcional)", type="password")
if access_token:
    st.sidebar.success("Conectado con cuenta privada")
else:
    st.sidebar.info("Modo Datos Públicos Activo")

st.sidebar.markdown("---")
st.sidebar.caption("Parámetros Impositivos Vigentes:")
st.sidebar.text(f"• IVA: {ALICUOTA_IVA*100:.1f}%")
st.sidebar.text(f"• IIBB: {ALICUOTA_IIBB*100:.1f}%")
st.sidebar.text(f"• Total Deducción: {TOTAL_IMPUESTOS*100:.1f}%")

# ==============================================================================
# NAVEGACIÓN PRINCIPAL (TABS)
# ==============================================================================
tab1, tab2, tab3 = st.tabs([
    "📊 Monitor de Competencia (Real Time)",
    "🧮 Calculadora de Precios & Cuotas",
    "🚚 Matriz Logística & Bultos (ME2 vs ME1)"
])

# ------------------------------------------------------------------------------
# TAB 1: MONITOR DE COMPETENCIA Y RANKING TOP 15
# ------------------------------------------------------------------------------
with tab1:
    st.markdown('<div class="main-header">⚡ Monitor de Competencia & Control de Mercado</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Rastreo de sold_quantity y estimación de volumen de facturación vía API pública de Mercado Libre.</div>', unsafe_allow_html=True)
    
    col_c1, col_c2, col_c3 = st.columns([2, 2, 1])
    with col_c1:
        query_input = st.text_input("🔍 Buscar Producto / Término / SKU", value="Ropero 4 puertas")
    with col_c2:
        seller_input = st.text_input("🏢 ID Vendedor Competidor (Opcional)", placeholder="Ej: 12345678")
    with col_c3:
        limit_input = st.slider("Límite Muestra", 10, 50, 50)
        
    if query_input or seller_input:
        df_comp = consultar_api_publica_meli(query_input, seller_input, limit_input)
        
        if not df_comp.empty:
            df_comp["facturacion_estimada"] = df_comp["price"] * df_comp["sold_quantity"]
            
            # Métricas Generales
            k1, k2, k3 = st.columns(3)
            total_fact = df_comp["facturacion_estimada"].sum()
            k1.metric("Facturación Muestreada", f"${total_fact:,.0f}")
            k2.metric("Unidades Vendidas Muestreadas", f"{df_comp['sold_quantity'].sum():,}")
            k3.metric("Precio Promedio Mercado", f"${df_comp['price'].mean():,.0f}")
            
            st.markdown("---")
            
            # 1. Resumen por Categoría
            st.subheader("1. Ventas Estimadas por Categoría")
            cat_summary = df_comp.groupby("category_id").agg(
                Publicaciones=("id", "count"),
                Unidades_Vendidas=("sold_quantity", "sum"),
                Facturacion_Total=("facturacion_estimada", "sum"),
                Precio_Promedio=("price", "mean")
            ).reset_index()
            
            cat_summary["Cuota_%"] = (cat_summary["Facturacion_Total"] / total_fact * 100) if total_fact > 0 else 0
            
            st.dataframe(
                cat_summary,
                column_config={
                    "category_id": "ID Categoría",
                    "Publicaciones": st.column_config.NumberColumn("Publicaciones", format="%d"),
                    "Unidades_Vendidas": st.column_config.NumberColumn("Unidades Vendidas", format="%d"),
                    "Facturacion_Total": st.column_config.NumberColumn("Facturación Est. ($)", format="$%.0f"),
                    "Precio_Promedio": st.column_config.NumberColumn("Precio Prom. ($)", format="$%.0f"),
                    "Cuota_%": st.column_config.NumberColumn("Cuota Muestra (%)", format="%.1f%%")
                },
                use_container_width=True,
                hide_index=True
            )
            
            st.markdown("---")
            
            # 2. Ranking Top 15 Productos
            st.subheader("2. Ranking Top 15 Productos Más Vendidos")
            top_15 = df_comp.sort_values(by="sold_quantity", ascending=False).head(15).reset_index(drop=True)
            top_15.index += 1
            
            st.dataframe(
                top_15[["seller_name", "title", "price", "sold_quantity", "facturacion_estimada", "permalink"]],
                column_config={
                    "seller_name": "Vendedor / Competidor",
                    "title": "Título de Publicación",
                    "price": st.column_config.NumberColumn("PVP Actual ($)", format="$%.0f"),
                    "sold_quantity": st.column_config.NumberColumn("Ventas Acum. (`sold_quantity`)", format="%d"),
                    "facturacion_estimada": st.column_config.NumberColumn("Facturación Acum. Est. ($)", format="$%.0f"),
                    "permalink": st.column_config.LinkColumn("Enlace MeLi 🔗")
                },
                use_container_width=True
            )
        else:
            st.info("No se encontraron resultados en la consulta.")

# ------------------------------------------------------------------------------
# TAB 2: CALCULADORA DE PRECIOS & CUOTAS (DESPEJE INVERSO)
# ------------------------------------------------------------------------------
with tab2:
    st.markdown('<div class="main-header">🧮 Calculadora de Precios Sugeridos & Rentabilidad</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Cálculo exacto de PVP considerando comisiones de cuotas, 24.5% de impuestos y fletes por bulto.</div>', unsafe_allow_html=True)
    
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        st.subheader("Entradas de Producto y Costos")
        sku_code = st.text_input("SKU / Código del Producto", value="C141BL")
        costo_producto = st.number_input("Costo de Fabricación / Lista ($)", value=148840.0, step=1000.0)
        pvp_base_actual = st.number_input("PVP Base / Clásica Actual ($)", value=310433.0, step=1000.0)
        
        c_cajas, c_peso = st.columns(2)
        with c_cajas:
            cant_cajas = st.number_input("Cantidad de Cajas / Bultos", value=3, min_value=1, max_value=10)
        with c_peso:
            peso_total_kg = st.number_input("Peso Total Embalado (Kg)", value=125.0, min_value=0.5)

    # Cálculo Logístico Interno
    peso_unitario_kg = peso_total_kg / cant_cajas
    tarifa_flete_unitario = obtener_costo_flete_unitario(peso_unitario_kg)
    flete_total_calculado = tarifa_flete_unitario * cant_cajas
    
    with col_p2:
        st.subheader("Desglose Logístico & Deducciones")
        st.info(f"📦 **Peso por bulto:** {peso_unitario_kg:.2f} kg ({cant_cajas} bultos)")
        st.info(f"🚚 **Flete Calculado (MeLi ME2):** ${tarifa_flete_unitario:,.0f} x {cant_cajas} = **${flete_total_calculado:,.0f}**")
        
        if peso_unitario_kg > 30.0:
            st.error("🚨 **ALERTA:** Este producto excede los 30 kg por caja de la Colecta MeLi (ME2). Debe operarse por **ME1 / Expreso / Envío Propio**.")
        else:
            st.success("✅ Apto para Colecta de Mercado Libre (ME2).")

    st.markdown("---")
    st.subheader("Tabla de PVP Sugeridos en Cuotas Sin Interés")
    
    comision_clasica = pvp_base_actual * TASAS_CUOTAS["1 Pago / Clásica"]["comision_base"]
    impuestos_clasica = pvp_base_actual * TOTAL_IMPUESTOS
    resultado_neto_base = pvp_base_actual - comision_clasica - flete_total_calculado - impuestos_clasica
    margen_neto_pct = (resultado_neto_base / pvp_base_actual) if pvp_base_actual > 0 else 0
    
    m_a, m_b, m_c = st.columns(3)
    m_a.metric("Resultado Neto en Mano", f"${resultado_neto_base:,.2f}")
    m_b.metric("Margen % Neto sobre PVP Base", f"{margen_neto_pct*100:.1f}%")
    m_c.metric("Costo Producto / CMV", f"${costo_producto:,.0f}")
    
    filas_cuotas = []
    for modalidad, info in TASAS_CUOTAS.items():
        divisor = info["divisor"]
        pvp_sugerido = (resultado_neto_base + flete_total_calculado) / divisor if divisor > 0 else 0
        pvp_sugerido_red = np.ceil(pvp_sugerido / 100) * 100
        
        comision_tot_pct = (info["comision_base"] + info["tasa_finan"]) * 100
        filas_cuotas.append({
            "Modalidad": modalidad,
            "Comisión Total (%)": f"{comision_tot_pct:.1f}%",
            "Impuestos (%)": f"{TOTAL_IMPUESTOS*100:.1f}%",
            "Factor Divisor": f"{divisor:.3f}",
            "PVP Sugerido ($)": pvp_sugerido_red
        })
        
    df_cuotas = pd.DataFrame(filas_cuotas)
    st.dataframe(
        df_cuotas,
        column_config={
            "PVP Sugerido ($)": st.column_config.NumberColumn("PVP Sugerido ($)", format="$%.0f")
        },
        use_container_width=True,
        hide_index=True
    )

# ------------------------------------------------------------------------------
# TAB 3: AUDITORÍA LOGÍSTICA & CANALES
# ------------------------------------------------------------------------------
with tab3:
    st.markdown('<div class="main-header">🚚 Matriz de Reglas Logísticas y Canales de Despacho</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Guía operativa para evitar rechazos en puerta y definir el canal correcto de envío.</div>', unsafe_allow_html=True)
    
    st.markdown("""
    ### 📌 Reglas de Asignación de Canales Logísticos:
    
    1. **Colecta de Mercado Libre (ME2):**
       - **Límite Físico:** Máximo **30 kg** por bulto/caja individual.
       - **Límite Dimensiones:** Largo máximo **150 cm**, suma de lados hasta **260 cm**.
       - **Aplica para:** Racks de TV, Zapateros, Mesas de centro, Cómodas chicas/medianas.
       
    2. **Mercado Envíos 1 (ME1) / Expreso / Envío Propio:**
       - **Límite Físico:** Bultos pesados de más de **30 kg** o paquetes voluminosos.
       - **Aplica para:** Roperos grandes (Libe40, Libe41), Camas pesadas (C141BL con 125 kg en 3 cajas).
       - **Estrategia:** Configurar cotización automática en la publicación para que el comprador pague el envío o integrar tarifa pesada.
       
    3. **Envíos Flex (En el día):**
       - **Límite Físico:** Exclusivo para entregas en CABA/GBA de productos de bajo peso (< 20 kg).
    """)
