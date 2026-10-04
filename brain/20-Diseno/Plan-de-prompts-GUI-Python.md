---
tipo: nota-de-diseno
estado: revisado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[_Indice]]"
  - "[[GUI-Diseno-Python]]"
  - "[[GUI-paridad]]"
  - "[[ADR-0016-Alcance-de-pantallas-y-datos-del-boceto]]"
  - "[[ADR-0017-Tecnologia-de-interfaz-Qt-Widgets]]"
origen: "Plan de trabajo para rehacer la interfaz de Python con Antigravity, 2026-10-03"
---

# Diseño · Plan de prompts para rehacer la interfaz de Python

## Propósito
Secuencia de prompts, **uno por vez**, para que el agente rehaga `src/pea/gui/` siguiendo [[GUI-Diseno-Python]]. Cada prompt es corto a propósito: el detalle vive en esa nota y el agente debe leerla. No incluye nada de C++.

## Cómo usarlos
1. Un prompt por conversación nueva del agente (o tras «limpiar contexto»). Espera el reporte final y revisa la captura antes de pasar al siguiente.
2. En los prompts marcados con 🖼 **adjunta las imágenes** indicadas (están en `brain/_adjuntos/`). Con texto solo no basta.
3. Rama sugerida: `feat/gui-rediseno-<tu-iniciales>`. Un commit por prompt (`feat:`, `test:`, `docs:`).
4. Si el agente propone algo que contradice [[GUI-Diseno-Python]], gana la nota.

## Orden

| # | Prompt | Resultado | Imágenes |
|---|---|---|---|
| 00 | Lectura y plan | Resumen y confirmación; nada de código | 🖼 las cuatro |
| 01 | Servicios nuevos | `serie_anual_por_categoria`, `red_coautoria`, `actualizar_producto`, datos de fichas, con pruebas | — |
| 02 | Tokens y recursos | `estilo.py`, `formato.py`, íconos, logos | 🖼 inicio + acabado |
| 03 | Componentes base | Tarjeta, ficha KPI, píldora, avatar, búsqueda, selector, avisos, vacíos | 🖼 inicio + acabado |
| 04 | Gráficos | Barras apiladas, dona doble, serie anual, minigráfico, mini red | 🖼 inicio + acabado |
| 05 | Tablas, fichas y diálogos | `TablaEstilizada`, delegados, `FichaLateral`, `dialogos.py` | 🖼 investigadores |
| 06 | Ventana principal | Barra superior, pestañas, filete, pie, atajos, historial | 🖼 inicio + acabado |
| 07 | Inicio | Pantalla Inicio (institución y grupo) | 🖼 inicio + acabado |
| 08 | Investigadores | Directorio + ficha | 🖼 investigadores |
| 09 | Grupos | Directorio + ficha | 🖼 investigadores + inicio |
| 10 | Productos | Catálogo + ficha | 🖼 investigadores |
| 11 | Análisis de redes | Grafo interactivo y métricas | 🖼 red |
| 12 | Importar, Configuración y Acerca de | Tres pantallas restantes | 🖼 inicio |
| 13 | Pruebas y limpieza | Pruebas nuevas, autoprueba en tres tamaños, retiro del código viejo | — |
| 14 | Revisión final (QA) | Comparación con referencias y lista de ajustes | 🖼 las cuatro |
| 15 | *(opcional)* Proyectos | Pestaña extra si el usuario la quiere | — |

## Bloque común (pégalo al inicio de cada prompt)

```text
Contexto: proyecto PEA-i (repo actual). Vas a trabajar SOLO en la interfaz de Python (PySide6). No toques cpp/.
Antes de empezar:
1. Lee AGENTS.md, .agent/rules/07-interfaz-python.md y brain/20-Diseno/GUI-Diseno-Python.md completo.
2. Lee las últimas notas de brain/50-Bitacora/ y ejecuta git status.
3. Mira las imágenes adjuntas (o las de brain/_adjuntos/ref-*): imita su ESTRUCTURA y ORDEN, pero no copies cifras, nombres ni logos; usa solo datos reales de los servicios (ver sección 7 de la nota).
Reglas: solo Qt Widgets + QSS + QPainter + QtSvg; colores y tamaños solo desde estilo.py; la interfaz solo llama a ServicioAplicacion; textos en español; cuerpo ≥ 11 pt; contraste ≥ 4,5:1.
Al terminar: ruff check, pytest tests/unit (muestra salidas reales), nota en brain/50-Bitacora/ y commit. Entrega con el REPORTE FINAL de AGENTS.md.
Si algo del prompt contradice la nota GUI-Diseno-Python.md, avísame y sigue la nota.
```

## Prompts

### P-UI-00 · Lectura y plan *(solo lectura)*
```text
[Bloque común]
Tarea: NO escribas código. Lee la nota y las cuatro imágenes y responde:
1. En 10 líneas, cómo será la ventana (barra superior, pestañas, pie) y cada una de las siete pantallas.
2. Tabla «archivo actual de src/pea/gui → qué pasa con él» (se reemplaza, se mueve o se borra).
3. Qué servicios nuevos hacen falta y qué hipercubo o multilista usarán.
4. Riesgos o dudas. Si algo es ambiguo, haz UNA pregunta.
5. Crea la rama feat/gui-rediseno-<iniciales> y ejecuta la línea base: ruff check y pytest tests/unit (muestra cuántas pruebas pasan hoy).
```

### P-UI-01 · Servicios nuevos
```text
[Bloque común]
Rol: ingeniero Python (no escribas en src/pea/gui).
Tarea: añade a ServicioAplicacion, con pruebas en tests/unit, lo que pide GUI-Diseno-Python.md (secciones 6 y 7):
1. serie_anual_por_categoria(filtro, codigo_grupo=None) -> dict[int, dict[str,int]] (año → GNC/DTI/ASC/FRH). Calcúlala desde el hipercubo con rebanada y enrollar, sin consultar la base. Debe coincidir con productos_por_anio al sumar tipologías.
2. red_coautoria(filtro, codigo_grupo=None, min_coautorias=2) -> nodos (código, nombre, categoría, grupo principal, grado, intermediación), aristas (origen, destino, productos compartidos) y resumen (investigadores, vínculos, densidad). Desde la multilista. Intermediación con el algoritmo de Brandes escrito a mano. Orden y resultados deterministas.
3. actualizar_producto(codigo, datos) -> str: edita cualquier campo (título, tipología, subtipo, año, validación, grupo) con la misma compensación, validación y apilado en la pila de deshacer que actualizar_grupo.
4. Datos para fichas: estudiantes del grupo, productos avalados, años con producción por investigador, coautores (grado) por investigador y aporte del grupo a la institución.
Pruebas: casos normales, vacío, un solo nodo, filtros de año, grupo inexistente, deshacer de actualizar_producto y fallo de persistencia (reversión). Anota en GUI-paridad.md que son deuda de paridad con C++.
Criterio: pytest verde y estadísticas idénticas a las ya existentes.
```

### P-UI-02 · Tokens y recursos 🖼
```text
[Bloque común]
Tarea:
1. Reescribe src/pea/gui/estilo.py con TODOS los tokens de la sección 4 (color, tipografía, espaciado, radios, sombras, movimiento) y una función que genere la hoja de estilo global. Elimina la paleta vieja (#003366, #0D47A1…).
2. Crea src/pea/gui/formato.py: números con QLocale es_CO (miles con punto, decimales con coma), porcentajes, iniciales de nombre, nombre completo de cada tipología (GNC = Generación de nuevo conocimiento, DTI = Desarrollo tecnológico e innovación, ASC = Apropiación social del conocimiento, FRH = Formación de recurso humano).
3. Crea src/pea/gui/recursos/: iconos SVG de la sección 4.4 (24×24, trazo 1,75, un color cada uno), logo_pea.svg (átomo blanco) y logo_upc.png recortado al contenido desde docs/entrada/identidad/logo_upc.png (NO modifiques el original). Asegura que se incluyan al empaquetar (pyproject).
4. Cargador de recursos con QtSvg y caché.
Pruebas: tokens con contraste ≥ 4,5:1 para cada par texto/fondo de la tabla 4.1, formato de números y que todos los recursos existan.
```

### P-UI-03 · Componentes base 🖼
```text
[Bloque común]
Tarea: crea los componentes de la sección 8 (tarjeta, ficha KPI con minigráfico opcional, píldora, avatar, campo de búsqueda con retardo de 250 ms, selector segmentado, chip de ventana con popover del filtro de años, estado vacío, esqueleto, toast con gestor, animacion.py que respete PEA_SIN_ANIMACIONES). Conserva la API pública de TarjetaKPI.actualizar(valor, subtitulo).
Cada componente con objectName propio, setAccessibleName, foco visible y estados hover/pulsado/deshabilitado.
Crea un archivo temporal tools/galeria_gui.py que muestre todos los componentes juntos y guarda su captura offscreen en datos/capturas/galeria.png. Compárala con ref-inicio-acabado.jpg y dime qué se ve peor.
Pruebas con pytest-qt (offscreen) de cada componente.
```

### P-UI-04 · Gráficos 🖼
```text
[Bloque común]
Tarea: crea src/pea/gui/componentes/graficos/ con la sección 9: base (exportar PNG a doble resolución y estado vacío), barras apiladas, dona doble, serie anual, minigráfico y mini red. Tooltip oscuro al pasar el ratón, leyenda con clic para atenuar series, animación de entrada y botón «Ver como tabla» en las barras apiladas.
Colores de datos de la tabla 4.1; ningún dato solo por color (etiquetas y leyenda visibles).
Mantén temporalmente los gráficos viejos hasta el prompt 13.
Genera capturas con datos de demostración y compáralas con ref-inicio-acabado.jpg (el boceto debe quedar igualado o superado).
Pruebas: datos vacíos, un solo dato, valores grandes, exportación PNG con tamaño correcto.
```

### P-UI-05 · Tablas, fichas y diálogos 🖼
```text
[Bloque común]
Tarea:
1. componentes/tabla.py: TablaEstilizada (filas de 48 px, hover, selección con barra de acento, encabezado, orden con QSortFilterProxyModel, pie «Mostrando N de M») y delegados de píldora, avatar + nombre, enlace con copia al portapapeles y número.
2. componentes/ficha_lateral.py: base de 360 px con cabecera, fichas KPI y zona de acciones.
3. src/pea/gui/dialogos.py: mueve DialogoGrupo, DialogoInvestigador, DialogoProducto desde pantalla_gestion.py, con el estilo nuevo, errores bajo cada campo, y un DialogoEditarProducto (usa actualizar_producto).
4. componentes/popover_historial.py.
No borres aún pantalla_gestion.py. Pruebas de cada pieza y capturas comparadas con ref-investigadores.png.
```

### P-UI-06 · Ventana principal 🖼
```text
[Bloque común]
Tarea: reescribe ventana_principal.py según la sección 5:
- Barra superior con degradado, átomo + «PEA-i» + eslogan, siete pestañas con íconos (orden y textos exactos), botón Deshacer con insignia y popover de historial, avatar con iniciales, «Cerrar sesión» y «ⓘ Acerca de», filete institucional UPC de 3 px, píldora «Datos de demostración».
- Pie institucional con logo UPC en pastilla blanca, texto institucional y estado vivo (conexión, revisión, deshacer, cola).
- QStackedWidget con transición de 200 ms; enum Pantalla (INICIO=0 … ACERCA=7) y seleccionar_pantalla(Pantalla).
- Aviso de revisión («La base de datos cambió…» + Recargar ahora), franja de sin conexión, toasts, atajos Ctrl+1…7, Ctrl+Z, Ctrl+F, F5, Ctrl+S, Alt+←.
- Filtro de años global compartido; temporizador de revisión como hoy.
- Barra de título oscura en Windows (try/except).
Las pantallas aún no existen: usa marcadores de posición con EstadoVacio. Conserva _btn_deshacer, _apilador, _pestanas y _pie. Tamaño 1360×820 (mínimo 1100×700), responsivo según sección 11.
Captura en tres tamaños y compárala con ref-inicio.png y ref-inicio-acabado.jpg.
```

### P-UI-07 · Inicio 🖼
```text
[Bloque común]
Tarea: crea pantallas/inicio.py según 6.1: selector «Institución | Grupo», tarjeta de Ámbito (avatar, líneas, «Ver más detalles», 6 fichas), barras apiladas, dona doble, mini red (sin datos reales aún: usa red_coautoria del prompt 01 si ya está), segunda fila con rankings, menú Exportar (CSV/PNG), estado vacío con dos botones, esqueleto de carga. Rejilla de 4 columnas a ≥ 1360 px y 2×2 por debajo.
Datos solo de ServicioAplicacion; nada de cifras del boceto.
Captura con datos de demostración en 1366×768 y 1920×1080 y compárala con ref-inicio.png y ref-inicio-acabado.jpg: debe verse igual de limpia o mejor.
```

### P-UI-08 · Investigadores 🖼
```text
[Bloque común]
Tarea: crea pantallas/investigadores.py según 6.2: directorio con búsqueda (Ctrl+F), combos Grupo, Categoría y Estado, «+ Nuevo investigador», tabla con avatar, píldora, código CvLAC copiable y orden; ficha lateral con KPI, minigráfico, barras por tipología y botones Editar, Activar/Desactivar, Eliminar… (muestra describir_cascada), Ver ficha completa (diálogo con aportes, membresías y productos) y Ver productos. Inactivos al 60 %. Toasts en vez de cuadros de éxito.
Compara la captura con ref-investigadores.png.
```

### P-UI-09 · Grupos 🖼
```text
[Bloque común]
Tarea: crea pantallas/grupos.py según 6.3, reutilizando FichaGrupo (la misma tarjeta de Ámbito de Inicio en modo Grupo). Combos de categoría y estado, «+ Nuevo grupo», tabla y botones de la ficha con diálogo de ficha completa (integrantes y productos enlazados).
```

### P-UI-10 · Productos 🖼
```text
[Bloque común]
Tarea: crea pantallas/productos.py según 6.4: búsqueda, combos de tipología, validación y estado, «+ Nuevo producto», tabla con píldoras y autores «Nombre +2», ficha con coautores clicables, insignia de la ventana del Modelo 2024 con tooltip, y botones Editar (DialogoEditarProducto), Activar/Desactivar y Eliminar. El filtro de años global afecta la tabla.
```

### P-UI-11 · Análisis de redes 🖼
```text
[Bloque común]
Tarea: crea src/pea/gui/red/ (vista_red.py, nodo.py, arista.py, disposicion.py) y pantallas/redes.py según 6.5 y ADR-0015: QGraphicsView, nodos por categoría y tamaño por grado, aristas por productos compartidos, disposición por fuerzas en EjecutorAsincrono con semilla fija, zoom con rueda, arrastre, resaltado de vecinos, selección con panel de métricas, doble clic abre al investigador, combo de grupo, mínimo de coautorías, búsqueda, Reordenar y leyenda. Tope de 400 nodos con aviso. Conecta también el MiniRed de Inicio.
Compara con ref-red-coautorias.png.
Pruebas: el layout es determinista, y filtros y selección actualizan el panel.
```

### P-UI-12 · Importar, Configuración y Acerca de 🖼
```text
[Bloque común]
Tarea: crea pantallas/importar.py (tres tarjetas de fuente con arrastrar y soltar, cola con píldoras de estado y progreso, toast de resultado), pantallas/configuracion.py (selector «Conexión | Verificación cruzada»; conserva toda la funcionalidad de las antiguas pantalla_conectar y pantalla_cruzada) y pantallas/acerca.py (se abre desde «ⓘ Acerca de», con botón Volver e integrantes). Todo en hilos con EjecutorAsincrono, sin congelar la ventana.
```

### P-UI-13 · Pruebas y limpieza
```text
[Bloque común]
Tarea:
1. Borra los archivos viejos de src/pea/gui/pantallas (pantalla_*.py), componentes/graficos.py y filtro_anios viejo, cuando ya nada los use (git grep).
2. Reescribe tests/unit/test_gui_completa.py y test_cli_gui.py a la estructura nueva (siete pestañas con sus textos, navegación entre todas, filtros, fichas, creación/edición/deshacer, importación con cola, exportaciones, red, estados vacío y sin conexión).
3. Actualiza ejecutar_autoprueba: capturas pantalla_<nn>_<nombre>_<ancho>x<alto>.png en 1100×700, 1366×768 y 1920×1080, con PEA_SIN_ANIMACIONES=1.
4. Corre ruff check, pytest tests/unit y python -m pea.gui --autoprueba. Muestra salidas reales y cuántas pruebas pasan.
5. Búsqueda de textos en inglés y de colores escritos a mano fuera de estilo.py.
```

### P-UI-14 · Revisión final (QA) 🖼
```text
Rol: QA (revisa SIN modificar). [Bloque común]
Tarea: compara las capturas de datos/capturas con las cuatro imágenes de referencia y la lista de criterios de la sección 15. Entrega una tabla pantalla × criterio (OK / falla / mejora) con evidencia, más: textos en inglés, contrastes, desbordes en los tres tamaños, pantallas que bloquean la ventana, y cualquier cifra o logo copiado del boceto. No arregles nada: lista los ajustes por prioridad.
Después, en otra conversación, aplica solo los ajustes que yo apruebe.
```

### P-UI-15 · Proyectos *(opcional)*
```text
[Bloque común]
Solo si lo pido: añade tabla_proyectos al servicio (entidad Proyecto ya existe), una pestaña «Proyectos» entre Grupos y Productos con tabla, ficha y filtros, y actualiza GUI-Diseno-Python.md y ADR-0016 en la misma tarea.
```

## Decisiones relacionadas
- [[GUI-Diseno-Python]]
- [[ADR-0016-Alcance-de-pantallas-y-datos-del-boceto]]

## Riesgos y casos borde
- Si el agente intenta hacer varios prompts de una vez, pierde calidad: pídele que haga solo el que pegaste.
- Los prompts 07 a 12 dependen de los servicios del 01; si falta algo, el agente debe avisar en vez de inventar datos.
- Cada prompt deja el código en un estado que ejecuta (las pantallas pendientes usan marcadores de posición).
