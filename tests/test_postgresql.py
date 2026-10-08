"""Pruebas contra PostgreSQL real en un esquema temporal aislado."""

from datetime import date
from decimal import Decimal
from hashlib import sha256
import os
import unittest
from uuid import uuid4

import psycopg
from psycopg import sql

from src.database import conectar, inicializar_esquema
from src.repositorio import consultar_ventas, guardar_ventas


@unittest.skipUnless(
    os.environ.get("POSTGRES_TEST_DATABASE")
    and os.environ.get("POSTGRES_TEST_DATABASE") == os.environ.get("PGDATABASE"),
    "Configura POSTGRES_TEST_DATABASE igual a PGDATABASE de la base de pruebas",
)
class PostgreSQLTest(unittest.TestCase):
    def setUp(self):
        self.conexion = conectar()
        self.addCleanup(self.conexion.close)
        self.esquema = "test_sergio_" + uuid4().hex
        self.conexion.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(self.esquema)))
        self.addCleanup(self.conexion.execute,
                        sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(self.esquema)))
        self.conexion.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(self.esquema)))
        inicializar_esquema(self.conexion)
        self.lote = sha256(b"ventas-ejemplo").hexdigest()
        self.ventas = [
            dict(fecha=date(2026, 8, 1), producto=nombre, categoria=categoria,
                 cantidad=cantidad, precio_unitario=Decimal(precio), fila_origen=fila)
            for fila, (nombre, categoria, cantidad, precio) in enumerate([
                ("Teclado", "Tecnología", 2, "85.50"),
                ("Mouse", "Tecnología", 3, "24.90"),
                ("Cuaderno", "Oficina", 10, "6.75"),
            ], start=2)
        ]

    def test_persistencia_reconexion_y_precision(self):
        self.assertEqual(guardar_ventas(self.conexion, self.ventas, self.lote), 3)
        with conectar() as otra:
            otra.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(self.esquema)))
            ventas = consultar_ventas(otra)
        self.assertEqual(len(ventas), 3)
        self.assertEqual(sum(v["cantidad"] for v in ventas), 15)
        self.assertEqual(sum(v["total"] for v in ventas), Decimal("313.20"))
        self.assertIsInstance(ventas[0]["precio_unitario"], Decimal)

    def test_reimportacion_sin_duplicados(self):
        guardar_ventas(self.conexion, self.ventas, self.lote)
        self.assertEqual(guardar_ventas(self.conexion, self.ventas, self.lote), 0)
        self.assertEqual(len(consultar_ventas(self.conexion)), 3)
        self.assertEqual(self.conexion.execute("SELECT count(*) AS n FROM categorias").fetchone()["n"], 2)

    def test_rollback_del_lote_y_catalogos(self):
        mala = dict(self.ventas[1], cantidad=0)
        with self.assertRaises(ValueError):
            guardar_ventas(self.conexion, [self.ventas[0], mala], self.lote)
        for tabla in ["ventas", "productos", "categorias"]:
            n = self.conexion.execute(sql.SQL("SELECT count(*) AS n FROM {}").format(sql.Identifier(tabla))).fetchone()["n"]
            self.assertEqual(n, 0)

    def test_clave_foranea_y_borrado_restringido(self):
        with self.assertRaises(psycopg.errors.ForeignKeyViolation):
            self.conexion.execute("INSERT INTO productos (nombre,id_categoria) VALUES (%s,%s)", ("Huérfano", 999))
        guardar_ventas(self.conexion, self.ventas, self.lote)
        with self.assertRaises((psycopg.errors.ForeignKeyViolation, psycopg.errors.RestrictViolation)):
            self.conexion.execute("DELETE FROM productos")

    def test_precios_invalidos_y_constraint_sql(self):
        for precio in ["NaN", "Infinity", "-1", "1.001", "10000000000"]:
            with self.subTest(precio=precio), self.assertRaises(ValueError):
                guardar_ventas(self.conexion, [dict(self.ventas[0], precio_unitario=Decimal(precio))], self.lote)
        guardar_ventas(self.conexion, self.ventas, self.lote)
        with self.assertRaises(psycopg.errors.CheckViolation):
            self.conexion.execute("UPDATE ventas SET precio_unitario = 'NaN'::numeric")

    def test_esquema_repetible_y_base_vacia(self):
        inicializar_esquema(self.conexion)
        self.assertEqual(consultar_ventas(self.conexion), [])

    def test_parametros_y_producto_por_categoria(self):
        ventas = [dict(self.ventas[0], producto="O'Reilly; DROP TABLE ventas; --"),
                  dict(self.ventas[1], producto="O'Reilly; DROP TABLE ventas; --", categoria="Oficina")]
        guardar_ventas(self.conexion, ventas, self.lote)
        self.assertEqual(len(consultar_ventas(self.conexion)), 2)
        self.assertEqual(self.conexion.execute("SELECT count(*) AS n FROM productos").fetchone()["n"], 2)


if __name__ == "__main__":
    unittest.main()
