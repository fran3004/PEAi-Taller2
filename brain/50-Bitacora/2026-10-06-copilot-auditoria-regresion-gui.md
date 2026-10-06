---
tipo: bitacora
estado: revisado
creado: 2026-10-06
actualizado: 2026-10-06
relacionado:
  - "[[GUI-Diseno-Python]]"
  - "[[2026-10-06-copilot-saneamiento-estilos-qss]]"
origen: "Auditoria de regresion posterior a los arreglos de GUI Python"
agente: "Copilot"
rama: "master"
---

# Auditoria de regresion de la GUI Python

## Alcance

Se audito `src/pea/gui` en 1100x700, 1366x768 y 1920x1080. Se regeneraron las ocho pantallas y sus 24 capturas oficiales.

## Resultados

- KPI de Inicio visibles y responsivos.
- Tabla de Productos sin barra horizontal y con columna Título de al menos 200 px.
- FichaProducto sin widgets huérfanos, solapamientos ni acumulación al actualizar.
- Redes carga datos de demostración, inicia en Mín. 1 coautoría y mantiene los nodos dentro del viewport.
- Barra superior sin truncamiento en las resoluciones estándar.
- Configuración conserva campos con altura útil.
- Importar conserva botones, zona de arrastre y texto adaptable.
- Acerca mantiene tarjeta institucional y ficha técnica.
- Pie institucional visible en las tres resoluciones.
- No se detectaron recuadros ni regresiones visuales bloqueantes.

## Comandos y resultados

- `ruff check src tests`: aprobado.
- `python scripts/diagnostico_desborde.py`: ninguna barra horizontal visible en las tres resoluciones.
- `pytest tests/unit/test_estilo_recursos.py -k guardian -vv`: 1 pasada.
- `pytest tests/unit`: 216 pasaron, 1 deseleccionada.
- Pruebas específicas de Inicio, Investigadores y Grupos: 35 pasaron.
- Pruebas clave de GUI, Productos, Redes, Importar, Configuración y Acerca: 53 pasaron.
- `python -m pea.gui --autoprueba` con Qt offscreen: completada exitosamente.
- Capturas oficiales: 24 PNG válidos en `datos/capturas/oficiales/`.

## Observaciones

La autoprueba informa advertencias de geometría de widgets internos, pero no detecta barras horizontales ni termina con error. No se realizó ninguna corrección de código porque no apareció una regresión reproducible.
