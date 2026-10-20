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

Esta matriz documenta la equivalencia funcional entre la implementación de Python y la base C++ actual. Se sigue la convención del enunciado: una fila por operación pública relevante y columnas para `Python`, `C++ existente`, `Estado` (`igual` / `falta` / `distinto`) y la `Tarea` pendiente o ya resuelta.

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
| Actualizar producto | `ServicioDominio.actualizar_producto()` | `CatalogoInvestigacion::actualizar_producto()` | igual | Requiere pruebas de edición y deshacer |
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
| Hipercubo rebanada | `Hipercubo.rebanada()` | `Hipercubo5D` / subcubo | igual | Probar ventana temporal y dimensiones |
| Enrollar / enrollamiento | `Hipercubo.enrollar()` | `Hipercubo5D` | igual | Comprobar densidad y reagrupación |
| Filtro de años TODOS | `FiltroAnios.TODOS` | equivalente de servicio | igual | Confirmar salida global |
| Filtro de años ULTIMOS N | `FiltroAnios.ULTIMOS` | funcional equivalente | igual | Validar `N` y texto descriptivo |
| Filtro de años RANGO | `FiltroAnios.RANGO` | equivalente | igual | Ordenar desde/hasta y revertir si aplica |
| Filtro de años MODELO_2024 | `FiltroAnios.MODELO_2024` | equivalente | igual | Validar ventanas según tipología |
| Descripción textual del filtro | `descripcion()` | `FiltroAnios` / `ServicioEstadisticas` | igual | Mantener textos de pantalla |
| Importación CSV | lector en Python | `ServicioIngesta` / `lector_csv` | igual | Probar filas omitidas y errores |
| Importación URL | extractor URL / parseador | `ServicioIngesta` + `extractor_url` | igual | Validar política de scraping y límites |
| Exportación CSV | exportador de catálogo | parte del CLI | distinto | C++ necesita completar por completo la salida de CSV |
| Modo no interactivo / CLI | `pea.cli` | `pea-cpp` + `pea::cli::ejecutar` | igual | Validar en flujos reales y argumentos |
| Modo TUI interactivo | no existe en Python | planeado para C++ | falta | Implementar terminal moderna con FTXUI |

## Observaciones finales

- La paridad funcional del núcleo está consolidada en la mayoría de las operaciones del dominio, estadísticas y estructuras.
- La diferencia más importante que queda abierta es la etapa de interfaz y la exportación CSV de C++.
- El cambio de C++ a terminal no elimina la necesidad de mantener la lógica de negocio alineada con Python; la regla de Python como fuente de verdad sigue vigente.
- La matriz debe actualizarse cada vez que se complete una operación o una diferencia funcional se resuelva.
