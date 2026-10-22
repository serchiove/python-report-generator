"""Validación del CSV y contrato para importar sin perder la fila original."""

import csv
from datetime import date
from decimal import Decimal
from hashlib import sha256
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from src.extractor import cargar_lote, cargar_ventas
from src.procesador import calcular_resumen

ENCABEZADO = "fecha,producto,categoria,cantidad,precio_unitario\n"
FILA = ["2026-08-01", "Teclado", "Tecnología", "2", "85.50"]


class ExtractorTest(unittest.TestCase):
    def leer(self, contenido):
        with TemporaryDirectory() as directorio:
            ruta = Path(directorio) / "ventas.csv"
            ruta.write_bytes(contenido if isinstance(contenido, bytes) else contenido.encode("utf-8"))
            return cargar_lote(ruta)

    def csv_fila(self, fila):
        salida = StringIO(newline="")
        csv.writer(salida).writerow(fila)
        return salida.getvalue()

    def test_decimal_fecha_hash_y_contrato_main(self):
        contenido = ENCABEZADO + self.csv_fila(FILA)
        ventas, errores, lote = self.leer(contenido)
        self.assertEqual(errores, [])
        self.assertEqual(lote, sha256(contenido.encode("utf-8")).hexdigest())
        self.assertEqual(ventas[0]["precio_unitario"], Decimal("85.50"))
        self.assertEqual(ventas[0]["fecha"], date(2026, 8, 1))
        self.assertEqual(ventas[0]["fila_origen"], 2)
        resumen = calcular_resumen(ventas)
        self.assertEqual(resumen["total_facturado"], Decimal("171.00"))
        self.assertIsInstance(resumen["total_facturado"], Decimal)
        with TemporaryDirectory() as d:
            ruta = Path(d) / "ventas.csv"
            ruta.write_text(contenido, encoding="utf-8")
            self.assertEqual(cargar_ventas(ruta), (ventas, errores))

    def test_filas_invalidas_no_renumeran_las_validas(self):
        contenido = ENCABEZADO + self.csv_fila(FILA) + self.csv_fila(FILA[:3] + ["0", "85.50"]) + "\n" + self.csv_fila(FILA)
        ventas, errores, _ = self.leer(contenido)
        self.assertEqual([v["fila_origen"] for v in ventas], [2, 5])
        self.assertTrue(errores[0].startswith("Fila 3:"))

    def test_filas_cortas_y_largas_se_descartan(self):
        ventas, errores, _ = self.leer(ENCABEZADO + "2026-08-01,Teclado\n" + self.csv_fila(FILA + ["extra"]) + self.csv_fila(FILA))
        self.assertEqual(len(errores), 2)
        self.assertEqual(ventas[0]["fila_origen"], 4)

    def test_valores_invalidos_se_registran_por_fila(self):
        casos = [(0, "2026-02-30"), (0, "20260801"), (1, " "), (2, ""),
                 (3, "0"), (3, "-1"), (3, "2.5"), (3, "2147483648"),
                 (4, "NaN"), (4, "Infinity"), (4, "-1"), (4, "0.001"),
                 (4, "10000000000"), (4, "1,50"), (4, "abc"),
                 (1, "x" * 151), (2, "x" * 101), (1, "a\x00b")]
        for columna, valor in casos:
            with self.subTest(columna=columna, valor=valor):
                fila = FILA.copy()
                fila[columna] = valor
                ventas, errores, _ = self.leer(ENCABEZADO + self.csv_fila(fila))
                self.assertEqual(ventas, [])
                self.assertEqual(len(errores), 1)
                self.assertTrue(errores[0].startswith("Fila 2:"))

    def test_encabezados_duplicados_faltantes_y_archivo_vacio(self):
        for contenido in ["", "fecha,producto,categoria,cantidad\n", ENCABEZADO.replace("categoria", "producto"), "fecha;producto;categoria;cantidad;precio_unitario\n"]:
            with self.subTest(contenido=contenido), self.assertRaises(ValueError):
                self.leer(contenido)

    def test_bom_espacios_y_columnas_reordenadas(self):
        contenido = "\ufeffproducto,fecha,cantidad,precio_unitario,categoria\r\n Teclado ,2026-08-01,2,85.50, Tecnología \r\n"
        ventas, errores, _ = self.leer(contenido)
        self.assertEqual(errores, [])
        self.assertEqual(ventas[0]["producto"], "Teclado")
        self.assertEqual(ventas[0]["categoria"], "Tecnología")

    def test_lineas_multilinea_conservan_fila_de_inicio(self):
        fila = FILA.copy()
        fila[1] = "Teclado\nmecánico"
        ventas, errores, _ = self.leer(ENCABEZADO + self.csv_fila(fila) + self.csv_fila(FILA))
        self.assertEqual(errores, [])
        self.assertEqual([v["fila_origen"] for v in ventas], [2, 4])

    def test_csv_mal_formado_y_codificacion_invalida(self):
        for contenido in [ENCABEZADO + '2026-08-01,"sin cierre', b"\xff\xfe"]:
            with self.subTest(contenido=contenido), self.assertRaises(ValueError):
                self.leer(contenido)

    def test_solo_encabezados_y_precio_cero(self):
        self.assertEqual(self.leer(ENCABEZADO)[:2], ([], []))
        ventas, errores, _ = self.leer(ENCABEZADO + self.csv_fila(FILA[:4] + ["0"]))
        self.assertEqual(errores, [])
        self.assertEqual(ventas[0]["precio_unitario"], Decimal("0.00"))


if __name__ == "__main__":
    unittest.main()
