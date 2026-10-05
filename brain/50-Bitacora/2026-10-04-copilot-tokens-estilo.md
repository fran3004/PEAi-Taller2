---
tipo: bitacora
estado: revisado
creado: 2026-10-04
actualizado: 2026-10-04
relacionado:
  - "[[GUI-Diseno-Python]]"
  - "[[2026-10-04-copilot-fuentes-inter-gui]]"
origen: "Solicitud de centralizar tokens de color y tamaño y preparar generadores QSS"
agente: "Copilot"
rama: "master"
commit: ""
---

# Bitácora · Tokens y generadores de estilo

## Objetivo
Preparar `estilo.py` para que la migración de colores y tamaños escritos directamente en las pantallas pueda hacerse de forma uniforme y verificable.

## Qué se hizo
- Se inventariaron los colores hexadecimales y transparencias usados por la GUI Python.
- Se añadieron tokens semánticos para superficies, estados deshabilitados, estados de error y superposiciones de la barra superior.
- Se añadieron `css_etiqueta`, `css_boton`, `css_pildora`, `css_menu` y `css_pestana_interna`.
- `css_boton` admite las variantes `primario`, `secundario`, `peligro` e `icono`, y rechaza variantes desconocidas con `ValueError`.
- `generar_hoja_estilos()` ahora incluye `QToolTip`, `QMenu` y `QComboBox` con 11 pt.
- Los nuevos pares de texto/fondo se incorporaron a la tabla de contraste WCAG 2.1.
- Se añadió una prueba que aplica los QSS a Qt y captura avisos de parseo.
- Se añadió el guardián de literales solicitado como `xfail(strict=False)` mientras continúa la migración de pantallas.

## Archivos modificados
- `src/pea/gui/estilo.py`
- `tests/unit/test_estilo_recursos.py`
- `brain/50-Bitacora/2026-10-04-copilot-tokens-estilo.md`

## Comandos y resultados
- Inventario de colores con `grep` equivalente sobre `src/pea/gui/**/*.py`: se encontraron 59 códigos hexadecimales únicos y 12 transparencias únicas.
- `ruff check src tests`: `All checks passed!`.
- `pytest tests/unit/test_estilo_recursos.py -q`: `19 passed, 1 xfailed`.
- `pytest tests/unit -v`: `172 passed, 1 deselected, 1 xfailed in 62.20s`.
- `QT_QPA_PLATFORM=offscreen PEA_SIN_ANIMACIONES=1 python -m pea.gui --autoprueba`: código 0; 24 capturas regeneradas.
- `tools/brain/verificar_brain.py`: 92 notas, 0 errores y 0 advertencias.

## Alcance y pendientes
- No se modificaron las pantallas ni otros componentes porque esta tarea restringió los cambios a `estilo.py`, su prueba y la bitácora.
- El guardián continúa fallando de forma esperada debido a los literales existentes fuera de `estilo.py`; queda listo para retirarse en el prompt 4B tras completar la migración.
- No se modificó la funcionalidad de filtros, cascadas, deshacer o importación.
