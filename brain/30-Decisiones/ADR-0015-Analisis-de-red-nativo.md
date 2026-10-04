---
tipo: adr
estado: revisado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[_Indice]]"
  - "[[GUI-Diseno-Python]]"
  - "[[GUI-paridad]]"
  - "[[Multilista]]"
  - "[[ADR-0017-Tecnologia-de-interfaz-Qt-Widgets]]"
  - "[[SPEC]]"
origen: "AGENTS.md y AUDITORIA-DISENO-PEAI.md - Fase 12; detalle ajustado al boceto de red de coautorías, 2026-10-03"
---

# ADR-0015 · Renderizado nativo del grafo de red de coautoría

## Contexto
El análisis de relaciones entre investigadores se representa como un grafo: nodos = investigadores, aristas = productos compartidos. Existen soluciones que incrustan un navegador web (D3.js, Vis.js), pero aumentan cientos de megabytes el ejecutable, consumen memoria y complican la compilación cruzada en C++.

## Opciones consideradas
1. **Navegador incrustado (`QWebEngineView`)**: reutiliza librerías de JavaScript, pero añade más de 120 MB y dependencias pesadas.
2. **Dibujo nativo con `QGraphicsView` y `QGraphicsScene`**: ligero, sin dependencias externas, integrado con los estilos de Qt. **Elegida.**

## Decisión
Se adopta el dibujo nativo. Detalle visual en la sección 6.5 de [[GUI-Diseno-Python]]:

- **Nodos**: círculos cuyo radio crece con el número de coautores y cuyo color indica la categoría de Minciencias.
- **Aristas**: líneas con grosor proporcional a los productos compartidos.
- **Disposición**: algoritmo de fuerzas (Hooke y Coulomb) en un hilo secundario, con semilla fija para que el resultado se repita.
- **Interacción**: zoom con la rueda, arrastre del lienzo, resaltado de vecinos al pasar el ratón, selección de nodo que llena el panel de métricas y doble clic que abre la ficha del investigador.
- **Métricas** calculadas en memoria desde la [[Multilista]]: grado de conexión, intermediación (algoritmo de Brandes propio) y densidad de la red. Se exponen mediante el servicio `red_coautoria`.
- **Alcance por grupo**: al filtrar por un grupo específico, la red incluye a los investigadores del grupo y también a los coautores externos que colaboren en productos de dicho grupo.
- **Límites**: más de 400 nodos se recortan a los de mayor grado con aviso.

## Consecuencias
- **Positivas**: ejecutables ligeros, arranque rápido, sin motor web; el mismo enfoque sirve luego para C++.
- **Costos**: hay que programar la disposición por fuerzas y las métricas de centralidad a mano; el servicio `red_coautoria` es nuevo y debe replicarse en C++ (ver [[GUI-paridad]]).
