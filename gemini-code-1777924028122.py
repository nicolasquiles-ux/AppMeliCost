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
    # Extrae el código MLA de un link o de un texto sucio
    match = re.search(r'MLA[- ]?(\d+)', texto.upper())
    return f"MLA{match.group(1)}" if match else None

def buscar_producto_mla(mla_id):
    if not mla_id: return {"status": "error", "mensaje": "ID inválido"}
    
    # Intentamos buscar como ITEM (Publicación individual)
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
        else:
            # Si falla, intentamos buscar como PRODUCTO (Catálogo)
            url_p = f"https://api.mercadolibre.com/products/{mla_id}"
            res_p = requests.get(url_p)
            if res_p.status_code == 200:
                data_p = res_p.json()
                return {
                    "titulo": data_p.get("name"),
                    "precio": data_p.get("buy_box_winner", {}).get("price") or 0,
                    "imagen": data_p.get("pictures")[0].get("url") if data_p.get("pictures") else "",
                    "status": "ok"
                }
        return {"status": "error", "mensaje": "No se encontró publicación ni producto de catálogo con ese ID."}
    except:
        return {"status": "error", "mensaje": "Error de conexión con MeLi"}

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://http2.mlstatic.com/static/org-img/mkt/vendas-mkt/v3/logo-mercado-livre.png", width=140)
    st.header("🔐 Acceso Clientes")
    
    clave_ingresada = st.text_input("Ingresá tu Clave Pro", type="password")
    es_pro = (clave_ingresada == CLAVE_CORRECTA)
    
    if es_pro:
        st.success("✅ Cuenta Pro Activa")
    else:
        st.warning("⚠️ Funciones Limitadas")
        st.markdown(f'<a href="https://wa.me/5491165808113?text=Quiero%20mi%20clave%20Pro" class="whatsapp-button">Pedir Clave por WhatsApp</a>', unsafe_allow_html=True)

    st.divider()
    reputacion = st.selectbox("Tu Reputación", ["Verde (50%)", "Amarilla (40%)", "Roja (0%)"])
    tipo_vend = st.radio("IVA", ["Responsable Inscripto", "Monotributista"])
    iibb_tax = st.number_input("% IIBB", value=3.5)

# --- APP PRINCIPAL ---
st.title("🚀 MeLi Smart Pricing")

tab_calc, tab_mla = st.tabs(["🧮 Calculadora de Margen", "🔍 Buscador MeLi"])

# Variables globales para persistencia
if 'precio_mla' not in st.session_state: st.session_state.precio_mla = 0.0

with tab_mla:
    st.subheader("Buscador de Precios Reales")
    mla_raw = st.text_input("Pegá el link o el MLA (ej: MLA27392194)", placeholder="MLA...")
    
    if st.button("Consultar Mercado Libre", use_container_width=True):
        if not es_pro:
            st.error("🔒 Necesitás una cuenta Pro para usar el buscador.")
        else:
            id_limpio = extraer_mla(mla_raw)
            with st.spinner('Buscando en MeLi...'):
                res = buscar_producto_mla(id_limpio)
                if res["status"] == "ok":
                    st.session_state.precio_mla = float(res["precio"])
                    st.success(f"Producto: {res['titulo']}")
                    col_img, col_txt = st.columns([1, 3])
                    with col_img: st.image(res["imagen"], width=150)
                    with col_txt: st.metric("Precio en MeLi", f"$ {res['precio']:,.2f}")
                else:
                    st.error(res["mensaje"])

with tab_calc:
    c1, c2 = st.columns(2)
    with c1:
        costo_compra = st.number_input("Costo de Compra ($)", value=15000.0)
        # Si buscamos un MLA, usamos ese precio, si no, el sugerido
        default_pvp = st.session_state.precio_mla if st.session_state.precio_mla > 0 else (costo_compra * 1.5)
        precio_venta = st.number_input("Precio de Venta (PVP)", value=float(default_pvp))
        comision_pct = st.number_input("% Comisión MeLi", value=15.0)

    # Cálculos dinámicos
    iva_r = (precio_venta * 0.1735) if tipo_vend == "Responsable Inscripto" else 0.0
    iibb_r = precio_venta * (iibb_tax / 100)
    costo_fijo = 3030.0 if precio_venta < 33000 else 0.0
    envio = 6500.0 * (0.5 if "Verde" in reputacion else 1) if precio_venta >= 33000 else 0.0
    
    gastos = (precio_venta * (comision_pct/100)) + iva_r + iibb_r + costo_fijo + envio
    ganancia = precio_venta - gastos - costo_compra
    
    st.divider()
    r1, r2 = st.columns(2)
    r1.metric("Ganancia Neta", f"$ {ganancia:,.2f}")
    r2.metric("Margen Real", f"{(ganancia/precio_venta if precio_venta > 0 else 0):.2%}")
