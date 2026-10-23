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

## Corrección 1: Validación de rango de año en entidad Producto (esquema Supabase)

- **Problema:** En `src/pea/dominio/producto.py`, la entidad `Producto` aceptaba cualquier año (por ejemplo 1800), fallando únicamente en persistencia si Supabase rechazaba el valor por la restricción `CHECK (ano >= 1970 AND ano <= 2100)`.
- **Acciones realizadas:**
  1. **TDD:** Se crearon pruebas unitarias en `tests/unit/test_dominio_producto.py` reproduciendo la falla con años 1800, 1969 y 2101, validando aceptación de 1970 y 2100, y rechazo de tipos no enteros o booleanos (`True`/`False`).
  2. **Modelo de dominio:** Se definieron las constantes `ANO_MINIMO_BASE = 1970` y `ANO_MAXIMO_BASE = 2100` (`ANO_MINIMO_PRODUCTO` / `ANO_MAXIMO_PRODUCTO`), y se añadió `@field_validator("ano", mode="before")` en `Producto` alineado con la base de datos sin restringir al año actual en el modelo. Se conservó `validar_ano_producto` con el límite del año actual para flujos de ingesta/importación.
  3. **Manejo en GUI / Servicio de Aplicación:** Se mejoró `_mensaje_validacion` en `servicio_aplicacion.py` para traducir `ValidationError` de Pydantic a `ErrorValidacion` con mensajes amables y claros en español ante formularios con campos inválidos.
  4. **Paridad Python/C++:** Se verificó que en C++ `validar_ano_producto` valida enteros y el rango 1970 a año actual en el catálogo, mientras `Producto` en Python valida contra el esquema de base de datos (1970-2100). Se añadió prueba de paridad de casos compartidos en `test_dominio_producto.py`.
- **Resultados de validación:**
  - `ruff check .`: Limpio (0 errores).
  - `pytest -m "not red"`: 332 aprobadas, 3 omitidas.
  - C++ build y CTest: 100% aprobado (62 casos doctest, 862 aserciones).
  - `pea-cpp --autoprueba`: 0 hallazgos en 32 pantallas.
  - `pea-cli --autoprueba-gui`: 0 hallazgos en 24 combinaciones de pantalla.
  - `pea-cli --verificar-cruzada`: 3 de 3 comprobaciones coincidentes.

## Corrección 2: Control de revisión remota estricto y detección de pérdida de conexión

- **Problema:** En `src/pea/datos/revision.py`, `ControladorRevision.consultar_remota` devolvía `self._revision_local` cuando tanto la RPC rápida como la consulta REST a `meta` fallaban o devolvían valores inválidos (por ejemplo, lista vacía o `.get("revision", 1)`). Esto causaba un falso éxito en `verificar_consistencia` simulando sincronización cuando no había conectividad.
- **Acciones realizadas:**
  1. **TDD:** Se crearon pruebas unitarias en `tests/unit/test_revision_remota.py` con un cliente falso para los 4 casos: (a) RPC exitosa devuelve valor; (b) RPC fallida pero meta exitosa devuelve meta; (c) RPC y meta fallidas lanza `ErrorConexion` detallando ambos fallos; (d) meta vacía, nula o revisión no positiva lanza `ErrorConexion`.
  2. **Paridad Python/C++:** Se implementó `_revision_valida` y se refactorizó `consultar_remota` para exigir enteros mayores que cero y lanzar `ErrorConexion` con la misma estructura diagnóstica de C++ (`cpp/src/datos/revision.cpp`). Se añadió caso de prueba idéntico en C++ (`cpp/tests/test_resiliencia.cpp`).
  3. **Manejo en GUI y CLI:** Se añadieron pruebas en `tests/unit/test_revision_sin_conexion.py` verificando el comportamiento sin red de los llamadores (`cli.py`, `servicio_aplicacion.py`, `servicio_dominio.py`). En `ventana_principal.py`, se conectó `actualizar_estado_global()` en el callback de la verificación periódica para desplegar la franja roja de sin conexión y bloquear escrituras sin congelar la ventana.
  4. **Modo demostración y resiliencia:** Se verificó que el modo demo utiliza `_revision_demo_remota` sin consultar la red y que `test_resiliencia_persistencia.py` mantiene el 100% de aprobación.
  5. **Prueba manual con Supabase real y corte simulado:** Se comprobó conexión real obteniendo la revisión remota vigente (revisión 4368) y se simuló caída de red validando la captura inmediata de `ErrorConexion`, activación de `sin_conexion = True` y motivo de bloqueo de mutaciones.
- **Resultados de validación:**
  - `ruff check .`: Limpio (0 errores).
  - `pytest -m "not red"`: 362 aprobadas, 3 omitidas.
  - C++ build y CTest: 100% aprobado (63 casos doctest, 879 aserciones).
  - `pea-cpp --autoprueba`: 0 hallazgos en 32 pantallas.
  - `pea-cli --autoprueba-gui`: 0 hallazgos en 24 combinaciones de pantalla.
  - `pea-cli --verificar-cruzada`: 3 de 3 comprobaciones coincidentes.

## Próximos pasos

Continuar con la resolución progresiva de los siguientes hallazgos de auditoría en la rama `fix/auditoria-2026-10-22` siguiendo estrictamente la metodología TDD.

