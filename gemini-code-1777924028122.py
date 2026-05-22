import streamlit as st

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Centro Estant | Sales Intelligence V13.1", layout="centered")

# =========================================================
# DATOS MAESTROS
# =========================================================
TABLA_ME1 = {
    "Hasta 0,3 Kg": 6080.0, "0,3 a 0,5 Kg": 6600.0, "0,5 a 1 Kg": 7470.0,
    "1 a 2 Kg": 7970.0, "2 a 5 Kg": 10760.0, "5 a 10 Kg": 12840.0,
    "10 a 15 Kg": 14930.0, "15 a 20 Kg": 17830.0, "20 a 25 Kg": 21420.0,
    "25 a 30 Kg": 29410.0, "30 a 40 Kg": 33570.0, "40 a 50 Kg": 35490.0,
    "50 a 60 Kg": 39610.0, "60 a 70 Kg": 41290.0, "70 a 80 Kg": 47850.0,
    "80 a 90 Kg": 59180.0, "90 a 100 Kg": 68230.0, "100 a 120 Kg": 74490.0,
    "120 a 140 Kg": 83890.0, "140 a 160 Kg": 93280.0, "160 a 180 Kg": 102660.0,
    "Mas de 180 Kg": 112060.0
}

FINANCIACION = {
    "1 Pago": 0.0,
    "3 Cuotas (5% Promo)": 5.0,
    "3 Cuotas (8.40% Actual)": 8.40,
    "6 Cuotas (12.30% Actual)": 12.30,
    "9 Cuotas (15.70% Actual)": 15.70,
    "12 Cuotas (19.20% Actual)": 19.20
}

CLAVE_CORRECTA = "CENTRO_PRO_2026"

# --- CSS: DISEÑO SOBRIO Y PROFESIONAL ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F4F7F9; }

    .stNumberInput input, .stSelectbox div {
        background-color: white !important;
        border: 1px solid #D1D9E0 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        color: #1A202C !important;
    }

    .dash-main {
        background-color: #0F172A; color: white; padding: 30px;
        border-radius: 12px; text-align: center;
        border-bottom: 5px solid #3B82F6; margin-bottom: 25px;
    }
    .dash-main-inverse {
        background-color: #1E293B; color: white; padding: 30px;
        border-radius: 12px; text-align: center;
        border-bottom: 5px solid #10B981; margin-bottom: 25px;
    }
    .dash-label { font-size: 0.9rem; text-transform: uppercase; letter-spacing: 2px; color: #94A3B8; }
    .dash-price { font-size: 3.5rem; font-weight: 900; color: #FFFFFF; margin: 10px 0; }
    .dash-margin { background: #0F172A; display: inline-block; padding: 5px 15px; border-radius: 20px; font-size: 0.9rem; color: #10B981; font-weight: bold; }

    .btn-wa {
        background-color: #1E293B; color: white !important; padding: 12px;
        border-radius: 8px; text-align: center; text-decoration: none;
        display: block; font-weight: bold; margin-top: 20px; border: 1px solid #334155;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st
