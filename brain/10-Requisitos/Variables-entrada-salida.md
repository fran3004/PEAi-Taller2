---
tipo: requisito
estado: aprobado
creado: 2026-10-02
actualizado: 2026-10-02
relacionado:
  - "[[SPEC]]"
  - "[[Glosario]]"
  - "[[Modelo-Grupos]]"
  - "[[Modelo-Investigadores]]"
  - "[[Modelo-Productos]]"
  - "[[SCIENTI-Mapa-de-campos]]"
  - "[[00-Inicio]]"
origen: "Modelo Minciencias 2024 y Extracción SCIENTI (GrupLAC/CvLAC)"
---

# Variables de Entrada y Salida del Sistema · PEA-i

Este documento formaliza el diccionario de datos de todas las entidades, atributos, variables de entrada y métricas de salida del sistema PEA-i, garantizando la trazabilidad estricta hacia el **Modelo Minciencias 2024** y las fuentes extraídas de **SCIENTI**.

---

## 1. Entidad Grupo de Investigación (`Grupo`)

| Variable | Tipo de Dato | Req. | E/S | Fuente y Cita | Descripción |
|---|---|---|---|---|---|
| `codigo_gruplac` | Texto (14-20) | Sí | E/S | [[SCIENTI-Mapa-de-campos#1. Entidad Grupo de Investigación]] | Código único institucional en la plataforma GrupLAC (ej. `0000000002099`). Clave primaria natural. |
| `nombre` | Texto (255) | Sí | E/S | [[SCIENTI-Mapa-de-campos#1. Entidad Grupo de Investigación]] | Nombre formal registrado del grupo de investigación. |
| `fecha_creacion` | Fecha (AAAA-MM) | Sí | E/S | [[SCIENTI-Mapa-de-campos#1. Entidad Grupo de Investigación]] | Año y mes de constitución oficial del grupo. |
| `pais` | Texto (50) | Sí | E/S | [[SCIENTI-Mapa-de-campos#1. Entidad Grupo de Investigación]] | País de ubicación principal (por defecto Colombia). |
| `departamento_ciudad` | Texto (100) | Sí | E/S | [[SCIENTI-Mapa-de-campos#1. Entidad Grupo de Investigación]] | Departamento y ciudad o municipio de sede principal. |
| `lider` | Texto (255) | Sí | E/S | [[SCIENTI-Mapa-de-campos#1. Entidad Grupo de Investigación]] | Nombre completo del investigador principal responsable del grupo. |
| `institucion_principal` | Texto (255) | Sí | E/S | [[SCIENTI-Mapa-de-campos#1. Entidad Grupo de Investigación]] | Nombre de la entidad o universidad que avala al grupo. |
| `gran_area_ocde` | Texto (100) | Sí | E/S | [[Modelo-Areas-OCDE#1. Las 6 Grandes Áreas del Conocimiento]] | Una de las 6 grandes áreas OCDE (ej. "Ingeniería y Tecnología"). |
| `area_ocde` | Texto (100) | Sí | E/S | [[Modelo-Areas-OCDE#2. Desglose de las 42 Subáreas del Conocimiento]] | Subárea específica OCDE de focalización investigativa. |
| `categoria` | Enumeración | Sí | E/S | [[Modelo-Grupos#Categorías de Grupos de Investigación]] | Clasificación Minciencias: `A1`, `A`, `B`, `C` o `Reconocido`. |
| `activo` | Booleano | Sí | E/S | `[SUPUESTO]` Control de borrado lógico | Indica si el grupo se encuentra activo (`true`) o desactivado (`false`) en el sistema. |

---

## 2. Entidad Investigador (`Investigador`)

| Variable | Tipo de Dato | Req. | E/S | Fuente y Cita | Descripción |
|---|---|---|---|---|---|
| `codigo_rh` | Texto (10-15) | Sí | E/S | [[SCIENTI-Mapa-de-campos#2. Entidad Investigador]] | Identificador único de currículo en CvLAC (ej. `0000494917`). Clave primaria. |
| `nombre_completo` | Texto (255) | Sí | E/S | [[SCIENTI-Mapa-de-campos#2. Entidad Investigador]] | Nombres y apellidos completos del investigador. |
| `nombre_en_citas` | Texto (255) | No | E/S | [[SCIENTI-Mapa-de-campos#2. Entidad Investigador]] | Variante bibliográfica de firma estandarizada en publicaciones. |
| `nacionalidad` | Texto (50) | Sí | E/S | [[SCIENTI-Mapa-de-campos#2. Entidad Investigador]] | País de nacionalidad del investigador. |
| `sexo` | Texto (20) | Sí | E/S | [[SCIENTI-Mapa-de-campos#2. Entidad Investigador]] | Sexo reportado en su hoja de vida oficial. |
| `categoria` | Enumeración | Sí | E/S | [[Modelo-Investigadores#Categorías de investigadores]] | Categoría oficial: `Investigador Emérito`, `Investigador Senior`, `Investigador Asociado`, `Investigador Junior` o `Sin categoría / Vinculado`. |
| `formacion_academica` | Texto (100) | Sí | E/S | [[SCIENTI-Mapa-de-campos#2. Entidad Investigador]] | Máximo nivel académico completado (Doctorado, Maestría, Especialización, Pregrado). |
| `activo` | Booleano | Sí | E/S | `[SUPUESTO]` Control de borrado lógico | `true` si el investigador está activo para cálculos y vistas regulares; `false` si está desactivado. |

---

## 3. Entidad Vinculación de Integrante (`IntegranteGrupo`)

| Variable | Tipo de Dato | Req. | E/S | Fuente y Cita | Descripción |
|---|---|---|---|---|---|
| `codigo_gruplac` | Texto (14-20) | Sí | E/S | [[SCIENTI-Mapa-de-campos#3. Entidad Integrante del Grupo]] | Código del grupo al que pertenece la vinculación. |
| `codigo_rh` | Texto (10-15) | Sí | E/S | [[SCIENTI-Mapa-de-campos#3. Entidad Integrante del Grupo]] | Código CvLAC del investigador vinculado. |
| `nombre_completo` | Texto (255) | Sí | E/S | [[SCIENTI-Mapa-de-campos#3. Entidad Integrante del Grupo]] | Nombre registrado en la lista de integrantes del grupo. |
| `rol` | Enumeración | Sí | E/S | [[SCIENTI-Mapa-de-campos#3. Entidad Integrante del Grupo]] | Rol dentro del colectivo: `Líder`, `Investigador` o `Estudiante`. |
| `fecha_inicio` | Fecha (AAAA-MM) | Sí | E/S | [[SCIENTI-Mapa-de-campos#3. Entidad Integrante del Grupo]] | Fecha en que inició la vinculación con el grupo. |
| `fecha_fin` | Fecha (AAAA-MM) | No | E/S | [[SCIENTI-Mapa-de-campos#3. Entidad Integrante del Grupo]] | Fecha de terminación de la vinculación (o nulo / "Actual" si sigue activo). |
| `activo` | Booleano | Sí | E/S | `[SUPUESTO]` Control de estado | Estado activo de la relación de membresía. |

---

## 4. Entidad Producto de Investigación (`Producto`)

| Variable | Tipo de Dato | Req. | E/S | Fuente y Cita | Descripción |
|---|---|---|---|---|---|
| `id_producto` | Texto (UUID/Hash) | Sí | E/S | `[SUPUESTO]` Identificador unívoco | Clave primaria del producto para garantizar persistencia y nodo único en la multilista. |
| `titulo` | Texto (500) | Sí | E/S | [[SCIENTI-Mapa-de-campos#4. Entidad Producto de Investigación]] | Título oficial de la publicación o desarrollo tecnológico. |
| `tipo_mayor` | Enumeración | Sí | E/S | [[Modelo-Productos#Clasificación tipológica y pesos ponderados]] | Agrupación canónica: `GNC`, `DTI`, `ASC` o `FRH`. Dimensión 3 del Hipercubo. |
| `subtipo` | Texto (100) | Sí | E/S | [[Modelo-Productos#1. Productos de Generación de Nuevo Conocimiento (GNC)]] | Subtipo específico: `Articulo`, `Libro`, `Capitulo`, `Patente`, `Software`, `Diseno_Industrial`, `Tesis_Doctorado`, etc. |
| `ano` | Entero (4) | Sí | E/S | [[SCIENTI-Mapa-de-campos#4. Entidad Producto de Investigación]] | Año de publicación, patente u obtención. Dimensión 4 del Hipercubo. |
| `mes` | Entero (1-12) | No | E/S | [[SCIENTI-Mapa-de-campos#4. Entidad Producto de Investigación]] | Mes de publicación cuando esté registrado en la fuente. |
| `pais` | Texto (50) | No | E/S | [[SCIENTI-Mapa-de-campos#4. Entidad Producto de Investigación]] | País de edición o publicación del producto. |
| `estado_validacion` | Enumeración | Sí | E/S | [[Modelo#Estados de validación]]; [[SCIENTI-Mapa-de-campos#4. Entidad Producto de Investigación]] | Estado de validez institucional: `Avalado`, `Con soporte` o `No avalado`. Dimensión 5 del Hipercubo. |
| `detalles` | JSON / Texto | No | E/S | [[SCIENTI-Mapa-de-campos#4. Entidad Producto de Investigación]] | Metadatos bibliográficos complementarios: revista, ISSN, DOI, volumen, ISBN, registro de patente, etc. |
| `activo` | Booleano | Sí | E/S | `[SUPUESTO]` Control de borrado lógico | `true` si el producto está activo; si es `false`, se excluye de las sumatorias del hipercubo. |

---

## 5. Relaciones de la Multilista

### Relación Coautoría (`ProductoAutor`)
- `id_producto` (Texto): Referencia al nodo único del producto.
- `codigo_rh` (Texto): Referencia al investigador coautor.
- Permite que un producto sea referenciado simultáneamente por $N$ autores.

### Relación Pertenencia (`ProductoGrupo`)
- `id_producto` (Texto): Referencia al nodo único del producto.
- `codigo_gruplac` (Texto): Referencia al grupo de investigación que declara el producto.

---

## 6. Variables y Métricas de Salida (Hipercubo y GUI)

| Métrica de Salida | Tipo | Operación Hipercubo | Descripción |
|---|---|---|---|
| `total_productos_activos` | Entero | `Roll-up` total sobre todas las dimensiones | Cantidad consolidada de productos activos en la institución o selección actual. |
| `conteo_por_categoria` | Diccionario {Cat: Int} | `Slice` / `Roll-up` colapsando Grupo, Investigador y Año | Distribución agregada de productos en GNC, DTI, ASC y FRH. |
| `conteo_por_ano` | Serie Temporal {Año: Int} | `Roll-up` colapsando Grupo, Investigador y Categoría | Evolución histórica anual de la producción científica. |
| `produccion_investigador` | Tabla {Inv, GNC, DTI, ASC, FRH} | `Slice` por Investigador + `Roll-up` | Perfil de producción individual discriminado por categorías. |
| `produccion_grupo_ventana` | Matriz {Año × Cat} | `Subcubo` (Grupo $G$, Años $[A_1, A_2]$) | Vista detallada de la producción de un grupo en una ventana de observación quinquenal. |
| `indicador_cohesion_bruto` | Decimal [0.0 - 1.0] | Algorítmico desde Multilista | Proporción de productos del grupo con al menos 2 coautores pertenecientes al grupo. |
| `indicador_cooperacion_bruto` | Decimal [0.0 - 1.0] | Algorítmico desde Multilista | Proporción de productos del grupo con coautores externos o de otros grupos. |
