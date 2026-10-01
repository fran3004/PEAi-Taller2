---
description: Actualiza y valida la bóveda de Obsidian
agent: documentador
---
Actualiza la bóveda de Obsidian. Enfoque: $ARGUMENTS (si está vacío, revisa todo brain/).

1. Ejecuta `python tools/brain/verificar_brain.py` y anota los errores.
2. Corrige propiedades faltantes, enlaces rotos y notas huérfanas.
3. Verifica que los ADR tengan numeración consecutiva y que brain/00-Inicio.md enlace a todo lo importante.
4. No toques brain/40-Fuentes/Modelo-original.md ni brain/.obsidian/.
5. Vuelve a ejecutar el verificador y muestra el resultado final.
