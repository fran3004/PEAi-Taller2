---
tipo: bitacora
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[GUI-Diseno-Python]]"
origen: "Corrección responsive de las fichas laterales de Investigadores, Grupos y Productos"
agente: "Copilot"
rama: "feat/python-cierre-francisco"
commit: ""
---

# Bitácora · Fichas laterales responsivas

## Objetivo
Evitar que las tarjetas KPI y las acciones de las fichas laterales se compriman
o recorten en anchos reducidos y mantener una sola zona efectiva de
desplazamiento.

## Qué se hizo
- La cuadrícula KPI reorganiza sus widgets en una columna cuando el ancho no
  permite dos tarjetas de al menos 180 px.
- Los botones principales cambian entre una y dos columnas según el ancho
  disponible y el tamaño medido de sus rótulos; las acciones permanecen fuera
  del área desplazable.
- «Ver ficha completa» reduce su relleno horizontal para caber en la ficha más
  estrecha.
- La tabla alternativa del gráfico de Grupos oculta sus barras internas y, al
  activarse, ajusta su altura para mostrar todas las filas y dejar el
  desplazamiento al cuerpo de la ficha.
- Se añadieron pruebas responsive y se actualizó la especificación de diseño.

## Comandos y resultados
- `QT_QPA_PLATFORM=offscreen; python -m pytest -q` sobre las tres pruebas
  focalizadas de KPI, ficha de Grupo y alternancia del gráfico: **5 pasaron**.
- `ruff check` sobre los archivos Python modificados: **All checks passed!**
- Pylance en los cinco archivos Python modificados: **sin errores**.
- Ejecución offscreen de la GUI de demostración a 1100 × 700 y 1366 × 768:
  las acciones aplicables quedan visibles y son más anchas que sus tamaños
  mínimos; las fichas muestran un solo conjunto de barras de desplazamiento.
  La alternativa tabular de Grupos muestra sus 5 filas sin barras internas.
- Suite relacionada de cinco módulos: **58 pasaron, 1 falló, 1 se excluyó**.
  El fallo observado fue `test_pantalla_investigadores_tabla_responsive_y_elipsis`,
  que esperaba visible la columna «Grupo(s)». No modifica la ficha lateral y
  queda pendiente de investigar en la revisión de tablas responsive.

## Decisiones
La ficha usa una columna de KPI por debajo de 368 px de ancho útil. Las
acciones primarias ocupan una o dos columnas según los tamaños reales de sus
botones, en vez de imponer una cuadrícula fija. La tabla accesible del gráfico
ajusta su altura solo mientras está activa para no aumentar la altura mínima
del gráfico normal.

## Pendientes y siguiente paso
- Investigar el fallo de visibilidad de columnas en la tabla de Investigadores
  sin mezclarlo con la corrección de fichas.
- Continuar con la autoprueba estricta de la GUI.
