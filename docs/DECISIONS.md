# Decisiones del proyecto

## 2026-10-19 — Normalización estructural conservadora v1

Decisión: implementar el pipeline autorizado usando solo biblioteca estándar. Salida JSONL con valores originales como texto, nombres técnicos posicionales para anchura 13 y sin alineación para anchura 11. Preservar repeticiones y marcar incertidumbres. Clave técnica: hash del archivo y línea física.

Motivo: DATA_AUDIT.md no identifica inequívocamente los campos intermedios omitidos, ni confirma nombres semánticos o causas de repetición. El usuario autorizó explícitamente el pipeline y fixtures unitarios; esto amplía el alcance inicial de AGENTS.md.

Alternativas: insertar dos vacíos en posiciones supuestas; deduplicar por contenido o pedido-producto; asignar nombres comerciales a columnas. Descartadas porque modificarían interpretaciones o multiplicidades sin evidencia suficiente. Se eligió JSONL porque permite listas de anchura variable y conserva texto/errores sin fabricar un esquema uniforme.

Consecuencias: los 95.911 registros y 2.589 excedentes se conservan, pero no quedan habilitados como ventas validadas. Se requiere un destino nuevo por ejecución y hashes para reproducibilidad. El contrato de una línea física por registro se basa en la inspección exhaustiva del archivo; las anomalías futuras se conservan con marcas, no se reparan. Los datos y reportes con trazabilidad permanecen locales en data/processed, excluidos de Git.

Verificación: 13 pruebas aprobadas, incluida integración completa y reproducibilidad byte a byte; ejecución local con --check-audit satisfactoria. Detalle en STATUS.md y guía en PIPELINE.md.

## 2026-10-19 — Cierre de observaciones de QA de v1

Decisión: conservar exactamente el contrato y salidas de v1 para el archivo auditado, endureciendo errores de formato y publicación del reporte. BOM, CR aislado, comillas sin cerrar/multilínea y campos superiores a 131.072 caracteres se rechazan sin marcador de éxito. Alternativa descartada: aceptar parcialmente esas entradas e interpretar continuaciones por anchura, porque podía clasificar erróneamente un fragmento. Los errores de comillas cerradas y anchuras inesperadas siguen conservándose como registros inválidos, sin corrección.

El reporte se publica mediante enlace duro exclusivo tras escritura, flush/fsync y cierre de un archivo temporal en el destino. Alternativas descartadas: escribir directamente quality.json, porque podía quedar truncado con el nombre definitivo; o reemplazar un archivo existente. Consecuencia: se necesita un filesystem con soporte de enlaces duros; si falla, se termina sin publicar éxito. No se garantiza durabilidad ante corte de energía ni se modifica la política de conservar directorios parciales.

La integración real ya no se omite ante ausencia de dataset. Un runner explícito separa unitarias de integración y rechaza cualquier skip en la aceptación completa. Un oráculo de QA sin imports del pipeline verifica todos los registros y campos del reporte y detecta mutaciones temporales. La suite completa ejecutada terminó con 39 pruebas, cero fallos, errores u omisiones; tres corridas medidas y verificadas coinciden con los hashes oficiales. Evidencia en STATUS.md y contrato actualizado en PIPELINE.md. No se inició el diccionario de datos.

## 2026-10-19 — Diccionario preliminar y separación de evidencia semántica

Autorización existente: el usuario solicitó explícitamente construir diccionario, validación semántica, viabilidad y propuesta conceptual, manteniendo congelados src, tests y datos. No se registra autorización para implementar un modelo analítico ni una aprobación comercial de campos.

Decisión documental: mantener field_01–field_13 como nombres posicionales y proponer aliases candidatos sin implementarlos. Separar hechos de formato CONFIRMADOS de significados INFERIDOS o NO VERIFICADOS. Posición 7 se describe como código desconocido; marca sigue siendo una alternativa. Cantidad, moneda, precio unitario/importe efectivo y granularidad no se dan por confirmados. Motivo: no se recuperó un encabezado/diccionario primario de la edición y la evidencia local no permite identificarlos inequívocamente.

Decisión: conservar las cortas pendientes. Las omisiones {5,6}, {5,7} y {6,7} son compatibles con el mismo patrón de campos vacíos; 999 coincidencias de grupo/fecha/usuario apoyan parte de la correspondencia, pero no distinguen el bloque omitido. Alternativa descartada: elegir una alineación por conveniencia de un esquema analítico.

Consecuencias: perfil descriptivo de posiciones/códigos viable; indicadores comerciales condicionales o no soportados según ANALYTICS_FEASIBILITY.md. La recomendación técnica es GO CON CONDICIONES únicamente para revisión conceptual y NO GO para un modelo definitivo o métricas sin cerrar sus bloqueos. Es una recomendación del equipo en esta entrega, **no aprobación del usuario ni cierre semántico**.

Evidencia: ejecución de docs/semantic_profile.py en solo lectura, E01–E09 en SEMANTIC_VALIDATION.md; S01–S05 documentan acceso primario, períodos contradictorios y pendientes de licencia. Se conservaron hashes de 15 archivos protegidos, incluidos original, salidas v1, src y tests. No se reejecutó ni cambió el pipeline. Ejemplos documentales enmascaran completamente identificadores; no se guardan filas de clientes.

## 2026-10-19 — Preparación documental del portfolio público

El usuario autorizó preparar el proyecto para una futura publicación pública bajo PaulaCe3: código y materiales originales de PLATHEL con derechos reservados y sin licencia open source. Se creó COPYRIGHT.md, limitado a materiales propios, que distingue los derechos de REES46 y los permisos del servicio de alojamiento. No se eligió una licencia open source ni se incorporaron materiales ajenos como propios.

Decisión: presentar el estado actual en README, retirar rutas personales y detalles locales innecesarios y conservar evidencia agregada de auditoría. Las instrucciones por defecto del clon público usan --unit-only, porque datos y baseline oficial permanecen excluidos; no se sustituyen pruebas de integración por omisiones silenciosas ni se atribuyen al clon público las 39 pruebas históricas.

Se reforzaron exclusiones de datos reubicados, procesados, archivos comprimidos, credenciales, logs, cachés y configuración local. Los marcadores .gitkeep existentes se mantienen. Las plantillas de entorno futuras se excluyen por defecto hasta revisión explícita. Alternativa descartada: confiar solamente en la ubicación actual del dataset o en que un archivo «de ejemplo» no contiene credenciales.

Límites expresos de autorización: no modificar datos, src o tests; no instalar dependencias; no inicializar Git, crear commits/repositorios ni hacer push. La preparación no implica que exista un remoto ni que se haya aprobado el cierre semántico. La identidad pública de commits se elegirá al autorizar la inicialización; se recomienda email noreply configurado solo en este repositorio para no alterar otros proyectos.

## 2026-10-20 — Consolidación documental y puertas semánticas

Decisión: incorporar E10/S06/S07 y usar CONFIRMADO, PROVISIONAL y NO RESUELTO por afirmación; conservar por separado hechos técnicos y significado comercial. S06 resuelve granularidad declarada, asociación slug/ID y condiciones publicadas; no resuelve posiciones, cantidad, moneda, pago ni mapeo de edición interna a pública. Las tres omisiones equivalentes permanecen sin selección y los 2.589 excedentes se preservan.

Motivo: nuevas fuentes primarias y contraste independiente de hipótesis; ver [validación](SEMANTIC_VALIDATION.md) y [fuentes](DATA_SOURCES.md). Alternativas descartadas: asumir quantity/price/brand por analogía, deduplicar o alinear cortas porque tres imputaciones de vacíos resultan iguales. Igual resultado de valores no identifica la procedencia de la ausencia.

Se documentan escenarios A/B/C sin ejecutarlos ni escoger supuesto. GO CON CONDICIONES exclusivamente conceptual; NO GO para KPIs o modelo definitivo hasta cerrar cada requisito. No se cierra Data Engineering. Se justificaron antes de editar los cambios mínimos de README y referencias de AGENTS/COPYRIGHT, para evitar contradicciones sobre acceso y permisos. La auditoría y el estado históricos se conservan identificados como antecedentes. Cambios únicamente locales, sin commit/push; ningún cambio al pipeline, pruebas, datos ni configuración Git.

## 2026-10-20 — Capa técnica de evidencia SQLite

Autorización posterior: implementar una capa independiente de normalización v1 con SQLite/biblioteca estándar; añadir módulo, CLI y pruebas nuevos sin modificar código ni pruebas anteriores. Modelo técnico: archivo, ocurrencia, campo original posicional, línea vacía, manifiesto de importación y propiedades de calidad. No incluir hipótesis semánticas en el núcleo: no existe contrato ejecutable validado.

Decisión: reconstruir fuente/hash desde raw_text, terminadores y líneas vacías; recalcular todos los agregados de quality.json. Cargar transaccionalmente en staging, publicar por enlace exclusivo y rechazar destinos distintos. Una repetición compara esquema y todas las tablas contra una carga nueva, sin confiar solo en manifiestos. No deduplicar, alinear ni convertir valores en tipos comerciales. Identidad técnica no equivale a autenticidad externa.

Alternativas descartadas: cargar JSON sin validar contenido, usar INSERT OR IGNORE que oculte pérdidas, sobrescribir una base existente o importar el pipeline como validador del cargador. El esquema conserva texto y estados inválidos documentados por v1; un registro inválido preservado no es una entrada JSON incompatible.

Consecuencias: espacio adicional para staging y costo de una carga completa al repetir; memoria proporcional a textos distintos; requiere enlaces duros y uso sin escritores concurrentes. Bases/auxiliares/staging excluidos de Git. No se amplían permisos de datos ni se aprueban KPIs; Data Engineering y validación semántica siguen abiertos. Procedimiento y límites en [EVIDENCE_SQLITE.md](EVIDENCE_SQLITE.md).

## 2026-10-20 — Entrega vertical Aurelia sintética v1

Decisión autorizada: línea independiente de Data Warehouse en src/aurelia y data/aurelia, sin mover ni modificar normalización/evidencia REES46 y sin incorporar Olist. Generador propio determinista; distribuciones y casos contractuales originales, nunca resultados empresariales observados. No se añade licencia open source ni se publica ningún artefacto generado.

Contrato mínimo propio: pedidos, artículos y pagos; USD, centavos enteros, estados finitos, impuestos/descuentos/envío cero, devoluciones fuera de v1. Hechos separados fact_item/fact_payment con fecha del pedido y dimensiones mínimas. No fecha ficticia de pago, asignación de pagos a artículos, SUM(DISTINCT), ingreso contable o información personal.

Política de calidad: cualquier rechazo de registro impide integrar el lote completo; se publica una base explícitamente REJECTED con staging íntegro y motivos, código CLI 1. Fallo operativo/hash/manifiesto impide publicar base nueva. Repetición compara esquema y todas las tablas, sin alterar un destino diferente. Se prefirió snapshot por base a una gestión incremental prematura. Se exige un escritor por destino; no se garantiza durabilidad del directorio ante corte de energía.

Alternativas descartadas: unir artículos y pagos en detalle, deduplicar importes iguales, completar semántica REES46 con simulación o incorporar Olist pese al uso previsto. La demostración negativa de fan-out evidencia por qué las agregaciones independientes son necesarias. Pruebas y comandos en [AURELIA_DW.md](AURELIA_DW.md). Cambios locales para única evaluación funcional; no commit/push ni cierre global de Data Engineering.
