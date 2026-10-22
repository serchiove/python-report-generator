"""Lectura de CSV y validación previa a la persistencia de ventas."""

import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from io import StringIO
from pathlib import Path
import re

COLUMNAS = {"fecha", "producto", "categoria", "cantidad", "precio_unitario"}


def _validar_fila(fila, numero_fila):
    """Retorna una venta con Decimal y su número físico original en el CSV."""
    campos = {clave: valor.strip() for clave, valor in fila.items()}
    for clave, valor in campos.items():
        if not valor:
            raise ValueError(f"{clave} es obligatorio")
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", campos["fecha"]):
        raise ValueError("fecha debe usar YYYY-MM-DD")
    try:
        fecha = date.fromisoformat(campos["fecha"])
    except ValueError as error:
        raise ValueError("fecha inexistente") from error
    for clave, limite in [("producto", 150), ("categoria", 100)]:
        if len(campos[clave]) > limite:
            raise ValueError(f"{clave} admite como máximo {limite} caracteres")
        if "\x00" in campos[clave]:
            raise ValueError(f"{clave} contiene un carácter nulo no permitido")
    texto_cantidad = campos["cantidad"]
    if not re.fullmatch(r"[0-9]+", texto_cantidad) or len(texto_cantidad) > 10:
        raise ValueError("cantidad debe ser un entero positivo hasta 2147483647")
    cantidad = int(texto_cantidad)
    if not 0 < cantidad <= 2147483647:
        raise ValueError("cantidad debe estar entre 1 y 2147483647")
    try:
        precio = Decimal(campos["precio_unitario"])
    except InvalidOperation as error:
        raise ValueError("precio_unitario debe ser numérico y usar punto decimal") from error
    if not precio.is_finite() or not Decimal("0") <= precio < Decimal("10000000000"):
        raise ValueError("precio_unitario debe ser finito, no negativo y menor a 10000000000")
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]{1,2})?", campos["precio_unitario"]):
        raise ValueError("precio_unitario debe usar punto y como máximo dos decimales")
    precio = precio.quantize(Decimal("0.01"))
    return dict(fecha=fecha, producto=campos["producto"], categoria=campos["categoria"],
                cantidad=cantidad, precio_unitario=precio, total=cantidad * precio,
                fila_origen=numero_fila)


def cargar_lote(ruta_archivo):
    """Retorna (ventas, errores, hash) leyendo los bytes del archivo una sola vez.

    Archivos ilegibles, encabezados incorrectos o sintaxis CSV rota abortan la
    lectura; errores de datos se registran por fila y permiten continuar.
    """
    contenido = Path(ruta_archivo).read_bytes()
    try:
        texto = contenido.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValueError("El CSV debe estar codificado en UTF-8") from error
    lector = csv.reader(StringIO(texto, newline=""), strict=True)
    ventas, errores = [], []
    try:
        encabezados = next(lector, None)
        if encabezados is None:
            raise ValueError("El CSV está vacío; faltan los encabezados")
        if len(encabezados) != len(COLUMNAS) or set(encabezados) != COLUMNAS:
            raise ValueError("Encabezados inválidos; se requieren una vez cada uno: "
                             + ", ".join(sorted(COLUMNAS)))
        while True:
            numero_fila = lector.line_num + 1
            valores = next(lector, None)
            if valores is None:
                break
            if not valores:
                continue
            if len(valores) != len(encabezados):
                errores.append(f"Fila {numero_fila}: se esperaban 5 campos y llegaron {len(valores)}")
                continue
            try:
                ventas.append(_validar_fila(dict(zip(encabezados, valores)), numero_fila))
            except ValueError as error:
                errores.append(f"Fila {numero_fila}: {error}")
    except csv.Error as error:
        raise ValueError(f"CSV mal formado cerca de la línea {lector.line_num}: {error}") from error
    return ventas, errores, sha256(contenido).hexdigest()


def cargar_ventas(ruta_archivo):
    """Conserva la interfaz (ventas, errores) que utiliza main.py."""
    ventas, errores, _ = cargar_lote(ruta_archivo)
    return ventas, errores
