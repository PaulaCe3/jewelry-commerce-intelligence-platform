# Procedencia, condiciones y límites de REES46 Jewelry

## Estado vigente — 2026-10-20

La investigación primaria posterior recuperó S06/S07, documentadas en [SEMANTIC_VALIDATION.md](SEMANTIC_VALIDATION.md). Este apartado sustituye las conclusiones anteriores de falta total de acceso a Kaggle, sin alterar el historial que sigue.

- **CONFIRMADO:** [API oficial de metadatos](https://www.kaggle.com/api/v1/datasets/view/mkechinov/ecommerce-purchase-history-from-jewelry-store) vincula el slug mkechinov/ecommerce-purchase-history-from-jewelry-store con dataset ID 1005588. Autor: Michael Kechinov; versión pública actual 2, actualizada el 01/12/2021. Versión 1: 29/11/2020.
- **CONFIRMADO como declaración del proveedor:** un producto comprado por fila; productos de una misma compra vinculados por order_id. No equivale a línea única, unidad, pago o entrega confirmados en el archivo local.
- **CONFIRMADO:** [listado oficial de archivos](https://www.kaggle.com/api/v1/datasets/list/mkechinov/ecommerce-purchase-history-from-jewelry-store) contiene jewelry.csv de 13.617.148 bytes, descripción vacía y columns vacío. No se recuperó encabezado/diccionario posicional.
- **PROVISIONAL:** correspondencia de la edición local con versión pública 2. La cadena local ZIP→CSV está verificada por SHA-256; su ruta contiene 1005588/2873760. Falta vincular 2873760→2 o contrastar un checksum publicado. Igual nombre/tamaño/período no demuestra identidad remota byte a byte.
- **CONFIRMADO:** la API publica la etiqueta **Data files © Original Authors** y permite uso gratuito solicitando enlaces a la [ficha del dataset](https://www.kaggle.com/datasets/mkechinov/ecommerce-purchase-history-from-jewelry-store) y [REES46](https://rees46.com). Esto no concede derechos a PLATHEL sobre esos datos ni es una licencia open source del código propio.
- **NO RESUELTO:** alcance expreso de redistribución, sublicencia e incorporación a un producto comercial; no se afirma autorización ni prohibición específica. Se mantiene la prohibición del proyecto de publicar registros originales o procesados.

La descripción Kaggle indica diciembre de 2018–diciembre de 2021, pero su subtítulo menciona 130K productos y dos años; las páginas REES46 también discrepan entre sí. Son inconsistencias editoriales: no permiten concluir pérdida de datos, completitud de la tienda ni ventas faltantes. No trasladar moneda, esquema o licencias de otros datasets/notebooks a esta edición.

Esta consolidación usa las consultas ya realizadas el 2026-10-20; no volvió a descargar datos ni guardó respuestas con registros. Las fuentes se identifican por URL, endpoint, campos recuperados y fecha; no se conserva una captura inmutable de la respuesta remota. Los metadatos del servicio pueden cambiar. Aurelia Jewelry es ficticia y no es dueña de REES46.

## Pendientes vigentes — 2026-10-20

- Vinculación verificable del identificador interno local **2873760** con su número público de versión. La versión pública actual **2** y la asociación slug→dataset **1005588** sí están verificadas; no deben confundirse con la edición exacta del archivo local.
- Encabezado/diccionario posicional, unidad física y clave de línea; cantidad, importe/moneda, estados e identidad persistente.
- Causa de las filas cortas y de las repeticiones; no se seleccionó alineación ni política comercial de multiplicidad.
- Alcance expreso de redistribución, sublicencia y explotación comercial adicional: uso gratuito y atribución publicados no equivalen a autorización irrestricta.
- Completitud respecto de origen, checksum remoto y fecha real de adquisición. La identidad CSV→ZIP local no prueba identidad con cualquier versión remota.

## Historial de adquisición y consultas — evidencia anterior

Los apartados siguientes conservan lo conocido en las revisiones anteriores. Sus pendientes de granularidad declarada, asociación slug/ID y condiciones publicadas se actualizan arriba; los pendientes de posiciones, moneda y edición exacta permanecen.

### Registro de procedencia anterior — 2026-10-19

Verificación: 2026-10-19. Aurelia Jewelry es una empresa ficticia del caso de PLATHEL; los datos no son propios de Aurelia.

Actualización de la misma fecha: la sección final incorpora evidencia de procedencia recuperada del ZIP local. Sustituye parcialmente el pendiente inicial de adquisición; el número público de edición, diccionario y licencia siguen sin verificarse.

### Histórico al 2026-10-19 — Fuentes primarias consultadas

- [REES46: datasets](https://rees46.com/en/datasets): clasifica Jewelry como transacciones y anuncia noviembre de 2018–noviembre de 2020; enlaza a Kaggle.
- [REES46: catálogo de datos](https://data.rees46.com/): describe compras de una tienda de joyería entre diciembre de 2018 y diciembre de 2021; ofrece un archivo denominado `jewelry-purchases.csv.gz` (~3 MB). Declara los datos anónimos y su utilización para análisis e investigación de marketing y comercio electrónico. No se descargó el archivo remoto.
- [Kaggle: eCommerce purchase history from jewelry store](https://www.kaggle.com/datasets/mkechinov/ecommerce-purchase-history-from-jewelry-store): URL consultada, pero sin contenido textual recuperable en la herramienta web. No fue posible verificar aquí diccionario, versión, licencia ni condiciones específicas.

Las dos páginas oficiales difieren en el período. El rango local observado concuerda aproximadamente con la descripción de data.rees46.com, pero esto **no demuestra identidad de edición o integridad**. No se trasladan licencias, columnas ni condiciones de otros datasets REES46 al de joyería.

### Histórico al 2026-10-19 — Archivo local

El usuario informó que colocó datos REES46 en `data/raw/`. Archivo observado `jewelry.csv`, 13.617.148 bytes, UTF-8 CSV no comprimido, sin encabezado, 95.911 registros no vacíos; 90.559 de 13 campos y 5.352 de 11. Rango 2018-12-01 11:40:29 UTC a 2021-12-01 09:59:07 UTC.

SHA-256: `09d8a61644f66cbb9ad8c50f59180978a0995d121196faf25ef28083dd7b84a2`.

Esquema posicional y tipos detallados en DATA_AUDIT.md. La correspondencia semántica es provisional porque no hay encabezado local y no se pudo recuperar el diccionario primario.

Pendientes: URL exacta utilizada para este archivo, versión/revisión, fecha de adquisición, nombre original, si hubo descompresión, renombrado, filtrado, eliminación de encabezado u otra transformación antes de recibirlo. No atribuir esas acciones al usuario sin confirmación. No se comparó con un checksum del proveedor.

### Histórico al 2026-10-19 — Licencia y límites

**Conclusión histórica del 2026-10-19, actualizada por S06:** licencia específica y condiciones de uso pendientes de verificar. Que una página diga gratuito, público o anónimo no verifica por sí solo permisos de redistribución o explotación comercial. No se confirmó autorización para redistribuir, publicar registros ni incorporarlos a un producto comercial. Debe recuperarse la licencia de esta edición y registrar sus términos antes de decidir usos adicionales. Referenciar REES46 y la ficha exacta cuando se presenten resultados, sin afirmar que esa atribución resuelve permisos pendientes.

La anonimización es una afirmación del proveedor, no una evaluación independiente. Los identificadores locales se tratan como seudónimos: no se exportaron registros ni IDs a la documentación. No hay garantías verificadas de representatividad, continuidad, persistencia de identidad ni totalidad de ventas de la tienda. La empresa real y su relación con Aurelia no están establecidas.

### Histórico al 2026-10-19 — Tratamiento realizado

Solo lectura local para inventario, firma, decodificación, estructura, agregados de calidad e integridad por SHA-256 antes/después. Sin alteración del original, descarga, limpieza ni derivados de registros. No se instalaron dependencias ni se publicaron datos. `.gitignore` conserva exclusiones de `data/raw/` y `data/processed/`. La ausencia de Git inicializado observada anteriormente no autoriza crear un remoto ni publicar.

### Histórico al 2026-10-19 — Evidencia adicional de procedencia — 2026-10-19

Se consultaron exclusivamente el archivo de origen referenciado por el CSV y sus metadatos asociados; no se exploró el historial del navegador ni otros archivos personales.

1. El flujo NTFS `Zone.Identifier` de `data/raw/jewelry.csv` contiene una referencia al ZIP de adquisición. Se omiten su nombre local y ubicación personal en la documentación pública.
2. Ese ZIP existe, mide 2.730.948 bytes y contiene únicamente `jewelry.csv`. Su miembro tiene 13.617.148 bytes, CRC32 `d38d9e33` y SHA-256 `09d8a61644f66cbb9ad8c50f59180978a0995d121196faf25ef28083dd7b84a2`, idéntico al CSV auditado. Se leyó en streaming sin extraerlo ni modificarlo. No contiene README, licencia, encabezado separado o diccionario.
3. El `Zone.Identifier` del ZIP tiene `ReferrerUrl` igual a `https://www.kaggle.com/`. Su `HostUrl`, omitiendo todos los parámetros firmados, es `https://storage.googleapis.com/kaggle-data-sets/1005588/2873760/bundle/archive.zip`. Es evidencia local de un bundle Kaggle: identificador de dataset `1005588`, identificador interno de versión `2873760`. No equivale a un número público del tipo «Version 1/2/3», que no se ha verificado. Los parámetros temporales y firmas no se conservan en esta documentación.

**Conclusión confirmada localmente:** el CSV coincide byte a byte por SHA-256 con el miembro del ZIP referenciado, cuyo metadato de descarga apunta a esa ruta Kaggle. No hay evidencia de cambios del contenido entre ese ZIP y el original en data/raw. Los metadatos NTFS constituyen una pista local de adquisición, no una certificación del proveedor.

**Correspondencia probable, pendiente de verificación remota:** la ficha [Jewelry de Michael Kechinov](https://www.kaggle.com/datasets/mkechinov/ecommerce-purchase-history-from-jewelry-store), enlazada por [REES46](https://data.rees46.com/), por dominio, nombre y cobertura. No se recuperó una respuesta de metadatos que vincule oficialmente el slug con el ID 1005588 y la versión interna 2873760. No se afirma una versión pública exacta ni se compara el archivo con un checksum publicado. No se infiere la fecha efectiva de descarga de las fechas del sistema de archivos o de la firma temporal de la URL.

### Histórico al 2026-10-19 — Reintentos de documentación oficial y licencia

Internet sí estuvo disponible a través de la herramienta web: se recuperó la descripción de compras de joyería 2018–2021 en REES46 y se siguió su enlace a Kaggle. Se consultaron la ficha, las rutas `/data`, `/metadata` y endpoints de metadatos API; no devolvieron contenido utilizable para verificar el diccionario o la licencia. El acceso HTTP directo desde Python fue bloqueado por el entorno (WinError 10013); el navegador integrado no pudo iniciarse. No se instalaron herramientas ni se descargó el dataset para resolverlo.

Se encontró el [notebook inicial del propio autor](https://www.kaggle.com/code/mkechinov/starter-ecommerce-purchase-history-overview). El resultado indexado muestra Apache 2.0 **para el notebook**; su contenido no se recuperó como diccionario. Esa licencia no se traslada al dataset. Las búsquedas no recuperaron otra documentación primaria verificable de columnas o una licencia específica de esta edición. No se usan licencias de copias de terceros, notebooks o datasets REES46 diferentes como autorización.

Al cierre de esa consulta del 2026-10-19 estaban pendientes la licencia del dataset, la atribución exigida y los permisos o restricciones concretas de redistribución y uso comercial. S06 recuperó posteriormente la etiqueta y la atribución; no resolvió el alcance de permisos adicionales. No se ha demostrado ni una prohibición específica ni una autorización. La instrucción del proyecto de no publicar datos se mantiene con independencia de la licencia.

### Pendientes registrados al 2026-10-19 — no son la lista vigente

- Número público de versión y correspondencia remota del ID/versión interna con la ficha candidata.
- Diccionario oficial, unidad de registro, naturaleza de cantidad y precio, moneda y persistencia del cliente.
- Causa de omisión de campos intermedios y política correcta para repeticiones exactas; no se aplicó ninguna reparación.
- Completitud frente al archivo del proveedor y fecha real de adquisición. Solo se confirmó igualdad con el ZIP local, no con todas las ediciones existentes.

Los controles locales adicionales y sus niveles de confianza están en la revisión final de DATA_AUDIT.md. No se modificaron los datos originales ni se creó un dataset limpio.

### Histórico al 2026-10-19 — Transformación estructural autorizada v1 — 2026-10-19

Posteriormente a la auditoría se ejecutó src/normalize_jewelry.py sobre el original, conservando cada línea no vacía, todos los campos como texto y todas las repeticiones. Salidas locales: data/processed/normalization-v1/records.jsonl y quality.json. Las filas de 11 campos no se alinearon: permanecen pendientes. Las de 13 tienen solo nombres técnicos de posición. La línea vacía inicial se registra en el reporte. No se tiparon ni imputaron valores y no se generó un dataset semánticamente limpio.

Hash original antes/durante/después idéntico al registrado; 95.911 registros y 2.589 excedentes conservados. Resultados, pruebas y límites en STATUS.md y PIPELINE.md. Esta transformación no resuelve ni amplía los permisos de uso del proveedor; no se publicaron datos.
