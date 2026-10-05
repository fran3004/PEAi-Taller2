---
tipo: bitacora
estado: revisado
creado: 2026-10-04
actualizado: 2026-10-04
relacionado:
  - "[[GUI-Diseno-Python]]"
  - "[[2026-10-04-copilot-responsividad-redes]]"
origen: "Solicitud de responsividad en Importar, Configuracion y Acerca de"
agente: "Copilot"
rama: "master"
---

# Responsividad de Importar, Configuracion y Acerca de

## Que cambie

- En Importar envolvi el contenido en un `QScrollArea` vertical con la barra horizontal apagada, manteniendo visibles las acciones dentro de la cola.
- La zona de arrastre conserva sus 88 px de alto y ahora el nombre del archivo se elide en el centro; el nombre completo queda disponible en el tooltip.
- En Configuracion los cuatro campos de acceso tienen politica horizontal expansible.
- El splitter vertical de Verificacion Cruzada no permite colapsar sus paneles y recibe una distribucion inicial separada para que la tabla y los visores no se pisen.
- En Acerca de mantuve el desplazamiento vertical y apague el horizontal; se conservaron referencias directas a institucion, nombre/version y proposito para validar que la informacion esencial se cargue.

## Pruebas

- Para Importar, Configuracion y Acerca de se probaron 1100x700 y 1366x768.
- En cada resolucion se verifico que no hubiera barras horizontales visibles.
- En Importar se verificaron los botones de encolar CSV, PDF, URL y procesar siguiente.
- En Configuracion se verificaron campos expansibles y alturas positivas del splitter.
- En Acerca de se verifico que la identidad institucional, nombre/version y proposito estuvieran visibles.

## Archivos

- `src/pea/gui/pantallas/importar.py`
- `src/pea/gui/pantallas/configuracion.py`
- `src/pea/gui/pantallas/acerca.py`
- `tests/unit/test_pantallas_compactas.py`

## Verificacion

- `ruff check src tests`: OK.
- `pytest tests/unit/test_pantallas_compactas.py -q`: 6 pasaron.
- `pytest tests/unit -v`: 195 pasaron y 1 fue deseleccionada.
- `python -m pea.gui --autoprueba` con offscreen y sin animaciones: OK; genero capturas en las tres resoluciones oficiales.
