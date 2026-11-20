# Generador de reportes de ventas

## Nuestro proyecto

Desarrollamos una aplicación de consola en Python para automatizar el procesamiento
de ventas. Para la segunda entrega integramos una base de datos PostgreSQL: leemos
un CSV, validamos cada registro, almacenamos las ventas válidas, consultamos las
métricas mediante SQL y generamos un reporte de texto.

Con esta integración podemos conservar las ventas después de cerrar el programa
y generar otro reporte sin volver a importar el archivo.

**Flujo principal:** CSV → validación → PostgreSQL → resumen SQL → reporte.

La preparación para la tercera entrega y los pasos de seguimiento de incidentes,
CI, empaquetado y nube están en [docs/avance_3.md](docs/avance_3.md). La guía
distingue el alcance que figura en el sílabo de las evidencias sugeridas para
aplicar los temas al proyecto.

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

## Inicio local sin escribir la contraseña

La configuración local se guarda una sola vez en `.env`, un archivo ignorado
por Git. La interfaz y `main.py` cargan esos valores automáticamente; no hace
falta volver a escribir ni copiar la contraseña en PowerShell o VS Code.

Para iniciar PostgreSQL de Docker y abrir el menú gráfico con un solo comando:

```powershell
.\scripts\iniciar_local.ps1
```

Docker Desktop debe estar abierto. El script espera a que PostgreSQL esté listo
antes de abrir la aplicación. Para iniciar solo la base:

```powershell
.\scripts\iniciar_local.ps1 -SoloBase
```

El menú gráfico y los comandos de consola conectan usando `PGHOST`, `PGPORT`,
`PGDATABASE`, `PGUSER` y `PGPASSWORD` definidos en `.env`. Para el proyecto
Docker local, el puerto publicado es `5434`.

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

Este archivo pequeño se conserva para las pruebas automatizadas y para repetir
el total de ejemplo. El menú gráfico preselecciona
`data/examples/ventas_ejemplo_ampliado.csv`, con 25 ventas válidas y una fila
inválida repartidas en cinco categorías. Al importarlo, PostgreSQL guarda un
lote nuevo porque el archivo tiene otro contenido; el reporte suma también las
ventas que ya existan en la base. Para ver solo el lote ampliado, utiliza una
base de demostración vacía; no borres las ventas existentes.

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

## Demostración en contenedores

Con Docker Desktop y Compose disponibles, ejecutamos desde la raíz del proyecto:

```powershell
docker compose up --build
```

El comando inicia un PostgreSQL local aislado, ejecuta la importación y deja el
reporte en `data/reports/reporte_final.txt`. Para volver a generar el reporte
con los datos persistidos, ejecutamos:

```powershell
docker compose run --rm app --solo-reporte
```

El volumen de la base se conserva al detener Compose. Para borrar únicamente
esta base local de demostración y empezar de cero, ejecutamos
`docker compose down --volumes`. No usamos el password de ejemplo fuera del
entorno local. PostgreSQL queda accesible solo desde esta computadora en el
puerto `5434`, para pgAdmin o para ejecutar la suite contra otra base aislada.

Al publicar un release en GitHub, `publish-image.yml` publica la imagen en GHCR.
La imagen es un artefacto de contenedor listo para ejecutarse; no convierte el
programa de consola en un servicio web.

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

La suite contiene **42 pruebas**, incluidas las de PostgreSQL real y el recorrido
completo. El detalle histórico está en el
[registro de verificación](docs/verificacion_entrega.md).

Para repetirlas localmente, iniciamos PostgreSQL y ejecutamos el preparador de
pruebas. Lee la conexión de `.env`, crea `reportes_pruebas` si todavía no existe
y ejecuta toda la suite dentro de esa base:

```powershell
\.venv\Scripts\python.exe scripts\run_postgres_tests.py
```

Las pruebas usan esquemas temporales que eliminan al terminar. No modifican la
base `reportes_presentacion` ni sus ventas. Si ejecutamos directamente
`unittest discover`, las pruebas de PostgreSQL se omiten salvo que se configure
explícitamente la base aislada mediante `PGDATABASE` y `POSTGRES_TEST_DATABASE`.

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

## Menú gráfico de escritorio

También podemos abrir el panel y la base local con:

```powershell
.\scripts\iniciar_local.ps1
```

El menú toma la conexión desde `.env`; el campo de contraseña aparece rellenado
y oculto. Pulsa **Probar conexión** y, si hace falta, **Crear tablas**.
El CSV preseleccionado tiene 25 ventas válidas de cinco categorías y una fila
inválida para mostrar la validación. Puedes seleccionar otro CSV. Luego elige
el destino TXT y utiliza **Importar CSV + TXT y QR**
o **Solo reporte + QR**. Este último consulta las ventas persistidas sin importar.
El resultado y las incidencias aparecen en la ventana. **Abrir TXT** y **Abrir QR**
muestran los últimos archivos generados desde el panel. El QR contiene las
métricas en texto, no una dirección web. Se pide confirmación antes de reemplazar
archivos existentes. El panel utiliza Tkinter, incluido habitualmente con Python
para Windows, y las dependencias de requirements.txt.

### Exportar el reporte a PDF

En el menú gráfico, genera primero un reporte y pulsa **Exportar a PDF**.
Selecciona el nombre y la ubicación del PDF; al terminar puedes abrirlo desde
el diálogo de confirmación. La exportación utiliza el último TXT generado desde
el menú, conserva todas sus secciones y agrega páginas cuando es necesario.
No requiere consultar nuevamente PostgreSQL. Instala las dependencias con
`.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.

### Gráfico por categoría

Después de generar un reporte desde el menú, pulsa **Gráfico por categoría**.
Se abre una ventana con barras ordenadas por facturación e importes con dos
decimales. El gráfico usa el resumen del último reporte generado, sin volver a
consultar PostgreSQL. Si hay muchas categorías, utiliza la barra de desplazamiento.
Una base vacía muestra un mensaje sin ventas; los importes cero se muestran sin
barra. Esta funcionalidad utiliza Tkinter y no añade dependencias.


### Datos ampliados para el gráfico

`data/examples/ventas_graficos.csv` contiene datos ficticios: 80 ventas válidas,
8 categorías, 24 productos y fechas del 1 al 19 de octubre de 2026.
El lote suma 360 unidades y una facturación de 15420.50.
En el menú, selecciona ese CSV, pulsa **Importar CSV + TXT y QR** y después
**Gráfico por categoría**. El resumen abarca toda la base: si ya estaba el lote
original, se suman sus 3 ventas y 313.20. Volver a importar el mismo archivo
sin modificarlo no agrega ventas duplicadas. Este ejemplo amplía las barras
del gráfico existente; no añade tipos de gráficos nuevos.
