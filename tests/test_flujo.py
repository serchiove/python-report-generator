"""Pruebas del recorrido completo y de la recuperación sin reimportación."""

from decimal import Decimal
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from main import ejecutar_flujo, main
import test_postgresql as pruebas_bd


@unittest.skipUnless(
    os.environ.get("POSTGRES_TEST_DATABASE")
    and os.environ.get("POSTGRES_TEST_DATABASE") == os.environ.get("PGDATABASE"),
    "Configura una base PostgreSQL de pruebas explícita",
)
class FlujoPostgreSQLTest(unittest.TestCase):
    # Reutiliza exclusivamente la preparación aislada de la suite PostgreSQL.
    setUp = pruebas_bd.PostgreSQLTest.setUp
    def test_flujo_importa_consulta_y_reporta(self):
        archivo = Path(__file__).resolve().parent.parent / "data/examples/ventas_ejemplo.csv"
        with TemporaryDirectory() as d:
            resultado = ejecutar_flujo(self.conexion, archivo, Path(d), "final.txt")
            self.assertEqual(resultado["importacion"]["ventas_insertadas"], 3)
            texto = resultado["ruta_reporte"].read_text(encoding="utf-8")
            for valor in ["$313.20", "$104.40", "Tecnología: $245.70", "Fila 5:"]:
                self.assertIn(valor, texto)
            repetido = ejecutar_flujo(self.conexion, archivo, Path(d), "final.txt")
            self.assertEqual(repetido["importacion"]["ventas_insertadas"], 0)
            self.assertEqual(repetido["resumen"]["numero_ventas"], 3)

    def test_solo_reporte_usa_toda_la_base_y_no_abre_csv(self):
        from src.repositorio import guardar_ventas
        guardar_ventas(self.conexion, self.ventas, self.lote)
        with TemporaryDirectory() as d, patch("main.importar_ventas") as importar:
            resultado = ejecutar_flujo(self.conexion, None, Path(d), "solo.txt")
            importar.assert_not_called()
            self.assertEqual(resultado["resumen"]["total_facturado"], Decimal("313.20"))
            self.assertIn("Sin importación", resultado["ruta_reporte"].read_text(encoding="utf-8"))

    def test_csv_invalido_no_crea_reporte_ni_guarda_ventas(self):
        from src.repositorio import consultar_ventas
        with TemporaryDirectory() as d:
            archivo = Path(d) / "roto.csv"
            archivo.write_text("encabezado_incorrecto\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                ejecutar_flujo(self.conexion, archivo, Path(d), "final.txt")
            self.assertFalse((Path(d) / "final.txt").exists())
            self.assertEqual(consultar_ventas(self.conexion), [])


class ComandoTest(unittest.TestCase):
    def test_error_conexion_retorna_codigo_uno(self):
        import psycopg
        with patch("main.conectar", side_effect=psycopg.OperationalError("no disponible")), patch("sys.stderr"):
            self.assertEqual(main(["--solo-reporte"]), 1)

    def test_no_acepta_archivo_con_solo_reporte(self):
        with patch("sys.stderr"), self.assertRaises(SystemExit) as error:
            main(["ventas.csv", "--solo-reporte"])
        self.assertEqual(error.exception.code, 2)
