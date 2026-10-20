---
tipo: bitacora
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[GUI-Diseno-Python]]"
origen: "Corrección de los fallos en las pruebas responsivas de las tablas"
agente: "Copilot"
rama: "feat/python-cierre-francisco"
commit: ""
---

# Anchos mínimos de tablas responsivas

## Objetivo
Resolver los fallos de visibilidad de columnas en las pruebas de Grupos e
Investigadores y mantener cabeceras completas sin barras horizontales.

## Qué se hizo
- Las columnas conservan los mínimos previstos para contenido habitual y miden
  los encabezados con `QFontMetrics`; textos extensos no inflan el ancho mínimo
  de toda la tabla, ya que se eliden y tienen tooltip.
- Se ajustaron los mínimos de Nombre, Categoría, Líder y Grupo(s) para que las
  columnas se mantengan legibles en las resoluciones probadas.
- Las pruebas responsivas fijan la tipografía Inter que configura la aplicación
  real, en vez de depender de la fuente de sustitución de Qt fuera de la app.
- Se actualizó el criterio de legibilidad de la especificación visual.

## Comandos y resultados
- Las dos pruebas que fallaban (`test_pantalla_grupos_tabla_responsive_y_elipsis`
  y `test_pantalla_investigadores_tabla_responsive_y_elipsis`): 2 pasaron.
- Ruff focalizado: aprobado.
- `git diff --check`: sin errores.

## Decisiones
Los datos con texto largo deben elidirse con tooltip antes de hacer desaparecer
una columna vecina. Los anchos mínimos corresponden al contenido habitual
declarado por cada pantalla; los encabezados nunca quedan por debajo de su
ancho medido.

## Pendientes y siguiente paso
- Ejecutar la suite unitaria completa con la tipografía de producción en las
  pruebas de geometría.
- Continuar con el histograma calculado desde el hipercubo.
