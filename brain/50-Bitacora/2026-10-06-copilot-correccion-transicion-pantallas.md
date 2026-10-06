---
tipo: bitacora
estado: revisado
creado: 2026-10-06
actualizado: 2026-10-06
relacionado:
  - "[[GUI-Diseno-Python]]"
origen: "Correccion del renderizado y transicion entre pantallas de la GUI Python"
agente: "Copilot"
rama: "master"
---

# Correccion de transicion entre pantallas

## Objetivo
Eliminar la corrupcion visual causada por efectos de opacidad aplicados a paginas
complejas del `QStackedWidget`.

## Que se hizo
- Se reemplazo la transicion de paginas por un cambio sincronico de indice.
- Se retira cualquier `QGraphicsEffect` residual de la pagina anterior y de la
  nueva antes de pintarla.
- Se conservo `animar_desvanecimiento()` para widgets sencillos que no son
  paginas del `QStackedWidget`.
- No se modificaron servicios, repositorios, estructuras ni la distribucion de
  las pantallas.

## Comandos y resultados
- `python -m ruff check src tests`: aprobado.
- `python -m pytest tests\unit`: 216 pasaron, 1 deseleccionada.
- `python -m pea.gui --autoprueba` con Qt offscreen: completada exitosamente,
  sin mensajes `QPainter`.
- Navegacion repetida y redimensionamiento: 45 cambios de pantalla, una pagina
  visible y cero efectos residuales.
- `git diff --check`: aprobado.

## Decisiones
Se priorizo la estabilidad del pipeline de pintura sobre una animacion
cosmetica. `PEA_SIN_ANIMACIONES` permanece disponible para las animaciones de
componentes que no son paginas completas.

## Pendientes y siguiente paso
Ninguno dentro del alcance de esta correccion.
