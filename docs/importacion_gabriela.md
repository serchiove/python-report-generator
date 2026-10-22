# Validación e importación de ventas CSV

Esta parte lee el CSV, valida cada fila y guarda las ventas válidas mediante
el repositorio PostgreSQL de Sergio. Usa el resumen SQL de Ricardo en las
pruebas para verificar la facturación. La unión definitiva con el reporte
de Melissa desde `main.py` queda para la tarea de integración.

## Ejecución

Instala `requirements.txt` y configura PostgreSQL y las variables `PG*` según
[la guía de conexión](postgresql_sergio.md). Después, desde PowerShell:

```powershell
.\.venv\Scripts\python.exe postgres.py inicializar
.\.venv\Scripts\python.exe postgres.py importar data/examples/ventas_ejemplo.csv
.\.venv\Scripts\python.exe postgres.py listar
```

El ejemplo contiene tres ventas válidas por 313.20 y una fila inválida con
cantidad cero. En una base vacía, devuelve 3 ventas nuevas y 1 fila descartada.
Al importar el mismo archivo otra vez devuelve 0 nuevas y 3 ya existentes.
Si antes se ejecutó `postgres.py demo`, ese lote ficticio es diferente del CSV:
no se deduplican ventas entre lotes distintos, aunque sus datos coincidan.
Para demostrar el total esperado usa una base de demostración vacía distinta
de cualquier base que tenga datos que quieras conservar.

## Reglas de validación

- CSV separado por comas, en UTF-8; se admite BOM y columnas reordenadas.
- Encabezados exactos, una vez cada uno: fecha, producto, categoria, cantidad,
  precio_unitario. No se admiten columnas adicionales o faltantes.
- Fecha real con formato YYYY-MM-DD; producto y categoría obligatorios, sin
  caracteres nulos, con límites de 150 y 100 caracteres respectivamente.
- Cantidad entera entre 1 y 2147483647.
- Precio finito, no negativo, menor a 10000000000, con punto decimal y hasta
  dos decimales. Se rechazan NaN, Infinity, notación científica y coma decimal.
- Importes representados como Decimal y fechas como datetime.date.
- Filas con más o menos campos se descartan y se registra el motivo.
- Las líneas completamente vacías se omiten. Se conserva el número físico
  de inicio de cada registro, incluso con filas descartadas o campos multilínea.
- Archivo vacío, UTF-8 inválido, encabezados incorrectos o comillas mal cerradas
  abortan el lote antes de escribir. Un fallo de persistencia revierte el lote.

## Contrato de integración

`cargar_ventas(ruta)` conserva la interfaz `(ventas, errores)` del programa
anterior. Ahora cada venta contiene `fila_origen`, `total` y precio Decimal.
El acumulador de `calcular_resumen` se adaptó para conservar esos importes y
mantener también compatibilidad con las entradas float existentes.

`cargar_lote(ruta)` devuelve `(ventas, errores, lote_hash)`. El hash SHA-256 y
las ventas se calculan sobre los mismos bytes, sin reabrir el archivo.

`importar_ventas(conexion, ruta)` devuelve un diccionario con `lote_hash`,
`ventas_validas`, `ventas_insertadas`, `ventas_ya_existentes` y `filas_invalidas`.
Estas incidencias pertenecen a la importación actual y podrán entregarse al
generador cuando se integre el flujo completo. No son un historial de errores.

## Pruebas y exposición

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_extractor.py -v
```

La suite PostgreSQL comprueba importación real, reimportación, totales y
conservación de la fila original. Requiere una base aislada y la habilitación
descrita en la guía de Sergio. Para exponer, muestra la fila inválida del
ejemplo, el resultado de la importación y la segunda ejecución sin duplicados.
