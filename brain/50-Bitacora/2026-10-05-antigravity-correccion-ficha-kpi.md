---
tipo: bitacora
estado: revisado
creado: 2026-10-05
actualizado: 2026-10-05
relacionado:
  - "[[GUI-Diseno-Python]]"
  - "[[2026-10-05-antigravity-auditoria-qa-gui]]"
origen: "Corrección de tamaño y visibilidad de lbl_valor en FichaKPI"
agente: "Antigravity"
rama: "master"
commit: "fix: corregir politica de tamano de lbl_valor en FichaKPI para asegurar visibilidad"
---

# Bitácora · Corrección de Visibilidad en FichaKPI

## Objetivo
Resolver el fallo visual en [`FichaKPI`](file:///c:/dev/PEAi-Taller2/src/pea/gui/componentes/tarjeta_kpi.py), donde la política de tamaño `QSizePolicy.Policy.Ignored` junto con el espaciador elástico `addStretch()` colapsaba el ancho de `lbl_valor` a 0 píxeles, haciendo invisibles los valores numéricos destacados en las pantallas de Inicio, Investigadores, Grupos y Redes.

## Qué se hizo
- En [`src/pea/gui/componentes/tarjeta_kpi.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/componentes/tarjeta_kpi.py):
  - Se modificó la política de tamaño de `self.lbl_valor` de `Ignored` a `QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed`.
  - Se removió la restricción rígida `setMinimumWidth(0)` para permitir que la etiqueta informe su `sizeHint` basado en la tipografía (`TAMANO_KPI` pt en negrita).
  - Se mantuvo intacto el diseño general, el espaciador horizontal y la posición alineada a la derecha del `Minigrafico` cuando está presente.
- En [`tests/unit/test_componentes_gui.py`](file:///c:/dev/PEAi-Taller2/tests/unit/test_componentes_gui.py):
  - Se añadió la prueba de regresión `test_ficha_kpi_ancho_util_y_visibilidad_lbl_valor` que verifica que `lbl_valor` es visible, tiene ancho útil ($\ge 15$ px), preserva el texto formateado tras invocar `actualizar()` y conserva la posición relativa del minigráfico a la derecha del número.

## Comandos y resultados
1. `ruff check src tests`:
   - Salida: `All checks passed!`
2. `pytest tests/unit/test_componentes_gui.py -v`:
   - Salida: 12 passed en 1.27s (incluyendo la nueva prueba de regresión).
3. `pytest tests/unit -v` (con `QT_QPA_PLATFORM=offscreen` y `PEA_SIN_ANIMACIONES=1`):
   - Salida: 196 passed, 1 deselected en 69.01s.
4. `python -m pea.gui --autoprueba`:
   - Salida: 24 capturas generadas con 0 barras horizontales y confirmación visual de cifras destacadas legibles en Inicio, Investigadores y Grupos.
5. `python tools/brain/verificar_brain.py`:
   - Salida: 103 notas inspeccionadas, 0 errores, 0 advertencias.

## Decisiones
- Se adoptó `QSizePolicy.Policy.Preferred` para `lbl_valor` porque respeta el `sizeHint` del texto numérico formateado sin impedir que el layout asigne espacio adicional si fuera necesario, mientras que el `addStretch()` adyacente absorbe el espacio restante y mantiene el minigráfico en el extremo derecho.

## Pendientes y siguiente paso
- Continuar con el siguiente elemento del backlog de la auditoría QA: reconstruir la maquetación de [`FichaProducto`](file:///c:/dev/PEAi-Taller2/src/pea/gui/pantallas/productos.py) (eliminar píldoras huérfanas en 0,0 y solucionar solapamiento de textos en metadatos y autores).
