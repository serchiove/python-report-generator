"""Conexión e inicialización de PostgreSQL sin credenciales en el código."""

import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

ESQUEMA_SQL = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"


def cargar_entorno_local(archivo=None):
    """Carga .env local sin imprimir credenciales ni reemplazar el entorno."""
    archivo = Path(archivo) if archivo is not None else Path(__file__).resolve().parent.parent / ".env"
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


def conectar():
    """Usa PGHOST, PGPORT, PGDATABASE, PGUSER y PGPASSWORD del entorno.

    La conexión se utiliza con ``with conectar() as conexion`` para cerrarla.
    Autocommit evita transacciones abiertas por lecturas; cada escritura
    compuesta debe usar ``conexion.transaction()``.
    """
    cargar_entorno_local()
    if not os.environ.get("PGDATABASE") or not os.environ.get("PGUSER"):
        raise ValueError("Configura PGDATABASE y PGUSER antes de conectar.")
    return psycopg.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=os.environ.get("PGPORT", "5432"),
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        connect_timeout=5,
        application_name="python-report-generator",
        autocommit=True,
        row_factory=dict_row,
    )


def inicializar_esquema(conexion):
    """Crea tablas e índices de forma atómica y admite repetir la operación."""
    with conexion.transaction():
        conexion.execute(ESQUEMA_SQL.read_text(encoding="utf-8"))
