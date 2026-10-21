---
tipo: bitacora
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[Paridad-Python-Cpp]]"
origen: "Corrección y comparación del contrato JSON de las vistas estadísticas"
agente: "Copilot"
rama: "feat/python-cierre-francisco"
commit: ""
---

# Bitácora · Paridad de vistas estadísticas

## Objetivo

Comparar el contrato JSON de las vistas institucional, grupal e individual en
Python y C++ con un único fixture compartido.

## Qué se hizo

- Se capturó la salida real de las vistas Python con tres productos, dos grupos,
  dos investigadores con productos y un investigador sin productos.
- La comparación evidenció que C++ omitía `distribucion_productos_por_investigador`
  en las vistas institucional y grupal y emitía el top 5 como objetos en lugar
  de pares JSON, que es el contrato Python.
- Se añadieron los campos de distribución a ambas vistas C++ y se alineó la
  representación de top 5 a pares `[código, cantidad]`.
- Python y C++ ahora construyen sus resultados desde
  `cpp/tests/fixtures/vistas_analiticas.json`; la igualdad cubre campos,
  agregaciones, porcentajes, histogramas, contribuciones y forma JSON.

## Comandos y resultados

- `.venv\Scripts\python.exe -m pytest -q tests\unit\test_vistas_paridad.py`:
  1 prueba aprobada.
- Build C++ focalizado y CTest: correctos; 1/1 suite aprobada.
- `pruebas_cpp.exe --no-version`: 52 casos y 510 aserciones aprobados.
- `.venv\Scripts\python.exe -m pytest -q tests\unit\test_vistas_paridad.py tests\unit\test_hipercubo.py`:
  14 pruebas aprobadas.
- `pea-cpp.exe --autoprueba`: 32 combinaciones de pantalla/tamaño y formularios,
  sin hallazgos.
- `git diff --check`: correcto.
- Sin conexiones a Supabase ni modificaciones remotas.

## Decisiones

- El contrato Python existente se toma como referencia, incluidos los pares
  serializados como arreglos JSON y los rangos de investigadores.
- El fixture incluye a un investigador sin productos para verificar el rango
  cero en las vistas agregadas.

## Pendientes y siguiente paso

- Contrastar con fixtures diferenciales el resto de las estadísticas y probar
  la equivalencia de filtros temporales por rangos explícitos.
