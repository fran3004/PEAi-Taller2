---
tipo: adr
estado: aprobado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[_Indice]]"
  - "[[Seguridad-y-credenciales]]"
  - "[[Contrato-de-datos]]"
origen: "AGENTS.md y AUDITORIA-DISENO-PEAI.md - Fase 12"
---

# ADR-0008 · Modelo de Autenticación con Supabase Auth y Row Level Security (RLS)

## Contexto
La base de datos PostgreSQL alojada en Supabase expone endpoints públicos HTTPS a través del API Gateway PostgREST. Si no se restringen adecuadamente los permisos, cualquier usuario con la clave pública podría alterar, insertar o eliminar registros de grupos, investigadores o productos sin control.

## Opciones consideradas
1. **Embeber la clave de servicio (`service_role` / `secret key`) en los clientes**: Permite acceso irrestricto sin autenticación de usuario, pero expone el control total de la base de datos a ingeniería inversa del binario ejecutable. Viola gravemente las directrices de seguridad de AGENTS.md.
2. **Autenticación con Supabase Auth y aplicación estricta de Row Level Security (RLS)**: Los clientes utilizan únicamente la clave publicable (`anon key`). La lectura de datos consolidados se permite de forma pública/anónima, mientras que cualquier mutación o escritura requiere una sesión iniciada mediante Supabase Auth con token JWT válido.

## Decisión
Se adopta el **modelo de autenticación con Supabase Auth y Row Level Security (RLS)** formalizado en [[Seguridad-y-credenciales]] y [[Contrato-de-datos]].
Queda prohibido incluir claves secretas (`service_role`) en cualquier ejecutable, script de cliente o archivo de configuración distribuido. Las políticas RLS protegen todas las tablas y restringen las operaciones de inserción, actualización y borrado a usuarios autenticados autorizados.

## Consecuencias
- **Positivas**: Máxima seguridad defensiva; imposibilidad de secuestro de la base de datos mediante decompilación del cliente; trazabilidad de autoría de cambios.
- **Costos**: La aplicación cliente debe gestionar el flujo de inicio de sesión, almacenamiento seguro de tokens y renovación de credenciales.
