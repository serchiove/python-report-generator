"""Rutas y configuración central del proyecto."""

from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
ARCHIVO_VENTAS = RAIZ_PROYECTO / "data" / "examples" / "ventas_ejemplo.csv"
CARPETA_REPORTES = RAIZ_PROYECTO / "data" / "reports"
NOMBRE_REPORTE = "reporte_final.txt"
