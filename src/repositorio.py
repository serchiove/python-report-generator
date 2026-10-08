"""Persistencia de ventas validadas y consulta del contrato compartido."""

from datetime import date
from decimal import Decimal, InvalidOperation
import re


def _preparar_venta(venta):
    """Protege la persistencia; la validación del CSV pertenece al extractor."""
    producto = venta["producto"].strip()
    categoria = venta["categoria"].strip()
    fecha = venta["fecha"]
    if type(fecha) is not date:
        fecha = date.fromisoformat(fecha)
    cantidad = venta["cantidad"]
    if type(cantidad) is not int or not 0 < cantidad <= 2147483647:
        raise ValueError("cantidad debe ser un entero positivo de PostgreSQL")
    try:
        precio = Decimal(str(venta["precio_unitario"]))
    except InvalidOperation as error:
        raise ValueError("precio_unitario inválido") from error
    if not precio.is_finite() or not Decimal("0") <= precio < Decimal("10000000000"):
        raise ValueError("precio_unitario debe ser finito, no negativo y menor a 10000000000")
    if precio != precio.quantize(Decimal("0.01")):
        raise ValueError("precio_unitario admite como máximo dos decimales")
    if not producto or len(producto) > 150 or not categoria or len(categoria) > 100:
        raise ValueError("producto o categoría vacío o demasiado largo")
    fila = venta["fila_origen"]
    if type(fila) is not int or not 2 <= fila <= 2147483647:
        raise ValueError("fila_origen debe ser el número original de la fila CSV, desde 2")
    return producto, categoria, fecha, cantidad, precio, fila


def guardar_ventas(conexion, ventas, lote_hash):
    """Guarda un lote completo y retorna cuántas ventas se insertaron.

    ``ventas`` contiene fecha, producto, categoria, cantidad, precio_unitario
    y fila_origen. ``lote_hash`` es el SHA-256 de los bytes del CSV. Reimportar
    el mismo lote y fila no duplica ventas. Una excepción revierte el lote.
    """
    if not isinstance(lote_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", lote_hash):
        raise ValueError("lote_hash debe ser un SHA-256 hexadecimal en minúsculas")
    insertadas = 0
    with conexion.transaction():
        for venta in ventas:
            producto, categoria, fecha, cantidad, precio, fila = _preparar_venta(venta)
            # El conflicto actualiza al mismo valor y permite RETURNING
            # también si otro proceso creó el catálogo concurrentemente.
            id_categoria = conexion.execute(
                "INSERT INTO categorias (nombre) VALUES (%s) "
                "ON CONFLICT (nombre) DO UPDATE SET nombre = EXCLUDED.nombre "
                "RETURNING id_categoria", (categoria,),
            ).fetchone()["id_categoria"]
            id_producto = conexion.execute(
                "INSERT INTO productos (nombre, id_categoria) VALUES (%s, %s) "
                "ON CONFLICT (nombre, id_categoria) DO UPDATE SET nombre = EXCLUDED.nombre "
                "RETURNING id_producto", (producto, id_categoria),
            ).fetchone()["id_producto"]
            fila_insertada = conexion.execute(
                "INSERT INTO ventas (fecha, id_producto, cantidad, precio_unitario, "
                "lote_hash, fila_origen) VALUES (%s, %s, %s, %s, %s, %s) "
                "ON CONFLICT (lote_hash, fila_origen) DO NOTHING RETURNING id_venta",
                (fecha, id_producto, cantidad, precio, lote_hash, fila),
            ).fetchone()
            insertadas += fila_insertada is not None
    return insertadas


def consultar_ventas(conexion):
    """Retorna dicts con Decimal; los compañeros pueden calcular o reportar."""
    return conexion.execute(
        "SELECT v.id_venta, v.fecha, p.nombre AS producto, c.nombre AS categoria, "
        "v.cantidad, v.precio_unitario, v.cantidad * v.precio_unitario AS total, "
        "v.lote_hash, v.fila_origen FROM ventas v "
        "JOIN productos p USING (id_producto) "
        "JOIN categorias c USING (id_categoria) ORDER BY v.id_venta"
    ).fetchall()
