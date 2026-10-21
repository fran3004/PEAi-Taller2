---
tipo: adr
estado: aprobado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[Ingesta]]"
  - "[[SPEC]]"
  - "[[Modelo-Productos]]"
  - "[[Paridad-Python-Cpp]]"
origen: "Discrepancia entre el encabezado legado tipo_categoria y la tipología mayor requerida por RF-04"
numero: ADR-0022
decision: "Interpretar tipo_categoria como etiqueta de producto; mapear etiquetas reconocidas al tipo mayor y preservar la etiqueta como subtipo cuando no haya uno explícito"
---

# ADR-0022 · Interpretación de la categoría legada en CSV

## Contexto

RF-04 define `tipo_mayor` con los códigos `GNC`, `DTI`, `ASC` y `FRH`, y exige
un subtipo específico. El ejemplo previo de `Ingesta.md` usaba el encabezado
`tipo_categoria` con el valor `Artículo Tipo A1`, que no es uno de esos códigos.
El Modelo clasifica los artículos A1 en GNC, pero no define directamente el
significado de ese encabezado CSV legado.

## Opciones consideradas

1. Copiar `tipo_categoria` literalmente a `tipo_mayor`: no distingue un
   subtipo descriptivo de un código normativo y produce registros inválidos.
2. Rechazar siempre `tipo_categoria`: evita inferencias, pero rompe el ejemplo
   documentado y no permite importar categorías que RF-04 sí clasifica.
3. Interpretar solo etiquetas documentadas, conservar el texto de categoría
   como subtipo cuando falte uno explícito y rechazar valores desconocidos o
   contradictorios. **Elegida como supuesto de compatibilidad acotado.**

## Decisión

`tipo_categoria` se acepta como nombre legado de columna, pero su valor se
normaliza contra la lista de categorías de RF-04 y las tipologías del Modelo:
artículos A1, A2, B y C, libros y capítulos resultado de investigación,
patentes de invención, las categorías enumeradas de DTI, ASC y FRH, además de
los códigos directos `GNC`, `DTI`, `ASC` y `FRH`. Así, `Artículo Tipo A1` se
asigna a `GNC`; si no hay un `subtipo` explícito, se conserva el valor original
como subtipo. La comparación ignora mayúsculas, tildes y espacios redundantes.

Cuando existen ambas columnas, `tipo_categoria` y `tipo_mayor` deben concordar.
Se rechazan las etiquetas no reconocidas, los códigos de tipo mayor inválidos
y las combinaciones contradictorias. La implementación Python y C++ debe
mantener la misma tabla y los mismos errores verificables con el fixture
compartido.

## Consecuencias

- El ejemplo documentado importa al producto con `tipo_mayor=GNC` y conserva
  `Artículo Tipo A1` como subtipo.
- Los valores que no se puedan asignar con evidencia explícita se reportan como
  errores de fila en lugar de guardarse como una categoría mayor inventada.
- Esta decisión solo afecta la importación CSV; no modifica datos remotos ni
  sustituye la clasificación explícita por código en las demás rutas.
- La lista admitida es deliberadamente acotada a RF-04; si se amplía el
  vocabulario CSV, debe contrastarse con el Modelo antes de incorporarlo.
