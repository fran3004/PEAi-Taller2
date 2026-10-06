---
tipo: bitacora
estado: revisado
creado: 2026-10-06
actualizado: 2026-10-06
relacionado:
  - "[[GUI-Diseno-Python]]"
origen: "Correccion de la integracion de GestorAvisos en la GUI Python"
agente: "Copilot"
rama: "master"
---

# Integracion de GestorAvisos

## Objetivo
Garantizar que todas las pantallas usen el unico gestor de avisos de
`VentanaPrincipal`, sin singleton global ni gestores secundarios.

## Que se hizo
- Se agrego la resolucion `GestorAvisos.desde_widget()`, basada en
  `widget.window()` y validacion con `isinstance`.
- Se agrego `GestorAvisos.mostrar_desde()` y la API `mostrar()`, que delega en
  los metodos semanticos de exito, aviso, error e informacion.
- Se reemplazaron todos los usos de `GestorAvisos.instancia()`.
- Se elimino el gestor adicional que creaba `PantallaInicio`.
- Se elimino el fallback que creaba `Toast` directamente en Importar.
- Se agrego una prueba para los cuatro tipos de aviso y la resolucion desde una
  pantalla hija.

## Comandos y resultados
- `python -m ruff check src tests`: aprobado.
- `python -m pytest tests\unit`: 217 pasaron, 1 deseleccionada.
- `python -m pytest tests\unit\test_componentes_gui.py`: 13 pasaron.
- `python -m pea.gui --autoprueba` con Qt offscreen: completada exitosamente.
- Verificacion real de 8 pantallas: un gestor, 32 avisos, resultado OK.
- `git diff --check`: aprobado.

## Decisiones
La ausencia de una ventana principal devuelve `None` desde `mostrar_desde()`;
no se crea un gestor alternativo ni se oculta el error con un `except` amplio.

## Pendientes y siguiente paso
Ninguno dentro del alcance de esta correccion.
