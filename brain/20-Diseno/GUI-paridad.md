---
tipo: nota-de-diseno
estado: revisado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[_Indice]]"
  - "[[GUI-Diseno-Python]]"
  - "[[Arquitectura]]"
  - "[[Interoperabilidad]]"
  - "[[ADR-0011-Paridad-arquitectural-Python-Cpp]]"
  - "[[ADR-0012-Diseno-GUI-y-navegacion]]"
  - "[[ADR-0016-Alcance-de-pantallas-y-datos-del-boceto]]"
  - "[[SPEC]]"
origen: "Rediseño de la interfaz de Python (2026-10-03); contrato para el rediseño posterior de C++"
---

# Diseño · Contrato visual entre Python y C++

## Propósito

Esta nota responde una sola pregunta: **qué deberá igualar la interfaz de C++ cuando se rediseñe**, tomando como modelo la de Python.

- La **fuente de verdad visual** es [[GUI-Diseno-Python]]. Esta nota no describe pantallas; solo fija el contrato.
- La interfaz de **C++ todavía no está rediseñada** y se hará con prompts aparte. Mientras tanto, `cpp/src/gui/` conserva su primera versión y **no debe usarse como referencia visual**.
- La paridad **arquitectónica y funcional** (mismas capas, mismas estructuras, mismos resultados) sigue vigente por [[ADR-0011-Paridad-arquitectural-Python-Cpp]].

## Estado

| Elemento | Python | C++ |
|---|---|---|
| Diseño visual | Definido en [[GUI-Diseno-Python]] | **Pendiente** (prompts aparte) |
| Navegación | Barra superior con 7 pestañas | Pendiente |
| Gráficos | `QPainter` | Pendiente (`QPainter` previsto) |
| Red de coautoría | `QGraphicsView` ([[ADR-0015-Analisis-de-red-nativo]]) | Pendiente |
| Pruebas de interfaz | `tests/unit/test_gui_completa.py` | `cpp/tests/test_gui.cpp` (a actualizar) |

## Lo que C++ deberá igualar

1. **Navegación y textos**: mismas siete pestañas, en el mismo orden y con el mismo texto; mismos botones y mensajes de la sección 7.2 de [[GUI-Diseno-Python]].
2. **Tokens**: mismos colores (hex), escala tipográfica, radios y espaciados de la sección 4 de [[GUI-Diseno-Python]].
3. **Colores de datos**: la misma tipología, validación y categoría con el mismo color en todas las pantallas.
4. **Estructura de ventana**: barra superior con degradado y filete institucional UPC, zona de contenido y pie institucional.
5. **Tablas**: mismas columnas, mismo orden y mismos encabezados que en Python.
6. **Formato de números**: miles con punto, decimales con coma, porcentajes con espacio fino.
7. **Cálculos nuevos**: la serie por año y tipología, el grafo de coautoría y sus métricas deben dar **el mismo resultado** que Python, verificado con el oráculo canónico descrito en [[Interoperabilidad]].
8. **Atajos**: los de la sección 12 de [[GUI-Diseno-Python]].

## Lo que C++ no tiene que igualar

- La implementación (cada lenguaje usa su API de Qt).
- Los detalles de animación y sombra, mientras el resultado se vea cuidado y consistente.
- El efecto de barra de título oscura de Windows.

## Deuda de paridad funcional que deja el rediseño de Python

Servicios nuevos creados para la interfaz de Python que C++ deberá replicar:

| Servicio | Para qué sirve | Verificación |
|---|---|---|
| `serie_anual_por_categoria` | Barras apiladas por año y tipología (calculado desde el [[Hipercubo]]) | Comparar contra el oráculo |
| `red_coautoria` (con grado, intermediación y densidad) | Análisis de redes (calculado desde la [[Multilista]]) | Mismo grafo y mismas métricas con datos canónicos |
| `actualizar_producto` | Editar cualquier dato de un producto (requisito 9 y 11 del taller) | Prueba de cascada y deshacer |

## Decisiones relacionadas
- [[ADR-0011-Paridad-arquitectural-Python-Cpp]]
- [[ADR-0012-Diseno-GUI-y-navegacion]]
- [[ADR-0016-Alcance-de-pantallas-y-datos-del-boceto]]

## Riesgos y casos borde
- Si C++ se rediseña sin leer esta nota, puede reproducir el diseño anterior; por eso `AGENTS.md` apunta a [[GUI-Diseno-Python]].
- Las diferencias de renderizado de fuentes entre lenguajes son aceptables; las de colores, textos y orden de columnas no.
