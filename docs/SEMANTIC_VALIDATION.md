# Validación semántica — evidencia, hipótesis y pendientes

Actualización: 2026-10-20; perfil original: 2026-10-19. Proyecto 01 de PLATHEL. **Validación semántica parcial, no cerrada.** La aprobación del software v1 no confirma significados de negocio. Aurelia Jewelry es ficticia y no representa al proveedor de los datos.

## Estado vigente y método

Prevalece la consolidación del 2026-10-20 al final de este documento: se recuperaron metadatos primarios, granularidad declarada y condiciones de atribución; persisten bloqueos posicionales y comerciales. El registro inicial se conserva como historial de consultas, no como conclusión actual.

## Método y evidencia reproducible

Se leyeron AGENTS.md, README.md, DATA_AUDIT.md, DATA_SOURCES.md, PIPELINE.md, STATUS.md y DECISIONS.md. Se recorrió el CSV completo y se inspeccionaron los metadatos y estados de todos los objetos normalizados, exclusivamente en lectura. No se ejecutó el pipeline ni se cambiaron src/tests/datos. Las 39 pruebas aprobadas son evidencia de la fase QA anterior, **no pruebas reejecutadas en esta fase documental**.

Reproducción desde la raíz, Python preexistente, sin dependencias adicionales:

```powershell
python -B docs/semantic_profile.py
```

Se utilizó un intérprete Python preexistente, sin instalar herramientas. El comando terminó con código 0. El script solo emite agregados; no exporta IDs o registros. Usa contadores y conjuntos en memoria proporcional a cardinalidades/textos, sin cargar un DataFrame completo. La lectura decimal y temporal sirve para comprobar patrones, no convierte ni escribe tipos de datos del proyecto. No calcula KPIs comerciales.

| Evidencia | Fuente local y comprobación | Resultado |
|---|---|---|
| E01 | CSV, hashes de datos/src/tests antes y después | CSV 13.617.148 bytes; SHA-256 coincide con auditoría. 15 archivos protegidos sin cambios, incluidos marcadores/cachés preexistentes |
| E02 | Contadores por posición separados por anchura | 90.559 filas largas y 5.352 cortas; cardinalidades, dominios y vacíos del diccionario. Cero tokens de nulo y cadenas de solo espacios |
| E03 | Parseo de posición 1 en todas las filas | 0 errores; 2018-12-01 11:40:29 a 2021-12-01 09:59:07 UTC; 14 fechas calendario sin registros |
| E04 | Agrupación de posiciones 2/3 y usuario candidato | 74.760 grupos de posición 2; 0 con combinaciones fecha/usuario contradictorias; 999 grupos compartidos entre anchuras con coincidencia exacta |
| E05 | Dependencias no vacías por producto largo | 0 productos con atributos conflictivos en 5/6/7/10/11/12/13; 0 con más de un valor de posición 8. Relaciones categoría ID/código no son uno a uno |
| E06 | Dominio de posición 4 y patrón decimal en 8 larga / 6 corta | Constante 1; importes candidatos con dos decimales. Hay 4.392 ceros en 6 corta y ninguno en 8 larga |
| E07 | Contador de líneas originales sin terminador; auditoría previa con mismo hash | 2.298 grupos y 2.589 excedentes exactos. Auditoría previa: 2.275 excedentes en anillos, casi todos contiguos; ninguna eliminación |
| E08 | Relación usuario candidato con códigos f/m | 106 IDs de posición 9 larga con ambos códigos; el atributo no vacío es estable por producto |
| E09 | Lectura completa de records.jsonl y quality.json | 95.911 objetos, 90.559/5.352; 0 nulos dentro de original_fields y 0 cortas alineadas. Todas las filas siguen pendientes de semántica |

Identidad del CSV: `09d8a61644f66cbb9ad8c50f59180978a0995d121196faf25ef28083dd7b84a2`.

Hash de records.jsonl: `5eef0df67a63c918b23a5d01627d6debfd88937c7f499e5b4bc25322bbff63e8`. Hash de quality.json: `d58407f19d6f3727866ce2ec7674756da7a1a96624f0f5aac74e4c070fefe129`.

Manifiesto protegido del perfil, SHA-256 sobre el JSON de rutas relativas y hashes ordenados: `d3d3c600ab51320103cb7a3c146b0610f6f499f8ec093dd30ea5a579ce7dec67`. Depende de rutas y cachés de esta instalación; es control de no modificación en esta máquina, no identificador portable del dataset.

## Registro histórico de investigación primaria — 2026-10-19

Las consultas S01–S05 de la fase inicial corresponden a **2026-10-19**. Internet estuvo disponible mediante la herramienta web para REES46. Kaggle no entregó documentación suficiente; no se infiere de ello que la documentación no exista. No se descargaron datasets ni se consultaron historiales de navegación o credenciales.

| ID | URL y acceso | Qué respalda / qué no respalda |
|---|---|---|
| S01 | [Catálogo REES46](https://data.rees46.com/), contenido recuperado | Contexto de compras de tienda de joyería, período publicado diciembre de 2018–diciembre de 2021, oferta jewelry-purchases.csv.gz y afirmación del proveedor de datos anónimos. No da un diccionario de 13 posiciones, moneda o licencia específica verificables |
| S02 | [Datasets REES46](https://rees46.com/en/datasets), contenido recuperado | Clasificación Jewelry como transacciones y enlace a Kaggle. Publica noviembre de 2018–noviembre de 2020, distinto de S01 y del archivo local |
| S03 | [Ficha Kaggle candidata](https://www.kaggle.com/datasets/mkechinov/ecommerce-purchase-history-from-jewelry-store), sin texto recuperable | No permitió confirmar encabezado, diccionario, moneda, licencia ni número público de versión. No constituye confirmación de ningún nombre de campo |
| S04 | Ruta Kaggle de descarga registrada localmente, véase DATA_SOURCES.md | Evidencia local heredada del ZIP con dataset ID 1005588 y versión interna 2873760; miembro idéntico al CSV. No confirma correspondencia remota de slug, edición pública o integridad frente a otras versiones |
| S05 | [Notebook del autor](https://www.kaggle.com/code/mkechinov/starter-ecommerce-purchase-history-overview), resultado indexado; página sin contenido de código recuperable | Referencia al dataset y licencia Apache 2.0 del notebook. No es licencia del dataset ni encabezado oficial recuperado |

Reintentos específicos de S03, sin contenido utilizable:

- [Ruta legacy metadata](https://www.kaggle.com/mkechinov/ecommerce-purchase-history-from-jewelry-store/metadata).
- [Ruta legacy data](https://www.kaggle.com/mkechinov/ecommerce-purchase-history-from-jewelry-store/data).
- [API de metadatos](https://www.kaggle.com/api/v1/datasets/view/mkechinov/ecommerce-purchase-history-from-jewelry-store).
- [Datos del notebook](https://www.kaggle.com/code/mkechinov/starter-ecommerce-purchase-history-overview/data).

Las búsquedas dirigidas de columnas y licencia también devolvieron material de otros datasets y análisis de terceros. No se usaron como diccionario ni autorización de uso. En particular, documentación de eventos multicategoría de REES46 no se traslada a compras de joyería; ni USD ni event_type/user_session se incorporan por analogía.

**Estado histórico al 2026-10-19, sustituido parcialmente por S06/S07:** licencia y redistribución pendientes. No se recuperaron términos específicos verificables de la edición interna 2873760; no se ha demostrado ni autorización ni prohibición concreta de redistribución. La disponibilidad gratuita no resuelve ese punto. La prohibición de publicar datos del proyecto permanece. No hay una aprobación jurídica nueva.

## Filas de 11 campos: hipótesis y alternativas

Hechos E02/E04/E06, confirmados en las 5.352 filas:

| Posición corta | Forma observada | Correspondencia larga candidata |
|---:|---|---|
| 1 | Timestamp UTC, sin vacíos | 1 |
| 2 | ID de 19 dígitos, 4.826 distintos | 2 |
| 3 | ID de 19 dígitos, 1.341 distintos | 3 |
| 4 | Constante textual 1 | 4 |
| 5 | Vacío en todas las filas | Alguna de 5/6/7, sin identificar |
| 6 | Decimal con dos cifras; 209 distintos | 8, candidato |
| 7 | ID de 19 dígitos, 2.540 distintos | 9, candidato |
| 8–11 | Cuatro posiciones presentes, todas vacías | 10–13, candidato |

**A favor de omisión intermedia:** precio/ID candidatos se adelantan dos posiciones. De las cortas, 3.951 filas tienen en posición 7 un valor visto en 9 larga; 1.376 IDs distintos se comparten entre ambas posiciones. En los 999 grupos de pedido compartidos, las combinaciones de fecha y usuario coinciden en todos los casos: cero contradicciones. No hay productos candidatos presentes en ambas anchuras, consistente con un patrón ligado a disponibilidad de metadatos del producto. Esto último no identifica un error de exportación concreto.

**Alternativas no resueltas:** bajo la hipótesis de orden conservado, la posición 5 vacía podría ser la categoría ID larga, el código de categoría o el código de posición 7. Las omisiones compatibles serían respectivamente `{6,7}`, `{5,7}` o `{5,6}`. Esas tres posibilidades reproducen los mismos vacíos observados; no hay un valor testigo que discrimine entre ellas. También es posible un esquema distinto o un problema previo de exportación. La correspondencia candidata no constituye demostración del esquema completo ni de la causa.

**Alternativas descartadas por estructura local:**

- Solo faltan dos campos al final: no explica por qué los decimales e IDs ya están en posiciones 6/7. Rellenar al final conserva el desplazamiento equivocado.
- Delimitador diferente/comillas: todas las largas tienen 12 comas y las cortas 10; no hay comillas, punto y coma ni tabuladores. El parser conserva vacíos y no colapsa separadores.
- Un único cambio de esquema temporal: las cortas se distribuyen en 116 filas de 2019, 198 de 2020 y 5.038 de 2021, intercaladas con largas. La muestra inicial y el recorrido completo no apoyan una frontera única.

**Contrapesos y límites:** 960 filas cortas tienen decimal candidato no cero, 4.392 tienen 0,00. Rango 0,00–4.876,49. Son valores posicionales; no significan transacciones gratuitas, errores, regalos o devoluciones confirmadas. Los otros 1.401 registros cortos tienen un ID candidato no visto entre largas; esto no invalida un posible usuario nuevo. La ausencia de productos compartidos impide comprobar/recuperar sus atributos contra largas. Las últimas cuatro columnas cortas vacías no permiten confirmar su orden semántico.

**Resultado:** 5.352 filas pendientes, cero alineaciones nuevas. El pipeline y los outputs aprobados permanecen intactos. Obtener encabezado/especificación de exportación para esta edición o evidencia del productor que distinga las tres alternativas; mientras tanto, conservar posiciones separadas por anchura.

## Semántica comercial y contradicciones

| Interpretación | Evidencia a favor | Límite / contradicción / estado |
|---|---|---|
| Fecha de evento en 1 | Forma timestamp UTC y relación con grupo 2 | La etapa del proceso no está documentada. Timestamp literal CONFIRMADO, fecha de compra PROVISIONAL |
| Pedido en 2 | Agrupa productos con fecha/usuario único; coherencia global | No hay estado, total ni diccionario. PROVISIONAL; no garantiza pedido pagado ni clave global |
| Producto en 3 | Reutilización y atributos estables; 9.613 IDs globales | Modelo vs SKU vs talla/variante no identificado. PROVISIONAL |
| Cliente en 9 larga / 7 corta | Coincidencias cruzadas y repetición entre grupos | Podría identificar cuenta/dispositivo; persistencia y persona desconocidas. PROVISIONAL como usuario, NO RESUELTO como cliente-persona |
| Cantidad en 4 | Siempre 1 | También compatible con indicador/código; ninguna variación ni encabezado para contrastar. NO RESUELTO |
| Precio unitario vs importe de línea en 8 | Decimales positivos; compatible con compras | Con cantidad candidata siempre 1, ambas interpretaciones son observacionalmente indistinguibles. Valor fijo por producto es compatible con catálogo/exportación, no prueba importe pagado. NO RESUELTO cuál de las dos, ni bruto/neto |
| Moneda | No hay columna ni declaración accesible de esta edición | No inferir USD por formato decimal, país del proveedor u otros datasets. NO RESUELTO |
| Categoría ID/código | Léxico y dependencias estables | Etiqueta no es clave única de ID; códigos vacíos y relojes requieren alcance. PROVISIONAL |
| Marca en 7 | Código estable por producto | Dominio 0–6 no tiene decodificador. Tampoco prueba estado de devolución. NO RESUELTO |
| f/m como demografía de comprador | Solo parecido léxico | 106 usuarios con ambos códigos y estabilidad por producto; no utilizar como demografía. Atributo de producto PROVISIONAL, código exacto NO RESUELTO |
| Color/material/piedra | Dominios léxicos y estabilidad | Componente descrito, certificación, pureza, origen y unidades físicas desconocidos. PROVISIONAL |
| Devoluciones/cancelaciones | No hay campo de estado identificado; no se observan valores negativos en decimales candidatos | Ausencia de negativos no demuestra ausencia de devoluciones; podrían faltar o usar otra codificación. NO RESUELTO |
| Ocurrencia de compra/producto | S01/S02 dicen compras/transacciones; grupo 2 contiene productos | Línea de pedido es PROVISIONAL. Unidad, evento de compra, línea comercial y copia de exportación no se distinguen definitivamente |

### Repeticiones y granularidad

Se confirman 2.589 excedentes de contenido exacto conservados. DATA_AUDIT.md registra 2.469 en largas y 120 en cortas, grupos de dos a cinco ocurrencias y concentración en anillos (2.275 excedentes). Coinciden con el mismo hash fuente; el perfil vuelve a confirmar el total y los 2.298 grupos. El patrón admite unidades repetidas, variantes no representadas o duplicación de exportación/joins; ninguna causa queda demostrada. No hay talla ni ID de línea identificado que permita resolverlo.

La granularidad técnica inequívoca es **ocurrencia física no vacía del archivo**, con un ID técnico único creado por v1. S06 confirma además la granularidad declarada de producto comprado, sin identificar unidad ni clave de línea comercial. Ni `(pedido candidato, producto candidato)` ni el timestamp es clave única comercial de la fuente. No existe evidencia para declarar un excedente «error» o «otra venta». Conservar multiplicidades; no imputar cantidades ni colapsar registros. Un recuento de ocurrencias no se debe titular unidades vendidas.

## Calidad, cobertura y privacidad

- Los vacíos más relevantes de largas son 42.816 en f/m, 28.706 en piedra, 9.933 en código de categoría y 4.785 en código desconocido. No representan porcentajes de todos los 95.911 registros. Las cortas tienen un patrón de ausencia diferente, potencialmente no aleatorio.
- Hay 14 días sin registros entre extremos: 2018-12-24/26/29, 2019-01-01/02 y 2020-05-03 a 2020-05-11 inclusive. No se conoce si son cierres comerciales, falta de captura o falta de compras. La cobertura de los meses extremos no puede asumirse completa.
- Excluir cortas afectaría especialmente 2021 (5.038 de 5.352 cortas) y ciertos productos. Un análisis sobre largas debe declarar ese sesgo y nunca presentarse como total completo de la tienda.
- Categoría vacía no es una categoría conocida; unknown-color no equivale a color vacío; cero de posición 7 no es nulo confirmado. Etiquetas de piedra no son certificaciones. Precio extremo no es error confirmado.
- IDs de usuario/pedido y timestamps precisos pueden permitir vinculación de comportamiento; se tratan como seudónimos y potencialmente sensibles. S01 declara datos anónimos, pero PLATHEL no verificó irreversibilidad ni riesgo de reidentificación.
- No se identificaron columnas explícitas de nombre, email, teléfono o dirección; esto no certifica anonimato. El campo f/m podría ser sensible si se vincula indebidamente a una persona. No realizar esa inferencia ni unir IDs a terceros.
- Los documentos no contienen filas completas, IDs de usuarios/pedidos ni URL de descarga firmada. Ejemplos técnicos enmascaran IDs íntegros y tiempo; resultados solo agregados. Datos y trazabilidad se mantienen locales y excluidos de Git según reglas del proyecto.

## Preguntas pendientes y evidencia necesaria

| Prioridad | Pregunta que bloquea interpretación | Evidencia mínima para resolverla |
|---|---|---|
| Alta | ¿Cuál es el encabezado y número público de versión del bundle 1005588/2873760? | Metadatos/ficha primaria de esa versión o documentación aportada con origen verificable |
| Alta | ¿Qué campos faltan en las cortas? | Especificación de exportación o encabezado aplicable que distinga las tres alternativas, no un simple ajuste de anchura |
| Alta | ¿Qué son 4 y 8, y cuál es la moneda? | Definición de cantidad/precio/importe, unidad monetaria, impuestos/descuentos y etapa del pedido |
| Alta | ¿Las ocurrencias repetidas son unidades, variantes o errores? | ID de línea o especificación de granularidad y exportación; no basta igualdad textual |
| Alta | ¿Qué permisos de uso/redistribución aplican? | Licencia específica de la edición y condiciones adicionales verificables |
| Media | ¿Qué representa/persiste el ID de usuario y cuándo se asigna? | Documentación de identidad, ventana histórica y cambios/reinicio de IDs |
| Media | ¿Qué son 7 y 10 y cómo se interpretan los vacíos? | Catálogo de códigos y definiciones del proveedor; no mappings de terceros |
| Media | ¿La captura es completa y qué estados incluye? | Política de cobertura, devoluciones/cancelaciones y límites temporales |

## Resultado y alcance del GO

**GO CON CONDICIONES exclusivamente para revisión conceptual y diseño exploratorio documentado.** No se autoriza ni se ejecuta implementación analítica. **NO GO para fijar un modelo físico/dimensional definitivo, tipado de negocio o publicar KPIs de ventas, ticket, clientes o RFM**, hasta cerrar los bloqueos de semántica correspondientes. El catálogo documental está construido; la validación semántica de métricas comerciales sigue abierta.

La matriz de viabilidad y el modelo conceptual preliminar están en [ANALYTICS_FEASIBILITY.md](ANALYTICS_FEASIBILITY.md). Los nombres y estados deben interpretarse junto con [DATA_DICTIONARY.md](DATA_DICTIONARY.md); una observación CONFIRMADA de formato no transforma una interpretación PROVISIONAL en nombre oficial.

## Consolidación vigente — 2026-10-20

Esta sección incorpora la investigación de solo lectura ya realizada; no repite descargas, no cierra Data Engineering y no modifica v1. E01–E09 conservan su alcance y sus fechas. Las pruebas históricas de software no validan semántica.

| ID | Fuente / método | Conclusión y estado | Límite |
|---|---|---|---|
| S06 | [API oficial view de Kaggle](https://www.kaggle.com/api/v1/datasets/view/mkechinov/ecommerce-purchase-history-from-jewelry-store), respuesta JSON recuperada en la investigación del 2026-10-20 | CONFIRMADO: dataset ID 1005588, slug del autor mkechinov, versión pública actual 2, actualización 2021-12-01T10:03:33.553Z. Declara producto comprado por fila y agrupación por order_id; publica uso gratuito y atribución a ficha/REES46 | No identifica posiciones, moneda, estado de pago o clave de línea; no vincula expresamente versión interna 2873760 con versión pública 2 |
| S07 | [API oficial list de archivos](https://www.kaggle.com/api/v1/datasets/list/mkechinov/ecommerce-purchase-history-from-jewelry-store) | CONFIRMADO: jewelry.csv de 13.617.148 bytes; descripción vacía y columns vacío | Coincidencia de tamaño no sustituye checksum remoto ni confirma edición local exacta |
| E10 | Contraste independiente con csv.reader y biblioteca estándar sobre todo el original; SHA-256 antes/después | CONFIRMADO: 95.911 ocurrencias, anchuras 90.559/5.352, 2.589 excedentes; las tres hipótesis compatibles en 5.352 casos y con igual secuencia al representar omisiones como vacío | No demuestra causa de omisión ni legitimidad comercial de repeticiones; comparación de investigación previa y reproducida mediante el procedimiento E10 de este documento, sin reparación |

### Matriz de decisiones semánticas

| Afirmación | Estado | Evidencia | Pendiente / límite |
|---|---|---|---|
| Una fila es un producto comprado, según proveedor | CONFIRMADO como declaración de fuente | S06 | Unidad física, línea única, pago y entrega NO RESUELTOS |
| Posiciones 2/3/9 son pedido/producto/usuario | PROVISIONAL | E04/E05 y contexto S06 | Encabezado, ámbito de IDs y persistencia; no personas confirmadas |
| Posición 4 es cantidad | NO RESUELTO | E06: constante 1 | Diccionario y contrato de extracción |
| Decimal 8 larga / 6 corta es dinero cobrado | NO RESUELTO | E05/E06: fijo por producto largo; ceros cortos | Precio catálogo/unitario/línea, moneda, impuestos, descuentos y estados |
| Posición 7 es marca; f/m es demografía | NO RESUELTO | E05/E08 | No asignar marca; evidencia favorece atributo de producto, no demografía |
| 2.589 excedentes son errores | NO RESUELTO | E07/E10: igualdad de contenido | ID de línea, unidades/variantes y mecanismo de extracción |
| Identidad del dataset Kaggle 1005588 | CONFIRMADO dentro de la cadena de procedencia | S04/S06 | Metadato NTFS no es certificación del proveedor |
| Edición local equivale a versión pública 2 | PROVISIONAL | S04/S06/S07 y tamaño coincidente | Mapeo 2873760→2 o manifiesto/checksum remoto |
| Condiciones publicadas de uso gratuito y atribución | CONFIRMADO | S06; etiqueta Data files © Original Authors | No resuelve expresamente redistribución, sublicencia o incorporación a producto comercial |

### Tres hipótesis de omisión sin selección

| Posiciones largas omitidas | Posición larga del campo corto 5 vacío | Compatibles |
|---|---:|---:|
| {5,6} | 7 | 5.352 |
| {5,7} | 6 | 5.352 |
| {6,7} | 5 | 5.352 |

Las tres preservan 1–4 y proponen C6→P8 y C7→P9, apoyadas por 999 grupos mixtos sin contradicción de fecha/usuario. Al insertar vacíos, el bloque 5–7 queda vacío en las tres; no se identifica qué posición estaba presente. Otro esquema o defecto previo de exportación sigue siendo posible. No hay productos compartidos entre anchuras para completar atributos. Los controles de caracteres descartan comillas y delimitadores alternativos en el archivo observado, no errores anteriores a su exportación.

### Bloqueos priorizados y criterio de salida

1. **P0 — contrato de datos:** encabezado posicional por anchura, clave de línea, reglas de cantidad/repetición y extracción. Impacta todos los conteos, relaciones de Power BI y variables de Data Science.
2. **P0 — contrato monetario:** moneda, significado del decimal, impuestos/descuentos, estados y fecha de reconocimiento. Bloquea ingresos, ticket y M de RFM.
3. **P1 — identidad y cobertura:** cuenta/persona/dispositivo, persistencia, SKU/variante, límites temporales, 14 fechas sin registros y concentración de cortas en 2021. Condiciona cohortes, recompra y evaluación temporal.
4. **P1 — permisos:** precisar usos externos adicionales antes de explotación/redistribución; no publicar registros aunque cambien los permisos.
5. **P2 — atributos:** decodificadores de 7 y 10–13, categorías y vacíos. Condiciona surtido y segmentación interpretable.

GO CON CONDICIONES solo para revisión conceptual documental. NO GO para modelo físico/dimensional definitivo, KPIs comerciales, dashboards o modelos predictivos. Los escenarios y requisitos de desbloqueo se definen en [SEMANTIC_SCENARIOS.md](SEMANTIC_SCENARIOS.md); viabilidad por capacidad en [ANALYTICS_FEASIBILITY.md](ANALYTICS_FEASIBILITY.md). La validación semántica continúa abierta.

## Procedimiento reproducible E10 — contraste de omisiones

**Entrada:** archivo local autorizado `data/raw/jewelry.csv`, sin encabezado, con el SHA-256 indicado en el comando. Ejecutar desde la raíz con Python 3.11 o superior y biblioteca estándar, sin instalar dependencias. El dataset no se distribuye: un clon sin él no puede reproducir E10; necesita acceso legítimo al mismo archivo local. No se descarga automáticamente.

**Pasos y reglas:**

1. Calcular SHA-256 por bloques y detenerse si difiere del original auditado.
2. Leer secuencialmente con `csv.reader(strict=True)`; contar registros vacíos, anchuras y contenido exacto parseado. Excedente es la suma de ocurrencias menos uno por contenido; no se elimina nada.
3. Para cada fila de 11 campos, construir exclusivamente en memoria tres candidatos que insertan texto vacío en {5,6}, {5,7} o {6,7} (base 1). Preservar los once campos en orden. No escribir ni reemplazar registros.
4. Contrastar conservación de campos retenidos, prefijo 1–4, tramo C6–C11→P8–P13 y bloque P5–P7 vacío. Contar compatibilidad por hipótesis y candidatos con valores idénticos entre las tres.
5. Recalcular hash, emitir únicamente agregados y exigir los resultados esperados. Error de lectura, hash o conteos produce salida distinta de cero; no certifica una nueva edición.

La equivalencia compara **valores bajo una representación experimental de omisión como vacío**. No identifica el origen de esos vacíos ni prueba la causa del esquema corto; no valida nombres comerciales ni selecciona una hipótesis. Se mantiene `pending_schema_11`. Memoria proporcional al contenido distinto retenido por Counter, no memoria constante; no se carga un DataFrame.

**Comando PowerShell reproducible** (sustituir `python` por el ejecutable preexistente si corresponde; `-B` evita generar cachés):

```powershell
@'
from collections import Counter
import csv
import hashlib
from pathlib import Path

source = Path("data/raw/jewelry.csv")
expected = "09d8a61644f66cbb9ad8c50f59180978a0995d121196faf25ef28083dd7b84a2"
def sha256(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            result.update(block)
    return result.hexdigest()

before = sha256(source)
if before != expected:
    raise SystemExit("ERROR: source hash differs from audited file")
widths, occurrences = Counter(), Counter()
hypotheses = ((5, 6), (5, 7), (6, 7))
compatible = Counter()
blank = same_values = unexpected = 0
with source.open(encoding="utf-8", newline="") as stream:
    for row in csv.reader(stream, strict=True):
        if not row:
            blank += 1
            continue
        widths[len(row)] += 1
        occurrences[tuple(row)] += 1
        if len(row) not in (11, 13):
            unexpected += 1
            continue
        if len(row) != 11:
            continue
        candidates = []
        for omitted in hypotheses:
            fields = iter(row)
            candidate = tuple("" if position in omitted else next(fields)
                              for position in range(1, 14))
            retained = tuple(candidate[position - 1]
                             for position in range(1, 14)
                             if position not in omitted)
            fits = (retained == tuple(row)
                    and candidate[:4] == tuple(row[:4])
                    and candidate[7:] == tuple(row[5:])
                    and candidate[4:7] == ("", "", ""))
            compatible[omitted] += int(fits)
            candidates.append(candidate)
        same_values += int(candidates[0] == candidates[1] == candidates[2])
excess = sum(count - 1 for count in occurrences.values())
after = sha256(source)
if before != after:
    raise SystemExit("ERROR: source hash changed")
print("rows=" + str(sum(widths.values())))
print("blank_records=" + str(blank))
print("width_13=" + str(widths[13]))
print("width_11=" + str(widths[11]))
print("unexpected_widths=" + str(unexpected))
print("duplicate_excess=" + str(excess))
for omitted in hypotheses:
    print("compatible_" + "_".join(map(str, omitted)) + "=" + str(compatible[omitted]))
print("same_values_all_three=" + str(same_values))
print("source_sha256=" + before)
print("source_unchanged=" + str(before == after))
if not (widths == Counter({13: 90559, 11: 5352}) and blank == 1
        and unexpected == 0 and excess == 2589 and same_values == 5352
        and all(compatible[h] == 5352 for h in hypotheses)):
    raise SystemExit("ERROR: aggregates differ from documented evidence")
'@ | python -B -
```

**Salida obtenida en esta corrección documental, código de salida 0:**

```text
rows=95911
blank_records=1
width_13=90559
width_11=5352
unexpected_widths=0
duplicate_excess=2589
compatible_5_6=5352
compatible_5_7=5352
compatible_6_7=5352
same_values_all_three=5352
source_sha256=09d8a61644f66cbb9ad8c50f59180978a0995d121196faf25ef28083dd7b84a2
source_unchanged=True
```

No se guardaron datos ni candidatos. Este comando se ejecutó mediante el intérprete preexistente con `-B -`, pasando exactamente el bloque Python por stdin. No se ejecutó normalización ni cálculo comercial.

**Diferencia respecto de `semantic_profile.py`:** ese script reproduce E01–E09 (perfil, dependencias candidatas, metadatos v1 y hashes protegidos). No implementa el bucle de tres omisiones ni el contador de equivalencia E10. El comando anterior reproduce E10 de forma independiente, sin importar funciones del pipeline o del perfil. No sustituye las pruebas QA ni demuestra pago, cantidad o moneda.
