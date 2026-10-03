---
tipo: adr
estado: aprobado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[_Indice]]"
  - "[[Modelo-de-dominio]]"
  - "[[Contrato-de-datos]]"
origen: "AGENTS.md y AUDITORIA-DISENO-PEAI.md - Fase 12"
---

# ADR-0014 · Nomenclatura del Dominio en Español y Convención en Base de Datos

## Contexto
El dominio científico y académico del proyecto (SCIENTI, Minciencias, Universidad Popular del Cesar) está regulado en español. Mezclar términos en inglés en nombres de clases y entidades (`Group`, `Researcher`, `ResearchProduct`) con términos en español genera un código confuso ("Spanglish") y dificulta la trazabilidad contra los documentos oficiales de entrada.

## Opciones consideradas
1. **Convención en inglés tradicional para código**: Emplear nombres en inglés para clases y variables. Crea disonancias cognitivas con los términos oficiales del Modelo Minciencias (ej. *Apropiación Social del Conocimiento*, *GrupLAC*, *CvLAC*).
2. **Nomenclatura rigurosa en español sin caracteres no ASCII en identificadores de código y `snake_case` en base de datos**:
   - Clases y estructuras en español sin tildes: `Grupo`, `Investigador`, `Producto`, `ListaDoble`, `Multilista`, `Hipercubo`.
   - Base de datos y APIs en `snake_case` sin tildes: `codigo_cvlac`, `estado_validacion`, `es_ejemplo`.
   - Nombres de archivos y rutas sin tildes ni espacios: `Modelo-de-dominio.md`, `verificar_brain.py`.

## Decisión
Se adopta la **nomenclatura unificada en español sin caracteres especiales** en todo el proyecto:
- El modelo conceptual, clases, estructuras y métodos usan vocabulario en español neutro sin acentos gráficos en identificadores.
- La persistencia en PostgreSQL utiliza nombres en minúsculas con guiones bajos (`snake_case`).
- Todo texto visible en pantallas, mensajes y bitácoras debe llevar ortografía y acentuación perfecta en español (UTF-8).

## Consecuencias
- **Positivas**: Claridad conceptual inmediata; trazabilidad directa con la literatura del Modelo Minciencias; eliminación de errores de codificación en compiladores y enlazadores.
- **Disciplina**: Obligación de evitar tildes en nombres de variables y nombres de archivos de Obsidian.
