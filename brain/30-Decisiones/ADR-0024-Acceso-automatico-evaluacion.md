---
tipo: adr
estado: revisado
creado: 2026-10-21
actualizado: 2026-10-21
relacionado:
  - "[[00-Inicio]]"
  - "[[ADR-0023-Entrega-reproducible-Windows]]"
  - "[[Seguridad-y-credenciales]]"
origen: "El usuario exige cero configuracion y autoriza acceso a los datos reales de pea-prod"
numero: 24
decision: "Sesion temporal de Auth, configuracion publica incluida y datos reales protegidos"
---

# ADR · Acceso automático de evaluación

> Decisión sustituida por [[ADR-0025-Acceso-academico-completo]] a petición explícita
> del usuario. Se conserva como evidencia de la alternativa protegida evaluada.

## Contexto

El profesor debe abrir los ejecutables sin escribir claves, contraseñas ni comandos.
El usuario autorizó acceder a los datos reales y proporcionó exclusivamente una
clave publicable. El repositorio ya es público: cualquier descargador puede obtener
esa misma clave. La sesión administrativa de la CLI no se distribuye.

## Opciones consideradas

1. Incluir una cuenta y contraseña: expone credenciales, se descarta.
2. Sesiones anónimas sin restricciones: daría permisos generales a cualquier visitante,
   se descarta para proteger los datos reales.
3. Sesiones anónimas de Auth con lectura real y escritura de evaluación protegida.

## Decisión

Se adopta la opción 3. El paquete contiene URL, clave publicable y un indicador de
evaluación. Python y C++ lo buscan junto a la distribución, sin depender del directorio
actual. Obtienen una sesión temporal por HTTPS; sus tokens solo permanecen en RAM.
`anon` no gana permisos de escritura: se mantienen Auth y RLS.

Antes de habilitar sesiones anónimas se aplican restricciones de escritura adicionales
para `is_anonymous=true`: solo entidades `es_ejemplo=true` con código `PRUEBA-` y sus
relaciones permitidas. Un trigger también rechaza modificaciones de filas reales,
incluidas cascadas, para evitar falsos éxitos de DELETE que no afectan ninguna fila.
Los servicios marcan automáticamente las nuevas entidades creadas en este modo.
Los usuarios permanentes conservan los permisos existentes.

La migración 006 registra las cuentas permanentes existentes en `usuarios_autorizados`
y exige esa autorización para cuentas permanentes. Esto evita que un visitante
eluda la protección creando una cuenta nueva o vinculando correo a su sesión anónima.
La tabla no permite altas desde el cliente. Una futura cuenta institucional requiere
autorización administrativa explícita; no se distribuyen identificadores de usuarios.

El respaldo previo usa `tools/db/respaldar.py --cli` y la sesión existente de la CLI
por Management API HTTPS. Comprueba inventario completo, conteos, paginación, revisión
estable y checksum, sin leer `.env` ni extraer tokens. Esta vía es administrativa;
las aplicaciones siguen usando exclusivamente REST/RPC.

## Consecuencias

- El profesor consulta datos reales sin configurar nada y evalúa cambios con registros
  de prueba persistidos en el mismo Supabase. No puede editar/borrar registros reales.
- La configuración pública no es una barrera de seguridad; la protección está en la base.
- Los registros de evaluación se comparten entre sesiones; no contienen datos privados.
- Se necesita Internet y Supabase disponible. Sus límites de Auth siguen aplicándose.
- La distribución pública haría accesibles los datos de lectura a otros descargadores;
  se solicitó autorización explícita antes de habilitarla. No se publican respaldos en Git.
- Referencia: [sesiones anónimas de Supabase](https://supabase.com/docs/guides/auth/auth-anonymous).
