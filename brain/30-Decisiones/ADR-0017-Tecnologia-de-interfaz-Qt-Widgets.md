---
tipo: adr
estado: revisado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[_Indice]]"
  - "[[GUI-Diseno-Python]]"
  - "[[ADR-0012-Diseno-GUI-y-navegacion]]"
  - "[[ADR-0015-Analisis-de-red-nativo]]"
  - "[[ADR-0011-Paridad-arquitectural-Python-Cpp]]"
origen: "Conflicto entre SPEC/skill (matplotlib) y el código (QPainter); decisión de rediseño, 2026-10-03"
---

# ADR-0017 · Tecnología de la interfaz: Qt Widgets, hojas de estilo, QPainter y QtSvg

## Contexto
La documentación mencionaba `matplotlib` embebido para los gráficos de Python, mientras el código ya usaba `QPainter`. El nuevo diseño pide tarjetas con sombra, degradados, íconos de color, gráficos animados con interacción y un grafo interactivo. El proyecto se apoya en Qt 6 Widgets en ambos lenguajes ([[ADR-0011-Paridad-arquitectural-Python-Cpp]]).

## Opciones consideradas
1. **`matplotlib` embebido**: gran biblioteca de gráficos, pero añade una dependencia pesada, es difícil de igualar visualmente con el nuevo diseño y no existe equivalente directo en C++.
2. **QML / Qt Quick**: animaciones muy fluidas, pero cambia la arquitectura, las pruebas y se aleja de Qt Widgets que usa C++.
3. **`QtCharts`**: gráficos listos, pero limita el estilo y complica el empaquetado y la equivalencia con C++.
4. **Qt Widgets + hoja de estilo (QSS) + `QPainter` + `QtSvg`**: control total del aspecto, sin dependencias nuevas y con un camino directo hacia C++. **Elegida.**

## Decisión
La interfaz de Python se construye con **Qt Widgets**, una hoja de estilo central con tokens (`estilo.py`), gráficos propios con `QPainter`, el grafo con `QGraphicsView` ([[ADR-0015-Analisis-de-red-nativo]]) e íconos SVG con `QtSvg`. **No** se usa `QML`, `QtWebEngine`, `matplotlib` ni `QtCharts`. Las animaciones usan `QVariantAnimation` y se pueden desactivar con `PEA_SIN_ANIMACIONES=1`.

## Consecuencias
- **Positivas**: pocas dependencias, mismas piezas disponibles en C++, pruebas offscreen sencillas.
- **Costos**: los gráficos (barras apiladas, dona doble, minigráficos) se escriben a mano.
- **A corregir en la documentación**: las menciones a `matplotlib` en [[SPEC]], en las historias de usuario y en la skill `python-pyside6` quedan reemplazadas por esta decisión.
