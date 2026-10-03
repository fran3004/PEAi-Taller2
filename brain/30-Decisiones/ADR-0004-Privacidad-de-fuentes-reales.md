---
tipo: adr
estado: aprobado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[_Indice]]"
  - "[[Seguridad-y-credenciales]]"
  - "[[Ingesta]]"
origen: "AGENTS.md y AUDITORIA-DISENO-PEAI.md - Fase 12"
---

# ADR-0004 · Privacidad de Datos Personales de Investigadores y Anonimización

## Contexto
Las consultas a la plataforma CvLAC de Minciencias retornan hojas de vida académicas que contienen datos de carácter personal y sensible (documento de identidad, correos personales, trayectorias, nacionalidad). Publicar esta información en un repositorio de código o en notas públicas de documentación compromete la privacidad de los investigadores y contraviene leyes de protección de datos personales (Habeas Data).

## Opciones consideradas
1. **Versionar las extracciones completas en el repositorio**: Facilita el desarrollo pero expone información privada sensible de terceros en el historial de Git.
2. **Aislar los datos reales en carpetas ignoradas por Git y publicar únicamente fixtures anonimizados**: Las extracciones completas van a carpetas privadas excluidas del control de versiones (`datos/cache/`, `brain/40-Fuentes/privado/`), mientras que las pruebas y ejemplos utilizan identificadores y datos sintéticos en `tests/fixtures/`.

## Decisión
Se adopta la **estricta privacidad y aislamiento de datos personales**.
El repositorio solo contiene datos anonimizados, sintéticos o con consentimiento institucional explícito. Ningún commit, nota pública de Obsidian ni informe de bitácora debe contener números de cédula reales ni datos sensibles de investigadores.

## Consecuencias
- **Positivas**: Cumplimiento legal y ético estricto; seguridad de los datos personales.
- **Costos**: Necesidad de mantener scripts de anonimización y fixtures sintéticos coherentes para las pruebas automatizadas.
