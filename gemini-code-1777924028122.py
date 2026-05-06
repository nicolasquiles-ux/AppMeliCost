import streamlit as st
import pandas as pd
import requests
import re

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="MeLi Intelligence Pro", layout="wide", page_icon="🚀")

# --- CLAVE DE ACCESO PRO ---
CLAVE_CORRECTA = "CENTRO_PRO_2026"

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-left: 6px solid #ffe600; }
    .whatsapp-button { background-color: #25d366; color: white !important; padding: 12px 20px; border-radius: 8px; text-decoration: none; font-weight: bold; display: block; text-align: center; margin-top: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES TÉCNICAS ---
def extraer_mla(texto):
    match = re.search(r'MLA[- ]?(\d+)', texto.upper())
    return f"MLA{match.group(1)}" if match else None

def buscar_en_meli(mla_id):
    if not mla_id: return {"status": "error", "mensaje": "ID inválido"}
    
    # 1. Intentamos como ITEM (Publicación normal)
    url_item = f"https://api.mercadolibre.com/items/{mla_id}"
    res_item = requests.get(url_item)
    
    if res_item.status_code == 200:
        data = res_item.json()
        return {
            "titulo": data.get("title"),
            "precio": data.get("price"),
            "imagen": data.get("thumbnail"),
            "status": "ok"
        }
    
    # 2. Si falla, intentamos como PRODUCTO (Catálogo como el MLA27392194)
    # Nota: Para catálogo, a veces el ID no lleva el prefijo "MLA" en la URL de la API
    solo_numeros = mla_id.replace("MLA", "")
    url_prod = f"https://api.mercadolibre.com/products/{mla_id}"
    res_prod = requests.get(url_prod)
    
    if res_prod.status_code == 200:
        data = res_prod.json()
        return {
            "titulo": data.get("name"),
            "precio": data.get("buy_box_winner", {}).get("price") or 0,
            "imagen": data.get("pictures")[0].get("url") if data.get("pictures") else "",
            "status": "ok"
        }
    
    return {"status": "error", "mensaje": "No se encontró el ID en Publicaciones ni en Catálogo."}

# --- DATA DE REFERENCIA ---
tarifario_envios = {
    "0.5 kg (Sobres)": 4800.0, "1 kg": 5200.0, "2 kg": 5900.0, "5 kg": 7400.0,
    "10 kg": 9800.0, "15 kg": 12500.0, "20 kg": 15200.0, "25 kg": 18400.0,
    "30 kg (Límite)": 22000.0, "Especial (Muebles)": 35000.0
}
tasas_financiacion = {"1 Pago": 0.0, "3 Pagos": 12.5, "6 Pagos": 23.8, "9 Pagos": 35.0, "12 Pagos": 45.0}

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://http2.mlstatic.com/static/org-img/mkt/vendas-mkt/v3/logo-mercado-livre.png", width=140)
    st.header("🔐 Acceso Clientes")
    clave_ingresada = st.text_input("Ingresá tu Clave Pro", type="password")
    es_pro = (clave_ingresada == CLAVE_CORRECTA)
    
    if not es_pro:
        st.markdown(f'<a href="https://wa.me/5491165808113?text=Quiero%20mi%20clave%20Pro" class="whatsapp-button">Pedir Clave Pro</a>', unsafe_allow_html=True)
    
    st.divider()
    reputacion = st.selectbox("Tu Reputación", ["Verde (50%)", "Amarilla (40%)", "Roja (0%)"])
    tipo_vend = st.radio("IVA", ["Responsable Inscripto", "Monotributista"])
    iibb_tax = st.number_input("% IIBB", value=3.5)

# --- APP PRINCIPAL ---
st.title("🚀 MeLi Smart Pricing")

tab_calc, tab_mla = st.tabs(["🧮 Calculadora", "🔍 Buscador MeLi"])

# Persistencia de precio buscado
if 'precio_buscado' not in st.session_state: st.session_state.precio_buscado = 0.0

with tab_mla:
    st.subheader("Buscador Híbrido (Publicación o Catálogo)")
    mla_input = st.text_input("Pegá el código o link aquí", placeholder="Ej: MLA27392194")
    
    if st.button("Consultar MeLi", use_container_width=True):
        if not es_pro:
            st.error("🔒 Función exclusiva para suscriptores Pro.")
        else:
            id_limpio = extraer_mla(mla_input)
            with st.spinner('Consultando base de datos de MeLi...'):
                res = buscar_en_meli(id_limpio)
                if res["status"] == "ok":
                    st.session_state.precio_buscado = float(res["precio"])
                    st.success(f"Encontrado: {res['titulo']}")
                    st.image(res["imagen"], width=150)
                    st.metric("Precio Competencia", f"$ {res['precio']:,.2f}")
                    st.info("✅ Precio cargado en la calculadora.")
                else:
                    st.error(res["mensaje"])

with tab_calc:
    col_l, col_r = st.columns(2)
    
    with col_l:
        st.subheader("💰 Costos y Márgenes")
        costo_compra = st.number_input("Costo de Compra ($)", value=15000.0)
        margen_obj = st.slider("% Margen Objetivo", 5, 50, 20)
        comision_base = st.number_input("% Comisión MeLi", value=15.0)
        plan_cuotas = st.selectbox("Financiación", list(tasas_financiacion.keys()))
        tasa_f = tasas_financiacion[plan_cuotas]

    with col_r:
        st.subheader("📦 Logística")
        peso_sel = st.selectbox("Peso del bulto", list(tarifario_envios.keys()))
        otros_gastos = st.number_input("Embalaje/Otros ($)", value=0.0)
        
        # Sugerencia de PVP automática (Pricing Inteligente)
        t_iva = 0.1735 if tipo_vend == "Responsable Inscripto" else 0.0
        t_iibb = iibb_tax / 100
        t_comm = comision_base / 100
        t_finan = tasa_f / 100
        divisor = (1 - t_comm - (margen_obj/100) - t_iibb - t_iva - t_finan)
        
        c_envio_lista = tarifario_envios[peso_sel]
        dcto_e = 0.5 if "Verde" in reputacion else (0.6 if "Amarilla" in reputacion else 1)
        # Estimamos costo envío para el PVP sugerido
        c_envio_est = c_envio_lista * dcto_e
        
        pvp_sugerido = (costo_compra + otros_gastos + c_envio_est) / divisor if divisor > 0 else costo_compra * 2
        
        # El precio de venta toma el valor buscado en MLA si existe, sino el sugerido
        val_inicial = st.session_state.precio_buscado if st.session_state.precio_buscado > 0 else pvp_sugerido
        precio_venta = st.number_input("Precio de Venta Final (PVP)", value=float(round(val_inicial, 0)))

    # --- RE-CÁLCULO DE DESGLOSE ---
    costo_fijo = 3030.0 if precio_venta < 33000 else 0.0
    envio_real = c_envio_lista * dcto_e if precio_venta >= 33000 else 0.0
    iva_r = (precio_venta - (precio_venta / 1.21)) if tipo_vend == "Responsable Inscripto" else 0.0
    iibb_r = (precio_venta / (1.21 if tipo_vend == "Responsable Inscripto" else 1)) * (iibb_tax/100)
    comm_r = precio_venta * (comision_base / 100)
    finan_r = precio_venta * (tasa_f / 100)
    
    total_gastos = comm_r + costo_fijo + envio_real + iva_r + iibb_r + finan_r + otros_gastos
    ganancia_neta = precio_venta - total_gastos - costo_compra
    margen_real = (ganancia_neta / precio_venta) if precio_venta > 0 else 0

    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("Ganancia Neta", f"$ {ganancia_neta:,.2f}")
    m2.metric("Margen Real", f"{margen_real:.2%}")
    m3.metric("PVP Sugerido", f"$ {pvp_sugerido:,.0f}")

    with st.expander("📊 Ver Desglose de Costos Detallado"):
        df_desc = pd.DataFrame({
            "Concepto": ["Costo Producto", "Comisión MeLi", "Costo Fijo MeLi", "Envío (Fulfillment/Colecta)", "IVA (ARCA)", "Ingresos Brutos", "Costo Financiero", "Embalaje/Otros"],
            "Monto": [costo_compra, comm_r, costo_fijo, envio_real, iva_r, iibb_r, finan_r, otros_gastos]
        })
        st.table(df_desc.style.format({"Monto": "${:,.2f}"}))
