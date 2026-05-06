import streamlit as st
import pandas as pd
import requests

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="MeLi Intelligence Pro", layout="wide", page_icon="🚀")

# --- ESTILOS CSS PERSONALIZADOS (UI/UX) ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    /* Estilo de métricas tipo tarjeta */
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #2d3436; }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 6px solid #ffe600;
    }
    /* Tarjetas de Planes */
    .plan-card {
        padding: 25px;
        border-radius: 15px;
        border: 1px solid #e0e0e0;
        background-color: white;
        text-align: center;
        transition: 0.3s;
    }
    .plan-card:hover { border-color: #ffe600; box-shadow: 0 10px 15px rgba(0,0,0,0.1); }
    
    /* Botón de WhatsApp */
    .whatsapp-button {
        background-color: #25d366;
        color: white !important;
        padding: 12px 20px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: bold;
        display: block;
        text-align: center;
        margin-top: 15px;
        font-size: 14px;
    }
    /* Ajustes Android */
    @media (max-width: 640px) {
        .stTabs [data-baseweb="tab"] { font-size: 12px; padding: 10px 5px; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURACIÓN DE CONTACTO ---
# Tu número configurado: 11 6580 8113
MI_WHATSAPP = "5491165808113" 
MENSAJE_WS = "Hola! Vi tu App de MeLi Analytics y quiero activar mi cuenta Pro."

# --- FUNCIONES TÉCNICAS (API MeLi) ---
def buscar_producto_mla(mla_id):
    mla_id = str(mla_id).upper().replace(" ", "").replace("-", "")
    if not mla_id.startswith("MLA"): mla_id = "MLA" + mla_id
    url = f"https://api.mercadolibre.com/items/{mla_id}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return {
                "titulo": data.get("title"),
                "precio": data.get("price"),
                "imagen": data.get("thumbnail"),
                "status": "ok"
            }
        return {"status": "error", "mensaje": "Producto no encontrado"}
    except:
        return {"status": "error", "mensaje": "Error de conexión"}

# --- DATA DE REFERENCIA (Tasas Mayo 2026) ---
tarifario_envios = {
    "0.5 kg (Sobres)": 4800.0, "1 kg": 5200.0, "2 kg": 5900.0, "5 kg": 7400.0,
    "10 kg": 9800.0, "15 kg": 12500.0, "20 kg": 15200.0, "25 kg": 18400.0,
    "30 kg (Límite)": 22000.0, "Especial (Muebles)": 35000.0
}
tasas_financiacion = {
    "1 Pago": 0.0, "3 Pagos (Cuota Simple)": 12.5, "6 Pagos (Cuota Simple)": 23.8,
    "9 Pagos": 35.0, "12 Pagos": 45.0
}

# --- SIDEBAR & SOPORTE ---
with st.sidebar:
    st.image("https://http2.mlstatic.com/static/org-img/mkt/vendas-mkt/v3/logo-mercado-livre.png", width=140)
    st.header("👤 Mi Cuenta")
    
    # Toggle de administrador para que vos puedas mostrar la app funcionando
    es_pro = st.toggle("Activar Funciones Pro", value=False, help="Solo visible para cuentas con suscripción paga.")
    
    st.divider()
    st.write("💬 **Soporte y Ventas**")
    link_ws = f"https://wa.me/{MI_WHATSAPP}?text={MENSAJE_WS.replace(' ', '%20')}"
    st.markdown(f'<a href="{link_ws}" target="_blank" class="whatsapp-button">Solicitar Acceso Pro</a>', unsafe_allow_html=True)
    
    st.divider()
    reputacion = st.selectbox("Reputación", ["Verde (50%)", "Amarilla (40%)", "Roja (0%)"])
    tipo_vend = st.radio("Condición IVA", ["Responsable Inscripto", "Monotributista"])
    iibb_tax = st.number_input("% Ingresos Brutos", value=3.5)

# --- PANTALLA PRINCIPAL ---
st.title("🚀 MeLi Market Intelligence")

tab_calc, tab_mla, tab_premium = st.tabs(["🧮 Calculadora", "🔍 Buscador MLA", "💎 Planes Pro"])

with tab_calc:
    # Bloque de Inputs
    c_base1, c_base2 = st.columns(2)
    with c_base1:
        costo_compra = st.number_input("Costo de Compra ($)", value=15000.0, step=500.0)
        comision_base = st.number_input("% Comisión MeLi", value=15.0)
        plan_sel = st.selectbox("Financiación", list(tasas_financiacion.keys()))
    
    with c_base2:
        margen_obj = st.slider("% Margen Neto Deseado", 5, 50, 20)
        # Cálculo sugerido inicial
        t_iva = 0.1735 if tipo_vend == "Responsable Inscripto" else 0.0
        t_iibb = iibb_tax / 100
        t_comm = comision_base / 100
        t_finan = tasas_financiacion[plan_sel] / 100
        divisor = (1 - t_comm - (margen_obj/100) - t_iibb - t_iva - t_finan)
        pvp_sug = (costo_compra + 4000) / divisor if divisor > 0 else costo_compra * 2
        
        precio_venta = st.number_input("Precio de Venta Final (PVP)", value=float(round(pvp_sug, 0)))

    # Motor de Cálculo Real
    costo_fijo = 3030.0 if precio_venta < 33000 else 0.0
    costo_envio = 6500.0 * (0.5 if "Verde" in reputacion else 0.6 if "Amarilla" in reputacion else 1) if precio_venta >= 33000 else 0.0
    
    iva_r = (precio_venta - (precio_venta / 1.21)) if tipo_vend == "Responsable Inscripto" else 0.0
    iibb_r = (precio_venta / (1.21 if tipo_vend == "Responsable Inscripto" else 1)) * (iibb_tax / 100)
    comm_r = precio_venta * (comision_base / 100)
    finan_r = precio_venta * (tasas_financiacion[plan_sel] / 100)
    
    gastos_t = comm_r + costo_fijo + costo_envio + iva_r + iibb_r + finan_r
    ganancia_n = precio_venta - gastos_t - costo_compra
    margen_r = ganancia_n / precio_venta if precio_venta > 0 else 0

    # Resultados UI
    st.divider()
    res1, res2, res3 = st.columns(3)
    res1.metric("Ganancia Neta", f"$ {ganancia_n:,.2f}")
    res2.metric("Margen Real", f"{margen_r:.2%}")
    res3.metric("Gastos Totales", f"$ {gastos_t:,.2f}")

with tab_mla:
    if not es_pro:
        st.info("🔒 **Función Pro bloqueada**")
        st.write("Buscá cualquier producto de Mercado Libre por su código MLA y obtené su rentabilidad al instante.")
        if st.button("Ver Planes y Precios", use_container_width=True):
            st.balloons()
    else:
        st.subheader("🔍 Analizador de Competencia")
        mla_id = st.text_input("Código MLA", placeholder="Ej: MLA1414163532")
        if st.button("Analizar Publicación", use_container_width=True):
            data = buscar_producto_mla(mla_id)
            if data["status"] == "ok":
                st.success(f"Producto encontrado: {data['titulo']}")
                st.image(data["imagen"], width=150)
                st.metric("Precio en MeLi", f"$ {data['precio']:,.2f}")
                st.info("💡 Este precio se cargó automáticamente en la pestaña 'Calculadora'")
            else:
                st.error(data["mensaje"])

with tab_premium:
    st.subheader("Planes de Suscripción")
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown('<div class="plan-card"><h3>Free</h3><p>Calculadora Manual</p><h2>$0</h2><hr><p>Limitado</p></div>', unsafe_allow_html=True)
    with p2:
        st.markdown('<div class="plan-card" style="border: 2px solid #ffe600"><h3>Pro</h3><p>Buscador MLA + IA</p><h2>$18.000</h2><hr><p>Mes / ARS</p></div>', unsafe_allow_html=True)
        st.markdown(f'<a href="{link_ws}" class="whatsapp-button">Activar Ahora</a>', unsafe_allow_html=True)
    with p3:
        st.markdown('<div class="plan-card"><h3>Expert</h3><p>Análisis Masivo</p><h2>$35.000</h2><hr><p>Mes / ARS</p></div>', unsafe_allow_html=True)
