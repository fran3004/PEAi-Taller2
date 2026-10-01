---
description: Descarga, analiza y organiza una URL de SCIENTI con tools/fuentes
agent: fuentes
---
Procesa esta fuente: $ARGUMENTS

1. Valida la dirección: HTTPS y host scienti.minciencias.gov.co. Si no cumple, DETENTE y avisa.
2. Ejecuta `python -m tools.fuentes organizar "$ARGUMENTS"`.
3. Reporta: secciones y campos extraídos, campos que NO se pudieron extraer, filas descartadas y dónde quedaron el JSON, el CSV y la nota de brain/40-Fuentes/.
4. Respeta la pausa de 1 segundo y la caché. Nunca simules una descarga.
