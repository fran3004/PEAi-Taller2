---
trigger: always_on
description: Nada se da por terminado sin pruebas ejecutadas
---
# Verificación
- Ningún módulo está terminado sin pruebas ejecutadas y con su resultado a la vista.
- Nunca digas que algo funciona sin haberlo corrido. Una suite verde es evidencia, no prueba.
- Las pruebas que usan internet van marcadas "red" y no corren por defecto (se activan con -ConRed).
- scripts/verificar.ps1 es el comando único: compila C++, corre las pruebas de C++ y de Python y valida la bóveda.
- Antes de cerrar una tarea, cambia al rol QA y revisa casos borde, errores y fugas de credenciales.
- Cierra siempre con el REPORTE FINAL: objetivo, archivos, comandos, pruebas, supuestos, riesgos y siguiente paso.
- Un commit por tarea, con prefijo feat:, fix:, docs:, test: o chore:.

El contrato completo está en AGENTS.md.
