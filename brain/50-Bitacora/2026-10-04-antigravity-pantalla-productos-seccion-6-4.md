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
origen: "Prompt 16: Pantalla Productos segun seccion 6.4"
agente: "Antigravity"
rama: "feat/gui-rediseno-faf"
commit: "feat: pantalla productos y catalogo segun seccion 6.4"
---

# Bitácora · Pantalla Productos y Catálogo según sección 6.4

## Objetivo
Implementar la pantalla de Productos (`src/pea/gui/pantallas/productos.py`, `PantallaProductos` y `FichaProducto`) conforme a las especificaciones de la sección 6.4 de [[GUI-Diseno-Python]] y el patrón de catálogo institucional:
1. **Barra de contexto**:
   - Título («Catálogo de Productos») y subtítulo institucional («Producción científica clasificada en las 4 tipologías del Modelo Minciencias»).
   - Chip de ventana temporal global (`ChipVentana`) con popover interactivo de filtro de años.
   - Menú desplegable «Exportar ▾» con exportación a CSV del catálogo visible o filtrado.
2. **Tarjeta de Catálogo de Productos**:
   - Campo de búsqueda interactivo (`CampoBusqueda`) con atajo `Ctrl+F` y retardo debounced de 250 ms (búsqueda por título, código o autores).
   - Combos desplegables: Tipología (GNC, DTI, ASC, FRH), Validación (Avalado, Con soporte, No avalado) y Estado («Activos» / «Todos»).
   - Botón primario de acción destacada: «+ Nuevo producto» que abre `DialogoProducto` para creación inmediata.
3. **Tabla estilizada de productos**:
   - Filas de 48 px de altura, hover `#F3F7FB`, selección `#E3EEF7` con barra de acento institucional de 3 px `#35B6E8`.
   - Columnas: Código (enlace clickeable que copia al portapapeles y notifica mediante toast), Título (hasta 2 líneas con elipsis), Tipología (píldora con color de dato), Subtipo, Año (número centrado), Validación (píldora), Grupo, Autores (formato «Primer Autor (+N)») y Estado (píldora «Activo» / «Inactivo»).
   - Representación atenuada de registros inactivos al 60% de opacidad.
   - Ordenamiento interactivo por columnas respetando orden numérico en Año (`ProxyCatalogoProductos`).
   - Pie de tabla con conteo en vivo: «Mostrando N de M productos».
4. **Ficha lateral del producto (`FichaProducto`, 360 px)**:
   - Título del producto y subtítulo «Código: ...».
   - Píldoras cromáticas de tipología y validación en la cabecera.
   - Cuadro de metadatos (Año de publicación, Subtipo y Grupo de investigación).
   - Distintivo e insignia de la ventana del Modelo 2024 («✔ Dentro de la ventana del Modelo 2024» / «✖ Fuera de la ventana…») con tooltip explicativo de la ventana según el tipo de producto (5 años para artículos, software, ASC y FRH; 10 años para libros y patentes).
   - Lista interactiva de autores y coautores: avatar de 28 px con iniciales + nombre; al hacer clic navega automáticamente a la pantalla de Investigadores seleccionando la ficha del autor.
   - Botones de acción rápida: Editar (`DialogoEditarProducto`), Activar / Desactivar (cambio de estado reversible con toast) y Eliminar… (con advertencia en cascada detallada mediante `DialogoConfirmarEliminar`).
5. **Navegación e interoperabilidad**:
   - Conexión cruzada desde botones «Ver productos» en las pantallas de Investigadores y Grupos para filtrar automáticamente por el autor o grupo seleccionado.
   - Navegación bidireccional desde los coautores del producto hacia el directorio de Investigadores.

## Qué se hizo
- Se enriqueció `detalle_producto(codigo)` en `src/pea/servicios/servicio_aplicacion.py` para devolver campos estructurados (`codigo_identificador`, `anio`, `estado_validacion`, `codigo_grupo` y `autores_lista` con diccionarios `{nombre, codigo_rh}`).
- Se implementó `src/pea/gui/pantallas/productos.py` conteniendo:
  - `ModeloCatalogoProductos`: modelo tabular adaptado con roles de visualización, formateo abreviado de autores «Nombre (+N)», alineación numérica y `ROL_ACTIVO`.
  - `ProxyCatalogoProductos`: proxy reactivo con ordenamiento numérico en la columna de Año y filtros reactivos cruzados (texto, tipología, validación y estado).
  - `DialogoConfirmarEliminar`: confirmación modal de eliminación con inspección de dependencias (`describir_cascada`).
  - `FichaProducto`: ficha lateral de 360 px con cuadro de metadatos, insignia de ventana del Modelo 2024 con tooltip descriptivo, lista interactiva de coautores y botones de acción.
  - `PantallaProductos`: contenedor general del catálogo con barra de contexto, tarjeta de filtros/tabla, divisor responsivo (`QSplitter`), atajos (`Ctrl+F`) y exportación a CSV.
- Se exportaron `PantallaProductos` y `FichaProducto` en `src/pea/gui/pantallas/__init__.py`.
- Se integró `PantallaProductos` en `src/pea/gui/ventana_principal.py` reemplazando el marcador provisional en `_pantalla_productos_modulo` (índice 3: `Pantalla.PRODUCTOS`), conectando las señales de navegación, sincronización de filtros temporales, modificaciones de datos y navegación cruzada desde/hacia Investigadores y Grupos.
- Se amplió la función `ejecutar_autoprueba()` en `ventana_principal.py` para capturar la pantalla de Productos en los 4 tamaños oficiales (1366×768, 1920×1080, 1100×700 y 1360×820).
- Se diseñó la suite de pruebas unitarias en `tests/unit/test_pantalla_productos.py` (8 pruebas completas cubriendo construcción, datos, filtros reactivos, selección, navegación interactiva de coautores, productos inactivos, diálogo de eliminación y filtro de años).
- Se ejecutó `python -m pea.gui --autoprueba`, validando la generación correcta de las 4 capturas de pantalla de productos en `datos/capturas/pantalla_productos_*.png`.

## Verificación
- `ruff check src tests`: 0 advertencias, estilo impecable.
- `pytest tests/unit/test_pantalla_productos.py`: 8 pruebas pasadas.
- `pytest tests/unit`: 153 pruebas unitarias pasadas (1 deselectionada para entorno con red), 100% verde en toda la aplicación.
- `python -m pea.gui --autoprueba`: ejecutado exitosamente generando capturas visuales en `datos/capturas/pantalla_productos_*.png`.
- `python tools/brain/verificar_brain.py`: validación de la bóveda de documentación viva.
