# Generador de reportes de ventas

Aplicación de consola en Python para procesar ventas y generar reportes de texto.

Segunda entrega: importación validada de CSV, almacenamiento relacional en
PostgreSQL, métricas mediante SQL y reporte con importes decimales.
Consulta la [guía de defensa](docs/guia_defensa.md) y el
[registro de verificación](docs/verificacion_entrega.md).

## Preparación en Windows

Abre una terminal de PowerShell en la carpeta que contiene `main.py`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Para los comandos PostgreSQL necesitas el servidor instalado y activo.
La [guía de Sergio](docs/postgresql_sergio.md) explica cómo crear el usuario y la
base, configurar las variables `PG*` y conectar desde Python. No guardes
contraseñas reales en archivos versionados.

## Probar el reporte de Melissa

Esta demo funciona sin base de datos y sin CSV:

```powershell
.\.venv\Scripts\python.exe demo_reporte.py
Get-Content -Encoding utf8 data/reports/reporte_demo_melissa.txt
```

Usa un resumen ficticio con `Decimal`: 3 registros, 15 unidades, total 313.20,
promedio por registro 104.40, Tecnología 245.70 y Oficina 67.50. Incluye una
incidencia ficticia para enseñar el formato; no valida ni importa filas reales.
El símbolo `$` conserva el formato del proyecto y no convierte monedas.

## Ejecutar la entrega completa

Con PostgreSQL activo, la base creada y las variables `PG*` configuradas:

```powershell
.\.venv\Scripts\python.exe postgres.py inicializar
.\.venv\Scripts\python.exe main.py
Get-Content -Encoding utf8 data/reports/reporte_final.txt
```

`main.py` usa por defecto `data/examples/ventas_ejemplo.csv`: valida el archivo,
guarda las filas válidas, consulta las métricas en PostgreSQL y escribe el
reporte. En una base vacía debe mostrar 3 ventas nuevas, 15 unidades, total
313.20 y una incidencia por cantidad cero. Al repetirlo habrá 0 ventas nuevas,
sin modificar el total. Una fila representa un producto vendido; el promedio
104.40 es por registro, no por comprobante.

Para usar otro CSV o generar el reporte sin importar ningún archivo:

```powershell
.\.venv\Scripts\python.exe main.py data/raw/ventas.csv
.\.venv\Scripts\python.exe main.py --solo-reporte
.\.venv\Scripts\python.exe main.py --solo-reporte --salida data/reports/otro_reporte.txt
```

Las métricas abarcan **todas las ventas de la base**, no solo el archivo actual.
Las incidencias corresponden al CSV de esta ejecución; con `--solo-reporte`
se indica que no hubo importación, sin afirmar que no existan errores históricos.
Cada ejecución reemplaza el reporte de destino. La importación se confirma
antes de generar el reporte: si falla su escritura, las ventas permanecen
guardadas y se puede reintentar el mismo CSV sin duplicarlo, o usar `--solo-reporte`.

## Comprobar PostgreSQL

Tras preparar la conexión según la guía de Sergio:

```powershell
.\.venv\Scripts\python.exe postgres.py conexion
.\.venv\Scripts\python.exe postgres.py inicializar
.\.venv\Scripts\python.exe postgres.py demo
.\.venv\Scripts\python.exe postgres.py listar
```

En una base vacía, la demo inserta 3 ventas con total 313.20; al repetirla inserta
0 ventas nuevas. Para ver las tablas en psql, conecta con
`psql -h localhost -U reportes_app -d reportes_ventas` y ejecuta `\dt`.
En pgAdmin, conecta al servidor y abre Databases > reportes_ventas > Schemas >
public > Tables; actualiza la vista si las tablas todavía no aparecen.

## Estado de integración

- Sergio: esquema, conexión y persistencia PostgreSQL disponibles.
- Melissa: formato del reporte, demo independiente y documentación disponibles.
- Sergio: unión final desde `main.py`, errores de ejecución y modo solo reporte.
- Ricardo: consultas SQL del resumen con JOIN, GROUP BY y Decimal disponibles.
- Gabriela: validación del CSV e importación a PostgreSQL disponibles;
  consulta [la guía de importación](docs/importacion_gabriela.md).

Para importar el ejemplo versionado, con la conexión PostgreSQL configurada:

```powershell
.\.venv\Scripts\python.exe postgres.py importar data/examples/ventas_ejemplo.csv
```

Contiene tres ventas válidas y una inválida. Reimportar el mismo archivo no
duplica ventas. La demo ficticia de Sergio es otro lote distinto: no mezcles
ambas demos en la misma base si necesitas conservar el total de ejemplo 313.20.

`generar_reporte` recibe las claves `numero_ventas`, `unidades_vendidas`,
`total_facturado`, `ticket_promedio`, `por_categoria` y `por_producto`.
Las agrupaciones son secuencias de pares `(nombre, total)`. Los importes admiten
`Decimal` y se muestran con dos decimales sin convertirlos a `float`.
Las incidencias corresponden a la importación actual, no al historial persistido.

## Verificación y exposición

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_generador.py -v
```

Las pruebas de PostgreSQL requieren una base de pruebas independiente y las
variables de habilitación descritas en la guía de Sergio.
Con esa base configurada, ejecutar toda la suite:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

La suite usa esquemas temporales dentro de la base de pruebas y verifica también
el flujo completo, la reimportación y la generación sin volver a abrir el CSV.
Consulta el [guion de Melissa](docs/demo_melissa.md) para la demostración y las
diapositivas 7 y 8.
