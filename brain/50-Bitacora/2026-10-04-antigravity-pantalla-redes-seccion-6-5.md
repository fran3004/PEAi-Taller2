---
tipo: bitacora
estado: revisado
creado: 2026-10-04
actualizado: 2026-10-04
relacionado:
  - "[[00-Inicio]]"
  - "[[GUI-Diseno-Python]]"
  - "[[ADR-0012-Diseno-GUI-y-navegacion]]"
  - "[[ADR-0015-Analisis-de-red-nativo]]"
  - "[[ADR-0016-Alcance-de-pantallas-y-datos-del-boceto]]"
  - "[[ADR-0017-Tecnologia-de-interfaz-Qt-Widgets]]"
origen: "Prompt 17: Pantalla Analisis de Redes de Colaboracion segun seccion 6.5 y ADR-0015"
agente: "Antigravity"
rama: "feat/gui-rediseno-faf"
commit: "feat: pantalla analisis de redes de colaboracion segun seccion 6.5 y adr-0015"
---

# Bitácora · Pantalla Análisis de Redes de Colaboración según sección 6.5 y ADR-0015

## Objetivo
Implementar el módulo completo de visualización e interacción de grafos de coautoría académica (`src/pea/gui/red/` y `src/pea/gui/pantallas/redes.py`, `PantallaRedes`) conforme a las especificaciones de la sección 6.5 de [[GUI-Diseno-Python]] y las decisiones de [[ADR-0015-Analisis-de-red-nativo]]:
1. **Paquete `src/pea/gui/red/`**:
   - `disposicion.py`: Algoritmo determinista de fuerzas basado en el modelo físico de Fruchterman-Reingold / Hooke + Coulomb, con semilla fija (`semilla=42`), repulsión cuadrática, atracción lineal ponderada por coautorías compartidas, amortiguamiento por enfriamiento simulado (simulated annealing) y gravedad centrípeta.
   - `nodo.py`: `NodoGrafoItem(QGraphicsItem)` con radio proporcional $r = 8 + 2.5 \sqrt{\text{grado}}$, colores institucionales por categoría Minciencias (Emérito, Senior, Asociado, Junior, Sin categoría), anillo de selección de 3 px `#35B6E8`, abreviación de etiqueta «J. Apellido», visibilidad condicional de rótulos (zoom $\ge 0.8$, top 10 o hover), resaltado de vecinos directos con atenuación al 25% del resto del grafo, arrastre con fijado de posición (pinning) y doble clic para abrir la ficha en Investigadores.
   - `arista.py`: `AristaGrafoItem(QGraphicsItem)` con grosor proporcional $\min(4.0, 1.0 + \log_2(\text{peso}))$, color base `#9DB5C9`, resaltado a `#35B6E8` y atenuación interactiva.
   - `vista_red.py`: `VistaRed(QGraphicsView)` con cuadrícula tenue de puntos (`#E2E8F0` cada 36 px), zoom suave con rueda del ratón hacia el cursor, desplazamiento mediante arrastre (`ScrollHandDrag`), leyenda flotante institucional en la esquina inferior izquierda (`LeyendaRed`), y tope de rendimiento a 400 nodos de mayor conectividad.
2. **Pantalla de Redes (`PantallaRedes`, sección 6.5)**:
   - **Barra de contexto (56 px)**: Título («Análisis de Redes de Colaboración»), subtítulo («Grafo de coautorías académicas y métricas de centralidad topológica»), `ChipVentana` interactivo con sincronización global y botón «Exportar red (PNG)» a doble resolución (2x).
   - **Fila de controles interactivos**: Combo Grupo («Todos los grupos» + lista alfabética), combo selector de umbral de coautorías («Mín. 1» a «Mín. 5 coautorías»), campo de búsqueda interactivo (`CampoBusqueda`) con atajo `Ctrl+F` para localizar y centrar nodos, botón «Reordenar» para reiniciar la física determinista, y botones de zoom («+», «−», «Ajustar»).
   - **Banner de aviso para tope de 400 nodos**: Franja de advertencia en color aviso que informa cuando la red original supera los 400 investigadores y se visualizan los 400 más conectados.
   - **Panel lateral de Métricas de Centralidad (340 px)**:
     - **Estado inicial (sin selección)**: Texto explicativo orientativo, lista de «Investigadores más conectados» (Top 5 con insignias numeradas, categoría y grado clicable para seleccionar el nodo), y tarjeta fija inferior de «Resumen de la red» con conteo de investigadores, vínculos y densidad.
     - **Estado seleccionado**: Avatar de 48 px con iniciales, nombre completo, subtítulo con código CvLAC y categoría, Fichas KPI para Grado de conexión (vínculos directos) y Centralidad de Intermediación de Brandes (betweenness centrality), cuadro de metadatos (Grupo principal, Categoría y Rol en la red), botón primario «Ver ficha de investigador →» y botón secundario «Deseleccionar».
3. **Integración global y navegación**:
   - Conexión de `MiniRed` en `PantallaInicio`: al pulsar «Abrir análisis completo →» o pulsar cualquier nodo de la vista previa, se navega automáticamente a `Pantalla.REDES` y se enfoca/selecciona el investigador correspondiente.
   - Integración de `PantallaRedes` en `VentanaPrincipal` (índice 4: `Pantalla.REDES`), conectando navegación, filtros globales y apertura de fichas en Investigadores.
   - Inclusión de capturas oficiales de `Pantalla.REDES` en las 4 resoluciones reglamentarias dentro de `ejecutar_autoprueba()`.

## Qué se hizo
- Se crearon los módulos gráficos en `src/pea/gui/red/`:
  - `disposicion.py`: Función `calcular_disposicion_fuerzas` con soporte flexible para claves de nodo (`codigo`/`id`) y aristas (`origen`/`source`, `destino`/`target`, `peso`/`productos_compartidos`), garantizando convergencia y determinismo estricto.
  - `arista.py`: Implementación de `AristaGrafoItem` con actualización reactiva ante movimiento de nodos y soporte de kwargs.
  - `nodo.py`: Implementación de `NodoGrafoItem` con renderizado vectorial por `QPainter`, cálculo de etiquetas de texto, radios, colores de categoría, tooltips detallados y eventos de interacción.
  - `vista_red.py`: `VistaRed` con escena de 4000×4000 px, fondo matricial de puntos, coordenadas de leyenda fijas en pantalla y emisión de señales (`nodo_seleccionado`, `nodo_deseleccionado`, `abrir_investigador_solicitado`, `limite_nodos_alcanzado`).
  - `__init__.py`: Exportación de la API pública del paquete `red`.
- Se implementó `src/pea/gui/pantallas/redes.py` con `PantallaRedes`, `FilaTopConectado`, divisor horizontal `QSplitter`, exportación a PNG a doble resolución (2x) mediante `render()` de la escena, sincronización con `ServicioAplicacion.red_coautoria` y soporte para ejecución sincrónica o en segundo plano con `EjecutorHilos`.
- Se exportó `PantallaRedes` en `src/pea/gui/pantallas/__init__.py`.
- En `src/pea/gui/pantallas/inicio.py`, se conectó `self._mini_red.nodo_pulsado` para emitir la nueva señal `ver_red_nodo_solicitado`.
- En `src/pea/gui/ventana_principal.py`:
  - Se sustituyó `MarcadorPantalla` por `PantallaRedes` en `_inicializar_pantallas`.
  - Se conectaron las señales `solicitar_navegacion`, `filtro_cambiado`, `abrir_investigador_solicitado` y `ver_red_nodo_solicitado`.
  - Se añadió el manejador `_al_solicitar_ver_nodo_red(codigo_investigador)` que transiciona a `Pantalla.REDES` y selecciona al investigador.
  - Se amplió `ejecutar_autoprueba()` para generar capturas de la pantalla de redes en las 4 resoluciones oficiales.
- Se implementaron 8 pruebas unitarias en `tests/unit/test_pantalla_redes.py`:
  1. `test_disposicion_fuerzas_determinista`: Validación de repetibilidad matemática exacta (100% determinismo).
  2. `test_calculo_geometria_nodos_y_aristas`: Validación de fórmulas de radio $r=8+2.5\sqrt{\text{grado}}$ y grosor $1+\log_2(\text{peso})$.
  3. `test_pantalla_redes_construccion_y_componentes`: Comprobación de widgets, dimensiones y controles.
  4. `test_pantalla_redes_carga_y_metricas_estado_inicial`: Carga de datos de demostración, visualización del resumen de red y Top 5.
  5. `test_pantalla_redes_seleccion_nodo_actualiza_panel`: Actualización de estado en el panel de métricas y botón deseleccionar.
  6. `test_pantalla_redes_navegacion_investigador_solicitada`: Emisión de señal al pulsar «Ver ficha de investigador →».
  7. `test_pantalla_redes_filtros_reactivos`: Filtrado dinámico por grupo, umbral de coautorías y búsqueda.
  8. `test_pantalla_redes_banner_limite_400`: Verificación del límite y activación del banner de advertencia con > 400 nodos.

## Verificación
- `ruff check src tests`: 0 errores, código completamente limpio.
- `pytest tests/unit/test_pantalla_redes.py`: 8 pasadas de 8.
- `pytest tests/unit`: 161 pruebas pasadas (1 deselected por marcador `red`).
- `python -m pea.gui --autoprueba`: Ejecutó con éxito, generando `datos/capturas/pantalla_redes_*.png` en resoluciones 1366×768, 1920×1080, 1100×700 y 1360×820.
- `tools/brain/verificar_brain.py`: Bóveda íntegra con 87 notas inspeccionadas, 0 errores, 0 advertencias.
