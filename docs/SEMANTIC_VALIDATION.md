# Validación semántica — evidencia, hipótesis y pendientes

Fecha: 2026-10-19. Proyecto 01 de PLATHEL. **Validación semántica parcial, no cerrada.** La aprobación del software v1 no confirma significados de negocio. Aurelia Jewelry es ficticia y no representa al proveedor de los datos.

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

## Registro de investigación primaria

Todas las consultas externas de esta fase corresponden a **2026-10-19**. Internet estuvo disponible mediante la herramienta web para REES46. Kaggle no entregó documentación suficiente; no se infiere de ello que la documentación no exista. No se descargaron datasets ni se consultaron historiales de navegación o credenciales.

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

**Licencia y redistribución:** pendientes. No se recuperaron términos específicos verificables de la edición interna 2873760; no se ha demostrado ni autorización ni prohibición concreta de redistribución. La disponibilidad gratuita no resuelve ese punto. La prohibición de publicar datos del proyecto permanece. No hay una aprobación jurídica nueva.

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
| Fecha de evento en 1 | Forma timestamp UTC y relación con grupo 2 | La etapa del proceso no está documentada. Timestamp literal CONFIRMADO, fecha de compra INFERIDA |
| Pedido en 2 | Agrupa productos con fecha/usuario único; coherencia global | No hay estado, total ni diccionario. INFERIDO; no garantiza pedido pagado ni clave global |
| Producto en 3 | Reutilización y atributos estables; 9.613 IDs globales | Modelo vs SKU vs talla/variante no identificado. INFERIDO |
| Cliente en 9 larga / 7 corta | Coincidencias cruzadas y repetición entre grupos | Podría identificar cuenta/dispositivo; persistencia y persona desconocidas. INFERIDO como usuario, NO VERIFICADO como cliente-persona |
| Cantidad en 4 | Siempre 1 | También compatible con indicador/código; ninguna variación ni encabezado para contrastar. NO VERIFICADO |
| Precio unitario vs importe de línea en 8 | Decimales positivos; compatible con compras | Con cantidad candidata siempre 1, ambas interpretaciones son observacionalmente indistinguibles. Valor fijo por producto es compatible con catálogo/exportación, no prueba importe pagado. NO VERIFICADO cuál de las dos, ni bruto/neto |
| Moneda | No hay columna ni declaración accesible de esta edición | No inferir USD por formato decimal, país del proveedor u otros datasets. NO VERIFICADO |
| Categoría ID/código | Léxico y dependencias estables | Etiqueta no es clave única de ID; códigos vacíos y relojes requieren alcance. INFERIDO |
| Marca en 7 | Código estable por producto | Dominio 0–6 no tiene decodificador. Tampoco prueba estado de devolución. NO VERIFICADO |
| f/m como demografía de comprador | Solo parecido léxico | 106 usuarios con ambos códigos y estabilidad por producto; no utilizar como demografía. Atributo de producto INFERIDO, código exacto NO VERIFICADO |
| Color/material/piedra | Dominios léxicos y estabilidad | Componente descrito, certificación, pureza, origen y unidades físicas desconocidos. INFERIDO |
| Devoluciones/cancelaciones | No hay campo de estado identificado; no se observan valores negativos en decimales candidatos | Ausencia de negativos no demuestra ausencia de devoluciones; podrían faltar o usar otra codificación. NO VERIFICADO |
| Ocurrencia de compra/producto | S01/S02 dicen compras/transacciones; grupo 2 contiene productos | Línea de pedido es INFERIDA. Unidad, evento de compra, línea comercial y copia de exportación no se distinguen definitivamente |

### Repeticiones y granularidad

Se confirman 2.589 excedentes de contenido exacto conservados. DATA_AUDIT.md registra 2.469 en largas y 120 en cortas, grupos de dos a cinco ocurrencias y concentración en anillos (2.275 excedentes). Coinciden con el mismo hash fuente; el perfil vuelve a confirmar el total y los 2.298 grupos. El patrón admite unidades repetidas, variantes no representadas o duplicación de exportación/joins; ninguna causa queda demostrada. No hay talla ni ID de línea identificado que permita resolverlo.

La única granularidad inequívoca es **ocurrencia física no vacía del archivo**, con un ID técnico único creado por v1. Ni `(pedido candidato, producto candidato)` ni el timestamp es clave única comercial de la fuente. No existe evidencia para declarar un excedente «error» o «otra venta». Conservar multiplicidades; no imputar cantidades ni colapsar registros. Un recuento de ocurrencias no se debe titular unidades vendidas.

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

La matriz de viabilidad y el modelo conceptual preliminar están en [ANALYTICS_FEASIBILITY.md](ANALYTICS_FEASIBILITY.md). Los nombres y estados deben interpretarse junto con [DATA_DICTIONARY.md](DATA_DICTIONARY.md); una observación CONFIRMADA de formato no transforma una interpretación INFERIDA en nombre oficial.
