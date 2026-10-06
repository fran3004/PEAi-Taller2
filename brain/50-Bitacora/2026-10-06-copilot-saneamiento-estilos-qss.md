---
tipo: bitacora
estado: revisado
creado: 2026-10-06
actualizado: 2026-10-06
relacionado:
  - "[[GUI-Diseno-Python]]"
  - "[[2026-10-06-copilot-infraestructura-pruebas-gui]]"
origen: "Solicitud de saneamiento de tokens sin interpolar en estilos Qt"
agente: "Copilot"
rama: "master"
---

# Saneamiento de estilos QSS

## Objetivo

Corregir expresiones de tokens `estilo.X` que llegaban literalmente a QSS o a `QColor`, sin cambiar la paleta ni eliminar el sistema centralizado de tokens.

## Cambios

- Se corrigio el fondo de las filas del popover de historial usando una variable de color interpolada antes de construir el QSS.
- Se corrigieron el titulo, los controles y el borde de leyenda de `barras_apiladas.py`.
- Se corrigieron los bordes de leyenda de `dona_doble.py`.
- Se verifico que las filas de autores de `productos.py` y el fondo de arrastre de `importar.py` ya usaban f-strings correctos.
- Se corrigieron los usos de `QColor("{estilo.SUPERFICIE}")` en los graficos.
- Se agrego una prueba AST que detecta tokens de estilo sin interpolar dentro de llamadas `setStyleSheet` y `QColor`.

## Verificacion

- `ruff check src tests`: aprobado.
- `pytest tests/unit/test_estilo_recursos.py -q`: 21 pasaron.
- La prueba de tokens sin interpolar paso sin hallazgos.
- Se conservaron la paleta, los tokens y el comportamiento de produccion.
