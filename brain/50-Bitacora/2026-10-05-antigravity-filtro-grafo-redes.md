---
tipo: bitacora
estado: revisado
creado: 2026-10-05
actualizado: 2026-10-05
relacionado:
  - "[[GUI-Diseno-Python]]"
  - "[[ADR-0015-Analisis-de-red-nativo]]"
  - "[[2026-10-05-antigravity-auditoria-qa-gui]]"
origen: "Corrección de filtro inicial de coautorías, controles de zoom y panel de redes"
agente: "Antigravity"
rama: "master"
commit: "fix: corregir filtro inicial de coautorias, controles de zoom y panel en redes"
---

# Bitácora · Corrección de Filtro Inicial de Coautorías, Controles de Zoom y Panel en Redes

## Objetivo
Corregir los defectos detectados en la pantalla de Análisis de Redes de Colaboración (`src/pea/gui/pantallas/redes.py`):
1. Iniciar el filtro de coautorías en «Mín. 1 coautoría» (`_min_coautorias_actual = 1`, índice 0 en `combo_min_coautorias`) para que el grafo y sus enlaces sean visibles de inmediato con los datos de demostración cargados.
2. Eliminar el `QLabel` huérfano `lbl_titulo_metricas` creado con `parent=self` sin layout, el cual provocaba texto residual superpuesto sobre el título de la pantalla.
3. Asegurar que los botones de zoom y ajuste (`+`, `−`, `Ajustar`) muestren sus símbolos y texto nítidamente, tengan contraste WCAG adecuado con tokens oficiales de `estilo.py`, tamaño consistente (30 px de altura) y tooltips accesibles.
4. Preservar la retención de tareas asíncronas en `EjecutorAsincrono` para evitar que el recolector de basura de Python destruya prematuramente las tareas de fondo antes de entregar los resultados al hilo principal.

## Qué se hizo
- En [`src/pea/gui/pantallas/redes.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/pantallas/redes.py):
  - Se cambió el valor inicial de `_min_coautorias_actual` de 2 a 1 en `__init__()`, y se seleccionó el índice 0 en `combo_min_coautorias`. Se actualizaron los fallbacks a `1` en `refrescar()` y `_al_cambiar_min_coautorias()`.
  - Se eliminó la instancia huérfana `self.lbl_titulo_metricas = QLabel("Métricas de centralidad", self)` en `_crear_panel_metricas()`, dejando que `Tarjeta` gestione su propio encabezado estilizado de forma limpia.
  - Se rediseñaron los estilos y dimensiones de `btn_zoom_mas`, `btn_zoom_menos` y `btn_zoom_ajustar`:
    - Se fijaron dimensiones de 30×30 px para `btn_zoom_mas` y `btn_zoom_menos`, y altura de 30 px con ancho mínimo de 64 px para `btn_zoom_ajustar`.
    - Se agregó `padding: 0px; margin: 0px;` en `estilo_zoom_btn` para anular el padding global de `QPushButton` (16 px a cada lado) que provocaba el colapso y recorte a 0 px de los glifos `+` y `−`.
    - Se aplicaron colores oficiales `{TEXTO}` sobre `{SUPERFICIE}` con borde `{LINEA}`, hover con borde `{PRIMARIO}` y foco con borde `{ACENTO}`.
    - Se asignaron tooltips descriptivos y nombres accesibles: «Acercar lienzo (+ / Rueda arriba)», «Alejar lienzo (− / Rueda abajo)» y «Ajustar vista al contenido completo».
    - En `_ajustar_distribucion()`, se garantizó que `btn_zoom_ajustar` mantenga siempre el texto «Ajustar» y `btn_reordenar` conserve «Reordenar», eliminando el truncamiento a flechas o texto incompleto en resolución compacta.
- En [`src/pea/gui/ejecutor.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/ejecutor.py):
  - Se implementó retención de tareas en `EjecutorAsincrono` (`self._tareas_activas: set[TareaSegundoPlano]`), conectando su remoción al término o fallo de la tarea, asegurando que las señales y callbacks Qt entre hilos se entreguen con total confiabilidad en todo el ciclo de vida de la aplicación.
- En [`src/pea/gui/ventana_principal.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/ventana_principal.py):
  - En `ejecutar_autoprueba()`, se sincronizó la finalización de hilos secundarios con `QThreadPool.globalInstance().waitForDone(3000)` tras invocar `p_widget.refrescar()`, permitiendo que el grafo renderice con datos reales en todas las capturas oficiales.
- En [`tests/unit/test_pantalla_redes.py`](file:///c:/dev/PEAi-Taller2/tests/unit/test_pantalla_redes.py):
  - Se actualizó `test_pantalla_redes_construccion_y_componentes` para verificar que el combo inicie en índice 0 con dato 1, que no exista `lbl_titulo_metricas` como atributo huérfano, que el panel contenga su título a través de `Tarjeta._lbl_titulo` y que los botones de zoom tengan dimensiones de 30 px y tooltips no vacíos.
  - Se actualizó `test_pantalla_redes_reencuadra_grafo_y_pliega_panel` comprobando que en resolución 1100×700 los botones conserven sus textos completos «Ajustar» y «Reordenar».
  - Se agregó la prueba `test_pantalla_redes_filtro_inicial_y_demostracion`, que valida el filtro inicial en 1, la presencia inmediata de nodos y aristas en el grafo de demostración y la accesibilidad de los controles.

## Comandos ejecutados y resultados
- `ruff check src tests`: 0 errores, comprobaciones aprobadas.
- `pytest tests/unit/test_pantalla_redes.py -v`: 10 pruebas pasadas exitosamente (10/10 OK en 9.77s).
- `pytest tests/unit/test_gui_completa.py -v`: 12 pruebas pasadas exitosamente (12/12 OK en 26.76s).
- `pytest tests/unit/test_estilo_recursos.py -v`: 20 pruebas pasadas exitosamente (20/20 OK, incluyendo guardián de estilos sin literales).
- `python -m pea.gui --autoprueba`: 24 capturas regeneradas en `datos/capturas/oficiales/` (1100×700, 1366×768, 1920×1080); `pantalla_04_redes_*.png` muestra el grafo cargado con 12 investigadores, 4 aristas, leyenda, panel lateral y botones `+`, `−`, `Ajustar` nítidos.

## Riesgos y mitigaciones
- **Sincronización de hilos en pruebas**: las pruebas unitarias que no pasan por `EjecutorAsincrono` ejecutan síncronamente; aquellas con hilos procesan eventos mediante `QThreadPool.waitForDone()`.
