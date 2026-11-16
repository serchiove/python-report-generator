"""Genera un QR con el resumen de ventas."""

from io import BytesIO
from pathlib import Path
from uuid import uuid4

import qrcode


def generar_qr(resumen, ruta_reporte):
    """Guarda el QR junto al TXT y devuelve su ruta."""
    contenido = (
        "REPORTE DE VENTAS\n"
        f"Registros: {resumen['numero_ventas']}\n"
        f"Unidades: {resumen['unidades_vendidas']}\n"
        f"Total: {resumen['total_facturado']:.2f}\n"
        f"Promedio por registro: {resumen['ticket_promedio']:.2f}"
    )

    ruta_qr = Path(ruta_reporte).with_suffix(".png")

    imagen = qrcode.make(contenido)
    # Escribe primero en un archivo nuevo para no truncar un QR existente.
    buffer = BytesIO()
    imagen.save(buffer, format="PNG")
    temporal = ruta_qr.with_name(f".qr_{uuid4().hex}.tmp")
    try:
        temporal.write_bytes(buffer.getvalue())
        temporal.replace(ruta_qr)
    except OSError as error:
        raise OSError(
            f"No se pudo guardar el QR en {ruta_qr}. "
            "Cierra la imagen si está abierta o elige otro nombre de salida TXT "
            "(por ejemplo reporte_nuevo.txt) y vuelve a generar el reporte. "
            f"Detalle: {error}"
        ) from error
    finally:
        if temporal.exists():
            temporal.unlink()

    return ruta_qr