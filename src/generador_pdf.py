"""Exporta el contenido del reporte TXT a un PDF paginado."""
from pathlib import Path
from xml.sax.saxutils import escape


def exportar_pdf(ruta_txt, ruta_pdf):
    """Conserva el texto y sus tildes, con ajuste de líneas y páginas A4."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

    ruta_txt, ruta_pdf = Path(ruta_txt), Path(ruta_pdf)
    if ruta_txt.resolve() == ruta_pdf.resolve():
        raise ValueError("El PDF debe tener una ruta diferente al TXT.")
    if ruta_pdf.suffix.lower() != ".pdf":
        raise ValueError("El destino debe tener extensión .pdf.")
    contenido = ruta_txt.read_text(encoding="utf-8-sig")
    if not contenido.strip():
        raise ValueError("El reporte está vacío. Genera un reporte antes de exportar.")
    normal = ParagraphStyle("Texto", fontName="Helvetica", fontSize=10, leading=15, spaceAfter=5)
    titulo = ParagraphStyle("Titulo", parent=normal, fontName="Helvetica-Bold", fontSize=18, leading=23, textColor=colors.HexColor("#172b4d"), spaceAfter=16)
    seccion = ParagraphStyle("Seccion", parent=normal, fontName="Helvetica-Bold", fontSize=11, leading=16, spaceBefore=12, spaceAfter=8, keepWithNext=True)
    elementos = []
    primero = True
    for linea in contenido.splitlines():
        if not linea.strip():
            elementos.append(Spacer(1, 5))
            continue
        if set(linea.strip()) <= {"=", "-"}:
            continue
        estilo = titulo if primero else (seccion if linea.isupper() and not linea.startswith("-") else normal)
        elementos.append(Paragraph(escape(linea), estilo))
        primero = False
    def pie(canvas, documento):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(2 * cm, 1.2 * cm, "Reporte de ventas")
        canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Página {documento.page}")
        canvas.restoreState()
    documento = SimpleDocTemplate(str(ruta_pdf), pagesize=A4, rightMargin=2*cm, leftMargin=2*cm,
                                  topMargin=1.8*cm, bottomMargin=2*cm, title="Reporte de ventas")
    documento.build(elementos, onFirstPage=pie, onLaterPages=pie)
    return ruta_pdf
