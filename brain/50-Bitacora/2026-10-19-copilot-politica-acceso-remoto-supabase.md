---
tipo: bitacora
estado: revisado
creado: 2026-10-19
actualizado: 2026-10-19
relacionado:
  - "[[Contrato-de-datos]]"
  - "[[Seguridad-y-credenciales]]"
origen: "Actualización de reglas del agente solicitada el 2026-10-19"
agente: "Copilot"
rama: "feat/gui-inicio-graficos-copilot"
commit: ""
---

# Bitácora · Política de acceso remoto autorizado a Supabase

## Objetivo
Distinguir en las instrucciones del proyecto las comprobaciones y migraciones rutinarias autorizadas de las operaciones destructivas que requieren una autorización específica.

## Qué se hizo
- Actualizada `.agent/rules/03-base-de-datos.md` con el uso de Supabase CLI bajo sesión autenticada previamente, sin pedir ni revelar credenciales.
- Actualizada la sección de Supabase de `AGENTS.md` con alcance explícito de autorización, comprobaciones previas a migraciones, validación de respaldo, `db push --dry-run`, límites destructivos y verificación posterior.
- Se preservó la regla de que `borrar_datos_ejemplo()` solo lo ejecuta el usuario y nunca las pruebas.
- No se conectó a Supabase ni se ejecutaron comandos remotos o de migración.

## Comandos y resultados
- `git status --short --untracked-files=all`: detectó cambios preexistentes en `.vscode/settings.json`, `brain/.obsidian/graph.json`, `package.json` y `package-lock.json`; se preservaron.
- `git diff --check`: código 0; sin errores de espacios en blanco.
- `.venv\Scripts\python.exe tools\brain\verificar_brain.py`: primera ejecución reportó CRLF en esta nota; tras normalizarla a LF, se volvió a ejecutar para confirmar 0 errores y 0 advertencias.

## Decisiones
- La autorización explícita cubre solo `pea-prod`, la tarea y el alcance indicados; no se extiende a otras operaciones.
- No destructivo excluye borrar/truncar datos, eliminar objetos con datos o debilitar RLS.
- Un respaldo que no pueda demostrarse completo bloquea la aplicación de migraciones.

## Pendientes y siguiente paso
- Ejecutar las validaciones documentales y revisar el diff.
- No realizar cambios remotos: esta tarea solo actualiza instrucciones.
