---
trigger: always_on
description: Reglas de la base de datos Supabase/PostgreSQL de un solo proyecto
---
# Base de datos
- La base es PostgreSQL en Supabase. No existe base local (nada de SQLite ni de datos/pea.db).
- Las aplicaciones solo usan HTTPS (REST/RPC). Nunca se conectan al puerto de PostgreSQL.
- Las migraciones de supabase/migrations/ son la única fuente del esquema. Una migración aplicada no se edita.
- Seguridad con Auth y RLS. Los clientes usan solo la clave publishable; la clave secret no se usa en ningún lugar.
- Existe UN solo proyecto (pea-prod). "pea-test" significa el mismo proyecto en modo prueba: solo filas es_ejemplo=true con prefijo PRUEBA-.
- Antes de proponer un db push: respaldo con tools/db/respaldar.py y "npx supabase db push --dry-run". El push real lo confirma el usuario.
- meta.revision sube en cada escritura; si cambió, se avisa "La base de datos cambió".
- Sin conexión: se bloquea la escritura y no se muestran datos viejos como actuales.

El contrato completo está en AGENTS.md.
