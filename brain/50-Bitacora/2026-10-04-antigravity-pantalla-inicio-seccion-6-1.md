---
tipo: bitacora
estado: revisado
creado: 2026-10-04
actualizado: 2026-10-04
relacionado:
  - "[[00-Inicio]]"
  - "[[GUI-Diseno-Python]]"
  - "[[ADR-0012-Diseno-GUI-y-navegacion]]"
  - "[[ADR-0016-Alcance-de-pantallas-y-datos-del-boceto]]"
  - "[[ADR-0017-Tecnologia-de-interfaz-Qt-Widgets]]"
origen: "Prompt 13: Pantalla Inicio segun seccion 6.1"
agente: "Antigravity"
rama: "feat/gui-rediseno-faf"
commit: "feat: pantalla inicio institucional y por grupo segun seccion 6.1"
---

# Bitácora · Pantalla Inicio institucional y por grupo según sección 6.1

## Objetivo
Implementar la pantalla principal de Inicio (`src/pea/gui/pantallas/inicio.py` y `PantallaInicio`) conforme a las especificaciones de la sección 6.1 y la responsividad de la sección 11 de [[GUI-Diseno-Python]]:
1. **Barra de contexto**:
   - Selector segmentado «Institución | Grupo» (`SelectorSegmentado`).
   - Selector desplegable de grupos (`QComboBox`) visible y reactivo únicamente en modo Grupo.
   - Chip de ventana temporal global (`ChipVentana`) con popover de filtro de años integrado.
   - Menú desplegable «Exportar ▾» con opciones de exportación a CSV (resumen estructurado con delimitador institucional) y PNG (gráficos a 2× de resolución).
2. **Tarjeta de Ámbito**:
   - Avatar circular de 112 px con anillo (`Avatar`), portando el logo de la Universidad Popular del Cesar (`logo_upc.png`) en modo Institución o las iniciales con degradado determinista en modo Grupo.
   - Título y líneas informativas («Universidad Popular del Cesar» / «Grupo de Investigación – {nombre}»).
   - Botón desplegable «Ver más detalles ⌄» con panel conmutable (grupos e investigadores activos en institución; líder, institución, área OCDE, ubicación y fecha de creación en grupo).
   - Cuadrícula 2×3 de 6 fichas KPI (`FichaKPI`):
     - Modo Institución: Grupos activos, Investigadores activos, Productos (ventana) con minigráfico (`Minigrafico`) de tendencia anual, Promedio por investigador, Productos avalados, Productos históricos.
     - Modo Grupo: Integrantes, Estudiantes, Productos (ventana) con minigráfico de tendencia anual, Productos avalados, Promedio por integrante, Aporte a la institución (%).
3. **Producción por año y tipología**:
   - Barras apiladas interactivas (`GraficoBarrasApiladas`) con colores canónicos Minciencias (GNC, DTI, ASC, FRH), leyendas con atenuación y botón de alternancia a tabla accesible.
4. **Tipología de productos**:
   - Gráfico de dona concéntrica doble (`GraficoDonaDoble`), anillo externo por tipologías y anillo interno por estado de validación.
5. **Red de colaboración**:
   - Vista previa de red (`MiniRed`) con los 18 nodos principales de coautoría y botón «Abrir análisis completo →» conectado a la pantalla de redes.
6. **Segunda fila con rankings Top 5**:
   - Modo Institución: «Investigadores más productivos» y «Grupos más productivos».
   - Modo Grupo: «Integrantes con más productos» y «Últimos productos del grupo».
   - Cada fila (`FilaRanking`) presenta insignia de puesto, nombre, barra horizontal proporcional embebida y cantidad de productos.
7. **Estados y responsividad**:
   - Estado vacío accesible (`EstadoVacio`) con dos botones («Conectar con Supabase» y «Cargar datos de demostración»).
   - Esqueleto animado de carga (`Esqueleto`).
   - Disposición en 4 columnas (11 : 13 : 12 : 13) para anchos ≥ 1360 px y rejilla 2×2 para anchos inferiores.

## Qué se hizo
- Se creó el módulo `src/pea/gui/pantallas/inicio.py` implementando `FilaRanking` y `PantallaInicio`.
- Se creó `src/pea/gui/pantallas/__init__.py` exportando `PantallaInicio`.
- Se integró `PantallaInicio` en `src/pea/gui/ventana_principal.py` reemplazando el marcador provisional y conectando las señales de navegación y sincronización del filtro global.
- Se ajustó `src/pea/gui/componentes/selector_segmentado.py` para emitir la señal `opcion_cambiada` al invocar programáticamente `seleccionar()`.
- Se protegió `src/pea/gui/componentes/toast.py` asegurando la inicialización segura del atributo `_ventana` en `GestorAvisos`.
- Se diseñó la suite de pruebas unitarias en `tests/unit/test_pantalla_inicio.py` (8 pruebas aprobadas).
- Se ejecutó `python -m pea.gui --autoprueba`, generando capturas offscreen en `datos/capturas/`:
  - `pantalla_inicio_1366x768.png` (modo 2×2 responsivo)
  - `pantalla_inicio_1920x1080.png` (modo 4 columnas institucional)
  - `pantalla_inicio_1100x700.png` (modo compacto con barras de desplazamiento)
  - `pantalla_inicio_grupo_1920x1080.png` (modo 4 columnas por grupo)
  Se compararon visualmente contra `ref-inicio.png` y `ref-inicio-acabado.jpg`, verificando fidelidad tipográfica, jerarquía y espaciados institucionales.

## Comandos y resultados
- `ruff check src tests`: 0 errores y advertencias.
- `pytest tests/unit`: 129 pruebas aprobadas (0 fallas, 1 deseccionada de red).
- `python -m pea.gui --autoprueba`: generación correcta de todas las capturas offscreen.
- `python tools/brain/verificar_brain.py`: validación de la bóveda sin errores ni advertencias.

## Decisiones
- **Barra de contexto integrada**: Se ubicaron en una barra de 56 px el selector de ámbito (Institución / Grupo) y el combo de selección de grupo a la izquierda, y a la derecha el chip de ventana global con el menú Exportar.
- **Detalles colapsables en tarjeta de Ámbito**: Se utilizó un panel desplegable activado por el botón «Ver más detalles ⌄» para no recargar visualmente la tarjeta pero ofrecer acceso completo a los metadatos secundarios.
- **Rejilla responsiva con scroll nativo**: Todo el contenido se aloja dentro de un `QScrollArea` con fondo transparente y ajuste automático de rejilla en `resizeEvent` (4 columnas a ≥ 1360 px, 2×2 por debajo).

## Pendientes y siguiente paso
- Continuar con la implementación de la pantalla **Investigadores** (`src/pea/gui/pantallas/investigadores.py`) integrando `TablaEstilizada`, `FichaLateral` y los diálogos modales.
