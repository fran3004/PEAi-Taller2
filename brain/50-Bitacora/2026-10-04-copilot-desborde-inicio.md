---
tipo: bitacora
estado: revisado
creado: 2026-10-04
actualizado: 2026-10-04
relacionado:
  - "[[GUI-Diseno-Python]]"
  - "[[2026-10-04-copilot-responsive-pantallas-directorios]]"
origen: "Solicitud de diagnostico y correccion de desbordes en Inicio"
agente: "Copilot"
rama: "master"
---

# Desborde horizontal de Inicio

## Que cambie

- Cree `scripts/diagnostico_desborde.py` para medir `minimumSizeHint().width()` y detectar barras horizontales en modo offscreen.
- El diagnostico inicial encontro una barra horizontal en `QScrollArea` para 1100x700, 1366x768 y 1920x1080; los mayores minimos llegaron a 1540, 2622 y 2622 px.
- Reduje las restricciones horizontales de los graficos, tarjetas, KPI y filas de ranking con politicas de tamano ignoradas o expansibles.
- Desactive la barra horizontal del contenido de Inicio y mantuve la vertical.
- Cambie la rejilla de cuatro columnas al umbral de 1500 px; entre 1100 y 1499 px conserva dos columnas.
- El combo de grupos usa un minimo de 200 px por debajo de 1240 px y 280 px desde ese ancho.
- Agregue pruebas para 1100x700, 1366x768 y 1920x1080.

## Evidencia del diagnostico posterior

- En las tres resoluciones no se detecta ninguna area con barra horizontal visible.
- Los 15 mayores minimos ya no incluyen las filas de ranking con anchos de 761 px; el mayor valor observado es 1268 px en un widget de contexto oculto o auxiliar.

## Archivos

- `scripts/diagnostico_desborde.py`
- `src/pea/gui/componentes/graficos/base.py`
- `src/pea/gui/componentes/tarjeta.py`
- `src/pea/gui/componentes/tarjeta_kpi.py`
- `src/pea/gui/pantallas/inicio.py`
- `tests/unit/test_pantalla_inicio.py`

## Verificacion

- Diagnostico offscreen: sin barras horizontales en 1100x700, 1366x768 y 1920x1080.
- `ruff check src tests`: OK.
- `pytest tests/unit/test_pantalla_inicio.py -q`: 8 pasaron.
