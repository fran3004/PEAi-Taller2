---
tipo: bitacora
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[GUI-Diseno-Python]]"
origen: "Correccion del formateo de años e identificadores en tablas GUI"
agente: "Copilot"
rama: "feat/python-cierre-francisco"
commit: ""
---

# Formato de años y cantidades en tablas

## Objetivo
Evitar separadores de miles en años e identificadores sin perder el formato
colombiano de las cantidades.

## Que se hizo
- Se incorporo `ROL_FORMATO_NUMERO`: el delegado agrupa solo celdas marcadas
  por su modelo como cantidades.
- `ModeloTabla` marca columnas de conteo conocidas y conserva valores numericos
  como numeros en DisplayRole.
- Los directorios de Investigadores y Grupos marcan sus columnas de cantidades.
- El catálogo de Productos declara que sus celdas de Año no son cantidades.
- Se agrego una prueba donde 2022 se presenta como `2022` y 1234 como `1.234`.

## Comandos y resultados
- `pytest tests\unit\test_tabla_ficha_dialogos.py tests\unit\test_pantallas_finales.py -q`:
  19 pasaron.
- `ruff check` para los seis archivos fuente y prueba modificados: aprobado.
- La inspeccion de los gráficos encontró que las etiquetas del eje temporal
  usan `str(anio)` y que `formatear_entero` se reserva para conteos.
- Pylance: `modelo_tabla.py` sin diagnósticos nuevos; los diagnósticos
  reportados en `tabla.py` son preexistentes.

## Decisiones
El delegado consume un rol explícito, por lo que no infiere un año desde el
valor numérico. Las columnas genéricas de cantidad se identifican por su
encabezado en el modelo central; los modelos especializados asignan el rol
directamente.

## Pendientes y siguiente paso
Continuar con el ajuste de textos, cabeceras y pestañas.
