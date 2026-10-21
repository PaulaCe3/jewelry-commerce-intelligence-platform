# Cierre de Data Engineering v1 — Aurelia Jewelry

Fecha de aceptación funcional: 2026-10-21.

## Decisión

**APROBADO — Data Engineering v1 del caso sintético Aurelia Jewelry**, dentro del alcance contractual documentado. El usuario confirmó en Power BI Desktop la importación de `analytics_orders.csv` y las medidas DAX de conciliación. Esta aceptación **no** certifica el resto de vistas en Power BI ni implica validación de datos empresariales reales.

## Evidencia de aceptación

- Origen: `data/aurelia/runs/seed42-orders30/exports/analytics_orders.csv` (local, excluido de Git).
- Power Query: 30 pedidos; tipos de importes interpretados como enteros.
- Medida `Pagos capturados USD`: `SUM(original_captured_cents) / 100` → **920,00 USD**.
- Medida `Reembolsos completados USD`: `SUM(posted_refund_cents) / 100` → **14,00 USD**.
- Medida `Saldo neto capturado USD`: diferencia de las anteriores → **906,00 USD**.
- Los tres resultados coinciden con la conciliación técnica: 92.000 − 1.400 = 90.600 centavos USD.
- Aceptación visual comunicada por el usuario durante la sesión; no se adjunta PBIX ni captura al repositorio y **no se afirma haber verificado su guardado**.
- Suite técnica previa reportada: **131 pruebas aprobadas**, sin fallos, errores u omisiones; ver `AURELIA_PIPELINE.md` y `STATUS.md`.

## Qué queda fuera del alcance

- REES46 permanece separado, con semántica no resuelta; no habilitar KPIs comerciales basados en REES46.
- Olist no se utiliza.
- No hay ledger incremental, cargas multibatch, operación multiusuario, garantías ante cortes eléctricos ni SLA.
- No se verificó el hash de la base SQLite REES46 retenida por limitación de permisos.
- No se verificaron manualmente las otras cinco exportaciones en Power BI.
- No se han desarrollado dashboards ni modelos predictivos.
- Los datos y resultados son **exclusivamente sintéticos**: no son ventas reales ni ingresos contables.

## Próxima etapa

**Data Analytics y Business Intelligence**: análisis exploratorio, definición de indicadores con granularidad controlada, modelado en Power BI y dashboard profesional, sin presentar la simulación como evidencia comercial observada. Los archivos `.pbix` y exportaciones locales deben revisarse antes de cualquier publicación.

Esta aceptación cierra la **primera versión** de Data Engineering del caso Aurelia; no significa que el proyecto completo esté terminado.
