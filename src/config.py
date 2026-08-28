"""Rutas y configuración central del proyecto."""

from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
ARCHIVO_VENTAS = RAIZ_PROYECTO / "data" / "raw" / "ventas.csv"
CARPETA_REPORTES = RAIZ_PROYECTO / "data" / "reports"
NOMBRE_REPORTE = "reporte_final.txt"
