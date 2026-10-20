---
tipo: bitacora
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[Contrato-de-datos]]"
  - "[[Matriz-cumplimiento-enunciado]]"
origen: "Pruebas locales de paginación, separación de datos y contrato red de conteos"
agente: "Copilot"
rama: "feat/python-cierre-francisco"
commit: ""
---

# Bitácora · Verificación de Supabase

## Objetivo
Probar la paginación sobre más de 1000 filas, evitar mezclar catálogos de
demostración con datos remotos y dejar un contrato explícito para los conteos
reales de `pea-prod`.

## Qué se hizo
- Se amplió la prueba simulada de paginación a 1500 registros.
- La insignia de la GUI muestra «Datos de demostración» o «Datos de Supabase»
  según el modo activo; la prueba confirma que instalar un catálogo remoto
  vacío no conserva filas del catálogo de demostración.
- Se añadió una prueba `red` para los conteos esperados: 1 grupo, 85
  investigadores y 855 productos con `es_ejemplo=false`.
- El contrato solo admite el host de `pea-prod` y nombres de variables
  explícitamente publicables/`anon`; no usa claves `service_role` ni ambiguas.
- La prueba remota se omitió porque el entorno no tenía disponible la sesión
  normal y la clave publicable. No se leyeron archivos de secretos ni se
  consultaron datos remotos.

## Comandos y resultados
- `.venv\Scripts\python.exe -m pytest -q tests\unit\test_resiliencia_persistencia.py -k paginacion_supera`:
  aprobada.
- `python -m pytest -q tests/test_contrato_supabase.py -m red -rs`:
  **1 omitida** por configuración de sesión ausente.
- `.venv\Scripts\python.exe -m ruff check src tests tools scripts`:
  **All checks passed!**

## Decisiones
Los conteos se verifican mediante REST autenticado como usuario normal, con
clave publicable y paginación; no se usa SQL privilegiado. No se modifica la
base remota ni se aplican migraciones.

## Pendientes y siguiente paso
- Cuando el entorno tenga la sesión normal de pruebas y la clave publicable
  configuradas, ejecutar la prueba marcada `red` y comparar los conteos reales.
- Si difieren de los esperados, detenerse y consultar antes de cualquier
  operación remota.
