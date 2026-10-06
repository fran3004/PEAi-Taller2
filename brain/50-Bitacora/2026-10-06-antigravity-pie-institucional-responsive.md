---
tipo: bitacora
estado: revisado
creado: 2026-10-06
actualizado: 2026-10-06
relacionado:
  - "[[GUI-Diseno-Python]]"
  - "[[2026-10-06-antigravity-correccion-glifos-iconos-svg-accesibilidad]]"
origen: "Corrección de responsividad del pie institucional en ventana_principal.py para resoluciones compactas (1100x700, 1366x768, 1920x1080)"
agente: "Antigravity"
rama: "master"
commit: "fix: corregir responsividad de pie institucional en ventana principal"
---

# Bitácora · Responsividad del Pie Institucional en Ventana Principal

## Objetivo
Corregir la responsividad del pie institucional (`_pie`) en `src/pea/gui/ventana_principal.py` para que en resolución compacta (1100×700) no se oculte la información institucional:
1. Eliminar la anulación total que realizaba `resizeEvent` al ocultar `_caja_texto_pie` en ventanas compactas (`alto < 760`).
2. Diseñar un modo compacto para el pie que conserve la primera línea institucional legible (`l1`), reduzca u oculte únicamente información secundaria (`l2`), y mantenga siempre visibles todos los indicadores de estado en tiempo real (`_lbl_estado_conexion`, `_chip_revision`, `_chip_deshacer`, `_chip_cola`).
3. Adaptar las proporciones del contenedor de logotipo UPC (`_pastilla_logo`) y márgenes verticales para que encajen con elegancia dentro de la altura compacta (44 px) sin desbordamiento ni recortes.
4. Mantener cero barras de desplazamiento horizontal (`ScrollBarAlwaysOff`), sin alterar la altura mínima de la ventana ni usar artificios mágicos.
5. Verificar el comportamiento en las tres resoluciones oficiales: 1100×700, 1366×768 y 1920×1080, e incorporar pruebas automatizadas en `tests/unit/test_gui_completa.py`.

## Diagnóstico y Causa Raíz
- En la implementación anterior de `resizeEvent`, las líneas 1236–1238 ejecutaban:
  ```python
  modo_pie_compacto = alto < 760
  self._caja_texto_pie.setVisible(not modo_pie_compacto)
  self._pie.setFixedHeight(44 if modo_pie_compacto else 72)
  ```
  Esto provocaba que en la resolución mínima soportada de 1100×700 (`alto = 700 < 760`), el pie institucional quedara totalmente desprovisto de identificación institucional, mostrando únicamente el logotipo, la palabra "PEA-i" y los chips a la derecha, dejando un vacío central.
- Además, `_pastilla_logo` tenía un tamaño fijo de 52×52 px (`lbl_upc` 42×42 px). Al forzar `_pie.setFixedHeight(44)`, la pastilla excedía los límites del pie (44 px) colisionando con los márgenes de 8 px superior e inferior.
- No existía jerarquía entre la información institucional primaria (Universidad Popular del Cesar / Ingeniería de Sistemas) y la secundaria (Taller 2 / SCIENTI / Modelo 2024), por lo que se ocultaba todo en lugar de adaptar el contenido al espacio disponible.

## Qué se hizo
1. **Jerarquización y Adaptabilidad en `_crear_pie_institucional`**:
   - Se guardaron referencias directas a `self._lbl_pie_l1`, `self._lbl_pie_l2`, `self._layout_pie`, `self._lbl_upc`, `self._zona_vivo_pie` y `self._zona_vivo_layout`.
   - Se añadió un *tooltip* institucional completo en `_caja_texto_pie` con ambas líneas:
     - Primaria: "Universidad Popular del Cesar · Facultad de Ingenierías y Tecnológicas · Ingeniería de Sistemas".
     - Secundaria: "Taller 2 de Estructura de Datos · Datos de SCIENTI (Minciencias) · Modelo de Medición 2024 (M601PR04G01)".
2. **Modo Compacto Proporcional en `resizeEvent`**:
   - Se activó el modo compacto cuando `alto < 760 or ancho < 1240`.
   - Altura del pie: 44 px en compacto vs. 72 px en resolución estándar.
   - Dimensiones de `_pastilla_logo`: 34×34 px (con icono UPC de 26×26 px y márgenes de 4 px) en compacto, frente a 52×52 px (icono 42×42 px) en estándar.
   - Márgenes y espaciado de layout: márgenes `(16, 4, 16, 4)` y espaciado `10` px en compacto; `(20, 8, 20, 8)` y espaciado `16` px en estándar.
   - Espaciado en bloque de estado vivo (`_zona_vivo_layout`): 6 px en compacto; 10 px en estándar.
   - Conservación del texto institucional:
     - `self._caja_texto_pie.setVisible(True)` y `self._lbl_pie_l1.setVisible(True)` en todo momento.
     - En anchos `< 1240` px (incluyendo 1100×700): `_lbl_pie_l1` muestra `"Universidad Popular del Cesar · Ingeniería de Sistemas"` (ancho de avance tipográfico ~341 px con Inter 9 pt, dejando >200 px libres en el stretch central).
     - En anchos `>= 1240` px: `_lbl_pie_l1` muestra el texto completo `"Universidad Popular del Cesar · Facultad de Ingenierías y Tecnológicas · Ingeniería de Sistemas"`.
     - `_lbl_pie_l2` se oculta únicamente en modo compacto (`setVisible(not modo_pie_compacto)`).
   - Todos los indicadores de estado en vivo (`_lbl_estado_conexion`, `_chip_revision`, `_chip_deshacer`, `_chip_cola`) permanecen 100% visibles en todas las resoluciones.
3. **Pruebas Automatizadas en `tests/unit/test_gui_completa.py`**:
   - Se actualizó `test_responsividad_adaptativa_ventana` para verificar que la línea 1 y los 4 chips de estado permanezcan visibles en 1100×700.
   - Se incorporó la prueba `test_responsividad_pie_institucional_resoluciones_oficiales`, que valida exhaustivamente:
     - 1100×700: altura 44 px, pastilla 34×34 px, L1 con texto compacto, L2 oculta, 4 indicadores visibles.
     - 1366×768: altura 72 px, pastilla 52×52 px, L1 con texto completo, L2 visible, 4 indicadores visibles.
     - 1920×1080: altura 72 px, pastilla 52×52 px, L1 con texto completo, L2 visible, 4 indicadores visibles.

## Verificación
- `ruff check src/pea/gui/ventana_principal.py tests/unit/test_gui_completa.py`: 0 advertencias, estilo impecable.
- `pytest tests/unit/test_gui_completa.py`: 15 pruebas pasadas.
- `pytest tests/unit`: 212 pruebas unitarias pasadas (1 deseleccionada por red).
- `python -m pea.gui --autoprueba`: 24 combinaciones (8 pantallas × 3 resoluciones) evaluadas con 0 barras de desplazamiento horizontal y 0 fallas.

## Pendientes y siguiente paso
- Ejecutar `tools/brain/verificar_brain.py` para certificar la bóveda.
- Realizar el commit correspondiente.

