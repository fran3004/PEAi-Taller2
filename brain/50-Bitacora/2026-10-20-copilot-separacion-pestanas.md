---
tipo: bitacora
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[GUI-Diseno-Python]]"
origen: "Solicitud del usuario sobre la distribución visual de los iconos de navegación"
agente: "Copilot"
rama: "feat/python-cierre-francisco"
commit: ""
---

# Distribución visual de pestañas

## Objetivo
Usar mejor el espacio libre de la barra superior y dar una separación uniforme
a los siete iconos de navegación.

## Qué se hizo
- La zona de pestañas ocupa el espacio central restante entre la marca y los
  controles de sesión.
- Los botones conservan su ancho responsivo y se distribuyen con separaciones
  flexibles y equitativas.
- Se añadió una prueba que verifica que el espacio se distribuya y que las
  separaciones entre pestañas sean uniformes.
- Se actualizó el criterio de navegación en `GUI-Diseno-Python.md`.

## Comandos y resultados
- `python -m pytest -q tests/unit/test_gui_completa.py`: 22 pasaron.
- `python -m ruff check src/pea/gui/ventana_principal.py tests/unit/test_gui_completa.py`:
  aprobado.
- Medición Qt con la fuente Inter en las tres anchuras: 1100 px conserva
  separaciones de 4–5 px; 1366 px distribuye las pestañas con 20–21 px; a
  1920 px las etiquetas completas permanecen visibles.
- `git diff --check`: sin errores.

## Decisiones
Las separaciones son flexibles y simétricas en vez de fijar un número mayor
de píxeles. De esta forma se aprovecha el espacio disponible sin forzar
desbordes en la ventana compacta.

## Pendientes y siguiente paso
- Investigar las pruebas de columnas responsivas de Grupos e Investigadores
  que fallaron en la ejecución completa.
- Continuar con los histogramas del servicio estadístico.
