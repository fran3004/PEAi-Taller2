---
tipo: adr
estado: aprobado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[Arquitectura]]"
  - "[[TUI-Diseno-Cpp]]"
  - "[[Paridad-Python-Cpp]]"
  - "[[ADR-0009-RPC-y-control-de-revision-optimista]]"
  - "[[ADR-0019-Cpp-terminal-con-ftxui]]"
origen: "Implementación de la consulta periódica de revisión remota en la TUI C++"
numero: ADR-0020
decision: "Consultar la revisión periódicamente con un cliente HTTPS propio del hilo trabajador, notificar a FTXUI mediante eventos y reportar los errores sin usar la revisión local como fallback"
---

# ADR-0020 · Revisión remota periódica en C++

## Contexto

La TUI C++ solo verificaba la revisión remota al recargar o antes de algunas
escrituras. Esto podía dejar visible un catálogo obsoleto mientras otra sesión
modificaba la base. La consulta HTTPS síncrona tampoco debe ejecutarse en el
hilo de interfaz, ni un trabajador puede leer el catálogo mutable.

## Opciones consideradas
1. Consultar desde el hilo TUI: sencilla, pero bloquea el renderizado durante
   operaciones de red.
2. Compartir el cliente HTTP y el catálogo con un hilo trabajador: evita
   bloquear la interfaz, pero expone objetos con afinidad de hilo y datos
   mutables a carreras.
3. Crear un cliente HTTPS exclusivo del trabajador y devolver solo resultados
   inmutables mediante eventos: evita compartir el cliente y el catálogo, a
   cambio de tener un protocolo de parada y sincronización. **Elegida.**

## Decisión

Mientras la TUI está conectada, un hilo consulta la revisión cada 30 segundos
con un `ClienteHTTPSupabase` propio. Copia al iniciar la configuración de URL,
clave publicable y token de acceso en memoria; no lee ni modifica el catálogo.
El resultado o error se comunica con `Event::Custom`, y la comparación con la
revisión local y el mensaje de estado ocurren en el hilo de interfaz.

La consulta solo se considera válida si devuelve una revisión positiva por RPC
o por `meta`. Si ambos mecanismos fallan o devuelven contenido inválido, se
propaga `ErrorConexion`; nunca se presenta la revisión local como si fuera una
lectura remota. Al salir, se señala la parada, se despierta el trabajador y se
le hace `join`.

## Consecuencias

- La interfaz detecta cambios remotos sin bloquearse por la consulta periódica
  y solicita una recarga explícita con `r`.
- Los errores de red o autenticación quedan visibles; un token vencido no se
  renueva automáticamente y se vuelve a intentar en el ciclo siguiente.
- El hilo tiene un cliente Qt Network propio; al cerrar la TUI, una solicitud
  en curso puede demorar el cierre hasta el timeout HTTP.
- La ingesta interactiva permanece síncrona y fuera del alcance de esta
  decisión. La interacción del ciclo de vida y la expiración de token aún
  requieren pruebas de integración.
