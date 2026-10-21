---
tipo: bitacora
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[Paridad-Python-Cpp]]"
  - "[[Ingesta]]"
origen: "Comparación diferencial de informes de importación CSV entre Python y C++"
agente: "Copilot"
rama: "feat/python-cierre-francisco"
commit: ""
---

# Bitácora · Informes de importación CSV

## Objetivo

Completar la comparación de los informes CSV de ambos lenguajes, incluyendo
errores por fila, el contrato del servicio y fallos al leer archivos.

## Qué se hizo

- Se alineó el mensaje de éxito del informe C++ con Python y se completó la
  fecha ISO UTC para informes CSV exitosos y fallidos.
- Se unificó el mensaje de archivo inexistente y se probaron informe, advertencia,
  tipo de fuente, contadores, filas omitidas y datos originales de error.
- Se rechazaron años vacíos, no numéricos, menores a 1970 o mayores al año
  actual. La ausencia de la columna de año también genera un error por fila.
- El fixture común verifica los textos en español, acepta los límites 1970 y
  año actual y conserva tres productos válidos mientras omite filas incorrectas.
- Se actualizó la matriz de paridad. La validación del año en otras vías de
  creación y la presentación visible CLI/TUI permanecen pendientes.

## Comandos y resultados

- `.venv\Scripts\python.exe -m pytest -q tests\unit\test_csv_paridad.py tests\unit\test_ingesta.py`:
  18 aprobadas, 1 omitida por configuración.
- `.venv\Scripts\python.exe -m ruff check src\pea\ingesta\lector_csv.py tests\unit\test_csv_paridad.py tests\unit\test_ingesta.py`:
  correcto.
- `cmake --build cpp\build --target pruebas_cpp --parallel 4` y
  `ctest --test-dir cpp\build --output-on-failure`: compilación correcta,
  1/1 suite aprobada.
- `cpp\build\pruebas_cpp.exe --no-version`: 53 casos y 599 aserciones aprobados.
- `python tools\brain\verificar_brain.py`: 0 errores y 1 aviso preexistente
  por el enlace a ADR-0016 en otra bitácora.
- `git diff --check`: correcto.
- No se accedió a Supabase ni se modificaron datos remotos.

## Decisiones

- El texto por fila es un contrato español compartido, independiente de los
  detalles de excepción de Pydantic o de la biblioteca de lectura.
- Python conserva el contenido original de la fila; C++ mantiene el mensaje
  compacto existente. Las pruebas comparan número de fila y mensaje común.
- La validación del rango se aplica aquí al lector CSV conforme al RF-04; no se
  afirma que los demás flujos de creación ya lo validen.

## Pendientes y siguiente paso

- Comparar y alinear los detalles de errores que se muestran en CLI y TUI.
- Revisar los alias/campos restantes del esquema CSV contra el contrato.
- Extender la validación del rango de año a las otras vías de creación de
  productos y agregar pruebas diferenciales.
