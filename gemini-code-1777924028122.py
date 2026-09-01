import numpy as np
import pandas as pd


def obtener_costo_flete_me2(peso):
  """Tabla de tarifas según tramo de peso para ME2."""
  try:
    peso = float(peso)
  except (ValueError, TypeError):
    peso = 0.0

  if peso <= 0.5:
    return 3500.0
  elif peso <= 2.0:
    return 4800.0
  elif peso <= 5.0:
    return 6500.0
  elif peso <= 10.0:
    return 9200.0
  elif peso <= 20.0:
    return 14000.0
  elif peso <= 25.0:
    return 18500.0
  else:
    return 24000.0  # +25kg


def procesar_matriz_precios(
    filepath,
    margen_objetivo=0.10,
    comision_clasica=0.14,
    tasa_3_cuotas=0.084,
    tasa_6_cuotas=0.15,
    peso_defecto_dropdown=22.5,
):
  # 1. Carga del archivo
  if filepath.endswith('.csv'):
    df = pd.read_csv(filepath)
  else:
    df = pd.read_excel(filepath)

  # 2. Limpieza de datos y prevención del error 'ME1'
  df['Costo_Base'] = pd.to_numeric(df['Costo_Base'], errors='coerce').fillna(0)
  df['Peso_Kg'] = pd.to_numeric(df['Peso_Kg'], errors='coerce')

  # Rellena pesos faltantes con la opción seleccionada en el desplegable de la interfaz
  df['Peso_Kg'] = df['Peso_Kg'].fillna(peso_defecto_dropdown)

  # Sanitizar columna Tipo_Flete
  df['Tipo_Flete'] = df['Tipo_Flete'].astype(str).str.strip().str.upper()

  # 3. Cálculo de Flete Aplicable
  def calcular_flete_fila(row):
    # Si es ME1 o retiro, el costo de flete que absorbe el vendedor es 0
    if 'ME1' in row['Tipo_Flete']:
      return 0.0
    # Si es ME2, calcula según la tabla de pesos
    return obtener_costo_flete_me2(row['Peso_Kg'])

  df['Costo_Flete'] = df.apply(calcular_flete_fila, axis=1)

  # 4. Generación de Escenarios de PVP (Matriz de Publicaciones)
  # Fórmula general: PVP = (Costo Base + Flete) / (1 - %Comisión - %Margen)

  # Escenario 1: Clásica 1 Cuota (Sin Envío Gratis)
  df['PVP_Clasica_SinEnvio'] = df['Costo_Base'] / (
      1 - comision_clasica - margen_objetivo
  )

  # Escenario 2: Clásica 1 Cuota (Con Envío Gratis incluido)
  df['PVP_Clasica_ConEnvio'] = (df['Costo_Base'] + df['Costo_Flete']) / (
      1 - comision_clasica - margen_objetivo
  )

  # Escenario 3: Premium 3 Cuotas (Con Envío Gratis)
  comision_p3 = comision_clasica + tasa_3_cuotas
  df['PVP_Premium_3C_ConEnvio'] = (df['Costo_Base'] + df['Costo_Flete']) / (
      1 - comision_p3 - margen_objetivo
  )

  # Escenario 4: Premium 6 Cuotas (Con Envío Gratis)
  comision_p6 = comision_clasica + tasa_6_cuotas
  df['PVP_Premium_6C_ConEnvio'] = (df['Costo_Base'] + df['Costo_Flete']) / (
      1 - comision_p6 - margen_objetivo
  )

  # Redondear precios finales a 2 decimales
  columnas_pvp = [c for c in df.columns if c.startswith('PVP_')]
  df[columnas_pvp] = df[columnas_pvp].round(2)

  return df


# Ejemplo de uso:
# df_resultado = procesar_matriz_precios('catalogo.xlsx', margen_objetivo=0.10, tasa_3_cuotas=0.084)
# df_resultado.to_excel('matriz_precios_calculada.xlsx', index=False)
