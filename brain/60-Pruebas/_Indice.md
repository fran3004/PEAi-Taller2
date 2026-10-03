---
tipo: indice
estado: revisado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[00-Inicio]]"
  - "[[SPEC]]"
  - "[[Arquitectura]]"
origen: "AUDITORIA-DISENO-PEAI.md - Fase 15"
---

# Bóveda de Pruebas, Verificación y Trazabilidad

Esta sección consolida el marco de pruebas de PEA-i, garantizando la trazabilidad bidireccional entre los requisitos normativos de la especificación, el diseño de componentes y las suites de prueba ejecutables en Python y C++.

## Contenido

- [[Trazabilidad]]: Matriz integral de cobertura de requisitos funcionales (R0–R12), criterios normativos (C1–C6), componentes de diseño, ADRs y pruebas unitarias/integración.
- Scripts de ejecución continua:
  - `scripts/verificar.ps1`: Comando maestro de verificación integral (bóveda, compilación C++, pruebas C++ y pruebas Python).
  - `tools/brain/verificar_brain.py`: Validador formal de la bóveda de Obsidian.
