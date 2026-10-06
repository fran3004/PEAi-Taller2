---
tipo: bitacora
estado: revisado
creado: 2026-10-06
actualizado: 2026-10-06
relacionado:
  - "[[GUI-Diseno-Python]]"
  - "[[2026-10-06-antigravity-tablas-responsive-investigadores-grupos]]"
origen: "Corrección transversal de glifos Unicode por caracteres ASCII seguros e iconos SVG en GUI"
agente: "Antigravity"
rama: "master"
commit: "fix: corregir transversalmente glifos unicode por caracteres ascii seguros e iconos svg"
---

# Bitácora · Corrección Transversal de Glifos Unicode por Caracteres ASCII e Iconos SVG

## Objetivo
Realizar una corrección transversal en la interfaz gráfica de usuario (PySide6) para sustituir glifos Unicode que no poseen representación fiable en Windows y provocan caracteres cuadrados ("tofu" o cajas vacías), especialmente en las pantallas de Grupos y Redes:
1. Reemplazar `▾` (U+25BE) en `ChipVentana` (`src/pea/gui/componentes/filtro_anios.py`) por el carácter ASCII seguro `v`, manteniendo el significado visual de menú desplegable y agregando *tooltip* descriptivo y nombre accesible.
2. Limpiar el botón «Exportar» en `Grupos`, `Inicio`, `Productos` e `Investigadores`, eliminando el glifo `▾` o espacios residuales para dejar un rótulo limpio («Exportar») respaldado por su `QMenu` nativo, con *tooltip* y nombre accesible (`setAccessibleName`).
3. En `Redes` (`src/pea/gui/pantallas/redes.py`):
   - Sustituir el glifo de menos Unicode `−` (U+2212) en `btn_zoom_menos` por el carácter ASCII seguro `-` (U+002D) con *tooltip* `Alejar lienzo (- / Rueda abajo)`.
   - Garantizar que los controles `+`, `-` y `Ajustar` cuenten con *tooltips* y nombres accesibles estandarizados.
   - Reemplazar los botones con flechas Unicode (`Ver ficha →`, etc.) por iconos SVG existentes del paquete (`investigadores.svg`, `limpiar.svg`), asignando *tooltips* y nombres accesibles.
4. En `FichaGrupo` (`grupos.py`) y `PantallaInicio` (`inicio.py`): sustituir los glifos de flecha matemática `⌄` (U+2304) y `⌃` (U+2303) del botón `btn_detalles` por los caracteres ASCII estándar `v` y `^` («Ver más detalles v» / «Ocultar detalles ^»), con *tooltips* y accesibilidad interactiva.
5. En `VentanaPrincipal`: sustituir el glifo `▾` del botón `btn_chevron` (historial de Deshacer) por el carácter ASCII `v` con *tooltip* `Abrir historial de operaciones` y nombre accesible.
6. En `Configuracion`: eliminar el glifo de triángulo `▶` (U+25B6) en el botón `btn_ejecutar` de verificación cruzada.
7. En `Acerca`: sustituir la flecha `←` en `btn_volver` por el icono SVG institucional existente `inicio.svg`.
8. En `MiniRed`: suprimir la flecha Unicode `→` en el pie dibujado con `QPainter`.
9. Añadir prueba integral automatizada y verificar responsividad en 1100×700, 1366×768 y 1920×1080.

## Diagnóstico y Causa Raíz
- Varios controles dependían de caracteres especiales del bloque de formas geométricas y flechas matemáticas de Unicode:
  - `▾` (U+25BE, *Black Down-Pointing Small Triangle*)
  - `−` (U+2212, *Minus Sign*)
  - `⌄` (U+2304, *Down Arrowhead*)
  - `⌃` (U+2303, *Up Arrowhead*)
  - `▶` (U+25B6, *Black Right-Pointing Triangle*)
- En Windows, cuando Qt renderiza texto utilizando fuentes del sistema o fuentes que carecen de dichos glifos en sus tablas CMAP específicas (o cuando DirectWrite no resuelve el fallback adecuado en QSS), estos caracteres se dibujan como rectángulos o cuadrados sin glifo ("tofu").
- Por el contrario, los caracteres ASCII estándar (`+`, `-`, `v`, `^`) y los recursos vectoriales SVG cargados mediante `QSvgRenderer` / `cargar_icono` tienen representación 100% garantizada y nítida en cualquier entorno y resolución.

## Qué se hizo
- [`src/pea/gui/componentes/filtro_anios.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/componentes/filtro_anios.py):
  - En `ChipVentana._actualizar_etiqueta`: sustituido `▾` por `v` (`f"Ventana: {desc}  v"`).
  - Añadido `setToolTip(f"Filtro de ventana temporal: {desc}. Clic para cambiar.")` y `setAccessibleName`.
- [`src/pea/gui/pantallas/grupos.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/pantallas/grupos.py):
  - `self.btn_exportar`: rótulo «Exportar» limpio, con `setToolTip` y `setAccessibleName`.
  - `self.btn_detalles`: textos «Ver más detalles v» y «Ocultar detalles ^», con `setToolTip` y `setAccessibleName`.
- [`src/pea/gui/pantallas/inicio.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/pantallas/inicio.py):
  - `self._btn_exportar`: rótulo «Exportar», con `setToolTip` y `setAccessibleName`.
  - `self._btn_detalles`: textos «Ver más detalles v» y «Ocultar detalles ^», con `setToolTip` y `setAccessibleName`.
  - `btn_abrir` (MiniRed): asignado icono SVG `redes.svg`, texto «Abrir análisis completo», `setToolTip` y `setAccessibleName`.
- [`src/pea/gui/pantallas/productos.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/pantallas/productos.py):
  - `self.btn_exportar`: rótulo «Exportar», con `setToolTip` y `setAccessibleName`.
- [`src/pea/gui/pantallas/investigadores.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/pantallas/investigadores.py):
  - `self._btn_exportar`: rótulo «Exportar», con `setToolTip` y `setAccessibleName`.
- [`src/pea/gui/pantallas/redes.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/pantallas/redes.py):
  - `self.btn_zoom_menos`: sustituido `−` por `-`, tooltip `Alejar lienzo (- / Rueda abajo)`, nombre accesible `Alejar lienzo`.
  - `self.btn_ver_investigador`: asignado icono SVG `investigadores.svg`, texto «Ver ficha», tooltip y nombre accesible.
  - `self.btn_deseleccionar`: asignado icono SVG `limpiar.svg`, tooltip y nombre accesible.
- [`src/pea/gui/ventana_principal.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/ventana_principal.py):
  - `self.btn_chevron` de `BotonDeshacerSuperior`: sustituido `▾` por `v`, asignado `setToolTip("Abrir historial de operaciones")` y `setAccessibleName`.
- [`src/pea/gui/pantallas/configuracion.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/pantallas/configuracion.py):
  - `self.btn_ejecutar`: texto «Ejecutar Verificación Cruzada» sin glifo `▶`, con tooltip y nombre accesible.
- [`src/pea/gui/pantallas/acerca.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/pantallas/acerca.py):
  - `self.btn_volver`: asignado icono SVG `inicio.svg`, texto «Volver al inicio», tooltip y nombre accesible.
- [`src/pea/gui/componentes/graficos/mini_red.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/componentes/graficos/mini_red.py):
  - Eliminada la flecha `→` del rótulo dibujado en pie.
- [`tests/unit/test_pantalla_redes.py`](file:///c:/dev/PEAi-Taller2/tests/unit/test_pantalla_redes.py):
  - Actualizadas aserciones para validar `-` en `btn_zoom_menos` y tooltip.
- [`tests/unit/test_pantallas_finales.py`](file:///c:/dev/PEAi-Taller2/tests/unit/test_pantallas_finales.py):
  - Incorporada la prueba integral `test_glifos_accesibilidad_y_tooltips_transversales` verificando la ausencia de glifos cuadrados, el uso de ASCII e iconos SVG, y la presencia de tooltips y accesibilidad en todos los controles impactados.

## Comandos y resultados
- `.\.venv\Scripts\ruff.exe check src tests` → `All checks passed!`
- `$env:QT_QPA_PLATFORM="offscreen"; .\.venv\Scripts\python.exe -m pytest tests/unit/test_pantallas_finales.py tests/unit/test_pantalla_redes.py` → `19 passed in 5.10s`
- `$env:QT_QPA_PLATFORM="offscreen"; .\.venv\Scripts\python.exe -m pytest tests/unit` → `323 passed in 30.65s` (100% de la suite pasando).
- `$env:QT_QPA_PLATFORM="offscreen"; $env:PEA_SIN_ANIMACIONES="1"; .\.venv\Scripts\python.exe -m pea.gui --autoprueba` → 21/21 verificaciones OK en las 7 pantallas x 3 resoluciones (1100×700, 1366×768, 1920×1080), 0 barras horizontales.
- `.\.venv\Scripts\python.exe tools/brain/verificar_brain.py` → 113 notas inspeccionadas, 0 errores, 0 advertencias.

## Decisiones
- Para botones de menú con desplegables nativos de Qt (`Exportar`), se eliminó el glifo `▾` del texto para evitar redundancia y cuadrados, permitiendo que el propio `QMenu` y el estilo del botón comuniquen su funcionalidad con rótulo limpio y accesible.
- Para botones de colapso/despliegue en fichas laterales (`btn_detalles`), se adoptaron los caracteres ASCII estándar `v` y `^`, universales y compatibles con cualquier sistema.
- Para botones de acción en fichas y modales (`Ver ficha`, `Volver al inicio`, `Deseleccionar`), se aprovecharon los iconos SVG oficiales existentes (`investigadores.svg`, `inicio.svg`, `limpiar.svg`), enriqueciendo la consistencia visual y eliminando glifos de flecha.

## Pendientes y siguiente paso
- Ejecutar `verificar_brain.py` y registrar el commit correspondiente.
