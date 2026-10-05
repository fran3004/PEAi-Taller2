---
tipo: bitacora
estado: revisado
creado: 2026-10-04
actualizado: 2026-10-04
relacionado:
  - "[[GUI-Diseno-Python]]"
  - "[[2026-10-04-copilot-desborde-inicio]]"
origen: "Solicitud de responsividad del grafo y panel de metricas"
agente: "Copilot"
rama: "master"
---

# Responsividad del analisis de redes

## Que cambie

- `VistaRed` reencuadra el grafo despues de mostrarse, al cambiar de tamano y cuando se mueve el divisor, usando un temporizador de 80 ms para evitar recalculos repetidos.
- El panel de metricas ahora tiene un ancho entre 280 y 340 px; en ventanas menores de 1240 px inicia con 280 px.
- Agregue el boton visible en espanol para ocultar o mostrar el panel y dejar el lienzo completo.
- Los controles compactan sus minimos a 1100 px y los botones exportar, ordenar y ajustar muestran textos breves con tooltip.
- El nombre de cada fila del ranking usa 11 pt y elipsis; el grado usa 10 pt.
- Se desactivo el desplazamiento horizontal del panel de metricas.
- La vista muestra un estado vacio claro cuando no hay nodos.

## Evidencia

- A 1100x700, todos los vertices de la red de demostracion quedan dentro del viewport mediante `mapFromScene`.
- No hay barra horizontal visible en la vista ni en el panel.
- El panel se puede plegar y el lienzo crece.

## Archivos

- `src/pea/gui/red/vista_red.py`
- `src/pea/gui/pantallas/redes.py`
- `tests/unit/test_pantalla_redes.py`

## Verificacion

- `ruff check src tests`: OK.
- `pytest tests/unit/test_pantalla_redes.py -q`: 9 pasaron.
- `pytest tests/unit -v`: 189 pasaron y 1 fue deseleccionada.
- `python -m pea.gui --autoprueba` en offscreen y sin animaciones: OK.
