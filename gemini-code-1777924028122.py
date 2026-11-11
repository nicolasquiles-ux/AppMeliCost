# ------------------------------------------------------------------------------
# TAB 6: PUBLICADOR A CATÁLOGO DEFINITIVO (PAYLOAD COMPLETO OBLIGATORIO)
# ------------------------------------------------------------------------------
with tabs[5]:
    st.header("🚀 Publicador a Catálogo Definitivo (Con Campos Requeridos)")
    st.caption("Sumado al catálogo oficial incluyendo category_id y family_name exigidos por la API.")

    opciones_ean_gold_pub = extraer_opciones_ean_lista_gold()

    def actualizar_desde_selectbox_pub():
        sel = st.session_state.get("select_gold_dropdown_pub", "")
        if sel:
            for lbl, ean_v in opciones_ean_gold_pub:
                if lbl == sel:
                    st.session_state["q_builder"] = ean_v
                    break

    if "q_builder" not in st.session_state:
        st.session_state["q_builder"] = "7798009181204"

    if opciones_ean_gold_pub:
        labels_gold_pub = [op[0] for op in opciones_ean_gold_pub]
        st.selectbox("📋 Seleccionar Producto de la Lista Gold", labels_gold_pub, key="select_gold_dropdown_pub", on_change=actualizar_desde_selectbox_pub)
        st.markdown("---")

    c_b1, c_b2 = st.columns([3, 1])
    with c_b1:
        query_builder = st.text_input("Código EAN / SKU / MLA para Sumar a Catálogo", key="q_builder")
    with c_b2:
        st.write("")
        btn_armar_ficha = st.button("⚡ BUSCAR EN CATÁLOGO", type="primary", use_container_width=True)

    if query_builder:
        found_gold_b, costo_gold_b, desc_gold_b, art_gold_b = buscar_costo_y_titulo_en_lista_gold(query_builder)
        pvp_sugerido_b = round(costo_gold_b * 2.1, 2) if found_gold_b else 185000.0

        cat_product_id = "MLA27874272"
        cat_meli_id = "MLA4765"

        type_inp, clean_val = extraer_id_catalogo_o_ean_input(query_builder)
        if type_inp == "EAN":
            try:
                res_cat = requests.get(
                    f"https://api.mercadolibre.com/products/search?status=active&site_id=MLA&product_identifier={clean_val}",
                    headers={"Authorization": f"Bearer {st.session_state['access_token'].strip()}"} if st.session_state["access_token"] else {},
                    timeout=5
                )
                if res_cat.status_code == 200:
                    results = res_cat.json().get("results", [])
                    if results:
                        cat_product_id = results[0].get("id", "")
                        domain_raw = results[0].get("domain_id", "MLA4765")
                        cat_meli_id = domain_raw.replace("MLA-", "MLA") if domain_raw.startswith("MLA") else "MLA4765"
            except Exception:
                pass

        st.markdown("---")
        st.success(f"🎯 **Catálogo Detectado:** Vinculando a Producto MeLi ID **`{cat_product_id}`**")

        f_col1, f_col2 = st.columns(2)
        with f_col1:
            pub_ean = st.text_input("🏷️ Código EAN / GTIN", value=clean_val if clean_val else query_builder, key="input_pub_ean")
            pub_family_name = st.text_input("🏷️ Nombre de Familia (FAMILY_NAME)", value="Alacenas", key="input_pub_family_name")

        with f_col2:
            pub_cat_id = st.text_input("📂 ID Categoría MeLi", value=cat_meli_id, key="input_pub_cat_id")
            pub_catalog_id = st.text_input("🎯 Catalog Product ID", value=cat_product_id, key="input_pub_catalog_id")
            pub_pvp = st.number_input("💲 Precio de Venta ($ ARS)", value=pvp_sugerido_b, step=500.0, key="input_pub_pvp")
            pub_stock_qty = st.number_input("📊 Stock Disponible", value=10, step=1, key="input_pub_stock_qty")
            pub_type = st.selectbox("💳 Tipo de Publicación", ["gold_pro (Premium)", "gold_special (Clásica)"], index=0, key="input_pub_type")

        st.markdown("---")
        if st.button("🚀 ENVIAR SUMADO A CATÁLOGO OFICIAL", type="primary", use_container_width=True):
            if not st.session_state["access_token"]:
                st.error("❌ Se requiere un Access Token activo en la barra lateral para publicar.")
            elif not pub_catalog_id.strip():
                st.error("❌ Se requiere un Catalog Product ID válido.")
            else:
                tipo_list_clean = pub_type.split()[0]
                
                # Payload completo con los campos obligatorios exigidos por la API en el error
                payload_post = {
                    "catalog_product_id": pub_catalog_id.strip(),
                    "category_id": pub_cat_id.strip(),
                    "price": pub_pvp,
                    "currency_id": "ARS",
                    "available_quantity": int(pub_stock_qty),
                    "buying_mode": "buy_it_now",
                    "listing_type_id": tipo_list_clean,
                    "condition": "new",
                    "sale_terms": [
                        {"id": "WARRANTY_TIME", "value_name": "90 días"}
                    ],
                    "shipping": {
                        "mode": "me2",
                        "local_pick_up": False,
                        "free_shipping": False
                    },
                    "attributes": [
                        {"id": "FAMILY_NAME", "value_name": pub_family_name.strip()}
                    ]
                }

                headers_post = {
                    "Authorization": f"Bearer {st.session_state['access_token'].strip()}",
                    "Content-Type": "application/json"
                }

                try:
                    with st.spinner("Enviando sumado a catálogo a Mercado Libre..."):
                        res_api = requests.post("https://api.mercadolibre.com/items", json=payload_post, headers=headers_post, timeout=12)
                        if res_api.status_code in [200, 201]:
                            data_created = res_api.json()
                            item_id = data_created.get("id")
                            permalink = data_created.get("permalink")
                            st.success(f"🎉 ¡Sumado a catálogo exitoso! ID Item: **{item_id}**")
                            if permalink:
                                st.markdown(f"🔗 [Ver Publicación en Mercado Libre]({permalink})")
                        else:
                            err_resp = res_api.json() if res_api.content else {}
                            st.error(f"Error API MeLi ({res_api.status_code}): {err_resp.get('message', res_api.text)}")
                            if "cause" in err_resp:
                                st.write("📋 Detalle técnico retornado por la API:", err_resp.get("cause"))
                except Exception as e:
                    st.error(f"Error de conexión: {e}")
