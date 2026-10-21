# Instrucciones para agentes

## Identidad y límites

- Proyecto: Jewelry Commerce Intelligence Platform, caso profesional independiente para PLATHEL.
- Aurelia Jewelry es una empresa ficticia con una línea sintética original autorizada. REES46 es una línea real auditada separada; nunca atribuir sus datos a Aurelia ni mezclar fuentes. Olist no se incorpora.
- Mantener este proyecto independiente; no copiar código ni incorporar archivos de otros proyectos.
- La normalización estructural v1 está aprobada con 39 pruebas históricas. Su código, pruebas y salidas oficiales están congelados para la fase actual.
- La validación semántica REES46 permanece abierta: GO CON CONDICIONES para revisión conceptual; NO GO para modelo definitivo o KPIs comerciales hasta resolver los bloqueos pertinentes.
- Alcance actual autorizado: Data Warehouse sintético Aurelia v2 aditivo en src/aurelia/v2.py, ajustes separados, nuevas pruebas y documentación. Los módulos, contratos y pruebas históricos Aurelia v1 permanecen intactos. Normalización REES46 y su capa SQLite de evidencia permanecen intactas; no implementar su modelo analítico comercial. El portfolio corresponde a PaulaCe3. Código y materiales originales de PLATHEL con derechos reservados, sin licencia open source; véase COPYRIGHT.md. REES46 conserva sus derechos y condiciones propios.
- No modificar data/raw/, data/processed/, src/ ni tests/ sin una autorización posterior que amplíe el alcance. No descargar datasets ni instalar dependencias. Solo generar datos sintéticos propios bajo el contrato Aurelia autorizado, claramente rotulados; nunca presentarlos como observaciones reales.
- No inicializar Git, crear commits, remotos o repositorios ni hacer push hasta recibir autorización explícita. La decisión de publicar no autoriza por sí sola esos pasos.
- SQL técnico de evidencia REES46 y SQL dimensional de la simulación Aurelia autorizados por separado. No KPIs comerciales REES46, dashboards, API o ML; no alinear sus filas cortas.
- Nunca versionar datasets originales o procesados. Conservar las exclusiones de `.gitignore`.
- No publicar secretos, registros individuales, identificadores de clientes, URLs firmadas o rutas personales. La documentación pública puede conservar esquema y resultados agregados de auditoría, sin muestras de registros.

## Inicio con contexto mínimo

1. Leer este archivo y `README.md`.
2. Si existen, leer `docs/STATUS.md` y únicamente las decisiones relevantes en `docs/DECISIONS.md`.
3. Revisar el estado local y los archivos vinculados con la tarea. Evitar leer todo el repositorio o cargar datasets completos en el contexto.
4. Identificar el objetivo autorizado, las restricciones y el siguiente paso verificable. Si no existe documentación previa, no asumir que ya hay datos o implementación.
5. Para verificaciones públicas sin dataset, ejecutar `python -B tests/run_suite.py --unit-only`. La suite completa requiere datos y baseline privados; no omitir silenciosamente la integración ni presentar una ejecución parcial como aprobación integral.

## Documentación persistente

Cuando comience trabajo posterior, crear o actualizar según corresponda:

- `docs/STATUS.md`: objetivo vigente, trabajo completado, verificaciones realizadas, pendientes, bloqueos y próximo paso concreto.
- `docs/DECISIONS.md`: fecha, decisión, motivo, alternativas pertinentes y consecuencias.
- `docs/DATA_SOURCES.md`: fuente exacta de REES46, URL, licencia y condiciones verificadas, versión o período, esquema, limitaciones y transformaciones aplicadas.

No crear estos documentos con contenido supuesto. Registrar hechos confirmados y señalar expresamente lo pendiente de verificar. No guardar credenciales, registros individuales ni datos sensibles en la documentación.

## Cierre y continuidad

- Actualizar el estado persistente después de un avance sustancial o antes de una pausa en una tarea de implementación.
- Dejar referencias a archivos y verificaciones suficientes para continuar sin depender del historial del chat.
- Distinguir resultados ejecutados de propuestas; documentar las comprobaciones que no pudieron realizarse.
- Mantener cambios pequeños y dentro del alcance solicitado. Añadir dependencias y pruebas solo cuando una implementación autorizada las necesite.
