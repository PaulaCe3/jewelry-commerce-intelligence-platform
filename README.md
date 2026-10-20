# Jewelry Commerce Intelligence Platform

**Proyecto 01 del portfolio profesional de PLATHEL.** Caso de consultoría de datos para **Aurelia Jewelry**, una empresa ficticia de joyería.

El proyecto demuestra cómo auditar una fuente de comercio electrónico, conservar su trazabilidad y resolver incertidumbres antes de construir métricas de negocio. El trabajo actual se centra en ingeniería y calidad de datos; sigue en desarrollo.

## Estado del proyecto

| Fase | Estado y alcance |
|---|---|
| Auditoría técnica | Archivo local recorrido completamente; calidad, estructura y procedencia documentadas |
| Normalización estructural v1 | **Aprobada**, con evidencia histórica de 39 pruebas y reproducibilidad byte a byte |
| Diccionario y validación semántica | Documentación preliminar disponible; **validación abierta** |
| Modelado analítico | **GO CON CONDICIONES** para revisión conceptual; sin implementación definitiva |
| KPIs comerciales definitivos | **NO GO** hasta resolver los bloqueos pertinentes |

La normalización conserva 95.911 registros: 90.559 filas de 13 campos y 5.352 de 11, incluidas las 2.589 repeticiones excedentes. Las filas cortas permanecen pendientes, sin alineación forzada. Estos números son resultados técnicos de auditoría, no ventas, pedidos ni clientes confirmados.

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
- [Diccionario preliminar de 13 posiciones](docs/DATA_DICTIONARY.md).
- [Validación semántica y cuestiones pendientes](docs/SEMANTIC_VALIDATION.md).
- [Viabilidad de indicadores y modelo conceptual](docs/ANALYTICS_FEASIBILITY.md).
- [Decisiones y límites autorizados](docs/DECISIONS.md).

Las mediciones y resultados completos corresponden a ejecuciones documentadas sobre el archivo auditado, no a garantías universales de rendimiento ni a una nueva ejecución automática en GitHub.

## Fuente y límites de uso

La fuente analizada es REES46 Jewelry Store Purchase History. Referencias primarias: [catálogo de datos REES46](https://data.rees46.com/), [datasets REES46](https://rees46.com/en/datasets) y [ficha Kaggle candidata](https://www.kaggle.com/datasets/mkechinov/ecommerce-purchase-history-from-jewelry-store). El vínculo de edición y sus límites se explican en DATA_SOURCES.md; la licencia específica no se considera verificada.

**Este repositorio no distribuye datasets, registros individuales, muestras de clientes ni datos procesados de REES46.** Los informes conservan esquema, metodología y resultados agregados de calidad. Aurelia Jewelry es ficticia y no posee los datos; no se afirma relación comercial con la tienda original, REES46 o Kaggle.

## Limitaciones actuales y próximos pasos

Siguen pendientes el encabezado oficial de la edición, la granularidad comercial, el papel de ciertos códigos, la moneda, precio unitario frente a importe, persistencia de identidad y causa de las repeticiones. La aprobación del pipeline es estructural y no resuelve esos puntos.

No hay dashboards, SQL, API ni modelos de Machine Learning implementados. El próximo paso es obtener evidencia primaria para resolver las preguntas semánticas y revisar el modelo conceptual; no convertir hipótesis en KPIs de ventas, clientes, rentabilidad o RFM.

## Derechos y portfolio

Código y materiales originales de **PLATHEL**, con derechos reservados, **sin licencia open source**. Véase [COPYRIGHT.md](COPYRIGHT.md). El aviso no atribuye derechos sobre REES46 ni sobre materiales de terceros.

Cuenta prevista para alojar el portfolio público: [PaulaCe3](https://github.com/PaulaCe3). Este documento no afirma que el repositorio remoto ya exista o haya sido publicado.
