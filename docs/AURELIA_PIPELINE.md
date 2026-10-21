# Aurelia: orquestación local y consumo

Simulación original PLATHEL; Aurelia Jewelry es ficticia. No contiene REES46 ni Olist. Contratos históricos: [v1](AURELIA_DW.md) y [v2](AURELIA_DW_V2.md). Data Engineering permanece abierto.

## Ejecutar

Python 3.11 o superior, biblioteca estándar, sin instalación adicional. Desde la raíz:

```powershell
python -B -m src.aurelia.pipeline run --output data/aurelia/runs/seed42-orders30 --seed 42 --orders 30
python -B -m src.aurelia.pipeline run --output data/aurelia/runs/seed42-orders30 --seed 42 --orders 30
python -B -m src.aurelia.pipeline verify --output data/aurelia/runs/seed42-orders30
python -B tests/run_aurelia_pipeline_suite.py
```

Semilla uint32; 6..10000 pedidos. Resultados: success, unchanged o fallo. Ambos éxitos tienen código 0; fallo operativo/contractual 1; argumentos CLI inválidos 2. verify devuelve PASSED al aceptar el paquete. Otro contenido/configuración exige otro destino; nunca se sobrescribe silenciosamente.

## Arquitectura y garantías

Generador v2 → staging e integración → conciliaciones → vistas → validación independiente desde fuentes → CSV → manifiesto → verificación → publicación local del directorio por rename.

Paquete: inputs/ (manifiestos y cinco JSONL, incluyendo base/), warehouse.sqlite, exports/ (seis CSV) y run_manifest.json: 15 archivos. Versiones aurelia-local-pipeline-v1 y aurelia-consumption-v1; user_version=2 del Warehouse intacto. Tabla adicional consumption_contract. No se migran bases existentes.

La base usa las transacciones v2. El paquete se prepara en un temporal hermano y solo se publica completo y validado. Bloqueo exclusivo por destino para escritores cooperantes. Fallos de generación, carga, vistas, aceptación, CSV y publicación no dejan una salida parcialmente aceptada; pueden quedar directorios padre vacíos. Un bloqueo huérfano requiere comprobar que no hay proceso activo antes de retirarlo manualmente.

La repetición verifica el destino, reconstruye un candidato y compara manifiestos y todos los hashes. Cuesta una reconstrucción completa. Reproducibilidad byte a byte probada en el mismo entorno Python/SQLite, no garantizada entre versiones. El manifiesto no es firma ni autenticación externa. No garantiza durabilidad ante corte de energía ni defensa frente a escritores externos hostiles.

Dentro del repositorio solo se generan destinos bajo data/aurelia, excluido de Git; también se admiten destinos externos seguros. Nunca versionar paquetes, manifiestos, bases o CSV generados.

## Diccionario de vistas y CSV

Todas incluyen synthetic=1 y currency=USD. Identificadores, códigos y estados son texto; cantidades y centavos son enteros. Las columnas y su orden exacto se definen en VIEWS de [analytics.py](../src/aurelia/analytics.py) y se verifican automáticamente.

| Vista | Clave / granularidad | Contenido |
|---|---|---|
| analytics_orders | order_id / pedido | order_at_utc, order_date, order_status; expected_item_cents, original_captured_cents, posted_refund_cents, committed_refund_cents, net_captured_cents, returned_units |
| analytics_items | order_id + item_no / línea | product_code, order_at_utc, order_status; quantity, unit_price_cents, line_amount_cents, returned_units, reserved_return_units |
| analytics_products | product_code / agregado del snapshot | item_records, ordered_units, paid_units, paid_item_cents, returned_units |
| analytics_payments | order_id + payment_no / pago | order_at_utc, order_status, payment_status; recorded_amount_cents, original_captured_cents, posted_refund_cents, committed_refund_cents, net_captured_cents, available_refund_cents |
| analytics_returns | return_id / devolución | order_id, item_no, requested_at_utc, received_at_utc, return_status; event_quantity, received_units, reserved_units, received_value_cents |
| analytics_refunds | refund_id / reembolso | order_id, payment_no, return_id, refund_reason, requested_at_utc, completed_at_utc, refund_status; recorded_amount_cents, posted_refund_cents, committed_refund_cents |

order_at_utc/order_date son fecha del pedido, incluso en pagos: no fecha de captura. requested_at_utc es solicitud; received_at_utc/completed_at_utc son recepción/finalización, admiten NULL según estado. Productos resume todo el snapshot; no es dimensión ni tiene fecha propia. Para temporalidad de producto usar artículos y fecha de pedido.

Estados: pedidos OPEN/PAID/CANCELLED; pagos CAPTURED/FAILED; devoluciones REQUESTED/RECEIVED/REJECTED; reembolsos REQUESTED/COMPLETED/FAILED. Reglas completas en v2. original_captured_cents cuenta CAPTURED; posted_refund_cents solo COMPLETED; committed_refund_cents incluye REQUESTED y COMPLETED. net_captured_cents = original - posted; available_refund_cents = original - committed. No son ingresos contables ni beneficio.

received_units/returned_units solo incluyen RECEIVED; reservas físicas incluyen REQUESTED y RECEIVED. event_quantity conserva la cantidad aun rechazada. received_value_cents es límite físico recibido, no reembolso. recorded_amount_cents conserva el importe registrado incluso fallido. expected_item_cents pertenece al pedido; line_amount_cents = quantity × unit_price_cents. ordered_units abarca todos los estados; paid_units/paid_item_cents solo PAID. GOODWILL puede tener return_id NULL. No se asignan reembolsos a productos.

## Consumo

Cada exportación se llama como su vista: UTF-8 sin BOM, coma, encabezado contractual, LF, orden por clave y NULL como campo vacío. Validación compara encabezados y todas las filas contra SQLite.

Power BI: Obtener datos → Texto/CSV → exports/analytics_orders.csv (o vista requerida). Identificadores como texto, cantidades/centavos como enteros, order_date como fecha y timestamps UTC como fecha/hora/zona; vacíos de fecha/return_id como nulos. Mantener hechos separados, sin relaciones automáticas entre detalles múltiples. analytics_products no es tabla de búsqueda. No sumar el mismo flujo desde varias vistas. Dividir centavos por 100 solo para presentación. No se instaló conector SQLite ni se construyó PBIX: importación real Power BI pendiente, contrato CSV probado.

Consulta reproducible de solo lectura, desde la raíz:

```python
from pathlib import Path
import sqlite3
from contextlib import closing
p = Path('data/aurelia/runs/seed42-orders30/warehouse.sqlite').resolve()
with closing(sqlite3.connect(p.as_uri() + '?mode=ro', uri=True)) as db:
    print(db.execute('SELECT COUNT(*), SUM(original_captured_cents), SUM(posted_refund_cents), SUM(net_captured_cents), SUM(returned_units) FROM analytics_orders').fetchone())
```

Guardar este fragmento fuera de las salidas oficiales o ejecutarlo en un intérprete Python; no requiere instalar paquetes.

## Aceptación ejecutada — 2026-10-21

18 pruebas nuevas en 7.063 s, cero fallos, errores u omisiones: ejecución inicial, idempotencia byte a byte, reconstrucción independiente, configuración distinta, entradas inválidas, fallos simulados de etapas/escritura/publicación, lote adverso, destino ajeno/bloqueo, alteración CSV/manifiesto/vista, rutas protegidas, contrato CSV, conciliación y CLI. Oráculo Python desde JSONL compara todas las filas de las seis vistas, integridad SQLite, FK y claves.

CLI persistido seed=42/orders=30: success → unchanged → PASSED. Pedidos 30, artículos 70, productos 3, pagos 35, devoluciones 5, reembolsos 7. Consulta anterior: (30, 92000, 1400, 90600, 3), centavos USD y unidades exclusivamente sintéticos; nunca resultados reales.

## Límites y cierre pendiente

Pendiente única aceptación funcional del usuario y autorización separada para registrar/publicar código. Si se exige interoperabilidad efectiva Power BI, ejecutar importación y comprobar tipos/agregados. Sin ledger incremental, transiciones, dashboards, ML, operación multiusuario o SLA. No se probó rendimiento a escala ni 10000 pedidos: es límite de entrada, no benchmark. Memoria/disco crecen con el snapshot y su reconstrucción.

REES46 sigue separado y con semántica abierta. Persiste la limitación de acceso al hash de su base SQLite retenida: no se afirma haberlo verificado. No bloquea esta simulación ni habilita KPIs REES46. No se declara Data Engineering terminado.

### Regresiones y protección ejecutadas — 2026-10-21

| Suite | Pruebas | Tiempo observado | Fallos / errores / omisiones |
|---|---:|---:|---|
| tests/run_aurelia_pipeline_suite.py | 18 | 7.063 s | 0 / 0 / 0 |
| tests/run_aurelia_v2_suite.py | 24 | 6.847 s | 0 / 0 / 0 |
| tests/run_aurelia_suite.py | 23 | 4.617 s | 0 / 0 / 0 |
| tests/run_suite.py (completa, datos locales) | 39 | 29.910 s | 0 / 0 / 0 |
| tests/run_evidence_suite.py (completa, datos locales) | 27 | 63.007 s | 0 / 0 / 0 |

Total 131 pruebas, códigos 0. Comandos: `python -B` seguido de cada ruta de la tabla. Tiempos de esta máquina, no SLA ni benchmark. Las integraciones REES46 usan datos/baseline privados y reconstrucciones temporales; no verifican el hash de la base SQLite retenida inaccesible.

Comparación contra HEAD: 22 archivos históricos versionados en src/tests/tools idénticos byte a byte. SHA-256 del original y ambas salidas oficiales coinciden con los hashes auditados: jewelry.csv 09d8a61644f66cbb9ad8c50f59180978a0995d121196faf25ef28083dd7b84a2; records.jsonl 5eef0df67a63c918b23a5d01627d6debfd88937c7f499e5b4bc25322bbff63e8; quality.json d58407f19d6f3727866ce2ec7674756da7a1a96624f0f5aac74e4c070fefe129.

Los 15 archivos del paquete local están excluidos mediante git check-ignore. git diff --check sin errores; enlaces relativos de los documentos cambiados resuelven; escaneo dirigido sin rutas personales, tokens reconocibles ni claves privadas. Consulta SQLite read-only confirmó (30, 92000, 1400, 90600, 3). Ninguna base o dataset incorporado a los cambios, sin commit/push ni configuración global modificada.
