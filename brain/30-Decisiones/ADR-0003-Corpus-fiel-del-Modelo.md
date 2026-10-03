---
tipo: adr
estado: aprobado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[_Indice]]"
  - "[[Modelo-de-dominio]]"
  - "[[Modelo-2024-original]]"
origen: "AGENTS.md y AUDITORIA-DISENO-PEAI.md - Fase 12"
---

# ADR-0003 · Corpus Fiel e Inmutable del Modelo Minciencias 2024

## Contexto
El Modelo de Medición de Grupos de Investigación de Minciencias 2024 (documento de 252 páginas) es la máxima fuente de verdad normativa para la tipología de productos, requisitos de categorización y fórmulas de ponderación. Modificar o resumir informalmente este texto puede introducir errores de interpretación científica o contradicciones con el enunciado del taller.

## Opciones consideradas
1. **Resumen libre en una nota general**: Rápido de redactar pero susceptible a omisiones, distorsiones y pérdida de trazabilidad con las páginas oficiales.
2. **Conservación íntegra de solo lectura (`Modelo-2024-original.md`) con notas derivadas indexadas**: Preservar el texto extraído página por página de forma inmutable, complementado por un índice temático y referencias cruzadas directas.

## Decisión
Se adopta la **preservación del corpus fiel e inmutable** en `brain/40-Fuentes/Modelo-2024-original.md`.
Esta nota es estrictamente de solo lectura y reproduce la totalidad de las 252 páginas del PDF. Toda afirmación, modelo de dominio o fórmula implementada en PEA-i debe citar expresamente la página correspondiente del documento original ([[Modelo-2024-original]]).

## Consecuencias
- **Positivas**: Trazabilidad jurídica y académica inexpugnable ante cualquier duda de diseño; verificación automática de completitud de secciones y tablas.
- **Costos**: Archivo Markdown de gran tamaño en la bóveda que requiere herramientas especializadas de búsqueda y navegación.
