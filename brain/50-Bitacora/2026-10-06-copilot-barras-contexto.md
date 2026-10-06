---
tipo: bitacora
estado: revisado
creado: 2026-10-06
actualizado: 2026-10-06
relacionado:
  - "[[GUI-Diseno-Python]]"
origen: "Correccion del renderizado de barras de contexto superiores"
agente: "Copilot"
rama: "master"
---

# Correccion de barras de contexto

## Objetivo
Evitar el truncamiento horizontal de titulos y subtitulos institucionales sin
alterar la distribucion funcional de las pantallas.

## Que se hizo
- Se reemplazo `QSizePolicy.Ignored` en los subtitulos de Investigadores,
  Grupos y Productos por una politica preferida y compatible con ajuste de
  texto.
- Se agrego `wordWrap` y ancho minimo cero a los subtitulos de las barras
  afectadas.
- Se dio stretch real a las columnas textuales de Investigadores, Grupos,
  Productos y Redes.
- Investigadores ahora agrupa titulo y subtitulo en una columna vertical,
  igual que las otras barras.
- Las barras mantienen un minimo de 56 px y pueden crecer hasta 68 px cuando
  el ajuste de texto lo necesita.
- Se conservaron los controles ChipVentana y Exportar fuera de la columna
  flexible.

## Comandos y resultados
- `python -m ruff check src tests`: aprobado.
- `python -m pytest tests\unit`: 217 pasaron, 1 deseleccionada.
- `python -m pea.gui --autoprueba` con Qt offscreen: completada exitosamente.
- Comprobacion geometrica en 1100x700, 1366x768 y 1920x1080: cuatro
  subtitulos completos, cero problemas de altura.
- `python tools\brain\verificar_brain.py`: 120 notas, cero errores y cero
  advertencias.

## Decisiones
Se mantuvo el cambio instantaneo de las barras y no se introdujeron barras
horizontales ni truncamiento visual. Configuracion ya contaba con stretch y
ajuste de texto; Inicio y Acerca de no presentan una barra institucional
equivalente.

## Pendientes y siguiente paso
Ninguno dentro del alcance de esta correccion.
