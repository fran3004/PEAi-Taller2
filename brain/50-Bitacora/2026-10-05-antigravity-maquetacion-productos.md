---
tipo: bitacora
estado: revisado
creado: 2026-10-05
actualizado: 2026-10-05
relacionado:
  - "[[GUI-Diseno-Python]]"
  - "[[2026-10-05-antigravity-auditoria-qa-gui]]"
  - "[[2026-10-05-antigravity-correccion-ficha-kpi]]"
origen: "Reconstrucción de maquetación de Productos, FichaProducto y ancho responsive de Título"
agente: "Antigravity"
rama: "master"
commit: "fix: corregir maquetacion de productos y ancho responsive de titulo"
---

# Bitácora · Reconstrucción de Maquetación de Productos y Ancho Responsive de Título

## Objetivo
Corregir de forma integral la maquetación de la pantalla de Productos (`src/pea/gui/pantallas/productos.py`):
1. Eliminar widgets huérfanos (`_pildora_tipologia`, `_pildora_validacion`, `_lbl_anio`) creados fuera de un layout que generaban duplicados y píldoras flotantes en la coordenada (0, 0).
2. Reconstruir la sección de metadatos y autores en `FichaProducto` con una rejilla (`QGridLayout`) persistente, ajuste de línea (`setWordWrap(True)`) y limpieza adecuada de elementos (`setParent(None)` antes de `deleteLater()`).
3. Reconfigurar las columnas de la tabla del catálogo para que la columna "Título" conserve siempre un ancho legible ($\ge 200$ px) sin colapsar a «...» y las columnas secundarias se oculten progresivamente, sin habilitar barras de desplazamiento horizontal.

## Qué se hizo
- En [`src/pea/gui/componentes/ficha_lateral.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/componentes/ficha_lateral.py):
  - En `establecer_cabecera()`, se aseguró que al limpiar las píldoras previas se invoque `widget.setParent(None)` inmediatamente antes de `widget.deleteLater()`, evitando que queden píldoras visibles flotando durante repintados síncronos.
- En [`src/pea/gui/componentes/tabla.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/componentes/tabla.py):
  - En `_aplicar_columnas()`, se corrigió la asignación de columnas fijas a `self.setColumnWidth(indice, spec.ancho_minimo)` directamente (en lugar de `max(spec.ancho_minimo, self.columnWidth(indice))`, lo cual inflaba columnas estrechas de 60-80 px a los 120 px por defecto de Qt).
  - En `NumeroDelegate.paint()`, se ajustó el margen interior de `rect_txt` de `adjusted(12, 0, -16, 0)` a `adjusted(6, 0, -8, 0)` para que los años de 4 dígitos no sufran recorte por la izquierda en anchos estrechos.
- En [`src/pea/gui/pantallas/productos.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/pantallas/productos.py):
  - Se eliminaron las instancias huérfanas de `Pildora` y `QLabel` que se creaban con `parent=self` sin layout.
  - Se expusieron las propiedades `_pildora_tipologia` y `_pildora_validacion` extrayendo los widgets directamente de `_layout_pildoras`, garantizando compatibilidad total con la suite de pruebas sin widgets huérfanos.
  - Se reconstruyó la sección de metadatos con `_layout_meta = QGridLayout(self._cuadro_meta)` persistente con etiquetas permanentes `_lbl_valor_anio`, `_lbl_valor_subtipo`, `_lbl_valor_grupo` con `setWordWrap(True)`.
  - En `actualizar()`, se desacoplan los widgets del layout de autores con `setParent(None)` antes de destruirlos para evitar cualquier solapamiento o acumulación de elementos fantasma.
  - Se reconfiguró la tabla del catálogo con 9 especificaciones de columna: Título con modo `estirar` y prioridad 1 ($\ge 200$ px, nunca sacrificada), y columnas secundarias con anchos mínimos realistas y prioridades 2 o 3 (Subtipo 115 px p3, Grupo 140 px p3, Autores 125 px p3) para ocultación progresiva en anchos de 1100 px y 1366 px.
- En [`tests/unit/test_pantalla_productos.py`](file:///c:/dev/PEAi-Taller2/tests/unit/test_pantalla_productos.py):
  - Se agregaron las pruebas de regresión:
    - `test_ficha_producto_sin_widgets_huerfanos`: verifica que no existan widgets hijos directos de la ficha sin layout y que píldoras y etiquetas pertenezcan a sus respectivos layouts.
    - `test_ficha_producto_actualizar_no_solapa_ni_acumula`: valida que múltiples llamadas consecutivas a `actualizar()` limpien correctamente la lista de autores sin acumular widgets.
    - `test_tabla_productos_titulo_ancho_legible`: comprueba en 1100×700, 1366×768 y 1920×1080 que la columna Título permanece visible, con ancho $\ge 200$ px y sin barra de scroll horizontal.

## Comandos y resultados
1. `ruff check src tests`:
   - Salida: `All checks passed!`
2. `pytest tests/unit/test_pantalla_productos.py -v`:
   - Salida: 16 passed en 3.53s.
3. `pytest tests/unit -v` (con `QT_QPA_PLATFORM=offscreen` y `PEA_SIN_ANIMACIONES=1`):
   - Salida: 201 passed, 1 deselected en 107.40s.
4. `python -m pea.gui --autoprueba`:
   - Salida: 24 capturas generadas; en pantalla_03_productos: 0 barras en todas las resoluciones, 0 widgets fuera en 1366×768 y 1920×1080.
5. Verificación visual de capturas (`datos/capturas/oficiales/pantalla_03_productos_*.png`):
   - 1100×700: Título amplio y legible, fichas de metadatos y autores limpias, sin píldoras en (0, 0), año centrado y nítido.
   - 1366×768 y 1920×1080: visualización equilibrada, autores visibles en tabla, ficha lateral perfectamente integrada.
6. `python tools/brain/verificar_brain.py`:
   - Salida: 104 notas inspeccionadas, 0 errores, 0 advertencias.

## Decisiones
- Mantener propiedades getter `_pildora_tipologia` y `_pildora_validacion` en `FichaProducto` apuntando al `_layout_pildoras` creado por `establecer_cabecera()`. Esto desacopla la creación del widget de la clase derivada y respeta la jerarquía visual nativa de `FichaLateral`.
- En `_aplicar_columnas`, fijar el ancho de columnas en modo `"fijo"` a `spec.ancho_minimo` sin permitir que Qt herede 120 px por omisión.

## Pendientes y siguiente paso
- Continuar con las siguientes observaciones de la auditoría QA en caso de requerirse ajustes en otras pantallas (ej. Investigadores o Grupos).
