# Estado del Proyecto 01

## Estado vigente — 2026-10-21

**DATA ENGINEERING v1 AURELIA: CERRADO Y ACEPTADO FUNCIONALMENTE.** Se importó `analytics_orders.csv` en Power BI Desktop y el usuario confirmó los tres indicadores sintéticos: 920 USD capturados, 14 USD reembolsados y 906 USD netos. Ver [acta de aceptación](DE_ACCEPTANCE.md). La etapa siguiente es Data Analytics / Business Intelligence. Los párrafos históricos siguientes registran el estado anterior al cierre.

Implementadas orquestación local sobre Aurelia v2 y seis vistas/CSV con contrato. Paquete completo publicado localmente tras aceptación independiente desde fuentes. Repetición reconstruye y compara hashes sin sobrescribir. Código y pruebas históricos intactos. [Comandos y garantías](AURELIA_PIPELINE.md).

18 pruebas nuevas en 7.063 s: cero fallos, errores u omisiones. CLI persistido: success, unchanged y verify PASSED; 30 pedidos, 70 artículos, 3 productos, 35 pagos, 5 devoluciones y 7 reembolsos (seed 42), exclusivamente sintéticos.

Estado anterior a la aceptación: la importación real de Power BI estaba pendiente. **Actualización:** aceptación funcional realizada y pipeline publicado en el commit `90986ffe1f31ac903c647c5096bcdad40391af7b`. REES46 sigue separado y con semántica abierta; persiste la limitación de acceso al hash de su base SQLite retenida, no verificado.


### Regresiones y protección ejecutadas — 2026-10-21

| Suite | Pruebas | Tiempo observado | Fallos / errores / omisiones |
|---|---:|---:|---|
| tests/run_aurelia_pipeline_suite.py | 18 | 7.063 s | 0 / 0 / 0 |
| tests/run_aurelia_v2_suite.py | 24 | 6.847 s | 0 / 0 / 0 |
| tests/run_aurelia_suite.py | 23 | 4.617 s | 0 / 0 / 0 |
| tests/run_suite.py (completa, datos locales) | 39 | 29.910 s | 0 / 0 / 0 |
| tests/run_evidence_suite.py (completa, datos locales) | 27 | 63.007 s | 0 / 0 / 0 |

Total 131 pruebas, códigos 0. Comandos: `python -B` seguido de cada ruta de la tabla. Tiempos de esta máquina, no SLA ni benchmark. Las integraciones REES46 usan datos/baseline privados y reconstrucciones temporales; no verifican el hash de la base SQLite retenida inaccesible.

Comparación contra HEAD: 22 archivos históricos versionados en src/tests/tools idénticos byte a byte. SHA-256 del original y ambas salidas oficiales coinciden con los hashes auditados: jewelry.csv 09d8a61644f66cbb9ad8c50f59180978a0995d121196faf25ef28083dd7b84a2; records.jsonl 5eef0df67a63c918b23a5d01627d6debfd88937c7f499e5b4bc25322bbff63e8; quality.json d58407f19d6f3727866ce2ec7674756da7a1a96624f0f5aac74e4c070fefe129.

Los 15 archivos del paquete local están excluidos mediante git check-ignore. git diff --check sin errores; enlaces relativos de los documentos cambiados resuelven; escaneo dirigido sin rutas personales, tokens reconocibles ni claves privadas. Consulta SQLite read-only confirmó (30, 92000, 1400, 90600, 3). Ninguna base o dataset incorporado a los cambios, sin commit/push ni configuración global modificada.

## Antecedente — 2026-10-20

Objetivo autorizado: segunda entrega funcional del Data Warehouse sintético Aurelia, devoluciones físicas y reembolsos financieros separados, sin romper contratos históricos. Empresa ficticia, datos originales PLATHEL; sin REES46 ni Olist en la simulación. Data Engineering sigue abierto.

Implementado aditivamente en src/aurelia/v2.py: manifiesto aurelia-synthetic-v2, generador con base/ v1 idéntica, ajustes trazables, validación de estados/fechas/FK y límites, hechos separados y vistas de conciliación. v2 reconstruye un snapshot nuevo; no migra bases v1 ni cambia tablas históricas. Pendientes reservan capacidad; completados afectan recibido/capturado; fallidos/rechazados no consumen acumulados. GOODWILL permite compensación sin recepción física bajo límites, sin asignación a productos. USD y centavos enteros, sin impuestos/envío/descuentos nuevos ni reconocimiento contable.

La normalización/evidencia REES46 y Aurelia v1 permanecen sin cambios en código, pruebas y contratos. Validación semántica REES46 abierta y NO GO para KPIs de esa fuente. Se conserva la limitación conocida de acceso al hash de la base REES46 persistida: no se afirma haberlo verificado.

Próximo paso: única evaluación funcional local siguiendo [AURELIA_DW_V2.md](AURELIA_DW_V2.md). Evolución posterior propuesta: ledger incremental con transiciones e idempotencia por evento; todavía no implementada. No commit/push ni publicación de artefactos bajo esta entrega. Resultados ejecutados al final; secciones siguientes son antecedentes fechados.

## Historial anterior (estados fechados)


Actualizado: 2026-10-19. Preparación pública del portfolio PLATHEL para PaulaCe3.

### Objetivo histórico al 2026-10-19: preparación previa a Git

Aplicar las correcciones de documentación, privacidad, derechos reservados y exclusiones autorizadas por el usuario. Destino previsto: repositorio público jewelry-commerce-intelligence-platform en la cuenta PaulaCe3. No se inicializó Git ni se crearon commits, remotos o repositorios; la publicación requiere una autorización posterior.

Estado técnico vigente: normalización estructural v1 aprobada con evidencia histórica de 39 pruebas; validación semántica abierta. GO CON CONDICIONES para revisión conceptual y NO GO para KPIs comerciales definitivos o modelo definitivo sin resolver bloqueos. La preparación pública no modifica esos estados.

Correcciones: README reescrito con capacidades y límites actuales, atribución a REES46 y ejecución sin datos; AGENTS actualizado sin referencias a otros proyectos; .gitignore reforzado; COPYRIGHT.md creado para materiales originales de PLATHEL, sin licencia open source ni atribución de derechos sobre REES46. Se sustituyeron rutas personales por comandos portables y se neutralizaron detalles locales de adquisición en la documentación, conservando hashes, conteos y procedencia verificable.

Pruebas ejecutadas en esta fase:

```powershell
python -B tests/run_suite.py --unit-only
```

- Proyecto original: 29 pruebas en 0.805 s; 0 fallos, errores u omisiones; código de salida 0.
- Copia temporal aislada de src/tests sin carpeta data: 29 pruebas en 0.687 s; 0 fallos, errores u omisiones; código 0. La copia y los fixtures temporales fueron eliminados.
- Ambas ejecuciones anunciaron UNIT ONLY - NO FULL APPROVAL. No se reejecutó ni se presenta como reejecutada la suite integral de 39 pruebas.

Verificaciones de preparación pública ejecutadas: escaneo por patrones de los 27 archivos candidatos sin secretos, credenciales, emails personales, rutas personales o identificadores reales detectados; la única cadena numérica de 19 dígitos en las pruebas corresponde al fixture sintético documentado. Se revisaron 18 enlaces internos y 15 referencias a scripts Python, todos con destino existente. Se comprobaron 37 casos de exclusión/inclusión, incluidos los cinco .gitkeep y ejemplos virtuales de datos, claves, logs y cachés; no se crearon archivos de esos ejemplos.

Los 27 candidatos son una proyección de las reglas actuales de .gitignore, no una lista de staging: Git sigue sin inicializar. Antes del primer commit se deberá confirmar la lista con Git real y configurar la identidad pública del autor, preferiblemente email noreply local al repositorio, sin alterar otros proyectos. Las exclusiones no sustituyen el escaneo y no protegen frente a un futuro git add forzado.

Se verificó igualdad SHA-256 antes/después de los 15 archivos protegidos en data/raw, data/processed, src y tests, incluidos marcadores y cachés preexistentes. El manifiesto agregado de rutas relativas con separador portable conserva SHA-256 0592acbe42d298f041838f553e0a9821c3374cbd77a0f3702ce7cdcfafe7ad37. El original y las dos salidas oficiales conservan los hashes históricos documentados más abajo. No se modificó el pipeline aprobado, sus pruebas ni los datos.

**Resultado: LISTO PARA INICIALIZAR GIT**, condicionado únicamente a recibir la autorización explícita para ese siguiente paso. No se ha publicado ni creado ningún repositorio. Riesgos residuales: escaneo por patrones no es garantía absoluta, derechos/licencia REES46 y semántica siguen abiertos, y la identidad de futuros commits aún debe seleccionarse. Ninguno habilita incluir datasets en la publicación. Solo se incluyen código propio, fixtures de prueba y documentación sin registros individuales.

Las secciones siguientes conservan la evidencia de fases anteriores. Las referencias a «esta fase documental» dentro de esos antecedentes corresponden a la elaboración del diccionario, no a una ejecución actual del pipeline.

### Antecedente: objetivo y resultado semántico

Construir diccionario verificable, evidencias semánticas, matriz de viabilidad y propuesta conceptual, según solicitud del usuario, sin tocar el pipeline cerrado. Aurelia Jewelry es ficticia; no se atribuyen datos REES46 a ella. **Documentos construidos; validación semántica parcial y abierta**, no aprobación de métricas comerciales.

### Avance de esta fase

- Creados docs/DATA_DICTIONARY.md (13 fichas con nombres técnicos, patrones, vacíos, cardinalidades, ejemplos enmascarados, reglas propuestas, confianza y evidencia), docs/SEMANTIC_VALIDATION.md (registro E01–E09/S01–S05, hipótesis y pendientes) y docs/ANALYTICS_FEASIBILITY.md (matriz de indicadores y modelo conceptual preliminar).
- Creado docs/semantic_profile.py como apoyo de reproducción: solo lectura, biblioteca estándar, salida de agregados sin IDs individuales. Ejecutado con Python preexistente y -B, código 0.
- Leídos los siete documentos de contexto solicitados; inspeccionados CSV completo y metadatos normalizados. Se verificaron 95.911 registros, 90.559/5.352 por anchura y 2.589 excedentes conservados. Ninguna fila corta fue alineada.
- Confirmados tipos observados y timestamp UTC literal; pedido, producto, usuario y atributos continúan inferidos. Cantidad real, código de posición 7, precio unitario frente a importe, moneda, estados, granularidad comercial e identidad personal siguen sin verificar.
- Evidencia nueva reproducible: 0 productos largos con variación del decimal de posición 8; 106 usuarios candidatos con ambos códigos f/m; 18 de 25 categorías ID con etiqueta no vacía y seis etiquetas asociadas a múltiples IDs. No se extraen conclusiones de ingresos o demografía de esos patrones.
- Filas cortas: 999 grupos de pedido compartidos con coincidencia fecha/usuario, 3.951 filas con usuario candidato visto entre largas, 0 productos compartidos. Las omisiones alternativas {5,6}, {5,7} o {6,7} siguen indistinguibles; no se adoptó ninguna.
- Investigación web primaria realizada 2026-10-19: REES46 accesible; Kaggle/ficha/API y rutas legacy no dieron documentación utilizable. Encabezado, moneda, licencia y número público de versión no recuperados. Los períodos de las dos páginas REES46 se contradicen. URLs y afirmaciones respaldadas en SEMANTIC_VALIDATION.md, no se usan encabezados de terceros.
- Actualizado DECISIONS.md con alcance documental y decisión conservadora; no se registran aprobaciones semánticas inexistentes.

### Verificaciones y pendientes de esta fase

Comando desde raíz (sustituir python por el intérprete preexistente disponible):

```powershell
python -B docs/semantic_profile.py
```

Recorrido completo y comparación SHA-256 de 15 archivos protegidos en data/raw, data/processed, src y tests: sin cambios. Hash del original y de ambas salidas oficiales idénticos a los de la evidencia QA conservada abajo. Manifiesto protegido de esta máquina: d3d3c600ab51320103cb7a3c146b0610f6f499f8ec093dd30ea5a579ce7dec67. No se instalaron herramientas, descargaron datos, tiparon/imputaron campos, eliminaron repetidos ni modificaron src/tests o datos. Las 39 pruebas que se citan debajo pertenecen al cierre previo: no se reejecutaron en esta fase documental.

Control documental final ejecutado, código 0: 13 fichas presentes; referencias relativas resuelven; registro E01–E09/S01–S05 presente; estados de viabilidad presentes; cero IDs de 19 dígitos sin enmascarar en los tres nuevos informes y ninguna URL firmada. Una segunda ejecución del perfil confirmó nuevamente 95.911 filas, 2.589 excedentes, cero cortas alineadas y el mismo manifiesto de 15 archivos. Las conclusiones se revisaron contra los agregados y sus referencias; estos controles documentales no sustituyen pruebas de semántica comercial ni recuperan el diccionario faltante.

**Recomendación: GO CON CONDICIONES para revisión conceptual exploratoria; NO GO para modelo físico/dimensional definitivo o KPIs comerciales mientras sigan abiertos los bloqueos relevantes.** No es una aprobación del usuario para implementar nada. Próximo paso: obtener encabezado/diccionario y metadatos de la edición, resolver cantidad/precio/moneda y granularidad/repetidos, confirmar identidad/cobertura y licencia con fuente verificable. Las preguntas concretas y criterios están en SEMANTIC_VALIDATION.md.

### Antecedente: cierre de QA de normalización v1

En la fase anterior se emitió **APROBADO para normalización estructural del archivo auditado**, con los criterios de software ejecutados. Las secciones siguientes preservan esa evidencia histórica y sus limitaciones; no constituyen validación semántica ni nuevas ejecuciones de esta fase.

### Archivos y trabajo completado

- src/normalize_jewelry.py: rechazo explícito de formatos no admitidos; límite de campo explícito y restaurado; publicación exclusiva de quality.json tras escribir, vaciar y cerrar .quality.json.partial. Contrato JSON y VERSION=1 conservados.
- tests/test_normalize_jewelry.py: integración real obligatoria, sin skip; caso multilínea exige rechazo; fixture CSV inválido cerrado sigue comprobando conservación.
- tests/independent_checks.py: oráculo sin imports de funciones o constantes del pipeline. Compara los 9 campos de cada registro, todos los campos posicionales y los 20 campos de quality.json, tipos incluidos, contra reconstrucción independiente del original.
- tests/test_qa_unit.py: 17 pruebas nuevas de oráculo, mutaciones, formatos y fallos controlados.
- tests/test_cli_integration.py: 9 pruebas nuevas de subprocess, códigos de salida, errores y compatibilidad real. Copia aislada de código y fixtures/original en un proyecto temporal; ninguna escritura en el proyecto oficial.
- tests/run_suite.py: selección explícita de unitarias/integración y rechazo de skips para aceptación completa.
- tools/benchmark_normalization.py: procesos nuevos, tiempo y memoria residente máxima, validación independiente y limpieza del árbol temporal propio.
- docs/PIPELINE.md y docs/DECISIONS.md: contrato, políticas y decisiones actualizados.

No se modificó data/raw ni data/processed/normalization-v1. No se instalaron dependencias ni se publicaron datos. Solo biblioteca estándar y Python preexistente.

### Ejecuciones y resultados exactos

Desde la raíz del proyecto, con un intérprete Python preexistente en el entorno de auditoría:

```powershell
python -B tests/run_suite.py
python -B tools/benchmark_normalization.py --runs 3
```

Ambos comandos terminaron con código 0. Resumen literal del runner completo:

```text
FULL SUITE - REAL DATA REQUIRED
----------------------------------------------------------------------
Ran 39 tests in 32.998s

OK
QA_RESULT tests=39 failures=0 errors=0 skipped=0
```

Desglose: 29 unitarias (12 originales actualizadas y 17 nuevas); 10 de integración (9 del CLI y 1 del módulo con dataset real). Son 26 pruebas nuevas sobre las 13 anteriores, con revisión de las que tenían expectativas insuficientes. Los subcasos se ejecutan dentro de esos métodos y no inflan el conteo de 39.

La primera corrida de desarrollo ejecutó 36 pruebas y terminó con 1 error: la captura UTF-8 no coincidía con la codificación de mensajes del subprocess Windows. Se corrigió usando -X utf8 en hijos, se añadieron tres escenarios adicionales y se ejecutó la suite completa de 39 con el resultado anterior. No se afirma aprobación de esa primera corrida.

### Cobertura incorporada

- CLI: éxito/ayuda=0, error operativo=1, argumento/ruta inválida=2; stdout/stderr, ausencia de traceback en fallos simulados, rechazo de sobrescritura y hash incorrecto, original intacto.
- Oráculo: cálculos independientes de todos los conteos, distribuciones, estados, líneas vacías, hashes y metadatos del reporte; igualdad registro a registro y unicidad de IDs. Sin reutilizar generadores ni helper SHA del pipeline.
- Mutaciones: los 20 campos del reporte y los 9 campos de un registro, individualmente; registro alterado detectado incluso actualizando el hash de salida. También filas faltantes, extras, reordenadas y deduplicadas. Solo fixtures temporales; no hay mutación del código oficial.
- Formatos: UTF-8 sin BOM, LF/CRLF mixtos, sin salto final, comas/comillas escapadas, vacíos y espacios; rechazo de BOM, CR aislado, multilínea y campos excesivos. Frontera de campo probada: 131.072 admitido, 131.073 rechazado. Anchuras 1, 2, 10, 12, 14 y 20 se conservan como inválidas.
- Fallos: permisos de lectura/creación denegados; escritura parcial de records y del reporte; errores de cierre, flush, fsync, publicación y colisión del marcador. Simulados en temporales, sin cambiar ACL ni llenar discos reales. Se verifica rechazo de directorio parcial y ausencia de marcador propio de éxito.
- Se prueba cambio real de un fixture durante normalize y rechazo por hash; nunca sobre data/raw.
- Ausencia de dataset: se comprueba con raíz simulada que la integración falla y no se omite. El runner parcial anuncia UNIT ONLY - NO FULL APPROVAL. No hay skips en la ejecución completa realizada.

### Integridad, compatibilidad y reproducibilidad

| Criterio | Resultado verificado |
|---|---|
| Registros conservados | 95.911 |
| 13 campos / 11 campos sin alinear | 90.559 / 5.352 |
| Repeticiones exactas excedentes | 2.589, conservadas |
| Grupos repetidos / filas involucradas | 2.298 / 4.887 |
| Línea vacía inicial | Preservada en el reporte, línea 1 |
| Registros estructuralmente inválidos en el archivo real | 0 |
| Pendientes de esquema corto | 5.352 |
| Validación semántica pendiente | 95.911; no se interpretaron valores de negocio |
| CLI real, dos salidas nuevas | Comparadas byte a byte con records.jsonl y quality.json oficiales |
| Módulo real, dos salidas nuevas | Reproducibilidad comprobada |
| Benchmark, tres salidas nuevas | Todas verificadas independientemente y con hashes iguales a oficiales |
| Original y oficiales | Hashes antes/después iguales |
| Temporales de aceptación | Eliminados por TemporaryDirectory, sin tocar salidas oficiales |

Hashes SHA-256 confirmados independientemente y nuevamente por Get-FileHash:

- Original: 09d8a61644f66cbb9ad8c50f59180978a0995d121196faf25ef28083dd7b84a2.
- records.jsonl oficial: 5eef0df67a63c918b23a5d01627d6debfd88937c7f499e5b4bc25322bbff63e8.
- quality.json oficial: d58407f19d6f3727866ce2ec7674756da7a1a96624f0f5aac74e4c070fefe129.

No cambió el formato de salida: las correcciones son compatibles byte a byte con el baseline. No se forzó alineación corta ni se eliminaron duplicados.

### Medición de recursos

Python 3.12.14, MSC v.1944 64 bit (AMD64); Windows-11-10.0.26200-SP0. Tres procesos nuevos, dataset de 13.617.148 bytes. Intervalo: llamada normalize completa con hashes y escritura, sin arranque del intérprete ni validación posterior. Memoria: PeakWorkingSetSize del proceso, medida con GetProcessMemoryInfo, no memoria neta exclusiva del algoritmo.

| Corrida | Segundos medidos | Pico residente, bytes | MiB |
|---|---:|---:|---:|
| 1 | 2.9962956998497248 | 44.236.800 | 42,1875 |
| 2 | 3.342081799870357 | 44.224.512 | 42,17578125 |
| 3 | 3.0552379998844117 | 44.322.816 | 42,26953125 |

El benchmark terminó indicando protected_files_unchanged=true y temporaries_removed=true. No se vació la caché de disco. No se definió un SLA ni un umbral artificial. Resultados dependientes de hardware, caché, sincronización de archivos, antivirus y carga del equipo; no extrapolados a datasets mayores.

### Riesgos residuales y siguiente paso

- Memoria proporcional a cantidad/longitud de textos distintos; medición disponible para este archivo, sin garantía de escala arbitraria.
- La publicación del reporte requiere enlaces duros; en filesystem incompatible falla sin publicar éxito. No se garantiza durabilidad de records/directorios ante corte de energía; no se ensayaron fallos físicos.
- Simulaciones de permisos/escritura no sustituyen pruebas de todas las ACL, dispositivos o fallos del sistema operativo.
- El límite csv se restaura, pero es global al proceso: no usar normalize concurrentemente desde threads. Un proceso por ejecución.
- Los directorios parciales se conservan para inspección; no se limpian ni reusan automáticamente. Una falla al quitar el alias temporal tras publicar puede dejarlo junto al resultado válido.
- El verificador independiente comparte la biblioteca CSV estándar; no hay verificación formal ni parser independiente de esa biblioteca.
- Diccionario oficial, licencia, semántica de columnas y causa de repetidos siguen pendientes como cuestiones de datos, fuera de este cierre de software.

No quedaron defectos críticos identificados dentro del contrato estructural auditado; las limitaciones anteriores están acotadas y documentadas. Ese cierre habilitó la fase documental posteriormente solicitada y descrita al comienzo de este archivo; no habilita transformaciones semánticas.

## Cierre documental — 2026-10-20

- Revisados git diff y git diff --check: sin errores de whitespace; Git advierte conversión futura LF→CRLF según configuración existente, sin cambiarla.
- 17 archivos protegidos comparados por SHA-256 antes/después (src, tests, raw, processed, tools y PIPELINE.md): todos idénticos; conjunto sin altas ni bajas. Manifiesto SHA-256 del JSON de rutas relativas y hashes ordenados: fa5f54d43ce4f15d08fc0243335904781c780d3758a12e655cc8bc6898cf2999. Incluye cachés preexistentes; control local, no benchmark portable.
- Verificados enlaces internos de los 11 documentos nuevos/modificados: sin destinos inexistentes. Fuentes externas reutilizadas de la investigación anterior, sin nueva comprobación de disponibilidad ni captura inmutable.
- Escaneo de los 11 documentos: sin patrones de rutas personales, URLs firmadas, tokens GitHub, claves privadas o IDs individuales de 19 dígitos. El escaneo por patrones no garantiza ausencia absoluta de secretos.
- git check-ignore confirma exclusión de jewelry.csv, records.jsonl y quality.json. Solo cambió documentación; no se publicó ningún archivo ni dataset.
- Sin nueva ejecución de la suite o pipeline: el cambio es documental; las 39 pruebas son evidencia histórica. Sin cálculos comerciales ni evaluación de escenarios ejecutada. Validación semántica abierta y cambios locales pendientes de aprobación.

## Corrección de cinco hallazgos documentales — 2026-10-20

Se corrigieron seis documentos: DATA_SOURCES, SEMANTIC_VALIDATION, DATA_DICTIONARY, ANALYTICS_FEASIBILITY, STATUS y README. Se separaron pendientes vigentes de consultas históricas fechadas; la versión pública actual 2 no se confunde con el mapeo pendiente del identificador interno local 2873760. Atribución y uso gratuito publicados no equivalen a redistribución o explotación comercial irrestricta.

E10 dispone de entradas, pasos, reglas, comando completo de solo lectura y salida ejecutada en SEMANTIC_VALIDATION. Se reprodujo sobre el original con Python preexistente, biblioteca estándar y -B, código 0: 95.911 registros (90.559/5.352), una línea vacía, cero anchuras inesperadas, 2.589 excedentes; cada hipótesis compatible en 5.352 casos e iguales valores en los 5.352. SHA-256 original antes/después idéntico. No se escribieron candidatos ni registros. semantic_profile.py no implementa E10 y no fue modificado ni ejecutado en esta corrección.

La matriz conserva 14 capacidades con un estado único por fila; los perfiles posicional y temporal son alcance técnico de calidad. El objetivo antiguo de preparación previa a Git queda subordinado al historial fechado. README conserva información duradera, sin la nota transitoria de cambios locales.

Verificaciones: bloque Python extraído del comando documentado y reejecutado con resultado idéntico y código 0; git diff revisado y git diff --check sin errores; enlaces internos/ancla E10 y escaneo por patrones sin hallazgos; 17 archivos protegidos con el mismo manifiesto fa5f54d43ce4f15d08fc0243335904781c780d3758a12e655cc8bc6898cf2999. Escenarios A/B/C sin modificaciones; C sigue hipotético y no ejecutado. No se reejecutó suite QA ni pipeline, ni se instalaron dependencias o cambió configuración Git. Comprobaciones documentales no equivalen a cierre semántico.

Dictamen para revisión: APROBADO para un futuro commit exclusivamente documental; los cambios siguen locales y requieren revisión del usuario. Data Engineering y validación semántica siguen abiertos. Persisten los bloqueos P0/P1/P2 del estado vigente. No se creó commit ni se hizo push.

## Cierre funcional de capa SQLite — 2026-10-20

Comandos ejecutados con el intérprete preexistente, reemplazando python por su ejecutable local (sin instalar):

```powershell
python -B tests/run_evidence_suite.py
python -B tests/run_suite.py
python -B src/evidence_sqlite.py load --records data/processed/normalization-v1/records.jsonl --quality data/processed/normalization-v1/quality.json --database data/evidence/jewelry.sqlite
python -B src/evidence_sqlite.py query --database data/evidence/jewelry.sqlite --query summary
python -B src/evidence_sqlite.py query --database data/evidence/jewelry.sqlite --query multiplicity
```

Suite final nueva: **27 pruebas en 76.464 s**, código 0; `EVIDENCE_QA tests=27 failures=0 errors=0 skipped=0` (26 unitarias y una integración real). Suite v1 sin modificaciones: **39 pruebas en 37.645 s**, código 0; `QA_RESULT tests=39 failures=0 errors=0 skipped=0`. Las duraciones corresponden a esta ejecución, con procesos simultáneos; no son benchmark ni SLA. Se ejecutaron unitarias durante desarrollo, detectando y corrigiendo cierre de conexiones en Windows; el resultado final citado corresponde al código final, incluyendo consulta de anchuras mixtas invalid_csv/parseable.

| Evidencia real | Resultado |
|---|---:|
| Ocurrencias | 95.911 |
| Anchura 13 / 11 | 90.559 / 5.352 |
| Campos originales almacenados | 1.236.139 |
| Grupos repetidos | 2.298 |
| Excedentes repetidos | 2.589 |
| Ocurrencias involucradas en repeticiones | 4.887 |
| Base local SQLite | 293.298.176 bytes |

Integración: comparación de todas las ocurrencias/campos con JSONL oficial, todas las propiedades de quality, dos cargas independientes lógicamente iguales y recarga idempotente; integridad SQLite y referencial sin hallazgos. Fuentes/reportes incompletos o alterados y fallos controlados rechazados sin base parcialmente aceptada. CLI real: load creó base y su repetición devolvió unchanged con bytes de base intactos; summary/multiplicity verificaron los conteos anteriores. quality y record contrastados contra entradas por subprocess, sin imprimir registros individuales.

17 archivos anteriores protegidos (raw, processed, src/tests previos, tools y PIPELINE.md), incluidos cachés preexistentes: hashes idénticos; manifiesto conservado fa5f54d43ce4f15d08fc0243335904781c780d3758a12e655cc8bc6898cf2999. Se verificó además identidad con HEAD del código, tests, tools y PIPELINE previos. Datos oficiales: CSV SHA-256 09d8a61644f66cbb9ad8c50f59180978a0995d121196faf25ef28083dd7b84a2; records 5eef0df67a63c918b23a5d01627d6debfd88937c7f499e5b4bc25322bbff63e8; quality d58407f19d6f3727866ce2ec7674756da7a1a96624f0f5aac74e4c070fefe129.

Nuevos: src/evidence_sqlite.py, tests/test_evidence_sqlite.py, tests/run_evidence_suite.py y docs/EVIDENCE_SQLITE.md. Modificados: .gitignore, AGENTS.md, README.md, docs/DECISIONS.md y este STATUS. Base generada solo en data/evidence, fuera de salidas oficiales y excluida. No se modificó ningún archivo previo de src/tests, ni pipeline ni datos oficiales. Las bases de integración se generaron y eliminaron con TemporaryDirectory; la base local consultable se conserva intencionalmente.

Verificaciones finales: git diff --check código 0; enlaces internos y escaneo por patrones sin hallazgos de secretos, IDs individuales o rutas personales; exclusiones de base, journal/WAL/SHM y staging confirmadas con git check-ignore. Git solo muestra los nueve archivos de implementación/documentación anteriores; sin staging, commit, push, configuración global o publicación. No se incorporaron datasets a los archivos publicables. El escaneo por patrones no certifica ausencia absoluta de secretos.

Implementación lista para una única evaluación funcional; sin bloqueos funcionales identificados dentro del alcance probado. Límites: enlaces duros requeridos, memoria proporcional a textos distintos, espacio extra para staging/recarga, operación sin escritores concurrentes, sin prueba física de ACL/disco lleno/corte eléctrico. No se promete durabilidad del directorio ante corte de energía. Data Engineering sigue abierto, igual que validación semántica; no se aprobaron cantidades, ingresos, clientes, KPIs, dashboards o modelos.

## Cierre de primera entrega vertical Aurelia — 2026-10-20

**Resultados ejecutados (no propuestas):**

| Comando (Python preexistente, -B) | Resultado |
|---|---|
| tests/run_aurelia_suite.py | 23 pruebas, 3.894 s, código 0; AURELIA_QA tests=23 failures=0 errors=0 skipped=0 |
| tests/run_suite.py | 39 pruebas v1, 33.140 s, código 0; QA_RESULT tests=39 failures=0 errors=0 skipped=0 |
| tests/run_evidence_suite.py | 27 pruebas de evidencia, 67.822 s, código 0; EVIDENCE_QA tests=27 failures=0 errors=0 skipped=0 |

Las duraciones reflejan esta máquina, incluyendo ejecuciones simultáneas; no son SLA ni benchmark. El sandbox de Windows denegó crear subdirectorios dentro de temporales; se interrumpieron esas ejecuciones y se ejecutaron las suites con permisos normales autorizados. Se corrigió la captura UTF-8 de subprocess en las nuevas pruebas para no ocultar errores de lectura de stderr. No se modificó código de REES46 para conseguir aprobación.

**Ejecución funcional sintética, semilla 42 y 30 pedidos solicitados:**

- data/aurelia/normal-seed42: 30 pedidos, 70 artículos y 35 pagos; 135 filas staging, status ACCEPTED, cero rechazos; integración y hechos conservan sus conteos. Base nueva data/aurelia/warehouse-normal.sqlite (192.512 bytes).
- Total contractual de artículos de pedidos PAID: 92.000 centavos USD sintéticos; capturados: 92.000. Son importes de simulación y no ventas observadas/ingresos contables. Los 30 pedidos tienen diferencias de artículos y pagos iguales a cero según su estado.
- data/aurelia/adverse-seed42: 31 cabeceras, 71 artículos y 35 pagos; 137 staging, 9 motivos de rechazo; status REJECTED y código CLI 1 esperado; cero filas integradas y cero hechos. Base nueva warehouse-adverse.sqlite para trazabilidad de rechazos.
- Reglas observadas: CURRENCY 1, DUPLICATE_KEY 2, INTEGER_RANGE 1, ITEM_RECONCILIATION 1, ORPHAN 3, PAYMENT_RECONCILIATION 1. Son motivos, no filas distintas; las cabeceras inválidas producen referencias no disponibles para validación.
- Recarga CLI/API de la base normal: unchanged; hash del destino antes/después idéntico. Dos reconstrucciones independientes y regeneración por semilla comparadas en pruebas. Rechazos, reconstrucción fuente, FK, claves, atomicidad, alteraciones e importes legítimamente iguales cubiertos por la suite.
- Ejemplo sintético SIM-O-000001: 3 artículos/2 pagos, correcto 3.000/3.000 centavos. El join incorrecto genera 6 filas y sumas 6.000/9.000; SUM(DISTINCT) daría 1.000 en artículos. La prueba negativa exige detectar ambas distorsiones.

**Protección y alcance:** se comprobó igualdad con HEAD de 14 archivos previos de código/pruebas/tools y documentación de pipeline/evidencia; hashes oficiales CSV, records.jsonl y quality.json coinciden con los registrados. Ninguna escritura solicitada sobre data/raw, data/processed o data/evidence. La base persistida data/evidence/jewelry.sqlite devolvió PermissionError al intentar calcular SHA-256, incluso con permisos ampliados: no se afirma verificación de hash de esa base. La suite de evidencia valida reconstrucciones temporales desde salidas oficiales; no sustituye ese control de acceso sobre la base existente. Es una limitación de verificación del entorno, no un fallo funcional demostrado del nuevo Warehouse. No se alteraron ACL ni se forzó su apertura.

Archivos nuevos: src/aurelia/__init__.py, contracts.py, generator.py, warehouse.py y __main__.py; tests/test_aurelia_dw.py y tests/run_aurelia_suite.py; docs/AURELIA_DW.md. Modificados: .gitignore, AGENTS.md, README.md, docs/DECISIONS.md y este STATUS. Ningún archivo preexistente de src/tests modificado. Artefactos normales/adversos locales están excluidos íntegramente, incluidos manifiestos y bases. No se instaló ninguna dependencia ni se descargó dataset.

Límites residuales: un snapshot por base, operación con un solo escritor; límites del generador 6–10.000 pedidos; listas en memoria, sin pretensión de escala de producción; publicación requiere enlaces duros; no se probaron fallos físicos de disco/corte eléctrico ni se garantiza durabilidad del directorio. Generador y Warehouse no son validación de una política fiscal real. El control de la base REES46 existente está limitado por el acceso descrito arriba. El incremento queda local, listo para una evaluación funcional; no se declara terminado Data Engineering.

Verificación de entrega: git diff --check código 0; enlaces internos y escaneo por patrones sin hallazgos; todos los archivos en data/aurelia confirmados ignorados por Git; staging vacío. Cambios limitados a cinco archivos de organización/documentación y ocho archivos nuevos de código/pruebas/documentación Aurelia. No hay datos generados en los candidatos versionables. Los límites de acceso a la base REES46 persistida permanecen explícitos; no se presenta como verificado su hash. No se ejecutaron commit ni push ni se cambió configuración global de Git.

## Cierre funcional Aurelia v2 — 2026-10-20

Comandos ejecutados con Python preexistente y -B; por restricciones del directorio temporal del sandbox se usaron permisos normales autorizados, sin cambiar ACL de datos históricos ni instalar herramientas:

| Suite | Resultado real final |
|---|---|
| python -B tests/run_aurelia_v2_suite.py | 24 pruebas, 6.623 s, código 0; AURELIA_V2_QA tests=24 failures=0 errors=0 skipped=0 |
| python -B tests/run_aurelia_suite.py | 23 pruebas v1, 4.613 s, código 0; AURELIA_QA tests=23 failures=0 errors=0 skipped=0 |
| python -B tests/run_suite.py | 39 pruebas REES46, 28.995 s, código 0; QA_RESULT tests=39 failures=0 errors=0 skipped=0 |
| python -B tests/run_evidence_suite.py | 27 pruebas de evidencia, 65.054 s, código 0; EVIDENCE_QA tests=27 failures=0 errors=0 skipped=0 |

113 pruebas ejecutadas en las cuatro suites finales, sin fallos/errores/omisiones. Duraciones de esta máquina con procesos simultáneos; no son benchmark o SLA. Durante desarrollo se corrigió la selección del caso parcial de línea y una prueba que dependía del orden incidental de los eventos; el resultado final usa selección por estado/condición. No se cambió v1 para hacer pasar pruebas.

Pruebas nuevas cubren base generada idéntica a v1, todas las tablas históricas iguales a un baseline independiente, rechazo de un destino v1 sin migración, retornos completos/parciales, reembolso total/parcial, pendientes/fallidos, GOODWILL sin recepción, límites acumulados al centavo, referencias/fechas/moneda, duplicados, manifest/hash, atomicidad tras inserciones y fallo en publicación final v2, reconstrucción de staging, idempotencia y comparación lógica completa. También ausencia de ajustes, pago fallido y pedido no pagado. Los casos inválidos quedan como lote de ajustes rechazado completo, no aceptación parcial.

**Ejecutado por CLI/API en directorios nuevos (todos los importes son sintéticos USD):**

- Fuente normal: data/aurelia/v2-normal-seed42; base local data/aurelia/warehouse-v2-normal.sqlite. 30 pedidos, 70 artículos, 35 pagos históricos; se añaden 5 eventos físicos y 7 registros financieros. Staging de ajustes 12, rechazos 0, status ACCEPTED/código 0.
- Capturado original 92.000 centavos; reembolsos COMPLETED 1.400; comprometido REQUESTED+COMPLETED 1.600; neto capturado 90.600; unidades físicamente recibidas 3. No son ingresos contables o resultados observados.
- Ejemplo SIM-O-000001: 3.000 capturados, 900 reembolsados, 1.100 comprometidos, neto 2.100 y una unidad recibida. El segundo pedido tiene devolución física completa sin reembolso; el tercero pagado (SIM-O-000005) tiene reembolso completo y ninguna recepción física.
- Fuente adversa: data/aurelia/v2-adverse-seed42; base warehouse-v2-adverse.sqlite. Staging de ajustes 14, motivos de rechazo 15, status REJECTED/código CLI 1 esperado; int_return/int_refund/fact_return/fact_refund vacíos. Los 30 pedidos/70 artículos/35 pagos base permanecen; capturado neto 92.000 sin ajustes aceptados. Reglas: RETURN_LIMIT 2, REFUND_PAYMENT_LIMIT 4, REFUND_RETURN_LIMIT 4 y REFUND_ORDER_LIMIT 5; motivos pueden compartir registro.
- Recarga de base normal: unchanged y bytes idénticos antes/después. Los cuatro archivos fuente v1 persistidos normal-seed42 coinciden byte a byte con v2-normal-seed42/base. Tests verifican todas las tablas históricas preservadas dentro de la reconstrucción v2 y un destino v1 existente intacto.

Protección: 22 archivos históricos versionados de src/tests/tools y contratos PIPELINE/EVIDENCE_SQLITE/AURELIA_DW comparados con HEAD sin diferencias. Hashes CSV original, records.jsonl y quality.json REES46 coinciden con los registrados. No se solicitaron escrituras sobre bases históricas. No se repitió ni se afirma el control bloqueado de hash de la base REES46 persistida; su limitación de acceso sigue explícita.

Nuevos: src/aurelia/v2.py, tests/test_aurelia_v2.py, tests/run_aurelia_v2_suite.py y docs/AURELIA_DW_V2.md. Modificados: AGENTS.md, README.md, docs/DECISIONS.md y STATUS.md. Sin cambios a .gitignore: sus reglas ya excluyen todos los artefactos v2 en data/aurelia y auxiliares SQLite. Sin dependencias, dashboards, ML, cambios a datos reales, commit o push.

Límites funcionales declarados: un snapshot completo por base, no ingestión incremental/transiciones; fechas de captura v1 desconocidas, sin cronología inventada; recepción física es un estado sintético, no prueba logística. La devolución parcial de una línea mult(unidad) depende de que exista una línea elegible con esa semilla/cantidad; el caso estándar 42/30 la incluye y prueba. Se mantienen enlaces duros/permisos normales, un escritor, espacio de staging y listas en memoria; sin garantía de crash recovery o durabilidad del directorio ante corte eléctrico. No quedaron fallos funcionales identificados en el alcance probado; cambios locales para evaluación, sin cierre de Data Engineering.
