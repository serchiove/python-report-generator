"""Prepara una base local aislada y ejecuta la suite con PostgreSQL real."""

import os
from pathlib import Path
import sys
import unittest

import psycopg
from psycopg import sql


ROOT = Path(__file__).resolve().parent.parent
NOMBRE_BASE_PRUEBAS = "reportes_pruebas"
sys.path.insert(0, str(ROOT))


class ResultadoVisible(unittest.TextTestResult):
    """Imprime el resultado de cada prueba al terminar, no al final de la suite."""

    def addSuccess(self, test):
        super().addSuccess(test)
        self.stream.writeln(f"[APROBADA] {test.id()}")
        self.stream.flush()

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.stream.writeln(f"[FALLÓ] {test.id()}")
        self.stream.flush()

    def addError(self, test, err):
        super().addError(test, err)
        self.stream.writeln(f"[ERROR] {test.id()}")
        self.stream.flush()

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.stream.writeln(f"[OMITIDA] {test.id()} — {reason}")
        self.stream.flush()


def cargar_env_local():
    """Carga .env sin imprimir credenciales ni reemplazar el entorno actual."""
    archivo = ROOT / ".env"
    if not archivo.is_file():
        return
    for linea in archivo.read_text(encoding="utf-8-sig").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        clave, valor = clave.strip(), valor.strip()
        if valor[:1] in ('"', "'") and valor[-1:] == valor[:1]:
            valor = valor[1:-1]
        if clave:
            os.environ.setdefault(clave, valor)


def preparar_base_pruebas():
    usuario = os.environ.get("PGUSER")
    if not usuario:
        raise RuntimeError("Configura PGUSER en .env antes de ejecutar las pruebas.")
    parametros = {
        "host": os.environ.get("PGHOST", "localhost"),
        "port": os.environ.get("PGPORT", "5432"),
        "user": usuario,
        "password": os.environ.get("PGPASSWORD"),
        "dbname": os.environ.get("PGDATABASE", "postgres"),
        "connect_timeout": 5,
        "autocommit": True,
        "application_name": "python-report-generator-test-setup",
    }
    try:
        with psycopg.connect(**parametros) as conexion:
            existe = conexion.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (NOMBRE_BASE_PRUEBAS,),
            ).fetchone()
            if not existe:
                conexion.execute(
                    sql.SQL("CREATE DATABASE {} OWNER {}").format(
                        sql.Identifier(NOMBRE_BASE_PRUEBAS), sql.Identifier(usuario)
                    )
                )
    except psycopg.Error as error:
        raise RuntimeError(
            "No se pudo preparar la base de pruebas. Revisa que PostgreSQL esté "
            "activo, que los datos PG* de .env sean correctos y que PGUSER "
            "pueda crear bases de datos."
        ) from error


def main():
    cargar_env_local()
    preparar_base_pruebas()
    entorno_pruebas = os.environ.copy()
    entorno_pruebas["PGDATABASE"] = NOMBRE_BASE_PRUEBAS
    entorno_pruebas["POSTGRES_TEST_DATABASE"] = NOMBRE_BASE_PRUEBAS
    print(f"Ejecutando la suite en la base aislada {NOMBRE_BASE_PRUEBAS}...", flush=True)
    os.environ.update(entorno_pruebas)
    suite = unittest.defaultTestLoader.discover(
        start_dir=str(ROOT / "tests"),
        top_level_dir=str(ROOT / "tests"),
    )
    resultado = unittest.TextTestRunner(
        stream=sys.stdout,
        verbosity=0,
        resultclass=ResultadoVisible,
        buffer=False,
    ).run(suite)
    aprobadas = resultado.testsRun - len(resultado.failures) - len(resultado.errors) - len(resultado.skipped)
    fallidas = len(resultado.failures) + len(resultado.errors)
    print(
        f"RESULTADO FINAL: {resultado.testsRun} pruebas, {aprobadas} aprobadas, "
        f"{fallidas} fallidas, {len(resultado.skipped)} omitidas."
    )
    return 0 if resultado.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
