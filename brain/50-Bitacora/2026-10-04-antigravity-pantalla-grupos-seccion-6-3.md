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
origen: "Prompt 15: Pantalla Grupos segun seccion 6.3"
agente: "Antigravity"
rama: "feat/gui-rediseno-faf"
commit: "feat: pantalla grupos y ficha de grupo segun seccion 6.3"
---

# Bitácora · Pantalla Grupos y Ficha de Grupo según sección 6.3

## Objetivo
Implementar la pantalla de Grupos (`src/pea/gui/pantallas/grupos.py`, `PantallaGrupos` y `FichaGrupo`) conforme a las especificaciones de la sección 6.3 de [[GUI-Diseno-Python]] y el patrón de directorios institucionales:
1. **Barra de contexto**:
   - Título («Grupos de Investigación») y subtítulo institucional.
   - Chip de ventana temporal global (`ChipVentana`) con popover interactivo de filtro de años.
   - Menú desplegable «Exportar ▾» con exportación a CSV del directorio visible o filtrado.
2. **Tarjeta de Directorio de Grupos**:
   - Campo de búsqueda interactivo (`CampoBusqueda`) con atajo `Ctrl+F` y retardo debounced de 250 ms (búsqueda por nombre, código GrupLAC o líder).
   - Filtros desplegables: Categoría (`QComboBox` con todas las categorías Minciencias: A1, A, B, C, Reconocido, Sin clasificar) y Estado («Activos» / «Todos»).
   - Botón primario de acción destacada: «+ Nuevo grupo» que abre `DialogoGrupo` para creación inmediata.
3. **Tabla estilizada de grupos**:
   - Filas de 48 px de altura, hover `#F3F7FB`, selección `#E3EEF7` con barra de acento institucional de 3 px `#35B6E8`.
   - Columnas: Nombre (avatar circular de 28 px + nombre en negrita), Código GrupLAC (enlace clickeable que copia al portapapeles y notifica mediante toast), Categoría (píldora con variante cromática respectiva), Líder, Integrantes (número entero alineado a la derecha), Productos (número entero alineado a la derecha en la ventana activa) y Estado (píldora «Activo» / «Inactivo»).
   - Representación atenuada de registros inactivos al 60% de opacidad.
   - Ordenamiento interactivo por columnas respetando orden numérico en Integrantes y Productos (`ProxyDirectorioGrupos`).
   - Pie de tabla con conteo en vivo: «Mostrando N de M grupos».
4. **Ficha lateral del grupo (`FichaGrupo`, 360 px)**:
   - Reutilización de la tarjeta de Ámbito de Inicio en modo Grupo.
   - Avatar de 96 px con iniciales del grupo y degradado determinista.
   - Título del grupo y subtítulo «Código · Categoría».
   - Botón desplegable «Ver más detalles ⌄» con panel conmutable (Líder, Institución principal, Área OCDE, Ubicación y Fecha de creación).
   - Cuadrícula 2×3 de 6 fichas KPI (`FichaKPI`): Integrantes, Estudiantes, Productos (ventana con minigráfico de tendencia), Productos avalados, Promedio por integrante y Aporte a la institución (%).
   - Minigráfico de barras apiladas (`GraficoBarrasApiladas`), calculando la evolución anual por tipología (GNC, DTI, ASC, FRH) del grupo mediante `serie_anual_por_categoria(filtro, codigo_grupo=cod)`.
   - Botones de acción rápida: Editar (formulario `DialogoGrupo`), Activar / Desactivar (cambio de estado reversible con toast), Eliminar… (con advertencia en cascada detallada mediante `DialogoConfirmarEliminar`), «Ver ficha completa» (diálogo modal con 2 pestañas: Integrantes y coautores, y Productos enlazados, con exportación CSV) y «Ver productos» (navegación a la pantalla de Productos).
5. **Notificaciones**:
   - Retroalimentación mediante avisos emergentes no intrusivos (`GestorAvisos`) para copia de códigos, altas, bajas y modificaciones.

## Qué se hizo
- Se extendió `tabla_grupos(texto="", filtro=None)` en `src/pea/servicios/servicio_aplicacion.py` para permitir el cálculo opcional de productos en la ventana temporal activa del catálogo.
- Se implementó `src/pea/gui/pantallas/grupos.py` conteniendo:
  - `ModeloDirectorioGrupos`: modelo tabular adaptado con roles de visualización, alineación numérica y `ROL_ACTIVO`.
  - `ProxyDirectorioGrupos`: proxy reactivo con ordenamiento numérico en columnas 4 y 5 y filtros cruzados (texto, categoría y estado).
  - `DialogoConfirmarEliminar`: confirmación modal de eliminación con inspección de cascada (`describir_cascada`).
  - `DialogoFichaCompletaGrupo`: diálogo modal con pestañas de integrantes/coautores y productos enlazados con exportación a CSV.
  - `FichaGrupo`: ficha lateral de 360 px que emula la tarjeta de Ámbito de Grupo con panel desplegable de detalles, 6 KPIs, minigráfico de barras apiladas de tipologías y fila de acciones.
  - `PantallaGrupos`: contenedor general del directorio, splitter responsivo, barra de contexto y atajos de teclado (`Ctrl+F` y `Enter`).
- Se exportaron `PantallaGrupos` y `FichaGrupo` en `src/pea/gui/pantallas/__init__.py`.
- Se integró `PantallaGrupos` en `src/pea/gui/ventana_principal.py` reemplazando el marcador provisional en `_pantalla_grupos_modulo` (índice 2: `Pantalla.GRUPOS`), conectando las señales de navegación, sincronización de filtros temporales y modificaciones de datos.
- Se amplió la función `ejecutar_autoprueba()` en `ventana_principal.py` para capturar la pantalla de Grupos en los 4 tamaños oficiales (1366×768, 1920×1080, 1100×700 y 1360×820).
- Se diseñó la suite de pruebas unitarias en `tests/unit/test_pantalla_grupos.py` (8 pruebas completas cubriendo construcción, datos, filtros, selección, KPIs, navegación, inactivos, diálogos y filtro de años).
- Se ejecutó `python -m pea.gui --autoprueba`, validando la generación correcta de las 4 capturas de pantalla de grupos en `datos/capturas/pantalla_grupos_*.png`.

## Comandos y resultados
- `ruff check src tests`: 0 errores y advertencias.
- `pytest tests/unit/test_pantalla_grupos.py`: 8/8 pruebas aprobadas.
- `pytest tests/unit`: 145 pruebas aprobadas (0 fallas, 1 deseccionada de red).
- `python -m pea.gui --autoprueba`: generación correcta de todas las capturas offscreen en `datos/capturas/`.
- `python tools/brain/verificar_brain.py`: validación de la bóveda sin errores ni advertencias.

## Decisiones
- **FichaGrupo basada en FichaLateral**: Se heredó de `FichaLateral` para garantizar consistencia visual y de ancho (360 px), embebiendo los 6 KPIs en cuadrícula 2×3 y el minigráfico de barras apiladas alimentado por `serie_anual_por_categoria(codigo_grupo=cod)`.
- **Detalles colapsables en ficha lateral**: Siguiendo el comportamiento de Inicio en modo Grupo, se incorporó el botón «Ver más detalles ⌄» para expandir u ocultar los metadatos secundarios (Líder, Institución, Área OCDE, Ciudad, Creación).
- **Filtrado reactivo con QSortFilterProxyModel**: Se aplicó invalidación limpia con `self.invalidate()` en el proxy para respuesta inmediata en búsqueda de texto, categoría y alternancia de estado (Activos / Todos).
- **Ficha completa con 2 pestañas**: El diálogo amplio de grupo organiza de manera clara las dos relaciones principales de la entidad: *Integrantes y coautores vinculados* y *Productos enlazados al grupo*, con botón para exportar ambas tablas a archivos CSV independientes.

## Pendientes y siguiente paso
- Continuar con la implementación de la pantalla **Productos** (`src/pea/gui/pantallas/productos.py`) conforme a la sección 6.4 de [[GUI-Diseno-Python]].
