---
tipo: bitacora
estado: revisado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[_Indice]]"
  - "[[GUI-paridad]]"
  - "[[ADR-0012-Diseno-GUI-y-navegacion]]"

  - "[[SPEC]]"
  - "[[Contrato-de-datos]]"
  - "[[Hipercubo]]"
origen: "Construcción completa de la interfaz gráfica de usuario en Python (PySide6) con arquitectura desacoplada por capas"
agente: "antigravity"
rama: "master"
commit: "pendiente"
---

# Bitácora · Interfaz Gráfica de Usuario PySide6 (PEA-i)

## Objetivo
Implementar la interfaz gráfica de escritorio completa en Python con **PySide6** conforme a [[GUI-paridad]], [[ADR-0012-Diseno-GUI-y-navegacion]] y [[SPEC]], manteniendo estricta separación de capas arquitectónicas (la GUI nunca accede directamente a Supabase, SQL ni a estructuras internas hechas a mano, interactuando exclusivamente a través de la fachada de servicios y modelos DTO inmutables). Integrar las 9 pantallas reglamentarias, control de estado de conexión, revisión remota (`meta.revision`) con banner de detección de cambios externos, sistema de deshacer con reversión completa en estructuras y base de datos, gráficos nativos con `QPainter` y exportación a PNG y CSV, cola visual de ingesta y modo de autoprueba automatizado *offscreen* con captura de pantallas y código de retorno 0.


## Qué se hizo

1. **Capa de Fachada y Modelos de Vista (`src/pea/servicios/`)**:
   - `ServicioAplicacion`: fachada unificada que orquesta el catálogo de investigación, ingesta en segundo plano, estadísticas sobre el hipercubo 5D, exportación y verificación cruzada.
   - `vistas.py`: DTOs inmutables desacoplados (`TablaDatos`, `EstadoAplicacion`, `FiltroAnios`, `ModoConexion`, `ModoFiltroAnios`).
   - `datos_demostracion.py`: conjunto de datos ficticio de prueba con prefijo `PRUEBA-` y `es_ejemplo=True` (3 grupos, 12 investigadores, 42 productos).
   - `servicio_exportacion.py`: exportación canónica de `TablaDatos` a CSV con codificación UTF-8 con BOM (`utf-8-sig`).
   - `servicio_verificacion_cruzada.py`: ejecución y cotejo automatizado del CLI Python contra el ejecutable C++ (`cpp/build/pea-cpp.exe`).

2. **Componentes Gráficos Reutilizables y Estilo Institucional (`src/pea/gui/componentes/`)**:
   - `estilo.py`: paleta institucional de la Universidad Popular del Cesar (`#003366`, `#0D47A1`, `#006633`) y hoja de estilos global Qt.
   - `ejecutor.py`: ejecución asíncrona mediante `QThreadPool` y `QRunnable` para garantizar que ninguna petición de red, importación o verificación cruzada bloquee el hilo de interfaz.
   - `modelo_tabla.py`: adaptador `ModeloTabla(QAbstractTableModel)` sobre `TablaDatos`.
   - `graficos.py`: componentes nativos de renderizado vectorial con `QPainter` (`GraficoBarras`, `GraficoTorta`, `GraficoSeries`) con exportación directa a imágenes PNG de alta resolución sin dependencias de navegadores ni servidores web.
   - `tarjeta_kpi.py`: tarjeta métrica para paneles de mando y estadísticas.
   - `filtro_anios.py`: barra interactiva con soporte para todos los años, últimos $N$ años, rango manual y ventana normativa del Modelo 2024.

3. **Las Nueve Pantallas Oficiales (`src/pea/gui/pantallas/`)**:
   - **Pantalla 1 (`pantalla_conectar.py`)**: autenticación HTTPS contra Supabase (token volátil en memoria) y alternancia al modo demostración local.
   - **Pantalla 2 (`pantalla_resumen.py`)**: panel institucional con 4 tarjetas KPI, distribución por categoría (gráfico de sectores), tipologías por año (gráfico apilado/series) y top 5 investigadores y grupos.
   - **Pantalla 3 (`pantalla_grupo.py`)**: ficha de grupo, KPIs específicos, tabla de integrantes e indicadores de producción.
   - **Pantalla 4 (`pantalla_investigador.py`)**: ficha individual de investigador, métricas de vinculación y tabla de productos asociados en la multilista.
   - **Pantalla 5 (`pantalla_producto.py`)**: catálogo interactivo de productos con filtrado por tipología y validación, búsqueda textual y panel lateral de detalle técnico.
   - **Pantalla 6 (`pantalla_gestion.py`)**: panel de control CRUD para grupos, investigadores y productos; desactivación lógica reversible, eliminación en cascada con previsualización analítica y reversión mediante la pila de deshacer.
   - **Pantalla 7 (`pantalla_importar.py`)**: encolado de fuentes CSV, PDF y URLs SCIENTI con visualización de cola FIFO y procesamiento secuencial o por lote.
   - **Pantalla 8 (`pantalla_cruzada.py`)**: ejecutor de verificación cruzada Python vs C++ con comparador byte-a-byte de resúmenes JSON y visualización de discrepancias.
   - **Pantalla 9 (`pantalla_acerca.py`)**: créditos institucionales UPC, referencias a la convocatoria 2024 de MinCiencias (M601PR04G01), arquitectura del sistema y metadatos de revisión.

4. **Ventana Principal (`src/pea/gui/ventana_principal.py`) y Empaquetado (`src/pea/gui/`)**:
   - Diseño de cuatro zonas:
     - Barra superior: identidad UPC, estado de conexión en vivo, botón de Deshacer (Ctrl+Z).
     - Banner de advertencia de concurrencia: se activa cuando `meta.revision` difiere en el servidor, con botón de recarga inmediata.
     - Barra de navegación lateral: listado de acceso directo a las 9 pantallas.
     - Zona central apilada: `QStackedWidget` con actualización dinámica de vistas.
     - Barra de estado inferior: revisión del esquema, estado de red, tamaño de la pila de deshacer y cola de ingesta.
   - Temporizador periódico `QTimer` en segundo plano para detección de cambios remotos.
   - Subcomando `--autoprueba` (`ejecutar_autoprueba`): recorrido secuencial de las 9 pantallas en modo *offscreen*, renderizado y guardado de capturas en `datos/capturas/pantalla_01_conectar.png` a `pantalla_09_acerca.png`, finalizando con código 0.

5. **Pruebas y Verificación Integral**:
   - `tests/unit/test_gui_completa.py`: 10 pruebas unitarias con `pytest-qt` cubriendo estructura de zonas, navegación de pantallas, interacción de filtros, selecciones, CRUD, deshacer, cola de importación, exportación CSV/PNG y ficha institucional.
   - 85 pruebas unitarias de Python aprobadas al 100%.
   - Pruebas C++ con doctest compiladas y aprobadas (-Werror).
   - `ruff check src tests` verificado sin advertencias ni errores.
   - Validación completa de la bóveda Obsidian con `tools/brain/verificar_brain.py` (0 errores).

## Pruebas ejecutadas y resultados
- `.venv\Scripts\python.exe -m pea.gui --autoprueba` → OK (Código 0, 9 capturas PNG generadas en `datos/capturas/`).
- `pytest tests/unit/test_gui_completa.py` → OK (10 passed).
- `pytest tests/unit/test_cli_gui.py` → OK (5 passed).
- `pytest` general → OK (85 passed, 2 deselected).
- `ruff check src tests` → OK (All checks passed).
- `scripts/verificar.ps1` → OK (Python, C++ y Bóveda Obsidian en verde).

## Supuestos y decisiones de diseño
- **Ausencia de dependencias pesadas para gráficos**: Para evitar dependencias externas como matplotlib o motores web Chromium en el despliegue de escritorio, los gráficos se implementaron usando componentes nativos vectoriales con `QPainter` en `src/pea/gui/componentes/graficos.py`.
- **Deshacer integral en la multilista**: El borrado o desactivación preserva los punteros y adyacencias mediante `ComandoInverso` para que `deshacer` reestablezca con precisión los enlaces cruzados grupo-investigador-producto.
