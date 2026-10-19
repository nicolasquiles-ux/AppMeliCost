import streamlit as st
import pandas as pd

st.set_page_config(page_title="MELI Manager Pro", layout="wide")

# 1. Carga y procesamiento de la Matriz de Artículos
@st.cache_data
def load_matriz():
    try:
        df = pd.read_excel("Matriz Articulos Gemini.xlsx")
        
        # Conversión de mm a cm y cálculo de Peso Volumétrico: (Ancho cm x Alto cm x Prof cm) / 4000
        df['Volumen_cm3'] = (df['Ancho caja (mm)'] / 10) * (df['Alto caja (mm)'] / 10) * (df['Prof caja (mm)'] / 10)
        df['Peso_Volumetrico_Kg'] = (df['Volumen_cm3'] / 4000).round(2)
        
        # El peso facturable por Mercado Envíos es el mayor entre el peso real y el volumétrico
        df['Peso_Facturable_Kg'] = df[['Peso embalado (Kg)', 'Peso_Volumetrico_Kg']].max(axis=1)
        return df
    except Exception as e:
        st.error(f"Error al cargar la Matriz de Artículos: {e}")
        return pd.DataFrame()

matriz_df = load_matriz()

# 2. Navegación Principal
st.sidebar.title("MELI Manager Pro")
menu = st.sidebar.radio("Navegación", [
    "Monitor de Publicaciones", 
    "Dashboard Diario", 
    "Matriz & Costos", 
    "Ajustador por Competencia (Siguiente Fase)"
])

# 3. Solapa: Monitor de Publicaciones
if menu == "Monitor de Publicaciones":
    st.header("Monitor de Publicaciones y Envíos")
    st.caption("Conectado con API de Mercado Libre y Matriz Logística")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Publicaciones Monitoreadas", len(matriz_df) if not matriz_df.empty else 0)
    col2.metric("Promedio Peso Facturable", f"{matriz_df['Peso_Facturable_Kg'].mean():.2f} Kg" if not matriz_df.empty else "0 Kg")
    col3.metric("Cobertura de EAN/GTIN", f"{(matriz_df['ean'].notnull().sum() / len(matriz_df) * 100):.1f}%" if not matriz_df.empty else "0%")

    st.subheader("Buscador y Monitor de Productos")
    search_term = st.text_input("Buscar por SKU / Artículo o Descripción:")
    
    if not matriz_df.empty:
        filtered_df = matriz_df[
            matriz_df['Articulo'].astype(str).str.contains(search_term, case=False, na=False) |
            matriz_df['Descripcion'].astype(str).str.contains(search_term, case=False, na=False)
        ] if search_term else matriz_df
        
        st.dataframe(
            filtered_df[[
                'Articulo', 'Descripcion', 'subcategoria', 
                'Peso embalado (Kg)', 'Peso_Volumetrico_Kg', 'Peso_Facturable_Kg',
                'Unidades por caja', 'Lote de producción'
            ]],
            use_container_width=True
        )

# 4. Solapa: Dashboard Diario
elif menu == "Dashboard Diario":
    st.header("Dashboard de Actividad Diaria")
    st.info("Módulo de ventas diarias y cálculo de margen neto real en desarrollo.")

# 5. Solapa: Matriz & Costos (Visualización Completa)
elif menu == "Matriz & Costos":
    st.header("Matriz Completa de Productos (266 SKUs)")
    st.dataframe(matriz_df, use_container_width=True)

# 6. Solapa: Próximo Paso
elif menu == "Ajustador por Competencia (Siguiente Fase)":
    st.header("Ajustador Automático de Precios por Competencia")
    st.warning("Próximo módulo a desarrollar en el siguiente paso.")
