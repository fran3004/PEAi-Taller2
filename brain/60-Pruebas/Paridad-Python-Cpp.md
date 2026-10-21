---
tipo: resultado-de-pruebas
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[SPEC]]"
  - "[[GUI-paridad]]"
  - "[[ADR-0019-Cpp-terminal-con-ftxui]]"
  - "[[Trazabilidad]]"
origen: "Matriz de paridad funcional y operativa entre la lógica de Python y el núcleo C++ del proyecto"
---

# Matriz de paridad Python ↔ C++

## Propósito

Esta matriz contrasta las operaciones públicas de Python con el código C++ inspeccionado. `igual` indica que existe una implementación equivalente y debe acompañarse de pruebas; no certifica por sí solo paridad byte a byte, persistencia remota ni aceptación de interfaz. La evidencia de la iteración se limita a los tests C++ indicados y a `pea-cpp --autoprueba`.

## Estado general

| Operación / función | Python | C++ existente | Estado | Tarea |
|---|---|---|---|---|
| Crear grupo | `ServicioDominio.crear_grupo()` | `CatalogoInvestigacion::crear_grupo()` y repositorios | igual | Mantener contratos y validaciones en ambos lados |
| Buscar grupo por id | `ServicioDominio.buscar_grupo()` | `CatalogoInvestigacion::buscar_grupo()` | igual | Validar resultados con fixtures y pruebas |
| Actualizar grupo | `ServicioDominio.actualizar_grupo()` | `CatalogoInvestigacion::actualizar_grupo()` | igual | Probar edición de campos obligatorios |
| Desactivar grupo | `ServicioDominio.desactivar_grupo()` | soporte en catálogo y repositorio | igual | Revisión de cascada Reversión y persistencia |
| Activar grupo | `ServicioDominio.activar_grupo()` | soporte en catálogo y repositorio | igual | Validar reactivación en servicios |
| Eliminar grupo | `ServicioDominio.eliminar_grupo()` | `CatalogoInvestigacion::eliminar_grupo()` | igual | Verificar sin datos huérfanos |
| Crear investigador | `ServicioDominio.crear_investigador()` | `CatalogoInvestigacion::crear_investigador()` | igual | Mantener reglas de validación |
| Buscar investigador | `ServicioDominio.buscar_investigador()` | `CatalogoInvestigacion::buscar_investigador()` | igual | Verificar búsquedas por ids y nombres |
| Actualizar investigador | `ServicioDominio.actualizar_investigador()` | `CatalogoInvestigacion::actualizar_investigador()` | igual | Confirmar restricciones y persistencia |
| Desactivar investigador | `ServicioDominio.desactivar_investigador()` | soporte en catálogo | igual | Confirmar reversión y trazabilidad |
| Activar investigador | `ServicioDominio.activar_investigador()` | soporte en catálogo | igual | Validar con pruebas de dominio |
| Eliminar investigador | `ServicioDominio.eliminar_investigador()` | `CatalogoInvestigacion::eliminar_investigador()` | igual | Comprobar dependencias y cascadas |
| Crear producto | `ServicioDominio.crear_producto()` | `CatalogoInvestigacion::crear_producto()` | igual | Validaciones de categoría / validación |
| Buscar producto | `ServicioDominio.buscar_producto()` | `CatalogoInvestigacion::buscar_producto()` | igual | Confirmar que devuelve producto activo e inactivo |
| Actualizar producto | `ServicioDominio.actualizar_producto()` | `CatalogoInvestigacion::actualizar_producto()` | distinto | C++ actualiza metadatos con compensación y undo; falta cambio de grupo y prueba diferencial |
| Desactivar producto | `ServicioDominio.desactivar_producto()` | soporte en catálogo/estructura | igual | Confirmar ser reversible |
| Activar producto | `ServicioDominio.activar_producto()` | soporte en catálogo | igual | Validar estado activo cuando se reanuda |
| Eliminar producto | `ServicioDominio.eliminar_producto()` | `CatalogoInvestigacion::eliminar_producto()` | igual | Verificar remoción de multilista y relaciones |
| Vincular integrante | `ServicioDominio.vincular_integrante()` | `CatalogoInvestigacion::vincular_integrante()` | igual | Revisar reglas de pertenencia y locales |
| Desvincular integrante | `ServicioDominio.desvincular_integrante()` | `CatalogoInvestigacion::desvincular_integrante()` | igual | Comprobar limpieza de enlaces |
| Enlazar producto a grupo | `multilista` / servicio | `multilista` + catálogo | igual | Verificar eliminación en cascada |
| Enlazar producto a investigador | `multilista` / servicio | `multilista` + catálogo | igual | Confirmar nodos compartidos y exclusión |
| Pila de deshacer | `PilaDeshacer` / servicio | `Pila` + `CatalogoInvestigacion` | igual | Mantener LIFO y reversiones |
| Cola de importación | `ColaImportacion` | `Cola` / `ServicioIngesta` | igual | Validar encolado y procesamiento |
| Recargar catálogo | `recargar_todo()` | `CatalogoInvestigacion::recargar_todo()` | igual | Releer revisión remota y comparar |
| Verificar revisión | `controlador_revision` | `RevisionController` + `CatalogoInvestigacion` | igual | Revalidar lock optimista |
| Resumen general | `resumen_dict()` / `resumen_json()` | `CatalogoInvestigacion::resumen_dict()` | igual | Confirmar conteos de activos y totales |
| Productos por año | `ServicioEstadisticas.productos_por_anio()` | `ServicioEstadisticas` | igual | Validar total y rangos por filtro |
| Productos por categoría | `ServicioEstadisticas.productos_por_categoria()` | `ServicioEstadisticas` | igual | Comprobar orden y agregación |
| Serie anual por categoría | `serie_anual_por_categoria` | `ServicioEstadisticas` | igual | Verificar sumas por año |
| Productos por validación | `productos_por_validacion()` | `productosPorValidacion()` | igual | Comparar resultados diferenciales |
| Productos por grupo | `productos_por_grupo()` | `productosPorGrupo()` | igual | Comparar resultados diferenciales |
| Productos por investigador | `productos_por_investigador()` | `productosPorInvestigador()` | igual | Comparar resultados diferenciales |
| Promedio por investigador | `promedio_por_investigador()` | `promedioPorInvestigador()` | igual | Verificar agrupación y redondeo con fixtures |
| Top 5 investigadores | `top_5_investigadores()` | `top5Investigadores()` | igual | Comparar desempate y filtro de grupo |
| Top 5 grupos | `top_5_grupos()` | `top5Grupos()` | igual | Comparar desempate |
| Porcentajes por categoría | `porcentajes_por_categoria()` | `porcentajesPorCategoria()` | igual | Comparar precisión y totales |
| Porcentajes por validación | `porcentajes_por_validacion()` | `porcentajesPorValidacion()` | igual | Comparar precisión y totales |
| Vista institucional | `obtener_vista_institucional()` | `obtenerVistaInstitucional()` | igual | Falta prueba de contrato JSON diferencial |
| Vista de grupo | `obtener_vista_grupo()` | `obtenerVistaGrupo()` | igual | Falta prueba de contrato JSON diferencial |
| Vista de investigador | `obtener_vista_investigador()` | `obtenerVistaInvestigador()` | igual | Falta prueba de contrato JSON diferencial |
| Vista de producto | No hay vista estadística pública equivalente | Sin función pública equivalente | falta | Definir una vista solo si está respaldada por el requisito; no inventar métricas |
| Histograma productos por investigador | `distribucion_productos_por_investigador()` | `distribucionProductosPorInvestigador()` | igual | Casos de rangos cubiertos en `test_filtro_estadisticas.cpp`; falta comparación diferencial |
| Histograma por año en vista de investigador | `vista_investigador()` | `obtenerVistaInvestigador()` | igual | Cubierto por `test_filtro_estadisticas.cpp`; falta comparación diferencial Python/C++ |
| Hipercubo rebanada | `Hipercubo.rebanada()` | `Hipercubo5D` / subcubo | igual | Probar ventana temporal y dimensiones |
| Enrollar / enrollamiento | `Hipercubo.enrollar()` | `Hipercubo5D` | igual | Comprobar densidad y reagrupación |
| Filtro de años TODOS | `FiltroAnios.TODOS` | equivalente de servicio | igual | Confirmar salida global |
| Filtro de años ULTIMOS N | `FiltroAnios.ULTIMOS` | funcional equivalente | igual | Validar `N` y texto descriptivo |
| Filtro de años RANGO | `FiltroAnios.RANGO` | equivalente | igual | Ordenar desde/hasta y revertir si aplica |
| Filtro de años MODELO_2024 | `FiltroAnios.MODELO_2024` | equivalente | igual | Validar ventanas según tipología |
| Descripción textual del filtro | `descripcion()` | `FiltroAnios` / `ServicioEstadisticas` | igual | Mantener textos de pantalla |
| Importación CSV | `LectorCSV` | `LectorCSV` / `ServicioIngesta` y formulario TUI | fixture compartido de grupos UTF-8/multilínea aprobado; demás tipos e informes aún sin equivalencia completa | Comparar entidades y reportes para grupos, investigadores, productos y autores, incluidas filas inválidas |
| Importación URL | extractor URL / parseador | `ServicioIngesta` + `extractor_url` y formulario TUI | equivalente en núcleo; verificación diferencial pendiente | El formulario solicita anonimización; comparar contenido/informes y probar límites de red |
| Exportación CSV | `exportar_tabla_csv()` y CLI | `comandoExportarCsv()` | serializador contrastado con fixtures compartidos; salida integral aún pendiente | Columnas y reglas de escape del serializador coinciden para UTF-8, CRLF, comas, comillas y saltos; comparar byte a byte los exportadores completos |
| Exportación Markdown y JSON de vista | No especificada para vistas estadísticas | Sin exportador de vistas | No constituye requisito identificado | SPEC exige tablas CSV y gráficos PNG; mantener JSON/Markdown en los flujos de ingesta donde sí se usan, sin inventar una exportación de vistas |
| Modo no interactivo / CLI | `pea.cli` | `pea-cpp` + `pea::cli::ejecutar` | distinto | Comparar salida, argumentos y códigos de salida |
| Modo TUI interactivo | GUI Python | TUI FTXUI parcial | distinto | CRUD básico, fichas, búsqueda de texto y `campo:valor`, análisis de coautoría, filtros temporales (todos/últimos/rango/Modelo 2024) e importación CSV/URL ya están implementados; faltan experiencia con modales, vistas estadísticas y revisión visual completa |
| Red de coautoría | `ServicioAplicacion.red_coautoria()` | Conteo de productos con coautoría y pares frecuentes en la TUI | distinto | Comparar contrato, nodos, enlaces, filtros y métricas contra la implementación Python |
| Escritura desconectada | Bloqueada en `ServicioAplicacion` | TUI bloquea CRUD sin catálogo remoto; servicios permiten `persistir=false` para demo/pruebas y rechazan persistencia sin cliente | equivalente en la superficie interactiva | Mantener explícita la separación de datos demo y remotos y probar errores de persistencia |
| Revisión remota periódica | Verificación de aplicación Python | Hilo de consulta C++ cada 30 s, evento a TUI y acción manual `r` | equivalente de detección; aún sin prueba diferencial de eventos | Confirmar expiración/renovación de sesión y probar fallo de RPC y meta |

## Brechas confirmadas y evidencia

- La edición de producto añadida en esta iteración cubre metadatos y undo local; aún no permite cambiar su grupo, y no se ha probado contra un repositorio remoto.
- La TUI mantiene brechas de paridad: CRUD básico, fichas, análisis de coautoría, filtros temporales e importación interactiva están implementados; filtros por campos, vistas/gráficos estadísticos avanzados y una experiencia modal completa no están terminados.
- La autoprueba ejecutada renderiza 32 combinaciones de pantalla/tamaño, comprueba búsqueda en los tres directorios, los quince formularios de gestión, formularios CSV/URL y rango, el efecto del filtro Modelo 2024 y una red con coautoría; las capturas no equivalen a snapshots aprobados ni detectan todo truncamiento.
- Un fixture JSON compartido prueba las mismas filas en el serializador C++ y el escritor CSV de Python, cubriendo UTF-8, comas, comillas, saltos de línea y CRLF. Aún falta comparar los exportadores completos, incluidos encabezados, orden y valores de entidades.
- Un fixture de importación compartido verifica que Python y C++ producen los mismos campos de grupo desde un CSV UTF-8 con delimitador punto y coma, comas/comillas escapadas y un valor con salto de línea. La equivalencia de otros tipos y de los informes por filas erróneas sigue pendiente.
- No se ejecutó verificación cruzada CLI contra Python ni conexión autenticada a `pea-prod`; sus conteos reales no se declaran coincidentes.
- Los estados `igual` describen equivalencia de operación visible en los servicios, no una prueba diferencial exhaustiva. Las tareas de validación de cada fila permanecen pendientes mientras no exista esa prueba.
- Toda discrepancia de comportamiento entre las implementaciones debe resolverse contra Python o registrarse explícitamente antes de cambiar la semántica.
