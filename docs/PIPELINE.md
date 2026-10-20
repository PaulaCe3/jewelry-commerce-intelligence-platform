# Normalización estructural v1

Usa Python >=3.11 y solo biblioteca estándar. No requiere instalación ni acceso a Internet. Para un clon público sin dataset, ejecutar desde la raíz:

```powershell
python -B tests/run_suite.py --unit-only
```

Esta selección ejecuta 29 pruebas unitarias con fixtures temporales; no sustituye las 39 pruebas de aceptación integral históricas. Los datos y el baseline no se distribuyen. Los comandos siguientes requieren el archivo auditado y las salidas oficiales disponibles localmente, con derechos de acceso/uso verificados; no funcionan sobre un clon público vacío de datos:

```powershell
python -B tests/run_suite.py
python -B tools/benchmark_normalization.py --runs 3
# Solo para una salida nueva, fuera de la validación temporal:
python -B src/normalize_jewelry.py --check-audit --output-dir data/processed/normalization-v1-new
```

Si `python` no está en PATH, sustituirlo por la ruta de un intérprete disponible. En la ejecución inicial se usó el Python ya incluido en el entorno de auditoría, sin instalar herramientas.

El destino debe ser un subdirectorio nuevo de data/processed. Si existe, el comando falla sin sobrescribirlo. Para repetir, usar otro nombre, por ejemplo `data/processed/normalization-v1-repeat`. Se conservan las exclusiones de Git de datos originales y derivados. No publicar estos archivos.

## Contrato y decisiones

La autorización de este pipeline amplía el alcance inicial registrado en AGENTS.md. La evidencia utilizada es la revisión de esquema en DATA_AUDIT.md y DATA_SOURCES.md: las posiciones omitidas siguen siendo ambiguas, por lo que no se implementa alineación para filas de 11 campos. Alternativa descartada: insertar dos vacíos intermedios sin saber sus posiciones. Tampoco se asignan nombres comerciales a las posiciones largas.

`records.jsonl`: un objeto JSON por línea física no vacía del CSV. Cada ocurrencia, incluidas las repetidas, se conserva en orden:

- `row_id`: SHA-256 del original seguido de `:` y número de línea física, desde 1. Es único por ocurrencia para este archivo y estable entre ejecuciones.
- `source_sha256`, `source_line`: trazabilidad al contenido original y su línea.
- `original_field_count`: anchura parseada; null si el CSV de esa línea no es parseable.
- `original_fields`: lista de cadenas en orden original, incluidos vacíos; null si falla el parseo. Sin trim, casting, imputación ni interpretación de importes, cantidad, fecha o IDs.
- `positional_fields_13`: claves técnicas `field_01` a `field_13` para filas de 13 campos, en identidad posicional. Null para cualquier otra anchura; no contiene nombres semánticos.
- `validation_status`: `structural_13_semantics_unverified`, `pending_schema_11`, `invalid_field_count` o `invalid_csv`. Validación estructural no significa validez de negocio. Todos siguen pendientes de validación semántica.
- `raw_text` y `line_ending`: texto original de la línea y terminador LF/CRLF o vacío; permiten reconstrucción UTF-8 sin perder la forma escrita del CSV.

La línea vacía inicial documentada no es uno de los 95.911 registros. Se conserva en `quality.json` mediante número de línea y terminador. Otras líneas vacías se registran igual; líneas con espacios o campos vacíos delimitados se conservan como registros.

`quality.json`: marcador de ejecución completa y reporte agregado: conteos, anchuras, estados, líneas vacías, pendientes, duplicados, hashes del original antes/después y de lo leído, y hash de records.jsonl. Duplicado exacto significa igualdad de `raw_text` excluyendo únicamente el terminador. No se elimina ni colapsa ninguna ocurrencia; los IDs técnicos distinguen duplicados.

Con `--check-audit` se exigen SHA-256 documentado, 95.911 registros, distribución 90.559/5.352 y 2.589 excedentes. Sin esa opción el CLI procesa el archivo local sin exigir esos valores, pero conserva la misma política; no implica aprobación de un archivo diferente.

## Reproducción y fallos

No hay timestamps de ejecución ni rutas del destino dentro de los resultados. Con el mismo contenido fuente y versión del pipeline, records.jsonl y quality.json deben ser idénticos byte a byte entre directorios. Las pruebas reales verifican dos ejecuciones del módulo y dos del CLI, además de comparar todos los bytes del CLI contra el baseline oficial. Si el dataset real no existe, la integración falla: ya no se omite. Los fixtures unitarios mínimos no representan resultados de negocio.

La lectura es secuencial; el contador de textos distintos para duplicados consume memoria proporcional a la cantidad y longitud de líneas únicas. No se carga un DataFrame; no es una implementación de memoria constante para datasets mucho mayores.

El contrato es una línea física por registro, documentado para el original. Los formatos admitidos y rechazados se detallan abajo. No se reconstruye CSV multilínea ni se elimina un BOM silenciosamente.

Si ocurre un error de lectura, escritura, cambio del original o incumplimiento de aceptación, el proceso termina con código no cero. Puede quedar un directorio parcial; **sin quality.json completo no se considera una salida válida**. No se borra ni reusa automáticamente: inspeccionarlo y elegir un destino nuevo. El reporte ahora se escribe primero en `.quality.json.partial`, se vacía con flush/fsync y se publica por enlace duro exclusivo como quality.json después de cerrar el archivo. Un fallo de escritura, flush, fsync o publicación no deja el marcador definitivo creado por el pipeline. La publicación falla si quality.json ya existe. Si solo falla la eliminación del alias temporal después de publicar, el resultado completo sigue siendo válido y puede quedar ese alias adicional. No se promete recuperación transaccional frente a corte de energía.

El pipeline abre el original exclusivamente para lectura. Verifica SHA-256 antes, durante y después; esto comprueba integridad durante su ejecución, no protege contra otros procesos que modifiquen el archivo posteriormente. No resuelve diccionario, licencia, moneda, unidad comercial ni causa de repeticiones.

## Formatos y límites explícitos tras el cierre de QA

| Caso | Política |
|---|---|
| UTF-8 sin BOM; LF/CRLF, mezclados o sin terminador final | Admitido; texto y terminador conservados |
| Comas entre campos; comas entrecomilladas y comillas escapadas | Admitido si el campo se cierra en la misma línea |
| 13 campos / 11 campos | Posiciones técnicas / pendiente sin alinear |
| Otras anchuras | Registro conservado con invalid_field_count; no es una ejecución libre de anomalías |
| Error de comillas cerradas, como texto tras una comilla de cierre | Conservado como raw_text con invalid_csv, sin campos parseados |
| Comillas sin cerrar o registro multilínea | Rechazo de la ejecución, sin quality.json; no se procesa una continuación como si fuese un registro válido |
| UTF-8 con BOM, codificación inválida, CR aislado o CR dentro del campo | Rechazo, sin sustitución ni corrección automática |
| Campo de hasta 131.072 caracteres | Admitido, sujeto a la estructura CSV |
| Campo de 131.073 caracteres o más | Rechazo explícito; no se confunde el límite del parser con una fila estructural válida |

Las entradas rechazadas no se modifican. El cambio endurece el tratamiento de formatos ajenos al archivo auditado; no cambia el esquema JSON, la versión de contrato 1 ni los bytes de las salidas oficiales. El parser ajusta y restaura el límite global de csv durante cada lectura: usar un proceso por ejecución, sin llamadas concurrentes en threads. No se impone un límite artificial de tamaño total; consumo de memoria y espacio sigue creciendo con los datos.

## Suite completa, pruebas parciales y oráculo independiente

```powershell
python -B tests/run_suite.py                     # Aceptación integral: exige dataset y baseline
python -B tests/run_suite.py --unit-only         # Pruebas parciales, NO aprobación integral
python -B tests/run_suite.py --integration-only  # CLI e integración real; exige dataset y baseline
```

También se admite `python -B -m unittest discover -s tests -v`. El runner explícito rechaza cualquier omisión, además de fallos/errores. Clasificación: NormalizationTests y QAUnitTests son unitarias; CLIIntegrationTests ejecuta subprocess sobre una copia temporal aislada del proyecto y contiene integración con el dataset real; LocalDatasetIntegrationTests exige el original. La copia de código para CLI cambia únicamente la raíz de ejecución mediante su ubicación: no modifica el código oficial. Las ejecuciones de subprocess usan `-X utf8` para capturar correctamente mensajes en Windows. Códigos verificados: 0 éxito/ayuda, 1 fallo operativo o de aceptación, 2 argumentos/ruta no permitidos.

`tests/independent_checks.py` no importa funciones ni constantes del pipeline. Reconstruye desde el original todos los campos y metadatos de cada registro, incluyendo tipos, posiciones, líneas e IDs; calcula por su cuenta todos los conteos, distribuciones y hashes de quality.json. Compara el conjunto completo de claves y valores del reporte, no solo una selección. Los mensajes de error no incluyen registros o identificadores. También verifica el original al terminar.

Se prueban mutaciones de todos los campos del reporte y todos los campos de un registro; estas últimas se detectan incluso recalculando el hash de records.jsonl. Se prueban filas faltantes, extras, reordenadas y deduplicadas. Las mutaciones ocurren exclusivamente en fixtures temporales y no quedan en código o datos oficiales. Sigue siendo un oráculo implementado con la misma biblioteca CSV estándar: no constituye verificación formal de esa biblioteca ni una segunda implementación de CSV.

## Fallos simulados y aceptación

Se simulan permisos de lectura y creación denegados; escrituras parciales con ENOSPC; error al cerrar records; flush/fsync del reporte y publicación fallidos; y colisión al publicar el marcador. Se verifican excepción/código no cero, ausencia de marcador propio de éxito, original intacto y rechazo de reutilización de un directorio parcial. La modificación concurrente se comprueba también alterando un fixture durante la ejecución; nunca se provoca sobre el original. No se llenó el disco ni se cambiaron ACL reales.

Criterios de aceptación de esta revisión: suite completa sin fallos, errores u omisiones; 95.911 registros, 90.559/5.352 campos, 2.589 excedentes conservados; igualdad de todos los registros y metadatos con el original; hashes coincidentes; igualdad byte a byte con oficiales; CLI validado; fallos simulados sin publicar éxito; recursos medidos y temporales eliminados. `--unit-only` no satisface estos criterios por sí solo.

## Medición reproducible

`tools/benchmark_normalization.py --runs 3` inicia un proceso nuevo por corrida y usa TemporaryDirectory fuera de las salidas oficiales. Mide con perf_counter la llamada normalize completa, incluidos hashes y escritura del reporte, pero excluye arranque del intérprete y verificación posterior. Obtiene el máximo de memoria residente del proceso: PeakWorkingSetSize mediante GetProcessMemoryInfo en Windows (ru_maxrss en otros sistemas). Incluye runtime/importaciones y asignaciones nativas; no es memoria neta exclusiva del algoritmo ni memoria reservada o paginada. El verificador se ejecuta después en el padre, fuera del intervalo medido.

Cada corrida se valida independientemente y sus hashes se contrastan con oficiales. El script verifica hashes protegidos antes/después y elimina solo su árbol temporal. No se vacían cachés de disco; tiempos pueden reflejar caché caliente, sincronización de archivos, antivirus y carga del equipo. No se inventó un SLA ni un umbral de memoria. Resultados de esta máquina en STATUS.md.

Limitaciones residuales: un filesystem sin enlaces duros falla de forma cerrada al publicar; no se garantiza durabilidad de records.jsonl ni directorios ante corte de energía (no se fuerza fsync de todo el dataset/directorio); no se probaron fallos físicos ni ACL reales; no hay soporte concurrente en threads; memoria proporcional a cardinalidad y textos distintos. Los directorios parciales se conservan para revisión. Estos límites no alteran el original ni habilitan indicadores de negocio.
