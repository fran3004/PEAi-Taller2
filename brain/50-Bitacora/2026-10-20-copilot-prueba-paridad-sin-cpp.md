---
tipo: bitacora
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[GUI-Diseno-Python]]"
origen: "Aislamiento de la prueba de verificacion cruzada respecto al ejecutable C++"
agente: "Copilot"
rama: "feat/python-cierre-francisco"
commit: ""
---

# Prueba de paridad sin dependencia de C++

## Objetivo
Evitar que la prueba unitaria de verificacion cruzada dependa de compilar
previamente el ejecutable C++, y aclarar su ausencia en Configuracion.

## Que se hizo
- La prueba unitaria usa un ejecutor simulado y exige exactamente tres filas
  con resultado `COINCIDEN`.
- Se agrego una prueba `cpp` que ejecuta el binario real solo cuando existe.
- Si no hay binario, la interfaz muestra `C++ no compilado`, la ruta esperada y
  la variable `PEA_CPP_EXE`.
- Se registro el marcador `cpp` en `pytest.ini`.

## Comandos y resultados
- `pytest tests\unit\test_pantallas_finales.py -q`: 11 pasaron.
- `ruff check tests\unit\test_pantallas_finales.py src\pea\gui\pantallas\configuracion.py`:
  aprobado.
- `git diff --check`: aprobado.

## Decisiones
La prueba de paridad normal no invoca procesos reales; se mantiene una prueba
separada para el binario C++ y se omite cuando no existe.

## Pendientes y siguiente paso
Continuar con el formato de años e identificadores de las tablas.
