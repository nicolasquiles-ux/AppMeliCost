import streamlit as st
import pandas as pd
import requests
import re

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="MeLi Intelligence Pro", layout="wide", page_icon="🚀")

# --- CLAVE DE ACCESO PRO ---
CLAVE_CORRECTA = "CENTRO_PRO_2026"

# --- ESTILOS CSS AVANZADOS ---
st.markdown("""
    <style>
    /* Destacar el PVP Sugerido */
    .pvp-box {
        background-color: #ffe600;
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        border: 2px solid #e6cf00;
        margin-bottom: 20px;
    }
    .pvp-label { font-size: 1.2rem; font-weight: bold; color: #333; }
    .pvp-value { font-size: 3rem; font-weight: 900; color: #000; }
    
    /* Estilo de métricas secundarias */
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .whatsapp-button { background-color: #25d366; color: white !important; padding: 12px 20px; border-radius: 8px; text-decoration: none; font-weight: bold; display: block; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES DE BÚSQUEDA ROBUSTA ---
def buscar_en_meli(id_input):
    if not id_input: return {"status": "error", "mensaje": "Ingresá un ID"}
    
    # Limpieza total del ID
    id_limpio = re.sub(r'\D', '', id_input) # Solo números
    
    intentos = [
        f"https://api.mercadolibre.com/items/MLA{id_limpio}",      # Opción 1: Publicación
        f"https://api.mercadolibre.com/products/MLA{id_limpio}",   # Opción 2: Catálogo con MLA
        f"https://api.mercadolibre.com/products/{id_limpio}"       # Opción 3: Catálogo puro
    ]
    
    for url in intentos:
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                # Normalizamos la respuesta según si es Item o Producto
                titulo = data.get("title") or data.get("name")
                precio = data.get("price") or data.get("buy_box_winner", {}).get("price")
                imagen = data.get("thumbnail") or (data.get("pictures")[0].get("url") if data.get("pictures") else "")
                if precio:
                    return {"titulo": titulo, "precio": precio, "imagen": imagen, "status": "ok"}
        except: continue
        
    return {"status": "error", "mensaje": "ID no encontrado. Verificá que el código sea correcto."}

# --- DATA DE REFERENCIA ---
tarifario_envios = {
    "0.5 kg (Sobres)": 4800.0, "1 kg": 5200.0, "2 kg": 5900.0, "5 kg": 7400.0,
    "10 kg": 9800.0, "15 kg": 12500.0, "20 kg": 15200.0, "25 kg": 18400.0,
    "30 kg (Límite)": 22000.0, "Especial (Muebles)": 35000.0
}
tasas_financiacion = {"1 Pago": 0.0, "3 Pagos": 12.5, "6 Pagos": 23.8, "9 Pagos": 35.0, "12 Pagos": 45.0}

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔐 Acceso")
    clave = st.text_input("Clave Pro", type="password")
    es_pro = (clave == CLAVE_CORRECTA)
    if not es_pro:
        st.markdown(f'<a href="https://wa.me/5491165808113" class="whatsapp-button">Pedir Clave Pro</a>', unsafe_allow_html=True)
    st.divider()
    reputacion = st.selectbox("Reputación", ["Verde (50%)", "Amarilla (40%)", "Roja (0%)"])
    tipo_vend = st.radio("IVA", ["Responsable Inscripto", "Monotributista"])
    iibb_tax = st.number_input("% IIBB", value=3.5)

# --- APP ---
st.title("🚀 MeLi Intelligence Pro")

tab_calc, tab_mla = st.tabs(["🧮 Calculadora", "🔍 Buscador MeLi"])

if 'precio_buscado' not in st.session_state: st.session_state.precio_buscado = 0.0

with tab_mla:
    st.subheader("Buscador de Competencia")
    mla_input = st.text_input("Pegá el código (ej: 27392194)")
    if st.button("Consultar MeLi", use_container_width=True):
        if not es_pro: st.error("Función Pro bloqueada.")
        else:
            res = buscar_en_meli(mla_input)
            if res["status"] == "ok":
                st.session_state.precio_buscado = float(res["precio"])
                st.success(f"Encontrado: {res['titulo']}")
                st.metric("Precio Competencia", f"$ {res['precio']:,.2f}")
            else: st.error(res["mensaje"])

with tab_calc:
    # FILA PRINCIPAL: PVP DESTACADO A LA IZQUIERDA
    col_pvp, col_inputs = st.columns([1.2, 2])
    
    # Lógica de cálculo primero para mostrar en el box
    costo_compra = st.session_state.get('costo_input', 15000.0)
    margen_obj = st.session_state.get('margen_input', 20)
    comision_base = st.session_state.get('comision_input', 15.0)
    tasa_f = tasas_financiacion[st.session_state.get('plan_input', '1 Pago')]
    
    t_iva = 0.1735 if tipo_vend == "Responsable Inscripto" else 0.0
    t_iibb = iibb_tax / 100
    divisor = (1 - (comision_base/100) - (margen_obj/100) - t_iibb - t_iva - (tasa_f/100))
    
    # Estimación envío para sugerencia
    peso_sel = st.session_state.get('peso_input', "10 kg")
    dcto_e = 0.5 if "Verde" in reputacion else 0.6
    c_envio_lista = tarifario_envios[peso_sel]
    
    pvp_sugerido = (costo_compra + (c_envio_lista * dcto_e)) / divisor if divisor > 0 else 0
    
    with col_pvp:
        st.markdown(f"""
            <div class="pvp-box">
                <div class="pvp-label">PVP SUGERIDO</div>
                <div class="pvp-value">$ {pvp_sugerido:,.0f}</div>
                <p style="color: #666; margin-top:10px;">Para ganar el {margen_obj}% neto</p>
            </div>
        """, unsafe_allow_html=True)

    with col_inputs:
        sub1, sub2 = st.columns(2)
        with sub1:
            st.session_state.costo_input = st.number_input("Costo Compra ($)", value=15000.0)
            st.session_state.plan_input = st.selectbox("Cuotas", list(tasas_financiacion.keys()))
        with sub2:
            st.session_state.margen_input = st.slider("% Margen", 5, 50, 20)
            st.session_state.comision_input = st.number_input("% Comisión MeLi", value=15.0)

    st.divider()
    
    # SEGUNDA FILA: PRECIO FINAL Y MÉTRICAS
    col_venta, col_m1, col_m2 = st.columns([1, 1, 1])
    
    with col_venta:
        val_pvp = st.session_state.precio_buscado if st.session_state.precio_buscado > 0 else pvp_sugerido
        precio_final = st.number_input("PVP Final (Editable)", value=float(round(val_pvp, 0)))
    
    # Recálculo con precio final
    costo_fijo = 3030.0 if precio_final < 33000 else 0.0
    envio_r = c_envio_lista * dcto_e if precio_final >= 33000 else 0.0
    iva_r = (precio_final - (precio_final / 1.21)) if tipo_vend == "Responsable Inscripto" else 0.0
    iibb_r = (precio_final / (1.21 if tipo_vend == "Responsable Inscripto" else 1)) * (iibb_tax/100)
    comm_r = precio_final * (comision_base / 100)
    finan_r = precio_final * (tasa_f / 100)
    
    total_g = comm_r + costo_fijo + envio_r + iva_r + iibb_r + finan_r
    ganancia = precio_final - total_g - costo_compra
    margen_r = (ganancia / precio_final) if precio_final > 0 else 0

    with col_m1: st.metric("Ganancia Neta", f"$ {ganancia:,.2f}")
    with col_m2: st.metric("Margen Real", f"{margen_r:.2%}")

    with st.expander("📊 Desglose de Gastos"):
        st.session_state.peso_input = st.selectbox("Peso para envío", list(tarifario_envios.keys()))
        df = pd.DataFrame({
            "Concepto": ["Compra", "Comisión", "Fijo", "Envío", "IVA", "IIBB", "Finan"],
            "Monto": [costo_compra, comm_r, costo_fijo, envio_r, iva_r, iibb_r, finan_r]
        })
        st.table(df.style.format({"Monto": "${:,.2f}"}))
