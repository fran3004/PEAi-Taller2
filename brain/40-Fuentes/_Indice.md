---
tipo: indice
estado: aprobado
creado: 2026-10-02
actualizado: 2026-10-02
relacionado:
  - "[[00-Inicio]]"
  - "[[Modelo-2024-indice]]"
  - "[[Modelo]]"
  - "[[SCIENTI-GrupLAC]]"
  - "[[SCIENTI-CvLAC]]"
  - "[[SCIENTI-Mapa-de-campos]]"
  - "[[SCIENTI-Informe-extraccion]]"
origen: "Fuentes oficiales del proyecto PEA-i (Modelo Minciencias 2024 y plataforma SCIENTI)"
---

# Índice de Fuentes de Verdad · PEA-i

Este índice reúne y clasifica todo el corpus normativo y las fuentes externas que gobiernan las reglas de negocio, entidades, atributos y validaciones del sistema **PEA-i**.

---

## 1. Jerarquía de Fuentes de Verdad (AGENTS.md)

1. **Documento Modelo Minciencias 2024** (`docs/entrada/` y `brain/40-Fuentes/`): Especificación metodológica oficial para el reconocimiento y medición de grupos e investigadores.
2. **Plataforma SCIENTI (Minciencias)**: Datos estructurados extraídos de las plataformas web oficiales GrupLAC y CvLAC.
3. **Especificación de Requisitos** (`brain/10-Requisitos/SPEC.md`).
4. **Decisiones de Arquitectura** (`brain/30-Decisiones/`).
5. **Código Fuente**. Si el código contradice al Modelo o a SCIENTI, prevalecen las fuentes.

---

## 2. Corpus Documental del Modelo Minciencias 2024

- **Índice General del Modelo**: [[Modelo-2024-indice]] (Mapeo de capítulos, secciones, números de página e impacto para PEA-i).
- **Modelo Organizado con Citas**: [[Modelo]] (Resumen normativo, tipologías, estados de validación y tablas por entidad).
- **Texto Oficial Íntegro (Solo Lectura)**: [[Modelo-2024-original]] (Extracción íntegra y no destructiva de las 252 páginas del código M601PR04G01).
- **Notas Temáticas Derivadas**:
  - [[Modelo-Investigadores]]: Requisitos de categorización (Emérito, Senior, Asociado, Junior, Integrante Vinculado).
  - [[Modelo-Grupos]]: Condiciones de existencia, aval institucional y categorías (A1, A, B, C, Reconocido).
  - [[Modelo-Productos]]: Tipologías (GNC, DTI, ASC, FRH), pesos, ponderaciones y ventanas temporales de observación.
  - [[Modelo-Areas-OCDE]]: Clasificación de 6 grandes áreas y 42 subáreas OCDE/FORD.
  - [[Modelo-Estadisticas]]: Fórmulas e indicadores de Cohesión, Cooperación y tipologías por área.
  - [[Modelo-Guias-Revision]]: Procedimientos de verificación documental y criterios de rechazo.

---

## 3. Fuentes SCIENTI (GrupLAC y CvLAC)

- **Captura GrupLAC (Público)**: [[SCIENTI-GrupLAC]] (Grupo de Investigación modelo anonimizado, 29 productos, 21 integrantes).
- **Captura CvLAC (Público)**: [[SCIENTI-CvLAC]] (Hoja de vida de investigador modelo anonimizada, trayectoria y producción).
- **Mapa de Campos Normativo**: [[SCIENTI-Mapa-de-campos]] (Mapeo exhaustivo de 52 campos, selectores DOM, modelos Pydantic y páginas del Modelo).
- **Informe de Auditoría y Extracción**: [[SCIENTI-Informe-extraccion]] (Bitácora de pruebas HTTP, codificaciones, trazabilidad y fixtures offline).
