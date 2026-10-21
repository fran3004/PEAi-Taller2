---
tipo: bitacora
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[GUI-paridad]]"
  - "[[TUI-Diseno-Cpp]]"
  - "[[Paridad-Python-Cpp]]"
  - "[[ADR-0021-Actualizacion-atomica-grupo-producto]]"
origen: "Paridad de edición de producto entre los servicios Python y C++"
agente: "Copilot"
rama: "feat/python-cierre-francisco"
commit: ""
---

# Bitácora · Edición del grupo de producto en C++

## Objetivo

Cerrar la diferencia registrada entre Python y C++ al editar el grupo asociado
a un producto, conservando estructuras enlazadas, deshacer, compensación y
persistencia atómica.

## Qué se hizo

- Se añadió a `Multilista` la reasignación/desvinculación de un grupo y el
  mantenimiento de los enlaces intragrupo.
- `CatalogoInvestigacion::actualizar_producto()` acepta `codigo_grupo` y sus
  alias existentes, comprueba el grupo, actualiza la multilista, sincroniza el
  hipercubo y permite deshacer o revertir un fallo de persistencia.
- El formulario TUI permite asignar un grupo nuevo o quitar el actual.
- Se añadió el contrato de repositorio para una RPC que actualiza producto y
  relación en una sola transacción con la revisión esperada.
- Se creó la migración 004 con `SECURITY INVOKER`, verificación de revisión y
  respuesta con la revisión posterior a los triggers. La migración no se
  aplicó a `pea-prod`.
- Se documentó la decisión en [[ADR-0021-Actualizacion-atomica-grupo-producto]]
  y se actualizó la matriz de paridad.

## Comandos y resultados

- Build independiente C++ en `%TEMP%\pea-taller2-export-qa`: correcto;
  `ctest --test-dir ... --output-on-failure`: 1/1 suite aprobada.
- `pruebas_cpp.exe --no-version`: 43 casos y 472 aserciones aprobados.
- `pea-cpp.exe --autoprueba`: 32 combinaciones de pantalla/tamaño y todos los
  formularios verificados sin hallazgos.
- `.venv\Scripts\python.exe -m pytest tests\unit\test_servicios_nuevos.py -k
  actualizar_producto -q`: 4 pruebas aprobadas y 10 omitidas por el selector.
- `python tools\brain\verificar_brain.py`: 160 notas, 0 errores y 1 aviso
  preexistente por el enlace `ADR-0016` en otra bitácora.
- `git diff --check`: correcto.
- La migración SQL no se ejecutó en base local ni remota. Se requiere
  autorización explícita y el protocolo de respaldo/dry-run para cualquier
  despliegue en `pea-prod`.

## Decisiones

- No se hacen escrituras REST encadenadas para cambiar una relación de varias
  tablas.
- La función SQL conserva RLS de invocador y no usa claves privilegiadas.
- El cambio local revierte si la verificación de revisión o la RPC falla.

## Pendientes y siguiente paso

- Ejecutar las pruebas de C++ y renderizado TUI.
- Aplicar la migración únicamente después de la autorización y comprobaciones
  remotas exigidas por el contrato del proyecto.
- Agregar una prueba de integración autenticada de la RPC cuando exista un
  entorno aprobado para ello.
