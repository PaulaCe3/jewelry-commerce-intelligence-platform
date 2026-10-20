# Capa técnica de evidencia SQLite

Implementación independiente de normalización v1. Python >=3.11, biblioteca estándar (`sqlite3` incluido); no requiere instalación, pip, red ni cambios al pipeline aprobado. Los archivos locales de entrada no se distribuyen. Aurelia Jewelry es ficticia; esta base no es un modelo comercial ni contiene KPIs validados.

## Ejecutar desde la raíz

Usar el Python preexistente; sustituir `python` por su ejecutable si no está en PATH. El directorio de salida elegido queda fuera de raw/processed y la base se excluye de Git:

```powershell
python -B src/evidence_sqlite.py load --records data/processed/normalization-v1/records.jsonl --quality data/processed/normalization-v1/quality.json --database data/evidence/jewelry.sqlite
python -B src/evidence_sqlite.py query --database data/evidence/jewelry.sqlite --query summary
python -B src/evidence_sqlite.py query --database data/evidence/jewelry.sqlite --query quality
python -B src/evidence_sqlite.py query --database data/evidence/jewelry.sqlite --query multiplicity
```

Repetir exactamente `load` verifica entradas y compara todas las tablas y esquema contra una carga nueva en staging. Devuelve `unchanged` si son iguales; no duplica filas ni sobrescribe una base distinta. El manifiesto identifica también los bytes exactos de ambos artefactos: cambiar formato JSON puede exigir un destino nuevo aunque el contenido lógico parezca equivalente.

Para localizar una ocurrencia sin copiar IDs a documentación pública, este ejemplo toma el ID de la primera ocurrencia del archivo local. Se ejecuta solo en el entorno privado y devuelve campos y texto originales:

```powershell
$rowId = python -B -c "import json; print(json.loads(open('data/processed/normalization-v1/records.jsonl', encoding='utf-8').readline())['row_id'])"
python -B src/evidence_sqlite.py query --database data/evidence/jewelry.sqlite --query record --row-id $rowId
```

No publicar stdout de `record`, bases, journals ni entradas. Las consultas abren SQLite en modo `ro` y `query_only`; un archivo ausente no se crea. CLI: 0 éxito, 1 rechazo operativo/contrato/consulta, 2 argumentos inválidos. Los errores del CLI no imprimen registros ni rutas personales. La API Python conserva excepciones técnicas para depuración local.

## Esquema técnico, versión 1

| Tabla | Contenido y claves |
|---|---|
| `source_file` | SHA-256 reconstruido, líneas físicas y versión del pipeline; hash como clave técnica de contenido |
| `import_manifest` | Versión del esquema y hashes de records/quality; una carga por base |
| `occurrence` | row_id v1, hash fuente, línea, anchura nullable, estado, raw_text y terminador; unicidad técnica de ID y archivo/línea |
| `original_field` | row_id, posición desde 1 y valor textual exacto; PK compuesta, vacíos preservados |
| `blank_line` | Línea y terminador de vacíos registrados en quality.json |
| `quality_result` | Cada propiedad del reporte, incluida su estructura JSON, con clave archivo/propiedad |

Foreign keys conectan ocurrencias, líneas vacías y calidad al archivo; campos a ocurrencias. Índices de anchura y contenido permiten conteos y multiplicidad. No hay claves de negocio, precio tipado, ventas, dimensiones ni hipótesis dentro del núcleo: siguen documentadas. No se guarda una versión pública de REES46 o procedencia remota como confirmada.

`positional_fields_13` es derivable de campos largos; la consulta `record` lo reconstruye solo para 13 campos, devolviendo null para cortas. `original_fields` es null en invalid_csv y lista en CSV parseable, incluso con anchura inesperada. `raw_text` y terminadores conservan la representación fuente; no se promete conservar espacios/formato del objeto JSON original, cuyo hash sí identifica sus bytes. La tabla de calidad preserva todas las propiedades del reporte, no inventa controles empresariales.

## Validación y aceptación

1. Rechazar JSON con claves repetidas, constantes no finitas, propiedades extra/ausentes, versiones incompatibles o ejecución incompleta. Comprobar output_sha256 antes de cargar.
2. Contrastar cada objeto con parseo CSV de raw_text: campos, anchura, estado, posiciones, ID y orden de líneas. Respetar formatos/límite v1 sin importar sus funciones.
3. Reconstruir secuencialmente el SHA-256 UTF-8 fuente, intercalando líneas vacías. Detectar faltantes, extras, desorden, terminadores incompatibles y mutaciones coherentes que no coincidan con el hash fuente.
4. Recalcular conteos, distribuciones y duplicados por igualdad exacta de raw_text sin terminador; contrastar todas las propiedades del reporte. `audit_acceptance_checked` se conserva como declaración de v1; si es true, se vuelven a exigir hash y conteos auditados. No implica aprobación semántica.
5. Verificar hashes de entradas otra vez, integridad SQLite y foreign keys antes de commit. No se modifican las entradas ni se elimina multiplicidad; las cortas conservan 11 posiciones.

La validación se ejecuta dentro de una transacción en una base temporal todavía no aceptada. Solo después del commit y cierre se publica con enlace duro exclusivo en el mismo filesystem; nunca reemplaza un destino existente. Errores de lectura, contrato, inserción o publicación no dejan una base final parcialmente aceptada; el staging de esa ejecución se elimina. Puede quedar el directorio padre vacío.

## Consultas SQL equivalentes

Consultas técnicas, no de negocio, ejecutables mediante `sqlite3` de Python sin instalar un CLI externo:

```sql
SELECT COUNT(*) FROM occurrence;
SELECT original_field_count, COUNT(*) FROM occurrence GROUP BY original_field_count;
SELECT source_line, raw_text, line_ending FROM occurrence WHERE row_id = ?;
SELECT position, value FROM original_field WHERE row_id = ? ORDER BY position;
SELECT property, value_json FROM quality_result ORDER BY property;
SELECT SUM(n - 1) FROM (SELECT COUNT(*) AS n FROM occurrence GROUP BY raw_text);
```

Los signos `?` requieren parámetros enlazados; no interpolar IDs en SQL. La implementación usa parámetros para la búsqueda.

## Pruebas

```powershell
python -B tests/run_evidence_suite.py --unit-only
python -B tests/run_evidence_suite.py
python -B tests/run_suite.py
```

El runner nuevo distingue unitarias de integración. Sin flags exige los artefactos oficiales y el original local para su control de hashes; si faltan, falla, no omite. `--unit-only` usa fixtures temporales producidos por v1 y no constituye aceptación integral. El runner antiguo permanece intacto y no incluye las pruebas nuevas; ejecutar ambos para verificar ambas capas. `unittest discover` también descubre las nuevas pruebas y exige integración real.

La integración contrasta todos los registros/campos y propiedades del reporte con lectores SQL/JSON independientes de las consultas del cargador; compara lógicamente todas las tablas de dos cargas independientes y verifica recarga idempotente. Las pruebas unitarias cubren referencialidad, unicidad, orden, vacíos, quoting, Unicode, terminadores, multiplicidad, anchuras inesperadas/invalid_csv, entradas alteradas, todos los metadatos del reporte, destino alterado, CLI y fallos simulados. Solo fixtures mutables temporales; no se altera código oficial para las simulaciones.

## Límites explícitos

- No se verifican permisos comerciales ni semántica de compra/cliente/cantidad/moneda. Data Engineering continúa abierto.
- Hashes verifican coherencia y cambios accidentales; no prueban autenticidad si un tercero reemplaza coherentemente todas las evidencias. La exigencia auditada añade el anclaje al original conocido cuando el reporte la declara.
- Memoria proporcional al número/tamaño de textos distintos del contador de repetidos; lectura JSONL secuencial, sin DataFrame. Staging y comparación idempotente requieren espacio adicional y una carga completa.
- Ejecutar una carga por proceso, sin cambios concurrentes de las entradas/base. Se detectan cambios por hashes antes/después, pero no se ofrece aislamiento contra un escritor hostil o modificaciones posteriores.
- Se requiere soporte de enlaces duros; si falta o no hay permisos, la publicación falla de forma cerrada. No se probaron ACL físicas, disco realmente lleno ni cortes eléctricos; no se garantiza durabilidad del directorio ante pérdida de energía. Un cierre abrupto puede dejar staging ignorado, nunca debe aceptarse como base final.
- La base es evidencia local sensible. Los hashes o IDs técnicos no anonimizan sus registros. `.gitignore` protege bases, auxiliares SQLite y staging, pero no reemplaza una revisión antes de cualquier futura publicación.

Resultados de ejecución e integridad: [STATUS.md](STATUS.md). Contrato original: [PIPELINE.md](PIPELINE.md). No se modifica normalización v1.

## Resultado local verificado — 2026-10-20

Suite nueva final: 27 pruebas (26 unitarias + una integración real), sin fallos, errores u omisiones. Regresión v1: 39 pruebas aprobadas. Base local cargada: 95.911 ocurrencias, anchuras 90.559/5.352, 1.236.139 campos y 2.589 excedentes. Dos bases temporales comparadas lógicamente; recarga CLI idempotente sin modificar bytes del destino. Archivo local: data/evidence/jewelry.sqlite, 293.298.176 bytes, no distribuido. Resultados son de ingeniería, no de negocio. Comandos, hashes, alcance de simulaciones y limitaciones en STATUS.md.
