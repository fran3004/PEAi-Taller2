---
description: Escribe la bitácora de la sesión y hace commit
---
1. Ejecuta `git status` y `git log --oneline -5`.
2. Crea la nota brain/50-Bitacora/AAAA-MM-DD-antigravity-<tema>.md con la plantilla Bitacora (agente, rama y commit llenos).
3. Ejecuta `python tools/brain/verificar_brain.py` y corrige lo que reporte.
4. Haz `git add -A` y un commit con prefijo (feat:, fix:, docs:, test: o chore:).
5. No hagas push. Muestra el hash del commit y un resumen de tres líneas.
