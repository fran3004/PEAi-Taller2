---
tipo: bitacora
estado: revisado
creado: 2026-10-06
actualizado: 2026-10-06
relacionado:
  - "[[GUI-Diseno-Python]]"
origen: "Correccion del contraste del dialogo de cierre de sesion y visualizacion de graficos en Inicio"
agente: "Copilot"
rama: "feat/gui-inicio-graficos-copilot"
commit: ""
---

# Contraste y graficos de Inicio

## Objetivo
Mejorar la legibilidad de la confirmacion de cierre de sesion y asegurar que
los graficos Dona y Red de colaboracion sean visibles en Inicio.

## Que se hizo
- Se aplico estilo local al QMessageBox para mostrar superficie blanca, texto
  oscuro y botones legibles sin cambiar sus botones ni el flujo de confirmacion.
- Se dio una altura minima de 260 px a la dona y la mini red para evitar que el
  diseno de dos columnas las colapsara.
- Se agregaron regresiones para altura, datos presentes, textos, opcion
  predeterminada y contraste del dialogo.

## Comandos y resultados
- `ruff check src tests`: aprobado.
- `pytest tests\unit\test_gui_completa.py tests\unit\test_pantalla_inicio.py -q`:
  31 pasaron.
- `pytest tests\unit -q`: 219 pasaron, 1 deseleccionada.
- `python -m pea.gui --autoprueba` con Qt offscreen:
  completada; 24 combinaciones de pantalla y resolucion, cero barras
  horizontales visibles. Se informaron widgets fuera del rectangulo de ventana
  en pantallas desplazables, como advertencias de la autoprueba.
- Capturas aisladas de los graficos tras 600 ms: dona con 7 segmentos y mini
  red con 12 nodos; ambos widgets midieron 260 px de alto.
- `git diff --check`: aprobado.

## Decisiones
Se mantuvieron los colores y la distribucion de datos de los graficos; la
correccion solo impide que el layout reduzca sus widgets a altura cero. El
estilo del dialogo se limita a ese QMessageBox.

## Pendientes y siguiente paso
Las capturas offscreen tienen glifos sustituidos por cuadrados porque el
entorno no dispone de las fuentes requeridas. El renderizado, el contraste y
las dimensiones se verificaron, pero la legibilidad tipografica final debe
confirmarse en un equipo con las fuentes del proyecto.
