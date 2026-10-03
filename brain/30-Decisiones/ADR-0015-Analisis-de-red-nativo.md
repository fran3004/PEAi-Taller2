---
tipo: adr
estado: aprobado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[_Indice]]"
  - "[[GUI-paridad]]"
  - "[[Multilista]]"
  - "[[SPEC]]"
origen: "AGENTS.md y AUDITORIA-DISENO-PEAI.md - Fase 12"
---

# ADR-0015 · Renderizado Nativo del Grafo de Red de Coautoría

## Contexto
El análisis de redes complejas y coautorías entre investigadores y grupos requiere representar visualmente un grafo interactivo de nodos (investigadores) y aristas (productos compartidos). En entornos de escritorio existen soluciones comunes basadas en renderizar librerías JavaScript (como D3.js o Vis.js) incrustando un motor web completo (Chromium / `QWebEngineView`). Sin embargo, incrustar un navegador web incrementa el peso del ejecutable en cientos de megabytes, consume memoria excesiva y complica la compilación cruzada en C++ con MinGW.

## Opciones consideradas
1. **Navegador web incrustado (`QWebEngineView` / WebView)**: Permite reutilizar gráficos HTML5/JS pero añade más de 120 MB de binarios, dependencias pesadas y dificultades de enlace en entornos UCRT64.
2. **Visualización nativa con Qt Graphics Framework (`QGraphicsView` / `QGraphicsScene`)**: Implementación directa en C++ y Python utilizando primitivas vectoriales aceleradas por hardware de Qt, con algoritmo de fuerzas en hilo secundario.

## Decisión
Se adopta la **visualización nativa de red mediante `QGraphicsView` y `QGraphicsScene`** formalizada en [[GUI-paridad]].
Tanto en Python como en C++, el grafo de coautoría se dibuja mediante objetos gráficos nativos de Qt:
- Los nodos son círculos interactivos con eventos de puntero.
- Las aristas son líneas vectoriales con grosor proporcional al número de colaboraciones.
- La física de relajación (*force-directed layout*) se ejecuta de manera asíncrona sin bloquear el hilo principal de la interfaz.

## Consecuencias
- **Positivas**: Ejecutables ligeros y rápidos; arranque instantáneo; cero dependencias de motores de renderizado web pesados; integración fluida con el sistema de estilos de Qt.
- **Costos**: Requiere programar manualmente el algoritmo de disposición física de nodos por fuerzas.
