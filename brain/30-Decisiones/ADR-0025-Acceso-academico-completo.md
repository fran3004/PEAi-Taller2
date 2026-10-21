---
tipo: adr
estado: aprobado
creado: 2026-10-21
actualizado: 2026-10-21
relacionado:
  - "[[00-Inicio]]"
  - "[[ADR-0024-Acceso-automatico-evaluacion]]"
  - "[[Seguridad-y-credenciales]]"
origen: "El usuario solicita expresamente acceso a todos los datos sin limitaciones para la calificacion"
numero: 25
decision: "Acceso academico automatico con los permisos originales de authenticated"
---

# ADR · Acceso académico completo

## Contexto

Tras explicar que cualquier descargador tendría los mismos permisos, el propietario
rechazó las limitaciones del [[ADR-0024-Acceso-automatico-evaluacion]] y solicitó que
el profesor tuviera acceso completo a los datos reales. Indicó que el destino es
exclusivamente la calificación académica y que acepta el alcance de privacidad.

## Opciones consideradas

1. Lectura real y escritura solo de evaluación: rechazada por el usuario.
2. Credenciales personales: contradice la exigencia de cero configuración.
3. Sesión automática con los permisos de las cuentas normales: elegida por el usuario.

## Decisión

La migración 007 retira las restricciones añadidas por 005/006 y conserva las
políticas authenticated originales. No elimina filas ni desactiva RLS. Auth genera
sesiones temporales sin contraseña incorporada; URL y clave publicable acompañan
los ejecutables. Los clientes renuevan la sesión sin escribir tokens en disco.

El profesor puede crear, modificar, desactivar, eliminar, importar y exportar según
las funciones implementadas de cada aplicación. Los servicios no fuerzan prefijos
ni convierten los registros ingresados por el usuario en datos de ejemplo.

## Consecuencias

- El programa no identifica exclusivamente al profesor: cualquier persona con el
  paquete y conexión puede disponer de los mismos permisos sobre los datos reales.
- Esto es una decisión académica explícita, no una configuración recomendada para
  producción ni para proteger información privada. Existe riesgo de modificación
  o eliminación por terceros; el respaldo local previo permite recuperación manual.
- Las pruebas del agente siguen limitadas a filas propias `PRUEBA-`, `es_ejemplo=true`.
- Las migraciones aplicadas se conservan sin reescribir su historial.
- Auth automático y migración 007 aplicados y verificados en pea-prod el 2026-10-21.
  La lectura real y el CRUD de una fila PRUEBA- propia pasaron; la fila fue eliminada.
