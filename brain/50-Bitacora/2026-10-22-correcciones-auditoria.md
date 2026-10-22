---
tipo: bitacora
estado: revisado
creado: 2026-10-22
actualizado: 2026-10-22
relacionado:
  - "[[00-Inicio]]"
  - "[[2026-10-19-auditoria-complementaria]]"
  - "[[2026-10-19-auditoria-integral-python-supabase]]"
origen: "Plan de remediación y corrección de hallazgos de auditoría integral PEA-i"
agente: "Antigravity"
rama: "fix/auditoria-2026-10-22"
commit: "0d17144"
---

# Bitácora · Línea base y preparación de correcciones de auditoría

## Objetivo

Preparar el entorno de trabajo, generar el respaldo íntegro de la base de datos de producción Supabase (`pea-prod`) y registrar la línea base de todas las suites y diagnósticos del sistema antes de iniciar las correcciones puntuales de los hallazgos de auditoría.

## Rama de trabajo

- **Rama base:** `master` en commit `0d17144` (*fix: stabilize SCIENTI imports and reporting*).
- **Rama creada para correcciones:** `fix/auditoria-2026-10-22`.
- **Árbol de trabajo:** Limpio, sin modificaciones en código fuente ni archivos de desarrollo.

## Respaldo de la base de datos Supabase

Se ejecutó `tools/db/respaldar.py` utilizando credenciales de solo lectura autenticadas bajo RLS:

- **Archivo de respaldo:** `datos/respaldos/respaldo_20261022_215421_346750.json` (directorio ignorado por Git).
- **Integridad:** SHA-256 `453b2e6fefeb85b937f15872be7fa3b20073cfb78002c3639cbbba641e7571a6`.
- **Total de filas respaldadas:** 6458 filas a través de 20 tablas.
- **Conteos de entidades clave confirmados:**
  - `grupos`: 4 filas
  - `investigadores`: 291 filas
  - `productos`: 2352 filas
  - `integrantes_grupo`: 291 filas
  - `producto_autores`: 2356 filas
  - `producto_grupos`: 1059 filas
- **Tablas secundarias y de metadatos:**
  - `meta`: 1 fila (revisión remota verificada)
  - `grupo_instituciones`: 2 filas
  - `grupo_plan_estrategico`: 1 fila
  - `lineas_investigacion`: 13 filas
  - `proyectos`: 42 filas
  - `semilleros`: 2 filas
  - `investigador_formacion`: 11 filas
  - `investigador_experiencia`: 14 filas
  - `investigador_areas_actuacion`: 2 filas
  - `investigador_idiomas`: 3 filas
  - `investigador_reconocimientos`: 4 filas
  - `investigador_redes_identificadores`: 9 filas
  - `auditoria_cambios`: 0 filas
  - `usuarios_autorizados`: 1 fila

## Línea base de comprobaciones

Se ejecutó y validó la totalidad de herramientas diagnósticas antes de introducir cualquier cambio:

1. **Ruff linter:**
   - Comando: `.\.venv\Scripts\ruff.exe check .`
   - Resultado: 0 advertencias, 0 errores (`All checks passed!`).
2. **Suite de pruebas Python:**
   - Comando: `.\.venv\Scripts\python.exe -m pytest -m "not red"`
   - Resultado: 325 pruebas aprobadas, 3 omitidas por requerir red (`325 passed, 3 deselected`).
3. **Compilación C++:**
   - Directorio: `build/entrega`
   - Comando: `cmake --build build/entrega`
   - Resultado: Compilación limpia sin errores ni advertencias (`-Werror`).
4. **Pruebas unitarias CTest / doctest:**
   - Comando: `ctest --test-dir build/entrega --output-on-failure`
   - Ejecutable: `build/entrega/pruebas_cpp.exe`
   - Resultado: 100% pruebas aprobadas (62 casos de prueba doctest, 862 aserciones).
5. **Autoprueba TUI C++:**
   - Comando: `.\build\entrega\pea-cpp.exe --autoprueba`
   - Resultado: 0 hallazgos en las 32 combinaciones de pantalla y terminal (80x24, 100x28, 120x35, 160x50).
6. **Autoprueba GUI PySide6:**
   - Comando: `.\dist\PEAi-Windows-x64\PEAi-Python\pea-cli.exe --autoprueba-gui`
   - Resultado: 0 hallazgos en las 24 combinaciones de pantalla y resolución (1100x700, 1366x768, 1920x1080).
7. **Verificación cruzada Python/C++:**
   - Comando: `.\dist\PEAi-Windows-x64\PEAi-Python\pea-cli.exe --verificar-cruzada`
   - Resultado: 3 de 3 comprobaciones coincidentes (versión de aplicación, resumen JSON canónico y mutaciones/deshacer).

## Próximos pasos

Iniciar la resolución progresiva de los hallazgos de auditoría en la rama `fix/auditoria-2026-10-22` siguiendo estrictamente la metodología TDD (reproducir con prueba que falle, aplicar cambio mínimo, verificar paridad y confirmar suite completa).
