---
tipo: bitacora
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[Matriz-cumplimiento-enunciado]]"
  - "[[SPEC]]"
origen: "Creación de archivos de entrega y matriz honesta de cumplimiento"
agente: "Copilot"
rama: "feat/python-cierre-francisco"
commit: ""
---

# Bitácora · Entregables del taller

## Objetivo
Preparar el punto de entrada Python, la especificación técnica Word, la copia
de identificación solicitada y una matriz de cumplimiento que no atribuya
requisitos sin evidencia.

## Qué se hizo
- Se creó `entrega/Taller2_FF_SM.py` con encabezado, índice y apertura de la
  GUI.
- Se generó `entrega/Especificacion_Tecnica_PEAi.docx` y se verificó su
  estructura de documento Word.
- Se copió `entrega/integrantes.txt` desde la identidad de entrega existente;
  incluye datos personales. La consulta de GitHub informó visibilidad pública;
  la copia permanece local y no se hizo `push`.
- Se creó [[Matriz-cumplimiento-enunciado]]. Como el enunciado numerado 1–14
  no está en `docs/entrada/`, el mapeo secuencial de puntos 1–13 a R0–R12 está
  marcado explícitamente como supuesto provisional. El punto 14 y C++ quedan
  pendientes de cotejo; no se inventaron códigos de grupos ni datos reales.
- Se ignoró el video, según la instrucción.

## Comandos y resultados
- `.venv\Scripts\python.exe -m py_compile entrega\Taller2_FF_SM.py`: aprobado.
- Validación de `word/document.xml` y `[Content_Types].xml` dentro del DOCX:
  aprobada.
- `.venv\Scripts\python.exe tools\brain\verificar_brain.py`: **0 errores**;
  permanece 1 advertencia histórica de un enlace ADR-0016 no resuelto.

## Decisiones
Los estados de la matriz son conservadores: cumplimiento local no equivale a
validación de datos remotos ni a cotejo con un enunciado ausente.

## Pendientes y siguiente paso
- Incorporar el enunciado original numerado para validar la trazabilidad exacta.
- Revisar con el docente el canal de entrega adecuado para los archivos con
  datos personales. `AGENTS.md` exige repositorio privado, pero el agente no
  puede cambiar la visibilidad del repositorio en GitHub.
