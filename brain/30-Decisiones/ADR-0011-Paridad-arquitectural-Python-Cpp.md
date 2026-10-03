---
tipo: adr
estado: aprobado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[_Indice]]"
  - "[[Interoperabilidad]]"
  - "[[Arquitectura]]"
  - "[[Despliegue]]"
origen: "AGENTS.md y AUDITORIA-DISENO-PEAI.md - Fase 12"
---

# ADR-0011 · Paridad Arquitectural y Funcional Estricta entre Python y C++

## Contexto
El taller formativo de la Universidad Popular del Cesar exige la entrega de dos implementaciones completas con interfaz gráfica: una en Python 3.12 (PySide6) y otra en C++17 (Qt 6 Widgets). Si cada implementación adopta un diseño arquitectónico distinto o librerías divergentes, el mantenimiento se duplica de forma caótica y se dificulta garantizar que ambas calculen exactamente los mismos resultados.

## Opciones consideradas
1. **Desarrollos desacoplados con libertad de diseño**: Permitir que Python use librerías de alto nivel (como Pandas) y C++ use librerías distintas. Viola el contrato de estructuras hechas a mano y produce divergencia en los cálculos estadísticos.
2. **Paridad arquitectural isomórfica por capas y oráculo canónico**: Mismas capas (*GUI $\rightarrow$ Servicios $\rightarrow$ Estructuras $\rightarrow$ Repositorios $\rightarrow$ HTTPS*), mismos algoritmos de hipercubo hechos a mano y verificación cruzada contra un archivo de resultados canónicos (`tests/fixtures/esperado.json`).

## Decisión
Se adopta la **paridad arquitectural y funcional isomórfica** formalizada en [[Arquitectura]] e [[Interoperabilidad]].
Ambas aplicaciones comparten la misma jerarquía de conceptos, los mismos nombres de dominio, el mismo contrato JSON y las mismas estructuras de datos. Cualquier función de análisis debe producir una salida idéntica verificada por el oráculo canónico en las pruebas unitarias de ambos lenguajes.

## Consecuencias
- **Positivas**: Simetría conceptual; fácil transferencia de conocimiento y depuración entre lenguajes; consistencia matemática garantizada en ambos escritorios.
- **Costos**: Requiere disciplina estricta al implementar estructuras en C++ (gestión de memoria sin fugas con RAII y punteros inteligentes) y en Python (anotaciones de tipo y linting riguroso).
