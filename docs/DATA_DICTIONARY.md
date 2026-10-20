# Diccionario de datos — REES46 Jewelry, edición local auditada

Actualización: 2026-10-20. Evidencia local obtenida el 2026-10-19 y contrastada en la investigación posterior. Proyecto 01 de PLATHEL; Aurelia Jewelry es ficticia. **Versión documental preliminar, validación semántica abierta.** No habilita KPIs comerciales definitivos ni cambia la normalización v1.

## Alcance, evidencia y convenciones

Fuente local: `data/raw/jewelry.csv`, SHA-256 `09d8a61644f66cbb9ad8c50f59180978a0995d121196faf25ef28083dd7b84a2`. Son 95.911 registros no vacíos: 90.559 de 13 campos y 5.352 de 11. No hay encabezado. Las posiciones originales son de base 1; los nombres `field_XX` son técnicos, existentes en v1 para filas largas, **no encabezados del proveedor**. Los alias terminados en `_candidate` son propuestas documentales, no renombrados implementados.

Los conteos por campo de este documento corresponden exclusivamente a las **90.559 filas de 13 campos, con todas sus repeticiones**. No mezclar posiciones cortas y largas. Ningún tipo de negocio se convirtió: la representación vigente es texto. Los tipos indicados describen patrones observados, no un esquema SQL aprobado.

Evidencias trazables: [SEMANTIC_VALIDATION.md](SEMANTIC_VALIDATION.md), E01–E10 para observaciones y S01–S07 para fuentes externas. Reproducción de E01–E09: `python -B docs/semantic_profile.py` desde la raíz, solo lectura y biblioteca estándar. El script emite agregados y verifica hashes de datos, src y tests. No muestra filas ni IDs individuales.

Niveles de confianza, aplicados a cada afirmación:

- **CONFIRMADO:** observado exhaustivamente en este archivo, o respaldado por fuente primaria identificada. No implica completitud del comercio ni generalización a otras ediciones.
- **PROVISIONAL:** interpretación compatible con patrones/relaciones; no confirmada por diccionario del proveedor.
- **NO RESUELTO:** no hay evidencia suficiente para decidir el significado o unidad. No equivale a dato falso.

Todos los patrones y conteos de la tabla son CONFIRMADOS localmente. La última columna califica **el significado comercial propuesto**, salvo posición 1, donde solo se confirma su forma temporal. No hay encabezado oficial posicional recuperado. La fuente menciona order_id, pero no identifica su posición en el archivo local.

## Índice de las 13 posiciones

| Pos. | Nombre técnico / alias documental propuesto | Nombre legible provisional | Patrón observado | Vacíos | Distintos no vacíos | Confianza del significado |
|---:|---|---|---|---:|---:|---|
| 1 | field_01 / timestamp_utc | Marca temporal UTC | Texto de 23 caracteres, fecha/hora válida | 0 | 70.702 | CONFIRMADO como timestamp literal; etapa comercial PROVISIONAL |
| 2 | field_02 / order_id_candidate | Identificador de pedido candidato | 19 dígitos ASCII | 0 | 70.933 | PROVISIONAL |
| 3 | field_03 / product_id_candidate | Identificador de producto candidato | 19 dígitos ASCII | 0 | 8.272 | PROVISIONAL |
| 4 | field_04 / quantity_candidate | Constante, cantidad candidata | Texto `1` | 0 | 1 | NO RESUELTO como cantidad |
| 5 | field_05 / category_id_candidate | Identificador de categoría candidato | 19 dígitos ASCII | 0 | 25 | PROVISIONAL |
| 6 | field_06 / category_code_candidate | Código de categoría candidato | Taxonomía textual con punto | 9.933 | 9 | PROVISIONAL; etiquetas literales CONFIRMADAS |
| 7 | field_07 / product_code_unknown | Código de producto sin identificar | Un dígito `0`–`6` o vacío | 4.785 | 7 | NO RESUELTO; marca es una alternativa |
| 8 | field_08 / price_or_amount_candidate | Valor decimal candidato | Texto decimal, exactamente dos cifras decimales | 0 | 3.166 | PROVISIONAL como precio/importe; unidad NO RESUELTA |
| 9 | field_09 / user_id_candidate | Identificador de usuario candidato | 19 dígitos ASCII | 0 | 32.233 | PROVISIONAL; identidad de persona NO RESUELTA |
| 10 | field_10 / product_gender_candidate | Atributo f/m candidato del producto | `f`, `m` o vacío | 42.816 | 2 | PROVISIONAL como atributo; significado de códigos NO RESUELTO |
| 11 | field_11 / color_candidate | Color candidato | Etiquetas textuales | 2.308 | 5 | PROVISIONAL |
| 12 | field_12 / material_candidate | Material candidato | Etiquetas textuales | 110 | 3 | PROVISIONAL |
| 13 | field_13 / stone_candidate | Piedra/ornamentación candidata | Etiquetas textuales | 28.706 | 30 | PROVISIONAL |

## Nulos, ejemplos y reglas comunes

En las 13 posiciones no se observaron cadenas compuestas únicamente de espacios ni tokens completos `null`, `none`, `nan`, `na`, `n/a` (comparación sin distinguir mayúsculas). No hay nulos JSON dentro de `original_fields`, tampoco en las filas cortas: los faltantes representados son `""`. El CSV no tiene un tipo nulo nativo: desconocemos si el vacío significa desconocido, no aplicable o error. Los campos omitidos de las filas cortas son otra clase de ausencia, no cadenas vacías ya localizadas.

Los ejemplos de IDs se enmascaran **por completo** como `[19 dígitos ocultos]`; no se conserva prefijo, sufijo ni clave de correspondencia. La fecha de ejemplo enmascara día/hora. Las etiquetas y valores de ejemplo restantes proceden de dominios o extremos agregados observados; no son filas sintéticas ni combinaciones de un cliente. Enmascaramiento no implica anonimización formal del dataset.

Las reglas propuestas son controles futuros de advertencia o de contrato, **no transformaciones ejecutadas**. Conservar siempre el texto original, vacíos, código cero, multiplicidad y línea. No imponer unicidad individual ni descartar valores sin decisión respaldada.

## Fichas de campo

### 1 — field_01: marca temporal

- Significado/unidad: forma de timestamp con segundos y sufijo literal UTC, CONFIRMADA por parseo completo; que sea fecha de compra, pago, creación o exportación es PROVISIONAL/pendiente. No hay fuente que demuestre la precisión real del reloj.
- Ejemplo enmascarado: `2018-12-** **:**:** UTC`, esquema visual derivado del período observado, no valor para parsear.
- Calidad/patrón: longitud 23; cero vacíos o errores de fecha. Rango global, incluyendo cortas: 2018-12-01 11:40:29 a 2021-12-01 09:59:07 UTC. No es clave única; hay instantes compartidos.
- Regla propuesta: comprobar formato y parseabilidad UTC sin sobrescribir el texto; marcar cambios de cobertura. No sustituir días sin registros por ventas cero ni convertir a fecha de negocio local sin política horaria.
- Evidencia: E02, E03, E07; S01 solo aporta contexto de compras.

### 2 — field_02: pedido candidato

- Significado/unidad: identificador que agrupa ocurrencias; pedido es PROVISIONAL. No tiene unidad aritmética. No hay garantía de unicidad entre fuentes/ediciones.
- Ejemplo: `[19 dígitos ocultos]`. Nunca publicar IDs de pedidos vinculables a usuarios.
- Calidad/patrón: 70.933 distintos en largas; 74.760 globales al incluir cortas. Cada grupo global tiene una única combinación de posición 1 y usuario candidato; cero contradicciones. Un grupo puede contener múltiples productos/filas.
- Regla propuesta: conservar como texto; controlar la dependencia pedido→fecha/usuario por archivo. No usar el ID como clave única de registro ni la cantidad de filas como cantidad de pedidos. No asumir pago completado.
- Evidencia: E02, E04. Falta encabezado oficial S03.

### 3 — field_03: producto candidato

- Significado/unidad: identificador compatible con producto; alcance SKU/modelo/variante NO RESUELTO. No tiene unidad numérica.
- Ejemplo: `[19 dígitos ocultos]`.
- Calidad/patrón: 8.272 distintos largos, 1.341 cortos, 9.613 globales; ningún identificador compartido entre anchuras. En largas, cada ID conserva un solo valor no vacío por atributo de posiciones 5/6/7/10/11/12/13 y un solo valor en 8. Esto no demuestra que se disponga de un maestro completo o de su historia.
- Regla propuesta: texto de 19 dígitos como perfil de esta edición; controlar conflictos sin colapsar variantes. No imputar atributos de las cortas desde largas: no hay coincidencias de ID que sustenten ese join.
- Evidencia: E02, E04, E05.

### 4 — field_04: cantidad candidata, no confirmada

- Significado/unidad: solo se confirma la constante textual `1` en ambas anchuras. Cantidad de unidades, indicador o código son explicaciones posibles; unidad NO RESUELTA.
- Ejemplo observado: `1`.
- Calidad/patrón: cero vacíos y una cardinalidad. Esta falta de variación impide validar que sea cantidad o separar precio unitario de importe de línea mediante multiplicación.
- Regla propuesta: comprobar y reportar nuevos valores; no forzar un entero de negocio ni sumar unidades. La restricción futura cantidad>0 necesita confirmar primero la semántica de devoluciones y cantidades.
- Evidencia: E02, E06; no hay evidencia primaria de nombre/unidad en S03.

### 5 — field_05: categoría ID candidata

- Significado/unidad: código agrupador compatible con una categoría de producto; taxonomía y nivel NO RESUELTOS. ID, no magnitud.
- Ejemplo: `[19 dígitos ocultos]`.
- Calidad/patrón: 25 distintos; 18 tienen algún código no vacío en posición 6, siete no tienen ninguno. Ninguno de esos 18 mapea a más de un código no vacío. En sentido inverso, seis de los nueve códigos se asocian a varios IDs: la etiqueta no es una clave sustituta segura.
- Regla propuesta: preservar ID y etiqueta separados; validar relaciones observadas sin exigir relación uno a uno ni inferir un código para los siete IDs restantes.
- Evidencia: E02, E05.

### 6 — field_06: categoría textual candidata

- Significado/unidad: etiquetas de categorías evidentes por su forma léxica; rol exacto y jerarquía son PROVISIONALES. No tiene unidad.
- Ejemplos de dominio: `jewelry.ring`, `jewelry.earring`, `electronics.clocks`.
- Calidad/patrón: 9.933 vacíos; nueve etiquetas. Conteos largos: earring 29.052; ring 28.300; pendant 13.088; bracelet 6.188; necklace 2.361; brooch 1.288; souvenir 170; stud 12; clocks 167. Son frecuencias de filas, no ventas de productos únicos.
- Regla propuesta: validar etiqueta sin traducir o fusionar valores; alertar etiquetas nuevas. Definir por separado si relojes, souvenirs y código vacío pertenecen al alcance comercial; no excluirlos en esta fase.
- Evidencia: E02; detalle literal reproducible mediante el perfil.

### 7 — field_07: código sin identificar

- Significado/unidad: NO RESUELTO. El alias histórico marca codificada es una hipótesis, no una identificación. No existe catálogo que vincule estos números a marcas, devoluciones, almacenes u otra entidad.
- Ejemplos de códigos agregados: `0`, `1`, `6`; no son nombres de marca ni booleanos confirmados.
- Calidad/patrón: vacío 4.785; código 0: 44.600; 1: 32.022; 2: 8.966; 3: 58; 4: 65; 5: 7; 6: 56. Cada producto candidato largo conserva un único código no vacío.
- Regla propuesta: preservar como etiqueta textual, incluyendo cero. No convertir 0 en nulo ni 0/1 en estado de devolución; no asignar marcas inventadas.
- Evidencia: E02, E05. La estabilidad por producto limita interpretaciones, pero no demuestra una marca.

### 8 — field_08: valor decimal candidato

- Significado/unidad: compatible con precio o importe, PROVISIONAL. Moneda, precio unitario vs línea, bruto/neto, impuestos, descuentos y pago efectivo son NO RESUELTOS.
- Ejemplos agregados de formato: `0.99` y `34448.60`, extremos observados, sin asociarlos a pedidos/clientes.
- Calidad/patrón: cero vacíos, ceros, negativos o no finitos; todas las 90.559 filas tienen dos decimales. 3.166 valores distintos, rango 0,99–34.448,60. Cada uno de los 8.272 productos largos conserva un solo valor decimal en toda la ventana: no hay variación observada dentro de producto.
- Regla propuesta: verificar forma decimal finita sin convertirla en esta fase; alertar extremos y cambios. No aplicar winsorización, redondeos o agregación como ingresos. La constancia por producto es compatible con precio de catálogo o de exportación; no demuestra importe cobrado en cada transacción. No trasladar la regla >0 a posición 6 corta: allí existen ceros y su significado es incierto.
- Evidencia: E02, E05, E06. Ninguna fuente primaria accesible confirma moneda o unidad.

### 9 — field_09: usuario candidato

- Significado/unidad: identificador persistente dentro del archivo compatible con usuario/comprador; persona, cuenta, hogar, dispositivo o seudónimo exacto NO RESUELTOS. Sin unidad aritmética.
- Ejemplo: `[19 dígitos ocultos]`, totalmente enmascarado.
- Calidad/patrón: 32.233 distintos largos. Bajo la correspondencia candidata con posición 7 corta, hay 2.540 distintos cortos y 1.376 compartidos. Un mismo ID aparece en pedidos candidatos diferentes; no demuestra identidad de una persona ni cobertura de todos los clientes.
- Regla propuesta: tratar como identificador seudónimo protegido, texto; verificar estabilidad temporal y reglas de captura antes de contar clientes o calcular recurrencia. No publicar IDs ni vincularlos con fuentes externas.
- Evidencia: E02, E04, E08; S01 declara anonimato del proveedor, no anonimización verificada por PLATHEL.

### 10 — field_10: atributo f/m

- Significado/unidad: compatible con género/segmento objetivo del producto, PROVISIONAL; traducción exacta de f/m NO RESUELTA. No es demografía confirmada del comprador.
- Ejemplos de dominio: `f`, `m`, `""`.
- Calidad/patrón: f 47.379, m 364, vacíos 42.816. Estable por producto en valores no vacíos; 106 usuarios candidatos aparecen con ambos códigos a través de distintas filas.
- Regla propuesta: conservar códigos sin expandirlos ni atribuirlos al usuario; un vacío no implica unisex. La mezcla por usuario contradice asumir un atributo demográfico fijo del cliente, pero no prueba por sí sola el significado del campo.
- Evidencia: E02, E05, E08.

### 11 — field_11: color candidato

- Significado/unidad: compatible con color de producto/material; qué componente describe es NO RESUELTO. Sin unidad.
- Ejemplos de dominio: `red`, `white`, `unknown-color`.
- Calidad/patrón: red 69.511, white 15.286, yellow 3.388, black 2, unknown-color 64; vacíos 2.308. El centinela explícito no es igual al vacío. Valores no vacíos estables por producto.
- Regla propuesta: conservar etiquetas exactas; no convertir red automáticamente en una aleación ni unknown-color en un color conocido. Catálogo futuro y política de desconocidos pendientes.
- Evidencia: E02, E05.

### 12 — field_12: material candidato

- Significado/unidad: compatible con metal/material del producto, PROVISIONAL; composición, pureza, baño, peso o certificación NO RESUELTOS. No contiene una unidad física confirmada.
- Ejemplos de dominio: `gold`, `silver`, `platinum`.
- Calidad/patrón: gold 89.082, silver 1.365, platinum 2; vacíos 110. Estabilidad no vacía por producto.
- Regla propuesta: validar etiquetas, sin inferir quilates, gramos, calidad o valor del metal. No imputar oro por predominio del dominio.
- Evidencia: E02, E05.

### 13 — field_13: piedra/ornamentación candidata

- Significado/unidad: compatible con piedra o decoración del producto, PROVISIONAL; autenticidad, cantidad, talla y origen NO RESUELTOS. Sin unidad numérica.
- Ejemplos de dominio: `diamond`, `fianit`, `mix`, `corundum_synthetic`.
- Calidad/patrón: 30 etiquetas, 28.706 vacíos; diamond 29.610, fianit 12.051, topaz 6.318, pearl 3.632. `mix` aparece 1.479 veces. Estable por producto. No existe evidencia para convertir vacío en ausencia física de piedra, mix en una gema única o para certificar materiales naturales/sintéticos.
- Regla propuesta: conservar literal, sin traducción o fusión irreversible; advertir categorías nuevas y documentar un catálogo solo si se obtiene su significado.
- Evidencia: E02, E05. Dominio completo disponible por reproducción del perfil.

## Filas cortas y metadatos de v1

Las 5.352 filas cortas conservan sus once posiciones originales. No completar ninguna de las 13 fichas con campos cortos por ordinal sin calificar la hipótesis. Correspondencia candidata y alternativas cuantificadas en [SEMANTIC_VALIDATION.md](SEMANTIC_VALIDATION.md#filas-de-11-campos-hipótesis-y-alternativas).

Metadatos CONFIRMADOS por contrato de software: `row_id` identifica una ocurrencia técnica mediante hash del archivo y línea física; no es ID comercial. `source_line`, `source_sha256`, `original_field_count`, `validation_status`, `original_fields`, `raw_text` y `line_ending` son trazabilidad. `positional_fields_13` contiene posiciones largas o null en cortas; ese null significa **alineación no aplicada**, no que todos los valores de la fila sean nulos. `pending_schema_11` no significa compra inválida o cancelada. `structural_13_semantics_unverified` tampoco significa compra completada.

## Condiciones antes de un esquema analítico

Confirmar encabezado y diccionario de esta edición, unidad física y clave de línea, papel de las posiciones 4/7/8/9/10, moneda, estado de transacción y alcance de permisos no resueltos. Mantener todas las ocurrencias hasta resolver repetidos. [ANALYTICS_FEASIBILITY.md](ANALYTICS_FEASIBILITY.md) define qué descripciones técnicas son viables y qué análisis comerciales permanecen condicionados. No se declara completada la validación semántica.

## Consolidación semántica — 2026-10-20

S06 confirma la granularidad declarada por el proveedor: un producto comprado por fila, con productos de una compra vinculados por `order_id`. Esto no convierte el ID técnico en clave de línea comercial ni confirma cantidad, pago o entrega. La asignación de `order_id` a field_02 permanece PROVISIONAL; los nombres posicionales y todos los valores originales siguen intactos.

E10 contrasta {5,6}, {5,7} y {6,7}: las tres hipótesis son compatibles con las 5.352 cortas. Si las omisiones se representan como texto vacío, generan la misma secuencia de valores; difiere la procedencia del vacío. No existe un testigo que permita elegir. S07 no aporta columnas: devuelve `columns: []`. No se autoriza alinear, imputar, deduplicar ni tipar campos comerciales.

Estados por afirmación: CONFIRMADO exige evidencia suficiente y alcance explícito; PROVISIONAL indica interpretación plausible no demostrada; NO RESUELTO indica evidencia insuficiente. Un patrón confirmado no confirma su significado empresarial. Véanse [fuentes](DATA_SOURCES.md), [validación](SEMANTIC_VALIDATION.md) y [escenarios](SEMANTIC_SCENARIOS.md).

### Reproducción independiente del contraste E10

Entradas, reglas, comando PowerShell/Python completo y salida ejecutada se documentan en [Procedimiento reproducible E10](SEMANTIC_VALIDATION.md#procedimiento-reproducible-e10--contraste-de-omisiones). Requiere el original local con su hash; sin dataset no se reproduce. `semantic_profile.py` no ejecuta ese contraste de tres hipótesis. Los candidatos de E10 solo existen en memoria y no modifican la representación v1 ni autorizan alineación.
