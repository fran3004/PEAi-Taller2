---
tipo: bitacora
estado: revisado
creado: 2026-10-05
actualizado: 2026-10-05
relacionado:
  - "[[GUI-Diseno-Python]]"
  - "[[AUDITORIA-DISENO-PEAI]]"
  - "[[2026-10-05-copilot-autoprueba-capturas]]"
origen: "Auditoría integral QA sin modificación de código sobre src/pea/gui/"
agente: "Antigravity"
rama: "master"
commit: "solo auditoria QA (sin modificacion de codigo)"
---

# Bitácora · Auditoría QA Integral de GUI PySide6 (src/pea/gui/)

## Objetivo
Ejecutar una auditoría estricta en rol **QA** sobre la interfaz de usuario en Python (`src/pea/gui/`) sin modificar código ni suites de pruebas existentes, evaluando las 24 capturas oficiales en `datos/capturas/oficiales/` (1100×700, 1366×768 y 1920×1080), ejecutando la suite de pruebas unitarias, el linter, el script de diagnóstico de desborde y la prueba guardián de tokens de estilo, para entregar una matriz estructurada "Pantalla × Criterio" y un backlog priorizado de pendientes.

---

## Matriz de Evaluación: Pantalla × Criterio

| Pantalla | Criterio | Estado | Evidencia observable |
| :--- | :--- | :---: | :--- |
| **Inicio** | Texto legible | Mejora | En las 6 tarjetas KPI (`FichaKPI`), el valor numérico grande (`lbl_valor`) no se visualiza (espacio en blanco) debido a que `lbl_valor` tiene `QSizePolicy.Policy.Ignored` junto a un `addStretch()` en `fila_valor`, colapsando su ancho a 0. En la cabecera superior derecha, los textos «Cerrar sesión» y «Acerca de» tienen color blanco sobre fondo claro (contraste $< 1.5:1$). |
| **Inicio** | Español estricto | OK | Cero términos en inglés: «Inicio», «Institución», «Grupo», «Ventana: Modelo 2024», «Exportar», «Grupos activos», «Investigadores activos». |
| **Inicio** | Sin barras horizontales | OK | 0 barras horizontales detectadas por `diagnostico_desborde.py` y la autoprueba en las tres resoluciones. |
| **Inicio** | Fichas completas | Mejora | La ficha institucional muestra logo y rótulos, pero carece de los números de métricas por el defecto en `FichaKPI`. Gráficos de barras apiladas y minirred visibles. |
| **Inicio** | Cuerpo $\ge 11$ pt | OK | El cuerpo general respeta $\ge 11$ pt (`TAMANO_CUERPO`); los rótulos descriptivos utilizan `TAMANO_AUXILIAR` (10 pt). |
| **Investigadores** | Texto legible | Mejora | En 1100×700 la columna «Nombre» se corta en el encabezado como «Nor» / «Nomb-». Los nombres largos de grupos y programas se eliden drásticamente. En la ficha lateral, los 4 bloques KPI no muestran sus cifras cuantitativas. |
| **Investigadores** | Español estricto | OK | Todos los textos en español: «Directorio de Investigadores», «+ Nuevo investigador», «Senior», «Asociado», «Junior», «Sin categoría», «Pregrado», «Maestría», «Doctorado», «Ver ficha completa», «Ver productos». |
| **Investigadores** | Sin barras horizontales | OK | 0 barras horizontales en 1100×700, 1366×768 y 1920×1080. |
| **Investigadores** | Fichas completas | Mejora | Ficha lateral contiene avatar, nombre, acciones («Editar», «Desactivar», «Eliminar...», «Ver ficha completa», «Ver productos»), pero los KPIs están vacíos de cifras y las barras por tipología requieren desplazamiento vertical en 1100×700. |
| **Investigadores** | Cuerpo $\ge 11$ pt | OK | Conforme a especificación (`TAMANO_CUERPO` = 11 pt). |
| **Grupos** | Texto legible | Mejora | En la tabla, nombres de grupos se recortan en pantallas compactas («Grupo Ficticio de Ing»). En `FichaGrupo`, todos los bloques KPI carecen de valor numérico visible. El selector de ventana y botón exportar muestran glifos cuadrados residuales en algunas resoluciones. |
| **Grupos** | Español estricto | OK | Rótulos en español: «Directorio de grupos», «+ Nuevo grupo», «Líder», «Integrantes», «Productos», «Estado», «Activo», «Ficha completa». |
| **Grupos** | Sin barras horizontales | OK | 0 barras horizontales en las tres resoluciones. |
| **Grupos** | Fichas completas | Mejora | Ficha lateral contiene cabecera con avatar e iniciales «GF», botones y gráfico de barras apiladas, pero las cifras de integrantes, productos y estudiantes están ocultas por el fallo de tamaño en los KPIs. |
| **Grupos** | Cuerpo $\ge 11$ pt | OK | Conforme a especificación. |
| **Productos** | Texto legible | Falla | En la tabla, la columna «Título» se colapsa a «...» en todas las filas (modo `Stretch` aplastado por el ancho acumulado de las otras 8 columnas). En `FichaProducto` hay colisiones severas: la píldora «Avalado» flota en (0,0); «No ava ASC No avalado» se solapan horizontalmente; «Grupo Ficticio» se superpone sobre «Año de publicación: 2022»; y en autores vinculados el texto colisiona con la lista subyacente. |
| **Productos** | Español estricto | OK | Vocabulario de MinCiencias íntegramente en español: «Catálogo de Productos», «+ Nuevo producto», «Tipología», «Validación», «Subtipo», «Dentro de la ventana del Modelo 2024». |
| **Productos** | Sin barras horizontales | OK | 0 barras horizontales registradas. |
| **Productos** | Fichas completas | Falla | La ficha lateral está visualmente rota por widgets creados con parent `self` fuera del layout (`_pildora_tipologia`, `_pildora_validacion`) y por la acumulación de elementos no eliminados síncronamente en `actualizar()`. |
| **Productos** | Cuerpo $\ge 11$ pt | OK | Conforme a especificación. |
| **Análisis de redes** | Texto legible | Mejora | Texto residual «Métricas de c...» superpuesto sobre el título principal «Análisis de Redes de Colaboración» en la cabecera. Dos botones cuadrados adyacentes a «Ordenar» aparecen sin icono ni texto visible. |
| **Análisis de redes** | Español estricto | OK | Todo en español: «Análisis de red de colaboración», «Métricas de centralidad», «Investigadores más conectados», «Resumen de la red». |
| **Análisis de redes** | Sin barras horizontales | OK | 0 barras horizontales en todas las resoluciones. |
| **Análisis de redes** | Grafo visible en 1100×700 | Falla | En las 24 capturas (incluida 1100×700), el lienzo muestra el estado vacío «No hay datos de red para los filtros seleccionados» (Investigadores: 0, Enlaces: 0). Causa: el combo de filtro se inicializa por defecto en «Mín. 2 coautorías», mientras que en los datos de demostración las colaboraciones tienen peso 1. Se debe inicializar en «Mín. 1 coautoría». |
| **Análisis de redes** | Fichas / Panel lateral | OK | Panel lateral derecho de métricas de centralidad visible y estructurado con resumen de red. |
| **Análisis de redes** | Cuerpo $\ge 11$ pt | OK | Conforme a especificación. |
| **Importar** | Texto legible | Mejora | En las zonas de arrastrar y soltar se comprime «Formatos aceptad». Los botones deshabilitados («Encolar CSV», «Encolar PDF», «Encolar URL SCIENTI», «Procesar siguiente») presentan texto blanco sobre fondo gris claro (`#FFFFFF` sobre `#F1F5F9`), provocando contraste deficiente. |
| **Importar** | Español estricto | OK | Textos en español: «Importación e Ingesta de Fuentes», «Archivo Tabular CSV», «Documento Oficial PDF», «Enlace Web SCIENTI», «Cola de Importación». |
| **Importar** | Sin barras horizontales | OK | 0 barras horizontales en todas las resoluciones. |
| **Importar** | Fichas / Estructura | OK | Las 3 tarjetas de origen y la tabla de cola de tareas están completas y funcionales. |
| **Importar** | Cuerpo $\ge 11$ pt | OK | Conforme a especificación. |
| **Configuración** | Texto legible | Falla | En «Parámetros de Acceso a Supabase», los campos `QLineEdit` tienen una altura tan reducida que los textos de placeholder quedan cortados horizontalmente por la mitad («nttps://yyy...», «Clave publicable», «Correo», «Contraseña»). El botón deshabilitado «Conectar con Supabase» tiene texto blanco sobre fondo claro ilegible. |
| **Configuración** | Español estricto | OK | Textos en español: «Configuración del Sistema», «Estado de la Conexión», «Parámetros de Acceso a Supabase (HTTPS)», «Cargar datos de demostración», «Cerrar sesión / Desconectar», «Verificación cruzada». |
| **Configuración** | Sin barras horizontales | OK | 0 barras horizontales. |
| **Configuración** | Fichas / Estructura | OK | Estructura con selector «Conexión \| Verificación cruzada» y tarjetas de estado presentes. |
| **Configuración** | Cuerpo $\ge 11$ pt | OK | Conforme a especificación. |
| **Acerca de** | Texto legible | Mejora | En el banner institucional azul marino superior, las tres líneas muestran recuadros de borde blanco extraños, y la segunda línea («Facultad de Ingenierías...») tiene contraste insuficiente contra el fondo oscuro. La etiqueta «• Estructuras de datos en memor» se trunca en la ficha técnica. |
| **Acerca de** | Español estricto | OK | 100% en español: «Software PEA-i», «Ficha Técnica y Arquitectura», «Equipo de Desarrollo», «Estado Dinámico del Sistema», «Volver al inicio». |
| **Acerca de** | Sin barras horizontales | OK | 0 barras horizontales. |
| **Acerca de** | Fichas / Estructura | OK | Identidad institucional, arquitectura, integrantes y estado dinámico visibles. |
| **Acerca de** | Cuerpo $\ge 11$ pt | OK | Conforme a especificación. |
| **Todas** | Pestañas de navegación | Mejora | En resoluciones 1366×768 y 1920×1080, los textos bajo los iconos se recortan lateralmente («vestigadore», «álisis de rec», «configuració») por ancho fijo insuficiente en cada pestaña. En 1100×700 se oculta el texto, evitando el desborde pero omitiendo etiquetas. |
| **Todas** | Bloque sesión usuario | Falla | El contenedor superior derecho («DE», «Cerrar sesión», «Acerca de») tiene fondo claro pero el texto está forzado a blanco puro (`#FFFFFF`), haciéndolo invisible a simple vista (falla de contraste WCAG 2.1). |
| **Todas** | Barra de estado | Mejora | En 1100×700 el texto institucional central («Universidad Popular del Cesar...») se oculta por falta de espacio horizontal. |
| **Todas** | Guardianes de estilo | OK | `test_guardian_estilos_sin_literales_en_gui` aprobado al 100% (cero literales hexadecimales/rgba/pt fuera de `estilo.py`). |
| **Todas** | Resiliencia de pruebas | Mejora | Al ejecutar `pytest` sin `QT_QPA_PLATFORM=offscreen`, el gestor de ventanas de Windows restringe las ventanas al monitor físico (1370×749), provocando fallas en las aserciones de 1920×1080. Con `QT_QPA_PLATFORM=offscreen`, pasan las 195 pruebas unitarias (100%). |

---

## Comparación fila a fila contra el reporte anterior

| Elemento / Pantalla | Estado Anterior | Estado Actual | Variación / Análisis |
| :--- | :--- | :--- | :--- |
| **Barras horizontales en Inicio** | Falla (desborde en 1100×700 y 1366×768) | **OK** (Resuelto) | Corregido eficazmente mediante `_reorganizar_rejilla`, `QScrollArea` con viewport adaptable y políticas sin desborde. |
| **Centralización de tokens (`estilo.py`)** | Mejora (literales dispersos) | **OK** (Resuelto) | `test_guardian_estilos_sin_literales_en_gui` pasa al 100%. Todos los colores y tamaños salen de `estilo.py`. |
| **Fuentes institucionales Inter** | Mejora (fuentes del sistema) | **OK** (Resuelto) | Integración de tipografía Inter desde assets con fallback a fuentes del sistema. |
| **Tarjetas KPI (`FichaKPI`)** | No auditado visualmente | **Falla** (Pendiente) | Nuevo hallazgo crítico: el valor numérico destacado no se visualiza en ninguna pantalla debido a `QSizePolicy.Policy.Ignored` en `lbl_valor`. |
| **Ficha de Producto (`FichaProducto`)** | No auditado en detalle | **Falla** (Pendiente) | Defecto severo de solapamiento de píldoras huérfanas, colisión de textos de metadatos y compresión de la columna «Título» a «...». |
| **Visibilidad de Red en 1100×700** | Falla | **Falla** (Pendiente) | El lienzo se inicializa con «No hay datos» porque el filtro por defecto exige «Mín. 2 coautorías» cuando los datos de demostración tienen peso 1. |
| **Contraste en bloque de usuario** | No detectado | **Falla** (Pendiente) | Texto blanco sobre fondo claro en «Cerrar sesión» y «Acerca de». |
| **Truncamiento de pestañas en Header** | No detectado | **Mejora** (Pendiente) | Recorte de etiquetas («vestigadore», «álisis de rec», «configuració») en 1366×768 y 1920×1080. |
| **Campos comprimidos en Configuración** | No auditado visualmente | **Falla** (Pendiente) | `QLineEdit` con altura insuficiente que corta por la mitad el texto del placeholder. |
| **Contraste de botones deshabilitados** | No detectado | **Mejora** (Pendiente) | En Importar y Configuración, botones deshabilitados con texto blanco sobre fondo gris claro (`#FFFFFF` sobre `#F1F5F9`). |

---

## Comandos ejecutados y resultados reales

1. **Ruff check**:
   ```powershell
   .\.venv\Scripts\python.exe -m ruff check src tests
   ```
   *Salida real*:
   ```text
   All checks passed!
   ```

2. **Diagnóstico de desborde horizontal**:
   ```powershell
   $env:QT_QPA_PLATFORM="offscreen"; $env:PEA_SIN_ANIMACIONES="1"; .\.venv\Scripts\python.exe scripts/diagnostico_desborde.py
   ```
   *Salida real*:
   ```text
   === 1100x700 ===
   Areas con barra horizontal visible: ninguna
   === 1366x768 ===
   Areas con barra horizontal visible: ninguna
   === 1920x1080 ===
   Areas con barra horizontal visible: ninguna
   ```

3. **Prueba guardián de tokens de estilo**:
   ```powershell
   $env:QT_QPA_PLATFORM="offscreen"; $env:PEA_SIN_ANIMACIONES="1"; .\.venv\Scripts\python.exe -m pytest tests/unit/test_estilo_recursos.py::test_guardian_estilos_sin_literales_en_gui -v
   ```
   *Salida real*:
   ```text
   tests/unit/test_estilo_recursos.py::test_guardian_estilos_sin_literales_en_gui PASSED [100%]
   1 passed in 0.80s
   ```

4. **Autoprueba gráfica oficial**:
   ```powershell
   $env:QT_QPA_PLATFORM="offscreen"; $env:PEA_SIN_ANIMACIONES="1"; $env:PYTHONPATH="src"; .\.venv\Scripts\python.exe -m pea.gui --autoprueba
   ```
   *Salida real*:
   ```text
   [AUTOPRUEBA] Captura guardada en datos\capturas\oficiales\pantalla_00_inicio_1100x700.png
   ...
   [AUTOPRUEBA] Resumen
   Pantalla               Tamano      Barras   Fuera  Captura
   ----------------------------------------------------------------------------------------------------
   00_inicio              1100x700         0     149  datos\capturas\oficiales\pantalla_00_inicio_1100x700.png
   00_inicio              1366x768         0     140  datos\capturas\oficiales\pantalla_00_inicio_1366x768.png
   00_inicio              1920x1080        0       3  datos\capturas\oficiales\pantalla_00_inicio_1920x1080.png
   01_investigadores      1100x700         0      19  datos\capturas\oficiales\pantalla_01_investigadores_1100x700.png
   01_investigadores      1366x768         0      16  datos\capturas\oficiales\pantalla_01_investigadores_1366x768.png
   01_investigadores      1920x1080        0       0  datos\capturas\oficiales\pantalla_01_investigadores_1920x1080.png
   02_grupos              1100x700         0      16  datos\capturas\oficiales\pantalla_02_grupos_1100x700.png
   02_grupos              1366x768         0       7  datos\capturas\oficiales\pantalla_02_grupos_1366x768.png
   02_grupos              1920x1080        0       0  datos\capturas\oficiales\pantalla_02_grupos_1920x1080.png
   03_productos           1100x700         0      20  datos\capturas\oficiales\pantalla_03_productos_1100x700.png
   03_productos           1366x768         0      15  datos\capturas\oficiales\pantalla_03_productos_1366x768.png
   03_productos           1920x1080        0      12  datos\capturas\oficiales\pantalla_03_productos_1920x1080.png
   04_redes               1100x700         0       2  datos\capturas\oficiales\pantalla_04_redes_1100x700.png
   04_redes               1366x768         0       0  datos\capturas\oficiales\pantalla_04_redes_1366x768.png
   04_redes               1920x1080        0       0  datos\capturas\oficiales\pantalla_04_redes_1920x1080.png
   05_importar            1100x700         0       8  datos\capturas\oficiales\pantalla_05_importar_1100x700.png
   05_importar            1366x768         0       4  datos\capturas\oficiales\pantalla_05_importar_1366x768.png
   05_importar            1920x1080        0       0  datos\capturas\oficiales\pantalla_05_importar_1920x1080.png
   06_configuracion       1100x700         0       2  datos\capturas\oficiales\pantalla_06_configuracion_1100x700.png
   06_configuracion       1366x768         0       0  datos\capturas\oficiales\pantalla_06_configuracion_1366x768.png
   06_configuracion       1920x1080        0       0  datos\capturas\oficiales\pantalla_06_configuracion_1920x1080.png
   07_acerca              1100x700         0      19  datos\capturas\oficiales\pantalla_07_acerca_1100x700.png
   07_acerca              1366x768         0      12  datos\capturas\oficiales\pantalla_07_acerca_1366x768.png
   07_acerca              1920x1080        0       0  datos\capturas\oficiales\pantalla_07_acerca_1920x1080.png
   [AUTOPRUEBA] Autoprueba completada exitosamente.
   ```

5. **Pruebas unitarias completas (pytest tests/unit -v)**:
   ```powershell
   $env:QT_QPA_PLATFORM="offscreen"; $env:PEA_SIN_ANIMACIONES="1"; .\.venv\Scripts\python.exe -m pytest tests/unit -v
   ```
   *Salida real*:
   ```text
   ===================== 195 passed, 1 deselected in 59.46s ======================
   ```

---

## Pendientes y siguiente paso (Backlog Priorizado)

### Prioridad 1 (Crítico / Bloqueante visual):
1. **Corregir visualización de valores en `FichaKPI`**: En `src/pea/gui/componentes/tarjeta_kpi.py`, cambiar `self.lbl_valor.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)` a `Preferred` o definir `setMinimumWidth` con tamaño de contenido para que el número destacado no colapse a ancho 0.
2. **Reconstruir maquetación de `FichaProducto` y ancho de tabla**: En `src/pea/gui/pantallas/productos.py`, eliminar píldoras creadas fuera de layout (`_pildora_tipologia`, `_pildora_validacion`), corregir el contenedor de metadatos y autores para evitar texto solapado, y ajustar las prioridades de `ColumnSpecification` para garantizar que la columna «Título» no se reduzca a «...».
3. **Corregir contraste en bloque de usuario del Header**: En `src/pea/gui/ventana_principal.py` (o componente de cabecera), cambiar el color de texto de «Cerrar sesión» y «Acerca de» de blanco a un color con contraste suficiente sobre su contenedor (o darle fondo institucional oscuro).

### Prioridad 2 (Importante / Funcional):
4. **Visibilidad inicial del grafo de redes**: En `src/pea/gui/pantallas/redes.py`, cambiar el valor predeterminado del filtro de coautorías de «Mín. 2» a «Mín. 1 coautoría» para que el grafo y sus nodos sean inmediatamente visibles en los datos de demostración en 1100×700.
5. **Altura de campos en Configuración**: En `src/pea/gui/pantallas/configuracion.py`, aumentar la altura mínima de los `QLineEdit` de parámetros de Supabase (mínimo 36 px) para que el texto del placeholder no se corte horizontalmente.

### Prioridad 3 (Mejora visual / Accesibilidad):
6. **Ancho de pestañas en barra superior**: En la barra de navegación, ajustar el tamaño mínimo o políticas de tamaño de los botones de pestañas para que «Investigadores», «Análisis de redes» y «Configuración» no se trunquen en 1366×768 ni 1920×1080.
7. **Estilo de botones deshabilitados**: En `src/pea/gui/estilo.py`, definir un color de texto accesible para botones en estado `:disabled` sobre fondos claros (p. ej. texto secundario con ratio $\ge 4.5:1$).
8. **Banner y elisiones en Acerca de**: Limpiar los bordes residuales de texto en el banner azul y asegurar ancho suficiente para «• Estructuras de datos en memoria».

