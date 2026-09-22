# =========================================================
# SOLAPA 6: CÁLCULO DE BONIFICACIÓN CON BÚSQUEDA AUTOMÁTICA POR EAN
# =========================================================
def buscar_pvp_meli_por_ean(ean_code):
  """Consulta la API de Mercado Libre para obtener el PVP actual de referencia buscando por EAN."""
  ean_clean = str(ean_code).strip().split('.')[0]
  if not ean_clean or len(ean_clean) < 8 or ean_clean == '-':
    return None

  url = f'https://api.mercadolibre.com/sites/MLA/search?q={ean_clean}'
  try:
    res = requests.get(url, timeout=5)
    if res.status_code == 200:
      results = res.json().get('results', [])
      if results:
        # Devuelve el precio del primer resultado (el mejor posicionado/ganador)
        return float(results[0].get('price', 0.0))
  except Exception:
    pass
  return None


with tab6:
  st.subheader(
      '🏆 Analizador Automatizado de Proveedores (Centro Estant / Buy Box)'
  )
  st.markdown(
      'Subí la lista oficial de Centro Estant. El sistema buscará'
      ' automáticamente en Mercado Libre el **PVP de referencia usando el'
      ' EAN** de cada producto y te indicará la bonificación necesaria.'
  )

  col_cat1, col_cat2, col_cat3 = st.columns(3)
  with col_cat1:
    margen_catalogo = (
        st.number_input(
            '% Margen Neto Pretendido',
            value=10.0,
            step=0.5,
            key='m_cat_input_ean',
        )
        / 100
    )
  with col_cat2:
    plan_catalogo = st.selectbox(
        'Modalidad Publicación Objetivo',
        [
            '1 Pago / Clásica (0%)',
            '3 Cuotas Mismo Precio (8.40%)',
            '6 Cuotas Mismo Precio (12.30%)',
        ],
        index=0,
        key='plan_cat_select_ean',
    )
    tasa_plan_cat = (
        0.0
        if '1 Pago' in plan_catalogo
        else (0.084 if '3 Cuotas' in plan_catalogo else 0.123)
    )
  with col_cat3:
    undercut_ganador = st.number_input(
        'Ajuste para ganar la Buy Box ($)',
        value=100.0,
        step=50.0,
        help='Monto a restar del PVP del competidor para quedar n.º 1',
    )

  uploaded_file_cat = st.file_uploader(
      'Subí la lista de Centro Estant / Proveedor (.xlsx o .csv)',
      type=['xlsx', 'csv'],
      key='uploader_catalogo_centroestant_ean',
  )

  if uploaded_file_cat is not None:
    try:
      if uploaded_file_cat.name.endswith('.csv'):
        try:
          df_cat = pd.read_csv(uploaded_file_cat, sep=';')
          if df_cat.shape[1] == 1:
            uploaded_file_cat.seek(0)
            df_cat = pd.read_csv(uploaded_file_cat, sep=',')
        except Exception:
          uploaded_file_cat.seek(0)
          df_cat = pd.read_csv(uploaded_file_cat, sep=None, engine='python')
      else:
        df_cat = pd.read_excel(uploaded_file_cat)

      st.write('📋 **Vista previa de los datos cargados:**', df_cat.head(4))

      # Mapeo de columnas
      col_map = {str(c).strip().lower(): c for c in df_cat.columns}
      c_ean = next(
          (col_map[k] for k in col_map if 'ean' in k or 'codigo' in k), None
      )
      c_art = next(
          (
              col_map[k]
              for k in col_map
              if 'articulo' in k or 'art' in k or 'sku' in k
          ),
          None,
      )
      c_desc = next(
          (
              col_map[k]
              for k in col_map
              if 'descripcion' in k or 'detalle' in k or 'nombre' in k
          ),
          None,
      )
      c_plist = next(
          (
              col_map[k]
              for k in col_map
              if 'list' in k or 'costo' in k or 'precio' in k or 'estant' in k
          ),
          None,
      )
      c_pvp_win = next(
          (
              col_map[k]
              for k in col_map
              if 'pvp' in k or 'competidor' in k or 'ganador' in k
          ),
          None,
      )

      if not c_plist or not c_ean:
        st.error(
            '❌ El archivo debe incluir obligatoriamente las columnas **EAN** y'
            ' **Precio de Lista**.'
        )
      else:
        if st.button(
            '🔍 ESCANEAR EANs EN MERCADO LIBRE Y CALCULAR BONIFICACIONES',
            use_container_width=True,
        ):
          res_cat = []
          progress_bar = st.progress(0)
          total_rows = len(df_cat)

          for idx, row in df_cat.iterrows():
            progress_bar.progress((idx + 1) / total_rows)

            ean_val = str(row[c_ean]).strip() if pd.notnull(row[c_ean]) else '-'
            art_val = (
                str(row[c_art]).strip()
                if c_art and pd.notnull(row[c_art])
                else f'SKU-{idx+1}'
            )
            desc_val = (
                str(row[c_desc]).strip()
                if c_desc and pd.notnull(row[c_desc])
                else 'Mueble Centro Estant'
            )

            # Limpieza del Precio de Lista de Fábrica
            raw_plist = (
                str(row[c_plist])
                .replace('$', '')
                .replace('.', '')
                .replace(',', '.')
                .strip()
            )
            plist_val = (
                float(raw_plist)
                if raw_plist and raw_plist.lower() != 'nan'
                else 0.0
            )

            # Búsqueda automática de PVP en MeLi por EAN
            pvp_meli_encontrado = None
            if c_pvp_win and pd.notnull(row[c_pvp_win]):
              raw_pvp = (
                  str(row[c_pvp_win])
                  .replace('$', '')
                  .replace('.', '')
                  .replace(',', '.')
                  .strip()
              )
              if raw_pvp and raw_pvp.lower() != 'nan':
                pvp_meli_encontrado = float(raw_pvp)

            # Si no venía en la planilla, se consulta en tiempo real a la API de MeLi
            if not pvp_meli_encontrado:
              pvp_meli_encontrado = buscar_pvp_meli_por_ean(ean_val)

            # Cálculo de viabilidad financiera si se encontró un PVP de competencia
            if pvp_meli_encontrado and pvp_meli_encontrado > 0:
              pvp_target_win = pvp_meli_encontrado - undercut_ganador
              peso_cat_str = (
                  'De 20 a 25 kg'  # Tramo promedio de muebles de melamina
              )

              flete_b = calcular_flete_segun_modalidad(
                  pvp_target_win,
                  peso_cat_str,
                  'Mercado Envíos Tradicional (ME2)',
                  0,
                  0,
                  0,
                  0,
              )
              fijo_b = (
                  CARGO_FIJO_MELI if pvp_target_win < UMBRAL_ENVIO_GRATIS else 0.0
              )

              pvp_neto = pvp_target_win / (1 + t_iva_prod)
              comi_b = pvp_target_win * (t_comi_base + tasa_plan_cat)
              iibb_m = pvp_neto * t_iibb
              gan_m = pvp_neto * t_ganancias_fijo
              ganancia_target = pvp_target_win * margen_catalogo

              if tipo_iva == 'Monotributista':
                costo_max_inc = pvp_target_win - (
                    ganancia_target
                    + comi_b
                    + flete_b
                    + fijo_b
                    + iibb_m
                    + gan_m
                )
                costo_max_neto = costo_max_inc / (1 + t_iva_prod)
              else:
                costo_max_neto = (
                    pvp_neto
                    - (comi_b / 1.21)
                    - (flete_b / 1.21)
                    - (fijo_b / 1.21)
                    - iibb_m
                    - gan_m
                    - ganancia_target
                )

              desc_requerido_pct = (
                  (1 - (costo_max_neto / plist_val)) * 100
                  if plist_val > 0
                  else 0.0
              )
              costo_max_out = max(0.0, round(costo_max_neto, 2))
              desc_out = round(desc_requerido_pct, 2)
              estado_out = (
                  '🟢 Viable (< 20% desc)'
                  if desc_requerido_pct <= 20
                  else '🔴 Exige Negociación (> 20% desc)'
              )
            else:
              pvp_target_win = 'No encontrado en MeLi'
              costo_max_out = '-'
              desc_out = '-'
              estado_out = '⚪ Sin PVP Competidor'

            res_cat.append({
                'EAN': ean_val,
                'Artículo': art_val,
                'Descripción': desc_val,
                'Precio Lista Proveedor ($)': plist_val,
                'PVP MeLi Detectado ($)': (
                    f'${pvp_meli_encontrado:,.2f}'
                    if pvp_meli_encontrado
                    else 'No publicado'
                ),
                'Costo Máx Compra (Sin IVA)': costo_max_out,
                '% Bonificación Requerida': desc_out,
                'Estado Viabilidad': estado_out,
            })

          df_res_cat = pd.DataFrame(res_cat)
          st.success(
              '✅ ¡Escaneo de EANs y Matriz de Negociación completada!'
          )
          st.dataframe(df_res_cat, use_container_width=True)

          csv_cat = df_res_cat.to_csv(index=False, sep=';').encode('utf-8-sig')
          st.download_button(
              label='📥 Descargar Matriz de Negociación con Centro Estant (.csv)',
              data=csv_cat,
              file_name='Estrategia_CentroEstant_EAN_MeLi.csv',
              mime='text/csv',
              use_container_width=True,
          )

    except Exception as e:
      st.error(f'Error al procesar el archivo: {str(e)}')
