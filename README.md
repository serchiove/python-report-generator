# Generador de reportes de ventas

## Nuestro proyecto

Desarrollamos una aplicación de consola en Python para automatizar el procesamiento
de ventas. Para la segunda entrega integramos una base de datos PostgreSQL: leemos
un CSV, validamos cada registro, almacenamos las ventas válidas, consultamos las
métricas mediante SQL y generamos un reporte de texto.

Con esta integración podemos conservar las ventas después de cerrar el programa
y generar otro reporte sin volver a importar el archivo.

**Flujo principal:** CSV → validación → PostgreSQL → resumen SQL → reporte.

## Organización del equipo

Organizamos el desarrollo en cuatro responsabilidades y reunimos los módulos
en un punto de entrada común, `main.py`.

| Integrante | Parte del proyecto |
| --- | --- |
| Sergio | Diseño relacional, conexión, persistencia e integración final. |
| Gabriela | Validación del CSV, importación y conservación de la fila original. |
| Ricardo | Consultas SQL, cálculos y agrupaciones. |
| Melissa | Formato del reporte, documentación y demostración de resultados. |

El historial y los pull requests del repositorio permiten consultar los cambios
de cada etapa. Las revisiones entre integrantes se registran en GitHub.

## Herramientas y requisitos

- Python 3.10 o superior; verificamos la entrega con Python 3.12.
- PostgreSQL instalado y activo; verificamos la entrega con PostgreSQL 18.
- Psycopg 3 para conectar Python con PostgreSQL, incluido en `requirements.txt`.
- pgAdmin para crear la base y consultar los datos.
- PowerShell para ejecutar los comandos de Windows que aparecen a continuación.

La aplicación funciona por consola. pgAdmin administra la base de datos;
no es una interfaz propia del programa. No necesitamos activar el entorno
virtual: los comandos utilizan directamente su ejecutable de Python.

## Instalación

Desde PowerShell, abrimos la carpeta donde están `main.py` y `requirements.txt`.
Si estamos en CMD, escribimos primero `powershell`. No copiamos el indicador
`PS C:\...>`: solo los comandos de los bloques.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Si `.venv` ya existe y tiene las dependencias instaladas, no hace falta recrearlo.

## Preparación en pgAdmin

Para una demostración con los resultados exactos de este documento utilizamos
una base nueva llamada `reportes_presentacion`. Si ya existe y contiene ventas,
podemos utilizar otra base vacía y ajustar `PGDATABASE`; no necesitamos borrar
datos existentes.

1. Abrimos el servidor PostgreSQL en pgAdmin con el usuario administrador.
2. En **Login/Group Roles → Create → Login/Group Role**, creamos `reportes_app`.
3. En **Definition**, asignamos su contraseña y, en **Privileges**, activamos
   **Can login?**. Si el usuario ya existe, omitimos su creación.
4. En **Databases → Create → Database**, creamos `reportes_presentacion`.
5. Seleccionamos `reportes_app` como **Owner** y guardamos.

El programa creará las tablas en el paso de inicialización. Las instrucciones
alternativas para psql están en la [guía de PostgreSQL](docs/postgresql_sergio.md).

## Configuración de la conexión

En la misma ventana de PowerShell donde ejecutaremos el programa:

```powershell
$env:PGHOST = 'localhost'
$env:PGPORT = '5432'
$env:PGDATABASE = 'reportes_presentacion'
$env:PGUSER = 'reportes_app'

$clave = Read-Host 'Contraseña de reportes_app' -AsSecureString
$env:PGPASSWORD = [System.Net.NetworkCredential]::new('', $clave).Password
```

Introducimos la contraseña de `reportes_app`, no necesariamente la del usuario
administrador. Estas variables duran en esta sesión; si cerramos PowerShell,
debemos configurarlas de nuevo. No guardamos contraseñas en el repositorio.

Si Windows bloquea la biblioteca binaria de Psycopg, utilizamos la implementación
Python con la biblioteca de PostgreSQL instalada. Ajustamos `18` si instalamos
otra versión:

```powershell
$env:PATH = 'C:\Program Files\PostgreSQL\18\bin;' + $env:PATH
$env:PSYCOPG_IMPL = 'python'
```

Comprobamos la conexión y creamos las tablas:

```powershell
.\.venv\Scripts\python.exe postgres.py conexion
.\.venv\Scripts\python.exe postgres.py inicializar
```

Esperamos `Conexión correcta: reportes_presentacion / reportes_app` y la
confirmación de creación del esquema. Podemos repetir la inicialización:
no borra las ventas ni crea otra base de datos.

## Prueba completa paso a paso

### Revisar los datos de entrada

Incluimos el ejemplo en el repositorio para reproducir la entrega desde una copia
nueva, sin preparar manualmente un CSV.

```powershell
Get-Content -Encoding utf8 data/examples/ventas_ejemplo.csv
```

```csv
fecha,producto,categoria,cantidad,precio_unitario
2026-08-01,Teclado,Tecnología,2,85.50
2026-08-01,Mouse,Tecnología,3,24.90
2026-08-01,Cuaderno,Oficina,10,6.75
2026-08-01,Monitor,Tecnología,0,120.00
```

La fila de Monitor tiene cantidad cero. La descartamos y mostramos su número
original, mientras continuamos con las tres ventas válidas.

### Ejecutar el programa y abrir el reporte

```powershell
.\.venv\Scripts\python.exe main.py
notepad data/reports/reporte_final.txt
```

En una base inicialmente vacía, estos son los resultados:

| Resultado | Valor |
| --- | --- |
| Ventas nuevas | 3 |
| Registros de venta en la base | 3 |
| Unidades vendidas | 15 |
| Total facturado | 313.20 |
| Promedio por registro | 104.40 |
| Tecnología | 245.70 |
| Oficina | 67.50 |
| Filas descartadas | 1, correspondiente a la fila 5 |

El reporte muestra además los productos: Teclado 171.00, Mouse 74.70 y Cuaderno
67.50. El símbolo `$` es el formato de presentación del proyecto; no realizamos
conversión de monedas. Cada registro representa un producto vendido: el promedio
es por registro, no por comprobante.

### Comprobar que no duplicamos ventas

```powershell
.\.venv\Scripts\python.exe main.py
```

La segunda ejecución del mismo archivo muestra **0 ventas nuevas**, 3 ya
existentes y el mismo total 313.20. Identificamos cada registro con el hash de
los bytes del CSV y su fila original. Un archivo con bytes distintos es otro
lote, aunque contenga ventas similares.

### Generar un reporte sin importar el CSV

```powershell
.\.venv\Scripts\python.exe main.py --solo-reporte --salida data/reports/solo_postgresql.txt
notepad data/reports/solo_postgresql.txt
```

El programa consulta lo que ya guardamos en PostgreSQL. Mantiene las métricas y
señala **“Sin importación en esta ejecución”** en incidencias. No consultamos ni
almacenamos un historial de errores de importaciones anteriores.

Los totales incluyen todas las ventas de la base, no solo el último CSV. Cada
ejecución reemplaza el archivo de salida elegido. La importación se confirma
antes de generar el reporte: si falla su escritura, podemos corregir el destino
y repetir el mismo archivo sin duplicar las ventas, o usar `--solo-reporte`.

### Ver los datos en pgAdmin

Abrimos **reportes_presentacion → Query Tool** y ejecutamos con F5:

```sql
SELECT v.id_venta, v.fecha,
       p.nombre AS producto, c.nombre AS categoria,
       v.cantidad, v.precio_unitario,
       v.cantidad * v.precio_unitario AS total
FROM ventas v
JOIN productos p USING (id_producto)
JOIN categorias c USING (id_categoria)
ORDER BY v.id_venta;
```

Veremos las tres ventas válidas. Monitor no debe aparecer. Las tablas están en
**Schemas → public → Tables**; usamos **Refresh** si no aparecen de inmediato.

## Modelo relacional y módulos

Una categoría tiene varios productos y un producto puede aparecer en varias
ventas: **categorias (1) → (N) productos (1) → (N) ventas**.

Usamos claves primarias, claves foráneas obligatorias y restricciones de valores.
No permitimos borrar productos con ventas asociadas. Almacenamos fechas con
`DATE`, precios con `NUMERIC(12,2)` y los representamos como `Decimal` en Python.
Guardamos el precio en cada venta para conservar su valor histórico.

| Archivo | Función en el proyecto |
| --- | --- |
| `main.py` | Coordina importación, consulta y reporte; admite modo solo reporte. |
| `src/config.py` | Define el CSV de ejemplo y el destino por defecto. |
| `src/extractor.py` | Valida el archivo y conserva números de fila y hash. |
| `src/importador.py` | Entrega los datos válidos al repositorio y devuelve las incidencias. |
| `src/database.py` | Abre la conexión y permite inicializar las tablas. |
| `src/repositorio.py` | Guarda las ventas con transacciones y evita reimportaciones duplicadas. |
| `src/procesador.py` | Consulta métricas con JOIN, SUM, COUNT, AVG y GROUP BY. |
| `src/generador.py` | Escribe el resumen, agrupaciones e incidencias en texto. |
| `sql/schema.sql` | Define las tres tablas, relaciones, restricciones e índices. |
| `tests/` | Comprueba los módulos y el recorrido completo. |

## Reglas de validación

- Requerimos los cinco encabezados del ejemplo, una sola vez; admitimos otro orden.
- Usamos CSV separado por comas y codificado en UTF-8, con o sin BOM.
- Validamos fechas reales en formato YYYY-MM-DD.
- Producto y categoría son obligatorios y tienen límites de 150 y 100 caracteres.
- La cantidad debe ser un entero entre 1 y 2147483647.
- El precio debe ser finito, no negativo, menor a 10000000000 y tener hasta dos
  decimales con punto. Rechazamos NaN, infinito y notación científica.
- Registramos las filas con datos inválidos y continuamos con las válidas.
- Encabezados incorrectos, codificación inválida o sintaxis CSV rota abortan
  el archivo antes de escribir en la base.
- Si ocurre un error al guardar el lote, revertimos sus cambios mediante una
  transacción. Las consultas utilizan parámetros para los valores recibidos.

## Otros comandos

Para importar nuestro propio CSV y obtener su reporte:

```powershell
.\.venv\Scripts\python.exe main.py data/raw/ventas.csv
```

Ese archivo debe existir y respetar el formato. Los CSV de `data/raw` están
ignorados por Git para no versionar datos privados.

Para probar únicamente la importación o listar las ventas:

```powershell
.\.venv\Scripts\python.exe postgres.py importar data/examples/ventas_ejemplo.csv
.\.venv\Scripts\python.exe postgres.py listar
```

Conservamos dos demostraciones auxiliares:

- `demo_reporte.py` prueba el formato con un resumen ficticio; no toca PostgreSQL.
- `postgres.py demo` guarda un lote ficticio distinto del CSV. **No lo ejecutamos
  en la base de presentación junto al CSV si esperamos el total 313.20**: mezclar
  ambos lotes en una base vacía puede llevar el total a 626.40. Para comprobar
  el recorrido completo utilizamos `main.py` como se explicó arriba.

## Pruebas automatizadas

Verificamos la entrega con **31 pruebas aprobadas**, incluidas las de PostgreSQL
real y el recorrido completo. El detalle está en el
[registro de verificación](docs/verificacion_entrega.md).

Para repetir la suite, creamos en pgAdmin una base separada llamada
`reportes_ventas_test`, con `reportes_app` como propietario. Con la conexión y
contraseña configuradas en PowerShell:

```powershell
$env:PGDATABASE = 'reportes_ventas_test'
$env:POSTGRES_TEST_DATABASE = 'reportes_ventas_test'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Usamos esquemas temporales dentro de esa base; no vaciamos las tablas públicas.
Sin esas variables, las pruebas de PostgreSQL se omiten. Para volver a la demo:

```powershell
Remove-Item Env:POSTGRES_TEST_DATABASE
$env:PGDATABASE = 'reportes_presentacion'
```

## Presentación del trabajo

Preparamos una exposición de aproximadamente diez minutos: dos diapositivas y
dos minutos y medio por integrante. Acompañamos las explicaciones con los datos
del ejemplo y el programa funcionando.

| Integrante | Diapositivas | Contenido |
| --- | --- | --- |
| Sergio | 1 y 2 | Problema, objetivo, arquitectura y modelo PostgreSQL. |
| Gabriela | 3 y 4 | CSV, validaciones, importación y control de duplicados. |
| Ricardo | 5 y 6 | Consultas SQL, métricas y pruebas. |
| Melissa | 7 y 8 | Reporte, demostración de resultados y conclusiones. |

### Sergio abre la presentación

“Desarrollamos un programa que automatiza el procesamiento de ventas. En esta
segunda entrega incorporamos PostgreSQL para conservar los datos y generar
reportes desde la información almacenada. Organizamos el modelo en categorías,
productos y ventas, con claves foráneas para mantener las relaciones. Integramos
los módulos del equipo en `main.py` para ejecutar el recorrido completo.”

Mostramos el objetivo, el flujo y las tablas en pgAdmin. Explicamos por qué
guardamos el precio histórico en cada venta y por qué usamos Decimal.

### Gabriela explica la entrada de datos

“Nuestra importación comprueba los encabezados, las fechas y los valores de cada
fila antes de guardarla. El ejemplo incluye un Monitor con cantidad cero, que
descartamos indicando su fila original. Calculamos el hash del archivo y lo
combinamos con el número de fila para evitar duplicar una misma importación.”

Mostramos el CSV, ejecutamos `main.py` y señalamos las tres ventas nuevas y la
incidencia. Repetimos el mismo comando para comprobar que inserta cero ventas.

### Ricardo explica los cálculos

“Obtenemos los resultados mediante consultas SQL. Relacionamos las tablas con
JOIN y usamos SUM, COUNT, AVG y GROUP BY para calcular las métricas. En el ejemplo
obtenemos 15 unidades, total 313.20 y promedio por registro 104.40. Las pruebas
comprueban también la base vacía, los empates y las restricciones relacionales.”

Mostramos la consulta en pgAdmin y los totales. Aclaramos que el resumen abarca
todas las ventas de la base y que cada registro corresponde a un producto.

### Melissa presenta los resultados y el cierre

“El reporte reúne las métricas generales, las categorías, los productos y las
incidencias de la importación actual. Podemos regenerarlo desde PostgreSQL sin
leer otro CSV. Con esta entrega reunimos validación, persistencia y consultas
en un proceso reproducible, documentado y comprobado con pruebas.”

Abrimos `reporte_final.txt`, ejecutamos `--solo-reporte` y mostramos el nuevo
archivo. Cerramos con los resultados de las pruebas y los enlaces del trabajo
del equipo en GitHub.

### Evidencias para mostrar

- CSV de ejemplo con la fila inválida identificada.
- Primera ejecución con tres ventas nuevas y segunda con cero.
- Consulta en pgAdmin y reporte con los totales correctos.
- Reporte generado sin una nueva importación.
- Resultado de las pruebas y enlaces a los commits y pull requests.

No incluimos contraseñas en las capturas. La guía complementaria de preguntas
está en [guía de defensa](docs/guia_defensa.md).

## Problemas frecuentes

| Situación | Cómo la resolvemos |
| --- | --- |
| `$env:` produce un error de sintaxis | Entramos a PowerShell; esos comandos no funcionan en CMD. |
| No se puede conectar | Revisamos el servidor, puerto, base, usuario y contraseña de esta sesión. |
| La contraseña fue eliminada | Repetimos el bloque de Read-Host y PGPASSWORD antes de continuar. |
| Windows bloquea la biblioteca de Psycopg | Usamos PSYCOPG_IMPL=python y la ruta de PostgreSQL indicada arriba. |
| Faltan tablas | Ejecutamos `postgres.py inicializar` en la base configurada. |
| El total supera 313.20 | La base tiene otros lotes; usamos otra base vacía para la demostración. |
| No aparece la tabla en pgAdmin | Actualizamos Tables y comprobamos que seleccionamos la base correcta. |

**Solo al terminar todas las ejecuciones**, retiramos la contraseña de la sesión:

```powershell
Remove-Item Env:PGPASSWORD
```

## Alcance

Esta entrega funciona por consola y no incluye una interfaz web, usuarios de
negocio ni comprobantes con varios detalles. Los datos de demostración son
ficticios. Las incidencias corresponden a la ejecución actual y el control de
duplicados aplica al mismo archivo y fila, no a ventas similares en otros lotes.
