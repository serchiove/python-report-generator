"""Pruebas de cálculo para los datos del gráfico de categorías."""
from decimal import Decimal
import unittest

from src.grafico_categorias import preparar_datos_grafico


class PrepararDatosGraficoTest(unittest.TestCase):
    def test_ordena_calcula_total_y_participacion(self):
        datos = preparar_datos_grafico({
            "por_categoria": [
                ("Oficina", Decimal("67.50")),
                ("Tecnología", Decimal("245.70")),
                ("Hogar", 86.8),
            ]
        })
        self.assertEqual([item["nombre"] for item in datos["items"]], ["Tecnología", "Hogar", "Oficina"])
        self.assertEqual(datos["total"], Decimal("400.00"))
        self.assertEqual(datos["maximo"], Decimal("245.70"))
        self.assertEqual(datos["cantidad"], 3)
        self.assertEqual(datos["lider"], "Tecnología")
        self.assertAlmostEqual(float(datos["participacion_lider"]), 61.425)

    def test_empates_se_ordenan_por_nombre_sin_distinguir_mayusculas(self):
        datos = preparar_datos_grafico({
            "por_categoria": [("zeta", 10), ("Alfa", 10), ("beta", 10)]
        })
        self.assertEqual([item["nombre"] for item in datos["items"]], ["Alfa", "beta", "zeta"])
        self.assertEqual([item["porcentaje"] for item in datos["items"]], [Decimal("100") / 3] * 3)

    def test_sin_categorias_devuelve_estado_vacio(self):
        datos = preparar_datos_grafico({"por_categoria": []})
        self.assertEqual(datos["items"], [])
        self.assertEqual(datos["total"], Decimal("0"))
        self.assertEqual(datos["maximo"], Decimal("0"))
        self.assertEqual(datos["cantidad"], 0)
        self.assertEqual(datos["lider"], "Sin datos")
        self.assertEqual(datos["participacion_lider"], Decimal("0"))

    def test_categoria_con_importe_cero_no_divide_por_cero(self):
        datos = preparar_datos_grafico({"por_categoria": [("General", 0)]})
        self.assertEqual(datos["items"][0]["porcentaje"], Decimal("0"))
        self.assertEqual(datos["participacion_lider"], Decimal("0"))


if __name__ == "__main__":
    unittest.main()
