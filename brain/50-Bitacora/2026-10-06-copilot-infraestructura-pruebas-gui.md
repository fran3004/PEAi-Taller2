---
tipo: bitacora
estado: revisado
creado: 2026-10-06
actualizado: 2026-10-06
relacionado:
  - "[[GUI-Diseno-Python]]"
  - "[[2026-10-06-antigravity-pie-institucional-responsive]]"
origen: "Solicitud de aislamiento de pruebas GUI respecto al entorno grafico del equipo"
agente: "Copilot"
rama: "master"
---

# Infraestructura de pruebas GUI

## Objetivo

Evitar que las pruebas de PySide6 dependan de que cada desarrollador configure manualmente `QT_QPA_PLATFORM=offscreen` o `PEA_SIN_ANIMACIONES`.

## Cambios

- Se agrego `tests/conftest.py`, cargado por pytest antes de los fixtures de `pytest-qt`.
- La infraestructura de pruebas fuerza `QT_QPA_PLATFORM=offscreen` y `PEA_SIN_ANIMACIONES=1` antes de crear cualquier `QApplication`.
- No se modifico el arranque de produccion ni la configuracion de `pea.gui`.
- Se agrego una regresion parametrizada para 1100x700, 1366x768 y 1920x1080. Verifica el backend offscreen y que cada ventana conserve exactamente el tamano logico solicitado, sin consultar el monitor fisico.

## Verificacion

- `pytest tests/unit -v` sin variables de entorno manuales: 215 pasaron y 1 fue deseleccionada.
- `pytest tests/unit/test_gui_completa.py -q` sin variables manuales: 21 pasaron.
- `ruff check src tests`: aprobado.
- Las pruebas graficas y la autoprueba invocada desde pytest heredan el backend offscreen y las animaciones desactivadas.
