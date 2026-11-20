# Verificación local de 80 pruebas

Fecha: 20 de noviembre de 2026.

Se ejecutó la suite completa con el entorno virtual del proyecto y PostgreSQL
18 local en Docker, usando la base separada `reportes_pruebas`. Cada prueba de
persistencia utiliza un esquema temporal que se elimina al terminar.

```powershell
.\.venv\Scripts\python.exe scripts\run_postgres_tests.py
```

Resultado observado:

```text
Ran 80 tests in 2.168s
OK
RESULTADO FINAL: 80 pruebas, 80 aprobadas, 0 fallidas, 0 omitidas.
```

Se conservaron las 42 pruebas originales y se añadieron 38 escenarios:

| Área adicional | Casos | Ejemplos |
| --- | ---: | --- |
| CSV inválidos | 12 | Fechas, signos, dígitos Unicode, notación científica y caracteres nulos. |
| CSV válidos | 8 | Año bisiesto, límites de longitud, cantidad y precio, comillas y comas. |
| Gráfico | 6 | Precisión decimal, cero, categoría única, 100 categorías y entrada inmutable. |
| PDF | 6 | Base vacía, destinos anidados, caracteres XML, precio cero, paginación y fuente inexistente. |
| PostgreSQL real | 6 | Distintos lotes, precio histórico, lote vacío y restricciones SQL. |

Los casos CSV parametrizados se registran como pruebas independientes con
nombres descriptivos mediante unittest. No se duplican clases de la suite
original. Las pruebas PDF validan generación y estructura básica; no sustituyen
la revisión visual del documento. Las pruebas del gráfico comprueban sus datos,
no la interacción con la ventana.

Este resultado corresponde a una ejecución local; no acredita una ejecución
de GitHub Actions. El workflow CI descubrirá también el nuevo archivo cuando
estos cambios se publiquen y se ejecute el workflow correspondiente.

## Ampliación de rentabilidad

Se extendieron escenarios de la suite conservando 80 pruebas principales:
validación de costo opcional mediante subcasos, precisión de utilidad y margen,
descuentos de 0 a 100%, descuentos inválidos, costo histórico por venta,
exclusión de costos desconocidos, costo negativo rechazado por SQL y PDF con
rentabilidad. La ejecución posterior terminó con 80 aprobadas, 0 fallidas y
0 omitidas (2.095 segundos).

Una comprobación adicional en un esquema temporal reprodujo una tabla de
ventas anterior sin costo: la migración preservó su registro con costo NULL.
Se importó el ejemplo de rentabilidad y se comprobó: ingresos con costo 6240,
costos 4772 y utilidad bruta 1468. La reimportación insertó cero ventas nuevas.
Se generó y revisó visualmente el PDF de dos páginas. Las ventanas principal
y de rentabilidad se construyeron mediante Tkinter sin errores; esto no
equivale a una prueba automatizada de todos los controles de la interfaz.

## Proyección de recuperación de inversión

La suite se mantiene en 80 pruebas principales y amplía subcasos de proyección:
recuperación exacta y fraccionaria por meses completos, flujo nulo y negativo,
inversión cero, recuperación fuera del horizonte, precisión de centavos,
sensibilidades de entradas, importes inválidos y horizonte fuera de rango.
También comprueba exportación PDF y que no se modifiquen los datos proyectados.
Resultado: 80 aprobadas, 0 fallidas y 0 omitidas (2.186 segundos).

Se construyó el panel mediante Tkinter y se recorrieron sus tres pestañas,
el cambio de alcance y la carga del ejemplo de negocio. Se verificó la
exportación de un horizonte de 120 meses y se revisó visualmente el PDF de
dos páginas del ejemplo de software (inversión 3000, ahorro 550, pagos 50).
Los escenarios recuperan la inversión al cierre de los meses 8, 6 y 5,
respectivamente. Son supuestos ficticios y no resultados reales del cliente.

## Gráficos con importes grandes

Se verificó visualmente la interfaz con una inversión ficticia de 100000,
cobros mensuales de 30000, pagos de productos de 15000 y otros pagos de 5000:
recuperación base al mes 10 y excedente de 20000 al finalizar el mes 12.
El gráfico muestra ejes en miles/millones, regiones de saldo positivo y
negativo, marcador de recuperación y saldos finales por escenario. Cuando
el cero está muy lejos de los saldos, la escala enfoca la variación y avisa
que el cero queda fuera de vista. Al mover el cursor se muestran los importes
exactos por mes. Se aceptan importes como 100k o 1.5k.

Las pruebas de regresión comprueban que la escala incluya los valores de
entrada, incluso con series constantes, importes de centavos y saldos grandes.
Última ejecución de esta revisión: 80 aprobadas, 0 fallidas y 0 omitidas
(2.369 segundos). El resultado de GitHub Actions debe acreditarse por separado.
