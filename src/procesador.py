from collections import defaultdict

def calcular_resumen(ventas):
    total_facturado = 0.0
    unidades_vendidas = 0
    total_por_categoria = defaultdict(float)
    total_por_producto = defaultdict(float)

    for venta in ventas:
        total_facturado += venta["total"]
        unidades_vendidas += venta["cantidad"]
        total_por_categoria[venta["categoria"]] += venta["total"]
        total_por_producto[venta["producto"]] += venta["total"]

    return {
        "numero_ventas": len(ventas),
        "unidades_vendidas": unidades_vendidas,
        "total_facturado": total_facturado,
        "ticket_promedio": total_facturado / len(ventas) if ventas else 0,
        "por_categoria": sorted(
            total_por_categoria.items(), key=lambda elemento: elemento[1], reverse=True
        ),
        "por_producto": sorted(
            total_por_producto.items(), key=lambda elemento: elemento[1], reverse=True
        ),
    }