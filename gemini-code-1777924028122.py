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
    .whatsapp-button { background-color: #25d366 !important; color: white !important; padding: 12px; border-radius: 8px; text-decoration: none; font-weight: bold; display: block; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIÓN DE BÚSQUEDA PROFESIONAL (API SEARCH) ---
def buscar_precio_meli_pro(query):
    # Extraemos solo los números por si pegan el link
    id_limpio = re.sub(r'\D', '', str(query))
    if not id_limpio: return None
    
    # Buscamos directamente en el motor de búsqueda de MeLi por el código
    # Esto funciona tanto para MLAs comunes como para IDs de catálogo
    url = f"https://api.mercadolibre.com/sites/MLA/search?q={id_limpio}"
    
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data.get("results"):
                # Tomamos el primer resultado (el más relevante)
                prod = data["results"][0]
                return {
                    "titulo": prod.get("title"),
                    "precio": float(prod.get("price")),
                    "status": "ok"
                }
    except Exception as e:
        print(f"Error en búsqueda: {e}")
    
    return None

# --- DATA ---
tarifario_envios = {"0.5 kg": 4800, "1 kg": 5200, "2 kg": 5900, "5 kg": 7400, "10 kg": 9800, "15 kg": 12500, "20 kg": 15200, "30 kg": 22000}
tasas_finan = {"1 Pago": 0.0, "3 Pagos": 7, "6 Pagos": 10, "9 Pagos": 13.5, "12 Pagos": 16.0}

# --- SIDEBAR ---
with st.sidebar:
    st.title("👤 Mi Perfil")
    clave = st.text_input("Clave Pro", type="password", help="Pedí tu clave al administrador")
    es_pro = (clave == CLAVE_CORRECTA)
    
    if not es_pro:
        st.markdown(f'<a href="https://wa.me/5491165808113?text=Hola!%20Quiero%20mi%20clave%20Pro" target="_blank" class="whatsapp-button">Solicitar Clave Pro</a>', unsafe_allow_html=True)
    
    st.divider()
    reputacion = st.selectbox("Tu Reputación", ["Verde (50%)", "Amarilla (40%)", "Roja (0%)"])
    tipo_vend = st.radio("IVA", ["Responsable Inscripto", "Monotributista"])
    iibb_tax = st.number_input("% IIBB", value=3.5)

# --- APP ---
st.title("🚀 MeLi Intelligence Pro")

tab_calc, tab_mla = st.tabs(["🧮 Calculadora", "🔍 Espiar Competencia"])

# Session State
if 'costo' not in st.session_state: st.session_state.costo = 15000.0
if 'precio_meli' not in st.session_state: st.session_state.precio_meli = 0.0

with tab_mla:
    st.subheader("Buscador por MLA / Catálogo / Link")
    input_busqueda = st.text_input("Pegá el código o el link completo", placeholder="Ej: 27392194")
    
    if st.button("Buscar en MeLi", use_container_width=True):
        if not es_pro:
            st.error("🔒 Función Pro bloqueada. Ingresá tu clave en el menú lateral.")
        else:
            with st.spinner('Conectando con Mercado Libre...'):
                resultado = buscar_precio_meli_pro(input_busqueda)
                if resultado:
                    st.session_state.precio_meli = resultado['precio']
                    st.success(f"✅ ¡Encontrado! {resultado['titulo']}")
                    st.metric("Precio en MeLi", f"$ {resultado['precio']:,.2f}")
                    st.info("Ya podés ir a la pestaña 'Calculadora' para ver tu rentabilidad.")
                else:
                    st.error("No se pudo obtener el precio. Verificá que el link o código sea correcto.")

with tab_calc:
    # FILA 1: PVP SUGERIDO (IZQUIERDA) E INPUTS (DERECHA)
    col_izq, col_der = st.columns([1.3, 2])
    
    with col_der:
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.costo = st.number_input("Costo Compra ($)", value=st.session_state.costo)
            plan = st.selectbox("Financiación", list(tasas_finan.keys()))
        with c2:
            margen_deseado = st.slider("% Margen Neto", 5, 50, 20)
            comision = st.number_input("% Comi MeLi", value=15.0)

    # Lógica de cálculo PVP Sugerido
    t_iva = 0.1735 if tipo_vend == "Responsable Inscripto" else 0.0
    t_iibb = iibb_tax / 100
    t_finan = tasas_finan[plan] / 100
    div = (1 - (comision/100) - (margen_deseado/100) - t_iibb - t_iva - t_finan)
    envio_sug = 9800 * (0.5 if "Verde" in reputacion else 1)
    pvp_sug = (st.session_state.costo + envio_sug) / div if div > 0 else 0

    with col_izq:
        st.markdown(f"""
            <div class="pvp-box">
                <div style="font-weight:bold; color:#333; font-size:1rem;">PVP SUGERIDO</div>
                <div class="pvp-value">${pvp_sug:,.0f}</div>
                <div style="margin-top:10px; font-size:0.9rem; font-weight:bold; color:#555;">MARGEN NETO: {margen_deseado}%</div>
            </div>
        """, unsafe_allow_html=True)

    st.divider()

    # FILA 2: AJUSTE MANUAL Y RESULTADOS
    col_final, col_res1, col_res2 = st.columns([1.2, 1, 1])
    
    with col_final:
        # Prioridad: 1. Precio buscado en MeLi | 2. PVP Sugerido
        base_pvp = st.session_state.precio_meli if st.session_state.precio_meli > 0 else pvp_sug
        pvp_final = st.number_input("PVP Final a Evaluar ($)", value=float(round(base_pvp, 0)))

    # Desglose Real
    c_fijo = 3030.0 if pvp_final < 33000 else 0.0
    peso_c = st.selectbox("Peso del bulto (Envío)", list(tarifario_envios.keys()), index=4)
    envio_r = tarifario_envios[peso_c] * (0.5 if "Verde" in reputacion else 1) if pvp_final >= 33000 else 0.0
    
    iva_r = (pvp_final - (pvp_final / 1.21)) if tipo_vend == "Responsable Inscripto" else 0.0
    iibb_r = (pvp_final / (1.21 if tipo_vend == "Responsable Inscripto" else 1)) * t_iibb
    comm_r = pvp_final * (comision/100)
    finan_r = pvp_final * t_finan
    
    gastos_totales = comm_r + c_fijo + envio_r + iva_r + iibb_r + finan_r
    ganancia = pvp_final - gastos_totales - st.session_state.costo
    margen_r = (ganancia / pvp_final) if pvp_final > 0 else 0

    with col_res1: st.metric("Ganancia Neta", f"$ {ganancia:,.2f}")
    with col_res2: st.metric("Margen Real", f"{margen_r:.2%}")

    with st.expander("📄 Ver Desglose Detallado"):
        df = pd.DataFrame({
            "Concepto": ["Compra", "Comisión MeLi", "Costo Fijo", "Envío", "IVA (ARCA)", "IIBB", "Financiación"],
            "Monto": [st.session_state.costo, comm_r, c_fijo, envio_r, iva_r, iibb_r, finan_r]
        })
        st.table(df.style.format({"Monto": "${:,.2f}"}))
