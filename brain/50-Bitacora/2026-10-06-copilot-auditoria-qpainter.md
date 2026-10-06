---
tipo: bitacora
estado: revisado
creado: 2026-10-06
actualizado: 2026-10-06
relacionado:
  - "[[GUI-Diseno-Python]]"
origen: "Auditoria exclusiva de QPainter y QGraphicsEffect en la GUI Python"
agente: "Copilot"
rama: "master"
---

# Auditoria de QPainter en la GUI Python

## Objetivo
Garantizar el ciclo de vida correcto de todos los `QPainter` creados por la GUI
Python y descartar reentrancia por composicion de efectos.

## Que se hizo
- Se localizaron todos los `QPainter`, `paintEvent`, pintores sobre
  `QImage`/`QPixmap` y efectos graficos bajo `src/pea/gui`.
- Se corrigieron tres pintores sin finalizacion explicita: el filete
  institucional, la barra superior y la barra de progreso de tipologia.
- Se corrigio el pintor de la barra de tipologia en Investigadores.
- Se protegieron con `try/finally` los `paintEvent` revisados y con context
  manager los pintores sobre imagenes.
- Los `QGraphicsEffect` encontrados se crean fuera de `paintEvent`; no se
  encontro `QGraphicsOpacityEffect` aplicado a paginas del `QStackedWidget`.

## Comandos y resultados
- `python -m ruff check src tests`: aprobado.
- `python -m pytest tests\unit`: 216 pasaron, 1 deseleccionada.
- `python -m pea.gui --autoprueba` con Qt offscreen: completada exitosamente.
- Navegacion repetida: 45 ciclos, cero errores de indice, visibilidad o efectos
  residuales.
- La salida de la autoprueba no contiene `QPainter::begin`,
  `QPainter::translate`, `QPainter::worldTransform`,
  `QPainter::setWorldTransform` ni `QWidgetEffectSourcePrivate::pixmap`.

## Decisiones
Los metodos `paint()` de `QGraphicsItem` reciben el `QPainter` administrado por
Qt y no crean otro painter; por eso no se les agrego `end()`.

## Pendientes y siguiente paso
La comprobacion con cursor fisico y ventanas nativas debe repetirse en una
sesion interactiva, ya que las pruebas automatizadas se ejecutaron offscreen.
