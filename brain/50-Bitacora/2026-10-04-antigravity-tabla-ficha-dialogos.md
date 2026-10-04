---
tipo: bitacora
estado: revisado
creado: 2026-10-04
actualizado: 2026-10-04
relacionado:
  - "[[00-Inicio]]"
  - "[[GUI-Diseno-Python]]"
  - "[[ADR-0012-Diseno-GUI-y-navegacion]]"
  - "[[ADR-0013-Vistas-secundarias]]"
  - "[[ADR-0017-Tecnologia-de-interfaz-Qt-Widgets]]"
origen: "Prompt 11: Tabla estilizada, ficha lateral, dialogos y popover de historial"
agente: "Antigravity"
rama: "feat/gui-rediseno-faf"
commit: "feat: tabla estilizada ficha lateral dialogos y popover historial"
---

# Bitácora · Tabla estilizada, ficha lateral, diálogos y popover de historial

## Objetivo
Implementar los componentes estructurales de navegación y gestión de directorios según las secciones 6.2 y 8 de [[GUI-Diseno-Python]]:
1. `TablaEstilizada` (`src/pea/gui/componentes/tabla.py`): filas de 48 px, hover `#F3F7FB`, selección `#E3EEF7` con barra de acento `#35B6E8` de 3 px en la primera columna, encabezado horizontal en color `FICHA` (`#E9EEF6`), ordenamiento insensible a mayúsculas mediante `QSortFilterProxyModel`, pie informativo «Mostrando N de M», y delegados especializados:
   - `PildoraDelegate`: renderiza badges redondeadas con colores según tipología, validación, categoría o estado.
   - `AvatarNombreDelegate`: avatar circular de 28 px con iniciales y degradado determinista junto al nombre completo en negrita.
   - `EnlaceDelegate`: enlace en azul `#1F6F94` con subrayado al hover y copia automática al portapapeles al hacer clic con emisión de señal `copiado`.
   - `NumeroDelegate`: cifras enteras o decimales alineadas a la derecha con separadores de miles según localización colombiana (`es_CO`).
2. `FichaLateral` (`src/pea/gui/componentes/ficha_lateral.py`): ancho fijo institucional de 360 px, encabezado con avatar de 72 px, título, subtítulo y píldoras de estado, cuadrícula 2×2 para fichas KPI, zona de contenido dinámico desplazable (para gráficos y detalles), y barra inferior de acciones fijas («Editar», «Desactivar/Activar», «Eliminar…», «Ver ficha completa») con estado vacío inicial.
3. `Dialogos` (`src/pea/gui/dialogos.py`): extracción y rediseño completo de los diálogos de gestión (`DialogoGrupo`, `DialogoInvestigador`, `DialogoProducto`) desde `pantalla_gestion.py` hacia un módulo dedicado, incorporando validación reactiva con mensajes de error en rojo `#A12626` debajo de cada campo obligatorio y añadiendo `DialogoEditarProducto` para modificaciones atómicas vía `ServicioAplicacion.actualizar_producto`. Se conserva intacto el funcionamiento de `pantalla_gestion.py`.
4. `PopoverHistorial` (`src/pea/gui/componentes/popover_historial.py`): menú flotante con sombra (`QGraphicsDropShadowEffect`), contador de operaciones, listado de eventos en orden cronológico inverso con viñeta destacada para la operación más reciente, y botón inferior «Deshacer última (Ctrl+Z)» con soporte para la pila de deshacer ([[ADR-0012-Diseno-GUI-y-navegacion]]).

## Qué se hizo
- Se crearon los módulos `src/pea/gui/componentes/tabla.py`, `src/pea/gui/componentes/ficha_lateral.py`, `src/pea/gui/dialogos.py` y `src/pea/gui/componentes/popover_historial.py`.
- Se adaptó `src/pea/gui/pantallas/pantalla_gestion.py` para importar los diálogos rediseñados manteniendo retrocompatibilidad total sin borrar la pantalla previa.
- Se actualizaron las exportaciones públicas en `src/pea/gui/componentes/__init__.py`.
- Se afinó `resolver_estilo_pildora` en `pildora.py` para admitir variantes con prefijo («Investigador Senior», «Investigador Asociado», etc.) y se aseguró el fondo blanco en `PildoraDelegate`.
- Se implementó la suite completa de pruebas unitarias en `tests/unit/test_tabla_ficha_dialogos.py` evaluando ordenamiento por proxy, emisión de señales de selección de fila y clave, delegados, ficha lateral con KPIs, validación de errores en diálogos y señalización del popover.
- Se creó la herramienta `tools/captura_directorio_tabla_ficha.py` generando capturas offscreen en `datos/capturas/` (`directorio_investigadores.png` y `dialogos_popover.png`) comparadas y validadas visualmente frente al boceto de referencia `brain/_adjuntos/ref-investigadores.png`.

## Comandos y resultados
- `pytest tests/unit`: 122 pruebas pasadas en 10,93 s (0 fallas, 1 deseccionada de red).
- `ruff check src tests`: 0 errores y advertencias en el código fuente.
- `python tools/brain/verificar_brain.py`: 80 notas inspeccionadas, 0 errores, 0 advertencias.
- `python tools/captura_directorio_tabla_ficha.py`: capturas visuales generadas exitosamente.

## Decisiones
- **Barra de acento en columna 0**: Se pinta una barra vertical de 3 px con `#35B6E8` en el borde izquierdo de la celda seleccionada si corresponde a la columna 0, replicando fielmente la indicación de `GUI-Diseno-Python.md` y `ref-investigadores.png`.
- **Copia no disruptiva en EnlaceDelegate**: Se intercepta el evento de ratón en `editorEvent` copiando el texto al portapapeles y emitiendo `copiado` sin interferir con la selección de la fila en el modelo.
- **Mensajes de error inline en diálogos**: Se ubicaron etiquetas de error con estilo `ERROR` (`#A12626`) directamente bajo cada campo de entrada, alternando su visibilidad sin borrar el texto que el usuario ya ingresó.
- **Preservación temporal de pantalla_gestion.py**: Se mantuvo la pantalla anterior intacta según las instrucciones del prompt 11, desacoplando los diálogos reutilizables para las futuras pantallas de directorios.

## Pendientes y siguiente paso
- Continuar con el ensamblaje de las pantallas principales de directorios (Investigadores, Grupos, Productos) utilizando `TablaEstilizada`, `FichaLateral` y los diálogos modales.
