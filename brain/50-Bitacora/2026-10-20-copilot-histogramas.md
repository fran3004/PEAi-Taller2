---
tipo: bitacora
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[GUI-Diseno-Python]]"
  - "[[ADR-0018-Histogramas-desde-hipercubo]]"
origen: "Implementación del histograma solicitado para Inicio y la ficha del investigador"
agente: "Copilot"
rama: "feat/python-cierre-francisco"
commit: ""
---

# Bitácora · Histogramas desde el hipercubo

## Objetivo
Añadir histogramas reales a Inicio y a la ficha de investigador, calculados en
los servicios desde el `Hipercubo5D`, sin alterar la arquitectura de datos ni
agregar bibliotecas de gráficos.

## Qué se hizo
- Se añadieron los bins `0`, `1–2`, `3–5`, `6–10` y `11+` para la distribución
  de productos por investigador en los modos Institución y Grupo.
- Se añadió la distribución anual del investigador desde el subcubo limitado
  por el filtro de años global.
- Se implementó `GraficoHistograma` con Qt Widgets, `QPainter`, etiquetas,
  conteos, *tooltip*, estado vacío, exportación PNG y alternancia a tabla.
- Se integró el histograma a Inicio, la ficha de investigador y las
  exportaciones gráficas y PDF.
- Se añadieron pruebas de límites de bins, filtro temporal, integración de
  servicios y renderizado vacío y con datos.
- Se documentó la decisión en [[ADR-0018-Histogramas-desde-hipercubo]] y se
  actualizó [[GUI-Diseno-Python]].

## Comandos y resultados
- `python -m pytest -q`: 281 pasaron, 2 excluidas por configuración.
- Ruff focalizado en los módulos y pruebas modificados: aprobado.
- `python -m pea.gui --autoprueba`: 24 combinaciones verificadas, 0 hallazgos.
- `python tools/brain/verificar_brain.py`: aprobado tras normalizar la nota
  nueva a LF; permanece una advertencia preexistente por un enlace ADR-0016
  no resuelto en otra bitácora.
- `git diff --check`: aprobado.

## Decisiones
Los servicios son responsables de agregar los conteos desde el hipercubo y de
aplicar la ventana temporal antes de exponer los datos a la GUI. El gráfico
solo representa esos valores y conserva una tabla accesible para consultarlos.

## Pendientes y siguiente paso
- Continuar con la eliminación de código muerto y la corrección completa de
  Ruff/Vulture de la tarea siguiente.
- Revisar las tareas restantes de entrega, verificación remota autorizada y
  documentación del taller.
