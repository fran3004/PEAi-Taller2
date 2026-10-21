---
tipo: bitacora
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[TUI-Diseno-Cpp]]"
  - "[[Paridad-Python-Cpp]]"
  - "[[ADR-0020-Revision-remota-periodica-cpp]]"
origen: "Pruebas del ciclo de vida del trabajador periódico de revisión C++"
agente: "Copilot"
rama: "feat/python-cierre-francisco"
commit: ""
---

# Bitácora · Ciclo de vida de revisión remota C++

## Objetivo

Hacer verificable el ciclo de ejecución y parada del hilo de revisión remota
sin conectar a Supabase ni compartir objetos Qt entre hilos.

## Qué se hizo

- Se extrajo el ciclo periódico a `TrabajadorPeriodico`. La tarea y el cliente
  HTTPS se preparan dentro del hilo de trabajo; la interfaz recibe solo
  notificaciones de resultado/error.
- La espera de 30 segundos se interrumpe al cerrar la TUI y el destructor
  garantiza la parada y unión del hilo.
- Las excepciones de tarea y preparación del cliente se remiten al notificador
  de error; una falla de consulta no termina el proceso y el ciclo vuelve a
  intentarlo en el siguiente intervalo.
- Se añadieron pruebas sin red para inicio en un hilo separado, repetición,
  parada durante la espera, errores, tarea de preparación vacía y configuración
  inválida.

## Comandos y resultados

- Build C++ independiente: correcto; CTest aprobó 1/1 suite.
- `pruebas_cpp.exe --no-version`: 49 casos y 486 aserciones aprobados.
- `pea-cpp.exe --autoprueba`: 32 combinaciones de pantalla/tamaño y formularios
  sin hallazgos.
- `git diff --check`: correcto.
- No se realizaron llamadas a Supabase. La autenticación y la expiración real
  de token quedan pendientes de una prueba de integración autorizada.

## Decisiones

- La tarea se prepara una vez dentro del hilo y se repite allí; así el cliente
  `QNetworkAccessManager` conserva su afinidad de hilo.
- Se conserva el intervalo inicial de 30 segundos y la primera consulta
  inmediata.

## Pendientes y siguiente paso

- Probar la interacción TUI con una sesión autorizada, incluyendo expiración
  del token y errores reales de RPC y lectura de `meta`.
