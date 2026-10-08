# Integración PostgreSQL de Sergio

Esta rama incluye el esquema, conexión Psycopg 3 y persistencia transaccional.
`postgres.py` permite demostrar esta parte sin esperar la integración de los
módulos de los compañeros. `main.py` conserva por ahora su flujo CSV original.

## Preparación local

Requisitos: Python 3.10 o superior, PostgreSQL activo y acceso con un usuario
administrador para crear el usuario y la base. Se probó con PostgreSQL 18.

Desde psql conectado a la base `postgres`, ejecutar una vez:

```sql
CREATE ROLE reportes_app LOGIN;
\password reportes_app
CREATE DATABASE reportes_ventas OWNER reportes_app;
```

`\password` solicita la contraseña sin escribirla en el script. Cada integrante
debe usar su propia base local. La base de pruebas debe estar separada.

En PowerShell, desde la raíz del repositorio:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:PGHOST = 'localhost'
$env:PGPORT = '5432'
$env:PGDATABASE = 'reportes_ventas'
$env:PGUSER = 'reportes_app'
$clave = Read-Host 'Contraseña de PostgreSQL' -AsSecureString
$env:PGPASSWORD = [System.Net.NetworkCredential]::new('', $clave).Password
.\.venv\Scripts\python.exe postgres.py conexion
.\.venv\Scripts\python.exe postgres.py inicializar
.\.venv\Scripts\python.exe postgres.py demo
.\.venv\Scripts\python.exe postgres.py listar
Remove-Item Env:PGPASSWORD
```

La demo inserta 3 ventas, 15 unidades y un total de 313.20 en una base vacía.
Al repetirla inserta 0 ventas nuevas. `inicializar` crea tablas e índices,
no crea el servidor, rol o base ni modifica esquemas antiguos incompatibles.

Si Windows bloquea la DLL del paquete binario, Psycopg también puede utilizar
su implementación Python con la biblioteca del PostgreSQL instalado. Ajusta
la versión de la ruta según tu instalación, antes de ejecutar los comandos:

```powershell
$env:PATH = 'C:\Program Files\PostgreSQL\18\bin;' + $env:PATH
$env:PSYCOPG_IMPL = 'python'
```

## Modelo y restricciones

`categorias (1) -> (N) productos (1) -> (N) ventas`.

- Claves primarias generadas por PostgreSQL y claves foráneas obligatorias.
- Nombre de categoría único y producto único dentro de una categoría.
- `DATE` para fechas; `NUMERIC(12,2)` para dinero y `Decimal` en Python.
- Cantidad positiva; precio no negativo y finito. PostgreSQL también rechaza NaN.
- No se borran categorías o productos con registros dependientes.
- El hash SHA-256 del lote y la fila original forman una identidad única.
- Nombres se limpian de espacios exteriores; las mayúsculas se conservan.

## Contrato para integrar las otras partes

Gabriela debe entregar una lista de diccionarios con:

```python
{
    "fecha": "2026-08-01",  # También admite datetime.date
    "producto": "Teclado",
    "categoria": "Tecnología",
    "cantidad": 2,
    "precio_unitario": Decimal("85.50"),
    "fila_origen": 2,  # Número real en el CSV; NO renumerar al descartar filas
}
```

Calcular `sha256(contenido_original_del_csv).hexdigest()` y llamar:

```python
from src.database import conectar
from src.repositorio import guardar_ventas, consultar_ventas

with conectar() as conexion:
    nuevas = guardar_ventas(conexion, ventas_validas, lote_hash)
    ventas_guardadas = consultar_ventas(conexion)
```

`guardar_ventas` devuelve el número de nuevas ventas. Si falla cualquier fila,
revierte también categorías y productos creados dentro de ese lote. La validación
de encabezados y el registro de filas inválidas corresponden a Gabriela.
La validación del repositorio protege la persistencia incluso con otros clientes.

`consultar_ventas` retorna una lista de diccionarios con fecha de tipo `date`,
precio y total de tipo `Decimal`, nombres, cantidad e identidad del lote.
Ricardo puede usar ese contrato y agregar sus consultas de métricas. El procesador
actual usa un acumulador float, por lo que deberá adaptarse a Decimal antes de
integrarlo. Melissa recibe el resumen resultante y adapta el reporte y README.

Los parámetros SQL se envían aparte del texto. Cada lote se guarda en una
transacción. Reimportar el mismo archivo no duplica filas; un archivo modificado
es otro lote. No se deduplican ventas coincidentes entre archivos distintos.

## Pruebas

Crear una base vacía de pruebas propiedad del usuario de prueba y configurar
las variables PG* para ella; además, habilitar explícitamente la suite:

```powershell
$env:PGDATABASE = 'reportes_ventas_test'
$env:POSTGRES_TEST_DATABASE = 'reportes_ventas_test'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

La suite crea un esquema temporal único dentro de la base indicada y lo elimina
al finalizar. Nunca usa ni vacía las tablas públicas. Verifica persistencia,
reimportación, rollback, restricciones relacionales y precisión monetaria.
