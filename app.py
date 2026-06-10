import streamlit as st
import base64
from datetime import datetime
import database as db
from invoice_design import generar_pdf_bytes

# Aseguramos que las tablas existan al arrancar
db.crear_tablas()

st.set_page_config(layout="wide", page_title="Sistema Contable")

estilo_limpio = """
    <style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    </style>
"""
st.markdown(estilo_limpio, unsafe_allow_html=True)

st.set_page_config(layout="wide", page_title="Sistema Contable")
st.title("Sistema de Gestión y Facturación :)")

# Creamos las pestañas de navegación
tab_facturar, tab_clientes, tab_gastos, tab_provisiones, tab_resumen = st.tabs(
    ["Emitir Factura", "Gestión de Clientes", "Gastos Empresa", "Provisiones", "Resumen"]
)

# ==========================================
# PESTAÑA 2: GESTIÓN DE CLIENTES
# ==========================================
with tab_clientes:
    st.header("Registrar Nuevo Cliente")
    col1, col2 = st.columns(2)
    with col1:
        c_nombre = st.text_input("Nombre Fiscal / Razón Social")
        c_cif = st.text_input("CIF o NIF")
    with col2:
        c_dir = st.text_input("Dirección Fiscal")
        c_email = st.text_input("Email de contacto")

    if st.button("Guardar Cliente"):
        if c_nombre and c_cif:
            exito = db.agregar_cliente(c_nombre, c_cif, c_dir, c_email)
            if exito:
                st.success(f"Cliente '{c_nombre}' guardado correctamente.")
                st.rerun()
            else:
                st.error("Error: Ya existe un cliente registrado con ese CIF/NIF.")
        else:
            st.warning("Por favor, rellena al menos el Nombre y el CIF.")

    st.divider()
    st.subheader("Eliminar cliente")
    lista_clientes_del = db.obtener_clientes()
    if not lista_clientes_del:
        st.info("No hay clientes registrados aún.")
    else:
        opciones_del = {f"{c['nombre_fiscal']} ({c['cif_nif']})": c['id'] for c in lista_clientes_del}
        cliente_a_borrar = st.selectbox("Selecciona el cliente a eliminar", opciones_del.keys(), key="sel_borrar_cliente")
        st.warning("⚠️ Eliminar un cliente no borra sus facturas, pero quedarán sin nombre asociado.")
        if st.button("🗑️ Eliminar cliente seleccionado", key="btn_borrar_cliente"):
            db.borrar_cliente(opciones_del[cliente_a_borrar])
            st.success(f"Cliente '{cliente_a_borrar}' eliminado correctamente.")
            st.rerun()

# ==========================================
# PESTAÑA 1: EMITIR FACTURA (CON VISTA PREVIA)
# ==========================================
with tab_facturar:
    lista_clientes = db.obtener_clientes()

    if not lista_clientes:
        st.info("Primero debes registrar al menos un cliente en la pestaña 'Gestión de Clientes'.")
    else:
        num_factura_auto = db.calcular_siguiente_factura()

        col_controles, col_visor = st.columns([1, 1])

        with col_controles:
            st.subheader("Datos de Facturación")
            st.info(f"Número asignado automáticamente: **{num_factura_auto}**")
            fecha = st.date_input("Fecha de Emisión", datetime.now()).strftime("%d/%m/%Y")

            opciones_clientes = {f"{c['nombre_fiscal']} ({c['cif_nif']})": c for c in lista_clientes}
            cliente_seleccionado = st.selectbox("Selecciona el Cliente", opciones_clientes.keys())

            cliente_elegido = opciones_clientes[cliente_seleccionado]
            id_c = cliente_elegido['id']
            nombre_c = cliente_elegido['nombre_fiscal']
            cif_c = cliente_elegido['cif_nif']
            dir_c = cliente_elegido['direccion']

            st.subheader("Detalle del Servicio")
            concepto = st.text_area("Concepto", placeholder="Describa el servicio prestado...")
            base = st.number_input("Base Imponible (EUR)", min_value=0.0, value=0.0, step=50.0)
            igic_porcentaje = st.selectbox("Tipo de IGIC aplicable", [7.0, 0.0, 3.0, 15.0])

            importe_igic = base * (igic_porcentaje / 100)
            total = base + importe_igic

            st.metric(label="Total a Cobrar (IGIC Inc.)", value=f"{total:.2f} EUR")

            # --- Provisiones pendientes del cliente seleccionado ---
            provisiones_pendientes = db.obtener_provisiones_pendientes(id_c)
            provisiones_seleccionadas = []
            total_provisiones_desc = 0.0

            if provisiones_pendientes:
                st.subheader("Provisiones a descontar")
                st.caption("Selecciona las provisiones de fondo a aplicar en esta factura.")
                for prov in provisiones_pendientes:
                    pd_ = dict(prov)
                    check = st.checkbox(
                        f"{pd_['numero_provision']} — {pd_['concepto']} — {pd_['importe']:.2f} EUR",
                        key=f"prov_{pd_['id']}"
                    )
                    if check:
                        provisiones_seleccionadas.append(pd_['id'])
                        total_provisiones_desc += pd_['importe']

            total_a_pagar = max(total - total_provisiones_desc, 0.0)
            st.metric(label="Total tras provisiones", value=f"{total_a_pagar:.2f} EUR")

            datos_factura = {
                "num_factura": num_factura_auto, "fecha": fecha,
                "cliente_nombre": nombre_c, "cliente_cif": cif_c, "cliente_dir": dir_c if dir_c else "S/D",
                "concepto": concepto if concepto else "Servicios profesionales",
                "base": base, "igic_porcentaje": igic_porcentaje, "total": total,
                # Nuevos campos:
                "provisiones": [
                    {"concepto": dict(p)["concepto"], "importe": dict(p)["importe"]}
                    for p in provisiones_pendientes if dict(p)["id"] in provisiones_seleccionadas
                ],
                "total_provisiones": total_provisiones_desc,
                "total_final": total_a_pagar,
            }

            if st.button("ASENTAR Y GUARDAR FACTURA EN LA BASE DE DATOS"):
                if base <= 0:
                    st.error("La base imponible debe ser mayor que 0.")
                else:
                    db.agregar_factura(num_factura_auto, fecha, id_c, concepto, base, igic_porcentaje)
                    if provisiones_seleccionadas:
                        db.marcar_provisiones_aplicadas(provisiones_seleccionadas, num_factura_auto)
                    st.toast(f"Factura {num_factura_auto} guardada correctamente.", icon="✅")
                    st.success(f"¡Factura {num_factura_auto} registrada con éxito en el histórico!")
                    st.balloons()
                    st.rerun()

        with col_visor:
            st.subheader("Vista Previa del PDF")
            pdf_bytes = generar_pdf_bytes(datos_factura)
            pdf_bytes_puros = bytes(pdf_bytes)

            base64_pdf = base64.b64encode(pdf_bytes_puros).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)

            st.download_button(
                label="Descargar copia en PDF",
                data=pdf_bytes_puros,
                file_name=f"{num_factura_auto}.pdf",
                mime="application/pdf"
            )

    # Sección eliminar factura — fuera del if/else, siempre visible
    st.divider()
    st.subheader("Eliminar factura existente")
    todas_facturas = db.obtener_facturas_periodo()
    if todas_facturas:
        opciones_facturas = [dict(f)["numero_factura"] for f in todas_facturas]
        factura_a_borrar = st.selectbox("Selecciona la factura a eliminar", opciones_facturas, key="sel_borrar_factura_tab")
        if st.button("🗑️ Eliminar factura seleccionada", key="btn_borrar_factura_tab"):
            db.borrar_factura(factura_a_borrar)
            st.warning(f"Factura {factura_a_borrar} eliminada.")
            st.rerun()
    else:
        st.info("No hay facturas registradas aún.")

# ==========================================
# PESTAÑA 4: RESUMEN
# ==========================================
with tab_resumen:
    st.header("Resumen de Ingresos y Gastos")

    col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
    with col_f1:
        año_sel = st.selectbox("Año", list(range(datetime.now().year, 2024, -1)), index=0)
    with col_f2:
        trimestre_sel = st.selectbox("Trimestre", ["Año completo", "T1 (Ene-Mar)", "T2 (Abr-Jun)", "T3 (Jul-Sep)", "T4 (Oct-Dic)"])

    trimestre_num = {"Año completo": None, "T1 (Ene-Mar)": 1, "T2 (Abr-Jun)": 2, "T3 (Jul-Sep)": 3, "T4 (Oct-Dic)": 4}[trimestre_sel]

    facturas_periodo = db.obtener_facturas_periodo(año=año_sel, trimestre=trimestre_num)
    gastos_periodo   = db.obtener_gastos_periodo(año=año_sel, trimestre=trimestre_num)

    total_ingresos = sum(float(dict(f)["total"]) for f in facturas_periodo)
    total_gastos   = sum(float(dict(g)["importe"]) for g in gastos_periodo)
    beneficio      = total_ingresos - total_gastos

    st.subheader("Resumen del periodo")
    m1, m2, m3 = st.columns(3)
    m1.metric("Ingresos (total facturado)", f"{total_ingresos:,.2f} €")
    m2.metric("Gastos", f"{total_gastos:,.2f} €")
    m3.metric("Beneficio neto", f"{beneficio:,.2f} €", delta=f"{beneficio:,.2f} €")

    st.divider()

    col_t1, col_t2 = st.columns(2)

    with col_t1:
        st.subheader("Facturas emitidas")
        if not facturas_periodo:
            st.info("Sin facturas en este periodo.")
        else:
            datos_f = []
            for f in facturas_periodo:
                fd = dict(f)
                datos_f.append({
                    "Nº Factura": fd["numero_factura"],
                    "Fecha":      fd["fecha"],
                    "Cliente":    fd["cliente"] or "—",
                    "Base (€)":   f"{float(fd['base_imponible']):.2f}",
                    "IGIC":       f"{fd['porcentaje_igic']}%",
                    "Total (€)":  f"{float(fd['total']):.2f}",
                })
            st.dataframe(datos_f, use_container_width=True, hide_index=True)

    with col_t2:
        st.subheader("Gastos registrados")
        if not gastos_periodo:
            st.info("Sin gastos en este periodo.")
        else:
            datos_g = []
            for g in gastos_periodo:
                gd = dict(g)
                datos_g.append({
                    "Nº Gasto":    gd["numero_gasto"],
                    "Fecha":       gd["fecha"],
                    "Proveedor":   gd["proveedor"],
                    "Concepto":    gd["concepto"],
                    "Importe (€)": f"{float(gd['importe']):.2f}",
                })
            st.dataframe(datos_g, use_container_width=True, hide_index=True)

# ==========================================
# PESTAÑA 3: GASTOS EMPRESA
# ==========================================
with tab_gastos:
    st.header("Control de Gastos de la Empresa")

    col_form, col_tabla = st.columns([1, 1.5])

    with col_form:
        st.subheader("Registrar nuevo Gasto")

        g_fecha = st.date_input("Fecha del Gasto", datetime.now()).strftime("%d/%m/%Y")
        g_proveedor = st.text_input("Proveedor", placeholder="CIF del proveedor o nombre comercial")
        g_concepto = st.text_input("Concepto / Descripción", placeholder="Ej: Suscripción mensual software")
        g_base = st.number_input("Importe (€)", min_value=0.0, value=0.0, step=10.0, key="importe_gasto")

        if st.button("Registrar Gasto"):
            if not g_proveedor or not g_concepto:
                st.error("Por favor, rellena el Proveedor y el Concepto.")
            elif g_base <= 0:
                st.error("La base imponible del gasto debe ser mayor que 0.")
            else:
                db.registrar_gasto(g_fecha, g_proveedor, g_concepto, g_base)
                st.success("¡Gasto guardado correctamente en el histórico!")
                st.rerun()

    with col_tabla:
        st.subheader("Historial de Gastos Introducidos")
        lista_gastos = db.obtener_gastos()

        if not lista_gastos:
            st.info("Aún no has registrado ningún gasto empresarial.")
        else:
            datos_tabla = []
            for item in lista_gastos:
                item_dict = dict(item)
                datos_tabla.append({
                    "Nº Gasto":    item_dict.get("numero_gasto", ""),
                    "Fecha":       item_dict.get("fecha", "S/F"),
                    "Proveedor":   item_dict.get("proveedor", "Desconocido"),
                    "Concepto":    item_dict.get("concepto", "Sin concepto"),
                    "Importe (€)": f"{float(item_dict.get('importe', 0)):.2f}",
                })
            st.dataframe(datos_tabla, use_container_width=True, hide_index=True)

            st.divider()
            st.subheader("Eliminar gasto")
            opciones_gastos = [dict(g)["numero_gasto"] for g in lista_gastos]
            gasto_a_borrar = st.selectbox("Selecciona el gasto a eliminar", opciones_gastos, key="sel_borrar_gasto")
            if st.button("🗑️ Eliminar gasto seleccionado", key="btn_borrar_gasto"):
                db.borrar_gasto(gasto_a_borrar)
                st.warning(f"Gasto {gasto_a_borrar} eliminado.")
                st.rerun()

# ==========================================
# PESTAÑA: PROVISIONES DE FONDO
# ==========================================
with tab_provisiones:
    st.header("Provisiones de Fondo")
    col_form, col_tabla = st.columns([1, 1.5])

    with col_form:
        st.subheader("Registrar provision")
        lista_cli = db.obtener_clientes()
        if not lista_cli:
            st.info("Primero registra un cliente.")
        else:
            opciones_cli = {f"{c['nombre_fiscal']} ({c['cif_nif']})": c['id'] for c in lista_cli}
            cli_sel = st.selectbox("Cliente", opciones_cli.keys(), key="sel_cli_prov")
            p_fecha = st.date_input("Fecha", datetime.now(), key="fecha_prov").strftime("%d/%m/%Y")
            p_concepto = st.text_input("Concepto", placeholder="Ej: Provision fondos asunto laboral")
            p_importe = st.number_input("Importe (EUR)", min_value=0.0, value=0.0, step=50.0, key="imp_prov")

            # Opcional: vincular a una factura existente
            todas_fac = db.obtener_facturas_periodo()
            opciones_fac = ["Sin factura asociada"] + [dict(f)["numero_factura"] for f in todas_fac]
            fac_sel = st.selectbox("Vincular a factura (opcional)", opciones_fac, key="sel_fac_prov")
            fac_val = None if fac_sel == "Sin factura asociada" else fac_sel

            if st.button("Registrar Provision", key="btn_reg_prov"):
                if not p_concepto or p_importe <= 0:
                    st.error("Rellena el concepto y un importe mayor que 0.")
                else:
                    db.registrar_provision(p_fecha, opciones_cli[cli_sel], p_concepto, p_importe, fac_val)
                    st.success("Provision registrada correctamente.")
                    st.rerun()

        st.divider()
        st.subheader("Eliminar provision")
        lista_prov = db.obtener_provisiones()
        if lista_prov:
            opts = [dict(p)["numero_provision"] for p in lista_prov]
            prov_borrar = st.selectbox("Selecciona", opts, key="sel_borrar_prov")
            if st.button("Eliminar provision", key="btn_borrar_prov"):
                db.borrar_provision(prov_borrar)
                st.warning(f"Provision {prov_borrar} eliminada.")
                st.rerun()

    with col_tabla:
        st.subheader("Historial de Provisiones")
        lista_prov = db.obtener_provisiones()
        if not lista_prov:
            st.info("No hay provisiones registradas.")
        else:
            datos_tabla = []
            for p in lista_prov:
                pd_ = dict(p)
                datos_tabla.append({
                    "Num":      pd_["numero_provision"],
                    "Fecha":    pd_["fecha"],
                    "Cliente":  pd_["cliente"] or "—",
                    "Concepto": pd_["concepto"],
                    "Importe":  f"{float(pd_['importe']):.2f} EUR",
                    "Factura":  pd_["factura_asociada"] or "—",
                })
            st.dataframe(datos_tabla, use_container_width=True, hide_index=True)