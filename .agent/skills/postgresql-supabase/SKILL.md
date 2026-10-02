---
name: postgresql-supabase
description: Usar para esquema, migraciones, RLS, funciones RPC, triggers de revisión, semillas, autenticación, pruebas contra Supabase, llamadas REST desde Python o C++, y para cualquier duda sobre claves, concurrencia, pausa del plan gratuito o respaldos.
---
# PostgreSQL y Supabase en PEA-i

## Proyecto único y modo prueba
- Existe un solo proyecto (pea-prod). "pea-test" significa el mismo proyecto en modo prueba.
- Las pruebas solo tocan filas con `es_ejemplo=true` y prefijo `PRUEBA-`. No se usa la clave secret.
- Antes de proponer un db push: `python tools/db/respaldar.py` y `npx supabase db push --dry-run`. El push real lo aprueba el usuario.

## Llamadas HTTP (iguales en Python y C++)
- Cabecera `apikey` con la clave publishable. Cabecera `Authorization: Bearer <access_token del usuario>`. Con las claves nuevas (`sb_publishable_...`) la publishable va solo en `apikey`, no como Bearer.
- Inicio de sesión: `POST {url}/auth/v1/token?grant_type=password` con correo y clave. Devuelve access_token, refresh_token y expires_in.
- Renovar: `POST {url}/auth/v1/token?grant_type=refresh_token` antes de que venza (por ejemplo al 80% de la vida). Tokens solo en memoria.
- Leer: `GET {url}/rest/v1/<tabla>?select=...&campo=eq.valor`. Operadores: eq, neq, gt, gte, lt, lte, in.(a,b), is.true.
- Paginar: cabeceras `Range-Unit: items`, `Range: 0-999` y `Prefer: count=exact`. La respuesta trae `Content-Range: 0-999/2500`. El tope por defecto es 1000 filas: siempre pagina.
- Escribir: POST para crear con `Prefer: return=representation`. PATCH y DELETE SIEMPRE con filtro (sin filtro afectan todas las filas).
- RPC: `POST {url}/rest/v1/rpc/<funcion>` con los parámetros por nombre en JSON (por ejemplo `p_revision_esperada`).
- Traducir errores a tipos propios: 401 (sesión o clave), 403 (RLS), 404, 409 (duplicado o conflicto de revisión), 400 (parámetro inválido), 429 (límite), 5xx (servidor), sin red y tiempo agotado.

## Esquema y reglas
- Identificadores `bigint generated always as identity`; `activo`, `es_ejemplo`, `creado_en` y `actualizado_en` en todas las entidades; fechas `timestamptz` en ISO-8601; UTF-8.
- FOREIGN KEY con ON DELETE explicado, CHECK para rangos (años), UNIQUE para claves naturales, índices para año, categoría y grupo.
- Migraciones: `npx supabase migration new <nombre>`, solo hacia adelante, una aplicada nunca se edita. `npx supabase migration list` muestra el estado.
- Tras cambiar funciones o tablas, si la API no las ve: `notify pgrst, 'reload schema';`.

## RLS y funciones
- RLS activado en TODAS las tablas. `anon` no lee ni escribe nada y se le revocan los privilegios por defecto. Los usuarios `authenticated` operan sobre las tablas de dominio.
- Políticas con `to authenticated` y `(select auth.uid())` cuando se compare con el usuario.
- Funciones con `security invoker` y `set search_path = ''`. Solo `ping()` la puede ejecutar anon.
- Las RPC de escritura reciben `p_revision_esperada`; si no coincide, lanzan una excepción con un código propio que las apps traducen a "La base de datos cambió".

## Revisión y concurrencia
- Triggers `FOR EACH STATEMENT` en cada tabla de dominio suben `meta.revision`. Los clientes la consultan cada pocos segundos y antes de escribir.
- Operaciones de varias tablas: una función RPC (una transacción del lado de PostgreSQL).

## Continuidad
- El plan gratuito pausa el proyecto tras 1 semana sin actividad: keep-alive programado en `.github/workflows/keep-alive.yml` (llama a `ping()` cada 3 días).
- No hay copias automáticas: respaldo semanal con `tools/db/respaldar.py` (volcado JSON fechado en datos/respaldos/).

## Lista de comprobación
- [ ] Ninguna clave secret ni contraseña de base en código, notas ni ejecutables.
- [ ] Sin sesión, todo es denegado; con sesión, lo previsto.
- [ ] La revisión sube con cada escritura y una RPC con revisión vieja falla.
- [ ] La carga paginada trae TODAS las filas (probar con más de 1000).
- [ ] Python y C++ ven los mismos datos (tools/db/volcar.py y comparar.py).
