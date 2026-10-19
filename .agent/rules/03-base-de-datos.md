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
- El agente puede usar Supabase CLI solo si el usuario ya dejó una sesión autenticada en el entorno. Nunca debe pedir, leer, imprimir ni guardar tokens, contraseñas o claves secretas; las credenciales se gestionan fuera del repositorio.
- Una solicitud que autorice explícitamente cambios remotos en pea-prod permite ejecutar las comprobaciones necesarias y aplicar migraciones no destructivas, sin pedir confirmación para cada comando de esa tarea. La autorización no se extiende a otros proyectos, tareas ni operaciones.
- Antes de aplicar una migración, verificar que el proyecto remoto sea pea-prod, revisar el estado remoto, ejecutar tools/db/respaldar.py y validar que el respaldo esté completo; después ejecutar "npx supabase db push --dry-run" y mostrar los resultados. Si el respaldo no puede demostrarse completo, o el estado/dry-run no coincide con lo esperado, detenerse sin aplicar cambios.
- Una migración no destructiva no borra ni trunca datos, no elimina objetos con datos y no debilita RLS. db reset, borrar datos reales, TRUNCATE, operaciones destructivas y cambios que relajen RLS requieren autorización explícita y específica para esa operación y su alcance. borrar_datos_ejemplo() (borra TODOS los datos de ejemplo) solo lo ejecuta el usuario, nunca las pruebas.
- Las operaciones de datos de la aplicación deben respetar Auth, permisos y las políticas RLS existentes.
- Una operación remota solo se considera completada tras el éxito del comando y la verificación de su resultado en pea-prod.
- meta.revision sube en cada escritura; si cambió, se avisa "La base de datos cambió".
- Sin conexión: se bloquea la escritura y no se muestran datos viejos como actuales.

El contrato completo está en AGENTS.md.
