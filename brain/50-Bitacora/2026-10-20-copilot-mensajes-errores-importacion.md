---
tipo: bitacora
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[Paridad-Python-Cpp]]"
  - "[[Ingesta]]"
origen: "Alineación de los resúmenes visibles de errores de importación CSV"
agente: "Copilot"
rama: "feat/python-cierre-francisco"
commit: ""
---

# Bitácora · Mensajes de errores de importación

## Objetivo

Mostrar el detalle útil de filas CSV omitidas en las superficies de importación
sin requerir una conexión remota para probar el formato.

## Qué se hizo

- Los avisos de la GUI Python incluyen el conteo de filas con errores y autores
  procesados, tanto para una tarea como para el procesamiento de toda la cola.
- El CLI C++ enumera los mensajes de cada fila omitida y su ayuda ahora incluye
  el tipo CSV `autores`.
- Se agregaron pruebas locales del texto del CLI y de los resúmenes GUI.
- Se actualizó el contrato visual y la matriz de paridad.

## Comandos y resultados

- `.venv\Scripts\python.exe -m pytest -q tests\unit\test_pantallas_finales.py -k "muestra_conteos_de_tarea or acumula_errores_al_procesar_cola"`: 2 aprobadas.
- `.venv\Scripts\python.exe -m pytest -q tests\unit\test_pantallas_finales.py`: 12 aprobadas y 1 fallida en `test_zona_soltar_archivo`; la etiqueta de archivo mostró `investi�res.csv` en lugar de `investigadores.csv`. Esa prueba cubre el nombre presentado en la zona de archivos, no los resúmenes cambiados.
- `.venv\Scripts\python.exe -m ruff check src\pea\gui\pantallas\importar.py tests\unit\test_pantallas_finales.py`: correcto.
- `cmake --build cpp\build --target pruebas_cpp --parallel 4` y `ctest --test-dir cpp\build --output-on-failure`: compilación correcta y 1/1 suite aprobada.
- `cpp\build\pruebas_cpp.exe --no-version`: 56 casos y 634 aserciones aprobados.
- `python tools\brain\verificar_brain.py`: 0 errores y 1 aviso preexistente por el enlace a ADR-0016 en otra bitácora.
- `git diff --check`: correcto.
- No se accedió a Supabase ni se modificaron datos remotos.

## Decisiones

- Los mensajes de filas C++ mantienen el número de fila y detalle ya generados
  por el lector; el CLI solo los presenta de manera legible.
- La GUI siempre muestra el conteo, incluido cero, para que el resumen tenga
  una forma consistente.

## Pendientes y siguiente paso

- Investigar por separado el texto truncado de la etiqueta en
  `test_zona_soltar_archivo`.
- Continuar con las brechas pendientes de validación temporal y paridad de
  importación.
