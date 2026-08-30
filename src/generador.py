"""Construcción y escritura de reportes."""


def generar_reporte(resumen, filas_invalidas, carpeta_reportes, nombre_reporte):
    """Genera un reporte de texto y devuelve la ruta del archivo creado."""

    carpeta_reportes.mkdir(parents=True, exist_ok=True)
    ruta_reporte = carpeta_reportes / nombre_reporte

    lineas = [
        "REPORTE AUTOMÁTICO DE VENTAS",
        "=" * 32,
        f"Ventas procesadas: {resumen['numero_ventas']}",
        f"Unidades vendidas: {resumen['unidades_vendidas']}",
        f"Total facturado: ${resumen['total_facturado']:,.2f}",
        f"Ticket promedio: ${resumen['ticket_promedio']:,.2f}",
        "",
        "FACTURACIÓN POR CATEGORÍA:",
    ]

    for categoria, total in resumen["por_categoria"]:
        lineas.append(f"- {categoria}: ${total:,.2f}")

    lineas.extend(["", "PRODUCTOS CON MAYOR FACTURACIÓN:"])

    for producto, total in resumen["por_producto"]:
        lineas.append(f"- {producto}: ${total:,.2f}")

    lineas.extend(
        ["", f"Filas descartadas por errores: {len(filas_invalidas)}"]
    )

    lineas.extend(f" {error}" for error in filas_invalidas)

    ruta_reporte.write_text("\n".join(lineas), encoding="utf-8")

    return ruta_reporte