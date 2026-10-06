---
tipo: bitacora
estado: revisado
creado: 2026-10-06
actualizado: 2026-10-06
relacionado:
  - "[[GUI-Diseno-Python]]"
origen: "Correccion de la animacion visual de Toast y su interaccion con QGraphicsEffect"
agente: "Copilot"
rama: "feat/gui-inicio-graficos-copilot"
commit: ""
---

# Animacion segura de Toast

## Objetivo
Conservar la sombra institucional de los Toast y evitar que su animacion de
opacidad reemplace efectos graficos existentes.

## Que se hizo
- `animar_desvanecimiento()` ahora reutiliza solo un QGraphicsOpacityEffect
  existente y no reemplaza efectos graficos incompatibles.
- `Toast` ya no solicita una transicion de opacidad porque su sombra impide
  realizarla de forma segura; se muestra directamente.
- Se conservaron la pausa/reanudacion por hover y el auto-cierre.
- Se agregaron pruebas de sombra, opacidad, secuencias simultaneas, cambio de
  pantalla, redimensionamiento y auto-cierre.

## Comandos y resultados
- `ruff check src\pea\gui\componentes\animacion.py src\pea\gui\componentes\toast.py tests\unit\test_componentes_gui.py`:
  aprobado.
- `pytest tests\unit\test_componentes_gui.py -q`: 18 pasaron.
- Escenario Qt offscreen con Toast de exito y error: ambos visibles con
  QGraphicsDropShadowEffect; cambio de pantalla completado; temporizador
  pausado sobre el Toast y reanudado al salir; cero avisos QPainter o
  QWidgetEffectSourcePrivate.
- `git diff --check`: aprobado.
- Pylance mantiene hallazgos previos ajenos a este cambio: argumento de tipo
  `object` en `crear_animacion_propiedad()` y firma de `enterEvent()` en Toast.

## Decisiones
La animacion de 180 ms no se aplica al Toast porque implicaria componer opacidad
con la sombra existente. Se priorizo mostrar inmediatamente el aviso sin
alterar el estilo ni su temporizador. Los widgets sin efecto siguen pudiendo
animarse.

## Pendientes y siguiente paso
La interaccion visual se verifico con Qt offscreen; una comprobacion en una
sesion de escritorio Windows no se ejecuto.
