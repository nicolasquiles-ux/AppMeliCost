import streamlit as st
import pandas as pd
import requests
import re
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="MeLi Intelligence Pro", layout="wide", page_icon="🚀")

# =========================================================
# TABLAS MAESTRAS (Editables)
# =========================================================
TARIFARIO_ENVIOS = {
    "0.5 kg": 4800.0, "1 kg": 5200.0, "2 kg": 5900.0, 
    "5 kg": 7400.0, "10 kg": 9800.0, "15 kg": 12500.0, 
    "20 kg": 15200.0, "25 kg": 18400.0, "30 kg": 22000.0
}

TASAS_FINANCIACION = {
    "1 Pago": 0.0, "3 Pagos (Cuota Simple)": 12.5, 
    "6 Pagos (Cuota Simple)": 23.8, "9 Pagos": 35.0, "12 Pagos": 45.0
}

CLAVE_CORRECTA = "CENTRO_PRO_2026"
# =========================================================

# --- MOTOR DE BÚSQUEDA "FINAL BOSS" ---
def extraer_precio_real(input_usuario):
    # Extraemos el ID (ya sea de un link o del número suelto)
    id_num = re.sub(r'\D', '', str(input_usuario))
    if not id_num: return None

    # Intentamos tres rutas diferentes
    urls_a_probar = [
        f"https://www.mercadolibre.com.ar/p/MLA{id_num}", # Ruta de Catálogo
        f"https://articulo.mercadolibre.com.ar/MLA-{id_num}", # Ruta de Publicación
        f"https://www.mercadolibre.com.ar/p/MLA{id_num}?pdp_filters=official_store%3A1542" # Tienda oficial Centro Estant
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept-Language": "es-AR,es;q=0.9"
    }

    for url in urls_a_probar:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Buscamos el precio en los metadatos de la página (lo más confiable)
                meta_price = soup.find("meta", itemprop="price")
                title = soup.find("h1", class_="ui-pdp-title")
                
                if meta_price:
                    return {
                        "titulo": title.text if title else "Producto Encontrado",
                        "precio": float(meta_price['content'])
                    }
        except:
            continue
    return None

# --- SIDEBAR ---
with st.sidebar:
    st.title("👤 Configuración")
    clave = st.text_input("Clave Pro", type="password")
    es_pro = (clave == CLAVE_CORRECTA)
    
    if not es_pro:
        st.error("🔒 Ingresá la clave para activar el rastreador.")
    
    st.divider()
    reputacion = st.selectbox("Tu Reputación", ["Verde (50% desc)", "Amarilla (40% desc)", "Roja (0% desc)"])
    tipo_vend = st.radio("Tu IVA", ["Responsable Inscripto", "Monotributista"])
    iibb_tax = st.number_input("% Percepción IIBB", value=3.5)

# --- APP ---
st.title("🚀 MeLi Intelligence Pro")
tab_calc, tab_mla = st.tabs(["🧮 Calculadora de Margen", "🔍 Espiar Competencia"])

if 'precio_meli' not in st.session_state: st.session_state.precio_meli = 0.0

with tab_mla:
    st.subheader("Rastreador de Precios en Tiempo Real")
    url_input = st.text_input("Pegá el código (27392194) o el LINK completo del vajillero")
    
    if st.button("Rastrear ahora", use_container_width=True):
        if not es_pro:
            st.warning("Clave incorrecta.")
        else:
            with st.spinner('Evadiendo bloqueos y extrayendo precio...'):
                resultado = extraer_precio_real(url_input)
                if resultado:
                    st.session_state.precio_meli = resultado['precio']
                    st.success(f"✅ ¡LO TENEMOS! {resultado['titulo']}")
                    st.metric("Precio Competencia", f"$ {resultado['precio']:,.2f}")
                else:
                    st.error("No se pudo extraer. MeLi bloqueó el acceso. Intentá pegando el link directo de la web.")

with tab_calc:
    col_izq, col_der = st.columns([1.3, 2])
    
    with col_der:
        c1, c2 = st.columns(2)
        with c1:
            costo_compra = st.number_input("Costo del Mueble ($)", value=15000.0)
            financiacion = st.selectbox("Cuotas", list(TASAS_FINANCIACION.keys()))
        with c2:
            margen_neto_obj = st.slider("% Margen deseado", 5, 50, 20)
            comision_meli = st.number_input("% Comisión MeLi", value=15.0)

    # Lógica de cálculo PVP Sugerido
    t_iva = 0.1735 if tipo_vend == "Responsable Inscripto" else 0.0
    t_iibb = iibb_tax / 100
    t_finan = TASAS_FINANCIACION[financiacion] / 100
    divisor = (1 - (comision_meli/100) - (margen_neto_obj/100) - t_iibb - t_iva - t_finan)
    
    dcto_envio = 0.5 if "Verde" in reputacion else 0.6 if "Amarilla" in reputacion else 1
    costo_logistico = TARIFARIO_ENVIOS["10 kg"] * dcto_envio
    pvp_sugerido = (costo_compra + costo_logistico) / divisor if divisor > 0 else 0

    with col_izq:
        st.markdown(f"""
            <div style="background-color:#ffe600; padding:30px; border-radius:20px; text-align:center; border:3px solid #000; box-shadow: 0 10px 20px rgba(0,0,0,0.1);">
                <div style="font-weight:bold; color:#333; font-size:1.2rem;">PVP SUGERIDO</div>
                <div style="font-size:3.5rem; font-weight:900; color:#000; line-height:1;">${pvp_sugerido:,.0f}</div>
                <div style="margin-top:15px; font-weight:bold; color:#555;">GANANCIA OBJETIVO: {margen_neto_obj}%</div>
            </div>
        """, unsafe_allow_html=True)

    st.divider()
    
    # Análisis Final
    col_f, col_r1, col_r2 = st.columns([1.2, 1, 1])
    with col_f:
        precio_a_testear = st.number_input("Precio a Evaluar ($)", value=float(round(st.session_state.precio_meli if st.session_state.precio_meli > 0 else pvp_sugerido, 0)))

    peso_seleccionado = st.selectbox("Peso para Envío Real", list(TARIFARIO_ENVIOS.keys()), index=4)
    envio_real = TARIFARIO_ENVIOS[peso_seleccionado] * dcto_envio if precio_a_testear >= 33000 else 0.0
    
    iva_calc = (precio_a_testear - (precio_a_testear / 1.21)) if tipo_vend == "Responsable Inscripto" else 0.0
    iibb_calc = (precio_a_testear / (1.21 if tipo_vend == "Responsable Inscripto" else 1)) * t_iibb
    comi_calc = precio_a_testear * (comision_meli/100)
    finan_calc = precio_a_testear * t_finan
    costo_fijo = 3030.0 if precio_a_testear < 33000 else 0.0
    
    ganancia_final = precio_a_testear - (comi_calc + costo_fijo + envio_real + iva_calc + iibb_calc + finan_calc) - costo_compra
    margen_final = (ganancia_final / precio_a_testear) if precio_a_testear > 0 else 0

    with col_r1: st.metric("Ganancia Neta", f"$ {ganancia_final:,.2f}")
    with col_r2: st.metric("Margen Real", f"{margen_final:.2%}")
