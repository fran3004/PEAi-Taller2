---
tipo: bitacora
estado: revisado
creado: 2026-10-19
actualizado: 2026-10-19
relacionado:
  - "[[00-Inicio]]"
  - "[[GUI-Diseno-Python]]"
  - "[[ADR-0015-Analisis-de-red-nativo]]"
  - "[[ADR-0017-Tecnologia-de-interfaz-Qt-Widgets]]"
origen: "Solicitud del usuario de mejora visual integral de gráficos, análisis de redes, filtro de años y exportación PDF/PNG/CSV"
agente: "Antigravity"
rama: "master"
commit: "pendiente"
---

# Bitácora · Mejora visual de gráficos, análisis de redes, filtro de años y exportación institucional

## Objetivo
Mejorar visualmente e interactivamente todas las vistas de gráficos (`GraficoDonaDoble`, `GraficoBarrasApiladas`, `GraficoSerieAnual`, `MiniRed`), rediseñar la disposición y el contraste del grafo de `Análisis de redes` (`VistaRed`, `NodoGrafoItem`, `AristaGrafoItem`, `calcular_disposicion_fuerzas`), corregir el solapamiento en el selector de ventana de años (`PopoverFiltroAnios`) y elevar la calidad ejecutiva de todos los archivos exportados (`PDF`, `PNG` y `CSV`) en toda la aplicación Python siguiendo estrictamente las reglas del proyecto.

## Qué se hizo
- **Tokens y contraste global (`src/pea/gui/estilo.py`)**:
  - Se añadieron tokens cromáticos de alta legibilidad para la red de coautoría (`COLOR_RED_ARISTAS`, `COLOR_RED_ARISTA_ACTIVA`, `COLOR_NODO_SIN_CATEGORIA`, `COLOR_NODO_AISLADO`, `PALETA_NODOS_RED`) y reglas QSS globales para `QSpinBox` sin recorte de dígitos.
- **Selector de ventana de años (`src/pea/gui/componentes/filtro_anios.py`)**:
  - Se rediseñó `PopoverFiltroAnios` con ancho de `404 px`, píldoras de atajo rápido (`3 años`, `5 años`, `10 años`, `Modelo 2024`, `Histórico`), indicadores circulares explícitos para `QRadioButton`, campos `QSpinBox` con ancho suficiente (`92 px` y `104 px`) y margen derecho para que los valores (`5`, `2015`, `2024`) nunca colisionen con las flechas de incremento/decremento, más botón de confirmación `Listo`.
- **Análisis de redes de colaboración (`src/pea/gui/red/` y `src/pea/gui/pantallas/redes.py`)**:
  - En `calcular_disposicion_fuerzas()` (`disposicion.py`), se separaron los nodos conectados (`grado > 0`) de los aislados (`grado == 0`): el subgrafo conectado se distribuye con Fruchterman-Reingold y pase de anticolisión ocupando el área central, mientras que los nodos aislados se ubican ordenadamente en un anillo elíptico perimetral sin comprimir el subgrafo conectado.
  - En `NodoGrafoItem` (`nodo.py`), se incorporaron gradientes radiales, iniciales centradas, insignia numérica de grado en nodos conectados, colores vivos para nodos activos sin categoría y etiquetas en cápsulas translúcidas con borde.
  - En `AristaGrafoItem` (`arista.py`), se mejoró el contraste de las líneas y se añadió insignia central con el número de productos compartidos.
  - En `VistaRed` (`vista_red.py`) y `PantallaRedes` (`redes.py`), se agregó halo central en el lienzo, resaltado persistente de subred ego al seleccionar un nodo, corrección de `FilaTopConectado` y menú de exportación a `PDF`, `PNG` y `CSV`.
- **Gráficos estadísticos y tarjetas (`src/pea/gui/componentes/graficos/`, `tarjeta_kpi.py`, `selector_segmentado.py`)**:
  - En `GraficoDonaDoble`, se amplió el radio interior (`0.60`), se ajustó el escalado dinámico del texto central (`278 productos` sin recortes) y se equilibró la proporción de columnas de leyenda (`44 % / 56 %`).
  - En `MiniRed`, se implementó disposición concéntrica en dos anillos con cápsulas legibles para los 6 investigadores principales.
  - En `GraficoBarrasApiladas` y `GraficoSerieAnual`, se añadieron bandas de resaltado en hover y leyendas adaptativas.
  - En `FichaKPI` y `SelectorSegmentado`, se ajustaron márgenes y anchos mínimos para evitar cualquier truncamiento en `Institución` o en los títulos de métricas.
- **Exportación ejecutiva (`src/pea/gui/exportador_visual.py` y pantallas)**:
  - Se creó `exportador_visual.py` usando exclusivamente `QPdfWriter`, `QPainter`, `QImage` y `csv` (`utf-8-sig`) conforme a [[ADR-0017-Tecnologia-de-interfaz-Qt-Widgets]], conectándolo a `PantallaInicio`, `PantallaInvestigadores`, `PantallaGrupos`, `PantallaProductos` y `PantallaRedes`.

## Comandos y resultados
- `.\.venv\Scripts\python.exe -m ruff check src tests` → `All checks passed!`
- `.\.venv\Scripts\python.exe -m pea.gui --autoprueba` → `0` barras horizontales en las 8 pantallas y 3 resoluciones (`1100x700`, `1366x768`, `1920x1080`).
- `.\.venv\Scripts\python.exe -m pytest tests/unit -q` → `238 passed`.

## Decisiones
- Los reportes ejecutivos `PDF` y las láminas institucionales `PNG` se generan íntegramente con primitivas de `PySide6.QtGui` (`QPdfWriter`, `QPainter`, `QImage`) respetando la prohibición de `matplotlib`, `QtCharts` y `QtWebEngine` establecida en [[ADR-0017-Tecnologia-de-interfaz-Qt-Widgets]].

## Pendientes y siguiente paso
- Ejecutar `tools/brain/verificar_brain.py` y realizar el commit correspondiente.
