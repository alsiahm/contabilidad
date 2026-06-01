from fpdf import FPDF
import os

# ──────────────────────────────────────────────
# CONFIGURACIÓN — edita estos valores
# ──────────────────────────────────────────────
EMPRESA = {
    "nombre":    "Martín García-Estrada Abogados",
    "forma":     "MARTÍN GARCÍA-ESTRADA ABOGADOS, S.C.",
    "cif":       "J38700829",
    "direccion": "Avda. Familia Betancourt y Molina, n.10, 1.03",
    "cp_ciudad": "38400 Puerto de la Cruz, Santa Cruz de Tenerife",
    "telefono":  "922 38 37 79",
    "email":     "luzmarinamge@gmail.com",
}

# Colores corporativos
AZUL_OSC  = (20,  60, 100)   # encabezado / títulos
AZUL_MED  = (41, 105, 176)   # barra de tabla
GRIS_LIN  = (210, 215, 220)  # líneas divisorias
GRIS_TEXT = (100, 100, 100)  # texto secundario
NEGRO     = (30,  30,  30)   # texto principal

# Ruta al logo (PNG o JPG).  Si no existe, se omite silenciosamente.
# Coloca el archivo en la misma carpeta que invoice_design.py y ajusta el nombre.
LOGO_PATH = os.path.join(os.path.dirname(__file__), "logo.png")

# ──────────────────────────────────────────────

PRIVACIDAD = (
    "Politica de privacidad - Responsable: MARTIN GARCIA-ESTRADA ABOGADOS, S.C. - NIF: J38700829 - "
    "Tel.: 922383779 - luzmarinamge@gmail.com - AVDA. FAMILIA BETANCOURT Y MOLINA, n.10, 103, "
    "PUERTO DE LA CRUZ, 38400, Santa Cruz de Tenerife. "
    "Los datos facilitados quedarán incorporados en nuestro registro interno de actividades de "
    "tratamiento con el fin de llevar a cabo una adecuada gestión fiscal y contable. Se conservarán "
    "mientras se mantenga la relación contractual y durante los años necesarios para cumplir "
    "con las obligaciones legales. No serán transferidos internacionalmente ni cedidos a terceros "
    "salvo obligación legal. Tiene derecho a acceder, rectificar, suprimir, limitar u oponerse al "
    "tratamiento de sus datos via e-mail, personalmente o por correo postal."
)


class FacturaPDF(FPDF):

    # ── CABECERA ──────────────────────────────
    def header(self):
        # Banda de color superior
        self.set_fill_color(*AZUL_OSC)
        self.rect(0, 0, 210, 28, style="F")

        # Logo (si existe)
        logo_w = 0
        if os.path.exists(LOGO_PATH):
            logo_w = 35
            self.image(LOGO_PATH, x=8, y=4, w=logo_w, h=20, keep_aspect_ratio=True)

        # Nombre empresa en la banda
        self.set_font("Helvetica", "B", 15)
        self.set_text_color(255, 255, 255)
        self.set_xy(logo_w + 10, 6)
        self.cell(0, 7, EMPRESA["nombre"], new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", size=8)
        self.set_text_color(200, 220, 240)
        self.set_x(logo_w + 10)
        self.cell(0, 5, f"CIF: {EMPRESA['cif']}   -   {EMPRESA['direccion']}   -   {EMPRESA['cp_ciudad']}")
        self.set_x(logo_w + 10)
        self.set_y(self.get_y() + 5)
        self.cell(0, 5, f"Tel.: {EMPRESA['telefono']}   -   {EMPRESA['email']}")


        self.ln(18)  # espacio tras la banda

    # ── PIE DE PÁGINA ─────────────────────────
    def footer(self):
        # Texto legal IGIC
        self.set_y(-42)
        self.set_draw_color(*GRIS_LIN)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)

        # Política de privacidad (texto muy pequeño, multilínea)
        self.ln(1)
        self.set_font("Helvetica", size=6)
        self.set_text_color(160, 160, 160)
        self.multi_cell(0, 3, PRIVACIDAD, align="J")

        # Número de página
        self.set_y(-8)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GRIS_TEXT)
        self.cell(0, 5, f"Página {self.page_no()}/{{nb}}", align="R")

    # ── UTILIDADES ────────────────────────────
    def seccion_titulo(self, texto, ancho=88):
        """Barra de seccion con fondo azul medio, respeta la X actual."""
        x_ini = self.get_x()
        y_ini = self.get_y()
        self.set_fill_color(*AZUL_MED)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 9)
        self.set_xy(x_ini, y_ini)
        self.cell(ancho, 6, f"  {texto}", fill=True)
        self.set_xy(x_ini, y_ini + 6 + 1)  # avanza Y, mantiene X
        self.set_text_color(*NEGRO)

    def fila_dato(self, etiqueta, valor, ancho_etiq=35, ancho_valor=53):
        """Par etiqueta / valor en una linea, respetando anchos fijos."""
        x_ini = self.get_x()
        y_ini = self.get_y()
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*GRIS_TEXT)
        self.set_xy(x_ini, y_ini)
        self.cell(ancho_etiq, 6, etiqueta)
        self.set_font("Helvetica", size=9)
        self.set_text_color(*NEGRO)
        self.cell(ancho_valor, 6, valor)
        self.set_xy(x_ini, y_ini + 6)  # siguiente fila, misma X


# ── GENERADOR PRINCIPAL ───────────────────────

def generar_pdf_bytes(datos: dict) -> bytes:
    """Genera el PDF en memoria y devuelve bytes."""
    pdf = FacturaPDF(orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.set_margins(left=12, top=12, right=12)
    pdf.set_auto_page_break(auto=True, margin=50)   # margen inferior amplio para el pie
    pdf.add_page()

    # ── BLOQUE: número de factura y fecha (destacado) ──
    pdf.set_fill_color(240, 245, 250)
    pdf.set_draw_color(*AZUL_MED)
    pdf.set_line_width(0.4)
    pdf.rect(12, pdf.get_y(), 186, 14, style="FD")
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*AZUL_OSC)
    pdf.set_x(14)
    pdf.cell(90, 7, f"Nº FACTURA:  {datos['num_factura']}")
    pdf.cell(90, 7, f"FECHA:  {datos['fecha']}", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(14)
    pdf.set_font("Helvetica", size=8)
    pdf.set_text_color(*GRIS_TEXT)
    pdf.cell(0, 7, "")   # fila vacía interior del rect
    pdf.ln(6)

    # ── BLOQUE: datos del cliente ──
    pdf.seccion_titulo("DATOS DEL CLIENTE", ancho=186)
    for etiq, val in [
        ("Nombre:",    datos["cliente_nombre"]),
        ("NIF/CIF:",   datos["cliente_cif"]),
        ("Dirección:", datos["cliente_dir"]),
    ]:
        pdf.fila_dato(etiq, val, ancho_etiq=35, ancho_valor=150)
    pdf.ln(6)

    # ── BLOQUE: tabla de conceptos ──
    pdf.seccion_titulo("DETALLE DE SERVICIOS")

    # Cabecera de tabla
    COL = [100, 28, 26, 34]
    pdf.set_fill_color(*AZUL_OSC)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(COL[0], 7, "  Concepto", fill=True)
    pdf.cell(COL[1], 7, "Base (EUR)", align="R", fill=True)
    pdf.cell(COL[2], 7, "IGIC", align="C", fill=True)
    pdf.cell(COL[3], 7, "Total (EUR)", align="R", fill=True, new_x="LMARGIN", new_y="NEXT")

    # Fila de datos (fondo alternado)
    pdf.set_fill_color(245, 248, 252)
    pdf.set_text_color(*NEGRO)
    pdf.set_font("Helvetica", size=9)
    pdf.set_line_width(0.2)
    pdf.set_draw_color(*GRIS_LIN)

    concepto_texto = datos.get("concepto") or "Servicios profesionales"
    pdf.cell(COL[0], 7, f"  {concepto_texto}", fill=True, border="B")
    pdf.cell(COL[1], 7, f"{datos['base']:,.2f}", align="R", fill=True, border="B")
    pdf.cell(COL[2], 7, f"{datos['igic_porcentaje']}%", align="C", fill=True, border="B")
    pdf.cell(COL[3], 7, f"{datos['base'] * (1 + datos['igic_porcentaje']/100):,.2f}", align="R", fill=True, border="B", new_x="LMARGIN", new_y="NEXT")

    # Filas de provisiones descontadas (si las hay)
    provisiones = datos.get("provisiones", [])
    if provisiones:
        for prov in provisiones:
            pdf.set_fill_color(255, 248, 235)  # fondo amarillo suave
            pdf.set_text_color(180, 100, 0)
            pdf.set_font("Helvetica", "I", 9)
            pdf.cell(COL[0], 7, f"  Provisión a cuenta: {prov['concepto']}", fill=True, border="B")
            pdf.cell(COL[1], 7, "", fill=True, border="B")
            pdf.cell(COL[2], 7, "", fill=True, border="B")
            pdf.cell(COL[3], 7, f"-{prov['importe']:,.2f}", align="R", fill=True, border="B", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*NEGRO)
    pdf.ln(4)

    # ── BLOQUE: totales (alineados a la derecha) ──
    igic_importe = datos["base"] * (datos["igic_porcentaje"] / 100)
    total = datos["base"] + igic_importe

    ancho_total = 90
    x_totales = 210 - 12 - ancho_total

    def fila_total(label, valor, negrita=False, fondo=None):
        pdf.set_x(x_totales)
        if fondo:
            pdf.set_fill_color(*fondo)
        pdf.set_font("Helvetica", "B" if negrita else "", 9)
        pdf.set_text_color(*NEGRO)
        pdf.cell(50, 7, label, fill=bool(fondo), border="B" if not negrita else 0)
        pdf.set_font("Helvetica", "B" if negrita else "", 9)
        pdf.cell(40, 7, f"{valor:,.2f} EUR", align="R", fill=bool(fondo), border="B" if not negrita else 0, new_x="LMARGIN", new_y="NEXT")

    fila_total("Base imponible:", datos["base"])
    fila_total(f"IGIC ({datos['igic_porcentaje']}%):", igic_importe)

    if datos.get("total_provisiones", 0) > 0:
      fila_total("Provisiones a cuenta:", -datos["total_provisiones"])

    # Línea separadora antes del total
    pdf.set_draw_color(*AZUL_MED)
    pdf.set_line_width(0.5)
    pdf.line(x_totales, pdf.get_y(), 198, pdf.get_y())
    pdf.ln(1)

    # Total en caja destacada
    pdf.set_x(x_totales)
    pdf.set_fill_color(*AZUL_OSC)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(50, 9, "  TOTAL A PAGAR:", fill=True)
    pdf.cell(40, 9, f"{datos.get('total_final', total):,.2f} EUR", align="R", fill=True, new_x="LMARGIN", new_y="NEXT")

    return pdf.output()