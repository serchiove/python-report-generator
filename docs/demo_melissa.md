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

1. Configurar PostgreSQL según el README e inicializar las tablas.
2. En una base de demostración vacía, ejecutar `python main.py` y abrir
   `data/reports/reporte_final.txt`.
3. Comprobar 3 registros, 15 unidades, total 313.20 y promedio 104.40.
4. Mostrar Tecnología 245.70, Oficina 67.50 y la incidencia real del CSV de ejemplo.
5. Repetir `python main.py`: 0 ventas nuevas. Ejecutar `python main.py --solo-reporte`
   para mostrar la generación desde los datos persistidos.
6. Mostrar commits y revisiones reales del equipo cuando existan.

Guion: «Esta demostración importa un CSV con datos ficticios a PostgreSQL,
consulta el resumen y genera el reporte. La fila con cantidad cero se descarta.
Al repetir el mismo archivo no se duplican ventas. También podemos regenerar
el reporte sin volver a importar. El README documenta el recorrido completo».

`demo_reporte.py` permanece como demostración independiente del formato,
sin conexión a PostgreSQL; no debe confundirse con la ejecución completa.

Tiempo sugerido: 1 minuto para explicar el reporte y 1 minuto y medio para
la demo y el cierre.

## Revisión de Gabriela que corresponde a Melissa

Durante la revisión cruzada, comprobar con datos ficticios:

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
