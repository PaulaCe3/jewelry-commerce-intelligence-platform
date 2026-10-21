# Aurelia sintética v2 — devoluciones y reembolsos

Aurelia Jewelry es ficticia. Esta simulación original de PLATHEL no contiene datos reales ni utiliza Olist/REES46. Los saldos son aritmética contractual sintética, no ingresos contables, beneficio ni resultados empresariales observados. Data Engineering sigue abierto.

## Compatibilidad y arquitectura

Implementación aditiva: `src/aurelia/v2.py`, CLI `python -B -m src.aurelia.v2`. Los módulos, CLI, contratos, documentación de contrato y pruebas de v1 permanecen intactos. v2 reutiliza el generador, cargador y utilidades v1; no cambia sus constantes ni estructuras globales.

Un conjunto v2 contiene `base/` (manifest.json y los tres JSONL v1 idénticos a generar v1 con la misma semilla/cantidad), manifest.json v2, returns.jsonl y refunds.jsonl. El manifiesto v2 fija `aurelia-synthetic-v2`, synthetic=true, creator=PLATHEL, semilla, escenario, hash del manifiesto base y hashes/conteos de ajustes. No se admiten propiedades extra, claves JSON duplicadas ni constantes no finitas.

La base v2 es un **snapshot nuevo**, PRAGMA user_version=2. Se reconstruye la base v1 dentro de staging privado, se exige ACCEPTED y se añaden tablas de ajustes transaccionalmente. Todas las tablas históricas v1 se conservan exactamente; se usa otra dimensión de fechas para no añadir filas a dim_date histórica. No se migra ni abre para escritura una base v1 persistida. La comparación con un destino existente exige esquema y todas las tablas iguales; otro contenido o versión se rechaza sin sobrescribirlo. El CLI v1 sigue operando sobre sus conjuntos/bases v1 y no admite silenciosamente v2.

## Contratos nuevos y granularidad

Los campos son obligatorios, salvo que su valor deba ser null según el estado. No hay float; enteros estrictos (bool no admitido), positivos y <=10^9 para item_no, payment_no, cantidades e importes. Currency=USD. IDs sintéticos string; return_id usa SIM-R- seguido de dígitos y refund_id SIM-F- seguido de dígitos. IDs técnicos de staging: hash del archivo:entidad:línea, independientes del ID contractual del evento.

| Entidad | Campos | Granularidad y relaciones |
|---|---|---|
| returns | return_id, order_id, item_no, quantity, status, requested_at, received_at, currency | Un registro de devolución de una línea; return_id único; FK (order_id,item_no) al artículo original de pedido PAID |
| refunds | refund_id, order_id, payment_no, return_id nullable, reason, status, requested_at, completed_at, amount_cents, currency | Un registro de reembolso de un pago; refund_id único; FK (order_id,payment_no) a pago CAPTURED de pedido PAID; enlace opcional a devolución |

Timestamp canónico UTC textual `YYYY-MM-DDTHH:MM:SSZ`. Toda solicitud debe ser posterior o igual a ordered_at; cierre posterior o igual a solicitud. v1 no proporciona fecha del evento de captura: no se inventa ni se valida una cronología captura→reembolso que esa fuente no permite demostrar.

**Devolución física:** estados REQUESTED, RECEIVED, REJECTED. received_at es obligatorio solo en RECEIVED; en los otros estados debe ser null. REQUESTED y RECEIVED reservan cantidad; solo RECEIVED cuenta como unidades devueltas. Cada evento nominal y la suma reservada por artículo no pueden superar quantity original. REJECTED no reserva ni cuenta como recibido. No se modifica cantidad vendida histórica.

**Reembolso financiero:** estados REQUESTED, COMPLETED, FAILED. completed_at es obligatorio solo en COMPLETED; en otros estados debe ser null. REQUESTED y COMPLETED comprometen capacidad monetaria, evitando sobreautorizar pendientes; solo COMPLETED reduce el saldo capturado. FAILED no reserva ni reduce saldo, pero su importe nominal individual debe respetar los máximos del pago y de la devolución enlazada, si existe. Los montos siempre son positivos; no se representan ajustes mediante importes negativos en ventas.

**Motivos y autorización v2:**

- RETURN exige return_id existente, RECEIVED y del mismo pedido. requested_at del reembolso debe ser >=received_at. Cada intento nominal y la suma comprometida vinculada a la devolución deben ser <=quantity recibida × precio unitario original. No se añaden impuestos, envío o descuentos a ese derecho.
- GOODWILL exige return_id=null. La política sintética permite compensar sin devolución física, hasta los límites financieros restantes. No se asigna ese importe a ningún producto ni se atribuye margen o costo.
- Cada intento nominal debe ser <=importe del pago capturado al que apunta; el comprometido acumulado por pago y por pedido no supera lo capturado originalmente. Los controles por pedido y devolución complementan el límite por pago. Una diferencia de un centavo causa rechazo, sin redondeo o tolerancia.
- Permitir GOODWILL no constituye una aprobación de un empleado real. Es una regla de autorización propia de la simulación; no hay roles/aprobaciones operativas, prueba de recepción logística ni certificación bancaria.

Se mantienen USD, centavos enteros e impuestos/descuentos/envío cero de v1. No se crean devoluciones de pedidos OPEN/CANCELLED, cambio de moneda, contracargos, reemplazos, reposición de inventario, impuestos legales, comisiones ni reconocimiento contable.

## Staging, integración y hechos separados

| Tabla nueva | Propósito |
|---|---|
| adjustment_batch / adjustment_source | Versión, estado explícito, manifiesto, hashes y conteos de archivos |
| adjustment_staging / adjustment_rejection | Texto exacto con terminador, línea e ID técnico; reglas de rechazo verificables |
| int_return / int_refund | Eventos validados y claves originales; FK a artículo/pago y al staging |
| dim_adjustment_date | Fechas de solicitud/recepción/completado en distintos roles, sin alterar dim_date v1 |
| dim_return_status / dim_refund_status | Estados observados del contrato |
| fact_return | Una fila por return_id; claves pedido/artículo, fechas solicitud/recepción, estado, received_units, reserved_units y received_value_cents |
| fact_refund | Una fila por refund_id; claves pedido/pago, fechas solicitud/completado, estado, posted_cents y committed_cents |

El enlace opcional refund→return se conserva en int_refund y es validado, no se utiliza para multiplicar hechos. `received_value_cents` es un techo contractual de mercancía recibida, no un reembolso realizado. No se distribuyen reembolsos entre artículos. Un pedido puede tener varios artículos, devoluciones, pagos y reembolsos; nunca se construye un join de detalles múltiples para sumar importes.

Si algún ajuste falla, **todo el lote de ajustes se publica REJECTED**, con staging y motivos completos, cero int_return/int_refund/fact_return/fact_refund. Las operaciones base válidas siguen presentes e intactas en el nuevo snapshot. No se informa como un lote aceptado: build devuelve código 1. Los registros con JSON inválido también son trazables. Si falla manifiesto, hash, conteo, lectura o construcción, no se publica base nueva, pues no hay evidencia confiable para aceptar el lote.

Publicación por enlace duro exclusivo tras commit y cierre; no se sobrescriben destinos diferentes. Repetir valida y reconstruye en privado y compara esquema y todas las tablas, incluidas las de ajustes; devuelve unchanged sin cambiar bytes. Los hashes de fuentes se vuelven a calcular antes de aceptar. Un fallo de inserción o publicación deja el destino previo intacto; staging temporal propio se limpia al salir normalmente.

## Conciliación implementada

Tres vistas evitan fan-out mediante agregaciones independientes:

1. `payment_adjustment_reconciliation`: una fila por pago, con original capturado, posted_refund_cents, committed_refund_cents, net_captured_cents=original−completados y available_refund_cents=original−comprometidos.
2. `item_return_reconciliation`: una fila por artículo, con unidades originales, recibidas, reservadas y disponibles=originales−reservadas.
3. `order_adjustment_reconciliation`: una fila por pedido; agrega pagos y unidades por separado antes de unirlos a la cabecera.

Los pendientes reducen capacidad disponible pero no el saldo capturado neto; los fallidos no reducen ninguno. Saldo neto no es beneficio ni ingreso. El detalle de una devolución no se cruza con todos los reembolsos del pedido. La suma de posted_cents no usa SUM(DISTINCT), porque reembolsos legítimos pueden tener el mismo importe.

```sql
SELECT order_id, original_captured_cents, posted_refund_cents,
       committed_refund_cents, net_captured_cents, returned_units
FROM order_adjustment_reconciliation ORDER BY order_id;
SELECT * FROM payment_adjustment_reconciliation WHERE available_refund_cents < 0;
SELECT * FROM item_return_reconciliation WHERE available_return_units < 0;
SELECT rule,COUNT(*) FROM adjustment_rejection GROUP BY rule;
```

En un snapshot aceptado las dos consultas de límites deben estar vacías. El ejemplo negativo deliberado en pruebas cruza artículos y reembolsos del primer pedido: suma errónea 2.700 frente a 900 centavos completados correctos. Es prueba del error, no consulta habilitada.

## Ejecución reproducible

Desde la raíz, Python >=3.11 preexistente y biblioteca estándar; sin instalación ni acceso a red:

```powershell
python -B -m src.aurelia.v2 generate --output data/aurelia/v2-normal-seed42 --seed 42 --orders 30
python -B -m src.aurelia.v2 build --input data/aurelia/v2-normal-seed42 --database data/aurelia/warehouse-v2-normal.sqlite
python -B -m src.aurelia.v2 query --database data/aurelia/warehouse-v2-normal.sqlite --query summary
python -B -m src.aurelia.v2 query --database data/aurelia/warehouse-v2-normal.sqlite --query orders
python -B -m src.aurelia.v2 query --database data/aurelia/warehouse-v2-normal.sqlite --query items
python -B -m src.aurelia.v2 query --database data/aurelia/warehouse-v2-normal.sqlite --query payments

python -B -m src.aurelia.v2 generate --output data/aurelia/v2-adverse-seed42 --seed 42 --orders 30 --adverse
python -B -m src.aurelia.v2 build --input data/aurelia/v2-adverse-seed42 --database data/aurelia/warehouse-v2-adverse.sqlite
python -B -m src.aurelia.v2 query --database data/aurelia/warehouse-v2-adverse.sqlite --query rejections

python -B tests/run_aurelia_v2_suite.py
python -B tests/run_aurelia_suite.py
python -B tests/run_suite.py
python -B tests/run_evidence_suite.py
```

El conjunto adverso debe devolver 1 y status=REJECTED. Consultas correctas devuelven 0, argumentos inválidos 2. El generador exige directorio nuevo; para repetir usar solo build/query o cambiar el destino de generación. Sustituir python por el ejecutable disponible si corresponde. No ejecutar dentro de un entorno que deniegue crear/subdividir temporales: usar los permisos normales autorizados, sin cambiar ACL de datos históricos.

El generador conserva límites y semilla de v1: 6–10.000 pedidos, uint32. Siempre incluye devolución parcial del primer pedido, completa del segundo sin reembolso, varios reembolsos iguales/parciales, pendientes/fallidos y compensación total sin recepción del tercero. Con el caso estándar semilla 42/30 añade también devolución parcial de una línea con quantity>1; esa variante depende de que exista una línea mult(unidad) elegible en el snapshot base, no se altera v1 para fabricarla. Otros tamaños/semillas pueden no incluir esa variante específica, aunque el contrato y pruebas la soportan.

## Pruebas, límites y evolución

Las nuevas pruebas no necesitan datasets reales. Comparan todas las tablas v1 dentro de una base v2 con una construcción v1 independiente y verifican que v2 no sobrescribe una base v1. Cubren archivos base idénticos, semillas, reconstrucción de staging, integridad, casos completos/parciales, límites individuales/acumulados y al centavo, pendientes, fallidos, estados/fechas/FK, fan-out, atomicidad con fallo tras inserciones y publicación final, idempotencia, alteración de destino, manifiestos y CLI. No hay omisiones como aprobación; los runners previos se ejecutan aparte.

Cada return_id/refund_id aparece una sola vez con su estado en el snapshot. No hay actualización incremental, historial de transiciones o procesamiento de mensajes; una nueva imagen acumulada exige otro destino y debe incluir todos los ajustes pertinentes. La integridad interna no prueba que una fuente haya omitido eventos. No se ofrece concurrencia de escritores, crash recovery físico ni durabilidad del directorio ante corte eléctrico; se requieren enlaces duros, espacio para staging y memoria proporcional a registros. Son límites explícitos, no garantías de producción.

Resultados realmente ejecutados y cualquier restricción de acceso REES46 se conservan en [STATUS.md](STATUS.md). v1 mantiene su [contrato histórico](AURELIA_DW.md). Próximo incremento recomendado: ingesta incremental de eventos con transiciones e idempotencia por evento, manteniendo ledger y límites acumulados; no implementado aquí. No commit/push ni publicación de datos bajo esta entrega.
