---
trigger: always_on
description: Extracción responsable de fuentes y manejo de secretos
---
# Fuentes y secretos
- Para páginas web usa requests + beautifulsoup4 (con lxml) + pydantic. Para PDF, pdfplumber. Otra herramienta exige un ADR.
- Solo se descarga de scienti.minciencias.gov.co, por HTTPS, con timeout, máximo 3 reintentos y pausa de 1 segundo.
- Usa caché en datos/cache/ y un User-Agent que diga que es un proyecto universitario.
- Nunca finjas una descarga ni inventes campos. Si la fuente falla, avisa y propone CSV o PDF.
- El documento Modelo ya está extraído en docs/entrada/: no lo vuelvas a descargar.
- Los datos de investigadores son personales: repositorio privado y solo lo mínimo en tests/fixtures.
- Nunca leas ni imprimas .env, claves sb_secret, service_role, contraseñas ni tokens.
- Si un secreto aparece en un archivo o en un commit, avisa de inmediato para rotarlo.

El contrato completo está en AGENTS.md.
