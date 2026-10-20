---
tipo: resultado-de-pruebas
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[SPEC]]"
  - "[[Trazabilidad]]"
  - "[[Variables-entrada-salida]]"
  - "[[Ingesta]]"
  - "[[Estructuras]]"
  - "[[GUI-Diseno-Python]]"
  - "[[Interoperabilidad]]"
origen: "Contraste de los requisitos funcionales del PDF docs/entrada/Taller 2 EdD (2026-09-24) - G 8.pdf con el código, las pruebas y la documentación del proyecto"
---

# Matriz de contraste del Taller 2

## Alcance

Fuente: `docs/entrada/Taller 2 EdD (2026-09-24) - G 8.pdf`, páginas 1–3. Esta matriz contrasta los requisitos funcionales introductorios y los puntos 1–14 con el estado del código y la evidencia local disponible.

Los estados describen la evidencia observada; «cumple» no significa que se hayan verificado los conteos actuales de Supabase ni todos los escenarios de datos reales. Los números de requisitos citados corresponden a la numeración literal del PDF, no a los identificadores R0–R12 del `SPEC.md`.

## Requisitos generales del enunciado

| Requisito | Estado | Evidencia | Contraste y límite |
|---|---|---|---|
| Gestionar mediante operaciones CRUD y persistir los datos de grupos, investigadores y productos | parcial | `src/pea/servicios/servicio_dominio.py`; `cpp/src/servicios/catalogo_investigacion.cpp`; `tests/unit/test_servicios_nuevos.py`; `cpp/build` · `ctest` | Python y C++ tienen servicios, estructuras y repositorios. Las pruebas locales pasan; no se verificó una escritura real contra Supabase durante este contraste. |
| Representar información con listas, multilistas, pilas y colas | cumple | `src/pea/estructuras/`; `cpp/include/pea/estructuras/`; `tests/unit/test_estructuras.py`; `cpp/tests/test_estructuras.cpp` | Hay implementaciones propias en ambos lenguajes; el hipercubo recomendado también está implementado. |
| Considerar el hipercubo recomendado por el enunciado | cumple | `src/pea/estructuras/hipercubo.py`; `cpp/include/pea/estructuras/hipercubo.hpp`; `tests/unit/test_hipercubo.py`; `cpp/tests/test_hipercubo.cpp` | Las estadísticas de servicio agregan desde el hipercubo en memoria. |

## Puntos funcionales 1–14

| Punto PDF | Requisito importante | Estado | Evidencia | Contraste y pendiente |
|---:|---|---|---|---|
| 1 | Gestionar grupos e investigadores de la institución en las dos soluciones | cumple | `src/pea/dominio/grupo.py`; `src/pea/dominio/investigador.py`; `src/pea/servicios/servicio_dominio.py`; `cpp/include/pea/dominio/`; `cpp/src/servicios/catalogo_investigacion.cpp`; `cpp/tests/test_estructuras.cpp` | Existen modelos, catálogo/servicios y estructuras en Python y C++. `ctest --test-dir cpp/build --output-on-failure` pasó. |
| 2 | Gestionar productos de investigación asociados a grupos e investigadores | cumple | `src/pea/estructuras/multilista.py`; `src/pea/servicios/servicio_dominio.py`; `cpp/include/pea/estructuras/multilista.hpp`; `tests/unit/test_estructuras.py` | La multilista mantiene productos enlazados con sus grupos y autores. |
| 3 | Gestionar, por grupo, integrantes, plan y productos | parcial | `src/pea/dominio/integrante.py`; `src/pea/dominio/plan.py`; `src/pea/servicios/servicio_dominio.py`; `src/pea/gui/pantallas/grupos.py` | Se gestionan integrantes y productos asociados. Existe la entidad `Plan`, pero no se encontró integración de planes en el catálogo/servicio de dominio ni en la ficha del grupo. |
| 4 | Gestionar información personal del investigador y sus productos | cumple | `src/pea/dominio/investigador.py`; `src/pea/servicios/servicio_dominio.py`; `src/pea/gui/pantallas/investigadores.py`; `src/pea/estructuras/multilista.py` | Se gestionan atributos de investigador y su relación con productos mediante autoría. |
| 5 | Ajustar los datos al documento «Modelo» | parcial | `docs/entrada/Modelo-2024.md`; `brain/40-Fuentes/Modelo.md`; `brain/10-Requisitos/Variables-entrada-salida.md`; modelos en `src/pea/dominio/` | El Modelo está extraído y el diccionario documenta campos y citas. La matriz no certifica aún una correspondencia campo por campo de todas las entidades con cada regla del documento. |
| 6 | Identificar claramente entradas y salidas para grupos, investigadores y productos | cumple | `brain/10-Requisitos/Variables-entrada-salida.md`; `src/pea/dominio/grupo.py`; `src/pea/dominio/investigador.py`; `src/pea/dominio/producto.py` | El diccionario formal separa atributos de entidades y métricas de salida del hipercubo. |
| 7 | Obtener datos desde URL o procesar PDF/CSV | parcial | `src/pea/ingesta/extractor_url.py`; `src/pea/ingesta/extractor_pdf.py`; `src/pea/ingesta/lector_csv.py`; `src/pea/cli.py`; `tests/unit/test_cli_importar_url_lote.py`; `tests/unit/test_ingesta.py` | Hay rutas para extracción URL y lectura PDF/CSV, probadas con fixtures y pruebas locales. No se verificó una descarga real de SCIENTI en esta sesión. |
| 8 | Diseñar una estructura de listas adecuada al problema | cumple | `src/pea/estructuras/lista_doble.py`; `src/pea/estructuras/multilista.py`; `cpp/include/pea/estructuras/lista_doble.hpp`; `cpp/include/pea/estructuras/multilista.hpp`; `brain/20-Diseno/Estructuras.md` | La selección e implementación de listas enlazadas y multilista está documentada y probada. |
| 9 | Crear, eliminar, desactivar y modificar grupos, investigadores y productos, incluyendo categoría y validación del producto | cumple | `src/pea/servicios/servicio_dominio.py`; `tests/unit/test_servicios_nuevos.py`; `tests/unit/test_cascadas.py`; `cpp/tests/test_cascadas.cpp`; `cpp/tests/test_deshacer.cpp` | Los servicios implementan operaciones y reglas de cascada; productos contienen tipología/categoría mayor y estado de validación. Las pruebas locales cubren edición, desactivación y eliminación. |
| 10 | Filtrar por año mediante una ventana de observación | cumple | `src/pea/gui/componentes/filtro_anios.py`; `src/pea/servicios/servicio_aplicacion.py`; `src/pea/servicios/servicio_estadisticas.py`; `tests/unit/test_hipercubo.py`; `tests/unit/test_servicios_nuevos.py` | La ventana temporal se aplica a estadísticas y pantallas; hay pruebas de filtros y agregación. |
| 11 | Permitir editar y modificar cualquier dato | parcial | `src/pea/servicios/servicio_dominio.py`; `src/pea/gui/pantallas/grupos.py`; `src/pea/gui/pantallas/investigadores.py`; `src/pea/gui/pantallas/productos.py`; `tests/unit/test_servicios_nuevos.py` | Hay edición para las entidades principales, pero no se comprobó que cada atributo de entrada del punto 6 pueda editarse desde la GUI. |
| 12.a | En C/C++, presentar estadísticas descriptivas como resumen, tablas y números; no exige GUI | parcial | `cpp/src/cli.cpp`; `cpp/src/tui/aplicacion_tui.cpp`; `cpp/src/servicios/servicio_estadisticas.cpp`; `cpp/build/pruebas_cpp.exe` (35 casos) | C++ tiene resumen CLI, panel institucional, directorios de lectura y estadísticas base; la TUI sigue parcial y no muestra aún todos los gráficos/vistas solicitados. La autoprueba cubre 32 tamaños; no se verificó paridad de conteos con Supabase. |
| 12.b | En Python, mostrar dashboard con estadísticas, histogramas y diagramas de barras | cumple | `src/pea/gui/pantallas/inicio.py`; `src/pea/gui/componentes/graficos/histograma.py`; `src/pea/gui/componentes/graficos/barras_apiladas.py`; `tests/unit/test_graficos_seccion9.py`; `python -m pea.gui --autoprueba` | Hay gráficos e histogramas basados en los servicios/hipercubo. La autoprueba final cubrió 8 pantallas × 3 resoluciones con cero hallazgos. |
| 12.c.i | Permitir una vista estadística por grupo | cumple | `src/pea/servicios/servicio_estadisticas.py` · `obtener_vista_grupo`; `src/pea/gui/pantallas/grupos.py` | Existe vista y ficha estadística de grupo. |
| 12.c.ii | Permitir una vista estadística por investigador | cumple | `src/pea/servicios/servicio_estadisticas.py` · `obtener_vista_investigador`; `src/pea/gui/pantallas/investigadores.py` | Existe vista individual, con indicadores y distribución anual. |
| 12.c.iii | Permitir una vista estadística por producto | parcial | `src/pea/gui/pantallas/productos.py`; `src/pea/servicios/servicio_estadisticas.py` | Existe catálogo y ficha de productos, pero no se encontró una función de estadísticas/vista analítica por producto equivalente a las vistas de grupo e investigador. |
| 13 | El enunciado indica una evaluación de 4.0 si se realizan estos requerimientos | informativo | PDF, página 2, punto 13 | Es una condición de evaluación, no una funcionalidad del programa; el cumplimiento global depende de la evaluación docente. |
| 14.a | Usar Git y GitHub | cumple | Historial Git de la rama `feat/python-cierre-francisco`; repositorio `fran3004/PEAi-Taller2` | Hay historial y ramas Git; el repositorio GitHub existe. |
| 14.b | Usar base de datos | parcial | `src/pea/cliente_http.py`; `src/pea/datos/repositorios.py`; `supabase/migrations/`; `tests/test_contrato_supabase.py` | La aplicación usa el contrato REST/RPC de Supabase. La prueba remota de conteos quedó omitida por falta de variables de sesión normal y clave publicable; no se verificaron conteos remotos aquí. |
| 14.c | Usar GUI creativa | cumple | `src/pea/gui/`; `cpp/src/gui/ventana_principal.cpp`; pruebas GUI Python y `cpp/tests/test_gui.cpp` | Hay GUI en Qt Widgets para ambos lenguajes. Se validaron visualmente las 24 capturas Python y pasó CTest; no se hizo revisión visual de la ventana C++ en esta sesión. |
| 14.d | Integrar lenguajes (interoperabilidad) | parcial | `brain/20-Diseno/Interoperabilidad.md`; contratos JSON, REST/RPC y Supabase compartidos | Los clientes comparten contratos y backend, pero no se encontró ni ejecutó una prueba de interoperabilidad directa entre procesos Python y C++. |
| 14.e | Documentar el proyecto | cumple | `README.md`; `brain/10-Requisitos/`; `brain/20-Diseno/`; ADR; `python tools/brain/verificar_brain.py` | Existe documentación de requisitos, arquitectura, datos, estructuras, GUI e ingesta. El verificador de la bóveda terminó con cero errores y una advertencia histórica no relacionada. |
| 14.f | «¿Rust?» | fuera de alcance / pregunta abierta | PDF, página 2, punto 14.f | El propio enunciado lo presenta como pregunta, no como requisito obligatorio; no se implementa Rust. |

## Verificaciones ejecutadas para este contraste

- Suite Python: `python -m pytest -q` → **284 pasaron, 3 excluidas**.
- C++: `ctest --test-dir cpp/build --output-on-failure` → **1/1 pruebas registradas pasaron**.
- GUI Python: `python -m pea.gui --autoprueba` → **0 hallazgos en 24 combinaciones**.
- Calidad: Ruff aprobó; Vulture con confianza 80 no reportó hallazgos.
- Documentación: `python tools/brain/verificar_brain.py` → **0 errores, 1 advertencia histórica** por un enlace ADR-0016 no resuelto en otra bitácora.
- Contrato remoto Supabase: **1 omitida** por variables de sesión normal y clave publicable ausentes; los datos remotos no se verificaron.

## Observaciones de prioridad

1. Integrar la entidad `Plan` con los servicios y la ficha de grupo, o justificar documentalmente por qué el alcance implementado la deja como entidad no operativa.
2. Definir si el punto 12.c.iii requiere métricas agregadas por producto. Si es así, añadir esa vista; actualmente hay ficha/catálogo, no una vista estadística específica.
3. Confirmar que todos los campos editables del punto 6 están disponibles en las interfaces de edición (punto 11).
4. Ejecutar la prueba de conteos remotos cuando el entorno tenga configuradas la sesión normal y la clave publicable.
5. Verificar el formato real del comando de resumen C++ en ejecución, aunque sus pruebas de CTest ya pasan.
