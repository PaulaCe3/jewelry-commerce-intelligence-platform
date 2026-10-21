# Jewelry Commerce Intelligence Platform

**Proyecto 01 del portfolio profesional de PLATHEL.** Caso de consultoría de datos para **Aurelia Jewelry**, una empresa ficticia de joyería.

El proyecto demuestra cómo auditar una fuente de comercio electrónico, conservar su trazabilidad y resolver incertidumbres antes de construir métricas de negocio. El trabajo actual se centra en ingeniería y calidad de datos; sigue en desarrollo.

## Línea REES46 — estado del proyecto

| Fase | Estado y alcance |
|---|---|
| Auditoría técnica | Archivo local recorrido completamente; calidad, estructura y procedencia documentadas |
| Normalización estructural v1 | **Aprobada**, con evidencia histórica de 39 pruebas y reproducibilidad byte a byte |
| Evidencia técnica SQLite | Capa local consultable, independiente de v1; pruebas y ejecución en EVIDENCE_SQLITE.md |
| Diccionario y validación semántica | Documentación preliminar disponible; **validación abierta** |
| Modelado analítico | **GO CON CONDICIONES** para revisión conceptual; sin implementación definitiva |
| KPIs comerciales definitivos | **NO GO** hasta resolver los bloqueos pertinentes |

La normalización conserva 95.911 registros: 90.559 filas de 13 campos y 5.352 de 11, incluidas las 2.589 repeticiones excedentes. Las filas cortas permanecen pendientes, sin alineación forzada. Estos números son resultados técnicos de auditoría, no ventas, pedidos ni clientes confirmados.

## Línea independiente: Aurelia Jewelry sintética

Aurelia Jewelry es ficticia. Se implementó una primera entrega vertical con datos sintéticos originales de PLATHEL: contratos de pedidos/artículos/pagos, generador determinista, staging transaccional con rechazos, integración y hechos dimensionales separados. Los importes USD son simulados; no son ventas observadas ni ingresos contables. No se copian datos ni distribuciones de REES46 u Olist. Olist queda descartado por ahora como fuente del portfolio comercial.

Código: src/aurelia; artefactos locales excluidos: data/aurelia. REES46, sus contratos y su evidencia SQLite permanecen independientes. Data Engineering sigue abierto; la validación semántica REES46 no se cierra por disponer de una simulación.

```powershell
python -B tests/run_aurelia_suite.py
```

Ejecución completa, contratos, límites y conciliación en [AURELIA_DW.md](docs/AURELIA_DW.md).

La versión aditiva v2 incorpora devoluciones físicas y reembolsos financieros separados, límites acumulados y saldos exclusivamente sintéticos, sin modificar v1 ni migrar sus bases. Contratos, comandos y pruebas en [AURELIA_DW_V2.md](docs/AURELIA_DW_V2.md). Se ejecuta con `python -B -m src.aurelia.v2`; pruebas con `python -B tests/run_aurelia_v2_suite.py`.

## Capacidades demostradas

- Auditoría reproducible de estructura, vacíos, duplicados, fechas y relaciones entre identificadores candidatos.
- Lectura secuencial con biblioteca estándar de Python, conservación del texto y trazabilidad por hash y línea de origen.
- Separación explícita entre hechos confirmados, inferencias y significados no verificados.
- Pruebas de CLI, integridad, reproducibilidad, manipulación de datos/metadatos y fallos de escritura controlados.
- Verificación independiente de registros y reportes, más medición documentada de tiempo y memoria.
- Diccionario preliminar, matriz de viabilidad y modelo conceptual sin anticipar conclusiones comerciales.

## Ejecución sin dataset

Requisito: Python 3.11 o superior. Esta fase usa exclusivamente biblioteca estándar; no requiere instalar dependencias, un entorno virtual ni el paquete del proyecto.

Si el intérprete se invoca como `python3`, `py` o mediante otra ruta en tu sistema, sustituí `python` en los comandos por ese ejecutable. No se necesitan rutas personales ni configuración específica del entorno de auditoría.

Desde la raíz del repositorio:

```powershell
python --version
python -B tests/run_suite.py --unit-only
```

La selección contiene **29 pruebas unitarias** con fixtures mínimos generados en directorios temporales y eliminados al finalizar. No necesita descargar datos ni crear archivos en data/raw o data/processed. El mensaje `UNIT ONLY - NO FULL APPROVAL` distingue esta verificación pública de la aceptación integral.

Las **39 pruebas completas**, incluidas las integraciones reales, se ejecutaron en el entorno de auditoría con datos locales y baseline oficial. Esos archivos no se distribuyen; la suite completa falla si faltan. No se debe prometer que un clon público sin datos ejecutará la integración ni descargar automáticamente el dataset para conseguirlo. Requisitos y comandos de integración en [PIPELINE.md](docs/PIPELINE.md).

## Estructura

```text
jewelry-commerce-intelligence-platform/
├── README.md
├── AGENTS.md
├── COPYRIGHT.md
├── .gitignore
├── pyproject.toml
├── src/       # Normalización estructural aprobada
├── tests/     # Unitarias, CLI, integración y verificador independiente
├── tools/     # Medición reproducible de recursos
├── docs/      # Auditoría, procedencia, diccionario, decisiones y estado
└── data/
    ├── raw/       # Solo .gitkeep en la versión pública
    └── processed/ # Solo .gitkeep en la versión pública
```

## Documentación y evidencias

- [Estado y verificaciones](docs/STATUS.md).
- [Auditoría técnica](docs/DATA_AUDIT.md).
- [Procedencia y condiciones de uso](docs/DATA_SOURCES.md).
- [Pipeline, contrato y pruebas](docs/PIPELINE.md).
- [Capa técnica SQLite: ejecución, consultas y pruebas](docs/EVIDENCE_SQLITE.md).
- [Diccionario preliminar de 13 posiciones](docs/DATA_DICTIONARY.md).
- [Validación semántica y cuestiones pendientes](docs/SEMANTIC_VALIDATION.md).
- [Viabilidad de indicadores y modelo conceptual](docs/ANALYTICS_FEASIBILITY.md).
- [Escenarios y criterios de desbloqueo](docs/SEMANTIC_SCENARIOS.md).
- [Decisiones y límites autorizados](docs/DECISIONS.md).

Las mediciones y resultados completos corresponden a ejecuciones documentadas sobre el archivo auditado, no a garantías universales de rendimiento ni a una nueva ejecución automática en GitHub.

## Fuente y límites de uso

La fuente analizada es REES46 Jewelry Store Purchase History. Referencias primarias: [catálogo de datos REES46](https://data.rees46.com/), [datasets REES46](https://rees46.com/en/datasets) y [ficha Kaggle identificada](https://www.kaggle.com/datasets/mkechinov/ecommerce-purchase-history-from-jewelry-store). El vínculo de edición y sus límites se explican en DATA_SOURCES.md; se verificaron la etiqueta de derechos y las condiciones publicadas de uso gratuito y atribución; el alcance de redistribución y usos comerciales adicionales continúa sin resolver.

**Este repositorio no distribuye datasets, registros individuales, muestras de clientes ni datos procesados de REES46.** Los informes conservan esquema, metodología y resultados agregados de calidad. Aurelia Jewelry es ficticia y no posee los datos; no se afirma relación comercial con la tienda original, REES46 o Kaggle.

## Limitaciones actuales y próximos pasos

Siguen pendientes el encabezado oficial de la edición, la unidad física y clave de línea comercial, el papel de ciertos códigos, la moneda, precio unitario frente a importe, persistencia de identidad y causa de las repeticiones. La fuente declara un producto comprado por fila y agrupación por order_id; no confirma sus posiciones locales, cantidad ni pago. La aprobación del pipeline es estructural y no resuelve esos puntos.

La capa SQLite REES46 incluye únicamente SQL técnico de evidencia. La línea Aurelia incorpora un modelo dimensional mínimo exclusivamente sintético. No hay dashboards, modelo comercial REES46, API ni modelos de Machine Learning implementados. En REES46 sigue pendiente obtener evidencia primaria para resolver las preguntas semánticas; no convertir hipótesis en KPIs de ventas, clientes, rentabilidad o RFM. En Aurelia corresponde la aceptación funcional de la orquestación y del consumo sintético documentados abajo.

## Derechos y portfolio

Código y materiales originales de **PLATHEL**, con derechos reservados, **sin licencia open source**. Véase [COPYRIGHT.md](COPYRIGHT.md). El aviso no atribuye derechos sobre REES46 ni sobre materiales de terceros.

Repositorio de portfolio: [PaulaCe3/jewelry-commerce-intelligence-platform](https://github.com/PaulaCe3/jewelry-commerce-intelligence-platform).

## Orquestación y consumo sintético

Interfaz local sobre Aurelia v2: generación, carga, conciliación, aceptación independiente y seis vistas/CSV con grano explícito. [Comandos, contratos y límites](docs/AURELIA_PIPELINE.md).

```powershell
python -B -m src.aurelia.pipeline run --output data/aurelia/runs/seed42-orders30 --seed 42 --orders 30
python -B -m src.aurelia.pipeline verify --output data/aurelia/runs/seed42-orders30
python -B tests/run_aurelia_pipeline_suite.py
```

Sin datasets privados ni dependencias adicionales. Repetición idéntica: unchanged; otro contenido exige destino nuevo. Artefactos excluidos de Git. No hay dashboards ni importación Power BI ejecutada. Data Engineering sigue abierto.
