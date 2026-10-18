"""Demostración del formato de Melissa con datos ficticios, sin PostgreSQL."""
from decimal import Decimal

from src.config import CARPETA_REPORTES
from src.generador import generar_reporte


def main():
    resumen = {
        "numero_ventas": 3,
        "unidades_vendidas": 15,
        "total_facturado": Decimal("313.20"),
        "ticket_promedio": Decimal("104.40"),
        "por_categoria": [("Tecnología", Decimal("245.70")), ("Oficina", Decimal("67.50"))],
        "por_producto": [
            ("Teclado", Decimal("171.00")),
            ("Mouse", Decimal("74.70")),
            ("Cuaderno", Decimal("67.50")),
        ],
    }
    incidencias = ["Fila 5: cantidad cero (incidencia ficticia para mostrar el formato)"]
    ruta = generar_reporte(resumen, incidencias, CARPETA_REPORTES, "reporte_demo_melissa.txt")
    print("Demo de formato con resumen ficticio; no consulta ni modifica PostgreSQL.")
    print(f"Reporte generado en: {ruta}")


if __name__ == "__main__":
    main()
