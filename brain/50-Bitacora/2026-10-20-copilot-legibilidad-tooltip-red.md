---
tipo: bitacora
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[GUI-Diseno-Python]]"
origen: "Corrección de contraste y legibilidad del tooltip del grafo de coautorías"
agente: "Copilot"
rama: "feat/python-cierre-francisco"
commit: ""
---

# Bitácora · Legibilidad del tooltip de la red

## Objetivo
Corregir el texto poco visible del tooltip que aparece al pasar el cursor sobre
un investigador en el gráfico de coautorías.

## Qué se hizo
- El estilo oscuro de alto contraste para `QToolTip` se aplica también en la
  hoja de estilos de `QApplication`, ya que los tooltips de elementos gráficos
  no recibían el estilo local de la ventana.
- Se añadió una prueba para comprobar el estilo de aplicación y se documentó el
  criterio de contraste para tooltips de nodos y aristas.

## Comandos y resultados
- `.venv\Scripts\python.exe -m pytest -q tests\unit\test_gui_completa.py -k tooltip`: 1 pasó.
- `.venv\Scripts\python.exe -m pytest -q tests\unit\test_pantalla_redes.py`: 10 pasaron.
- `.venv\Scripts\python.exe -m ruff check src\pea\gui\estilo.py src\pea\gui\ventana_principal.py tests\unit\test_gui_completa.py`: aprobado.
- `git diff --check`: sin errores.

## Decisiones
Se mantiene la paleta ya definida para tooltips: fondo oscuro y texto blanco,
con estilo de aplicación para cubrir tanto widgets como elementos del grafo.

## Pendientes y siguiente paso
- Ninguno.
