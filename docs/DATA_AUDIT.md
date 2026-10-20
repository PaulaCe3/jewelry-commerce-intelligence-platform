# Primera auditoría técnica de REES46

> Auditoría técnica histórica. Actualización de interpretación al 2026-10-20: prevalecen [SEMANTIC_VALIDATION.md](SEMANTIC_VALIDATION.md) y [DATA_SOURCES.md](DATA_SOURCES.md). S06 confirma granularidad declarada y condiciones publicadas; las posiciones comerciales y la edición local exacta siguen pendientes. Las propuestas antiguas de fact/dimensiones y tipado son antecedentes no aprobados: solo se permite revisión conceptual, sin alineación provisional implementada ni modelo definitivo.


Fecha: 2026-10-19. Proyecto 01 de PLATHEL. Aurelia Jewelry es ficticia y no es propietaria de estos datos.

Revisión posterior de esquema y procedencia, misma fecha: véase la sección final. Complementa la primera auditoría y resuelve parcialmente su pendiente de origen mediante evidencia local del ZIP; el diccionario y la licencia continúan sin verificar.

## Resultado y alcance

Auditoría ejecutada sobre todos los registros locales, sin modificar originales. El archivo es legible, pero **no está listo para calcular indicadores de negocio**: carece de encabezado, mezcla dos anchuras de registro y contiene repeticiones exactas. El diccionario y la licencia específica siguen pendientes. Los nombres semánticos siguientes son hipótesis, no nombres recuperados del archivo.

## Inventario y lectura segura

| Archivo en data/raw | Bytes | Formato observado |
|---|---:|---|
| .gitkeep | 0 | Marcador, sin datos |
| jewelry.csv | 13.617.148 | Texto UTF-8, CSV separado por comas, sin encabezado |

No se encontraron otros archivos ni subdirectorios. La firma inicial es `0A 32 30 31 38`: una línea vacía seguida de una fecha. No es gzip ni ZIP; no requiere extracción. Se leyó íntegramente como UTF-8 con `csv.reader(strict=True)` sin errores de decodificación ni parseo. Hay 95.912 registros CSV: uno vacío inicial y 95.911 no vacíos. No usar detección automática de encabezado ni descartar silenciosamente filas defectuosas.

SHA-256 antes y después, idéntico:

`09d8a61644f66cbb9ad8c50f59180978a0995d121196faf25ef28083dd7b84a2`

Método: Python preexistente en el entorno de auditoría, exclusivamente biblioteca estándar; lectura secuencial, sin DataFrame completo. Se retienen contadores, conjuntos, hashes y precios para controles exactos; memoria proporcional a cardinalidades y registros, adecuada para este archivo de 13,0 MiB. No es una solución de memoria constante para archivos arbitrariamente grandes. No se instalaron dependencias. La comprobación reproducible está en `docs/audit_rees46.py`; ejecutarla desde la raíz con Python. Imprime agregados y no exporta filas ni identificadores. Los controles complementarios de anchura y tokens también se ejecutaron con biblioteca estándar.

## Estructura y columnas

90.559 filas tienen 13 campos (94,42%); 5.352 tienen 11 (5,58%). Ambas estructuras están intercaladas: la primera fila corta es el registro CSV 448 y la última el 95.908. No asumir un cambio de esquema en una sola fecha.

Tabla exclusivamente sobre las 90.559 filas de 13 campos. Vacío significa cadena vacía; no implica que todos los códigos centinela estén identificados. Distintos excluye vacíos.

| Posición | Interpretación provisional | Tipo observado / recomendado | Vacíos | Distintos |
|---|---|---|---:|---:|
| 1 | Fecha de compra | Fecha válida con sufijo UTC / timestamp UTC | 0 | 70.702 |
| 2 | Pedido | Dígitos / string identificador | 0 | 70.933 |
| 3 | Producto | Dígitos / string identificador | 0 | 8.272 |
| 4 | Cantidad | Entero, siempre 1 / entero | 0 | 1 |
| 5 | Categoría ID | Dígitos / string identificador | 0 | 25 |
| 6 | Código de categoría | Texto / string nullable | 9.933 | 9 |
| 7 | Marca codificada | Dígitos / string nullable | 4.785 | 7 |
| 8 | Precio | Decimal finito de hasta 2 decimales / DECIMAL | 0 | 3.166 |
| 9 | Usuario | Dígitos / string identificador | 0 | 32.233 |
| 10 | Atributo de género, entidad por confirmar | f o m / categórico nullable | 42.816 | 2 |
| 11 | Color | Texto / categórico nullable | 2.308 | 5 |
| 12 | Material | Texto / categórico nullable | 110 | 3 |
| 13 | Piedra | Texto / categórico nullable | 28.706 | 30 |

No interpretar el campo 10 como género del comprador: podría describir el producto. Los campos ID 2, 3 y 9 alcanzan 19 dígitos; mantener como texto, nunca float ni Number de JavaScript. La posición 7 contiene `0` en 44.600 filas: su significado no está verificado; no convertirlo automáticamente en nulo.

Las 5.352 filas cortas conservan fecha y dos identificadores en posiciones 1–3 y valor 1 en posición 4. Posiciones 5 y 8–11 están siempre vacías; posición 6 contiene números decimales y posición 7 identificadores numéricos. Es compatible con omisión de campos intermedios, pero **no demuestra cuáles faltan**. No desplazar ni rellenar automáticamente. Si se interpretara posición 6 como precio, 4.392 valores serían cero y el rango sería 0,00–4.876,49; esto es una observación posicional, no un resultado comercial. Deben quedar en cuarentena lógica futura, conservando la referencia al original.

## Fechas, calidad y claves

- Rango global observado: 2018-12-01 11:40:29 UTC a 2021-12-01 09:59:07 UTC; todas las fechas parsearon correctamente. Filas cortas: 2019-01-26 05:51:21 a 2021-12-01 09:47:37 UTC.
- Las filas de 13 campos están ordenadas cronológicamente. Hay 37 meses calendario representados y 14 días sin registros incluso considerando ambas anchuras. No se puede distinguir falta de ventas de falta de captura. Diciembre de 2018 y diciembre de 2021 no deben asumirse meses completos.
- Volumen de filas de 13 campos: diciembre de 2018, 122; diciembre de 2020, 7.384; noviembre de 2021, 8.673; diciembre de 2021, 145. Son conteos de filas sin deduplicar, no ventas ni crecimiento confirmado.
- Duplicados exactos de contenido: 2.298 grupos, con 2.589 filas excedentes (2,70% de las 95.911); 2.469 excedentes en anchura 13 y 120 en anchura 11. Comparación por contenido CSV parseado, no por igualdad de bytes. No se eliminó ninguno. Pueden ser errores o unidades repetidas legítimas; falta una clave de línea que permita resolverlo.
- En anchura 13, `(posición 2, posición 3)` tiene 2.469 repeticiones excedentes, todas explicadas por duplicados exactos. Ni un campo individual ni esa combinación es clave única del original.
- Cada supuesto pedido de anchura 13 se asocia a un único usuario y timestamp: cero conflictos. Cada supuesto producto mantiene un único valor no vacío para categoría ID, código, marca, género, color, material y piedra: cero conflictos en esos atributos. No prueba integridad frente a maestros externos, que no existen localmente.
- En anchura 13 no se encontraron fallos de fecha, enteros no válidos en campos numéricos esperados, precios no finitos, negativos o cero, ni precios con más de dos decimales. Cantidad candidata siempre 1 en ambas anchuras; no hay evidencia de cantidades distintas, devoluciones ni cancelaciones.
- Precio candidato de anchura 13: mínimo 0,99; mediana 258,77; percentil 99 por rango más próximo 1.979,03; máximo 34.448,60. Hay extremos que requieren revisión, no eliminación automática. La suma posicional sin deduplicar es 32.801.847,88: **no equivale a ingresos validados**. Moneda, impuestos, descuentos y semántica de precio pendientes.
- Categorías observadas: jewelry.earring 29.052; jewelry.ring 28.300; jewelry.pendant 13.088; jewelry.bracelet 6.188; jewelry.necklace 2.361; jewelry.brooch 1.288; jewelry.souvenir 170; jewelry.stud 12; electronics.clocks 167. Además, 9.933 códigos vacíos. El alcance joyería requiere decidir sobre relojes y categorías sin código.
- `unknown-color` aparece 64 veces: centinela explícito, distinto de los 2.308 vacíos. Materiales no vacíos: gold 89.082, silver 1.365, platinum 2. No hay catálogo de dominios que permita declarar inválidos los demás valores categóricos.

## Qué representa cada registro

**Fuente externa confirmada:** REES46 clasifica el dataset Jewelry como transacciones/compras. **Observación local:** varias filas comparten posición 2, fecha y usuario y cambian de producto; posición 3 se repite entre pedidos. **Inferencia fundada:** cada fila de 13 campos parece una línea de producto de una compra, no un pedido completo ni una ficha de producto. No existe campo explícito de tipo de evento, encabezado ni ID de línea; por ello la semántica local no está definitivamente verificada. Las filas cortas permanecen sin resolver. No afirmar que hay eventos de navegación, carrito o sesiones.

## Viabilidad analítica

Las cifras siguientes describen únicamente anchura 13, sin resolver duplicados ni garantizar cobertura: 70.933 pedidos candidatos, 8.272 productos candidatos y 32.233 usuarios candidatos. 8.641 usuarios candidatos aparecen en más de un pedido distinto; no es aún una tasa publicada de recompra.

| Análisis | Evaluación |
|---|---|
| Ventas por tiempo / importe | Condicional: confirmar precio, moneda, cantidad, transacción completada y duplicados; no ventas netas |
| Productos, categorías y atributos | Posible descriptivamente en subconjunto de 13 campos, explicitando faltantes y sesgo de exclusión |
| Clientes compradores | Condicional a que posición 9 sea ID persistente de comprador; no padrón total de clientes |
| Recompra | Condicional a validar pedido/usuario, deduplicación y ventana; contar pedidos distintos, no filas |
| Cohortes | Cohortes de primera compra observada, nunca adquisición real; censura por inicio y fin del archivo |
| RFM | Viable solo tras validación: R desde última compra a fecha de corte explícita; F pedidos distintos; M importe validado. No entrenar ML |

No permiten actualmente: conversión, embudos, abandono o sesiones (faltan eventos y visitas); beneficio y margen (costos ausentes); ingresos netos y devoluciones (estado, reembolsos, impuestos y descuentos sin verificar); inventario y rotación real (stocks ausentes); segmentación demográfica o geográfica de clientes (atributos del comprador no confirmados); CAC, ROAS y atribución (marketing y costos ausentes); CLV completo o churn definitivo (historia y seguimiento limitados). Ausencia de columnas explícitas no demuestra ausencia de esos fenómenos en el negocio.

## Modelo inicial propuesto, no implementado

1. Capa de auditoría/staging con archivo, SHA-256, número de registro CSV, anchura y estado de validación; clave técnica `(archivo_hash, número_registro)`. Sin exportar registros al repositorio.
2. `fact_purchase_line`: clave técnica, fecha UTC, pedido candidato, producto candidato, usuario candidato, cantidad y precio DECIMAL. Clave natural de línea pendiente; no imponer pedido-producto como única.
3. `fact_order` derivada solo después de validación, una fila por pedido; controlar consistencia de fecha/cliente antes de sumar.
4. Dimensiones de producto, categoría, comprador seudónimo y fecha. No incluir atributos de producto como demografía del cliente. Preservar observaciones de atributos; no inferir catálogo histórico completo.

Transformaciones siguientes: obtener diccionario y versión; clasificar anchuras; resolver filas de 11 campos contra documentación confiable; normalizar vacíos sin perder centinelas; preservar IDs como string y fechas UTC; definir moneda/precio/cantidad; acordar política de repetidos con evidencia y mantener trazabilidad; definir alcance de categorías; validar agregaciones y cobertura; recién entonces producir derivados locales excluidos de Git y métricas con denominadores explícitos. Ninguna transformación de datos fue aplicada.

## Pendientes y criterio de salida

Confirmar URL de descarga usada por el usuario, versión, fecha de adquisición y transformaciones anteriores; conseguir encabezado/diccionario original; verificar licencia y uso comercial/redistribución; resolver discrepancia de períodos oficiales (ver DATA_SOURCES.md). La auditoría técnica inicial está ejecutada; la validación semántica y de derechos sigue abierta. No hay bloqueo para leer el archivo, pero sí para interpretar automáticamente las filas cortas y publicar métricas comerciales definitivas.

## Revisión de esquema, procedencia y repetidos — 2026-10-19

### Evidencia local de edición

Se inspeccionó el flujo NTFS `Zone.Identifier` del CSV, que referencia el archivo ZIP de adquisición. Se localizó ese archivo exacto y se leyó su directorio ZIP sin extraerlo: contiene únicamente `jewelry.csv`, de 13.617.148 bytes (2.730.788 comprimidos; CRC32 `d38d9e33`). El SHA-256 del miembro leído secuencialmente coincide con el original local: `09d8a61644f66cbb9ad8c50f59180978a0995d121196faf25ef28083dd7b84a2`. Esto demuestra identidad del contenido con el ZIP local; los defectos de estructura y las repeticiones ya están en ese contenido, no fueron introducidos por una limpieza del CSV dentro del proyecto.

El `Zone.Identifier` del ZIP contiene referente Kaggle y una ruta de descarga con dataset ID `1005588` y versión interna `2873760`. Detalle y URL sin parámetros firmados en DATA_SOURCES.md. No se verificó un número público de versión ni checksum remoto. La ficha candidata es la oficial de Jewelry enlazada por REES46; no se confirmó mediante API la asociación de su slug con esos IDs. La evidencia no permite asegurar que el archivo esté completo respecto de otra edición publicada.

### Muestra y controles estructurales

Se examinó una muestra determinista de 21 filas: tres por cada combinación existente de anchura y año, mediante reservoir sampling con semilla `20261019`. Incluye 12 de anchura 13 (2018–2021) y nueve de anchura 11 (2019–2021). Es una muestra estratificada para comparar estructura, no una estimación estadística de calidad o de ventas. Los resultados se corroboraron sobre las 95.911 filas, no se extrapolaron desde la muestra. No se guardaron registros individuales ni identificadores en la documentación.

Patrones observados, expresados solo como tipos:

- 13 campos: fecha UTC; ID numérico; ID numérico; entero 1; ID numérico; categoría textual o vacío; código numérico o vacío; decimal; ID numérico; atributo f/m o vacío; color o vacío; material o vacío; piedra o vacío.
- 11 campos, patrón uniforme: fecha UTC; ID numérico; ID numérico; entero 1; vacío; decimal; ID numérico; vacío; vacío; vacío; vacío.

Comprobación exhaustiva por líneas físicas y `csv.reader(strict=True)`: las 90.559 filas largas tienen exactamente 12 comas y las 5.352 cortas, 10; ninguna tiene comillas dobles, punto y coma o tabulador. Cada línea no vacía es un registro CSV; no hay campos multilínea que expliquen las diferencias. Los vacíos delimitados se conservan, no son colapsados por el lector. Las 5.352 posiciones 6 cortas cumplen el patrón decimal con dos cifras, sin negativos.

**Explicaciones evaluadas:**

| Explicación | Evidencia y evaluación |
|---|---|
| Dos campos finales omitidos | No explica el patrón: precio e ID ya aparecen en posiciones 6 y 7 en vez de 8 y 9. Añadir dos vacíos al final mantendría el desplazamiento |
| Otro delimitador o comillas mal interpretadas | Descartado para este archivo por inspección exhaustiva de caracteres y parseo |
| Vacíos convencionales | Existen, pero un vacío conserva su posición entre comas; no explica la pérdida de dos posiciones |
| Omisión de dos campos intermedios en la exportación | Hipótesis estructural más consistente; el bloque previo al precio tendría un campo en vez de tres |
| Error del productor, otro esquema o registros sin metadatos de producto | Compatibles con las observaciones, sin documentación que permita distinguir la causa |

La alineación más defendible conserva las posiciones 1–4 y desplaza 6–11 de las cortas a 8–13 del esquema largo. Su posición 5 vacía ocuparía alguna de las posiciones 5–7 largas. **No puede determinarse cuál**, ni si los dos campos ausentes son precisamente categoría ID/código o alguna otra combinación dentro de ese bloque. Las cuatro posiciones finales cortas existen y son vacías: no están simplemente truncadas.

Evidencia adicional: 999 pedidos candidatos contienen filas de ambas anchuras. En los 999 coinciden exactamente fecha y usuario al comparar posición 7 corta con posición 9 larga; cero conflictos. De las 5.352 filas cortas, 3.951 tienen en posición 7 un valor ya presente en posición 9 de las largas; son 1.376 valores distintos compartidos sobre 2.540 distintos cortos. Ningún producto candidato aparece en ambas anchuras: la estructura está asociada al producto en el archivo observado. Esto apoya ausencia de metadatos del producto, pero no prueba su causa. Las cortas se distribuyen en 116 filas de 2019, 198 de 2020 y 5.038 de 2021; no es un único bloque temporal.

### Esquema propuesto y confianza

**Confirmado localmente:** posiciones, tipos, dominios observados, vacíos y relaciones comprobadas. **No confirmado oficialmente:** ningún nombre de columna, el significado exacto del importe, la moneda o la condición de compra completada. Confianza alta significa evidencia local consistente, no validación del proveedor.

| Campo propuesto | Posición larga / corta | Confianza y límite |
|---|---|---|
| `event_time` o fecha de compra | 1 / 1 | Alta para timestamp UTC; nombre y etapa comercial pendientes |
| `order_id` | 2 / 2 | Alta: agrupación por una fecha y un usuario, incluso entre anchuras; ID comercial pendiente |
| `product_id` | 3 / 3 | Alta: repetición entre pedidos y atributos estables; SKU/variante exacta pendiente |
| `quantity` | 4 / 4 | Media: siempre 1, podría ser otra constante; falta diccionario |
| `category_id` | 5 / indeterminada | Alta como categoría candidata en filas largas; alineación corta sin resolver |
| `category_code` | 6 / indeterminada | Alta por taxonomía literal en filas largas; nombre oficial pendiente |
| `brand_id` | 7 / indeterminada | Media-baja: códigos estables por producto, pero significado y cero desconocidos |
| `price` | 8 / 6 | Alta como importe candidato por tipo y alineación; precio unitario, total, moneda y ceros pendientes |
| `user_id` o `customer_id` | 9 / 7 | Alta por coincidencia entre anchuras y relación con pedido; persistencia real del cliente pendiente |
| atributo de género | 10 / 8 | Media como atributo del producto; no validado como dato del comprador |
| color / material / piedra | 11–13 / 9–11 | Alta para dominios en largas, alineación estructural en cortas; nombres oficiales pendientes |

Sobre todo el archivo, usando únicamente esa correspondencia candidata de fecha/usuario, hay 74.760 pedidos candidatos y cero con más de una combinación fecha-usuario. La combinación pedido-producto sigue sin ser clave única; para trazabilidad se necesita archivo/hash y número de registro. La ausencia de productos compartidos entre anchuras impide recuperar sus atributos mediante un join al subconjunto largo.

### Distribución de repeticiones exactas

Se volvió a comprobar igualdad del texto de las líneas excluyendo solo el terminador de línea; el resultado coincide con el análisis CSV anterior: **2.589 excedentes**, 2.298 grupos y 4.887 filas involucradas. Se conservaron todas las ocurrencias. Excedente significa suma de `(ocurrencias - 1)` por grupo.

| Ocurrencias por grupo | Grupos | Excedentes |
|---:|---:|---:|
| 2 | 2.064 | 2.064 |
| 3 | 179 | 358 |
| 4 | 53 | 159 |
| 5 | 2 | 8 |
| Total | 2.298 | 2.589 |

| Año | Filas de 13 / 11 campos | Excedentes de 13 / 11 campos |
|---|---:|---:|
| 2018 | 122 / 0 | 4 / 0 |
| 2019 | 11.985 / 116 | 455 / 1 |
| 2020 | 26.948 / 198 | 833 / 9 |
| 2021 | 51.504 / 5.038 | 1.177 / 110 |

Hay repeticiones en 35 meses, desde diciembre de 2018 hasta octubre de 2021; no se observaron excedentes en noviembre ni diciembre de 2021. Máximos mensuales de excedentes: agosto de 2021, 189 (135 largas + 54 cortas); abril de 2021, 172; mayo de 2021, 158. Son conteos absolutos, no tasas comparables sin considerar volumen.

Distribución de excedentes por categoría de las largas: anillos 2.275; código vacío 96; pulseras 59; collares 26; pendientes/pendants (`jewelry.pendant`) 5; earrings 4; broches 2; relojes 2. Otros 120 pertenecen a cortas sin categoría alineada. Anillos representan 87,87% de todos los excedentes. Se involucran 2.230 pedidos candidatos y 583 productos candidatos en ambas anchuras.

Entre ocurrencias consecutivas del mismo contenido, 2.588 intervalos son de una línea y uno de dos líneas. **Inferencia:** agrupación casi totalmente contigua y concentración en anillos son compatibles con unidades repetidas del mismo producto o variantes no representadas (por ejemplo, talla), además de posibles duplicaciones de exportación o joins. No prueban ninguna causa. La ausencia de ID de línea, talla y documentación de cantidad impide distinguirlas. No hay evidencia para atribuir los 2.589 a reintentos, pedidos cancelados o errores sistemáticos; tampoco para considerarlos necesariamente ventas adicionales. Deduplicar automáticamente podría subestimar unidades e importes.

### Recomendación y verificaciones finales

Se puede preparar una limpieza **estructural conservadora**, tras su autorización, manteniendo cada ocurrencia, número de registro y anchura original, con campos posicionales y banderas de revisión. No aprobar todavía una limpieza semántica definitiva: no reparar cortas con columnas finales, eliminar repetidos, imputar categorías, convertir cero a nulo ni consolidar ingresos/RFM sin documentar esas decisiones. Para las cortas puede proponerse alineación provisional con bandera explícita, nunca como esquema confirmado.

El acceso web estuvo disponible para REES46, pero la ficha y API de Kaggle no entregaron documentación legible; el intento de acceso HTTP directo desde Python fue bloqueado por restricciones de red y el navegador integrado no pudo iniciarse. Esto limita la verificación de diccionario y licencia, no significa que no existan. El notebook del autor encontrado publica una licencia de código Apache 2.0; **no verifica la licencia del dataset**. No se usaron análisis de terceros como diccionario oficial.

Solo se actualizan DATA_AUDIT.md y DATA_SOURCES.md en esta revisión, conforme a la solicitud. No se alteró el script anterior; este no reproduce los controles adicionales de esta sección, ejecutados como comprobaciones locales con biblioteca estándar. No se descargaron datos, extrajeron archivos, instalaron dependencias ni escribieron derivados. Hash del CSV antes/después idéntico al registrado arriba.
