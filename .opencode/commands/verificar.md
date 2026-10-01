---
description: Ejecuta scripts/verificar.ps1 y resume el resultado
agent: qa
---
Ejecuta `powershell -File scripts/verificar.ps1` y muestra la tabla tal como salió.
Si "$ARGUMENTS" contiene la palabra "red", agrega el parámetro -ConRed; si no, NO lo agregues.
Si algo falla: explica la causa probable de cada paso en FALLA y qué agente debería corregirlo. No modifiques nada.
