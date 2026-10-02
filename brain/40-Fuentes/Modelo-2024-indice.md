---
tipo: indice
estado: aprobado
creado: 2026-10-02
actualizado: 2026-10-02
relacionado:
  - "[[Modelo-2024-original]]"
  - "[[Modelo]]"
  - "[[Modelo-Investigadores]]"
  - "[[Modelo-Grupos]]"
  - "[[Modelo-Productos]]"
  - "[[Modelo-Areas-OCDE]]"
  - "[[Modelo-Estadisticas]]"
  - "[[Modelo-Guias-Revision]]"
origen: "docs/entrada/Modelo-2024.original.pdf"
---

# Índice Analítico y Mapa Temático · Modelo Minciencias 2024

Documento de referencia: **M601PR04G01 (Versión 02)**, 252 páginas.  
Texto completo de solo lectura preservado en: [[Modelo-2024-original]].

Este índice desglosa cada capítulo, anexo y sección del documento oficial, su ubicación de página, la nota temática derivada en la bóveda `brain/` y su impacto específico en la arquitectura y dominio de **PEA-i**.

---

## Tabla de Navegación por Capítulos y Anexos

| Capítulo / Anexo | Sección | Página | Nota Temática | Impacto para PEA-i |
|---|---|:---:|---|---|
| **Contexto** | Marco legal y objetivo SNCTI | 10 | [[Modelo]] | Justificación institucional y definiciones del SNCTI. |
| **Capítulo I** | 1.1 Presentación y 1.2 Introducción | 12 | [[Modelo]] | Propósitos de la medición y evolución conceptual. |
| **Capítulo I** | 1.3 Propósitos del Modelo | 13 | [[Modelo]] | Objetivos de caracterización de la investigación en Colombia. |
| **Capítulo I** | 1.4 Antecedentes del Modelo (2013-2024) | 14–30 | [[Modelo]] | Historial de convocatorias de medición (Colciencias / Minciencias). |
| **Capítulo I** | 1.5 Decisiones para implementar el Modelo 2024 | 31–33 | [[Modelo]] | Ajustes metodológicos aplicables a la convocatoria actual. |
| **Capítulo I** | 1.6 Convocatoria de reconocimiento y medición | 34 | [[Modelo]] | Criterios operativos de la convocatoria. |
| **Capítulo II** | 2.1 Definición de Investigador | 35 | [[Modelo-Investigadores]] | Modelo de entidad `Investigador` y validación de perfiles. |
| **Capítulo II** | 2.2 Requisitos para Reconocimiento de Investigadores | 35–36 | [[Modelo-Investigadores]] | Reglas de vinculación a grupos y producción mínima. |
| **Capítulo II** | 2.3 Categorías de Investigadores (Emérito, Senior, Asociado, Junior, Integrantes) | 36–42 | [[Modelo-Investigadores]] | Campo `categoria_investigador` en BD y estructuras en memoria. |
| **Capítulo II** | 2.4 Criterios de Evaluación y Clasificación de Investigadores | 42–65 | [[Modelo-Investigadores]] | Algoritmo de clasificación de investigadores según trayectoria y producción. |
| **Capítulo III** | 3.1 Definición y Requisitos de Reconocimiento de Grupos | 66–114 | [[Modelo-Grupos]] | Modelo de entidad `Grupo`, validación de líder, aval institucional y proyectos. |
| **Capítulo III** | 3.2 Producción y 3.3 Ventana de Observación | 115 | [[Modelo-Grupos]] | Ventana temporal (5 años general, 10 años patentes/libros) para filtrado de productos. |
| **Capítulo III** | 3.4–3.5 Eliminación de Efectos de Escala y Producción Normalizada | 115–116 | [[Modelo-Grupos]] | Ecuaciones logarítmicas de producción usadas en análisis estadísticos. |
| **Capítulo III** | 3.6 Pesos Globales de la Producción (Tabla 6) | 116–118 | [[Modelo-Grupos]], [[Modelo-Productos]] | Tabla de pesos relativos por tipo/subtipo de producto para el Hipercubo. |
| **Capítulo III** | 3.7 Caracterización de Productos de Grupos | 118–123 | [[Modelo-Grupos]] | Tipologías válidas reconocidas a grupos de investigación. |
| **Capítulo III** | 3.8 Clasificación de Grupos (A1, A, B, C y Reconocido) | 123–130 | [[Modelo-Grupos]] | Reglas y umbrales de clasificación de grupos (cálculo de estado del grupo). |
| **Anexo 1** | 4.1 Productos de Generación de Nuevo Conocimiento (GNC) | 131–146 | [[Modelo-Productos]] | Artículos A1-D, Libros, Capítulos, Patentes, Variedades, Razas y Obras de Arte. |
| **Anexo 1** | 4.2 Productos de Desarrollo Tecnológico e Innovación (DTI) | 147–151 | [[Modelo-Productos]] | Diseños industriales, Software, Plantas piloto, Prototipos, Secretos e Innovaciones. |
| **Anexo 1** | 4.3 Productos de Apropiación Social del Conocimiento (ASC) | 152–155 | [[Modelo-Productos]] | Procesos de apropiación, participación ciudadana y codiseño. |
| **Anexo 1** | 4.4 Productos de Divulgación Pública de la Ciencia (DPC) | 156–161 | [[Modelo-Productos]] | Publicaciones de divulgación, eventos y contenidos de comunicación científica. |
| **Anexo 1** | 4.5 Productos de Formación de Recurso Humano (FRH) | 162–169 | [[Modelo-Productos]] | Tesis de doctorado, trabajos de grado de maestría y pregrado, proyectos CTeI. |
| **Anexo 2** | 5.1 Indicadores a partir de perfiles de grupos | 170–182 | [[Modelo-Estadisticas]] | Perfil de integrantes, colaboración, trayectoria y producción. |
| **Anexo 2** | 5.2 Visualización institucional y conteos por gran área | 183–193 | [[Modelo-Estadisticas]] | Vistas del Panel/Dashboard para la UPC: conteos por área OCDE y categorías. |
| **Anexo 3** | 6. Modelo Estadístico de Trayectoria de Grupos | 194–201 | [[Modelo-Estadisticas]] | Modelo logístico ordenado para evaluar evolución temporal de los grupos. |
| **Anexo 4** | 7. Guías de Revisión de Productos (Artículos, Libros, Software, Tesis) | 202–239 | [[Modelo-Guias-Revision]] | Reglas de validación documental aplicables al parser de CvLAC/GrupLAC. |
| **Anexo 5** | 8. Clasificación de Áreas Científicas según OCDE | 240–244 | [[Modelo-Areas-OCDE]] | Catálogo de 6 Grandes Áreas y 42 subáreas para tipificar entidades. |
| **Bibliografía** | 9. Referencias bibliográficas | 245–252 | [[Modelo]] | Referencias metodológicas y fuentes de consulta. |

---

## Directrices para el Consumo de Información en PEA-i

1. **Citas obligatorias**: Toda nota de requisitos, diseño o prueba debe citar la página exacta del original utilizando enlaces con ancla: `[[Modelo-2024-original#Página X]]`.
2. **Jerarquía en Estructuras**:
   - `Grupo`: Posee código de grupo, nombre, gran área OCDE, categoría Minciencias (A1, A, B, C, Reconocido), lista de integrantes vinculados y multilista de productos.
   - `Investigador`: Posee documento/código, nombre, categoría Minciencias (Emérito, Senior, Asociado, Junior, Sin Reconocimiento) y lista de vínculos a grupos.
   - `Producto`: Un solo nodo en memoria compartido bidireccionalmente por su grupo y por sus autores investigadores (multilista), tipificado con su categoría, año, subtipo y peso relativo.
3. **Cálculo de Métricas en el Hipercubo**:
   - Dimensiones: `Grupo` × `Categoría de Producto (GNC, DTI, ASC/DPC, FRH)` × `Año de Producción` × `Subtipo/Calidad`.
   - Se alimenta en memoria cargando las estructuras y permite consultas analíticas instantáneas sin consultar repetitivamente a PostgreSQL.
