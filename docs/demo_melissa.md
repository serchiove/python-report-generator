# Demostración y exposición de Melissa

## Diapositiva 7: presentación de resultados

- Reporte de texto con resumen, agrupaciones e incidencias.
- Importes con dos decimales y compatibilidad con Decimal.
- Promedio por registro de producto vendido, no por comprobante.
- Caso sin ventas e identificación de filas descartadas.

Guion: «Mi parte presenta los resultados en un reporte legible. Se muestran el
número de registros, las unidades, la facturación y el promedio por registro.
Las agrupaciones ayudan a comparar categorías y productos. Las incidencias se
muestran aparte para identificar qué filas se descartaron en la importación».

## Diapositiva 8: demostración y organización

1. Ejecutar `python demo_reporte.py` desde el entorno del proyecto.
2. Abrir `data/reports/reporte_demo_melissa.txt`.
3. Comprobar 3 registros, 15 unidades, total 313.20 y promedio 104.40.
4. Mostrar Tecnología 245.70, Oficina 67.50 y la incidencia ficticia.
5. Explicar cómo el README permite reproducir la demo.
6. Mostrar commits y revisiones reales del equipo cuando existan.

Guion: «Esta demostración usa un resumen ficticio para comprobar el formato de
mi módulo de manera independiente. La persistencia de Sergio se puede probar
con sus comandos. La demostración completa desde PostgreSQL requiere integrar
las validaciones y las consultas del equipo. Documentamos el estado real para
que cada paso se pueda reproducir».

Tiempo sugerido: 1 minuto para explicar el reporte y 1 minuto y medio para
la demo y el cierre. Ajustar el guion cuando se integre el flujo final.

## Revisión de Gabriela que corresponde a Melissa

Cuando su parte esté disponible, comprobar con datos ficticios:

- Una fila válida llega al resumen con el importe esperado.
- Cantidad cero, fecha inválida, NaN y campo ausente producen incidencias.
- Cada incidencia conserva el número de fila original.
- Reimportar el mismo archivo no aumenta las ventas persistidas.

Estos puntos son criterios pendientes de revisión, no pruebas ya superadas.

## Evidencias que se deben guardar

- Comando y salida de las pruebas del reporte.
- Reporte de demo y captura de sus resultados.
- Enlace del commit o PR de Melissa y revisión real de Ricardo.
- Resultado de la revisión de Gabriela cuando se realice.

Antes de exponer: ensayar el README desde una copia nueva; comprobar el flujo
integrado y reemplazar las afirmaciones pendientes por resultados verificados.
