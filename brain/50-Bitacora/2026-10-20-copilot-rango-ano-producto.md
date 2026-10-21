---
tipo: bitacora
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[SPEC]]"
  - "[[Paridad-Python-Cpp]]"
agente: "Copilot"
rama: "feat/python-cierre-francisco"
origen: "Aplicación del rango temporal normativo de RF-04 en alta y edición de productos"
commit: ""
---

# Bitácora · Rango de año de producto

## Objetivo

Aplicar el criterio RF-04 a las rutas de creación y actualización, además del
lector CSV, con el mismo límite en Python y C++.

## Qué se hizo

- Se cambió el rango de la fachada Python de 1900–año siguiente a
  1970–año actual.
- El catálogo Python valida antes de insertar o mutar, incluyendo la edición
  directa y valores no enteros.
- El catálogo C++ aplica el mismo límite al crear y editar productos; una
  edición rechazada no deja cambios parciales.
- Los formularios Python muestran el rango permitido; si se edita un registro
  histórico inválido, el diálogo informa y exige corregirlo.
- Los campos de año de creación y edición en la TUI C++ también muestran los
  límites dinámicos.
- Se actualizaron las pruebas diferenciales, el diseño de productos y esta
  matriz de paridad.

## Comandos y resultados

- `.venv\Scripts\python.exe -m pytest -q tests\unit\test_servicios_nuevos.py tests\unit\test_tabla_ficha_dialogos.py`: 31 aprobadas.
- `.venv\Scripts\python.exe -m ruff check src\pea\dominio\producto.py src\pea\servicios\servicio_dominio.py src\pea\servicios\servicio_aplicacion.py src\pea\gui\dialogos.py tests\unit\test_servicios_nuevos.py tests\unit\test_tabla_ficha_dialogos.py`: correcto.
- `cmake --build cpp\build --parallel 4` y `ctest --test-dir cpp\build --output-on-failure`: aplicación y pruebas compiladas; 1/1 suite aprobada.
- `cpp\build\pruebas_cpp.exe --no-version`: 57 casos y 647 aserciones aprobados.
- `python tools\brain\verificar_brain.py`: 0 errores y 1 aviso preexistente por el enlace a ADR-0016 en otra bitácora.
- `git diff --check`: correcto.
- No se accedió a Supabase ni se modificaron datos remotos.

## Decisiones

- El rango se toma de RF-04: entero desde 1970 hasta el año calendario actual,
  ambos inclusive. No se conserva el margen previo de un año futuro.
- Las consultas pueden seguir leyendo datos existentes; la regla se impone en
  los servicios de escritura sin añadir una migración remota.
- La migración inicial conserva un `CHECK` superior fijo en 2100. Por eso, un
  cliente que escribiera directamente por API sin pasar por estos servicios
  tendría un límite menos estricto; se registra como brecha de integridad SQL.

## Pendientes y siguiente paso

- Para cerrar la brecha de integridad directa, evaluar una migración nueva con
  verificación dinámica del año y validarla en el proceso autorizado antes de
  aplicarla a `pea-prod`.
