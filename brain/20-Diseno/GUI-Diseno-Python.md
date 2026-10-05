---
tipo: nota-de-diseno
estado: revisado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[_Indice]]"
  - "[[Arquitectura]]"
  - "[[GUI-paridad]]"
  - "[[ADR-0012-Diseno-GUI-y-navegacion]]"
  - "[[ADR-0013-Vistas-secundarias]]"
  - "[[ADR-0015-Analisis-de-red-nativo]]"
  - "[[ADR-0016-Alcance-de-pantallas-y-datos-del-boceto]]"
  - "[[ADR-0017-Tecnologia-de-interfaz-Qt-Widgets]]"
  - "[[SPEC]]"
  - "[[Hipercubo]]"
  - "[[Multilista]]"
origen: "Bocetos de referencia del usuario (brain/_adjuntos/ref-*) y revisión del código de src/pea/gui — 2026-10-03"
---

# Diseño · Interfaz gráfica de PEA-i en Python (PySide6)

## 1. Propósito y alcance

Esta nota es la **única fuente de verdad del diseño visual y de interacción** de la aplicación de escritorio en **Python (PySide6)**. Cualquier agente o persona que construya, cambie o revise la interfaz de Python se guía por este documento y por las imágenes de referencia que él enlaza.

- **Cubre**: identidad visual, estructura de la ventana, cada pantalla, componentes, gráficos, estados, atajos, accesibilidad y criterios de aceptación.
- **No cubre**: la interfaz de C++. Esa se definirá más adelante con prompts aparte; hasta entonces ver [[GUI-paridad]] (qué deberá igualar C++ cuando le toque).
- **Reemplaza por completo** cualquier descripción anterior de la interfaz (barra lateral de lista, diseño en «cuatro zonas», árbol de navegación con divisores). Esas ideas ya no rigen.

> [!IMPORTANT] Regla de oro
> La interfaz **imita la estructura y el orden** de los bocetos, pero **no copia marcas, cifras ni datos inventados**. Todo número que se vea en pantalla sale de los servicios. Y el resultado final debe verse **más pulido y más agradable** que el boceto, sin salirse de su estructura ni de lo que PEA-i realmente sabe hacer.

## 2. Imágenes de referencia

Estas cuatro imágenes también deben adjuntarse al agente cuando construya pantallas (el texto solo no alcanza para reproducir proporciones y acabados).

| Imagen                      | Qué se toma de ella                                                                                                                                               |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ![[ref-inicio.png]]         | Estructura de **Inicio**: barra superior con degradado y pestañas, tarjeta del grupo con avatar circular, fichas KPI en cuadrícula, dos gráficos, mini red y pie. |
| ![[ref-inicio-acabado.jpg]] | **Acabado visual**: sombras suaves, íconos de color, degradado del encabezado, gráficos con más presencia. Es la vara de calidad mínima.                          |
| ![[ref-investigadores.png]] | Patrón **directorio + ficha lateral**: tabla con buscador y filtros, botón primario «+ Nuevo…», ficha con avatar y cuatro fichas KPI.                             |
| ![[ref-red-coautorias.png]] | **Análisis de redes**: grafo grande a la izquierda y panel de métricas de centralidad a la derecha.                                                               |

**Qué NO se toma**: los logos y el texto legal de terceros del pie (ver [[ADR-0016-Alcance-de-pantallas-y-datos-del-boceto]]), los nombres ficticios de los nodos, las cifras de ejemplo (21, 6, 150, 14…) y los datos que PEA-i no tiene (H-Index, ORCID, semilleros, centros, convocatorias).

## 3. Principios de diseño

1. **Datos reales primero**: si el dato no existe en el dominio, no se dibuja. Se reemplaza por uno equivalente que sí exista (tabla de la sección 7).
2. **Jerarquía clara**: lo importante (cifras, estado de conexión, acción principal) se ve primero; lo secundario, más tenue.
3. **Un mismo dato, un mismo color** en toda la aplicación (tipologías, validaciones, categorías).
4. **Respuesta inmediata**: nada de la red o la ingesta bloquea la ventana; todo cambio confirma con un aviso breve (*toast*) en vez de un cuadro modal.
5. **Identidad institucional**: el azul profundo del boceto es la base; el verde de la UPC aparece como acento institucional (sección 4.1).

## 4. Tokens de diseño

Son constantes con nombre en `src/pea/gui/estilo.py`. Ningún archivo de la interfaz escribe un color, tamaño o radio «a mano»: siempre usa un token.

### 4.1 Color

Valores tomados del boceto (muestreo de píxeles) y ajustados donde el contraste no alcanzaba 4,5:1.

| Token | Hex | Uso | Contraste |
|---|---|---|---|
| `ENCABEZADO_INICIO` | `#0A2045` | Degradado de la barra superior, extremo izquierdo | blanco sobre él: 16,1:1 |
| `ENCABEZADO_MEDIO` | `#0E3A5C` | Degradado, punto medio | |
| `ENCABEZADO_FIN` | `#0E405C` | Degradado, extremo derecho | blanco: 11,0:1 |
| `ACENTO` | `#35B6E8` | Subrayado de pestaña activa, foco, enlaces sobre fondo oscuro | sobre `#0A2045`: 6,9:1 |
| `PRIMARIO` | `#0E3A5C` | Botón primario (hover `#0A2D49`, pulsado `#082338`) | blanco: 11,8:1 |
| `FONDO_APP` | `#F1F5F9` | Fondo general | |
| `SUPERFICIE` | `#FFFFFF` | Tarjetas, tablas, diálogos | |
| `FICHA` | `#E9EEF6` | Fichas KPI y encabezado de tabla | |
| `PIE` | `#D4DAE3` | Fondo del pie institucional | texto `#243648`: 8,8:1 |
| `LINEA` | `#D9E1EA` | Bordes finos y separadores | |
| `LINEA_FUERTE` | `#C3CFDC` | Bordes de campos de texto | |
| `TEXTO` | `#102B44` | Texto principal y títulos | sobre blanco: 14,5:1 |
| `TEXTO_SECUNDARIO` | `#475A6C` | Rótulos, ayudas | sobre blanco 7,1:1; sobre `FICHA` 6,1:1 |
| `TEXTO_SOBRE_OSCURO` | `#FFFFFF` | Texto en el encabezado | |
| `TEXTO_SOBRE_OSCURO_SUAVE` | `#C9D8EA` | Pestañas inactivas | sobre `#0E3A5C`: 8,2:1 |
| `ENLACE` | `#1F6F94` | Enlaces y códigos CvLAC | sobre blanco: 5,6:1 |
| `UPC_VERDE_OSCURO` | `#0F7B47` | Filete institucional, éxito | tomado del logo UPC |
| `UPC_VERDE` | `#43A242` | Filete institucional | tomado del logo UPC |
| `UPC_VERDE_CLARO` | `#A3CD91` | Filete institucional | tomado del logo UPC |
| `EXITO` / fondo | `#1B6E3F` / `#E6F4EC` | Avisos de éxito | 5,5:1 |
| `AVISO` / fondo | `#8A4B00` / `#FFF1DC` | Advertencias, modo demostración | 6,1:1 |
| `ERROR` / fondo | `#A12626` / `#FDECEC` | Errores, acciones destructivas | 6,5:1 |
| `INFO` / fondo | `#196E8F` / `#E3F1F7` | Información neutra | |

**Colores de datos** (siempre los mismos en toda la app):

| Dato | Color | Hex |
|---|---|---|
| Tipología **GNC** | azul datos | `#17375E` |
| Tipología **DTI** | petróleo | `#1F7A9E` |
| Tipología **ASC** | turquesa | `#2BB0A0` |
| Tipología **FRH** | índigo | `#4B4C9D` |
| Validación **Avalado** | verde suave | `#6BBF8E` |
| Validación **Con soporte** | naranja | `#E59D53` |
| Validación **No avalado** | gris azulado | `#9DB5C9` |
| Categoría **Emérito** | índigo | `#4B4C9D` |
| Categoría **Senior** | petróleo oscuro | `#196E8F` (texto blanco 5,7:1) |
| Categoría **Asociado** | azul datos | `#17375E` (texto blanco 12:1) |
| Categoría **Junior** | turquesa oscuro | `#0F7F73` (texto blanco 4,9:1) |
| Sin categoría | gris | fondo `#E3E9F0`, texto `#3F5163` |
| Aristas de la red | gris azulado | `#9DB5C9` |

> [!WARNING] Contraste de los colores de datos
> Turquesa, verde suave y naranja no llegan a 3:1 contra blanco. Por eso **ningún dato se comunica solo por color**: cada segmento lleva etiqueta o valor en texto, la leyenda siempre está visible y hay un borde blanco de 1,5 px entre segmentos.

### 4.2 Tipografía

Familia: `"Segoe UI", "Inter", "Noto Sans", "Helvetica Neue", sans-serif` (Windows trae Segoe UI; no se empaquetan fuentes).

| Rol | Tamaño | Peso |
|---|---|---|
| Marca «PEA-i» | 30 pt | Black (800) |
| Valor de ficha KPI | 22 pt | Bold |
| Título de pantalla | 18 pt | Semibold |
| Título de tarjeta | 14 pt | Bold (con barra de acento a la izquierda) |
| Subtítulo | 12 pt | Regular |
| **Cuerpo, tablas, pestañas** | **11 pt** | Regular |
| Rótulo auxiliar (pie, encabezado de tabla, ayudas) | 10 pt | Regular / Bold |
| Eslogan de la marca | 9 pt | Regular (solo en el encabezado) |

Regla de legibilidad: **el cuerpo nunca baja de 11 pt y los rótulos auxiliares nunca de 10 pt** (excepción única: el eslogan del encabezado).

### 4.3 Espaciado, radios, sombras y movimiento

- **Espaciado** (cuadrícula de 4): `4, 8, 12, 16, 20, 24, 32`. Relleno interno de tarjeta: 20. Separación entre tarjetas: 16. Margen exterior del contenido: 24 (20 si la ventana mide menos de 1200 px).
- **Radios**: 8 (botones y campos) · 12 (fichas KPI, pestaña activa) · 16 (tarjetas) · 999 (píldoras y avatares).
- **Sombras**: tarjeta → desenfoque 24, desplazamiento (0, 4), color `#0A2045` al 10 %. Tarjeta interactiva al pasar el ratón → desenfoque 32, desplazamiento (0, 8), 16 %. Barra superior → desenfoque 16, 25 %. La sombra se aplica solo al contenedor de la tarjeta, no a sus hijos (rendimiento).
- **Movimiento**: 120 ms en hover; 200 ms al cambiar de pantalla (aparece con desvanecimiento y 8 px de subida); 350–450 ms en gráficos (curva `OutCubic`). Con la variable de entorno `PEA_SIN_ANIMACIONES=1` todo ocurre al instante (las pruebas y la autoprueba la activan).

### 4.4 Iconografía

Íconos SVG propios en `src/pea/gui/recursos/iconos/`, 24×24, trazo de 1,75 px, extremos redondeados, un solo color por ícono. Se cargan con `QtSvg`.

| Pestaña | Ícono | Color |
|---|---|---|
| Inicio | casa | `#5AA9E6` |
| Investigadores | persona | `#4B8FE2` |
| Grupos | tres personas | `#8FB3E8` |
| Productos | cajas apiladas | `#F0A030` |
| Análisis de redes | nodos conectados | `#9B7FE6` |
| Importar | flecha entrando a bandeja | `#35B57A` |
| Configuración | engranaje | `#9AA9BA` |

La marca de PEA-i es un átomo (órbitas y núcleo) en blanco, dibujado en `logo_pea.svg`.

## 5. Estructura de la ventana

```
┌ Barra de título nativa: «PEA-i · Programa Estadístico de Análisis de Investigación» ──────────┐
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│ BARRA SUPERIOR (88 px, degradado)                                                            │
│ [átomo] PEA-i   [Inicio][Investigadores][Grupos][Productos][Análisis de redes][Importar]      │
│        eslogan  [Configuración]                       (↶3) (avatar) [Cerrar sesión]          │
│                                                                    ⓘ Acerca de               │
│▔▔▔▔ filete institucional UPC de 3 px (verde oscuro · verde · verde claro) ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔│
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│ [Aviso de revisión: «La base de datos cambió en el servidor» + Recargar ahora]  (solo si aplica)│
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                              │
│  ZONA DE CONTENIDO (fondo #F1F5F9, desplazamiento vertical, margen 24)                       │
│   Cada pantalla = barra de contexto + tarjetas                                               │
│                                                                                              │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│ PIE INSTITUCIONAL (72 px, fondo #D4DAE3)                                                     │
│ [logo UPC] [PEA-i]  texto institucional (2 líneas)            ● Conectado · Revisión 142    │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
        Avisos breves (toasts) aparecen abajo a la derecha, encima del pie.
```

**Tamaños**: mínimo 1100 × 700; al abrir, 1360 × 820 limitado a la pantalla disponible y centrado.

### 5.1 Barra superior

- **Izquierda**: átomo blanco (44 px) + «PEA-i» (marca) + eslogan en dos líneas: «Programa Estadístico de Análisis / de Investigación» (nombre oficial del taller; vive en `pea.version` como `NOMBRE_COMPLETO` para cambiarlo en un solo lugar).
- **Centro**: siete pestañas, en este orden: **Inicio · Investigadores · Grupos · Productos · Análisis de redes · Importar · Configuración**. Cada una = ícono de 28 px sobre etiqueta de 11 pt.
  - Normal: etiqueta `TEXTO_SOBRE_OSCURO_SUAVE`.
  - Hover: fondo blanco al 8 %.
  - **Activa**: fondo blanco al 14 %, radio 12, etiqueta blanca en seminegrita y subrayado de 3 px en `ACENTO` (40 % del ancho de la pestaña) centrado en el borde inferior.
  - Foco de teclado: anillo de 2 px `#7CC7F0`.
- **Derecha**: botón **Deshacer** circular (40 px) con insignia numérica y un pequeño chevron que abre el historial; **avatar** de 44 px con iniciales; botón **«Cerrar sesión»** (contorno blanco 1 px, radio 10, ícono de salida); debajo, el enlace **«ⓘ Acerca de»** (10 pt). Si los datos son de demostración, una píldora ámbar «Datos de demostración» aparece junto al eslogan.
- **Filete institucional**: línea de 3 px en la base, tres tramos iguales con `UPC_VERDE_OSCURO`, `UPC_VERDE` y `UPC_VERDE_CLARO`.
- **Barra de título de Windows**: si el sistema es Windows se pide el modo oscuro inmersivo (`DWMWA_USE_IMMERSIVE_DARK_MODE`, vía `ctypes`, dentro de `try/except`) para que combine con el degradado. Si falla, no pasa nada.

**Historial de operaciones** (ADR-0013): al pulsar el chevron de Deshacer se abre un *popover* de solo lectura con las últimas operaciones (`EstadoAplicacion.historial_deshacer`), la más reciente arriba. Pulsar el botón principal deshace la última (`Ctrl+Z`).

### 5.2 Pie institucional

- **Izquierda**: logo de la UPC dentro de una pastilla blanca de 52×52 (radio 12) —el archivo original es opaco, se recorta a su contenido y se guarda como `recursos/logo_upc.png`— y, al lado, la marca de PEA-i en pequeño.
- **Centro** (10 pt, 2 líneas): «Universidad Popular del Cesar · Facultad de Ingenierías y Tecnológicas · Ingeniería de Sistemas» / «Taller 2 de Estructura de Datos · Datos de SCIENTI (Minciencias) · Modelo de Medición 2024 (M601PR04G01)».
- **Derecha**: estado vivo desde `ServicioAplicacion.estado()`: «● Conectado a Supabase · Revisión 142» (verde), «● Datos de demostración» (ámbar) o «● Sin conexión» (rojo), más dos chips: «Deshacer 3» y «Cola 0».
- Si la ventana mide menos de 760 px de alto, el pie se reduce a 44 px y muestra solo el estado.

### 5.3 Avisos

- **Toast**: tarjeta de 320 px, abajo a la derecha, 4 s, con ícono y color semántico. Reemplaza los `QMessageBox.information` de éxito.
- **Cuadros modales** solo para: confirmar eliminación en cascada, errores que exigen decisión y formularios de creación/edición.
- **Aviso de revisión**: franja bajo la barra superior (color `AVISO`) con el botón «Recargar ahora».

## 6. Pantallas

Todas comparten: **barra de contexto** (alto 56: título de pantalla a la izquierda; a la derecha el filtro de años y, si aplica, el menú «Exportar ▾»), tarjetas con título de 14 pt y barra de acento de 3 px `#1F7A9E` a su izquierda, y los estados de la sección 10.

**Filtro de años global**: es un único estado de la ventana (`FiltroAnios`) mostrado como chip «Ventana: Modelo 2024 ▾» en la barra de contexto de Inicio, Investigadores, Grupos y Productos. Al abrirlo muestra un popover con las cuatro opciones existentes (*Todos los años · Últimos N años · Rango específico · Modelo 2024*) y una explicación de una línea. Cambiarlo en una pantalla lo cambia en todas (mejora respecto a la versión anterior, donde cada pantalla tenía el suyo).

### 6.1 Inicio

Referencia: ![[ref-inicio.png]] y ![[ref-inicio-acabado.jpg]]

- **Propósito**: panorama estadístico de la institución o de un grupo (requisito 12.b del taller: histogramas y barras).
- **Barra de contexto**: selector segmentado **«Institución | Grupo ▾»**. En «Grupo» se elige uno con un combo. A la derecha: chip de ventana y menú **«Exportar ▾»** (tablas CSV · gráficos PNG).
- **Disposición (≥ 1360 px)**: cuatro columnas con proporción 11 : 13 : 12 : 13 y separación de 16.

| # | Tarjeta | Contenido | Servicio |
|---|---|---|---|
| 1 | **Ámbito** | Avatar circular de 112 px con anillo de 3 px `PRIMARIO`; título; líneas de datos; «Ver más detalles ⌄» (se despliega); cuadrícula 2×3 de fichas KPI | `resumen_general` / `vista_grupo` / `datos_grupo` |
| 2 | **Producción por año y tipología** | Barras apiladas (sección 9.1) | `serie_anual_por_categoria` (nuevo) |
| 3 | **Tipología de productos** | Dona de dos anillos (sección 9.2) | `productos_por_categoria`, `productos_por_validacion` |
| 4 | **Red de colaboración** | Vista previa del grafo + enlace «Abrir análisis completo →» | `red_coautoria` (nuevo) |

- **Menos de 1360 px**: rejilla 2×2 (1 y 2 arriba; 3 y 4 abajo).
- **Segunda fila** (dos tarjetas): «Investigadores más productivos» y «Grupos más productivos» (Top 5, con barra horizontal incrustada en cada fila) desde `top_investigadores` y `top_grupos`. En modo Grupo se convierten en «Integrantes con más productos» y «Últimos productos del grupo».

**Tarjeta de Ámbito, modo Institución**
- Avatar: logo UPC. Título «Universidad Popular del Cesar». Líneas: «Grupos de investigación: N».
- «Ver más detalles» muestra: grupos activos de total, investigadores activos de total, descripción de la ventana.
- Fichas KPI: **Grupos activos** · **Investigadores activos** · **Productos (ventana)** (con minigráfico de tendencia de 56×18 px) · **Promedio por investigador** · **Productos avalados** · **Productos históricos**.

**Tarjeta de Ámbito, modo Grupo**
- Avatar: anillo con las iniciales del grupo (degradado plateado como en el boceto). Título «Grupo de Investigación – {nombre}». Líneas: «Código: {codigo_gruplac}» y «Categoría: {categoria}».
- «Ver más detalles» muestra: líder, institución principal, área OCDE, ciudad, fecha de creación (los que existan; los vacíos no se muestran).
- Fichas KPI: **Integrantes** · **Estudiantes** (integrantes con rol «Estudiante») · **Productos (ventana)** · **Productos avalados** · **Promedio por integrante** · **Aporte a la institución** (%).

Esta misma tarjeta se reutiliza como **ficha lateral de la pantalla Grupos** (componente `FichaGrupo`).

### 6.2 Investigadores

Referencia: ![[ref-investigadores.png]]

- **Disposición**: tarjeta «Directorio de investigadores» (flexible) + ficha lateral de 360 px.
- **Cabecera del directorio**: título, búsqueda («Buscar investigador…», `Ctrl+F`), combo **Grupo**, combo **Categoría**, combo **Estado** (Activos / Todos) y botón primario **«+ Nuevo investigador»**.
- **Tabla** (filas de 48 px, sin cebra, hover `#F3F7FB`, selección `#E3EEF7` con barra de 3 px `ACENTO` a la izquierda, encabezado `FICHA` en 10 pt negrita):
  `Nombre` (avatar de iniciales de 28 px + nombre en negrita) · `Grupo(s)` · `Categoría` (píldora) · `Formación` · `Productos` (alineado a la derecha) · `Código CvLAC` (color `ENLACE`; clic copia al portapapeles con toast).
  Ordenable por columna (`QSortFilterProxyModel`). Pie de tabla: «Mostrando 5 de 12».
  Los investigadores inactivos se ven al 60 % de opacidad con píldora «Inactivo».
- **Ficha lateral**: avatar de 96 px con degradado y iniciales; nombre (16 pt negrita); línea «GRUPO · Categoría»; fichas KPI 2×2: **Productos** (ventana) · **Grupos** (membresías) · **Coautores** (grado en la red) · **Años con producción**; minigráfico «Producción anual»; barras «Tipología». Botones: **Editar** · **Activar/Desactivar** · **Eliminar…** (confirma mostrando la cascada de `describir_cascada`) · **Ver ficha completa** (diálogo amplio con las tablas *Aporte a grupos*, *Membresías* y *Productos*, que son las pestañas de la versión anterior) · **Ver productos** (abre Productos con la búsqueda puesta en su nombre).
- **Servicios**: `tabla_investigadores`, `vista_investigador`, `datos_investigador`, `crear_/actualizar_investigador`, `cambiar_estado`, `eliminar`, `describir_cascada`, `red_coautoria` (para Coautores).

### 6.3 Grupos

Sin boceto propio: usa el patrón de Investigadores con la tarjeta de grupo de Inicio.

- **Cabecera**: título «Directorio de grupos», búsqueda, combo **Categoría** (A1, A, B, C, Reconocido, Sin clasificar), combo **Estado**, botón primario **«+ Nuevo grupo»**.
- **Tabla**: `Nombre` (avatar de iniciales + nombre) · `Código GrupLAC` · `Categoría` (píldora) · `Líder` · `Integrantes` · `Productos` · `Estado`.
- **Ficha lateral** (`FichaGrupo`): la misma tarjeta de Ámbito de Inicio en modo Grupo, más minigráfico de barras apiladas y los botones **Editar · Activar/Desactivar · Eliminar… · Ver ficha completa** (diálogo con *Integrantes y coautores* y *Productos enlazados*).
- **Servicios**: `tabla_grupos`, `vista_grupo`, `datos_grupo`, `crear_/actualizar_grupo`, `cambiar_estado`, `eliminar`, `describir_cascada`.

### 6.4 Productos

- **Cabecera**: título «Catálogo de productos», búsqueda («Buscar por título, código o autor…»), combo **Tipología** (GNC · DTI · ASC · FRH, con su nombre completo en la lista), combo **Validación**, combo **Estado**, botón primario **«+ Nuevo producto»**.
- **Tabla**: `Código` · `Título` (máximo 2 líneas, elipsis) · `Tipología` (píldora con color de dato) · `Subtipo` · `Año` · `Validación` (píldora) · `Grupo` · `Autores` (primer autor + «+2»).
- **Ficha lateral** (360 px): título, código, píldoras de tipología y validación, año, grupo, lista de coautores (avatar + nombre; clic abre su ficha en Investigadores) y la insignia **«✔ Dentro de la ventana del Modelo 2024» / «✖ Fuera de la ventana…»** con explicación en el *tooltip* (5 años para artículos, software, ASC y FRH; 10 para libros y patentes). Botones: **Editar** · **Activar/Desactivar** · **Eliminar**.
- **Servicios**: `tabla_productos`, `detalle_producto`, `crear_producto`, `cambiar_estado`, `eliminar`, y **`actualizar_producto` (nuevo, hoy no existe)** para el botón Editar.

### 6.5 Análisis de redes

Referencia: ![[ref-red-coautorias.png]]. Detalle técnico en [[ADR-0015-Analisis-de-red-nativo]].

- **Disposición**: tarjeta «Análisis de red de colaboración» (flexible) + panel «Métricas de centralidad» de 340 px.
- **Barra de la tarjeta**: combo **«Todos los grupos»**, selector **«Mín. coautorías: 2»** (paso 1), búsqueda «Buscar investigador…», botón **«Reordenar»** y controles de zoom (+, −, ajustar).
- **Lienzo** (`QGraphicsView`, fondo blanco con cuadrícula de puntos muy tenue):
  - Nodo = investigador. Radio = `8 + 2,5·√grado`. Color = categoría (sección 4.1).
  - Arista = productos compartidos. Grosor = `1 + log2(peso)` (máx. 4 px), color `#9DB5C9`.
  - Etiqueta (10 pt, «J. Apellido») visible si el zoom ≥ 0,8, o si el nodo está entre los 10 de mayor grado, o al pasar el ratón.
  - **Hover**: resalta el nodo y sus vecinos; el resto baja al 25 %. **Clic**: selecciona (anillo de 3 px `ACENTO`) y llena el panel. **Doble clic**: abre su ficha en Investigadores.
  - Rueda = zoom; arrastrar = mover el lienzo; arrastrar un nodo lo fija.
  - Leyenda abajo a la izquierda: categorías y «Tamaño = coautores · Grosor = productos compartidos».
- **Panel de métricas**: fichas **Grado de conexión** («14 coautores») · **Intermediación** («0,084») · **Grupo principal** · **Categoría** · **Productos compartidos**. Sin selección: texto «Selecciona un nodo para ver su posición en la red.» y la lista **«Más conectados»** (5, clicables). Al fondo, tarjeta «Resumen de la red»: investigadores, vínculos y densidad.
- **Rendimiento**: la disposición por fuerzas corre en `EjecutorAsincrono` con semilla fija (resultado repetible); más de 400 nodos → se muestran los 400 de mayor grado con aviso.
- **Servicios**: `red_coautoria(filtro, codigo_grupo, min_coautorias)` (nuevo) que devuelve nodos, aristas y métricas calculadas en memoria desde la [[Multilista]]. Al filtrar por un grupo específico, la red incluye tanto a los integrantes del grupo como a los coautores externos que participaron en productos del grupo (diferenciando su vinculación).

### 6.6 Importar

- **Disposición**: arriba, tres tarjetas de fuente en fila (**CSV**, **PDF**, **URL de SCIENTI**); abajo, la tarjeta «Cola de importación».
- **Tarjetas de fuente**: ícono, título, descripción de una línea, campo o zona para **arrastrar y soltar** (CSV y PDF), y botón primario «Encolar». El de CSV conserva el combo de tipo (Detección automática · Grupos · Investigadores · Productos · Autores / Relaciones).
- **Cola**: encabezado «Tareas pendientes: N» con **«Procesar siguiente»** (primario) y **«Procesar todas»**; tabla con **píldora de estado** (Pendiente · En proceso · Completada · Falló). Mientras procesa: barra de progreso indeterminada y botones deshabilitados; al terminar, toast con el resumen (grupos, investigadores, productos).
- **Servicios**: `encolar_csv`, `encolar_pdf`, `encolar_url`, `procesar_siguiente_tarea`, `tareas_pendientes`, `tabla_cola`.

### 6.7 Configuración

Selector segmentado con dos secciones:

1. **Conexión**: tarjeta de estado grande (círculo de color + modo + servidor + usuario + revisión local/remota + motivo de bloqueo) y formulario (URL de Supabase, clave publicable, correo, contraseña, casilla de la variable `PEA_USUARIO_CLAVE`). Botones: **«Conectar con Supabase»** (primario), **«Cargar datos de demostración»**, **«Desconectar»**. Es la misma funcionalidad de la antigua pantalla *Conectar*.
2. **Verificación cruzada**: la funcionalidad de la antigua pantalla *Verificación cruzada Python / C++* (tabla de pasos con píldoras «Coinciden / Difieren» y dos visores de salida lado a lado en fuente monoespaciada).

### 6.8 Acerca de

Se abre con el enlace «ⓘ Acerca de» (no es una pestaña). Tarjeta institucional (logo UPC, universidad, facultad, programa, asignatura), tarjeta del software, ficha técnica (arquitectura en capas, estructuras, base de datos, entorno de ejecución) e integrantes del grupo. Mantiene el contenido actual con el nuevo estilo. Botón «← Volver».

### 6.9 Sesión y primer arranque

- Al abrir sin conexión ni datos, **Inicio** muestra un estado vacío con dos botones: **«Conectar con Supabase»** (lleva a Configuración › Conexión) y **«Cargar datos de demostración»**.
- El avatar muestra las iniciales del correo conectado, «DM» en modo demostración y «—» sin sesión.
- **«Cerrar sesión»** pide confirmación, llama a `desconectar()` y vuelve a Inicio vacío.

## 7. Del boceto a los datos reales

El boceto muestra información que PEA-i no tiene. Esta tabla fija con qué se reemplaza cada elemento, para que nadie invente campos (regla de [[ADR-0016-Alcance-de-pantallas-y-datos-del-boceto]]).

| En el boceto | ¿Existe en PEA-i? | Se muestra en su lugar |
|---|---|---|
| Pestañas **Semilleros** y **Centros** | No (ni en el dominio ni en el taller) | No se incluyen |
| Pestaña **Proyectos** | Existe la entidad `Proyecto` y su tabla, pero sin servicio ni vista | Fuera de este rediseño; opcional más adelante (prompt P-UI-13) |
| Pestaña **Configuración** y **Cerrar sesión** | Sí (conexión Supabase y `desconectar()`) | Se mantienen |
| Pestañas nuevas **Importar** | Sí (requisito 7 del taller) | Se añade en lugar de Semilleros |
| «Total Semilleristas» | No | **Estudiantes** (integrantes con rol «Estudiante») |
| «Proyectos Activos» | No | **Productos (ventana)** |
| «Productos Reportados» | Duplicaba «Productos Totales» | **Productos avalados** |
| «H-Index Promedio», «H-Index» | No | **Promedio por integrante** / **Años con producción** |
| Columna **ORCID** | No | **Código CvLAC (RH)** |
| «Proyectos» en la ficha del investigador | No | **Grupos** (membresías) |
| Gráfico «Participación en proyectos» (Proyectos, Convocatorias, Financiados…) | No | **Producción por año y tipología** (GNC, DTI, ASC, FRH) |
| Dona «Productos por tipología» (anillo doble) | Sí, con otros datos | Anillo externo = tipología; interno = estado de validación |
| «Todas las Facultades» (red) | No hay facultades | **Todos los grupos** |
| «Clúster temático: Inteligencia Artificial» | No hay temas | **Grupo principal** y **Categoría** |
| Acrónimo del grupo | No hay campo | **Categoría** |
| Logos y texto legal de *Let Me Know* / SIGIIP del pie | Son de un tercero | Identidad de la UPC (sección 5.2) |
| Eslogan «Plataforma de Gestión y Análisis de Investigación – CTeI» | El taller dice «Programa Estadístico de Análisis de Investigación» | Nombre oficial del taller (configurable en `NOMBRE_COMPLETO`) |
| Conexión «Supabase backend» | Sí | Estado vivo en el pie |

### 7.1 Qué pasó con las nueve pantallas anteriores

| Pantalla anterior | Dónde queda |
|---|---|
| Conectar con PEA-i | Configuración › Conexión |
| Resumen general | **Inicio** |
| Por grupo | **Grupos** (ficha) y **Inicio** en modo Grupo |
| Por investigador | **Investigadores** (ficha) |
| Por producto | **Productos** |
| Gestión de datos (altas, bajas, cambios, deshacer) | Integrada en cada directorio (botón «+ Nuevo…» y botones de la ficha); Deshacer en la barra superior |
| Importar | **Importar** |
| Verificación cruzada | Configuración › Verificación cruzada |
| Acerca del proyecto | «ⓘ Acerca de» |

### 7.2 Textos de interfaz que no pueden variar

Pestañas: «Inicio», «Investigadores», «Grupos», «Productos», «Análisis de redes», «Importar», «Configuración». Acciones: «Cerrar sesión», «Deshacer», «Recargar», «Exportar», «+ Nuevo investigador / grupo / producto», «Editar», «Activar / Desactivar», «Eliminar…», «Ver ficha completa», «Conectar con Supabase», «Cargar datos de demostración». Estados vacíos: «Sin datos en esta ventana». Todo en español; está prohibido en pantalla: *Dashboard, Summary, Undo, Redo, Refresh, Settings, Login, Logout*.

Números con formato colombiano (`QLocale(Spanish, Colombia)`): miles con punto («1.234»), decimales con coma («0,084») y porcentajes con espacio fino («41,3 %»). Todo pasa por `pea/gui/formato.py`; no se usan f-strings con `.1f` para mostrar cifras.

## 8. Componentes reutilizables

Carpeta `src/pea/gui/componentes/`. Cada uno tiene `objectName` propio para la hoja de estilo y para las pruebas.

| Componente | Archivo | Qué hace |
|---|---|---|
| `Tarjeta` | `tarjeta.py` | Contenedor blanco, radio 16, sombra, título opcional con barra de acento y zona de acciones a la derecha |
| `FichaKPI` | `tarjeta_kpi.py` | Rótulo (10 pt) + valor (22 pt) sobre fondo `FICHA`; minigráfico opcional; método `actualizar(valor, subtitulo)` |
| `Pildora` | `pildora.py` | Etiqueta redondeada con color semántico o de dato (categoría, tipología, validación, estado) |
| `Avatar` | `avatar.py` | Círculo con iniciales y degradado derivado del nombre (estable); variante con anillo y variante con logo |
| `CampoBusqueda` | `campo_busqueda.py` | Campo con lupa, botón de limpiar y retardo de 250 ms antes de emitir |
| `SelectorSegmentado` | `selector_segmentado.py` | Pastillas excluyentes («Institución | Grupo», secciones de Configuración) |
| `ChipVentana` + popover | `filtro_anios.py` | Reemplaza a la barra de filtro de años; emite `FiltroAnios` |
| `EstadoVacio` | `estado_vacio.py` | Ilustración sencilla, texto y hasta dos botones |
| `Esqueleto` | `estado_vacio.py` | Bloques grises animados mientras carga |
| `Toast` / `GestorAvisos` | `toast.py` | Avisos breves apilables |
| `TablaEstilizada` y delegados | `tabla.py` | `QTableView` con filas de 48 px, `PildoraDelegate`, `AvatarNombreDelegate`, `EnlaceDelegate`, `NumeroDelegate` |
| `FichaLateral` | `ficha_lateral.py` | Base de las fichas de 360 px (cabecera, KPI, acciones) |
| `PopoverHistorial` | `popover_historial.py` | Lista de operaciones deshacibles |
| `animacion.py` | | Ayudas de animación que respetan `PEA_SIN_ANIMACIONES` |

Los diálogos de creación y edición (`DialogoGrupo`, `DialogoInvestigador`, `DialogoProducto`, y el nuevo de edición de producto) se mueven a `src/pea/gui/dialogos.py`, con el mismo estilo (radio 16, botones primario y secundario, errores de validación bajo cada campo en `ERROR`).

## 9. Gráficos (QPainter, sin dependencias externas)

Carpeta `src/pea/gui/componentes/graficos/`. Todos heredan de `GraficoBase`, que ya sabe **exportar a PNG** (el doble de resolución, fondo blanco, con título) y **dibujar el estado vacío**.

### 9.1 `GraficoBarrasApiladas`
- Datos: `dict[int, dict[str, int]]` (año → tipología → conteo). Apilado de abajo hacia arriba: GNC, DTI, ASC, FRH.
- Eje Y con 4–5 líneas punteadas `#E2E8F0` y máximo «redondo» (5, 10, 25, 50…); etiquetas de 10 pt `TEXTO_SECUNDARIO`.
- Barra: ancho `min(36, 55 % del paso)`, borde blanco de 1,5 px entre segmentos, esquinas superiores de 4 px solo en el segmento más alto. **Total** sobre cada barra (10 pt negrita).
- Leyenda inferior en dos columnas con el nombre completo (tooltip) y la sigla. **Clic en la leyenda** atenúa o restaura una serie.
- **Hover**: tooltip oscuro (`#0A2045`, radio 8, texto blanco): «2021 · 21 productos» y una línea por tipología.
- Animación de crecimiento 400 ms, con desfase de 30 ms por barra.
- Botón «Ver como tabla» alterna a una tabla año × tipología (accesible y útil para copiar).

### 9.2 `GraficoDonaDoble`
- Anillo externo = tipología (grosor 22 % del radio); anillo interno = validación (grosor 18 %), con 4 % de separación entre ambos.
- Inicio a las 12 en punto, sentido horario, orden canónico (no por tamaño) para que no «salte» al filtrar. Hueco angular de 1° entre segmentos.
- **Centro**: total (22 pt negrita) y «productos» (10 pt). Al pasar el ratón sobre un segmento, el centro muestra su nombre, cantidad y porcentaje, y el segmento sobresale 4 px.
- Leyenda debajo en dos columnas, «Tipología» y «Validación», con líneas «GNC · 62 (41,3 %)».

### 9.3 `GraficoSerieAnual`
Barras simples en `#1F7A9E` con valor encima, para las fichas de grupo e investigador. Sin línea de tendencia (ruido).

### 9.4 `Minigrafico`
Línea de 56×18 px sin ejes, para la ficha KPI de productos.

### 9.5 `MiniRed`
Vista previa estática del grafo (los 18 nodos de mayor grado), sin etiquetas salvo los 6 primeros; al pasar el ratón muestra el nombre. Pulsar abre Análisis de redes.

**Estado vacío de cualquier gráfico**: ícono tenue, «Sin datos en esta ventana» y la sugerencia «Prueba con “Todos los años”».

## 10. Estados de la interfaz

| Estado | Cómo se ve |
|---|---|
| **Vacío** (sin datos) | `EstadoVacio` con botones «Conectar con Supabase» y «Cargar datos de demostración» |
| **Cargando** (más de 150 ms) | `Esqueleto` en el lugar de tarjetas y tablas; nunca se congela la ventana |
| **Error** | Tarjeta `ERROR` con mensaje en español y botón «Reintentar» |
| **Sin conexión** | Franja ámbar bajo la barra superior; botones de escritura deshabilitados con *tooltip* del `motivo_bloqueo`; los datos mostrados no se presentan como actuales |
| **Cambio remoto** | Aviso de revisión con «Recargar ahora» |
| **Demostración** | Píldora ámbar «Datos de demostración» permanente en la barra superior y en el pie |
| **Procesando** (importación, verificación) | Botones deshabilitados y barra de progreso indeterminada |

## 11. Adaptación al tamaño de la ventana

| Ancho | Barra superior | Inicio | Directorios |
|---|---|---|---|
| ≥ 1360 | Completa | 4 columnas | Tabla + ficha de 360 px |
| 1240 – 1359 | Completa | Rejilla 2×2 | Tabla + ficha de 340 px |
| 1120 – 1239 | Sin eslogan; pestañas de 88 px | Rejilla 2×2 | Ficha debajo de la tabla si no cabe |
| 1100 – 1119 | Sin eslogan; pestañas solo con ícono y *tooltip* | Rejilla 2×2 | Ficha debajo de la tabla |

Se verifica con la autoprueba en tres tamaños: **1100×700**, **1366×768** y **1920×1080**.

## 12. Interacción y atajos

`Ctrl+1…7` cambia de pestaña · `Ctrl+Z` deshacer · `Ctrl+F` enfoca la búsqueda de la pantalla · `F5` recargar datos · `Ctrl+S` exporta a CSV la tabla visible · `Enter` abre la ficha completa de la fila · `Esc` cierra popovers y diálogos · `Alt+←` vuelve desde «Acerca de».

## 13. Accesibilidad

- Contraste de texto ≥ 4,5:1 (tabla de la sección 4.1).
- Foco visible en todo control (anillo de 2 px) y orden de tabulación lógico: barra superior → contexto → filtros → tabla → ficha.
- Cada control con `setAccessibleName`; los íconos sin texto llevan *tooltip*.
- Ningún dato se transmite solo por color (sección 4.1).
- Respeta la escala de pantalla del sistema (HiDPI) y el modo `PEA_SIN_ANIMACIONES`.

## 14. Implementación

Decisión tecnológica en [[ADR-0017-Tecnologia-de-interfaz-Qt-Widgets]]: **Qt Widgets + hoja de estilo (QSS) + QPainter + QtSvg**. No se usa QML, ni `QtWebEngine`, ni `matplotlib`.

```
src/pea/gui/
├── __init__.py              # main(): arranque, --autoprueba
├── __main__.py
├── estilo.py                # TOKENS, HOJA_ESTILO, fuente_base()
├── formato.py               # números, porcentajes, nombres de tipología, iniciales
├── ejecutor.py              # (ya existe) hilos
├── dialogos.py              # formularios de grupo, investigador, producto
├── ventana_principal.py     # barra superior, pestañas, pie, atajos, Pantalla(IntEnum)
├── recursos/
│   ├── logo_pea.svg
│   ├── logo_upc.png         # recortado desde docs/entrada/identidad/logo_upc.png
│   └── iconos/*.svg
├── componentes/
│   ├── tarjeta.py, tarjeta_kpi.py, pildora.py, avatar.py, campo_busqueda.py,
│   ├── selector_segmentado.py, filtro_anios.py, estado_vacio.py, toast.py,
│   ├── tabla.py, modelo_tabla.py, ficha_lateral.py, popover_historial.py, animacion.py
│   └── graficos/ (base.py, barras_apiladas.py, dona_doble.py, serie_anual.py, minigrafico.py, mini_red.py)
├── red/
│   ├── vista_red.py         # QGraphicsView
│   ├── nodo.py, arista.py
│   └── disposicion.py       # fuerzas (Hooke + Coulomb), semilla fija
└── pantallas/
    ├── inicio.py, investigadores.py, grupos.py, productos.py,
    ├── redes.py, importar.py, configuracion.py, acerca.py
```

**API pública estable** (las pruebas dependen de ella):
- `VentanaPrincipal.seleccionar_pantalla(Pantalla)`; `Pantalla` es un `IntEnum`: `INICIO=0, INVESTIGADORES=1, GRUPOS=2, PRODUCTOS=3, REDES=4, IMPORTAR=5, CONFIGURACION=6, ACERCA=7`.
- Atributos: `_pestanas` (grupo de botones de la barra), `_apilador` (`QStackedWidget`), `_btn_deshacer`, `_pie`.
- Cada pantalla expone `refrescar()` (como hasta ahora) y `establecer_filtro(FiltroAnios)`.

**Reglas técnicas**
- La interfaz solo llama a `ServicioAplicacion` (ni estructuras, ni red, ni SQL).
- Red, ingesta y verificación cruzada corren fuera del hilo principal con `EjecutorAsincrono`.
- Cada archivo nuevo con anotaciones de tipo y `ruff` sin errores.
- Sombras (`QGraphicsDropShadowEffect`) solo en tarjetas contenedoras, nunca en filas ni en celdas.

## 15. Criterios de aceptación

- [ ] Cada pantalla se parece a su referencia (sección 2) en **estructura, orden y proporciones**, y se ve igual de pulida o más que ![[ref-inicio-acabado.jpg]].
- [ ] No queda ninguna cifra, nombre ni logo de los bocetos en pantalla.
- [ ] Los siete textos de pestaña y los textos de la sección 7.2 coinciden exactamente.
- [ ] Todo color, tamaño y radio sale de `estilo.py`.
- [ ] Contraste ≥ 4,5:1 en todo texto; foco visible; cero textos en inglés.
- [ ] Con 1100×700, 1366×768 y 1920×1080 no hay recortes ni desbordes.
- [ ] La ventana nunca se congela (importar, conectar y la red usan hilos).
- [ ] `ruff check` sin errores y `pytest tests/unit` en verde (con las pruebas de interfaz actualizadas a esta estructura).
- [ ] La autoprueba (`python -m pea.gui --autoprueba`) guarda capturas `datos/capturas/oficiales/pantalla_<nn>_<nombre>_<ancho>x<alto>.png` de cada pantalla en los tres tamaños.
- [ ] Comparación lado a lado con las referencias hecha y anotada en la bitácora.

## 16. Pendiente para C++ (no se toca aquí)

La interfaz de C++ **sigue con su diseño original** y se rehará con prompts aparte. Lo que deberá igualar está en [[GUI-paridad]]. Los servicios nuevos creados para esta interfaz (`serie_anual_por_categoria`, `red_coautoria`, `actualizar_producto`) quedan registrados allí como deuda de paridad funcional con C++.

## Decisiones relacionadas
- [[ADR-0012-Diseno-GUI-y-navegacion]]
- [[ADR-0013-Vistas-secundarias]]
- [[ADR-0015-Analisis-de-red-nativo]]
- [[ADR-0016-Alcance-de-pantallas-y-datos-del-boceto]]
- [[ADR-0017-Tecnologia-de-interfaz-Qt-Widgets]]

## Riesgos y casos borde
- **Sombras y rendimiento**: muchas sombras sobre widgets con gráficos pesados pueden bajar los cuadros por segundo; por eso solo se aplican a las tarjetas contenedoras.
- **Fuentes**: si Segoe UI no existe (Linux/macOS) se cae a Inter o Noto Sans; las medidas deben tolerar ±8 % de ancho de texto.
- **Redes grandes**: más de 400 nodos se recortan a los de mayor grado con aviso visible.
- **Logo UPC opaco**: el archivo original tiene fondo blanco; por eso va en pastilla blanca y se usa una copia recortada, sin modificar el original.
- **Edición de productos**: depende del servicio nuevo `actualizar_producto`; hasta entonces el botón «Editar» del producto queda deshabilitado con *tooltip*.
