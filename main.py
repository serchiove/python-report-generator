"""Punto de entrada: conecta extracción, procesamiento y reporte."""

from src.config import ARCHIVO_VENTAS, CARPETA_REPORTES, NOMBRE_REPORTE
from src.extractor import cargar_ventas
from src.generador import generar_reporte
from src.procesador import calcular_resumen


def main():
    ventas, filas_invalidas = cargar_ventas(ARCHIVO_VENTAS)
    resumen = calcular_resumen(ventas)
    ruta_reporte = generar_reporte(
        resumen, filas_invalidas, CARPETA_REPORTES, NOMBRE_REPORTE
    )

    print(f"Proceso completado: {len(ventas)} ventas válidas.")
    print(f"Reporte generado en: {ruta_reporte}")


if __name__ == "__main__":
    main()
