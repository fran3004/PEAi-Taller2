---
tipo: bitacora
estado: revisado
creado: 2026-10-04
actualizado: 2026-10-04
relacionado:
  - "[[GUI-Diseno-Python]]"
origen: "Trabajo de implementacion y pruebas"
---

# Responsividad de tablas y fichas

## Que cambie

- Desactive permanentemente la barra horizontal de las tablas y estableci un ancho base de columna de 120 px.
- Agregue `ColumnSpecification` y `configurar_columnas()` con modos de estirar, contenido y fijo, minimos y prioridades.
- Las columnas prescindibles se ocultan cuando no caben y se restauran al recuperar espacio; la columna esencial conserva un minimo de 200 px en las pantallas migradas.
- Los delegados de texto muestran elipsis y tooltip con el valor completo; las pildoras tambien eliden su contenido.
- Las fichas laterales usan anchos adaptativos de 320, 380 y 440 px, solo desplazamiento vertical y ajuste de texto.
- Los splitters de grupos, investigadores y productos no permiten colapsar sus paneles.
- Reemplace el simbolo `✕`, que no esta disponible en Inter, por `X`.
- Actualice y amplie las pruebas unitarias para las tres resoluciones.

## Archivos

- `src/pea/gui/componentes/tabla.py`
- `src/pea/gui/componentes/ficha_lateral.py`
- `src/pea/gui/pantallas/grupos.py`
- `src/pea/gui/pantallas/investigadores.py`
- `src/pea/gui/pantallas/productos.py`
- `src/pea/gui/recursos/cargador.py`
- `src/pea/gui/pantallas/importar.py`
- `src/pea/gui/componentes/toast.py`
- `tests/unit/test_tabla_ficha_dialogos.py`
- `tests/unit/test_pantalla_grupos.py`
- `tests/unit/test_pantalla_investigadores.py`
- `tests/unit/test_pantalla_productos.py`

## Verificacion

- `ruff check src tests`: OK.
- Pruebas focalizadas responsive: 28 pasaron.
- Prueba especifica de tabla y ficha: 7 pasaron.
- Suite `pytest tests/unit -q`: OK, 176 pasaron y 1 fue deseleccionada.
- `python -m pea.gui --autoprueba` en offscreen y sin animaciones: OK; genero capturas en las 3 resoluciones para las 8 pantallas.
- `tools/brain/verificar_brain.py`: OK, 95 notas sin errores ni advertencias.

## Supuestos y riesgos

- En una ficha sin ventana contenedora se conserva el ancho solicitado directamente; en una pantalla se calcula con el ancho de la ventana contenedora durante el redimensionamiento.
- La autoprueba valida construccion y capturas; la inspeccion visual pixel a pixel de cada captura queda fuera de esta ejecucion.
