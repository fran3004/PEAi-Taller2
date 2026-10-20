---
tipo: bitacora
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[Matriz-cumplimiento-enunciado]]"
  - "[[SPEC]]"
  - "[[Variables-entrada-salida]]"
  - "[[Interoperabilidad]]"
origen: "Contraste de puntos funcionales del enunciado original suministrado por el usuario"
agente: "Copilot"
rama: "feat/python-cierre-francisco"
commit: ""
---

# Bitácora · Contraste del enunciado del Taller 2

## Objetivo
Contrastar los requisitos funcionales del PDF original con el estado verificable
del código.

## Qué se hizo
- Se extrajo el texto de las tres páginas de
  `docs/entrada/Taller 2 EdD (2026-09-24) - G 8.pdf`.
- Se reemplazó el mapeo provisional R0–R12 por una matriz ligada a los puntos
  literales 1–14 y los requisitos generales de la primera página.
- Se identificaron como parciales el soporte operativo del Plan de grupo, la
  vista estadística por producto, la edición exhaustiva de todos los campos,
  la verificación real de SCIENTI/Supabase y la interoperabilidad entre
  procesos Python/C++.
- Se verificó la suite C++ existente: el objetivo de CTest pasó.

## Comandos y resultados
- Extracción local con `pdfplumber`: **3 páginas**, requisitos 1–14 y notas.
- `ctest --test-dir cpp/build --output-on-failure`: **1/1 pruebas registradas
  pasaron**.
- Suite Python previamente ejecutada en este cierre: **284 pasaron, 3
  excluidas**.
- Autoprueba GUI previamente ejecutada: **0 hallazgos en 24 combinaciones**.
- El contrato remoto Supabase permanece omitido por falta de configuración de
  sesión normal y clave publicable.

## Decisiones
La matriz distingue requisitos funcionales de la condición de calificación
(punto 13) y de la pregunta opcional «¿Rust?» (punto 14.f). «Cumple» se limita a
la evidencia indicada y no implica validación remota ni aprobación docente.

## Pendientes y siguiente paso
- Priorizar la integración del Plan de grupo y decidir si se requiere la vista
  analítica por producto.
- Verificar remotamente los conteos cuando la sesión normal de Supabase esté
  configurada.
- Confirmar en ejecución la salida de resumen del CLI C++ y probar
  interoperabilidad directa si el curso la exige.
