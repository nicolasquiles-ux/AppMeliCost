# =========================================================
# FUNCIÓN AUXILIAR PARA OBTENER VENTAS REALES Y ANTIGÜEDAD
# =========================================================
def obtener_ventas_reales_item(item_id, access_token=None):
    """Consulta el ítem directo en la API para obtener sold_quantity real y calcular ventas diarias por fecha de creación."""
    if not item_id or item_id == "Sin ID":
        return 0, 0.0

    raw_id = item_id if item_id.startswith("MLA") else f"MLA{item_id}"
    url = f"https://api.mercadolibre.com/items/{raw_id}"

    try:
        res = requests.get(url, headers=get_headers(access_token), timeout=4)
        if res.status_code == 200:
            data = res.json()
            sold_quantity = int(data.get("sold_quantity", 0))
            date_created_str = data.get("date_created", "")

            if date_created_str:
                from datetime import datetime

                # Formato ISO de fecha de creación en MeLi
                fecha_inicio = datetime.strptime(
                    date_created_str.split("T")[0], "%Y-%m-%d"
                )
                dias_activo = (datetime.now() - fecha_inicio).days
                dias_activo = max(1, dias_activo)  # Evitar división por cero

                ventas_diarias = round(sold_quantity / dias_activo, 2)
                return sold_quantity, ventas_diarias
            return sold_quantity, round(sold_quantity / 30, 2)
    except Exception:
        pass

    return 0, 0.0


# --- SOLAPA 7: MONITOR BUY BOX & SUITE COMERCIAL COMPLETA (v37.1) ---
with tab7:
    st.subheader(
        "🎯 Monitor de Catálogo, Buy Box & Suite de Inteligencia Comercial"
    )
    st.markdown(
        "Auditoría en tiempo real con **Semáforo de Decisión, Ventas Diarias"
        " Reales de la API y Calculadora de Stock Crítico**."
    )

    col_s1, col_s2, col_s3 = st.columns([2.5, 1, 1])
    with col_s1:
        query_sku = st.text_input(
            "SKU / EAN / Descripción",
            value="7798274755797",
            key="input_sku_tab7",
        )
    with col_s2:
        costo_lista_f = st.number_input(
            "Costo Lista Proveedor ($)",
            value=70500.0,
            step=1000.0,
            key="costo_f_tab7",
        )
    with col_s3:
        margen_objetivo_tab7 = (
            st.number_input(
                "% Margen Objetivo", value=10.0, step=0.5, key="m_target_tab7"
            )
            / 100
        )

    if st.button(
        "🚀 AUDITAR CATÁLOGO Y COMPETENCIA",
        use_container_width=True,
        key="btn_audit_tab7",
    ):
        token = st.session_state.get("access_token")

        with st.spinner(
            "Consultando Mercado Libre API en vivo y calculando rotación"
            " real..."
        ):
            items_competencia, metodo_hallado = buscar_items_api_oficial(
                query_sku, limit=10, access_token=token
            )

            if items_competencia:
                first_item = items_competencia[0]
                item_id_first = str(
                    first_item.get("id", first_item.get("item_id", ""))
                ).replace("MLA", "").strip()

                pvp_ganador = float(
                    first_item.get("price")
                    or first_item.get("buy_box_winner", {}).get("price")
                    or 0.0
                )
                title_product = (
                    first_item.get("title")
                    or first_item.get("name")
                    or "Producto Mercado Libre"
                )

                # EXTRACCIÓN PRECISA DE VENTAS DESDE LA API DE MELI
                sold_total_real, ventas_dia_est = obtener_ventas_reales_item(
                    item_id_first, access_token=token
                )
                ventas_mes_est = int(ventas_dia_est * 30)

                # Flete con descuento oficial
                flete_std = obtener_flete_real_api(
                    item_id_first,
                    desc_factor=desc_rep_factor,
                    access_token=token,
                )
                fijo_std = (
                    CARGO_FIJO_MELI if pvp_ganador < UMBRAL_ENVIO_GRATIS else 0.0
                )

                pvp_objetivo = pvp_ganador - 100.0
                comi_std = pvp_objetivo * (comision_vender_input / 100)
                pvp_neto_std = pvp_objetivo / 1.21
                iibb_std = pvp_neto_std * (iibb_perc / 100)
                ganancia_target_std = pvp_objetivo * margen_objetivo_tab7

                costo_max_compra = (
                    pvp_neto_std
                    - (comi_std / 1.21)
                    - (flete_std / 1.21)
                    - (fijo_std / 1.21)
                    - iibb_std
                    - ganancia_target_std
                )
                bonif_requerida = (
                    ((1 - (costo_max_compra / costo_lista_f)) * 100)
                    if costo_lista_f > 0
                    else 0.0
                )

                st.caption(
                    f"🔎 **Origen:** {metodo_hallado} | 🟢 **Flete ME2 Neto"
                    f" Vendedor:** ${flete_std:,.2f}"
                )

                # =========================================================
                # RECUADROS COMERCIALES CON VENTAS REALES
                # =========================================================
                col_c1, col_c2 = st.columns(2)

                with col_c1:
                    if bonif_requerida <= 25.0:
                        st.markdown(
                            f"""
                        <div style="background-color: #D4EDDA; border: 2px solid #28A745; padding: 15px; border-radius: 10px; text-align: center;">
                            <h3 style="color: #155724; margin:0;">🟢 LUZ VERDE: PRODUCTO ALTAMENTE RENTABLE</h3>
                            <p style="color: #155724; margin:5px 0 0 0;">Bonificación requerida: <b>{bonif_requerida:.2f}%</b> (Fácil de negociar).</p>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )
                    elif bonif_requerida <= 40.0:
                        st.markdown(
                            f"""
                        <div style="background-color: #FFF3CD; border: 2px solid #FFC107; padding: 15px; border-radius: 10px; text-align: center;">
                            <h3 style="color: #856404; margin:0;">🟡 LUZ AMARILLA: REQUIERE NEGOCIACIÓN ESPECIAL</h3>
                            <p style="color: #856404; margin:5px 0 0 0;">Bonificación requerida: <b>{bonif_requerida:.2f}%</b> (Pedir descuento por volumen).</p>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f"""
                        <div style="background-color: #F8D7DA; border: 2px solid #DC3545; padding: 15px; border-radius: 10px; text-align: center;">
                            <h3 style="color: #721C24; margin:0;">🔴 LUZ ROJA: COSTO FUERA DE MERCADO</h3>
                            <p style="color: #721C24; margin:5px 0 0 0;">Bonificación requerida: <b>{bonif_requerida:.2f}%</b> (Muy alta para el PVP actual).</p>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                with col_c2:
                    # RECUADRO CON VENTAS HISTÓRICAS Y DIARIAS EXACTAS
                    st.markdown(
                        f"""
                    <div style="background-color: #D1ECF1; border: 2px solid #17A2B8; padding: 15px; border-radius: 10px; text-align: center;">
                        <h3 style="color: #0C5460; margin:0;">🔥 ROTACIÓN REAL DE PUBLICACIÓN GANADORA</h3>
                        <p style="font-size: 1.4rem; font-weight: 800; color: #0C5460; margin: 5px 0;">
                            {ventas_dia_est} un/día <span style="font-size: 1rem; font-weight: 400;">(Total vendidas: {sold_total_real:,} un)</span>
                        </p>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                st.markdown("<br>", unsafe_allow_html=True)

                # MÉTRICAS PRINCIPALES
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("🏆 PVP Ganador Actual", f"${pvp_ganador:,.2f}")
                m2.metric("🎯 PVP Objetivo (N.º 1)", f"${pvp_objetivo:,.2f}")
                m3.metric(
                    "📦 Costo Máx Compra Target",
                    f"${max(0.0, costo_max_compra):,.2f}",
                )
                m4.metric("📉 Bonificación Necesaria", f"{bonif_requerida:.2f}%")

                st.markdown("---")

                # CALCULADORA DE STOCK CRÍTICO BASADA EN VENTAS REALES
                st.markdown(
                    "### 📦 Calculadora de Inversión y Plan de Compra"
                )
                col_st1, col_st2, col_st3 = st.columns(3)
                with col_st1:
                    dias_cobertura = st.selectbox(
                        "Días de Stock Deseados",
                        [30, 45, 60],
                        index=0,
                        key="dias_stk",
                    )
                unidades_a_comprar = max(
                    1, int(round(ventas_dia_est * dias_cobertura))
                )
                inversion_necesaria = unidades_a_comprar * max(
                    0.0, costo_max_compra
                )

                with col_st2:
                    st.metric(
                        f"Unidades a Pedir ({dias_cobertura} días)",
                        f"{unidades_a_comprar} un",
                    )
                with col_st3:
                    st.metric(
                        "Capital Requerido de Compra",
                        f"${inversion_necesaria:,.2f}",
                    )
