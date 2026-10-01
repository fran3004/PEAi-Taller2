---
description: Escribe la bitácora de la sesión y hace commit
agent: documentador
---
Cierra la sesión de trabajo. Resumen del usuario: $ARGUMENTS

1. Ejecuta `git status` y `git log --oneline -5`.
2. Crea la nota brain/50-Bitacora/AAAA-MM-DD-opencode-<tema>.md con la plantilla Bitacora (agente, rama y commit llenos).
3. Ejecuta `python tools/brain/verificar_brain.py` y corrige lo que reporte.
4. Haz `git add -A` y un commit con prefijo (feat:, fix:, docs:, test: o chore:). No hagas push.
5. Muestra el hash del commit y un resumen de tres líneas.
