# Guía de defensa de la segunda entrega

## Objetivo

Nuestro programa importa ventas desde un archivo CSV, valida sus datos y guarda
las filas válidas en PostgreSQL. Después consulta el resumen con SQL y genera un
reporte de texto. Podemos generar el reporte de nuevo sin importar otro archivo.

## Responsabilidades del equipo

| Integrante | Responsabilidad |
| --- | --- |
| Sergio | Esquema relacional, conexión, persistencia e integración final. |
| Gabriela | Validación e importación del CSV y conservación de la fila original. |
| Ricardo | Consultas SQL, métricas y agrupaciones. |
| Melissa | Formato del reporte, documentación y demostración de resultados. |

## Recorrido del programa

1. `main.py` recibe el CSV o utiliza el ejemplo versionado.
2. `src/extractor.py` lee los bytes, comprueba encabezados y valida cada fila.
3. `src/importador.py` entrega las ventas válidas y el hash al repositorio.
4. `src/repositorio.py` guarda categorías, productos y ventas en una transacción.
5. `src/procesador.py` consulta el resumen de toda la base mediante SQL.
6. `src/generador.py` escribe el reporte y las incidencias de esta importación.

`src/database.py` abre la conexión y crea el esquema cuando se solicita con
`postgres.py inicializar`. La configuración usa variables de entorno `PG*`.

## Modelo relacional

Una categoría tiene varios productos y un producto puede aparecer en varias
ventas. Las tablas son `categorias`, `productos` y `ventas`. Las claves foráneas
impiden que una venta haga referencia a un producto inexistente. Tampoco se
pueden borrar productos que tengan ventas asociadas.

Cada registro de venta corresponde a un producto, no a un comprobante completo.
El precio se guarda en la venta para conservar su valor histórico. Las fechas
usan `DATE`; los precios, `NUMERIC(12,2)` y `Decimal` en Python.

## Demostración

Con PostgreSQL configurado según el README y una base de demostración vacía:

```powershell
.\.venv\Scripts\python.exe postgres.py conexion
.\.venv\Scripts\python.exe postgres.py inicializar
.\.venv\Scripts\python.exe main.py
Get-Content -Encoding utf8 data/reports/reporte_final.txt
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe main.py --solo-reporte
```

El ejemplo tiene tres ventas válidas y una fila con cantidad cero. La primera
ejecución inserta tres registros; la segunda no inserta nuevos registros.

| Resultado | Valor esperado |
| --- | --- |
| Ventas | 3 |
| Unidades | 15 |
| Total | 313.20 |
| Promedio por registro | 104.40 |
| Tecnología | 245.70 |
| Oficina | 67.50 |

La opción `--solo-reporte` consulta los datos persistidos sin abrir el CSV.
El reporte indica que no hubo importación; no presenta un historial de errores.

## Preguntas de la exposición

**¿Cómo se detecta una importación repetida?** Se calcula SHA-256 sobre los bytes
del archivo y se conserva el número original de cada fila. La restricción única
del par hash y fila evita repetir esa venta del mismo archivo. Un archivo cuyos
bytes cambian se considera otro lote; no se detectan coincidencias entre lotes.

**¿Qué ocurre con una fila inválida?** Se registra su número y el motivo, y se
continúa con las demás. Encabezados incorrectos, codificación inválida o comillas
mal cerradas abortan el archivo antes de guardarlo.

**¿Qué evita guardar un lote a medias?** La escritura de las ventas y sus
catálogos se realiza en una transacción. Si falla una fila al guardar, se
revierten los cambios de ese lote.

**¿Por qué Decimal?** Conserva la precisión de los importes en el recorrido
entre Python y PostgreSQL sin convertir el dinero a punto flotante binario.

**¿De dónde salen los totales?** De consultas PostgreSQL con `JOIN`, `SUM`,
`COUNT`, `AVG` y `GROUP BY`. El reporte resume todas las ventas de la base,
no solo las del último archivo.

**¿Qué pasa si falla la escritura del reporte?** La importación ya confirmada
permanece en PostgreSQL. Se puede repetir el mismo archivo sin duplicar sus
ventas o generar solo el reporte cuando se resuelva el problema de salida.

**¿Qué muestran las pruebas?** Validación de entradas, integridad relacional,
precisión monetaria, reversión de transacciones, reimportación y generación
del reporte con una base de pruebas aislada.

## Alcance de la entrega

La aplicación funciona por consola. No incluye interfaz web, autenticación de
usuarios de negocio ni comprobantes con varios detalles. Los datos de ejemplo
son ficticios. La revisión del código y la participación se acreditan con el
historial del repositorio y las revisiones del equipo.
