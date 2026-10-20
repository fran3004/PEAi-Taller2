---
tipo: bitacora
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[GUI-Diseno-Python]]"
origen: "Endurecimiento de la autoprueba visual de la GUI Python"
agente: "Copilot"
rama: "feat/python-cierre-francisco"
commit: ""
---

# Autoprueba visual estricta

## Objetivo
Hacer que la autoprueba de GUI ignore elementos alcanzables mediante
desplazamiento, detecte texto elidido sin tooltip y termine con error cuando
encuentre hallazgos.

## Qué se hizo
- La autoprueba comprueba las ocho pantallas en tres resoluciones y excluye
  widgets recortados que pueden alcanzarse mediante el desplazamiento de su
  `QScrollArea`.
- Se agregaron comprobaciones de elipsis sin tooltip para etiquetas, botones y
  encabezados de tabla. Los hallazgos ahora producen un código de salida
  distinto de cero y no se informa un éxito falso.
- Se eliminaron refrescos redundantes al seleccionar pantallas durante la
  autoprueba y se añadieron tooltips a textos de Inicio, Investigadores y Redes.
- Las zonas CSV y PDF ajustan el alto de sus etiquetas a su ancho real. A
  1100 × 700, las etiquetas principales miden 55 px y los subtextos 32 px,
  ambos según `heightForWidth`; la captura muestra completo el texto «aquí».
- Se conservó `scripts/diagnostico_desborde.py`: su diagnóstico no duplica la
  lógica de la autoprueba.

## Comandos y resultados
- `python -m pytest -q tests/unit/test_cli_gui.py tests/unit/test_pantallas_finales.py`:
  19 pasaron.
- `python -m ruff check src/pea/gui tests/unit/test_cli_gui.py tests/unit/test_pantallas_finales.py`:
  aprobado.
- `python -m pea.gui --autoprueba`: código 0; 24 combinaciones, cero barras
  horizontales, cero widgets inaccesibles y cero elipsis sin tooltip.
- Revisión visual de `datos/capturas/oficiales/pantalla_05_importar_1100x700.png`:
  el texto principal CSV y PDF se muestra completo.
- `python -m pytest -q`: 275 pasaron, 2 fallaron y 2 se omitieron. Fallaron
  `test_pantalla_grupos_tabla_responsive_y_elipsis` y
  `test_pantalla_investigadores_tabla_responsive_y_elipsis`; ambos fallos se
  reprodujeron individualmente. Se resolvieron en un seguimiento al ajustar
  los anchos mínimos de las columnas y fijar en esas pruebas la tipografía real.
- `git diff --check`: sin errores.

## Decisiones
Se conserva el cambio instantáneo de pantalla sin efectos de opacidad. Para
los textos envolventes de Importar, se asigna como alto mínimo el resultado
de `heightForWidth` del ancho actual, evitando depender solo del tooltip.

## Pendientes y siguiente paso
- Ejecutar la suite completa después del seguimiento de tablas responsivas.
- Continuar con la tarea 6: histograma real calculado desde el hipercubo.
