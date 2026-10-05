---
tipo: bitacora
estado: borrador
creado: 2026-10-04
actualizado: 2026-10-04
relacionado:
  - "[[GUI-Diseno-Python]]"
  - "[[2026-10-04-copilot-tokens-estilo]]"
origen: "Trabajo solicitado por el usuario"
agente: "Copilot"
rama: "master"
commit: ""
---

# Migracion de estilos en pantallas

## Que cambie

- Migre `grupos.py`, `investigadores.py` y `productos.py` para usar tokens centralizados de `estilo.py` en colores, tipografias y radios.
- Corregi la interpolacion de tokens en hojas QSS y normalice imports.
- Sustitui los tama?os funcionales y auxiliares por `TAMANO_CUERPO`, `TAMANO_AUXILIAR` y tokens de titulos, sin cambiar la logica de datos ni filtros.

## Archivos

- `src/pea/gui/pantallas/grupos.py`
- `src/pea/gui/pantallas/investigadores.py`
- `src/pea/gui/pantallas/productos.py`

## Verificacion

- Guardian dirigido: sin literales de color, `rgba`, `font-size` numerico, `setPointSize` numerico ni radios numericos en las tres pantallas.
- `ruff check src tests`: OK.
- `pytest tests/unit -q`: 172 pasadas, 1 omitida, 1 xfail.
- `QT_QPA_PLATFORM=offscreen PEA_SIN_ANIMACIONES=1 python -m pea.gui --autoprueba`: OK; genero capturas de las siete pantallas en 1100x700, 1366x768 y 1920x1080.

## Limitaciones

El guardian global continua marcado como `xfail` porque existen migraciones pendientes en otras pantallas, fuera del alcance de esta tarea.
