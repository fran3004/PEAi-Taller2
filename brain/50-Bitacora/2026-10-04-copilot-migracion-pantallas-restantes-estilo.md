---
tipo: bitacora
estado: revisado
creado: 2026-10-04
actualizado: 2026-10-04
relacionado:
  - "[[GUI-Diseno-Python]]"
  - "[[2026-10-04-copilot-tokens-estilo]]"
  - "[[2026-10-04-copilot-migracion-pantallas-estilo]]"
origen: "Solicitud de centralizar estilos en las pantallas restantes de la GUI Python"
agente: "Copilot"
rama: "master"
commit: ""
---

# Migracion de estilos en pantallas restantes

## Que cambie

- Migre `inicio.py`, `redes.py`, `importar.py`, `configuracion.py`, `acerca.py` y `ventana_principal.py` a tokens de `estilo.py`.
- Migre la transparencia residual de `selector_segmentado.py`, necesaria para que el guardian global cubriera toda la GUI.
- Reemplace colores hexadecimales y `rgba(...)` por tokens semanticos, y tama?os QSS y `setPointSize` por tokens de tipografia.
- Mantive `TAMANO_ESLOGAN` como unica excepcion de tama?o inferior al cuerpo en la barra superior.
- Retire el `xfail` del guardian global en `test_estilo_recursos.py`.

## Archivos

- `src/pea/gui/pantallas/inicio.py`
- `src/pea/gui/pantallas/redes.py`
- `src/pea/gui/pantallas/importar.py`
- `src/pea/gui/pantallas/configuracion.py`
- `src/pea/gui/pantallas/acerca.py`
- `src/pea/gui/ventana_principal.py`
- `src/pea/gui/componentes/selector_segmentado.py`
- `tests/unit/test_estilo_recursos.py`

## Verificacion

- Guardian global: OK; no encontro literales `#RRGGBB`, `rgba(...)`, tama?os numericos en `font-size` ni `setPointSize` numerico fuera de `estilo.py`.
- `ruff check src tests`: OK.
- `pytest tests/unit -v`: 173 pasadas, 1 omitida.
- `QT_QPA_PLATFORM=offscreen PEA_SIN_ANIMACIONES=1 python -m pea.gui --autoprueba`: OK; genero 24 capturas en tres resoluciones.
- `tools/brain/verificar_brain.py`: 0 errores y 0 advertencias.

## Limitaciones

La inspeccion visual manual pixel a pixel de las 24 capturas no forma parte de esta ejecucion; la autoprueba confirma que las siete pantallas se construyen, navegan y capturan sin error.
