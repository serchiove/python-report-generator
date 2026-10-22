"""Comandos de la parte de Sergio, independientes del flujo CSV existente."""

import argparse
from datetime import date
from decimal import Decimal
from hashlib import sha256
import sys

import psycopg

from src.database import conectar, inicializar_esquema
from src.importador import importar_ventas
from src.repositorio import consultar_ventas, guardar_ventas


def main():
    parser = argparse.ArgumentParser(description="Preparación y prueba de PostgreSQL")
    parser.add_argument("accion", choices=["conexion", "inicializar", "demo", "listar", "importar"])
    parser.add_argument("archivo", nargs="?", help="CSV UTF-8 para la acción importar")
    args = parser.parse_args()
    if args.accion == "importar" and not args.archivo:
        parser.error("importar requiere la ruta de un CSV")
    if args.accion != "importar" and args.archivo:
        parser.error("la ruta CSV solo se admite con importar")
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
            elif args.accion == "importar":
                resultado = importar_ventas(conexion, args.archivo)
                print(f"Ventas válidas: {resultado['ventas_validas']}")
                print(f"Ventas nuevas: {resultado['ventas_insertadas']}")
                print(f"Ventas ya existentes: {resultado['ventas_ya_existentes']}")
                print(f"Filas descartadas: {len(resultado['filas_invalidas'])}")
                for error in resultado["filas_invalidas"]:
                    print(error)
            else:
                ventas = consultar_ventas(conexion)
                for venta in ventas:
                    print(f"{venta['fecha']} | {venta['producto']} | {venta['cantidad']} | {venta['total']:.2f}")
                print(f"Registros: {len(ventas)}")
        return 0
    except (psycopg.Error, ValueError, OSError) as error:
        if isinstance(error, psycopg.OperationalError):
            print("No se pudo conectar. Revisa el servidor y las variables PG*.", file=sys.stderr)
        else:
            print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
