---
description: Pruebas cruzadas entre Python y C++ contra la misma base
agent: qa
---
Ejecuta las pruebas de interoperabilidad entre la aplicación Python y la de C++. Escenarios: $ARGUMENTS (si está vacío, todos los de tests/contrato/).

1. Corre `python tools/interop/probar_contrato.py` y muestra la salida completa.
2. Corre `python tools/interop/buscar_secretos.py` y muestra si hay hallazgos (sin imprimir claves completas).
3. Reporta las diferencias entre los resúmenes JSON de Python y de C++, campo por campo.
4. Trabaja en modo prueba: solo filas con es_ejemplo=true y prefijo PRUEBA-.
5. No modifiques archivos.
