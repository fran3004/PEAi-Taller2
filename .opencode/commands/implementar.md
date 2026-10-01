---
description: Implementa una tarea, pero solo si ya existen el SPEC y el contrato de datos
agent: orquestador
---
Implementa lo siguiente: $ARGUMENTS

Puertas (si alguna falla, DETENTE y avisa; no sigas):
1. Existe brain/10-Requisitos/SPEC.md con estado "revisado" o "aprobado".
2. Existe brain/20-Diseno/Contrato-de-datos.md.
3. Existe brain/20-Diseno/Arquitectura.md aprobado por el usuario.

Si las puertas pasan:
1. Delega en el agente dueño de cada carpeta (python, cpp, datos, gui...).
2. Un agente escribe a la vez en la misma carpeta.
3. Pide a qa que ejecute las pruebas y reporte los resultados exactos.
4. Termina con el REPORTE FINAL y una nota de bitácora.
