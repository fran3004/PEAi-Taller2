---
tipo: bitacora
estado: revisado
creado: 2026-10-19
actualizado: 2026-10-19
relacionado:
  - "[[00-Inicio]]"
origen: "Trabajo local e integración autorizada de Supabase"
agente: "Copilot"
rama: "feat/gui-inicio-graficos-copilot"
commit: "Incluido en el commit que incorpora esta bitácora"
---

# Bitácora · Respaldo e integración Supabase

## Objetivo

Corregir la generación del respaldo de Supabase para que no declare éxito ante respuestas incompletas, completar la lectura de membresías cuyos códigos están en las entidades relacionadas y validar la integración disponible sin exponer credenciales ni modificar datos reales.

## Qué se hizo

- Se reforzó `tools/db/respaldar.py`: autenticación de usuario normal, rechazo de claves secretas, fallos explícitos ante HTTP/red/JSON, exigencia de paginación y conteos exactos, lectura de las diez tablas (incluida `auditoria_cambios`), revisión `meta.revision` antes/después, verificación de integridad y publicación atómica.
- Se ajustó `tools/db/volcar.py` para reutilizar el flujo autenticado y la paginación validada.
- Se añadieron pruebas de respaldo para respuestas HTTP fallidas, autenticación, páginas incompletas, tabla de auditoría y revisión inconsistente.
- Se corrigió la carga de membresías Python y C++: PostgREST devuelve `grupo_id` e `investigador_id`, por lo que los códigos de dominio se resuelven mediante las relaciones `grupos` e `investigadores`.
- Se corrigió el orden de inicialización de `QCoreApplication` en la CLI C++ para permitir el comando de verificación.
- Se añadieron pruebas unitarias para la conversión de relaciones anidadas en ambos lenguajes.
- No se aplicaron migraciones. La última comprobación remota previa indicó que el historial local y remoto coincidía y que el `db push --dry-run` no tenía migraciones pendientes.
- Se preservaron los cambios preexistentes de `.vscode/settings.json`, `brain/.obsidian/graph.json`, `package.json` y `package-lock.json`; no forman parte de este trabajo.

## Comandos y resultados

- `npx --no-install supabase --version` → Supabase CLI `2.117.0`.
- `npx supabase projects list` → sesión CLI autenticada; proyecto vinculado `pea-prod`.
- `npx supabase migration list --linked` → las versiones `20261003055532` y `20261003061247` coinciden en local y remoto.
- `npx supabase db push --dry-run --linked` → código 0; remoto al día, sin migraciones pendientes. No se ejecutó `db push`.
- `npx supabase db diff --linked --schema public` y `npx supabase db dump --linked --schema public` → bloqueados por ausencia de Docker/Podman; no se verificó independientemente el drift completo del esquema.
- `python tools/db/respaldar.py` → respaldo completado previamente para diez tablas y trece filas visibles bajo RLS; `meta.revision` fue 18 antes y después. `auditoria_cambios` devolvió cero filas visibles. Esta evidencia cubre lo autorizado por RLS para el usuario, no filas no visibles para él.
- Prueba REST/RPC previa con `ClienteHTTPSupabase` → autenticación normal, `ping` y CRUD de un grupo sintético `PRUEBA-*` completados; se verificó su eliminación. La prueba de escritura fue limitada a ese registro de prueba.
- Prueba remota actual con `ServicioAplicacion` → detenida antes de conectar (código 2): faltan en el entorno variables de conexión/autenticación. No se leyó `.env`, no se pidió ni mostró ninguna credencial y no se intentó acceso alternativo.
- `.venv\Scripts\python.exe -m pytest -q tests/unit/test_repositorio_integrantes.py tests/unit/test_servicios_nuevos.py tests/unit/test_respaldar_db.py` → 26 pruebas aprobadas.
- `.venv\Scripts\ruff.exe check src/pea/datos/repositorios.py tests/unit/test_repositorio_integrantes.py tools/db/respaldar.py tools/db/volcar.py tests/unit/test_respaldar_db.py` → `All checks passed!`.
- `cmake --build cpp/build --config Release` → compilación correcta.
- `ctest --test-dir cpp/build --output-on-failure` → 1/1 prueba aprobada.
- `python -m pytest ...` y `python -m ruff ...` con el Python MSYS del PATH → no disponibles en ese intérprete; se repitieron correctamente con el entorno virtual existente.
- Intérprete disponible: Python 3.14.6 en `.venv` y Python 3.14.7 en el PATH; no se encontró Python 3.12, por lo que no se certificó esa versión.

## Decisiones

- El respaldo no se considera completo por recibir un HTTP exitoso: exige `Content-Range`, totalidad de filas visibles por RLS, conteos estables y revisión de base estable.
- Una falla de autenticación o falta de variables locales bloquea la integración; no se recurre a claves secretas, credenciales incrustadas ni acceso alternativo.
- No se ejecutaron comandos destructivos ni operaciones sobre filas reales. La eliminación de la fila de prueba previa fue parte de la prueba autorizada y se verificó.
- No se aplicaron migraciones, porque no había migraciones pendientes.

## Pendientes y siguiente paso

- Repetir la carga remota de `ServicioAplicacion` cuando el entorno de ejecución tenga configuradas las variables locales necesarias, sin compartirlas por chat. En esta sesión no se verificó el CRUD del servicio tras la corrección reciente.
- Comparar el esquema remoto íntegro contra las migraciones cuando Docker o Podman estén disponibles.
- No se verificó CRUD autenticado desde la GUI C++: la aplicación C++ continúa sin flujo gráfico de autenticación/CRUD. El ping de CLI probado no equivale a esa evidencia.
- El respaldo es exacto para filas visibles por RLS, no acredita acceso a filas que el usuario autenticado no puede consultar.
