# Aurelia Jewelry — Data Warehouse sintético v1

Aurelia Jewelry es una empresa ficticia. Todos los datos de esta línea son sintéticos, originales de PLATHEL y generados desde reglas propias; no se copian filas ni se ajustan distribuciones a REES46 u Olist. Los importes y resultados siguientes describen exclusivamente una simulación, nunca ventas observadas, desempeño real o ingresos contables.

## Separación y arquitectura

| Línea | Código / pruebas | Artefactos locales |
|---|---|---|
| REES46 | src/normalize_jewelry.py, src/evidence_sqlite.py y suites previas, sin modificaciones | data/raw, data/processed, data/evidence, sin escrituras nuevas |
| Aurelia sintética | src/aurelia y tests/test_aurelia_dw.py; runner independiente | data/aurelia, íntegramente excluido de Git |

Biblioteca estándar de Python >=3.11; SQLite incluido, sin instalación ni servicios adicionales. No hay imports entre las dos líneas. Olist queda descartado como fuente del portfolio comercial en esta etapa; no se descarga ni incorpora material suyo. Se mantiene la validación semántica abierta de REES46. Este incremento implementa solo la simulación contractual propia, no habilita métricas sobre datos reales.

Flujo funcional: **generación determinista → manifiesto/hashes → staging transaccional → validación → integración → hechos separados y dimensiones → conciliación**. Un lote con rechazos conserva staging completo y motivos, pero no integra ninguna fila. Un fallo operativo no publica base nueva.

## Contrato `aurelia-synthetic-v1`

Tres archivos UTF-8 JSONL, un objeto por registro. Claves exactas, sin propiedades adicionales ni claves JSON repetidas. Cada archivo tiene cantidad y SHA-256 en manifest.json; también se exige versión, creator=PLATHEL, synthetic=true, semilla y escenario. El manifiesto describe una simulación, no certifica autenticidad externa.

| Entidad / granularidad | Propiedades y tipos | Clave y reglas |
|---|---|---|
| Pedidos: una cabecera por pedido | order_id: string `SIM-O-` seguido de dígitos; ordered_at: timestamp UTC textual canónico `YYYY-MM-DDTHH:MM:SSZ`; status: OPEN/PAID/CANCELLED; currency: USD; expected_cents: integer no negativo | order_id único; al menos un artículo; expected_cents igual a suma quantity × unit_price_cents |
| Artículos: una línea por pedido | order_id: string; item_no: integer positivo; product_code: SIM-RING/SIM-EARRING/SIM-PENDANT; quantity y unit_price_cents: integer positivo | (order_id,item_no) única; FK pedido; dos líneas del mismo producto o importe pueden ser legítimas |
| Pagos: un registro por intento/componente de pago | order_id: string; payment_no: integer positivo; status: CAPTURED/FAILED; amount_cents: integer positivo | (order_id,payment_no) única; FK pedido; un pedido puede tener varios registros y cantidades monetarias iguales |

Campos enteros de negocio limitados a 10^9 por campo; bool no es entero válido. Al exigir conciliación, los pedidos aceptados con artículos positivos tienen expected_cents positivo. IDs y dimensiones son propios de la simulación y no se vinculan a personas reales.

**Reglas monetarias explícitas:** USD, centavos enteros, sin float ni conversión de moneda. Un centavo es 1/100 USD; no hay redondeo de cálculo. `line_amount_cents = quantity × unit_price_cents`. El total esperado es mercancía antes de considerar pago, no ingreso. Para PAID, la suma de pagos CAPTURED debe igualar el total esperado; OPEN y CANCELLED no pueden tener ningún cobro CAPTURED. FAILED conserva el importe intentado, pero contribuye cero a capturado. Una diferencia de un centavo rechaza el lote; no hay tolerancia implícita.

**Fuera de v1:** impuestos, descuentos, costos de envío y sus importes son cero por definición de esta simulación; no se calculan ni simulan impuestos legales. Devoluciones, reembolsos, capturas parciales de pedidos abiertos, comisiones, costos, margen, tipo de cambio, clientes, PII e inventario no están representados. CANCELLED significa sin cobro capturado en este snapshot, no una devolución ni una transición histórica. No se infieren eventos anteriores.

Cardinalidades contractuales: pedido 1:N artículos, con N>=1; pedido 1:0..N pagos. Producto 1:N artículos. No hay relación directa de pago a artículo. No se asignan cobros a productos ni se inventa fecha de pago: la fecha dimensional del hecho de pagos es explícitamente **fecha del pedido**.

## Generador y escenarios

Semilla uint32 configurable, generador local random.Random, versión de contrato fija; cantidad configurable de 6 a 10.000 pedidos. Determinismo comprobado con el mismo entorno Python y parámetros. No se garantiza identidad entre futuras versiones de generador/runtime sin volver a probarla. No existen timestamps de ejecución ni rutas personales en los artefactos.

El primer pedido garantiza tres artículos de 1.000 centavos (cantidad 1 cada uno) y dos pagos CAPTURED de 1.500 centavos. Esto permite detectar tanto fan-out como el error de SUM(DISTINCT). Los demás casos incluyen varios estados, cantidades y pagos fallidos/ausentes, según reglas propias. No se pretende representatividad estadística de un comercio real.

`--adverse` genera otro directorio con duplicado de clave, moneda inválida, cantidad negativa, referencia huérfana e importe no conciliado. Nunca cambia el conjunto normal. El error de una cabecera puede producir rechazos ORPHAN adicionales: los conteos de reglas no equivalen a número de filas distintas rechazadas.

## Staging, atomicidad y rechazos

- `batch`: versión, identidad del lote por hashes, manifiesto original y estado ACCEPTED/REJECTED; synthetic=1.
- `source_file`: entidad, hash y cantidad declarada del archivo.
- `stg_record`: ID técnico hash:entidad:línea, entidad, línea y texto fuente exacto con terminador. Conserva todas las ocurrencias, incluso repetidas o JSON inválido.
- `rejection`: ID técnico, regla y motivo, con FK a staging. Cada motivo es trazable a un registro original.
- `int_order`, `int_item`, `int_payment`: datos contractuales tipados y FK al ID técnico de staging; solo existen filas si el lote entero pasa validación.

Claves duplicadas, JSON inválido, campos/tipos/dominios inválidos, huérfanos, ausencia de artículos y diferencias monetarias generan rechazos verificables. Cero integración/hechos para cualquier lote REJECTED; no se aceptan subconjuntos. Un manifiesto/hash/archivo incompatible es error de entrada: aborta sin publicar una base y no inventa un rechazo de fila cuya procedencia no pudo verificarse.

El build crea staging SQLite privado con BEGIN IMMEDIATE y foreign_keys=ON; valida integridad y hashes de entrada nuevamente antes de commit. Publica mediante enlace duro exclusivo después de cerrar la base. Exige destino separado de fuentes y de carpetas REES46. Un destino existente se compara por esquema y todas las tablas contra una construcción nueva; si es idéntico retorna unchanged sin modificar sus bytes, si difiere se rechaza sin sobrescribirlo. Una base contiene un snapshot/lote, no es una carga incremental multibatch.

La generación también usa un directorio temporal y publica un directorio nuevo. Usar un solo escritor por destino; no se ofrece coordinación entre procesos ni resistencia a cambios hostiles concurrentes. Fallos de construcción limpian su staging propio; un cierre abrupto puede dejar temporales ignorados y no aceptables como salidas finales. Se requieren permisos normales y soporte de enlaces duros. No se promete durabilidad del directorio ante corte de energía; no se simulan ACL físicas ni disco realmente lleno.

## Modelo dimensional mínimo

| Tabla | Granularidad / claves / medidas |
|---|---|
| fact_item | Una fila por (order_id,item_no), FK a int_item, fecha del pedido, producto y estado; quantity y line_amount_cents |
| fact_payment | Una fila por (order_id,payment_no), FK a int_payment, fecha del pedido, estado de pedido/pago; recorded_amount_cents y captured_amount_cents |
| dim_date | Una fecha UTC de pedido; clave ISO y año/mes/día |
| dim_product | Un código de producto sintético observado |
| dim_order_status | Un estado de pedido observado |
| dim_payment_status | Un estado de pago observado |

order_id es dimensión degenerada para conectar con la cabecera integrada; no se construye un hecho ancho que cruce detalles de pagos y artículos. Dimensiones sin SCD: no existe historia de cambios para justificarla. Moneda constante USD del contrato, sin dimensión adicional innecesaria.

La vista `order_reconciliation` agrega cada hecho por order_id y después une ambos agregados a la cabecera. Permite comparar esperado/artículos/capturado sin multiplicación. `simulated_paid_item_cents` incluye artículos de pedidos PAID; `simulated_captured_cents` excluye pagos FAILED. Son importes contractuales sintéticos; ninguno se denomina ingreso contable.

## Comandos ejecutables desde la raíz

Si python no está en PATH, sustituirlo por un intérprete Python >=3.11 ya disponible. No hay pip install. Los directorios fuente deben ser nuevos; las bases admiten recarga idéntica.

```powershell
python -B -m src.aurelia generate --output data/aurelia/normal-seed42 --seed 42 --orders 30
python -B -m src.aurelia build --input data/aurelia/normal-seed42 --database data/aurelia/warehouse-normal.sqlite
python -B -m src.aurelia query --database data/aurelia/warehouse-normal.sqlite --query summary
python -B -m src.aurelia query --database data/aurelia/warehouse-normal.sqlite --query reconciliation

python -B -m src.aurelia generate --output data/aurelia/adverse-seed42 --seed 42 --orders 30 --adverse
python -B -m src.aurelia build --input data/aurelia/adverse-seed42 --database data/aurelia/warehouse-adverse.sqlite
python -B -m src.aurelia query --database data/aurelia/warehouse-adverse.sqlite --query rejections

python -B tests/run_aurelia_suite.py
python -B tests/run_suite.py
python -B tests/run_evidence_suite.py
```

El build adverso debe devolver código **1** y JSON status=REJECTED: es el resultado esperado, no una ejecución aprobada. La base de rechazos se conserva intencionalmente sin hechos. Consultarla devuelve 0 si la consulta funciona. Éxito normal: 0; argumentos inválidos: 2. Errores operativos/contrato: 1, sin volcar rutas personales. Las consultas abren bases en modo read-only/query_only; nunca crean una base ausente.

## Consultas y prueba de doble conteo

SQL ilustrativo implementado/probado sobre la simulación; no consulta ninguna fuente real:

```sql
SELECT order_id,status,expected_cents,item_cents,captured_cents,
       item_difference_cents,payment_difference_cents
FROM order_reconciliation ORDER BY order_id;

SELECT rule,COUNT(*) FROM rejection GROUP BY rule;

-- NEGATIVO DELIBERADO: no usar para métricas.
SELECT SUM(i.line_amount_cents), SUM(p.captured_amount_cents)
FROM fact_item i JOIN fact_payment p ON p.order_id=i.order_id
WHERE i.order_id='SIM-O-000001';
```

Para ese pedido sintético: la conciliación correcta da 3.000/3.000 centavos; el join incorrecto da 6.000/9.000 y SUM(DISTINCT line_amount_cents) da 1.000. La suite exige estas diferencias como prueba negativa, no incorpora la consulta errónea a los modelos.

## Pruebas y límites

Runner autónomo con fixtures temporales, sin datos reales ni descargas. Comprueba determinismo de archivos, semillas distintas, claves, FK, estados/tipos, conservación fuente/integración/hechos, reconstrucción exacta de JSONL, conciliación independiente en enteros, granularidad, fan-out deliberado, importes iguales, atomicidad, permisos simulados, idempotencia, igualdad lógica y rechazo verificable. No admite omisiones como aprobación.

Los runners REES46 previos se ejecutan por separado y permanecen intactos. Resultados reales, hashes y límites de acceso en [STATUS.md](STATUS.md). La carga mantiene listas parseadas en memoria; no se presenta como implementación de memoria constante ni como benchmark a escala. Usar enteros y límites del contrato no resuelve futuras políticas fiscales, reembolsos o reconocimiento contable.

Próximo incremento propuesto: incorporar una versión contractual de devoluciones/reembolsos y hechos de ajuste con pruebas de conciliación, solo después de aprobar esta primera entrega. No se implementó ese incremento. Data Engineering continúa abierto.
