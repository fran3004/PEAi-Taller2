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
Evitar el truncamiento, la superposicion y la salida del espacio disponible de
titulos y nombres en las barras y fichas laterales, sin alterar la
distribucion funcional de las pantallas.

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
- Se fijo el cuerpo de `FichaLateral` al ancho real del viewport de su
  `QScrollArea`, manteniendo desactivado el desplazamiento horizontal.
- Los nombres y subtitulos de las fichas laterales ahora tienen ancho minimo
  cero, politica expansiva y altura preferida para envolver nombres extensos.
- Los valores largos del panel de detalles de Grupos se envuelven dentro de
  su columna flexible.
- La ficha seleccionada de Redes recibe las mismas restricciones de ancho y
  ajuste de texto.

## Comandos y resultados
- `python -m ruff check src tests`: aprobado.
- `python -m pytest tests\unit`: 217 pasaron, 1 deseleccionada.
- `python -m pea.gui --autoprueba` con Qt offscreen: completada exitosamente.
- Comprobacion geometrica en 1100x700, 1366x768 y 1920x1080: cuatro
  subtitulos completos, cero problemas de altura.
- Auditoria de scrolls y etiquetas laterales en las 8 pantallas y 3
  resoluciones: cero desbordes horizontales y cero etiquetas recortadas.
- Prueba visual con nombres extensos en fichas de Producto y Grupo: texto
  envuelto dentro del viewport.
- `python tools\brain\verificar_brain.py`: 121 notas, cero errores y cero
  advertencias.

## Decisiones
Se mantuvo el cambio instantaneo de las barras y no se introdujeron barras
horizontales ni truncamiento visual. El ancho del cuerpo lateral se sincroniza
con el viewport mediante el filtro de redimensionamiento del area desplazable.
Configuracion ya contaba con stretch y ajuste de texto; Inicio y Acerca de no
presentan una barra institucional equivalente.

## Pendientes y siguiente paso
Ninguno dentro del alcance de esta correccion.
