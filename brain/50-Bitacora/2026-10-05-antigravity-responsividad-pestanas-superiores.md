---
tipo: bitacora
estado: revisado
creado: 2026-10-05
actualizado: 2026-10-05
relacionado:
  - "[[GUI-Diseno-Python]]"
  - "[[2026-10-05-antigravity-auditoria-qa-gui]]"
origen: "Corrección de responsividad de BotonPestanaSuperior y ancho real con QFontMetrics"
agente: "Antigravity"
rama: "master"
commit: "fix: corregir responsividad de pestanas superiores y calculo con qfontmetrics"
---

# Bitácora · Responsividad de Pestañas Superiores y Ancho Real con QFontMetrics

## Objetivo
Corregir los defectos de responsividad en los botones de pestaña de la barra superior institucional ([`src/pea/gui/ventana_principal.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/ventana_principal.py)):
1. Eliminar el tope rígido arbitrario de `setMaximumWidth(130)` y la falta de `sizeHint()`/`minimumSizeHint()` en `BotonPestanaSuperior`, que causaba que pestañas como «Investigadores», «Análisis de redes» y «Configuración» colapsaran a 80 px o truncaran sus etiquetas en resoluciones amplias.
2. Implementar un cálculo dinámico de ancho con `QFontMetrics` sobre la variante en negrita del texto (`estilo.TAMANO_AUXILIAR`) más un margen de respiración simétrico de 28 px (14 px por lado), garantizando que las siete pestañas muestren siempre sus rótulos completos sin rozar los bordes ni truncarse.
3. Asegurar que en 1366×768 y 1920×1080 las siete pestañas se muestren completas con espaciado natural, mientras que en resolución compacta (1100×700) se active el modo de solo ícono con tooltip accesible (`ancho < 1120`).
4. Reubicar la píldora «Datos de demostración» en la fila de marca junto a «PEA-i» dentro de `caja_textos_marca` para evitar el crecimiento excesivo de la zona izquierda a 400+ px, liberando más de 120 px de espacio central para las pestañas.
5. Preservar todas las pestañas, atajos (`Ctrl+1` a `Ctrl+7`) y tokens de estilo de `estilo.py`.
6. Añadir pruebas de regresión unitarias automatizadas que verifiquen las métricas tipográficas y la responsividad de los botones en las diferentes resoluciones.

## Qué se hizo
- En [`src/pea/gui/ventana_principal.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/ventana_principal.py):
  - Se importó `QFontMetrics` desde `PySide6.QtGui`.
  - En `BotonPestanaSuperior`:
    - Se implementó `_calcular_ancho_completo(self) -> int` utilizando `QFontMetrics.horizontalAdvance(self._texto)` con fuente en negrita y margen de 28 px (`max(76, ancho_texto + 28)`).
    - Se implementaron `sizeHint()` y `minimumSizeHint()` retornando `QSize(ancho_completo, 64)` en modo normal y `QSize(54, 64)` en modo compacto.
    - En `establecer_modo_compacto()`, al salir de compacto se eliminó el tope rígido de 130 px (`setMaximumWidth(16777215)`), se asignó `setMinimumWidth(ancho_completo)` y se invocó `updateGeometry()`.
    - En `paintEvent()`, se ajustaron los radios a `estilo.RADIO_PESTANA_ACTIVA` y se centró la etiqueta horizontalmente sobre todo el ancho del botón (`QRectF(0, 38, float(rect.width()), 20)`).
  - En `_crear_barra_superior()`:
    - Se integró `self._pildora_demo` en `fila_marca` junto al rótulo `PEA-i`, evitando que desborde verticalmente ni ensanche horizontalmente `_zona_marca` de forma desproporcionada.
- En [`tests/unit/test_gui_completa.py`](file:///c:/dev/PEAi-Taller2/tests/unit/test_gui_completa.py):
  - Se agregó la prueba de regresión `test_responsividad_botones_pestanas_superior`, validando:
    - En 1366×768 y 1920×1080: `_modo_compacto == False`, ancho $\ge$ avance de texto + 20 px en todos los botones, ancho $\ge 110$ px en «Investigadores», $\ge 128$ px en «Análisis de redes» y $\ge 110$ px en «Configuración», y ausencia del tope de 130 px.
    - En 1100×700: `_modo_compacto == True`, ancho fijo de 54 px y tooltips coincidentes con el texto de cada pestaña.
    - Verificación de `sizeHint()` normal y compacto.

## Comandos ejecutados y resultados
- `ruff check src tests`: Todos los archivos aprobados (0 errores, 0 advertencias).
- `pytest tests/unit/test_gui_completa.py -v`: 13/13 pruebas aprobadas en 10.11s.
- `python -m pea.gui --autoprueba`: 24 capturas generadas satisfactoriamente en `datos/capturas/oficiales/`.
  - En `pantalla_00_inicio_1366x768.png` y `1920x1080.png`: las siete pestañas («Inicio», «Investigadores», «Grupos», «Productos», «Análisis de redes», «Importar», «Configuración») muestran sus textos completos, sin truncamiento, sin solapamiento y con espaciado simétrico.
  - En `pantalla_00_inicio_1100x700.png`: las siete pestañas se presentan en modo compacto (54 px) con ícono centrado y tooltip accesible.
- `scripts/diagnostico_desborde.py`: `Areas con barra horizontal visible: ninguna` en 1100×700, 1366×768 y 1920×1080.
- `pytest tests/unit/test_estilo_recursos.py::test_guardian_estilos_sin_literales_en_gui`: Aprobado (1/1 OK).
- `pytest tests/unit -v`: **205 pasadas**, 1 deseleccionada (red) en 90.28s.
