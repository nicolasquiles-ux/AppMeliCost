import streamlit as st
import pandas as pd
import requests
import re
import json
import os

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="NQ Sales Intelligence Matrix Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { background-color: #f4f6f9; }
    .stMetric { background-color: #ffffff; padding: 18px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .stButton>button { border-radius: 8px; font-weight: 600; }
    .card-viable { background-color: #d4edda; color: #155724; padding: 15px; border-radius: 8px; border: 1px solid #c3e6cb; }
    .card-noviable { background-color: #f8d7da; color: #721c24; padding: 15px; border-radius: 8px; border: 1px solid #f5c6cb; }
    .badge-missing { background-color: #ff4d4d; color: white; padding: 10px; border-radius: 6px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CREDENCIALES Y OAUTH DE MERCADO LIBRE
# ==========================================
CLIENT_ID = st.secrets.get("MELI_CLIENT_ID", "7265495583900621")
CLIENT_SECRET = st.secrets.get("MELI_CLIENT_SECRET", "")
REDIRECT_URI = st.secrets.get("REDIRECT_URI", "https://melicost.streamlit.app").strip().rstrip("/")

CATEGORIAS_MELI = {
    "Aparadores, Vajilleros y Cómodas (MLA433221)": "MLA433221",
    "Bibliotecas, Estanterías y Repisas (MLA37209)": "MLA37209",
    "Respaldos de Cama y Sommiers (MLA432095)": "MLA432095",
    "Escritorios (MLA35254)": "MLA35254",
    "Mesas de Noche / Auxiliares (MLA37207)": "MLA37207",
    "Muebles para TV y Centros de Entretenimiento (MLA433223)": "MLA433223",
    "Placard y Roperos (MLA37210)": "MLA37210"
}

# ==========================================
# 3. ESTADO DE SESIÓN (SESSION STATE)
# ==========================================
if "authenticated_app" not in st.session_state:
    st.session_state["authenticated_app"] = False
if "access_token" not in st.session_state:
    st.session_state["access_token"] = ""
if "user_info" not in st.session_state:
    st.session_state["user_info"] = {}
if "lista_gold_df" not in st.session_state:
    st.session_state["lista_gold_df"] = None
if "matriz_custom_df" not in st.session_state:
    st.session_state["matriz_custom_df"] = None
if "selected_pub_data" not in st.session_state:
    st.session_state["selected_pub_data"] = {}
if "search_query_mon" not in st.session_state:
    st.session_state["search_query_mon"] = "7798274755803"

# ==========================================
# 4. FUNCIONES DE API, LOGÍSTICA Y CÁLCULOS
# ==========================================
def obtener_url_login_meli():
    return f"https://auth.mercadolibre.com.ar/authorization?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"

def intercambiar_code_por_token(code: str):
    url = "https://api.mercadolibre.com/oauth/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
    try:
        res = requests.post(url, data=payload, headers=headers, timeout=10)
        if res.status_code == 200:
            return True, res.json()
        else:
            err_data = res.json() if res.content else {}
            return False, err_data.get("message", f"Error HTTP {res.status_code}")
    except Exception as e:
        return False, str(e)

def obtener_perfil_meli(token: str):
    if not token:
        return {}
    url = "https://api.mercadolibre.com/users/me"
    headers = {"Authorization": f"Bearer {token.strip()}"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {}

def actualizar_item_meli(item_id: str, nuevo_precio: float, access_token: str):
    if not access_token:
        return False, "⚠️ Debés conectar Mercado Libre o ingresar un Access Token directo."
    
    clean_item_id = str(item_id).strip().upper()
    if not clean_item_id.startswith("MLA"):
        num = re.sub(r'\D', '', clean_item_id)
        if num:
            clean_item_id = f"MLA{num}"

    url = f"https://api.mercadolibre.com/items/{clean_item_id}"
    headers = {
        "Authorization": f"Bearer {access_token.strip()}",
        "Content-Type": "application/json"
    }
    payload = {"price": round(float(nuevo_precio), 2)}
    
    try:
        res = requests.put(url, json=payload, headers=headers, timeout=10)
        if res.status_code in [200, 201]:
            return True, f"✅ Publicación **{clean_item_id}** actualizada exitosamente a **${nuevo_precio:,.2f}**."
        else:
            err = res.json() if res.content else {}
            msg = err.get("message", f"Error HTTP {res.status_code}")
            return False, f"❌ Error API MeLi ({res.status_code}): {msg}"
    except Exception as e:
        return False, f"❌ Excepción de conexión: {str(e)}"

def procesar_archivo_lista_gold(file):
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        if not any('ean' in str(c).lower() for c in df.columns):
            for i in range(min(5, len(df))):
                row_vals = [str(x).lower() for x in df.iloc[i].values]
                if any('ean' in v for v in row_vals):
                    if file.name.endswith('.csv'):
                        df = pd.read_csv(file, header=i+1)
                    else:
                        df = pd.read_excel(file, header=i+1)
                    break
        return df
    except Exception as e:
        st.error(f"Error al procesar archivo: {e}")
        return None

def calcular_costo_envio_por_peso_facturable(peso_facturable: float) -> float:
    if pd.isna(peso_facturable) or peso_facturable <= 0:
        return 15000.0
    elif peso_facturable <= 3:
        return 8500.0
    elif peso_facturable <= 5:
        return 12000.0
    elif peso_facturable <= 10:
        return 17500.0
    elif peso_facturable <= 15:
        return 22000.0
    elif peso_facturable <= 20:
        return 28500.0
    elif peso_facturable <= 30:
        return 36000.0
    elif peso_facturable <= 50:
        return 48000.0
    else:
        return 65000.0

def procesar_matriz_articulos_df(df):
    try:
        df['Ancho_cm'] = df['Ancho caja (mm)'] / 10
        df['Alto_cm'] = df['Alto caja (mm)'] / 10
        df['Prof_cm'] = df['Prof caja (mm)'] / 10
        df['Volumen_cm3'] = df['Ancho_cm'] * df['Alto_cm'] * df['Prof_cm']
        df['Peso_Volumetrico_Kg'] = (df['Volumen_cm3'] / 4000).round(2)
        df['Peso_Facturable_Kg'] = df[['Peso embalado (Kg)', 'Peso_Volumetrico_Kg']].max(axis=1)
        df['Costo_Logistico_Estimado'] = df['Peso_Facturable_Kg'].apply(calcular_costo_envio_por_peso_facturable)
        return df
    except Exception as e:
        st.error(f"Error procesando columnas de la matriz: {e}")
        return df

def cargar_matriz_articulos_oficial():
    if st.session_state["matriz_custom_df"] is not None:
        return st.session_state["matriz_custom_df"]
    
    file_path = "Matriz Articulos Gemini.xlsx"
    if os.path.exists(file_path):
        try:
            df = pd.read_excel(file_path)
            return procesar_matriz_articulos_df(df)
        except Exception:
            pass
            
    return None

def buscar_datos_en_matriz(clave_busqueda: str):
    matriz_df = cargar_matriz_articulos_oficial()
    if matriz_df is None:
        return False, 0.0, 0.0, 0.0, ""

    q_clean = re.sub(r'\D', '', str(clave_busqueda).strip())
    if not q_clean:
        return False, 0.0, 0.0, 0.0, ""

    for col in ['ean', 'Articulo']:
        if col in matriz_df.columns:
            series_clean = (
                matriz_df[col]
                .fillna('')
                .astype(str)
                .str.split('.')
                .str[0]
                .str.replace(r'\D', '', regex=True)
            )
            matches = matriz_df[series_clean == q_clean]
            if not matches.empty:
                row = matches.iloc[0]
                peso_fact = float(row.get('Peso_Facturable_Kg', 10.0))
                costo_env = float(row.get('Costo_Logistico_Estimado', 28500.0))
                peso_real = float(row.get('Peso embalado (Kg)', 0.0))
                desc = str(row.get('Descripcion', ''))
                return True, costo_env, peso_fact, peso_real, desc

    return False, 0.0, 0.0, 0.0, ""

def extraer_opciones_ean_lista_gold():
    if st.session_state["lista_gold_df"] is None:
        return []
    
    df = st.session_state["lista_gold_df"]
    opciones = []
    
    ean_col = next((c for c in df.columns if any(k in str(c).lower() for k in ["ean", "gtin", "codigo", "código"])), None)
    desc_col = next((c for c in df.columns if any(k in str(c).lower() for k in ["descrip", "nombre", "titulo", "producto"])), None)
    art_col = next((c for c in df.columns if any(k in str(c).lower() for k in ["articul", "modelo"])), None)

    if not ean_col:
        return []

    for _, row in df.iterrows():
        val_ean = re.sub(r'\D', '', str(row[ean_col]).split('.')[0])
        if len(val_ean) >= 8:
            desc = str(row[desc_col]) if desc_col and pd.notna(row[desc_col]) else ""
            art = str(row[art_col]) if art_col and pd.notna(row[art_col]) else ""
            label = f"{val_ean} — {art} {desc}".strip()
            opciones.append((label, val_ean))

    return opciones

def limpiar_precio_moneda(valor_raw):
    if pd.isna(valor_raw):
        return 0.0
    val_str = str(valor_raw
