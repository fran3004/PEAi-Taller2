---
tipo: bitacora
estado: revisado
creado: 2026-10-21
actualizado: 2026-10-21
relacionado:
  - "[[Despliegue]]"
  - "[[GUI-paridad]]"
origen: "Reporte de cierre de la aplicación C++ conectada en el paquete descargable"
agente: "Codex"
rama: "feat/python-cierre-francisco"
commit: ""
---

# Bitácora · Corrección de cierre en TUI C++

## Objetivo

Corregir el cierre de la TUI C++ conectada y regenerar/verificar el paquete portable
de Windows para su nueva publicación.

## Qué se hizo

- Se reprodujo el cierre del ejecutable publicado: terminaba con `0xC0000005`;
  la versión demo permanecía abierta.
- Se aisló la causa en el movimiento de `CatalogoInvestigacion`: `ServicioEstadisticas`
  conservaba un puntero al hipercubo del objeto temporal destruido antes del primer
  render de la pantalla.
- Se implementaron movimientos que reatan el servicio estadístico al hipercubo
  destino y se añadió una prueba de regresión para move assignment y move construction.
- Se documentó la regresión dentro de las comprobaciones CTest del despliegue.
- Se reconstruyó el ZIP usando explícitamente `build/entrega`, que contiene el C++
  corregido; el primer intento con el directorio por defecto se detuvo en la prueba
  portable al detectar que dicho ejecutable no tenía el comando TLS esperado.

## Comandos y resultados

- C++ Release: compilación correcta; CTest 1/1.
- doctest C++: 60 casos y 685 aserciones aprobados.
- `scripts/verificar.ps1 -DirectorioCpp build/entrega`: correcto; Python 311 aprobadas,
  3 de red excluidas; bóveda 0 errores; autoprueba TUI correcta.
- `scripts/empaquetar.ps1 -Msys2 C:\msys64 -DirectorioCpp build/entrega`: paquete
  portable completo y escaneo de secretos aprobado.
- Se extrajo el ZIP generado y se comprobó el inicio conectado sin variables `PEA_*`;
  la TUI permaneció abierta y mostró datos cargados de Supabase.
- SHA-256 local: `d3499aae7753abfdb08046342cde99c3318f487f7651604f7d7d8573dccd2c8f`.
- No se hicieron escrituras de datos en Supabase durante la prueba; la aplicación
  autenticó y leyó el catálogo.

## Decisiones

- Se corrigió la semántica de movimiento del catálogo, no la autenticación ni el
  renderizado: el cierre era una referencia colgante al servicio de estadísticas.
- Se preservaron los artefactos locales anteriores en `build/entrega-anterior-20261021`.

## Pendientes y siguiente paso

- Publicar el commit y el nuevo paquete en una Release de GitHub; confirmar que los
  assets descargables coinciden con el SHA-256 verificado localmente.
- No se alteró la Release anterior.
