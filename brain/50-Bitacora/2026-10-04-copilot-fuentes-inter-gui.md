---
tipo: bitacora
estado: revisado
creado: 2026-10-04
actualizado: 2026-10-04
relacionado:
  - "[[GUI-Diseno-Python]]"
  - "[[ADR-0017-Tecnologia-de-interfaz-Qt-Widgets]]"
origen: "Solicitud de incorporar Inter para corregir texto ilegible en la GUI y autopruebas"
agente: "Copilot"
rama: "master"
commit: ""
---

# Bitácora · Fuente Inter en la GUI Python

## Objetivo
Incorporar la fuente Inter estática con licencia OFL, cargarla antes de crear la ventana PySide6 y evitar que las capturas o la aplicación vuelvan a mostrar cuadrados por falta de fuentes.

## Qué se hizo
- Se descargó la release oficial `rsms/inter v4.1`.
- Se copiaron únicamente `Inter-Regular.ttf`, `Inter-Medium.ttf`, `Inter-SemiBold.ttf`, `Inter-Bold.ttf`, `Inter-ExtraBold.ttf` y la licencia `OFL.txt` en `src/pea/gui/recursos/fuentes/`.
- Se implementó `cargar_fuentes()` en `src/pea/gui/recursos/cargador.py`, con errores explícitos si falta o falla una fuente.
- Se añadió `fuente_inter_cargada()` y la lista documentada de símbolos especiales usados por la interfaz.
- `pea.gui.main()` carga Inter después de crear `QApplication`, aplica `QFont("Inter", 11)` y lo hace también en `--autoprueba`.
- `FAMILIA_TIPOGRAFICA` deja Inter como primera familia.
- `ejecutar_autoprueba()` devuelve código 2 y muestra un error claro si Inter no está cargada.
- Se añadieron pruebas de existencia de archivos, registro de familia y cobertura de caracteres españoles y símbolos especiales.
- Se verificó el wheel generado: incluye los cinco TTF y `OFL.txt`.
- Se regeneraron las 24 capturas oficiales.
- Se inspeccionaron visualmente las 8 pantallas en 1100x700, 1366x768 y 1920x1080; el texto se lee y no aparecen cuadrados.

## Archivos cambiados
- `src/pea/gui/recursos/fuentes/Inter-Regular.ttf`
- `src/pea/gui/recursos/fuentes/Inter-Medium.ttf`
- `src/pea/gui/recursos/fuentes/Inter-SemiBold.ttf`
- `src/pea/gui/recursos/fuentes/Inter-Bold.ttf`
- `src/pea/gui/recursos/fuentes/Inter-ExtraBold.ttf`
- `src/pea/gui/recursos/fuentes/OFL.txt`
- `src/pea/gui/recursos/cargador.py`
- `src/pea/gui/recursos/__init__.py`
- `src/pea/gui/__init__.py`
- `src/pea/gui/estilo.py`
- `src/pea/gui/ventana_principal.py`
- `tests/unit/test_estilo_recursos.py`

## Comandos y resultados
- `ruff check src tests`: `All checks passed!`.
- `pytest tests/unit/test_estilo_recursos.py -q`: `17 passed`.
- `pytest tests/unit -v`: `170 passed, 1 deselected`.
- `QT_QPA_PLATFORM=offscreen PEA_SIN_ANIMACIONES=1 python -m pea.gui --autoprueba`: código 0; 24 capturas guardadas.
- `python -m build --wheel`: wheel creado correctamente.
- Comprobación del wheel: `PACKAGE_FONTS_OK`; los cinco TTF y `OFL.txt` están empaquetados.
- `tools/brain/verificar_brain.py`: se ejecutará después de normalizar esta nota a UTF-8 con finales LF.

## Decisiones
- No se modificó `pyproject.toml`: Hatchling incluye los archivos no Python ubicados dentro del paquete `src/pea`, y la comprobación del wheel confirmó que los recursos se distribuyen.
- No se reemplazaron los símbolos especiales porque Inter contiene todos los caracteres comprobados mediante `QFontMetricsF.inFontUcs4`.
- No se modificaron los desbordamientos visuales preexistentes observados en algunas capturas; quedan fuera del objetivo de fuentes.

## Pendientes y siguiente paso
- Registrar el commit que incluya esta bitácora y los cambios de fuente.
- Mantener la verificación de `--autoprueba` como requisito antes de aceptar cambios visuales futuros.
