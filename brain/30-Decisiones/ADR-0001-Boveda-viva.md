---
tipo: adr
estado: aprobado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[_Indice]]"
  - "[[00-Inicio]]"
  - "[[Arquitectura]]"
origen: "AGENTS.md y AUDITORIA-DISENO-PEAI.md - Fase 12"
---

# ADR-0001 · Bóveda Viva de Obsidian como Única Fuente de Documentación

## Contexto
En proyectos de ingeniería de software con múltiples agentes autónomos y colaboradores humanos, la documentación suele fragmentarse en wikis externas, archivos `README.md` desactualizados o comentarios dispersos en el código. Esto genera desalineación técnica y contradicciones sobre los requisitos y el diseño.

## Opciones consideradas
1. **Documentación tradicional en wikis externas o archivos README**: Fácil de crear inicialmente, pero propensa a desactualización silenciosa y sin validación programática en CI/CD.
2. **Bóveda viva de Obsidian en `brain/` integrada en el repositorio**: Todo el conocimiento técnico vive en texto plano con frontmatter estructurado, validado por scripts (`tools/brain/verificar_brain.py`) antes de cada commit.

## Decisión
Se adopta la **Bóveda viva de Obsidian (`brain/`)** como la **única casa de la documentación viva** del proyecto PEA-i.
Toda decisión técnica importante debe formularse como un ADR, todo cambio debe registrarse en la bitácora y ninguna funcionalidad se considera terminada si no está debidamente documentada y enlazada con wikienlaces válidos.

## Consecuencias
- **Positivas**: Trazabilidad completa entre requisitos, diseño, pruebas y código; detección automática de enlaces rotos y metadatos incompletos.
- **Negativas / Costos**: Requiere disciplina estricta de nombrado (sin tildes ni espacios en nombres de archivo) y ejecución obligatoria del verificador.
