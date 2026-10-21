---
tipo: bitacora
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[Paridad-Python-Cpp]]"
origen: "Paridad de rangos anuales explícitos en vistas estadísticas C++"
agente: "Copilot"
rama: "feat/python-cierre-francisco"
commit: ""
---

# Bitácora · Rango temporal en vistas C++

## Objetivo

Completar el filtro de rango temporal explícito en las vistas estadísticas
C++, con semántica y salida equivalentes a Python.

## Qué se hizo

- Se añadieron `anioInicio` y `anioFin` opcionales a las vistas institucional,
  grupal e individual de `ServicioEstadisticas`.
- `resolverCubo` aplica los filtros en el orden de Python: Modelo 2024, rango
  explícito, ventana de últimos años y, en otro caso, catálogo completo.
- El fixture común incorpora la salida exacta para el intervalo cerrado
  2023–2023 y ambos lenguajes la comparan en las tres vistas.
- Se probaron siete escenarios: intervalo cerrado, inicio abierto, fin abierto,
  límites invertidos, últimos cinco años, Modelo 2024 prioritario y rango
  explícito prioritario sobre últimos años.
- El contrato continúa calculando conteos desde el hipercubo; no se añadieron
  consultas agregadas ni acceso remoto.

## Comandos y resultados

- Build C++ focalizado y CTest: correctos; 1/1 suite aprobada.
- `pruebas_cpp.exe --no-version`: 52 casos y 555 aserciones aprobados.
- `.venv\Scripts\python.exe -m pytest -q tests\unit\test_vistas_paridad.py`:
  1 prueba aprobada.
- `.venv\Scripts\python.exe -m ruff check tests\unit\test_vistas_paridad.py`:
  todos los chequeos aprobados.
- `pea-cpp.exe --autoprueba`: 32 combinaciones de pantalla/tamaño y formularios,
  sin hallazgos.
- `git diff --check`: correcto.
- Sin conexiones a Supabase ni modificaciones remotas.

## Decisiones

- Se conserva la forma de los métodos existentes y se añaden límites
  opcionales; los argumentos ausentes no alteran el comportamiento anterior.
- El filtro explícito tiene prioridad sobre `ventanaAnios`, igual que en
  `_resolver_cubo` de Python, y Modelo 2024 conserva la prioridad normativa.

## Pendientes y siguiente paso

- Ampliar la prueba diferencial a intervalos abiertos, límites invertidos,
  ventana de últimos años y Modelo 2024 en cada vista.
