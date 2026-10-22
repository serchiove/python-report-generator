"""Flujo completo: CSV validado, PostgreSQL, resumen SQL y reporte."""

import argparse
from pathlib import Path
import sys

import psycopg

from src.config import ARCHIVO_VENTAS, CARPETA_REPORTES, NOMBRE_REPORTE
from src.database import conectar
from src.generador import generar_reporte
from src.importador import importar_ventas
from src.procesador import consultar_resumen


def ejecutar_flujo(conexion, archivo, carpeta_reportes, nombre_reporte):
    """Importa un CSV o, con archivo=None, reporta solo lo ya persistido.

    La importación se confirma antes de consultar el resumen de toda la base.
    Sus incidencias corresponden al archivo actual, no al historial de ventas.
    """
    importacion = importar_ventas(conexion, archivo) if archivo is not None else None
    resumen = consultar_resumen(conexion)
    errores = importacion["filas_invalidas"] if importacion is not None else None
    ruta = generar_reporte(resumen, errores, carpeta_reportes, nombre_reporte)
    return {"importacion": importacion, "resumen": resumen, "ruta_reporte": ruta}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Importar ventas a PostgreSQL y generar su reporte")
    parser.add_argument("archivo", nargs="?", type=Path, help="CSV UTF-8; por defecto usa el ejemplo versionado")
    parser.add_argument("--solo-reporte", action="store_true", help="Consultar PostgreSQL sin importar un CSV")
    parser.add_argument("--salida", type=Path, default=CARPETA_REPORTES / NOMBRE_REPORTE,
                        help="Ruta del reporte de texto; reemplaza su contenido si existe")
    args = parser.parse_args(argv)
    if args.solo_reporte and args.archivo is not None:
        parser.error("--solo-reporte no admite un archivo CSV")
    archivo = None if args.solo_reporte else (args.archivo or ARCHIVO_VENTAS)
    try:
        with conectar() as conexion:
            resultado = ejecutar_flujo(conexion, archivo, args.salida.parent, args.salida.name)
    except psycopg.OperationalError:
        print("No se pudo conectar a PostgreSQL. Revisa el servidor y las variables PG*.", file=sys.stderr)
        return 1
    except psycopg.errors.UndefinedTable:
        print("Faltan las tablas. Ejecuta primero: python postgres.py inicializar", file=sys.stderr)
        return 1
    except (psycopg.Error, OSError, ValueError) as error:
        print(f"No se completó el proceso: {error}", file=sys.stderr)
        print("Si la importación ya se confirmó, las ventas siguen guardadas. "
              "Puedes repetir el mismo CSV o ejecutar --solo-reporte.", file=sys.stderr)
        return 1
    importacion = resultado["importacion"]
    if importacion is not None:
        print(f"Ventas válidas: {importacion['ventas_validas']}")
        print(f"Ventas nuevas: {importacion['ventas_insertadas']}")
        print(f"Ventas ya existentes: {importacion['ventas_ya_existentes']}")
        for error in importacion["filas_invalidas"]:
            print(error)
    else:
        print("Reporte sin importación; incidencias históricas no disponibles.")
    resumen = resultado["resumen"]
    print(f"Registros en la base: {resumen['numero_ventas']}")
    print(f"Total facturado: {resumen['total_facturado']:.2f}")
    print(f"Reporte generado en: {resultado['ruta_reporte']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
