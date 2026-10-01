---
name: pruebas
description: Usar al diseñar, escribir o ejecutar pruebas del proyecto: unitarias, de integración, de contrato entre Python y C++, y pruebas con red marcadas; también al decidir si un módulo se puede dar por terminado.
---
# Pruebas en PEA-i

## Pirámide
1. Muchas pruebas unitarias rápidas y sin internet (estructuras, dominio, normalización, analizadores).
2. Pruebas de servicios y repositorios con respuestas HTTP simuladas (`responses` en Python; servidor falso con QTcpServer en C++).
3. Pocas pruebas de integración con la base real, marcadas `red` y en modo prueba (solo filas `PRUEBA-` con `es_ejemplo=true`).
4. Pruebas de contrato: el mismo escenario JSON lo ejecutan Python y C++ y se comparan los resúmenes.

## Reglas
- Una prueba que usa internet lleva la marca `red` y NO corre por defecto: se activa con `-ConRed` en `scripts/verificar.ps1`.
- Cada módulo cubre casos borde: vacío, un elemento, extremos, duplicados, datos faltantes, tildes y ñ.
- Probar también los fallos: sin conexión, sesión vencida, conflicto de revisión, persistencia que falla a la mitad (la estructura debe revertirse).
- Las estadísticas del hipercubo se comparan con la RPC `verificar_conteos`.
- Nunca digas "funciona" sin correr el comando y mostrar el resultado. Una suite verde es evidencia, no prueba.
- Cada prueba deja la base como estaba (borra lo que creó).

## Reporte
- Cuántas pruebas se ejecutaron, cuántas pasaron, cuáles fallaron y el comando exacto.
- Las aceptaciones y la trazabilidad (requisito → prueba) se anotan en `brain/60-Pruebas/` con la plantilla Resultado-de-pruebas.

## Lista de comprobación
- [ ] `scripts/verificar.ps1` en verde, y una vez con `-ConRed`.
- [ ] Cada RF del SPEC tiene al menos una prueba o una justificación.
- [ ] Ninguna prueba depende del orden de ejecución.
