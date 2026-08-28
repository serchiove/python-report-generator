"""Lectura y validación de datos externos."""

import csv


def cargar_ventas(ruta_archivo):
    """Lee un CSV y devuelve (ventas_validas, errores_encontrados)."""
    ventas = []
    filas_invalidas = []

    with open(ruta_archivo, mode="r", encoding="utf-8", newline="") as archivo:
        lector = csv.DictReader(archivo)

        # Cada iteración convierte una fila del CSV en un diccionario de Python.
        for numero_fila, fila in enumerate(lector, start=2):
            try:
                cantidad = int(fila["cantidad"])
                precio_unitario = float(fila["precio_unitario"])

                venta = {
                    "fecha": fila["fecha"].strip(),
                    "producto": fila["producto"].strip(),
                    "categoria": fila["categoria"].strip(),
                    "cantidad": cantidad,
                    "precio_unitario": precio_unitario,
                    "total": cantidad * precio_unitario,
                }

                if not venta["producto"] or cantidad <= 0 or precio_unitario < 0:
                    raise ValueError("producto vacío o valor no permitido")

                ventas.append(venta)
            except (KeyError, ValueError, TypeError) as error:
                filas_invalidas.append(f"Fila {numero_fila}: {error}")

    return ventas, filas_invalidas
