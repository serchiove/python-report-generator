# Verificación de la segunda entrega

Fecha de ejecución: 22 de octubre de 2026.

## Entorno y alcance

Se ejecutaron las pruebas desde una copia de los archivos de entrega, con el
entorno virtual del proyecto, Python 3.12, Psycopg 3.3.6 y PostgreSQL 18.
Se utilizó una instancia local aislada y una base de pruebas con esquemas
temporales. No se utilizaron ni modificaron los datos de la base de presentación.

## Suite automatizada

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Resultado: **31 pruebas ejecutadas, todas aprobadas**. Las pruebas de PostgreSQL
se ejecutaron contra el motor real, sin omitirlas.

| Área | Casos cubiertos |
| --- | --- |
| CSV | Encabezados, UTF-8, BOM, columnas reordenadas, campos y filas incompletas. |
| Validación | Fechas, cantidades, precios, límites y valores no finitos. |
| Contrato | Decimal, fechas y números originales de fila, incluso con campos multilínea. |
| Persistencia | Reconexión, precisión monetaria, claves foráneas y restricciones de borrado. |
| Importación | Hash del archivo, filas inválidas, reimportación sin duplicados y rollback. |
| Consultas SQL | Totales, agrupaciones, base vacía y ordenamiento con empates. |
| Reporte | Resumen, importes grandes, incidencias y ausencia de ventas. |
| Integración | Importar, consultar y reportar; modo solo reporte; recuperación tras fallo de salida. |
| Terminal | Código de error ante conexión no disponible y argumentos incompatibles. |

## Demostración por consola

También se comprobaron los comandos reales desde un esquema inicialmente vacío:

| Operación | Resultado observado |
| --- | --- |
| `postgres.py conexion` | Conexión correcta con el usuario de pruebas. |
| `postgres.py inicializar` | Creación de las tres tablas y sus relaciones. |
| Primera ejecución de `main.py` | 3 ventas nuevas, 15 unidades y 1 fila descartada. |
| Segunda ejecución del mismo CSV | 0 ventas nuevas; se conservan 3 registros. |
| Total y promedio por registro | 313.20 y 104.40. |
| Agrupación por categoría | Tecnología 245.70 y Oficina 67.50. |
| `main.py --solo-reporte` | Reporte desde PostgreSQL sin importar un archivo. |
| `demo_reporte.py` | Reporte independiente de formato generado correctamente. |
| CSV inexistente | Mensaje de error y código de salida 1. |
| Conexión a puerto no disponible | Mensaje de conexión fallida y código de salida 1. |

Se leyó el reporte generado y se verificaron los importes y el número de fila
de la incidencia. La instancia temporal se detuvo al finalizar.

## Preparación para exponer

1. Configurar la conexión del equipo de presentación con la guía del README.
2. Si se requieren exactamente los totales de ejemplo, utilizar una base de
   demostración vacía; no mezclar el CSV con otros lotes ficticios.
3. Ejecutar `main.py`, abrir el reporte y mostrar las tablas en pgAdmin.
4. Repetir la importación para demostrar que no duplica registros.
5. Ejecutar `--solo-reporte` para mostrar la persistencia de la información.

Esta verificación registra pruebas técnicas. Las revisiones cruzadas y los
acuerdos del equipo se documentan por separado en GitHub.
