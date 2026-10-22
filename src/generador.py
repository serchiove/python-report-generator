"""Construcción y escritura de reportes de ventas."""


def generar_reporte(resumen, filas_invalidas, carpeta_reportes, nombre_reporte):
    """Recibe el resumen acordado con Ricardo; admite float y Decimal.

    filas_invalidas contiene las incidencias de la importación actual,
    no un historial de errores de la base de datos. None indica que no se importó.
    """
    carpeta_reportes.mkdir(parents=True, exist_ok=True)
    ruta_reporte = carpeta_reportes / nombre_reporte
    lineas = [
        "REPORTE AUTOMÁTICO DE VENTAS",
        "=" * 48,
        "RESUMEN GENERAL",
        f"Registros de venta: {resumen['numero_ventas']}",
        f"Unidades vendidas: {resumen['unidades_vendidas']}",
        f"Total facturado: ${resumen['total_facturado']:,.2f}",
        f"Importe promedio por registro: ${resumen['ticket_promedio']:,.2f}",
        "Nota: cada registro corresponde a un producto vendido.",
    ]
    if resumen["numero_ventas"] == 0:
        lineas.append("No hay ventas para mostrar en este resumen.")

    for titulo, clave in [
        ("FACTURACIÓN POR CATEGORÍA", "por_categoria"),
        ("PRODUCTOS POR FACTURACIÓN", "por_producto"),
    ]:
        lineas.extend(["", titulo, "-" * 48])
        grupos = list(resumen[clave])
        if grupos:
            lineas.extend(f"- {nombre}: ${total:,.2f}" for nombre, total in grupos)
        else:
            lineas.append("Sin datos.")

    lineas.extend([
        "", "INCIDENCIAS DE LA IMPORTACIÓN ACTUAL", "-" * 48,
    ])
    if filas_invalidas is None:
        lineas.append("Sin importación en esta ejecución; no se consultó un historial de incidencias.")
    else:
        lineas.append(f"Filas descartadas por errores: {len(filas_invalidas)}")
        if filas_invalidas:
            lineas.extend(f"- {error}" for error in filas_invalidas)
        else:
            lineas.append("No se registraron filas inválidas en esta ejecución.")
    ruta_reporte.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return ruta_reporte
