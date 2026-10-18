# Generador de reportes de ventas

Aplicación de consola en Python para procesar ventas y generar reportes de texto.

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

## Ejecutar el flujo CSV actual

Prepara `data/raw/ventas.csv` en UTF-8 con estos encabezados:

```csv
fecha,producto,categoria,cantidad,precio_unitario
2026-08-01,Teclado,Tecnología,2,85.50
2026-08-01,Mouse,Tecnología,3,24.90
2026-08-01,Cuaderno,Oficina,10,6.75
```

Si el archivo ya existe, conserva una copia antes de reemplazarlo. Los CSV de
`data/raw` están ignorados por Git; el ejemplo anterior permite recrearlo.

```powershell
.\.venv\Scripts\python.exe main.py
Get-Content -Encoding utf8 data/reports/reporte_final.txt
```

El reporte muestra registros, unidades, facturación, promedio por registro,
agrupaciones e incidencias. Cada ejecución reemplaza su archivo de salida.
Una fila representa un producto vendido; el promedio no es por comprobante.

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
- `main.py` sigue leyendo CSV y calculando con el procesador actual; todavía
  no genera el reporte desde PostgreSQL.
- Falta integrar las validaciones de Gabriela y las consultas con `Decimal` de
  Ricardo. El extractor actual aún requiere corregir fechas, precios no finitos
  y campos ausentes antes de demostrar esas validaciones como completas.

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
Consulta el [guion de Melissa](docs/demo_melissa.md) para la demostración y las
diapositivas 7 y 8.
