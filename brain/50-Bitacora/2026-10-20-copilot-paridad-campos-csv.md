---
tipo: bitacora
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[Paridad-Python-Cpp]]"
  - "[[Ingesta]]"
origen: "Revisión de alias, campos opcionales y validación de filas CSV"
agente: "Copilot"
rama: "feat/python-cierre-francisco"
commit: ""
---

# Bitácora · Paridad de campos CSV

## Objetivo

Comparar los alias y campos extendidos de CSV en Python y C++ contra el
esquema documentado y cerrar diferencias comprobables sin inventar una
conversión de categorías.

## Qué se hizo

- Python ahora normaliza los encabezados sin distinguir mayúsculas, igual que
  C++; se verificaron los cuatro tipos de archivo.
- Se preserva `PRODUCTO.detalles` como objeto JSON en los dos lectores y ambos
  rechazan contenido JSON que no represente un objeto.
- Se alinearon valores booleanos (`si`/`sí`, `t`/`f`, valores comunes y campos
  vacíos con el valor predeterminado).
- C++ ahora rechaza el orden de autoría vacío/no numérico en lugar de
  sustituirlo silenciosamente por `1`; ambos usan `1` cuando falta la columna.
- Se documentaron alias y campos opcionales de los formatos CSV en `Ingesta`.
- Se registró que `tipo_categoria` del ejemplo no es semánticamente equivalente
  a las cuatro tipologías mayores de RF-04. No se añadió una transformación
  especulativa.

## Comandos y resultados

- `.venv\Scripts\python.exe -m pytest -q tests\unit\test_csv_paridad.py tests\unit\test_ingesta.py`:
  19 aprobadas, 1 omitida por configuración.
- `.venv\Scripts\python.exe -m ruff check src\pea\ingesta\lector_csv.py src\pea\ingesta\modelos.py tests\unit\test_csv_paridad.py tests\unit\test_ingesta.py`:
  correcto.
- `cmake --build cpp\build --target pruebas_cpp --parallel 4` y
  `ctest --test-dir cpp\build --output-on-failure`: compilación correcta,
  1/1 suite aprobada.
- `cpp\build\pruebas_cpp.exe --no-version`: 54 casos y 630 aserciones aprobados.
- `git diff --check`: correcto.
- `python tools\brain\verificar_brain.py`: 0 errores y 1 aviso preexistente
  por el enlace a ADR-0016 en otra bitácora.
- No se accedió a Supabase ni se modificaron datos remotos.

## Decisiones

- Se conserva la extensión `detalles` porque existe en el esquema PostgreSQL
  como JSONB y C++ ya la importaba; Python no debe descartarla.
- Se mantiene el conjunto booleano de C++ y se amplía la compatibilidad de
  Python, sin invalidar los valores que ya aceptaba Pydantic.
- El orden solo debe ser entero; la positividad no se impone porque no está
  declarada en el contrato.

## Pendientes y siguiente paso

- Resolver la semántica de `tipo_categoria` frente a RF-04 con la fuente
  normativa del Modelo antes de convertir valores.
- Comparar los errores que CLI y TUI presentan al usuario.
- Aplicar la validación del rango anual a las otras vías de creación de
  productos.
