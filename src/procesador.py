from collections import defaultdict
from decimal import Decimal


def consultar_resumen(conexion):
    
    with conexion.transaction():
        conexion.execute(
            "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY"
        )

        # 1. Métricas generales
        totales = conexion.execute(
            """
            SELECT COUNT(*) AS numero_ventas,
                   COALESCE(SUM(v.cantidad), 0) AS unidades_vendidas,
                   COALESCE(SUM(v.cantidad * v.precio_unitario), 0)::numeric(18, 2)
                       AS total_facturado,
                   COALESCE(AVG(v.cantidad * v.precio_unitario), 0)::numeric(18, 2)
                       AS ticket_promedio
            FROM ventas AS v
            JOIN productos AS p ON p.id_producto = v.id_producto
            JOIN categorias AS c ON c.id_categoria = p.id_categoria
            """
        ).fetchone()

        # 2. Facturación agrupada por categoría
        por_categoria = conexion.execute(
            """
            SELECT c.nombre AS nombre,
                   SUM(v.cantidad * v.precio_unitario)::numeric(18, 2) AS total
            FROM ventas AS v
            JOIN productos AS p ON p.id_producto = v.id_producto
            JOIN categorias AS c ON c.id_categoria = p.id_categoria
            GROUP BY c.id_categoria, c.nombre
            ORDER BY total DESC, c.nombre ASC
            """
        ).fetchall()

        # 3. Facturación agrupada por producto
        por_producto = conexion.execute(
            """
            SELECT p.nombre AS nombre,
                   SUM(v.cantidad * v.precio_unitario)::numeric(18, 2) AS total
            FROM ventas AS v
            JOIN productos AS p ON p.id_producto = v.id_producto
            GROUP BY p.id_producto, p.nombre
            ORDER BY total DESC, p.nombre ASC
            """
        ).fetchall()

    # 4. Contrato que necesita generador.py
    return {
        "numero_ventas": totales["numero_ventas"],
        "unidades_vendidas": totales["unidades_vendidas"],
        "total_facturado": totales["total_facturado"],
        "ticket_promedio": totales["ticket_promedio"],
        "por_categoria": [(f["nombre"], f["total"]) for f in por_categoria],
        "por_producto": [(f["nombre"], f["total"]) for f in por_producto],
    }


def calcular_resumen(ventas):

    usa_decimal = any(isinstance(venta["total"], Decimal) for venta in ventas)
    tipo_importe = Decimal if usa_decimal else float
    total_facturado = tipo_importe(0)
    unidades_vendidas = 0
    total_por_categoria = defaultdict(tipo_importe)
    total_por_producto = defaultdict(tipo_importe)

    for venta in ventas:
        importe = Decimal(str(venta["total"])) if usa_decimal else venta["total"]
        total_facturado += importe
        unidades_vendidas += venta["cantidad"]
        total_por_categoria[venta["categoria"]] += importe
        total_por_producto[venta["producto"]] += importe

    return {
        "numero_ventas": len(ventas),
        "unidades_vendidas": unidades_vendidas,
        "total_facturado": total_facturado,
        "ticket_promedio": (
            total_facturado / len(ventas) if ventas else 0
        ),
        "por_categoria": sorted(
            total_por_categoria.items(),
            key=lambda elemento: elemento[1],
            reverse=True,
        ),
        "por_producto": sorted(
            total_por_producto.items(),
            key=lambda elemento: elemento[1],
            reverse=True,
        ),
    }
