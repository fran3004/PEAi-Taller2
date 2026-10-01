# Formato de entrega entre agentes

Todo agente (principal o subagente) termina su trabajo con estas ocho secciones, en este orden:

1. **Objetivo**: qué se pidió, en una o dos líneas.
2. **Hallazgos**: lo que encontraste, con rutas de archivo.
3. **Evidencia**: comandos ejecutados y su salida real (recortada si es larga). Nunca inventes una salida.
4. **Decisiones**: lo que decidiste y por qué. Si es importante, enlaza el ADR.
5. **Riesgos**: lo que podría salir mal y qué tan probable es.
6. **Cambios**: archivos creados, editados o borrados.
7. **Pruebas**: cuántas se ejecutaron, cuántas pasaron, cuáles fallaron.
8. **Siguiente acción**: lo próximo que debe hacer el usuario o el siguiente agente.

Reglas:
- Si no pudiste comprobar algo, escribe "no verificado" en vez de afirmarlo.
- No pegues claves, tokens ni el contenido de .env en ninguna sección.
- Antes de entregar, escribe la nota de bitácora en brain/50-Bitacora/ (el orquestador la escribe si tú no puedes editar).
