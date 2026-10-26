---
tipo: adr
estado: aprobado
creado: 2026-10-25
actualizado: 2026-10-25
relacionado:
  - "[[00-Inicio]]"
  - "[[Arquitectura]]"
  - "[[Modelo-Productos]]"
  - "[[Paridad-Python-Cpp]]"
  - "[[ADR-0026-Indicadores-parcial-y-archivos-locales]]"
origen: "Solicitud del propietario: cumplir el enunciado del Parcial 2 con las URL dadas y entregar la especificación Word IEEE 830"
numero: 27
decision: "Estimación opcional y declarada de categorías, respuestas del parcial y especificación Word"
---

# ADR · Estimación declarada de categorías y especificación Word

Con las URL del enunciado, SCIENTI no publica el cuartil ni el nivel de calidad de ningún
producto. El modo estricto de la versión 0.2.0 excluye esos productos y el indicador del
grupo y del investigador resulta 0, lo que no responde de forma útil al parcial.

Se añade, de forma **opcional y declarada**, la estimación de categorías: a cada producto
sin categoría se le asigna la de menor peso de su tipología (artículo ART_D, libro LIB_C,
capítulo CAP_LIB_C, software SF, trabajo dirigido TD_B/TM_B/TP_B). Nunca sustituye una
categoría informada, no se aplica a proyectos ni a trabajos en curso, no modifica el catálogo
original, enumera cada producto estimado y marca el resultado como estimado e incompleto.
El modo estricto sigue siendo el predeterminado. Python y C++ aplican la misma tabla y sus
resultados se comparan en `tools/interop/verificar_parcial.py`.

También se corrigen dos defectos hallados al usar datos reales: los catálogos descargados no
podían reabrirse porque las fechas de vinculación de SCIENTI («2013/1», «Actual») no eran ISO,
y C++ guardaba el subtipo «TrabajoDirigido» frente a «Trabajo dirigido» de Python.

El comando `respuestas-parcial` (`--respuestas` en las entradas `Parcial2_FF_SM`) descarga las
dos URL y calcula ambos indicadores. Se revierte la exclusión del Word y los diagramas UML:
`entrega/Especificacion_Tecnica_PEAi.docx` sigue la plantilla IEEE 830 e incluye casos de uso,
secuencia, clases, despliegue, capturas y trazabilidad; se genera con `tools/generar_especificacion.py`.
El video sigue fuera de alcance.
