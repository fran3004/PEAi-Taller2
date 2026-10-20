---
tipo: adr
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[GUI-Diseno-Python]]"
  - "[[ADR-0006-Hipercubo-estadisticas-en-memoria]]"
  - "[[ADR-0017-Tecnologia-de-interfaz-Qt-Widgets]]"
origen: "Implementación del requisito 12.b del Taller 2 y distribuciones de productos del panel PEA-i"
numero: ADR-0018
decision: "Calcular histogramas desde Hipercubo5D y dibujarlos con Qt Widgets y QPainter"
---

# ADR-0018 · Histogramas calculados desde el hipercubo

## Contexto
El panel de Inicio debe presentar histogramas además de barras, y la ficha de
investigador necesita una distribución de sus productos por año. Los conteos
deben reflejar el filtro temporal activo y cumplir la arquitectura analítica
del proyecto: las estadísticas se calculan desde el `Hipercubo5D`, no mediante
consultas de agregación SQL.

## Opciones consideradas
1. **Agregar histogramas con una biblioteca externa**: ofrece componentes
   listos, pero contradice ADR-0017 y aumenta las dependencias de la GUI.
2. **Dibujar rangos fijos en las pantallas**: es sencillo, pero duplicaría
   lógica y permitiría introducir conteos que no provienen del servicio.
3. **Calcular las distribuciones en `ServicioEstadisticas` y dibujarlas con
   Qt Widgets y `QPainter`**: mantiene la fuente de datos y el renderizado
   alineados con las decisiones vigentes. **Elegida.**

## Decisión
`ServicioEstadisticas` calcula la distribución de productos por investigador
en los rangos `0`, `1–2`, `3–5`, `6–10` y `11+`. La población incluye los
códigos de investigadores del catálogo o de la membresía solicitada, además de
autores presentes en el subcubo, de modo que el rango cero también sea
observable. Los productos contados son los activos que contiene el hipercubo.

La distribución anual del investigador se proyecta desde la serie anual del
subcubo que ya fue filtrado por la ventana global. `GraficoHistograma` usa
`GraficoBase` y `QPainter`, muestra barras con etiquetas y conteos, ofrece
*tooltip* y permite alternar a una tabla accesible. Inicio lo muestra en los
modos Institución y Grupo; la ficha de investigador muestra la distribución
anual.

## Consecuencias
- Los datos de los histogramas se comparten entre servicios, GUI y exportación,
  sin lógica analítica en los widgets.
- El histograma puede representar tanto categorías discretas como años,
  manteniendo la misma interacción y el mismo estado vacío.
- La ficha del investigador añade contenido vertical; permanece dentro de su
  zona de desplazamiento existente.
- Se deben probar límites de rangos, aplicación de filtros temporales y
  renderizado vacío y con datos.
