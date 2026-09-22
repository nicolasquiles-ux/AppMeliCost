import streamlit as st
import pandas as pd
import math
import re

=========================================================

CONFIGURACIÓN DE PÁGINA Y CONSTANTES GENERALES

=========================================================

V_NUMBER = "29.0"

st.set_page_config(
page_title=f"Calculadora MeLi v{V_NUMBER} - Estrategia & Matriz",
page_icon="📦",
layout="wide"
)

Constantes Mercado Libre (Actualizables según tarifario vigente)

CARGO_FIJO_MELI = 1300.0        # Cargo fijo por unidad en ventas < $33.000
UMBRAL_ENVIO_GRATIS = 33000.0   # Umbral donde el envío gratis es obligatorio/subvencionado

Tarifario base de fletes según categoría de peso (ME2 / Tradicional)

TARIFAS_FLETE_BASE = {
"Hasta 0,3 kg": 2800.0,
"De 0,3 a 0,5 kg": 3200.0,
"De 0,5 a 1 kg": 3900.0,
"De 1 a 1,5 kg": 4500.0,
"De 1,5 a 2 kg": 5100.0,
"De 2 a 3 kg": 5900.0,
"De 4 a 5 kg": 7200.0,
"De 8 a 10 kg": 10500.0,
"De 13 a 15 kg": 13800.0,
"De 15 a 20 kg": 16500.0,
"De 20 a 25 kg": 19800.0,
"De 25 a 30 kg": 23500.0,
"De 30 a 40 kg": 2900.0
}

=========================================================

FUNCIONES AUXILIARES Y LÓGICA DE CÁLCULO

=========================================================

def mapear_peso_categoria(val):
"""Mapea pesos numéricos o cadenas del CSV/Excel a las categorías oficiales de MeLi."""
if pd.isna(val):
return "De 1,5 a 2 kg"
val_str = str(val).lower().replace(",", ".").strip()
try:
num_peso = float(re.findall(r"[-+]?\d*.\d+|\d+", val_str)[0])
if num_peso <= 0.3: return "Hasta 0,3 kg"
elif num_peso <= 0.5: return "De 0,3 a 0,5 kg"
elif num_peso <= 1.0: return "De 0,5 a 1 kg"
elif num_peso <= 1.5: return "De 1 a 1,5 kg"
elif num_peso <= 2.0: return "De 1,5 a 2 kg"
elif num_peso <= 3.0: return "De 2 a 3 kg"
elif num_peso <= 5.0: return "De 4 a 5 kg"
elif num_peso <= 10.0: return "De 8 a 10 kg"
elif num_peso <= 15.0: return "De 13 a 15 kg"
elif num_peso <= 20.0: return "De 15 a 20 kg"
elif num_peso <= 25.0: return "De 20 a 25 kg"
elif num_peso <= 30.0: return "De 25 a 30 kg"
else: return "De 30 a 40 kg"
except Exception:
return "De 1,5 a 2 kg"

def mapear_modalidad(val):
"""Mapea tipos de flete/logística del archivo cargado."""
if pd.isna(val):
return "Mercado Envíos Tradicional (ME2)"
v = str(val).lower().strip()
if "flex" in v or "m2" in v:
return "Mercado Envíos Flex"
elif "full" in v or "m3" in v:
return "Mercado Envíos Full"
return "Mercado Envíos Tradicional (ME2)"

def calcular_flete_segun_modalidad(pvp, peso_cat, mod_log, costo_moto, reemb_flex, full_unit, full_stor):
"""Calcula el costo del envío asumido por el vendedor según reglas de MeLi."""
if mod_log == "ME1":
return 0.0

flete_base = TARIFAS_FLETE_BASE.get(peso_cat, 5100.0)

# Subsidio de MeLi en publicaciones > UMBRAL
if pvp >= UMBRAL_ENVIO_GRATIS:
    costo_envio = flete_base * 0.50  # 50% de bonificación / costo asumido por vendedor
else:
    costo_envio = flete_base
    
if mod_log == "Mercado Envíos Flex":
    costo_envio += max(0.0, costo_moto - reemb_flex)
elif mod_log == "Mercado Envíos Full":
    costo_envio += (full_unit + full_stor)
    
return costo_envio


def calcular_pvp_recomendado_func(
costo_f, margen_deseado, t_finan, modalidad_log, peso_cat,
costo_moto=0.0, reemb_flex=0.0, full_unit=0.0, full_stor=0.0,
t_comi_base=0.1415, t_iva_prod=0.21, t_iibb=0.035, t_ganancias_fijo=0.02, tipo_iva="Responsable Inscripto"
):
"""
Motor matemático que despeja el PVP ideal para obtener el margen neto objetivo exacto.
"""
if costo_f <= 0:
return 0.0

# Iteración de convergencia para equilibrar umbrales de envío gratis y cargos fijos
pvp_est = costo_f * 2.0
for _ in range(5):
    flete = calcular_flete_segun_modalidad(pvp_est, peso_cat, modalidad_log, costo_moto, reemb_flex, full_unit, full_stor)
    fijo = CARGO_FIJO_MELI if pvp_est < UMBRAL_ENVIO_GRATIS else 0.0
    
    # Denominador de margen según régimen impositivo
    tasa_comision_total = t_comi_base + t_finan
    
    if tipo_iva == "Monotributista":
        denominador = 1.0 - margen_deseado - tasa_comision_total - t_iibb - t_ganancias_fijo
        if denominador <= 0:
            return 0.0
        pvp_est = (costo_f + flete + fijo) / denominador
    else:
        # Responsable Inscripto (Cálculo neto de IVA)
        factor_tax = (1.0 / (1.0 + t_iva_prod))
        denominador = (factor_tax * (1.0 - t_iibb - t_ganancias_fijo)) - tasa_comision_total - margen_deseado
        if denominador <= 0:
            return 0.0
        costo_neto = costo_f / (1.0 + t_iva_prod)
        pvp_est = (costo_neto + (flete / 1.21) + (fijo / 1.21)) / denominador

return max(0.0, round(pvp_est, 2))


=========================================================

ESTRUCTURA DE LA APLICACIÓN (SIDEBAR & TABS)

=========================================================

st.title("📊 Calculadora MeLi v29.0 & Análisis de Catálogo")
st.caption("Optimización de Precios, Márgenes Netos, Publicación Masiva y Análisis Competitivo de Catálogo (Buy Box).")

--- SIDEBAR: PARÁMETROS IMPOSITIVOS Y GENERALES ---

st.sidebar.header("⚙️ Parámetros Impositivos")
tipo_iva = st.sidebar.selectbox("Régimen Fiscal", ["Responsable Inscripto", "Monotributista"], index=0)
t_iva_prod = st.sidebar.number_input("IVA Productos (%)", value=21.0, step=0.5) / 100
t_comi_base = st.sidebar.number_input("Comisión Base MeLi (%)", value=14.15, step=0.05) / 100
t_iibb = st.sidebar.number_input("Retención IIBB (%)", value=3.5, step=0.1) / 100
t_ganancias_fijo = st.sidebar.number_input("Retención Ganancias (%)", value=2.0, step=0.1) / 100

st.sidebar.markdown("---")
st.sidebar.info("💡 Nota: La v29 contempla exención de cargos fijos en publicaciones superiores a $33.000 y subsidios logísticos de hasta un 50%.")

PESTAÑAS PRINCIPALES

tab1, tab5, tab6 = st.tabs([
"🧮 Calculadora Unitarias",
"📥 Carga Masiva (Matriz Precios)",
"🏆 Análisis de Catálogo (Buy Box)"
])

=========================================================

SOLAPA 1: CALCULADORA UNITARIA

=========================================================

with tab1:
st.subheader("Cálculo Individual por Producto")
col1, col2 = st.columns(2)

with col1:
    costo_unit = st.number_input("Costo Base del Producto ($)", value=15000.0, step=500.0)
    margen_unit = st.number_input("Margen Neto Objetivo (%)", value=12.0, step=0.5) / 100
    peso_cat_u = st.selectbox("Categoría de Peso", list(TARIFAS_FLETE_BASE.keys()), index=4)
    mod_log_u = st.selectbox("Modalidad Logística", ["Mercado Envíos Tradicional (ME2)", "Mercado Envíos Flex", "Mercado Envíos Full", "ME1"], index=0)
    
with col2:
    tasa_cuotas_u = st.selectbox("Plan de Financiamiento", [
        "Clásica / 1 Pago (0%)",
        "Premium / 3 Cuotas (8.40%)",
        "Premium / 6 Cuotas (12.30%)",
        "Premium / 9 Cuotas (15.70%)",
        "Premium / 12 Cuotas (19.20%)"
    ], index=0)
    
    tasa_finan_val = 0.0
    if "3 Cuotas" in tasa_cuotas_u: tasa_finan_val = 0.084
    elif "6 Cuotas" in tasa_cuotas_u: tasa_finan_val = 0.123
    elif "9 Cuotas" in tasa_cuotas_u: tasa_finan_val = 0.157
    elif "12 Cuotas" in tasa_cuotas_u: tasa_finan_val = 0.192

if st.button("🚀 Calcular PVP Unitario", use_container_width=True):
    pvp_res = calcular_pvp_recomendado_func(
        costo_f=costo_unit,
        margen_deseado=margen_unit,
        t_finan=tasa_finan_val,
        modalidad_log=mod_log_u,
        peso_cat=peso_cat_u,
        t_comi_base=t_comi_base,
        t_iva_prod=t_iva_prod,
        t_iibb=t_iibb,
        t_ganancias_fijo=t_ganancias_fijo,
        tipo_iva=tipo_iva
    )
    
    flete_res = calcular_flete_segun_modalidad(pvp_res, peso_cat_u, mod_log_u, 0, 0, 0, 0)
    fijo_res = CARGO_FIJO_MELI if pvp_res < UMBRAL_ENVIO_GRATIS else 0.0
    comi_res = pvp_res * (t_comi_base + tasa_finan_val)
    
    st.success(f"### PVP Sugerido: **${pvp_res:,.2f}**")
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Comisión Total MeLi", f"${comi_res:,.2f}")
    col_m2.metric("Costo Flete", f"${flete_res:,.2f}")
    col_m3.metric("Cargo Fijo", f"${fijo_res:,.2f}")
    col_m4.metric("Ganancia Neta Est.", f"${(pvp_res * margen_unit):,.2f}")


=========================================================

SOLAPA 5: PROCESAMIENTO MASIVO (AUTOMÁTICO DESDE ARCHIVO)

=========================================================

with tab5:
st.subheader("📥 Carga Masiva de SKUs y Cálculo de Matriz")
st.write("Subí tu archivo CSV o Excel. El sistema procesará las variables dinámicamente desde tus columnas y generará todas las variantes de publicación.")

c_m1, c_m2 = st.columns(2)
with c_m1:
    margen_global_m = st.number_input("% Margen Neto Objetivo Global", value=10.0, step=0.5, key="m_glob_m") / 100
with c_m2:
    st.info("💡 **Tasas aplicadas en la matriz:** Clásica (0%) | 3C (8.4%) | 6C (12.3%) | 9C (15.7%) | 12C (19.2%)")

archivo_subido = st.file_uploader("Subí tu catálogo (.xlsx o .csv)", type=["xlsx", "csv"], key="uploader_masivo_tab5")

def procesar_matriz_df(df, margen_neto):
    data = df.copy()
    col_map = {str(col).lower().strip(): col for col in data.columns}
    
    # 1. Costo Base
    col_costo = next((col_map[k] for k in col_map if "costo" in k or "price" in k or "precio" in k), None)
    if col_costo:
        data["Costo_Base_Limpio"] = pd.to_numeric(
            data[col_costo].astype(str).str.replace("$", "").str.replace(".", "").str.replace(",", "."),
            errors="coerce"
        ).fillna(0.0)
    else:
        data["Costo_Base_Limpio"] = 0.0

    # 2. Peso
    col_peso = next((col_map[k] for k in col_map if "peso" in k or "weight" in k or "kg" in k), None)
    data["Peso_Cat_Mapeado"] = data[col_peso].apply(mapear_peso_categoria) if col_peso else "De 1,5 a 2 kg"

    # 3. Modalidad
    col_flete = next((col_map[k] for k in col_map if "flete" in k or "modalidad" in k or "tipo" in k), None)
    data["Modalidad_Mapeada"] = data[col_flete].apply(mapear_modalidad) if col_flete else "Mercado Envíos Tradicional (ME2)"

    # Diccionario de Planes / Tasas
    tasas_variantes = {
        "PVP_Clasica_SinEnvio": (0.0, "ME1"),
        "PVP_Clasica_ConEnvio": (0.0, "AUTO"),
        "PVP_Premium_3Cuotas": (0.084, "AUTO"),
        "PVP_Premium_6Cuotas": (0.123, "AUTO"),
        "PVP_Premium_9Cuotas": (0.157, "AUTO"),
        "PVP_Premium_12Cuotas": (0.192, "AUTO")
    }
    
    resultados = {k: [] for k in tasas_variantes.keys()}

    for _, row in data.iterrows():
        c_base = row["Costo_Base_Limpio"]
        peso_cat = row["Peso_Cat_Mapeado"]
        mod_log = row["Modalidad_Mapeada"]
        
        if c_base <= 0:
            for var in tasas_variantes:
                resultados[var].append(0.0)
            continue

        for var, (tasa, modo) in tasas_variantes.items():
            log_final = mod_log if modo == "AUTO" else "ME1"
            pvp_calc = calcular_pvp_recomendado_func(
                costo_f=c_base,
                margen_deseado=margen_neto,
                t_finan=tasa,
                modalidad_log=log_final,
                peso_cat=peso_cat,
                t_comi_base=t_comi_base,
                t_iva_prod=t_iva_prod,
                t_iibb=t_iibb,
                t_ganancias_fijo=t_ganancias_fijo,
                tipo_iva=tipo_iva
            )
            resultados[var].append(pvp_calc)

    for var, list_values in resultados.items():
        data[var] = list_values

    data.drop(columns=["Costo_Base_Limpio", "Peso_Cat_Mapeado", "Modalidad_Mapeada"], inplace=True, errors="ignore")
    return data

if archivo_subido is not None:
    try:
        # Detección de separador de CSV
        if archivo_subido.name.endswith(".csv"):
            try:
                df_input = pd.read_csv(archivo_subido, sep=";")
                if df_input.shape[1] == 1:
                    archivo_subido.seek(0)
                    df_input = pd.read_csv(archivo_subido, sep=",")
            except Exception:
                archivo_subido.seek(0)
                df_input = pd.read_csv(archivo_subido, sep=None, engine="python")
        else:
            df_input = pd.read_excel(archivo_subido)

        df_resultado = procesar_matriz_df(df_input, margen_global_m)

        st.success("✅ ¡Catálogo procesado y mapeado exitosamente!")
        st.dataframe(df_resultado, use_container_width=True)

        data_csv = df_resultado.to_csv(index=False, sep=";").encode("utf-8-sig")

        st.download_button(
            label="📥 Descargar Matriz Completa (.csv)",
            data=data_csv,
            file_name=f"matriz_precios_NQ_v{V_NUMBER}.csv",
            mime="text/csv"
        )
    except Exception as e:
        st.error(f"Error al procesar el archivo masivo: {str(e)}")


=========================================================

SOLAPA 6: CÁLCULO DE BONIFICACIÓN OBJETIVO PARA GANAR CATÁLOGO

=========================================================

with tab6:
st.subheader("🏆 Simulador de Bonificación/Descuento para Ganar Catálogo")
st.markdown("Subí la lista de precios de tu proveedor (Centro Estant) con el PVP del competidor que hoy gana el catálogo. El sistema calculará el Descuento de Fábrica Requerido para ganarlo manteniendo tu margen deseado.")

col_cat1, col_cat2, col_cat3 = st.columns(3)
with col_cat1:
    margen_catalogo = st.number_input("% Margen Neto Pretendido", value=10.0, step=0.5, key="m_cat_input") / 100
with col_cat2:
    plan_catalogo = st.selectbox("Tipo de Publicación Objetivo", [
        "1 Pago / Clásica (0%)",
        "3 Cuotas Mismo Precio (8.40%)",
        "6 Cuotas Mismo Precio (12.30%)"
    ], index=0, key="plan_cat_select")
    tasa_plan_cat = 0.0 if "1 Pago" in plan_catalogo else (0.084 if "3 Cuotas" in plan_catalogo else 0.123)
with col_cat3:
    undercut_ganador = st.number_input("Descuento $ para superar al Ganador ($)", value=100.0, step=50.0, help="Monto a restar del PVP del competidor para ser el n.º 1 en la Buy Box")

uploaded_file_cat = st.file_uploader("Subí tu catálogo/lista (Excel o CSV)", type=["xlsx", "csv"], key="uploader_catalogo")

if uploaded_file_cat is not None:
    try:
        if uploaded_file_cat.name.endswith(".csv"):
            try:
                df_cat = pd.read_csv(uploaded_file_cat, sep=";")
                if df_cat.shape[1] == 1:
                    uploaded_file_cat.seek(0)
                    df_cat = pd.read_csv(uploaded_file_cat, sep=",")
            except Exception:
                uploaded_file_cat.seek(0)
                df_cat = pd.read_csv(uploaded_file_cat, sep=None, engine="python")
        else:
            df_cat = pd.read_excel(uploaded_file_cat)

        st.write("📋 **Vista previa de los datos:**", df_cat.head(3))

        col_map = {str(c).strip().lower(): c for c in df_cat.columns}
        
        c_ean = next((col_map[k] for k in col_map if "ean" in k or "sku" in k or "codigo" in k), None)
        c_plist = next((col_map[k] for k in col_map if "lista" in k or "costo" in k or "fabrica" in k), None)
        c_pvp_win = next((col_map[k] for k in col_map if "pvp" in k or "competidor" in k or "ganador" in k), None)
        c_peso = next((col_map[k] for k in col_map if "peso" in k or "kg" in k), None)

        if not c_plist or not c_pvp_win:
            st.error("❌ El archivo debe contener al menos dos columnas con nombres reconocibles: **Precio_Lista_Fabrica** y **PVP_Ganador_Actual**.")
        else:
            if st.button("🚀 CALCULAR BONIFICACIÓN NECESARIA PARA GANAR CATÁLOGO", use_container_width=True):
                res_cat = []
                
                for idx, row in df_cat.iterrows():
                    ean_val = str(row[c_ean]) if c_ean else f"Item-{idx+1}"
                    
                    plist_val = float(str(row[c_plist]).replace("$", "").replace(".", "").replace(",", ".").strip())
                    pvp_win_val = float(str(row[c_pvp_win]).replace("$", "").replace(".", "").replace(",", ".").strip())
                    peso_val = float(str(row[c_peso]).replace(",", ".").replace("kg", "").strip()) if (c_peso and pd.notnull(row[c_peso])) else 22.5
                    
                    # PVP Requerido para ganar (Buy Box)
                    pvp_target_win = pvp_win_val - undercut_ganador
                    peso_cat_str = mapear_peso_categoria(peso_val)
                    
                    # Costos de distribución asociados
                    flete_b = calcular_flete_segun_modalidad(pvp_target_win, peso_cat_str, "Mercado Envíos Tradicional (ME2)", 0, 0, 0, 0)
                    fijo_b = CARGO_FIJO_MELI if pvp_target_win < UMBRAL_ENVIO_GRATIS else 0.0
                    
                    # Deducciones
                    pvp_neto = pvp_target_win / (1 + t_iva_prod)
                    comi_b = pvp_target_win * (t_comi_base + tasa_plan_cat)
                    iibb_m = pvp_neto * t_iibb
                    gan_m = pvp_neto * t_ganancias_fijo
                    ganancia_target = pvp_target_win * margen_catalogo
                    
                    # Costo Neto de Compra Máximo Permitido
                    if tipo_iva == "Monotributista":
                        costo_max_inc = pvp_target_win - (ganancia_target + comi_b + flete_b + fijo_b + iibb_m + gan_m)
                        costo_max_neto = costo_max_inc / (1 + t_iva_prod)
                    else:
                        costo_max_neto = pvp_neto - (comi_b / 1.21) - (flete_b / 1.21) - (fijo_b / 1.21) - iibb_m - gan_m - ganancia_target

                    # % Descuento Requerido sobre lista de fábrica
                    desc_requerido_pct = ((1 - (costo_max_neto / plist_val)) * 100) if plist_val > 0 else 0.0

                    res_cat.append({
                        "EAN / SKU": ean_val,
                        "Precio Lista Fábrica ($)": plist_val,
                        "PVP Ganador Actual ($)": pvp_win_val,
                        "PVP Sugerido para Ganar ($)": pvp_target_win,
                        "Costo Máx Compra (Sin IVA)": max(0.0, round(costo_max_neto, 2)),
                        "% Descuento Requerido en Fábrica": round(desc_requerido_pct, 2),
                        "Estado Viabilidad": "🟢 Viable (< 25% desc)" if desc_requerido_pct <= 25 else "🔴 Difícil (> 25% desc)"
                    })

                df_res_cat = pd.DataFrame(res_cat)
                st.success("✅ Matriz de Estrategia de Catálogo Procesada!")
                st.dataframe(df_res_cat, use_container_width=True)

                csv_cat = df_res_cat.to_csv(index=False, sep=";").encode("utf-8-sig")
                st.download_button(
                    label="📥 Descargar Análisis de Descuentos para Catálogo (.csv)",
                    data=csv_cat,
                    file_name="Estrategia_Catalogo_CentroEstant.csv",
                    mime="text/csv",
                    use_container_width=True
                )

    except Exception as e:
        st.error(f"Error al analizar el catálogo: {str(e)}")

