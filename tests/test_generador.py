"""Contrato del reporte: importes, base vacía e incidencias visibles."""
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from src.generador import generar_reporte


class GeneradorTest(unittest.TestCase):
    def generar(self, resumen, errores):
        with TemporaryDirectory() as temporal:
            ruta = generar_reporte(resumen, errores, Path(temporal) / "reportes", "reporte.txt")
            return ruta.read_text(encoding="utf-8")

    def resumen(self):
        return dict(
            numero_ventas=3, unidades_vendidas=15,
            total_facturado=Decimal("313.20"), ticket_promedio=Decimal("104.40"),
            por_categoria=[("Tecnología", Decimal("245.70")), ("Oficina", Decimal("67.50"))],
            por_producto=[("Teclado", Decimal("171.00"))],
        )

    def test_resumen_decimal_e_incidencias(self):
        texto = self.generar(self.resumen(), ["Fila 5: cantidad cero"])
        for esperado in ["Registros de venta: 3", "Unidades vendidas: 15",
                         "Total facturado: $313.20", "Importe promedio por registro: $104.40",
                         "Tecnología: $245.70", "Oficina: $67.50", "Teclado: $171.00",
                         "Filas descartadas por errores: 1", "Fila 5: cantidad cero"]:
            self.assertIn(esperado, texto)

    def test_importe_grande_conserva_centavos_decimal(self):
        resumen = self.resumen()
        resumen["total_facturado"] = Decimal("9007199254740993.21")
        self.assertIn("$9,007,199,254,740,993.21", self.generar(resumen, []))

    def test_base_vacia(self):
        resumen = dict(numero_ventas=0, unidades_vendidas=0, total_facturado=Decimal("0"),
                       ticket_promedio=Decimal("0"), por_categoria=[], por_producto=[])
        texto = self.generar(resumen, [])
        self.assertIn("Total facturado: $0.00", texto)
        self.assertIn("Importe promedio por registro: $0.00", texto)
        self.assertIn("No hay ventas", texto)
        self.assertEqual(texto.count("Sin datos."), 2)
        self.assertIn("No se registraron filas inválidas", texto)

    def test_compatibilidad_con_resumen_actual_float(self):
        from src.procesador import calcular_resumen
        resumen = calcular_resumen([dict(total=12.5, cantidad=2, categoria="Oficina", producto="Lápiz")])
        self.assertIn("Total facturado: $12.50", self.generar(resumen, []))


if __name__ == "__main__":
    unittest.main()
