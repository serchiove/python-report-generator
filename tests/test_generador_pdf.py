"""Pruebas de exportación y validación del PDF de reportes."""
from pathlib import Path
from tempfile import TemporaryDirectory
import re
import unittest

from src.generador_pdf import exportar_pdf

REPORTE = """REPORTE AUTOMÁTICO DE VENTAS
================================================
RESUMEN GENERAL
Registros de venta: 3
Unidades vendidas: 15
Total facturado: $313.20
Importe promedio por registro: $104.40
Nota: cada registro corresponde a un producto vendido.

FACTURACIÓN POR CATEGORÍA
------------------------------------------------
- Tecnología: $245.70
- Oficina: $67.50

PRODUCTOS POR FACTURACIÓN
------------------------------------------------
- Teclado: $171.00
- Lápiz: $142.20

INCIDENCIAS DE LA IMPORTACIÓN ACTUAL
------------------------------------------------
Filas descartadas por errores: 1
- Fila 5: cantidad cero <valor>
"""

class GeneradorPdfTest(unittest.TestCase):
    def escribir_reporte(self, carpeta, contenido=REPORTE):
        ruta = Path(carpeta) / "reporte.txt"
        ruta.write_text(contenido, encoding="utf-8")
        return ruta

    def test_exporta_pdf_con_reporte_en_espanol(self):
        with TemporaryDirectory() as temporal:
            carpeta = Path(temporal)
            salida = exportar_pdf(self.escribir_reporte(carpeta), carpeta / "salida.pdf")
            contenido = salida.read_bytes()
            self.assertTrue(contenido.startswith(b"%PDF-"))
            self.assertIn(b"/Title (Reporte de ventas)", contenido)
            self.assertRegex(contenido, rb"/Count\s+1\b")

    def test_reporte_extenso_se_pagina(self):
        categorias = "\n".join("- Categoría %s: $%s.00" % (n, n + 100) for n in range(55))
        productos = "\n".join("- Producto %s: $%s.00" % (n, n + 200) for n in range(55))
        contenido = REPORTE.replace("- Tecnología: $245.70\n- Oficina: $67.50", categorias)
        contenido = contenido.replace("- Teclado: $171.00\n- Lápiz: $142.20", productos)
        with TemporaryDirectory() as temporal:
            salida = exportar_pdf(self.escribir_reporte(temporal, contenido), Path(temporal) / "largo.pdf")
            coincidencia = re.search(rb"/Count\s+(\d+)\b", salida.read_bytes())
            self.assertIsNotNone(coincidencia)
            self.assertGreater(int(coincidencia.group(1)), 1)

    def test_rechaza_destino_que_no_es_pdf(self):
        with TemporaryDirectory() as temporal:
            fuente = self.escribir_reporte(temporal)
            with self.assertRaisesRegex(ValueError, ".pdf"):
                exportar_pdf(fuente, Path(temporal) / "salida.txt")

    def test_rechaza_sobrescribir_el_txt_fuente(self):
        with TemporaryDirectory() as temporal:
            fuente = self.escribir_reporte(temporal)
            with self.assertRaisesRegex(ValueError, "diferente"):
                exportar_pdf(fuente, fuente)

    def test_rechaza_reporte_vacio(self):
        with TemporaryDirectory() as temporal:
            fuente = self.escribir_reporte(temporal, "  ")
            with self.assertRaisesRegex(ValueError, "vacío"):
                exportar_pdf(fuente, Path(temporal) / "salida.pdf")

if __name__ == "__main__":
    unittest.main()
