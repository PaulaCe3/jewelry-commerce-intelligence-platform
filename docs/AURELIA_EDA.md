# EDA v1 — Aurelia Jewelry, exclusivamente sintético

Data Engineering v1 fue aceptado: [acta](DE_ACCEPTANCE.md). Este análisis es independiente y no modifica Warehouse, contratos, generadores ni pruebas históricas. No usa REES46, Olist ni JSONL de generación: calcula desde las seis exportaciones y contrasta con SQLite read-only.

## Reproducción

Desde la raíz, Python 3.11+ con biblioteca estándar, sin instalar paquetes:

```powershell
python -B tests/test_aurelia_eda.py
python -B -m src.aurelia.eda --bundle data/aurelia/runs/seed42-orders30 --output data/aurelia/eda/seed42-orders30-v1
```

Requiere las seis exportaciones y warehouse.sqlite existentes del paquete aceptado. No descarga ni regenera datos. Las pruebas requieren específicamente seed42/orders30 y fallan explícitamente si falta; no son una suite pública sin datos ni omiten integración. Para repetir el análisis elegir otro destino nuevo bajo data/aurelia/eda, por ejemplo seed42-orders30-v2. No sobrescribe reportes. Código CLI 0 éxito, 1 fallo y 2 argumentos inválidos.

Código: [eda.py](../src/aurelia/eda.py). Pruebas: [test_aurelia_eda.py](../tests/test_aurelia_eda.py).

Salida local excluida de Git: results.json con resultados y siete hashes de entrada; seis tablas CSV (estados, días, productos, devoluciones, resumen de distribución e histograma); cinco SVG estáticos. No se genera dashboard. Los archivos SVG se abren directamente en un navegador; todas las figuras están rotuladas SINTÉTICO, con unidades, etiquetas y origen cero. La serie diaria usa barras porque solo contiene 30 fechas con recuentos idénticos; evita sugerir tendencias. El histograma tiene intervalos explícitos, no bins equiprobables.

## Método y controles

Se exige encabezado y anchura contractual de cada CSV, clave única y coincidencia de cada celda y orden con su vista SQLite. Solo synthetic=1 y USD. Los importes de entrada permanecen enteros; promedios descriptivos usan Decimal, con precisión decimal de Python y sin redondeo comercial implícito. Se verifica el hash de SQLite y los seis CSV antes/después. Sin escribir en fuentes.

No hay joins entre detalles múltiples. Cada medida se calcula en su grano nativo; las comparaciones son entre agregados. Artículos agregados por producto se contrastan con analytics_products. Pagos CAPTURED, reembolsos COMPLETED y devoluciones RECEIVED se concilian con agregados de pedidos y líneas. CSV alterado, duplicación financiera o agregado de producto incorrecto provocan rechazo. El reporte se publica localmente tras validación en un temporal; hashes no son prueba de autenticidad externa ni esta conciliación sustituye los controles del Warehouse aceptado.

## Diccionario de indicadores

Nombres abreviados O/I/P/D/R/G = analytics_orders/items/payments/returns/refunds/products. Todos los importes son centavos USD; dividir por 100 solo para visualización. Todos los conteos pertenecen a este snapshot sintético.

| Indicador | Definición y fórmula | Fuente y grano | Limitación |
|---|---|---|---|
| Pedidos por estado | COUNT(*) GROUP BY order_status; OPEN, PAID, CANCELLED | O, pedido | Estado actual; no flujo de transición ni conversión |
| Pedidos diarios | COUNT(*) GROUP BY order_date; completar ceros entre mínimo y máximo | O, pedido → día UTC | Fecha de pedido; no fecha de pago y sin fechas fuera del rango observado |
| Unidades pedidas por producto | SUM(quantity) GROUP BY product_code | I, línea → producto; contraste G | Incluye OPEN/CANCELLED; no demanda real ni unidades netas |
| Unidades en pedidos pagados | SUM(quantity) WHERE order_status='PAID' por producto | I, línea → producto | No descuenta devoluciones |
| Importe de pedidos pagados | SUM(expected_item_cents) WHERE order_status='PAID' | O, pedido | Importe esperado contractual, no ingreso contable |
| Importe pagado por producto | SUM(line_amount_cents) WHERE order_status='PAID' por producto | I, línea → producto; contraste G | No asigna reembolsos a productos ni mide rentabilidad |
| Pagos capturados | SUM(recorded_amount_cents) WHERE payment_status='CAPTURED' | P, pago | No sumar todos los intentos ni usar fecha de pedido como fecha de captura |
| Reembolsos completados | SUM(recorded_amount_cents) WHERE refund_status='COMPLETED' | R, evento financiero | Excluye pendientes/fallidos; no asignación a producto |
| Saldo neto capturado | Capturado − reembolsado completado | Agregados P y R, snapshot | Saldo sintético; no beneficios ni ingresos contables |
| Eventos de devolución por estado | COUNT(*) GROUP BY return_status | D, evento físico | REQUESTED pendiente, RECEIVED recibido, REJECTED rechazado; no necesariamente pedidos distintos |
| Unidades por estado de devolución | SUM(event_quantity) GROUP BY return_status | D, evento físico | Solo RECEIVED son unidades efectivamente devueltas; pendientes/rechazadas son solicitadas |
| Distribución de importe esperado | n, MIN, MAX, SUM/n, mediana; poblaciones ALL y PAID separadas | O, pedido | ALL incluye pedidos no pagados; media PAID no equivale a cobro neto medio |
| Histograma de importe esperado | COUNT por intervalos [0,1000), [1000,3000), [3000,5000), [5000,+∞) | O, pedido, ALL | Intervalos desiguales: barras de frecuencias por categoría, no densidad; último abierto |

## Hallazgos ejecutados — 2026-10-21

Paquete seed42/orders30: 30 pedidos, 70 líneas, 3 productos, 35 registros de pago, 5 devoluciones y 7 reembolsos. No confundir líneas con unidades ni eventos con pedidos.

- Estados: 15 PAID (50%), 10 OPEN y 5 CANCELLED. No se interpreta como conversión ni rendimiento comercial.
- Del 2025-01-01 al 2025-01-30: exactamente un pedido diario. Es una regularidad de la simulación, sin evidencia de crecimiento o estacionalidad.
- Unidades pedidas: SIM-RING 74, SIM-EARRING 36 y SIM-PENDANT 25; total 135. De ellas, 64 están en pedidos PAID (39, 14 y 11 respectivamente). La mayor participación de anillos describe solo este conjunto.
- Importe de pedidos PAID: 920 USD. Por producto: anillos 640 USD, pendientes 160 USD y colgantes 120 USD. No se distribuyen reembolsos ni se calcula margen por producto.
- Capturado 920 USD; reembolsos completados 14 USD; saldo neto capturado 906 USD. Conciliación PASSED entre CSV, vistas y agregados independientes.
- Devoluciones: 3 eventos RECEIVED/3 unidades, 1 REQUESTED/1 unidad y 1 REJECTED/1 unidad. Pendiente o rechazada no significa unidad recibida.
- Importe esperado por pedido ALL: mínimo 5 USD, máximo 185 USD, media 62,50 USD, mediana 52,50 USD. PAID: n=15, mínimo 5 USD, máximo 155 USD, media aproximadamente 61,33 USD y mediana 40 USD. Diferencias descriptivas, sin inferencia estadística.
- Histograma ALL: 2, 5, 7 y 16 pedidos en los cuatro intervalos definidos. Su tramo abierto y anchuras desiguales impiden leer las alturas como densidades.

Pruebas ejecutadas: 8 en 1.001 s, cero fallos/errores/omisiones. Incluyen conciliación conocida, duplicación que inflaría pagos, mutación de agregado, distribución/tiempo, CSV alterado contra SQLite, reproducibilidad de todos los reportes byte a byte y protección de fuentes, parseo de cinco SVG, destinos y CLI. No se reejecutaron suites históricas: no se modifican sus implementaciones. No se afirma validación visual manual de los SVG ni una nueva prueba de Power BI.

## Recomendación para el futuro Power BI

1. Tarjetas: pedidos, importe esperado de pedidos PAID, capturado, reembolsado completado y saldo neto; moneda y etiqueta sintética visibles. Mantener nombres distintos aunque dos valores coincidan en esta simulación.
2. Barras: pedidos por estado; unidades por producto diferenciando todos los pedidos y PAID; devoluciones por estado con selector explícito eventos/unidades.
3. Serie diaria por fecha de pedido, con nota de que la regularidad deriva del generador; no construir conclusiones de tendencia.
4. Distribución por pedido con filtros ALL/PAID explícitos y bins uniformes si se adopta un histograma de densidad. Para los intervalos actuales usar barras categóricas de frecuencia.
5. Conciliación financiera con tarjetas o barras separadas; no apilar capturado, reembolso y neto como si fueran partes aditivas. No mezclar fecha de pedido con fecha de finalización de reembolso sin identificar el rol temporal.

No relacionar hechos de detalle directamente ni usar G como dimensión. El filtro por producto no debe atribuir reembolsos o saldo neto a productos: no existe regla de asignación. No habilitar beneficio, margen, ingresos contables, conversión, recompra, cohortes de clientes o RFM: estas exportaciones no aportan identidad de cliente/costos/embudo suficientes.

## Límites

Muestra pequeña y construida, con casos deliberados; sin representatividad poblacional, causalidad ni significación comercial. Sin análisis predictivo. EDA carga en memoria seis CSV y resultados SQLite; adecuado al paquete actual, no benchmark de escala. El contrato de entrada es el consumo v1 existente: no amplía Data Engineering. Hashes verifican estabilidad durante el análisis, no origen externo. Data Engineering v1 continúa cerrado y aceptado; este EDA queda local para aprobación, sin commit/push ni publicación de resultados generados.
