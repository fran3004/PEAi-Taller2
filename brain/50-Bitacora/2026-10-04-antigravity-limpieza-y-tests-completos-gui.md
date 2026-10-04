---
tipo: bitacora
estado: revisado
creado: 2026-10-04
actualizado: 2026-10-04
relacionado:
  - "[[00-Inicio]]"
  - "[[GUI-Diseno-Python]]"
  - "[[ADR-0011-Paridad-arquitectural-Python-Cpp]]"
  - "[[ADR-0012-Diseno-GUI-y-navegacion]]"
  - "[[ADR-0016-Alcance-de-pantallas-y-datos-del-boceto]]"
  - "[[ADR-0017-Tecnologia-de-interfaz-Qt-Widgets]]"
origen: "Limpieza de pantallas obsoletas, consolidación de autoprueba y suite completa de pruebas GUI PySide6"
agente: "Antigravity"
rama: "feat/gui-rediseno-faf"
commit: "refactor: limpieza de pantallas obsoletas y reescritura de suite de pruebas gui"
---

# Bitácora · Limpieza de Pantallas Obsoletas y Suite Completa de Pruebas GUI

## Objetivo
Finalizar la consolidación de la interfaz gráfica institucional de PEA-i (PySide6) según [[GUI-Diseno-Python]]:
1. Eliminar los archivos legados de `src/pea/gui/pantallas/` (`pantalla_*.py`), el módulo de gráficos antiguos (`antiguos.py`) y la barra de filtros previa (`BarraFiltroAnios`).
2. Desacoplar las instancias obsoletas en `src/pea/gui/ventana_principal.py` reteniendo exclusivamente los 8 módulos oficiales (`Pantalla.INICIO` a `Pantalla.ACERCA`).
3. Actualizar `ejecutar_autoprueba` para generar capturas canónicas con el patrón `pantalla_<nn>_<nombre>_<ancho>x<alto>.png` en las tres resoluciones oficiales (1100×700, 1366×768, 1920×1080) asegurando `PEA_SIN_ANIMACIONES=1`.
4. Reescribir `tests/unit/test_gui_completa.py` y actualizar `tests/unit/test_cli_gui.py` para validar de forma integral la nueva arquitectura (7 pestañas, navegación cruzada, filtros globales reactivos, fichas laterales, pila de deshacer, importación con cola, exportaciones CSV con BOM y gráficos PNG, análisis de redes y franjas de aviso/sin conexión).
5. Validar la ausencia de etiquetas en inglés y colores quemados fuera de `estilo.py`.

## Qué se hizo
1. **Eliminación de archivos legados**:
   - Se removieron de git los 9 archivos en `src/pea/gui/pantallas/`:
     * `pantalla_acerca.py`
     * `pantalla_conectar.py`
     * `pantalla_cruzada.py`
     * `pantalla_gestion.py`
     * `pantalla_grupo.py`
     * `pantalla_importar.py`
     * `pantalla_investigador.py`
     * `pantalla_producto.py`
     * `pantalla_resumen.py`
   - Se eliminó `src/pea/gui/componentes/graficos/antiguos.py` y se sanearon las exportaciones en `graficos/__init__.py`.
   - Se retiró la clase `BarraFiltroAnios` de `src/pea/gui/componentes/filtro_anios.py` y de `componentes/__init__.py`, preservando los componentes canónicos `ChipVentana`, `PopoverFiltroAnios` y `texto_resumen_filtro`.

2. **Limpieza de `VentanaPrincipal` (`src/pea/gui/ventana_principal.py`)**:
   - Eliminación de referencias a clases obsoletas (`PantallaCruzada`, `PantallaGestion`, `PantallaGrupo`, `PantallaInvestigador`, `PantallaProducto`, `PantallaResumen`).
   - Apilador central estandarizado en las 8 pantallas oficiales (`[self._pantalla_inicio, self._pantalla_investigadores_modulo, self._pantalla_grupos_modulo, self._pantalla_productos_modulo, self._pantalla_redes_modulo, self._pantalla_importar, self._pantalla_configuracion_modulo, self._pantalla_acerca]`).
   - Incorporación del método institucional `mostrar_aviso_revision(rev_local, rev_remota)` y sincronización del banner de aviso.
   - Sustitución de colores quemados (`#7CC7F0`) por el token central `ACENTO`.

3. **Consolidación de Autoprueba (`ejecutar_autoprueba`)**:
   - Configuración explícita `os.environ["PEA_SIN_ANIMACIONES"] = "1"`.
   - Generación de capturas de las 8 pantallas en las 3 resoluciones oficiales (`1100x700`, `1366x768`, `1920x1080`):
     * `pantalla_00_inicio_<ancho>x<alto>.png`
     * `pantalla_01_investigadores_<ancho>x<alto>.png`
     * `pantalla_02_grupos_<ancho>x<alto>.png`
     * `pantalla_03_productos_<ancho>x<alto>.png`
     * `pantalla_04_redes_<ancho>x<alto>.png`
     * `pantalla_05_importar_<ancho>x<alto>.png`
     * `pantalla_06_configuracion_<ancho>x<alto>.png`
     * `pantalla_07_acerca_<ancho>x<alto>.png`
     (Total: 24 capturas verificadas).

4. **Reescritura de pruebas unitarias (`tests/unit/test_gui_completa.py`)**:
   - `test_ventana_principal_estructura_siete_pestanas`: verifica las 4 zonas, 7 pestañas institucionales («Inicio», «Investigadores», «Grupos», «Productos», «Análisis de redes», «Importar», «Configuración»), botones de deshacer, avatar, sesión y chips de estado vivo del pie.
   - `test_navegacion_entre_todas_las_pantallas`: navegación secuencial por las 8 pantallas del enum `Pantalla`.
   - `test_navegacion_cruzada_entre_pantallas`: flujos de interacción cruzada (Inicio → Redes, Investigadores → Productos, Grupos → Productos, Productos → Investigador, Redes → Investigador, Acerca de → Inicio).
   - `test_filtros_globales_y_reactividad`: cambio global de ventana temporal (`FiltroAnios`) y propagación a los módulos.
   - `test_fichas_laterales_directorios`: presencia y reactividad de `_ficha_lateral` en Investigadores, Grupos y Productos.
   - `test_creacion_edicion_y_pila_deshacer`: integración de operaciones, activación de `_btn_deshacer`, apertura de `PopoverHistorial` y reversión mediante deshacer.
   - `test_pantalla_importar_cola_ingesta`: encolado de archivos CSV y reflejo en la tabla de cola FIFO.
   - `test_exportacion_tabla_csv_y_grafico_png`: exportación de datos con BOM UTF-8 y renderizado vectorial de `GraficoBarrasApiladas` a PNG.
   - `test_pantalla_redes_componentes_y_metricas`: carga de `VistaRed` y panel de métricas.
   - `test_estados_vacio_aviso_y_sin_conexion`: comprobación de franja roja sin conexión y franja ámbar de revisión remota.
   - `test_responsividad_adaptativa_ventana`: adaptación de barra superior y pie ante las resoluciones 1360×820, 1200×820 y 1100×700.

5. **Corrección de bug en `seleccionar_investigador`**:
   - Corrección en `src/pea/gui/pantallas/investigadores.py` donde se invocaba `src.registro_en_fila(row)` en lugar del método existente `src.registro(row)` en `ModeloDirectorioInvestigadores`.

## Comandos y resultados
- `git rm src/pea/gui/pantallas/pantalla_*.py src/pea/gui/componentes/graficos/antiguos.py`: 10 archivos eliminados de git.
- `ruff check src tests`: Exitoso, 0 errores ("All checks passed!").
- `pytest tests/unit/test_cli_gui.py -v`: 5 passed en 12.90s.
- `pytest tests/unit/test_gui_completa.py -v`: 11 passed en 13.34s.
- `python -m pea.gui --autoprueba`: Exitoso, 24 capturas generadas bajo `datos/capturas/` sin excepciones.
- `pytest tests/unit`: 168 passed, 1 deselected en 53.18s.
- `python tools/brain/verificar_brain.py`: Verificación de la bóveda de Obsidian.

## Decisiones
- Se consolidó la autoprueba para generar nombres correlativos `pantalla_00_inicio_...` a `pantalla_07_acerca_...` alineados con el enum `Pantalla` y el criterio de aceptación de [[GUI-Diseno-Python]].
- Se removió por completo `BarraFiltroAnios` al estar completamente reemplazada por el componente `ChipVentana` y su popover accesible.

## Pendientes y siguiente paso
- La interfaz gráfica de Python (PySide6) se encuentra 100% completada, verificada y libre de componentes heredados.
- El siguiente paso corresponde a la integración final o a los desarrollos en C++ en fases posteriores.
