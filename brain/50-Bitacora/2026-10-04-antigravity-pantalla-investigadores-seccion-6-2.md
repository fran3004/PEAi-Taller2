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
origen: "Prompt 14: Pantalla Investigadores segun seccion 6.2"
agente: "Antigravity"
rama: "feat/gui-rediseno-faf"
commit: "feat: pantalla investigadores y ficha lateral segun seccion 6.2"
---

# Bitácora · Pantalla Investigadores y ficha lateral según sección 6.2

## Objetivo
Implementar la pantalla de Investigadores (`src/pea/gui/pantallas/investigadores.py` y `PantallaInvestigadores`) de acuerdo con la sección 6.2 y los requisitos de responsividad y accesibilidad de [[GUI-Diseno-Python]] y el boceto de referencia `ref-investigadores.png`:
1. **Barra de contexto**:
   - Título de sección y subtítulo descriptivo.
   - Chip de ventana temporal global (`ChipVentana`) con popover de filtro de años.
   - Menú desplegable «Exportar ▾» (exportación a CSV del directorio visible o filtrado).
2. **Tarjeta de Directorio**:
   - Campo de búsqueda interactivo (`CampoBusqueda`) con atajo `Ctrl+F` y retardo debounced de 250 ms.
   - Filtros desplegables: Grupo (`QComboBox`), Categoría (`QComboBox` con todas las categorías Minciencias: Emérito, Senior, Asociado, Junior, Sin categoría) y Estado («Activos» / «Todos»).
   - Botón primario de acción destacada: «+ Nuevo investigador» con diálogo de creación.
3. **Tabla estilizada de investigadores**:
   - Filas de 48 px de altura, hover `#F3F7FB`, selección `#E3EEF7` con barra de acento institucional de 3 px `#35B6E8`.
   - Columnas: Nombre (avatar circular de 28 px + nombre en negrita), Grupo(s), Categoría (píldora con variante cromática respectiva), Formación académica, Productos (número entero formateado alineado a la derecha) y Código CvLAC (enlace clickeable que copia al portapapeles y notifica mediante toast).
   - Representación atenuada de registros inactivos al 60% de opacidad y píldora de aviso «Inactivo».
   - Ordenamiento interactivo por columnas respetando orden numérico en Productos y alfabético en nombres (`ProxyDirectorioInvestigadores`).
   - Pie de tabla con conteo en vivo: «Mostrando N de M investigadores».
4. **Ficha lateral de detalle (360 px)**:
   - Avatar circular de 96 px con iniciales e insignia de estado.
   - Título del investigador y subtítulo «GRUPO · Categoría».
   - Cuadrícula 2×2 de fichas KPI: Productos (en ventana temporal), Grupos (membresías activas), Coautores (red de colaboración) y Años con producción.
   - Minigráfico de serie anual histórica (`GraficoSerieAnual`).
   - Distribución proporcional por tipologías Minciencias (`BarrasTipologia`: GNC, DTI, ASC, FRH) con barras horizontales y etiquetas de porcentaje.
   - Botones de acción rápida: Editar, Activar / Desactivar (cambio de estado reversible con toast), Eliminar… (con advertencia en cascada detallada mediante diálogo modal `DialogoConfirmarEliminar`), «Ver ficha completa» (diálogo modal con 3 pestañas: Aporte a grupos, Membresías, Productos) y «Ver productos» (navegación fluida a la pantalla de Productos con filtro preestablecido).
5. **Notificaciones**:
   - Retroalimentación mediante avisos emergentes no intrusivos (`Toast` y `GestorAvisos`) para copia de códigos, altas, bajas y modificaciones.

## Qué se hizo
- Se extendió `src/pea/gui/componentes/tabla.py`:
  - Definición del rol personalizado `ROL_ACTIVO`.
  - Creación de `TextoDelegate` con soporte de opacidad al 60% para registros inactivos y alineación configurable.
  - Soporte de opacidad al 60% en `PildoraDelegate`, `AvatarNombreDelegate` y `EnlaceCopiaDelegate`.
  - Método `establecer_proxy()` en `TablaEstilizada` para enlazar modelos proxys personalizados y mantener sincronizado el pie «Mostrando N de M».
- Se adaptó `src/pea/gui/componentes/ficha_lateral.py` para permitir avatares de 96 px (`diametro_avatar`), botón `btn_ver_productos` y la señal `ver_productos_solicitado`.
- Se añadió el método `establecer_texto()` a `src/pea/gui/componentes/campo_busqueda.py`.
- Se expuso la propiedad `filtro` en `ChipVentana` (`src/pea/gui/componentes/filtro_anios.py`).
- Se optimizó `tabla_investigadores()` en `ServicioAplicacion` para computar opcionalmente el conteo de productos filtrado por `FiltroAnios`.
- Se creó el módulo `src/pea/gui/pantallas/investigadores.py` con las clases `ModeloDirectorioInvestigadores`, `ProxyDirectorioInvestigadores`, `BarrasTipologia`, `DialogoConfirmarEliminar`, `DialogoFichaCompletaInvestigador` y `PantallaInvestigadores`.
- Se exportó `PantallaInvestigadores` en `src/pea/gui/pantallas/__init__.py`.
- Se conectó `PantallaInvestigadores` en `src/pea/gui/ventana_principal.py` en el índice de la pila correspondiente a `Pantalla.INVESTIGADORES`, enlazando señales de navegación, cambio de ventana temporal y modificaciones del modelo.
- Se implementó la suite de pruebas unitarias `tests/unit/test_pantalla_investigadores.py` (8 pruebas completas).
- Se amplió la función `ejecutar_autoprueba()` en `ventana_principal.py` para capturar la pantalla de investigadores en 4 resoluciones (1366×768, 1920×1080, 1100×700 y 1360×820).
- Se ejecutó `python -m pea.gui --autoprueba`, validando la generación exitosa de las capturas offscreen en `datos/capturas/pantalla_investigadores_*.png`.

## Comandos y resultados
- `ruff check src tests`: 0 errores y 0 advertencias.
- `pytest tests/unit/test_pantalla_investigadores.py`: 8/8 pruebas aprobadas.
- `pytest tests/unit`: 137 pruebas unitarias aprobadas (0 fallas, 1 de red omitida por defecto).
- `python -m pea.gui --autoprueba`: 10 capturas offscreen generadas correctamente en `datos/capturas/` finalizando con código de salida 0.
- `python tools/brain/verificar_brain.py`: validación de la bóveda sin errores ni advertencias.

## Decisiones
- **Filtrado reactivo mediante QSortFilterProxyModel**: Se implementó `ProxyDirectorioInvestigadores` invalidando selectivamente el proxy con `self.invalidate()` en PySide6 6.11, garantizando respuesta instantánea al escribir en el buscador o alternar combos.
- **Atenuación visual de inactivos**: Los registros inactivos mantienen su información legible pero renderizan a 60% de opacidad tanto en texto, avatar como enlace de CvLAC, junto con la píldora informativa «Inactivo».
- **Modal de cascada informativo**: Al pulsar «Eliminar…», `DialogoConfirmarEliminar` utiliza `servicio.describir_cascada(TipoEntidad.INVESTIGADOR, id)` para advertir al usuario qué relaciones y productos se verán afectados antes de confirmar la operación destructiva.
- **Detalle completo en pestañas**: La vista de ficha completa organiza la información exhaustiva en tres pestañas limpias («Aporte a grupos», «Membresías» y «Productos») con botón de exportación CSV directo.

## Pendientes y siguiente paso
- Continuar con la implementación de la pantalla **Grupos** (`src/pea/gui/pantallas/grupos.py`) siguiendo la sección 6.3 de [[GUI-Diseno-Python]].
