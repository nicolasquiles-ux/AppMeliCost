import streamlit as st
import pandas as pd
import requests
import re
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="MeLi Intelligence Pro", layout="wide", page_icon="🚀")

# --- CLAVE DE ACCESO PRO ---
CLAVE_CORRECTA = "CENTRO_PRO_2026"

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .pvp-box {
        background-color: #ffe600;
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        border: 3px solid #000;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    .pvp-value { font-size: 3.5rem; font-weight: 900; color: #000; line-height: 1; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 12px; border: 1px solid #eee; }
    .whatsapp-button { background-color: #25d366; color: white !important; padding: 12px; border-radius: 8px; text-decoration: none; font-weight: bold; display: block; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIÓN DE BÚSQUEDA "TANQUE" (API + SCRAPPING) ---
def buscar_precio_meli(id_input):
    id_limpio = re.sub(r'\D', '', str(id_input))
    if not id_limpio: return None
    
    # Intento 1: API de Items
    try:
        url = f"https://api.mercadolibre.com/items/MLA{id_limpio}"
        res = requests.get(url, timeout=3)
        if res.status_code == 200:
            data = res.json()
            return {"titulo": data.get("title"), "precio": data.get("price"), "status": "ok"}
    except: pass

    # Intento 2: Scrapping Público (Para IDs de Catálogo como el tuyo)
    try:
        # Probamos con la URL de producto de catálogo
        headers = {'User-Agent': 'Mozilla/5.0'}
        url_web = f"https://www.mercadolibre.com.ar/p/MLA{id_limpio}"
        res_web = requests.get(url_web, headers=headers, timeout=5)
        if res_web.status_code == 200:
            soup = BeautifulSoup(res_web.text, 'html.parser')
            # Buscamos el precio en los meta tags o clases comunes
            meta_price = soup.find("meta", itemprop="price")
            title = soup.find("h1").text if soup.find("h1") else "Producto Catálogo"
            if meta_price:
                return {"titulo": title, "precio": float(meta_price['content']), "status": "ok"}
    except: pass

    return None

# --- DATA ---
tarifario_envios = {"0.5 kg": 4800, "1 kg": 5200, "2 kg": 5900, "5 kg": 7400, "10 kg": 9800, "15 kg": 12500, "20 kg": 15200, "30 kg": 22000}
tasas_finan = {"1 Pago": 0.0, "3 Pagos": 7.0, "6 Pagos": 10.5, "9 Pagos": 13.5, "12 Pagos": 16.0}

# --- SIDEBAR ---
with st.sidebar:
    st.title("👤 Mi Perfil")
    clave = st.text_input("Clave Pro", type="password")
    es_pro = (clave == CLAVE_CORRECTA)
    if not es_pro:
        st.markdown(f'<a href="https://wa.me/5491165808113" class="whatsapp-button">Solicitar Clave Pro</a>', unsafe_allow_html=True)
    st.divider()
    reputacion = st.selectbox("Reputación", ["Verde (50%)", "Amarilla (40%)", "Roja (0%)"])
    tipo_vend = st.radio("Condición IVA", ["Responsable Inscripto", "Monotributista"])
    iibb_tax = st.number_input("% IIBB", value=3.5)

# --- APP ---
st.title("🚀 MeLi Intelligence Pro")

tab_calc, tab_mla = st.tabs(["🧮 Calculadora", "🔍 Espiar Competencia"])

# Session State para mantener datos
if 'costo' not in st.session_state: st.session_state.costo = 15000.0
if 'precio_meli' not in st.session_state: st.session_state.precio_meli = 0.0

with tab_mla:
    st.subheader("Buscador por MLA / Link")
    input_busqueda = st.text_input("Pegá el código o link", placeholder="Ej: 27392194")
    if st.button("Buscar en MeLi", use_container_width=True):
        if not es_pro: st.error("🔒 Función Pro bloqueada.")
        else:
            with st.spinner('Analizando publicación...'):
                resultado = buscar_precio_meli(input_busqueda)
                if resultado:
                    st.session_state.precio_meli = resultado['precio']
                    st.success(f"Producto: {resultado['titulo']}")
                    st.metric("Precio Detectado", f"$ {resultado['precio']:,.2f}")
                else:
                    st.error("No pudimos obtener el precio. Intentá pegando el link completo.")

with tab_calc:
    # FILA 1: PVP SUGERIDO (IZQUIERDA) E INPUTS (DERECHA)
    col_izq, col_der = st.columns([1.3, 2])
    
    with col_der:
        c1, c2 = st.columns(2)
        with c1:
            costo_c = st.number_input("Costo Compra ($)", value=st.session_state.costo)
            st.session_state.costo = costo_c
            plan = st.selectbox("Financiación", list(tasas_finan.keys()))
        with c2:
            margen_deseado = st.slider("% Margen Neto", 5, 50, 20)
            comision = st.number_input("% Comi MeLi", value=15.0)

    # Lógica de cálculo para el PVP Sugerido
    t_iva = 0.1735 if tipo_vend == "Responsable Inscripto" else 0.0
    t_iibb = iibb_tax / 100
    t_finan = tasas_finan[plan] / 100
    div = (1 - (comision/100) - (margen_deseado/100) - t_iibb - t_iva - t_finan)
    
    # Costo envío base para el sugerido (10kg verde)
    envio_sug = 9800 * 0.5
    pvp_sug = (costo_c + envio_sug) / div if div > 0 else 0

    with col_izq:
        st.markdown(f"""
            <div class="pvp-box">
                <div style="font-weight:bold; color:#333;">PVP SUGERIDO</div>
                <div class="pvp-value">${pvp_sug:,.0f}</div>
                <div style="margin-top:10px; font-size:0.9rem;">Para ganar {margen_deseado}% neto</div>
            </div>
        """, unsafe_allow_html=True)

    st.divider()

    # FILA 2: AJUSTE MANUAL Y RESULTADOS
    col_final, col_res1, col_res2 = st.columns([1.2, 1, 1])
    
    with col_final:
        # Si buscamos en MeLi, usamos ese precio como base
        base_pvp = st.session_state.precio_meli if st.session_state.precio_meli > 0 else pvp_sug
        pvp_final = st.number_input("Precio Final a Evaluar ($)", value=float(round(base_pvp, 0)))

    # Desglose Real
    c_fijo = 3030.0 if pvp_final < 33000 else 0.0
    # Peso para el cálculo real
    peso_c = st.selectbox("Peso del bulto (Envío)", list(tarifario_envios.keys()), index=4)
    envio_r = tarifario_envios[peso_c] * (0.5 if "Verde" in reputacion else 1) if pvp_final >= 33000 else 0.0
    
    iva_r = (pvp_final - (pvp_final / 1.21)) if tipo_vend == "Responsable Inscripto" else 0.0
    iibb_r = (pvp_final / (1.21 if tipo_vend == "Responsable Inscripto" else 1)) * t_iibb
    comm_r = pvp_final * (comision/100)
    finan_r = pvp_final * t_finan
    
    gastos_totales = comm_r + c_fijo + envio_r + iva_r + iibb_r + finan_r
    ganancia = pvp_final - gastos_totales - costo_c
    margen_r = (ganancia / pvp_final) if pvp_final > 0 else 0

    with col_res1: st.metric("Ganancia Neta", f"$ {ganancia:,.2f}")
    with col_res2: st.metric("Margen Real", f"{margen_r:.2%}")

    with st.expander("📄 Ver Desglose Detallado"):
        df = pd.DataFrame({
            "Concepto": ["Compra", "Comisión", "Costo Fijo", "Envío", "IVA", "IIBB", "Finan"],
            "Monto": [costo_c, comm_r, c_fijo, envio_r, iva_r, iibb_r, finan_r]
        })
        st.table(df.style.format({"Monto": "${:,.2f}"}))
