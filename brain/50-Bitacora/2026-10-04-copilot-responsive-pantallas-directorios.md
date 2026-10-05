---
tipo: bitacora
estado: revisado
creado: 2026-10-04
actualizado: 2026-10-04
relacionado:
  - "[[GUI-Diseno-Python]]"
  - "[[2026-10-04-copilot-responsividad-tablas-fichas]]"
origen: "Solicitud de responsividad en investigadores, grupos y productos"
agente: "Copilot"
rama: "master"
---

# Responsividad de pantallas de directorios

## Que cambie

- Ajuste las prioridades de columnas en investigadores, grupos y productos: nombres o titulos estiran con prioridad 1; categorias, tipologias, grupos y estados usan prioridad 2; codigos, anos, conteos, autores y otros metadatos usan prioridad 3.
- Elimine los minimos rigidos de los combos y configure el buscador como expansible; los combos pueden ceder espacio en la barra de contexto de 56 px sin crear desplazamiento horizontal.
- Conecte `resizeEvent` de cada pantalla con el ancho responsive de la ficha y la distribucion del `QSplitter`.
- Hice flexibles los graficos de las fichas: 120 px para la serie de investigadores y 150 px para las barras de grupos en ventanas con alto menor de 760 px; en ventanas mayores conservan 140 y 180 px como minimo.
- Manteni las acciones de las fichas fuera del `QScrollArea`, por lo que permanecen fijas mientras el cuerpo se desplaza verticalmente.
- Agregue pruebas parametrizadas para 1100x700, 1366x768 y 1920x1080 en las tres pantallas.

## Archivos

- `src/pea/gui/pantallas/investigadores.py`
- `src/pea/gui/pantallas/grupos.py`
- `src/pea/gui/pantallas/productos.py`
- `src/pea/gui/componentes/ficha_lateral.py`
- `tests/unit/test_pantalla_investigadores.py`
- `tests/unit/test_pantalla_grupos.py`
- `tests/unit/test_pantalla_productos.py`

## Verificacion

- `ruff check src tests`: OK.
- Pruebas focalizadas de las tres pantallas: 33 pasaron.
- `pytest tests/unit -v`: OK, 185 pasaron y 1 fue deseleccionada.
- `python -m pea.gui --autoprueba` en offscreen y sin animaciones: OK; genero capturas para las 8 pantallas en las 3 resoluciones.
- `tools/brain/verificar_brain.py`: OK despues de normalizar esta nota a LF.
