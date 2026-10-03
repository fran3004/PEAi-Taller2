---
tipo: nota-de-diseno
estado: revisado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[_Indice]]"
  - "[[Arquitectura]]"
  - "[[ADR-0012-Diseno-GUI-y-navegacion]]"
  - "[[ADR-0013-Vistas-secundarias]]"
  - "[[ADR-0015-Analisis-de-red-nativo]]"
  - "[[SPEC]]"
origen: "brain/50-Bitacora/AUDITORIA-DISENO-PEAI.md - Fase 9"
---

# Especificación UX/UI y Paridad Visual de Interfaz Gráfica

## 1. Identidad Visual y Principios Generales

Tanto la aplicación en **Python (PySide6)** como en **C++ (Qt 6 Widgets)** comparten la misma disposición espacial, paleta de colores y componentes visuales, brindando una experiencia indistinguible para el usuario final.

> [!IMPORTANT] Prohibición de Términos en Inglés en la Interfaz
> La totalidad de la interfaz de usuario se expresa en español correcto:
> - *Dashboard* $\rightarrow$ **Panel Principal** o **Panel**
> - *Summary* $\rightarrow$ **Resumen**
> - *Undo / Redo* $\rightarrow$ **Deshacer / Rehacer**
> - *Refresh* $\rightarrow$ **Recargar**
> - *Settings* $\rightarrow$ **Configuración**

### Paleta de Colores Institucional
- **Azul Primario UPC**: `#003366` (Barra superior y encabezados).
- **Azul Acento**: `#0D47A1` (Botones de acción principal y pestañas activas).
- **Fondo General**: `#F5F7FA` (Gris suave neutro de alto contraste).
- **Fondo de Contenedores**: `#FFFFFF` (Blanco puro para tarjetas y tablas).
- **Texto Principal**: `#1A1A1A` / Texto Secundario: `#5F6368`.
- **Estados Semánticos**:
  - Éxito / Vigente: `#2E7D32` (Verde).
  - Advertencia / En Revisión: `#ED6C02` (Naranja).
  - Error / Inactivo: `#D32F2F` (Rojo).

## 2. Estructura y Distribución de la Ventana Principal

La interfaz se organiza en cuatro zonas ergonómicas principales:

```
+-----------------------------------------------------------------------------------+
|  [Logo UPC]  PEA-i: Programa Estadístico de Análisis de Investigación   [Conectado]  | (Barra Superior)
+-----------------------------------------------------------------------------------+
|  [ Tarjeta: 12 Grupos ]  [ Tarjeta: 85 Inv ]  [ Tarjeta: 420 Prod ]  [ KPI: 89.4 ] | (Tarjetas KPI)
+-----------------------------------------------------------------------------------+
|  (Panel Izquierdo)     |  (Panel Central)                 |  (Panel Derecho)      |
|  Árbol de Navegación   |  Tabla Detallada de Entidades    |  Ficha de Detalle y   |
|  - Grupos              |  [Buscador / Filtros por Año]    |  Estadísticas OLAP    |
|    └─ Investigadores   |  | Código | Título | Tipo | Año | |  del Hipercubo        |
|  - Red de Coautoría    |  | ...    | ...    | ...  | ... | |  [Gráfica Nativa]   |
+-----------------------------------------------------------------------------------+
|  Estado: Sincronizado | Revisión: 142 | Deshacer: Ctrl+Z | Tareas en cola: 0      | (Barra de Estado)
+-----------------------------------------------------------------------------------+
```

### 2.1. Barra Superior Institucional
- Logotipo de la Universidad Popular del Cesar cargado desde `docs/entrada/identidad/logo_upc.png`.
- Título institucional: `PEA-i · Universidad Popular del Cesar`.
- Indicador de estado de conexión: círculo verde (`Sincronizado`) o ámbar (`Sin conexión`).
- Botón de cambio de modo (Producción / Datos de Prueba con aviso visual destacado en amarillo).

### 2.2. Tarjetas KPI Superiores
Cuatro tarjetas rectangulares con sombra sutil y tipografía legible que muestran métricas directas calculadas desde el [[Hipercubo]]:
1. **Total Grupos de Investigación**: Conteo activo.
2. **Total Investigadores**: Clasificados (Senior, Asociado, Junior).
3. **Total Productos**: Distribución por categoría.
4. **Índice Global de Productividad**: Promedio ponderado por investigador.

### 2.3. Zona Central con Paneles Divisibles (*QSplitter*)
- **Panel Izquierdo (Navegación)**: `QTreeView` que lista las instituciones, grupos e investigadores afiliados. Permite filtrar y seleccionar un nodo para acotar la visualización global. Pestaña alternativa con el acceso al visualizador de red.
- **Panel Central (Tabla de Contenido)**: `QTableView` con paginación local y ordenamiento multicolumna de productos, proyectos o miembros según la selección del árbol.
- **Panel Derecho (Detalle y OLAP)**: Pestañas con:
  - Ficha de datos completos de la entidad seleccionada.
  - Subcubo OLAP y gráficos estadísticos generados mediante renderizado nativo (`QPainter` / `matplotlib` embebido en PySide6).

### 2.4. Barra de Estado Inferior
- Muestra el ID de revisión de la base de datos (`meta.revision`).
- Cantidad de operaciones en la [[Pila-deshacer]].
- Elementos pendientes en la [[Cola-importacion]].

## 3. Visualizador de Red de Coautoría Nativo

Conforme a [[ADR-0015-Analisis-de-red-nativo]], el análisis de relaciones y coautorías entre investigadores y grupos se renderiza **de forma nativa sin navegadores web incrustados**:
- Implementado mediante `QGraphicsView` y `QGraphicsScene`.
- Nodos circulares representando investigadores (color según categoría Minciencias).
- Aristas entre nodos representando productos compartidos (grosor proporcional al número de publicaciones conjuntas).
- Algoritmo de posicionamiento basado en fuerzas (fuerza elástica de Hooke y repulsión de Coulomb) ejecutado en un hilo secundario sin congelar la interfaz.
- Interacción completa: zoom con la rueda del ratón, paneo por arrastre y selección de nodo para abrir su ficha técnica.
