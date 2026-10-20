---
tipo: bitacora
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[GUI-Diseno-Python]]"
origen: "Corrección de texto recortado en cabecera, pestañas, tablas y píldoras de la GUI"
agente: "Copilot"
rama: "feat/python-cierre-francisco"
commit: ""
---

# Legibilidad de cabecera y tablas

## Objetivo
Evitar el recorte de rótulos de la cabecera, columnas, códigos y píldoras en las
resoluciones de aceptación sin quitar controles funcionales.

## Qué se hizo
- La insignia de demostración pasa a una fila propia en anchos menores de
  2000 px; la marca, el texto de insignia y los controles de sesión mantienen
  su espacio en las tres resoluciones comprobadas.
- Las pestañas se muestran con ícono y tooltip bajo 1600 px; a 1920 px se
  muestran con su etiqueta completa. El anillo de foco solo se dibuja en la
  pestaña activa.
- Las píldoras reservan el ancho medido de su texto y lo ofrecen como tooltip.
- Las columnas reservan el ancho de encabezado y de una muestra de contenido;
  el encabezado y el contenido completo se obtienen con tooltip cuando procede.
- Se actualizaron los criterios responsivos de diseño y se agregaron pruebas de
  ancho y tooltip.

## Comandos y resultados
- `python -m pytest -q tests\unit\test_componentes_gui.py tests\unit\test_gui_completa.py tests\unit\test_tabla_ficha_dialogos.py`:
  49 pasaron.
- `ruff check` para los archivos modificados: aprobado.
- Medición offscreen de 1100 × 700, 1366 × 768 y 1920 × 1080: la insignia
  reserva sus 289 px mínimos; las pestañas usan 44 px por botón en las dos
  primeras resoluciones y ocupan 1169 px con rótulos completos a 1920 px.
- Pylance: `pildora.py` sin diagnósticos.

## Decisiones
Se prioriza la lectura del nombre de pantalla mediante tooltip en ventanas
estrechas, en lugar de forzar etiquetas que desbordan la cabecera. Las columnas
no fuerzan barras horizontales: se ocultan según su prioridad y preservan
tooltips para consultar el texto completo.

## Pendientes y siguiente paso
Revisar las fichas laterales de Investigadores, Grupos y Productos para
confirmar que el contenido se desplaza en una sola zona y que las acciones
permanecen fijas al pie.
