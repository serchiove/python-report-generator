"""Exporta el reporte de texto a un PDF diseñado y paginado."""

from pathlib import Path
import re
from decimal import Decimal, InvalidOperation
from xml.sax.saxutils import escape


SECCIONES = {
    "RESUMEN GENERAL": "resumen",
    "FACTURACIÓN POR CATEGORÍA": "categorias",
    "PRODUCTOS POR FACTURACIÓN": "productos",
    "INCIDENCIAS DE LA IMPORTACIÓN ACTUAL": "incidencias",
}
METRICAS = (
    "Registros de venta",
    "Unidades vendidas",
    "Total facturado",
    "Importe promedio por registro",
)
IMPORTE_RE = re.compile(r"\$?\s*(-?\d[\d,]*(?:\.\d{1,2})?)")


def _leer_campo(linea):
    texto = linea.strip().lstrip("- ").strip()
    if ":" not in texto:
        return texto, ""
    return tuple(parte.strip() for parte in texto.split(":", 1))


def _leer_importe(texto):
    coincidencia = IMPORTE_RE.search(texto)
    if not coincidencia:
        return None
    try:
        return Decimal(coincidencia.group(1).replace(",", ""))
    except InvalidOperation:
        return None


def _analizar_reporte(contenido):
    lineas = contenido.splitlines()
    titulo = next((linea.strip() for linea in lineas if linea.strip()), "Reporte de ventas")
    secciones = {clave: [] for clave in SECCIONES.values()}
    actual = None
    for linea in lineas:
        texto = linea.strip()
        if not texto or set(texto) <= {"=", "-"} or texto == titulo:
            continue
        clave = SECCIONES.get(texto.upper())
        if clave:
            actual = clave
            continue
        if actual:
            secciones[actual].append(texto)
    return titulo, secciones


def _tabla_detalle(filas, ancho, mostrar_porcentaje=False):
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import LongTable, Paragraph, TableStyle

    estilo_celda = ParagraphStyle(
        "CeldaReporte", fontName="Helvetica", fontSize=9, leading=13,
        textColor=colors.HexColor("#26364f"),
    )
    estilo_cabecera = ParagraphStyle(
        "CabeceraReporte", parent=estilo_celda, fontName="Helvetica-Bold",
        textColor=colors.white,
    )
    cabeceras = ["Concepto", "Importe"] + (["% del total"] if mostrar_porcentaje else [])
    filas_tabla = [[Paragraph(escape(texto), estilo_cabecera) for texto in cabeceras]]
    total = sum((importe or Decimal("0") for _, importe, _ in filas), Decimal("0"))
    for nombre, importe, original in filas:
        monto = original or "Sin importe"
        valores = [Paragraph(escape(nombre), estilo_celda), Paragraph(escape(monto), estilo_celda)]
        if mostrar_porcentaje:
            porcentaje = (importe / total * Decimal("100")) if total else Decimal("0")
            valores.append(Paragraph(f"{porcentaje:.2f}%", estilo_celda))
        filas_tabla.append(valores)

    anchos = [ancho * 0.56, ancho * (0.25 if mostrar_porcentaje else 0.44)]
    if mostrar_porcentaje:
        anchos.append(ancho * 0.19)
    tabla = LongTable(filas_tabla, colWidths=anchos, repeatRows=1, hAlign="LEFT")
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17345c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f8fc")]),
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, colors.HexColor("#17345c")),
        ("LINEBELOW", (0, 1), (-1, -1), 0.35, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return tabla


def _filas_importe(lineas):
    filas = []
    for linea in lineas:
        nombre, valor = _leer_campo(linea)
        if nombre.casefold() == "sin datos":
            continue
        importe = _leer_importe(valor)
        filas.append((nombre, importe, valor))
    return filas


def exportar_pdf(ruta_txt, ruta_pdf):
    """Genera un PDF A4 con indicadores, tablas, incidencias y paginación."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    ruta_txt, ruta_pdf = Path(ruta_txt), Path(ruta_pdf)
    if ruta_txt.resolve() == ruta_pdf.resolve():
        raise ValueError("El PDF debe tener una ruta diferente al TXT.")
    if ruta_pdf.suffix.lower() != ".pdf":
        raise ValueError("El destino debe tener extensión .pdf.")
    contenido = ruta_txt.read_text(encoding="utf-8-sig")
    if not contenido.strip():
        raise ValueError("El reporte está vacío. Genera un reporte antes de exportar.")

    ruta_pdf.parent.mkdir(parents=True, exist_ok=True)
    titulo_original, secciones = _analizar_reporte(contenido)
    estilos_base = getSampleStyleSheet()
    estilos = {
        "titulo": ParagraphStyle(
            "TituloReporte", parent=estilos_base["Title"], fontName="Helvetica-Bold",
            fontSize=22, leading=27, alignment=0, textColor=colors.HexColor("#17345c"),
            spaceAfter=5,
        ),
        "subtitulo": ParagraphStyle(
            "SubtituloReporte", parent=estilos_base["Normal"], fontName="Helvetica",
            fontSize=9, leading=13, textColor=colors.HexColor("#64748b"), spaceAfter=16,
        ),
        "seccion": ParagraphStyle(
            "SeccionReporte", parent=estilos_base["Heading2"], fontName="Helvetica-Bold",
            fontSize=12, leading=16, textColor=colors.HexColor("#17345c"),
            spaceBefore=14, spaceAfter=8, keepWithNext=True,
        ),
        "texto": ParagraphStyle(
            "TextoReporte", parent=estilos_base["BodyText"], fontName="Helvetica",
            fontSize=9, leading=13, textColor=colors.HexColor("#26364f"), spaceAfter=5,
        ),
        "aviso": ParagraphStyle(
            "AvisoReporte", parent=estilos_base["BodyText"], fontName="Helvetica",
            fontSize=9, leading=13, textColor=colors.HexColor("#7c3f12"), spaceAfter=4,
        ),
    }

    documento = SimpleDocTemplate(
        str(ruta_pdf), pagesize=A4, rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=2.25 * cm, bottomMargin=1.9 * cm,
        title="Reporte de ventas", author="Generador de reportes",
        subject="Resumen de ventas por categoría y producto",
    )
    elementos = [
        Paragraph(escape(titulo_original), estilos["titulo"]),
        Paragraph("Indicadores generales y detalle de facturación", estilos["subtitulo"]),
    ]

    resumen = secciones["resumen"]
    metricas = []
    lineas_resumen = []
    for linea in resumen:
        nombre, valor = _leer_campo(linea)
        if nombre in METRICAS:
            metricas.append((nombre, valor))
        else:
            lineas_resumen.append(linea)

    if metricas:
        elementos.append(Paragraph("Resumen general", estilos["seccion"]))
        celdas = []
        for nombre, valor in metricas:
            celdas.append(Paragraph(
                f'<font size="8" color="#64748b">{escape(nombre.upper())}</font><br/>'
                f'<font size="15" color="#17345c"><b>{escape(valor)}</b></font>',
                estilos["texto"],
            ))
        while len(celdas) % 2:
            celdas.append(Paragraph("", estilos["texto"]))
        datos_tarjetas = [celdas[indice:indice + 2] for indice in range(0, len(celdas), 2)]
        tarjetas = Table(datos_tarjetas, colWidths=[documento.width / 2] * 2, hAlign="LEFT")
        tarjetas.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f2f6fc")),
            ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#dbe5f2")),
            ("INNERGRID", (0, 0), (-1, -1), 0.7, colors.HexColor("#dbe5f2")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        elementos.extend([tarjetas, Spacer(1, 5)])
    for linea in lineas_resumen:
        elementos.append(Paragraph(escape(linea), estilos["texto"]))

    categorias = _filas_importe(secciones["categorias"])
    elementos.append(Paragraph("Facturación por categoría", estilos["seccion"]))
    if categorias:
        elementos.append(_tabla_detalle(categorias, documento.width, mostrar_porcentaje=True))
    else:
        elementos.append(Paragraph("Sin datos de categoría para mostrar.", estilos["texto"]))

    productos = _filas_importe(secciones["productos"])
    elementos.append(Paragraph("Productos por facturación", estilos["seccion"]))
    if productos:
        elementos.append(_tabla_detalle(productos, documento.width))
    else:
        elementos.append(Paragraph("Sin datos de producto para mostrar.", estilos["texto"]))

    incidencias = secciones["incidencias"]
    elementos.append(Paragraph("Incidencias de la importación", estilos["seccion"]))
    texto_incidencias = incidencias or ["No se registraron incidencias."]
    aviso = Table(
        [[Paragraph(escape(linea), estilos["aviso"])] for linea in texto_incidencias],
        colWidths=[documento.width], hAlign="LEFT",
    )
    aviso.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff7ed")),
        ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#fed7aa")),
        ("LINEBEFORE", (0, 0), (0, -1), 3, colors.HexColor("#f59e0b")),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elementos.append(aviso)

    def decorar_pagina(canvas, doc):
        canvas.saveState()
        ancho, alto = A4
        canvas.setFillColor(colors.HexColor("#17345c"))
        canvas.rect(0, alto - 0.55 * cm, ancho, 0.55 * cm, stroke=0, fill=1)
        canvas.setStrokeColor(colors.HexColor("#dbe5f2"))
        canvas.setLineWidth(0.6)
        canvas.line(2 * cm, 1.45 * cm, ancho - 2 * cm, 1.45 * cm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(2 * cm, 1.05 * cm, "Generador de reportes de ventas")
        canvas.drawRightString(ancho - 2 * cm, 1.05 * cm, f"Página {doc.page}")
        canvas.restoreState()

    documento.build(elementos, onFirstPage=decorar_pagina, onLaterPages=decorar_pagina)
    return ruta_pdf
