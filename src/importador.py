"""Coordinación de la validación del archivo y su importación a PostgreSQL."""

from src.extractor import cargar_lote
from src.repositorio import guardar_ventas


def importar_ventas(conexion, ruta_archivo):
    """Guarda filas válidas; un fallo al guardar revierte el lote completo.

    Hash y datos provienen de la misma lectura. Las incidencias corresponden
    a esta importación y pueden pasarse al generador del reporte.
    """
    ventas, errores, lote_hash = cargar_lote(ruta_archivo)
    nuevas = guardar_ventas(conexion, ventas, lote_hash)
    return {"lote_hash": lote_hash, "ventas_validas": len(ventas),
            "ventas_insertadas": nuevas, "ventas_ya_existentes": len(ventas) - nuevas,
            "filas_invalidas": errores}
