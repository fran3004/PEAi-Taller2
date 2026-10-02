---
description: Corre scripts/verificar.ps1 y resume el resultado
---
1. Ejecuta `git status` y anota si hay cambios sin guardar.
2. Ejecuta `powershell -File scripts/verificar.ps1` (agrega `-ConRed` solo si el usuario lo pidió).
3. Muestra la tabla OK / FALLA / sin pruebas aún tal como salió.
4. Si hay FALLA, explica la causa probable de cada una, sin corregir nada todavía.
5. Termina con una línea: "Todo en verde" o la lista de pasos que fallaron.
