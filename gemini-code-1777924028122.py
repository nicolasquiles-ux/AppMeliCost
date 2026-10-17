import streamlit as st
import pandas as pd
import requests

# ==========================================
# CONFIGURACIÓN DE PÁGINA DE STREAMLIT
# ==========================================
st.set_page_config(
    page_title="NQ Sales Intelligence Matrix",
    page_icon="⚡",
    layout="wide"
)

# ==========================================
# ESTADO DE SESIÓN (SESSION STATE)
# ==========================================
if "access_token" not in st.session_state:
    st.session_state["access_token"] = ""
if "lista_gold_df" not in st.session_state:
    st.session_state["lista_gold_df"] = None

# ==========================================
# FUNCIONES DE COMUNICACIÓN CON MERCADO LIBRE
# ==========================================
def publicar_item_en_catalogo(
    catalog_product_id: str,
    precio_venta: float,
    listing_type_id: str = "gold_pro",
    quantity: int = 1,
    condition: str = "new",
    access_token: str = None
):
    """
    Ejecuta la publicación directa vinculada al Catálogo / Buy Box de Mercado Libre.
    Endpoint: POST /items
    """
    if not access_token:
        return False, "⚠️ Se requiere un Access Token activo de Mercado Libre para publicar."

    url = "https://api.mercadolibre.com/items"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "site_id": "MLA",
        "catalog_product_id": catalog_product_id,
        "price": round(precio_venta, 2),
        "currency_id": "ARS",
        "available_quantity": quantity,
        "buying_mode": "buy_it_now",
        "listing_type_id": listing_type_id,
        "condition": condition
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code in [200, 201]:
            data = response.json()
            return True, {
                "item_id": data.get("id"),
                "permalink": data.get("permalink"),
                "message": f"✅ ¡Publicación creada con éxito en el catálogo! ID: {data.get('id')}"
            }
        else:
            err_data = response.json()
            err_msg = err_data.get("message", "Error devuelto por la API de Mercado Libre")
            return False, f"❌ Error ({response.status_code}): {err_msg}"
    except Exception as e:
        return False, f"❌ Excepción durante la conexión: {str(e)}"


def consultar_producto_catalogo(catalog_id: str):
    """
    Obtiene los detalles del producto de catálogo mediante la API pública de MeLi.
    """
    url = f"https://api.mercadolibre.com/products/{catalog_id}"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None

# ==========================================
# ESTRUCTURA DE LA INTERFAZ (UI / TABS)
# ==========================================
st.title("⚡ NQ Sales Intelligence Matrix v46")
st.caption("Sistema Integrado de Análisis Comercial y Publicación Directa en Mercado Libre")

# Barra lateral para Token y Configuración
with st.sidebar:
    st.header("🔑 Autenticación MeLi")
    st.session_state["access_token"] = st.text_input(
        "Access Token (OAuth)",
        value=st.session_state["access_token"],
        type="password",
        help="Token de acceso otorgado por Mercado Libre con permisos de escritura"
    )
    
    st.markdown("---")
    st.header("📄 Carga Lista Gold")
    uploaded_file = st.file_uploader("Cargar Excel / CSV con costos baseline", type=["xlsx", "xls", "csv"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                st.session_state["lista_gold_df"] = pd.read_csv(uploaded_file)
            else:
                st.session_state["lista_gold_df"] = pd.read_excel(uploaded_file)
            st.success("Lista Gold cargada correctamente.")
        except Exception as e:
            st.error(f"Error al leer la Lista Gold: {e}")

# Pestañas principales de trabajo
tabs = st.tabs([
    "1. Resumen",
    "2. Competencia",
    "3. Costos & Lista Gold",
    "4. Financiación & Cuotas",
    "5. Envíos & Logística",
    "6. Matriz de Margen",
    "7. Publicador & Monitor de Catálogo"
])

# ------------------------------------------
# TAB 7: PUBLICADOR Y MONITOR DE CATÁLOGO
# ------------------------------------------
with tabs[6]:
    st.subheader("📦 Publicación Directa en Catálogo de Mercado Libre")
    st.write("Escribí o seleccioná un producto de catálogo para evaluar la viabilidad e ingresar a la competencia.")

    col_cat1, col_cat2 = st.columns([2, 1])

    with col_cat1:
        catalog_id_input = st.text_input(
            "ID de Producto de Catálogo (catalog_product_id)",
            value="MLA12345678",
            help="Ejemplo: MLA20491823"
        )
    
    with col_cat2:
        costo_base_input = st.number_input(
            "Costo Producto (Lista Gold)",
            min_value=0.0,
            value=10000.0,
            step=500.0
        )

    # Detalle dinámico del producto seleccionado
    if catalog_id_input:
        cat_info = consultar_producto_catalogo(catalog_id_input)
        if cat_info:
            st.info(f"**Producto:** {cat_info.get('title', 'Sin Título')} | **Categoría:** {cat_info.get('category_id', 'N/A')}")
        else:
            st.warning("No se pudieron cargar los datos del catálogo desde la API pública. Podés continuar manualmente.")

    st.markdown("---")
    st.subheader("⚙️ Configuración del Precio y Tipo de Publicación")

    col_conf1, col_conf2, col_conf3 = st.columns(3)

    with col_conf1:
        modalidad_sel = st.selectbox(
            "Tipo de Publicación / Financiación",
            [
                "Premium (Cuotas sin interés - gold_pro)",
                "Clásica (1 pago / Cuotas con interés - gold_special)"
            ]
        )
        listing_code = "gold_pro" if "Premium" in modalidad_sel else "gold_special"

    with col_conf2:
        pvp_objetivo = st.number_input(
            "Precio de Venta Objetivo ($ ARS)",
            min_value=0.0,
            value=25000.0,
            step=1000.0
        )

    with col_conf3:
        cantidad_stock = st.number_input(
            "Stock Inicial a Publicar",
            min_value=1,
            value=5,
            step=1
        )

    # Cálculo preliminar de comisiones y margen estimado
    comision_estimada = pvp_objetivo * (0.15 if listing_code == "gold_special" else 0.28)
    margen_neto_est = pvp_objetivo - costo_base_input - comision_estimada

    st.metric(
        label="Margen Estimado",
        value=f"${margen_neto_est:,.2f}",
        delta=f"{(margen_neto_est / pvp_objetivo * 100):.1f}% sobre PVP" if pvp_objetivo > 0 else "0%"
    )

    st.markdown("---")
    
    # Botón de acción para realizar la publicación en live
    col_act1, col_act2 = st.columns([2, 1])
    
    with col_act1:
        st.write("Verificá los valores antes de ejecutar la acción.")
    
    with col_act2:
        if st.button("🚀 PUBLICAR EN MERCADO LIBRE", type="primary", use_container_width=True):
            with st.spinner("Procesando publicación en Mercado Libre..."):
                exito, resultado = publicar_item_en_catalogo(
                    catalog_product_id=catalog_id_input,
                    precio_venta=pvp_objetivo,
                    listing_type_id=listing_code,
                    quantity=int(cantidad_stock),
                    access_token=st.session_state.get("access_token")
                )

                if exito:
                    st.success(resultado["message"])
                    st.markdown(f"👉 [Abrir publicación creada en Mercado Libre]({resultado['permalink']})")
                else:
                    st.error(resultado)
