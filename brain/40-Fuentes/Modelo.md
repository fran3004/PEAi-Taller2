---
tipo: fuente
estado: aprobado
creado: 2026-10-02
actualizado: 2026-10-02
relacionado:
  - "[[Modelo-2024-indice]]"
  - "[[Modelo-2024-original]]"
  - "[[Modelo-Investigadores]]"
  - "[[Modelo-Grupos]]"
  - "[[Modelo-Productos]]"
  - "[[Modelo-Areas-OCDE]]"
  - "[[Modelo-Estadisticas]]"
  - "[[Modelo-Guias-Revision]]"
origen: "docs/entrada/Modelo-2024.original.pdf"
---

# Modelo de Medición de Grupos e Investigadores · Minciencias 2024

Documento oficial de referencia: **M601PR04G01 (Versión 02)**, 252 páginas.  
Transcripción íntegra de solo lectura: [[Modelo-2024-original]].  
Índice analítico y mapa temático: [[Modelo-2024-indice]].

---

## 1. Resumen Fiel del Modelo

El Modelo de Medición de Grupos de Investigación, Desarrollo Tecnológico o de Innovación y de Reconocimiento de Investigadores del SNCTI (Año 2024) constituye el estándar oficial de Minciencias para caracterizar la capacidad científica y tecnológica de Colombia ([[Modelo-2024-original#Página 10]], [[Modelo-2024-original#Página 13]]).

El sistema se fundamenta en:
1. **Reconocimiento de Investigadores**: Clasificación individual según trayectoria formativa y producción en cuatro niveles: Emérito, Sénior, Asociado y Junior, además de categorizar a los integrantes vinculados y estudiantes ([[Modelo-2024-original#Página 42]]).
2. **Reconocimiento y Clasificación de Grupos**: Evaluación colectiva que categoriza los grupos en A1, A, B, C y Reconocidos a partir de ventanas temporales (5 y 10 años) y fórmulas logarítmicas de normalización que mitigan el efecto del tamaño ([[Modelo-2024-original#Página 115]], [[Modelo-2024-original#Página 123]]).
3. **Ponderación de Productos**: Tipificación rigurosa de productos en 4 grandes ejes (GNC, DTI, ASC/DPC, FRH) con pesos relativos diferenciados por cuartiles de impacto, evaluación por pares y exámenes de concesión legal ([[Modelo-2024-original#Página 116]], [[Modelo-2024-original#Página 131]]).
4. **Taxonomía Científica**: Uso estricto de las 6 Grandes Áreas de la OCDE ([[Modelo-2024-original#Página 240]]).

Debido a la extensión del documento original (252 páginas), la especificación detallada se desglosa en el corpus temático:
- **Investigadores**: [[Modelo-Investigadores]]
- **Grupos y Clasificación**: [[Modelo-Grupos]]
- **Catálogo de Productos y Pesos**: [[Modelo-Productos]]
- **Áreas y Disciplinas OCDE**: [[Modelo-Areas-OCDE]]
- **Indicadores y Estadísticas Institucionales**: [[Modelo-Estadisticas]]
- **Guías de Revisión Documental**: [[Modelo-Guias-Revision]]

---

## 2. Categorías de Producto y Estados de Validación

### Categorías Principales ([[Modelo-2024-original#Página 131]])
1. **GNC (Generación de Nuevo Conocimiento)**: Artículos científicos (A1, A2, B, C, D), notas científicas, libros y capítulos de investigación, patentes concedidas, variedades vegetales, nuevas razas animales y obras de arte/arquitectura.
2. **DTI (Desarrollo Tecnológico e Innovación)**: Diseños industriales, software registrado con certificación de uso, plantas piloto, prototipos industriales, secretos empresariales, spin-offs (EBT/ICC) e innovaciones de gestión y procesos.
3. **ASC / DPC (Apropiación Social y Divulgación Pública)**: Procesos de apropiación social, ciencia ciudadana, publicaciones de divulgación, boletines y contenidos transmedia.
4. **FRH (Formación de Recurso Humano)**: Tesis de doctorado, trabajos de grado de maestría y pregrado dirigidos y aprobados, y proyectos de investigación y desarrollo.

### Estados de Validación ([[Modelo-2024-original#Página 131]])
- **Cumple Existencia**: El producto cuenta con los metadatos y soportes formales mínimos indispensables. Si no cumple existencia, el producto queda descartado de todo cálculo.
- **Cumple Calidad**: El producto cumple con los estándares exigidos para alcanzar una categoría específica (ej. indexación en cuartil Q1/Q2, evaluación por pares ciegos, concesión de patente).

---

## 3. Tablas por Entidad del Dominio PEA-i

### 3.1 Entidad `Grupo`
| Campo | Tipo | Obligatorio | Descripción | Entrada/Salida | Cita |
|---|---|:---:|---|:---:|---|
| `id_grupo` | UUID | Sí | Identificador interno único del grupo en BD | Salida (sistema) | Supuesto técnico |
| `codigo_gruplac` | String | Sí | Código alfanumérico oficial en Minciencias | Entrada (GrupLAC) | [[Modelo-2024-original#Página 67]] |
| `nombre` | String | Sí | Nombre oficial del grupo de investigación | Entrada (GrupLAC) | [[Modelo-2024-original#Página 66]] |
| `gran_area_ocde` | String | Sí | Gran área de conocimiento principal | Entrada (GrupLAC) | [[Modelo-2024-original#Página 240]] |
| `area_conocimiento` | String | Sí | Área o disciplina OCDE específica | Entrada (GrupLAC) | [[Modelo-2024-original#Página 240]] |
| `categoria` | Enum | Sí | Clasificación oficial: A1, A, B, C, Reconocido | Entrada / Calculado | [[Modelo-2024-original#Página 123]] |
| `ano_fundacion` | Integer | Sí | Año de creación del grupo | Entrada (GrupLAC) | [[Modelo-2024-original#Página 115]] |
| `lider_id` | UUID | Sí | Referencia al investigador líder del grupo | Entrada / Relación | [[Modelo-2024-original#Página 67]] |
| `activo` | Boolean | Sí | Indicador de estado para borrado lógico | Salida (sistema) | Supuesto técnico |

### 3.2 Entidad `Investigador`
| Campo | Tipo | Obligatorio | Descripción | Entrada/Salida | Cita |
|---|---|:---:|---|:---:|---|
| `id_investigador` | UUID | Sí | Identificador interno único en BD | Salida (sistema) | Supuesto técnico |
| `codigo_cvlac` | String | Sí | Identificador alfanumérico en CvLAC | Entrada (CvLAC) | [[Modelo-2024-original#Página 41]] |
| `nombre_completo` | String | Sí | Nombres y apellidos del investigador | Entrada (CvLAC) | [[Modelo-2024-original#Página 41]] |
| `categoria` | Enum | Sí | Emérito, Sénior, Asociado, Junior, Sin categoría | Entrada / Calculado | [[Modelo-2024-original#Página 42]] |
| `nivel_formacion` | Enum | Sí | Máximo título alcanzado (Doctor, Magíster, etc.) | Entrada (CvLAC) | [[Modelo-2024-original#Página 43]] |
| `activo` | Boolean | Sí | Indicador de estado para borrado lógico | Salida (sistema) | Supuesto técnico |

### 3.3 Entidad `Producto`
| Campo | Tipo | Obligatorio | Descripción | Entrada/Salida | Cita |
|---|---|:---:|---|:---:|---|
| `id_producto` | UUID | Sí | Identificador interno único en BD | Salida (sistema) | Supuesto técnico |
| `titulo` | String | Sí | Nombre o título del producto de CTeI | Entrada (fuentes) | [[Modelo-2024-original#Página 131]] |
| `categoria_principal` | Enum | Sí | Eje temático: GNC, DTI, ASC_DPC, FRH | Entrada / Catálogo | [[Modelo-2024-original#Página 131]] |
| `subtipo_codigo` | String | Sí | Código de tipología (ej. `ART_OPEN_A1`, `SF`, `TD_DOC`) | Entrada / Catálogo | [[Modelo-2024-original#Página 116]] |
| `ano` | Integer | Sí | Año de publicación o finalización | Entrada (fuentes) | [[Modelo-2024-original#Página 115]] |
| `peso_relativo` | Decimal | Sí | Ponderación relativa del producto | Salida (calculado) | [[Modelo-2024-original#Página 116]] |
| `identificador` | String | No | ISSN, ISBN, DOI o radicado de patente | Entrada (fuentes) | [[Modelo-2024-original#Página 131]] |
| `cumple_existencia` | Boolean | Sí | Validación de requisitos mínimos de existencia | Salida (regla) | [[Modelo-2024-original#Página 131]] |
| `cumple_calidad` | Boolean | Sí | Validación de requisitos de tipología de calidad | Salida (regla) | [[Modelo-2024-original#Página 131]] |
| `activo` | Boolean | Sí | Indicador de estado para borrado lógico | Salida (sistema) | Supuesto técnico |

### 3.4 Entidad `Integrante` (Vínculo Grupo - Investigador)
| Campo | Tipo | Obligatorio | Descripción | Entrada/Salida | Cita |
|---|---|:---:|---|:---:|---|
| `grupo_id` | UUID | Sí | Referencia al grupo | Entrada / Relación | [[Modelo-2024-original#Página 42]] |
| `investigador_id` | UUID | Sí | Referencia al investigador | Entrada / Relación | [[Modelo-2024-original#Página 42]] |
| `rol` | Enum | Sí | Líder, Investigador, Estudiante, Vinculado | Entrada | [[Modelo-2024-original#Página 42]] |
| `fecha_inicio` | Date | Sí | Fecha de inicio de vinculación al grupo | Entrada | [[Modelo-2024-original#Página 67]] |
| `fecha_fin` | Date | No | Fecha de retiro (nulo si activo) | Entrada | [[Modelo-2024-original#Página 67]] |

### 3.5 Entidad `PlanTrabajo` / `Proyecto`
| Campo | Tipo | Obligatorio | Descripción | Entrada/Salida | Cita |
|---|---|:---:|---|:---:|---|
| `id_proyecto` | UUID | Sí | Identificador interno del proyecto | Salida (sistema) | Supuesto técnico |
| `grupo_id` | UUID | Sí | Grupo al que pertenece el proyecto | Entrada / Relación | [[Modelo-2024-original#Página 67]] |
| `titulo` | String | Sí | Título del proyecto de investigación | Entrada | [[Modelo-2024-original#Página 67]] |
| `estado` | Enum | Sí | En ejecución, Terminado | Entrada | [[Modelo-2024-original#Página 67]] |
| `fecha_inicio` | Date | Sí | Fecha de inicio | Entrada | [[Modelo-2024-original#Página 67]] |

---

## 4. Supuestos de Diseño e Implementación para PEA-i

1. **Borrado Lógico**: Todo registro en la base de datos y en las estructuras en memoria dispone del campo `activo = true/false`. La desactivación no destruye el nodo; la eliminación definitiva sólo se realiza previa confirmación en cascada y registro en la Pila de Deshacer.
2. **Paginación PostgREST**: PostgREST restringe las consultas REST a un límite de 1000 filas por petición; el cliente debe implementar paginación basada en rangos (`offset`/`limit`) para no truncar la lectura.
3. **Nodo Único de Producto en Multilista**: Cuando un producto es elaborado en coautoría por integrantes del mismo o distintos grupos, existe como **un solo nodo en memoria**, vinculado desde los respectivos grupos e investigadores.
