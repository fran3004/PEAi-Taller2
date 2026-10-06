---
tipo: bitacora
estado: revisado
creado: 2026-10-06
actualizado: 2026-10-06
relacionado:
  - "[[GUI-Diseno-Python]]"
origen: "Localizacion de botones del dialogo nativo de cierre de sesion"
agente: "Copilot"
rama: "master"
---

# Localizacion de dialogo de cierre

## Objetivo
Mostrar en espanol las etiquetas de botones del dialogo nativo para cerrar
sesion, conservando los valores estandar y el comportamiento existente.

## Que se hizo
- Se reemplazo `QMessageBox.question()` por una instancia explicita de
  `QMessageBox`.
- Se configuraron icono, titulo y mensaje en espanol.
- Se asignaron los textos visibles "Si" y "No" a los botones estandar Yes y
  No, respectivamente.
- Se mantuvo No como boton predeterminado y Yes conserva la misma rama de
  desconexion.
- Se agrego una prueba que comprueba textos, boton predeterminado y cierre
  seguro con No.
- La busqueda global de botones estandar en la GUI encontro solamente este
  dialogo; no se encontraron otras etiquetas inglesas comunes de botones.

## Comandos y resultados
- `python -m ruff check src tests`: aprobado.
- `python -m pytest tests\unit`: 219 pasaron, 1 deseleccionada.
- Pruebas dirigidas del dialogo y botones deshabilitados: 2 pasaron.
- `python -m pea.gui --autoprueba` con Qt offscreen: completada.
- `python tools\brain\verificar_brain.py`: 122 notas, cero errores y cero
  advertencias.
- `git diff --check`: aprobado.

## Decisiones
Se conservan `QMessageBox.StandardButton.Yes` y `No` como resultados internos;
solo se localizan las etiquetas visibles. La opcion predeterminada sigue
siendo No.

## Pendientes y siguiente paso
Ninguno dentro del alcance de esta correccion.
