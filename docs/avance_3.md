# Preparación del Avance 3

## Qué pide el material del curso

El sílabo ubica el Avance de Proyecto Final 3 en la semana 15, después de la
sesión de plataformas en la nube. El contenido de esa evaluación es **plataformas
en la nube**. Contenedores y despliegue de aplicaciones aparecen en las semanas
16 y 17, después del Avance 3. El PDF recibido es el sílabo del curso, no una
rúbrica detallada del APF3; por eso este plan prepara una demostración aplicable
al proyecto sin atribuirle criterios de calificación que no figuran allí.

Las sesiones 12 a 14 dan contexto práctico que conviene mostrar como parte de la
solución: seguimiento de incidentes, integración continua y entrega continua.
Las diapositivas proponen aplicar esos temas al proyecto. Este repositorio ya
registra importación, persistencia PostgreSQL, consultas y generación de reportes.

## Aplicación al generador de reportes

El generador es una aplicación por consola: recibe un CSV, persiste ventas en
PostgreSQL y produce un archivo de texto. La opción de nube más directa consiste
en conservar el programa como proceso por lotes y conectar PostgreSQL a un
servicio administrado (DBaaS). Así se aprovecha el diseño existente y no se
simula que pgAdmin sea una aplicación alojada.

```text
CSV de entrada → aplicación Python → PostgreSQL administrado (DBaaS)
                         │
                         └── reporte de texto

GitHub Issues → GitHub Actions (CI: pruebas con PostgreSQL temporal)
              → publicación versionada de imagen en GHCR al publicar un release
```

## Qué queda preparado en este checkout

- `.github/ISSUE_TEMPLATE/incidente.yml`: captura resumen, pasos, resultados,
  severidad, entorno y evidencia segura para registrar incidentes.
- `.github/workflows/ci.yml`: ejecuta la suite con Python 3.12 y un PostgreSQL
  aislado al hacer push o abrir un pull request a `main`.
- `Dockerfile` y `compose.yaml`: empaquetan el programa y permiten una
  demostración local reproducible con PostgreSQL en contenedor.
- `.github/workflows/publish-image.yml`: al publicar un release, vuelve a
  ejecutar la suite y, si pasa, construye la imagen y la publica en GitHub
  Container Registry (GHCR) con la etiqueta del release y `latest`.

La publicación del contenedor demuestra entrega de un artefacto a un registro
en la nube. No significa que el proceso de consola quede ejecutándose como un
servicio web ni que ya exista una base administrada conectada.

## Beneficios y limitaciones que explicar

**Beneficios:** PostgreSQL administrado evita instalar y parchear el motor en
una computadora del equipo; los datos persisten aunque termine el proceso;
GitHub Actions ejecuta la misma suite en una máquina limpia; el registro conserva
una imagen asociada a una versión publicada.

**Limitaciones:** se requiere internet y credenciales del proveedor; los planes
gratuitos pueden suspenderse o tener límites; deben configurarse copias de
seguridad, accesos de red, costos y región; una imagen publicada no constituye
por sí sola un despliegue de aplicación; este programa todavía genera el reporte
en el entorno donde se invoca.

## Evidencias para la presentación

1. Crear un incidente de demostración con datos ficticios y mostrar su estado,
   responsable y conversación en GitHub Issues.
2. Abrir un pull request y mostrar el resultado de la ejecución CI, incluida la
   conexión al PostgreSQL temporal.
3. Ejecutar la demostración con `docker compose up --build` y abrir el reporte
   generado en `data/reports/reporte_final.txt`.
4. Publicar un release de práctica solo cuando el equipo esté listo; mostrar el
   paquete resultante en GHCR. El workflow publica una imagen externa al
   repositorio cuando se publica un release.
5. Explicar la arquitectura DBaaS elegida, el beneficio observado y al menos
   una limitación real del servicio que se use.

## Pruebas locales ejecutadas

En este checkout, el 15 de noviembre de 2026, se usó Python 3.12.14 y un
PostgreSQL 18.6 temporal en Docker:

- Las **31 pruebas automatizadas pasaron**, incluidas las de persistencia,
  transacciones, restricciones y flujo completo. La base de pruebas fue
  `reportes_ventas_test`, separada de la base de demostración.
- `docker compose up --build` construyó la imagen e importó 3 ventas válidas;
  descartó la fila inválida 5 y generó el total esperado de 313.20.
- Al repetir la importación, insertó 0 ventas nuevas y conservó las 3 existentes.
- `--solo-reporte` volvió a generar el reporte desde la base sin importar otro
  CSV; conservó el total 313.20.
- También pasaron la validación de `docker compose config`, el parseo YAML de
  workflows/plantilla y la compilación sintáctica Python.

Estas comprobaciones fueron locales. No se publicó un release, no se ejecutó
el workflow alojado en GitHub ni se conectó un proveedor de base administrada.

No publicar credenciales, capturas con secretos ni datos de clientes. La clave
`demo-local-only` de `compose.yaml` es solo para la demostración local; no debe
reutilizarse en una plataforma externa.

## Pendientes antes de presentar

- Confirmar la rúbrica y el formato de entrega que indique el docente; no están
  incluidos en el PDF recibido.
- Elegir y probar una instancia PostgreSQL administrada que el equipo pueda
  usar. Configurar las variables `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER` y
  `PGPASSWORD` como secretos/variables del entorno que ejecute la aplicación.
- Acordar quién registra incidentes, revisa pull requests y presenta cada parte.
- Ejecutar los workflows alojados luego de publicar los cambios en GitHub y
  conectar/probar una base administrada. La preparación local aún no se ha
  publicado ni desplegado a una cuenta cloud.
