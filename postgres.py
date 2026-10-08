"""Comandos de la parte de Sergio, independientes del flujo CSV existente."""

import argparse
from datetime import date
from decimal import Decimal
from hashlib import sha256
import sys

import psycopg

from src.database import conectar, inicializar_esquema
from src.repositorio import consultar_ventas, guardar_ventas


def main():
    parser = argparse.ArgumentParser(description="Preparación y prueba de PostgreSQL")
    parser.add_argument("accion", choices=["conexion", "inicializar", "demo", "listar"])
    args = parser.parse_args()
    try:
        with conectar() as conexion:
            if args.accion == "conexion":
                info = conexion.execute("SELECT current_database() AS base, current_user AS usuario").fetchone()
                print(f"Conexión correcta: {info['base']} / {info['usuario']}")
            elif args.accion == "inicializar":
                inicializar_esquema(conexion)
                print("Esquema PostgreSQL creado: categorias, productos y ventas.")
            elif args.accion == "demo":
                ventas = [
                    dict(fecha=date(2026, 8, 1), producto=nombre, categoria=categoria,
                         cantidad=cantidad, precio_unitario=Decimal(precio), fila_origen=fila)
                    for fila, (nombre, categoria, cantidad, precio) in enumerate([
                        ("Teclado", "Tecnología", 2, "85.50"),
                        ("Mouse", "Tecnología", 3, "24.90"),
                        ("Cuaderno", "Oficina", 10, "6.75"),
                    ], start=2)
                ]
                lote = sha256(b"demo-sergio-postgresql-v1").hexdigest()
                nuevas = guardar_ventas(conexion, ventas, lote)
                print(f"Ventas nuevas: {nuevas}. Repetir la demo no duplica registros.")
            else:
                ventas = consultar_ventas(conexion)
                for venta in ventas:
                    print(f"{venta['fecha']} | {venta['producto']} | {venta['cantidad']} | {venta['total']:.2f}")
                print(f"Registros: {len(ventas)}")
        return 0
    except (psycopg.Error, ValueError) as error:
        if isinstance(error, psycopg.OperationalError):
            print("No se pudo conectar. Revisa el servidor y las variables PG*.", file=sys.stderr)
        else:
            print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
