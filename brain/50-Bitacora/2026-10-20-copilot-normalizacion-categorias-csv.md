---
tipo: bitacora
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[Ingesta]]"
  - "[[Paridad-Python-Cpp]]"
  - "[[ADR-0022-Interpretacion-categoria-legada-csv]]"
  - "[[SPEC]]"
origen: "Cierre de la compatibilidad del CSV legado y corrección de años en la ingesta SCIENTI"
agente: "Copilot"
rama: "feat/python-cierre-francisco"
commit: ""
---

# Bitácora · Normalización de categorías CSV

## Objetivo

Completar la conversión compatible de `tipo_categoria` en Python y C++, y
corregir la extracción de años SCIENTI para evitar confundir identificadores
bibliográficos con años de publicación o inventar valores predeterminados.

## Qué se hizo

- Se normalizó el encabezado legado `tipo_categoria` según las etiquetas
  reconocidas por RF-04 y el Modelo; las categorías desconocidas o
  contradictorias se rechazan. La interpretación se acotó y registró como
  supuesto en ADR-0022.
- Se compartió entre Python y C++ un fixture que verifica categorías válidas,
  contradicciones y valores inválidos.
- El extractor SCIENTI busca el año en su contexto bibliográfico para no tomar
  números de ISSN/ISBN. Los productos sin año válido se omiten con advertencia,
  y el CSV canónico deja el año vacío en vez de usar 2024.
- Se ajustó la prueba del nombre truncado en la zona de archivos para aceptar
  la elipsis visual prevista, manteniendo disponible el nombre completo en el
  tooltip.
- Se actualizaron la documentación de ingesta, la matriz de paridad y las
  pruebas de Python/C++.

## Comandos y resultados

- `.\scripts\verificar.ps1`: terminó con código 0.
- Python: 301 pruebas aprobadas y 3 excluidas.
- C++: compilación con `-Werror` y suite doctest aprobadas; CTest 1/1.
- Autoprueba TUI: 32 pantallas renderizadas, sin hallazgos.
- Bóveda: 0 errores y 1 aviso preexistente por el enlace no resuelto
  `ADR-0016` en otra bitácora.
- `git diff --check`: correcto antes de crear esta nota; se repetirá como
  verificación final.
- No se accedió a Supabase, no se leyeron secretos ni se modificaron datos
  remotos.

## Decisiones

- `tipo_categoria` se conserva como encabezado CSV legado, pero sus valores se
  convierten solo cuando la clasificación está respaldada por RF-04 y el
  Modelo; no se inventan categorías.
- Si la fuente SCIENTI no informa un año dentro del rango permitido, el
  producto no se incorpora. Se comunica la omisión y no se usa un año
  sustituto.

## Pendientes y siguiente paso

- Crear un commit `fix:` con los cambios revisados. No hacer push.
