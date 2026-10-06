---
tipo: bitacora
estado: revisado
creado: 2026-10-06
actualizado: 2026-10-06
relacionado:
  - "[[GUI-Diseno-Python]]"
  - "[[2026-10-06-antigravity-acerca-tarjeta-institucional-ficha-tecnica]]"
origen: "Corrección de distribución responsive de tablas en pantallas de Investigadores y Grupos"
agente: "Antigravity"
rama: "master"
commit: "fix: corregir distribucion responsive de tablas en investigadores y grupos"
---

# Bitácora · Distribución Responsive de Tablas en Investigadores y Grupos

## Objetivo
Corregir la distribución responsive de las tablas de [`src/pea/gui/pantallas/investigadores.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/pantallas/investigadores.py) y [`src/pea/gui/pantallas/grupos.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/pantallas/grupos.py):
1. En resolución compacta (1100×700) la columna principal de «Nombre» / «Grupo» debe conservar un ancho útil (>= 240 px) y su cabecera nunca debe quedar recortada como «Nor», «Nomb-» o «Grupo Ficticio de Ing».
2. Ajustar prioridades en `ColumnSpecification` para ocultar columnas secundarias de menor relevancia antes de comprimir la columna principal, garantizando cero barras de desplazamiento horizontal (`ScrollBarAlwaysOff`).
3. Aplicar elipsis (`...`) a los textos largos mediante `QFontMetrics.elidedText` solo cuando sea estrictamente necesario y asegurar que se despliegue un tooltip nativo con el valor completo al pasar el puntero sobre la celda o cabecera.
4. Mantener intactas las columnas, el funcionamiento de la selección de filas, la visualización en la ficha lateral y la exportación a CSV.

## Diagnóstico y Causa Raíz
1. **Modo de columna «contenido» (`ResizeToContents`) desbordante**:
   - En las tablas de Investigadores y Grupos, varias columnas secundarias de texto libre («Grupo(s)», «Líder») estaban configuradas con `modo="contenido"`.
   - Qt calcula para estas columnas el ancho exacto del contenido más largo (e.g. 623 px para «Grupo(s)» y 443 px para «Líder»). Al sumar los anchos fijos y calculados, el ancho acumulado superaba ampliamente los ~700 px disponibles del viewport en 1100×700.
   - Dado que `_VistaTablaEstilizada` fuerza `setHorizontalScrollBarPolicy(ScrollBarAlwaysOff)`, la única columna con `modo="estirar"` (Nombre) recibía el residuo: escasos 98 px. Al restar los 24 px de márgenes internos del encabezado, el área para texto era de solo 74 px, provocando que la cabecera se cortara como «Nor» o «Nomb-» y que los textos de celda quedaran mutilados.
2. **Falta de elipsis y tooltips en los delegados visuales**:
   - `AvatarNombreDelegate` dibujaba el nombre directamente con `drawText(rect_nom, ...)` sin calcular previamente `fontMetrics().elidedText`.
   - Ninguno de los delegados (`AvatarNombreDelegate`, `PildoraDelegate`, `NumeroDelegate`) interceptaba el evento `helpEvent` (`QEvent.Type.ToolTip`), por lo que las celdas truncadas no proveían mecanismo accesible de lectura completa.
3. **Modelos sin soporte para `ToolTipRole`**:
   - `ModeloDirectorioInvestigadores` y `ModeloDirectorioGrupos` solo respondían a `Qt.ItemDataRole.DisplayRole` en `data()` y `headerData()`, ignorando `Qt.ItemDataRole.ToolTipRole`.
4. **Desfase de geometría en el divisor del Splitter**:
   - En `_ajustar_distribucion_responsive()`, el cálculo de espacio disponible dependía de `self._splitter.width() - ancho_ficha`. Durante los ciclos de eventos `resizeEvent`, el ancho del splitter interno a menudo aún no se había actualizado por parte del motor de layout de Qt, provocando lecturas erróneas.

## Qué se hizo
1. **En [`src/pea/gui/componentes/tabla.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/componentes/tabla.py)**:
   - En `AvatarNombreDelegate.paint()`: se calculó la elisión explícita del texto con `fontMetrics().elidedText(nombre, Qt.TextElideMode.ElideRight, int(ancho_nom))` para garantizar un truncado limpio con puntos suspensivos sin invadir el avatar.
   - En `AvatarNombreDelegate`, `PildoraDelegate` y `NumeroDelegate`: se implementó el método `helpEvent()` para responder al evento de tooltip (`QEvent.Type.ToolTip`) mostrando `QToolTip.showText` con el texto completo y sin truncar.
   - En `_VistaTablaEstilizada._aplicar_columnas()`: se afinó el criterio de ordenamiento para desempate al ocultar columnas: `key=lambda i: (specs[i].prioridad, i)`, garantizando que a igual prioridad se oculten primero las columnas situadas más a la derecha.

2. **En [`src/pea/gui/pantallas/investigadores.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/pantallas/investigadores.py)**:
   - En `ModeloDirectorioInvestigadores`: se agregó soporte para `Qt.ItemDataRole.ToolTipRole` tanto en `data()` (retornando el valor de la celda) como en `headerData()` (retornando el título de la columna).
   - En `configurar_columnas()`: se reemplazaron los modos `contenido` con anchos fijos delimitados y prioridades graduadas:
     - Col 0 (`Nombre`): modo `"estirar"`, mín. 240 px, prioridad 1 (siempre visible).
     - Col 1 (`Grupo(s)`): modo `"fijo"`, 150 px, prioridad 3 (ocultable en compacta).
     - Col 2 (`Categoría`): modo `"fijo"`, 105 px, prioridad 2.
     - Col 3 (`Formación`): modo `"fijo"`, 110 px, prioridad 3 (ocultable en compacta).
     - Col 4 (`Productos`): modo `"fijo"`, 80 px, prioridad 2.
     - Col 5 (`Código CvLAC`): modo `"fijo"`, 110 px, prioridad 3 (ocultable en compacta).
   - En `_ajustar_distribucion_responsive()`: se reemplazó `self._splitter.width()` por `max(200, self.width() - 48)`, garantizando sincronía inmediata con la ventana.

3. **En [`src/pea/gui/pantallas/grupos.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/pantallas/grupos.py)**:
   - En `ModeloDirectorioGrupos`: se agregó soporte para `Qt.ItemDataRole.ToolTipRole` en `data()` y `headerData()`.
   - En `configurar_columnas()`: se especificaron anchos fijos estables y prioridades:
     - Col 0 (`Nombre`): modo `"estirar"`, mín. 240 px, prioridad 1 (siempre visible).
     - Col 1 (`Código GrupLAC`): modo `"fijo"`, 110 px, prioridad 3 (ocultable en compacta).
     - Col 2 (`Categoría`): modo `"fijo"`, 95 px, prioridad 2.
     - Col 3 (`Líder`): modo `"fijo"`, 140 px, prioridad 3 (ocultable en compacta).
     - Col 4 (`Integrantes`): modo `"fijo"`, 85 px, prioridad 2.
     - Col 5 (`Productos`): modo `"fijo"`, 80 px, prioridad 2.
     - Col 6 (`Estado`): modo `"fijo"`, 85 px, prioridad 2.
   - En `_ajustar_distribucion_responsive()`: se vinculó el divisor a `max(200, self.width() - 48)`.

4. **Pruebas de unidad automatizadas**:
   - En [`tests/unit/test_pantalla_investigadores.py`](file:///c:/dev/PEAi-Taller2/tests/unit/test_pantalla_investigadores.py): se incorporó `test_pantalla_investigadores_tabla_responsive_y_elipsis` verificando que en 1100×700 el ancho de Nombre sea >= 240 px (efectivo ~300 px), que las columnas de prioridad 3 se oculten ordenadamente, que en 1366×768 y 1920×1080 todas las columnas sean visibles y que los tooltips estén operativos.
   - En [`tests/unit/test_pantalla_grupos.py`](file:///c:/dev/PEAi-Taller2/tests/unit/test_pantalla_grupos.py): se incorporó `test_pantalla_grupos_tabla_responsive_y_elipsis` verificando los mismos criterios para el directorio de grupos.

## Comandos y resultados
- `.\.venv\Scripts\ruff.exe check src tests` → `All checks passed!`
- `$env:QT_QPA_PLATFORM="offscreen"; .\.venv\Scripts\python.exe -m pytest tests/unit/test_pantalla_investigadores.py` → `12 passed in 1.45s`
- `$env:QT_QPA_PLATFORM="offscreen"; .\.venv\Scripts\python.exe -m pytest tests/unit/test_pantalla_grupos.py` → `12 passed in 4.41s`
- `$env:QT_QPA_PLATFORM="offscreen"; .\.venv\Scripts\python.exe -m pytest tests/unit` → `322 passed in 30.71s` (100% pruebas unitarias pasando).
- `$env:QT_QPA_PLATFORM="offscreen"; $env:PEA_SIN_ANIMACIONES="1"; .\.venv\Scripts\python.exe -m pea.gui --autoprueba` → 21/21 verificaciones OK; cero barras de desplazamiento horizontal detectadas en 1100×700, 1366×768 y 1920×1080.

## Decisiones
- Se descartó el uso de `modo="contenido"` para columnas de texto abierto en favor de `modo="fijo"` con anchos reglamentarios calculados a partir de los datos representativos de Minciencias. Esto previene que una cadena inusualmente larga infle una columna secundaria y canibalice el espacio de la columna de Nombre.
- Se implementó `helpEvent` en todos los delegados visuales estándar de la tabla para que cualquier texto que sufra elipsis por falta de espacio en pantalla muestre automáticamente un `QToolTip` nativo con el valor textual íntegro al posicionar el ratón sobre la celda.

## Pendientes y siguiente paso
- Ejecutar `python tools/brain/verificar_brain.py` para asegurar consistencia del cerebro.
- Realizar el commit correspondiente en Git.
