# Escenarios y decisiones semánticas

Fecha: 2026-10-20. PLATHEL; Aurelia Jewelry es ficticia. Diseño documental, sin ejecución de cálculos comerciales, transformaciones o modelos. Evidencias E01–E10/S01–S07 en [SEMANTIC_VALIDATION.md](SEMANTIC_VALIDATION.md); criterios por capacidad en [ANALYTICS_FEASIBILITY.md](ANALYTICS_FEASIBILITY.md).

## Escenario A — Información confirmada, condición futura

Actualmente no contamos con el diccionario posicional ni el contrato de extracción. Si el proveedor los entregara, solicitaríamos versión, encabezados por anchura, tipos y unidades, clave de línea, ámbitos de pedido/producto/usuario, estados, fecha comercial, moneda, cantidad, precio/importe, impuestos/descuentos, variantes, multiplicidad, vacíos, cobertura y permisos.

Validaríamos autoría y edición de la documentación contra ID 1005588, versión interna 2873760 y manifiesto/hash del archivo local; nombre y tamaño por sí solos no bastan. Mapearíamos cada posición y anchura sin sobrescribir evidencia. Contrastaríamos dominios, cardinalidades, dependencias, muestras autorizadas conciliadas con origen y explicación de repeticiones/ceros. Repetiríamos controles de conservación, integridad y reconciliación de totales con denominadores explícitos antes de aprobar cambios.

Solo un contrato que explique las cortas podría desbloquear su alineación; solo evidencia sobre líneas/unidades permitiría una política de multiplicidad. Pedido/producto/usuario confirmados y cobertura adecuada podrían habilitar conteos, recompra y cohortes de primera compra observada. Importe/moneda/estados y conciliación podrían habilitar ingresos/ticket/M de RFM. Margen e inventario seguirían requiriendo costos y existencias. Cada capacidad necesita aceptación documentada; recibir un diccionario no aprueba todo el modelo.

## Escenario B — Información insuficiente

Sin documentación adicional siguen siendo confiables el hash del original, las 95.911 ocurrencias, anchuras 90.559/5.352, dominios posicionales, vacíos, timestamps parseables, 2.589 excedentes y trazabilidad v1. Son hechos del archivo, no cantidades de ventas o personas.

Permanecen abiertos posiciones comerciales, cantidad, decimal/moneda, pago, persistencia de identidad, variantes, omisiones y causa de repetidos. Se bloquean ingresos, ticket, RFM completo y conclusiones comerciales definitivas; cohortes/recompra solo admiten diseño condicionado, no métricas validadas. Se conserva original inmutable, hash, línea, original_fields, anchura y estado pendiente; no alinear, imputar ni deduplicar.

Entregables útiles: informe de calidad, diccionario con confianza, catálogo de incertidumbres, contrato propuesto y evaluación de aptitud analítica. A un cliente real solicitaríamos responsable del dato, evidencia de extracción, esquema/versionado, maestros, reglas comerciales, conciliación con sistema fuente, cobertura/estados, política de identidad y permisos. Si no se obtienen, el cierre sería del diagnóstico técnico, no de la aptitud para KPIs.

## Escenario C — Sensibilidad hipotética, no ejecutada

Se diseñarían dos ramas experimentales trazables, sin modificar el original ni elegir una como verdadera:

| Supuesto | Regla conceptual de conteo | Posible efecto |
|---|---|---|
| H1: toda fila idéntica es ocurrencia comercial legítima | Conservar cada ocurrencia | Mantiene el conteo técnico original; no demuestra unidades o ventas |
| H2: toda repetición exacta excedente es error de extracción | Una representación por contenido en una vista experimental | Reduciría el conteo en los excedentes; podría subcontar compras legítimas |

Ejemplo ilustrativo, no registro del dataset: dos alianzas idénticas compradas en un mismo pedido pueden aparecer como dos líneas iguales si talla o identificador de línea no se exportan. H2 colapsaría una compra legítima; H1 podría sobrecontar si hubo duplicación de extracción. Ningún parecido permite decidir la causa.

La futura comparación registraría supuesto, población por anchura, regla de equivalencia, denominador, diferencia y procedencia de cada ocurrencia. Mantendría separadas incertidumbre de multiplicidad y de esquema corto; las tres omisiones equivalentes no discriminan hechos comerciales. No se calculan aquí resultados comerciales ni totales alternativos. No se resuelven automáticamente moneda, importe o cantidad; no se escoge hipótesis, implementa código o construye dashboard.

## Puertas de decisión

1. Revisar evidencia y responsables de cada pendiente P0/P1/P2.
2. Aprobar documentalmente el contrato pertinente por capacidad.
3. Solicitar autorización separada para implementación y pruebas de reconciliación.
4. Habilitar únicamente los resultados cuyos requisitos se hayan satisfecho.

Dictamen vigente: GO CON CONDICIONES para revisión conceptual; NO GO para modelo definitivo o KPIs comerciales. Data Engineering continúa abierto.
