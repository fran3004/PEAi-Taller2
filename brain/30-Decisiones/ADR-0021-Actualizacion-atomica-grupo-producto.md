---
tipo: adr
estado: aprobado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[GUI-paridad]]"
  - "[[TUI-Diseno-Cpp]]"
  - "[[Paridad-Python-Cpp]]"
  - "[[ADR-0009-RPC-y-control-de-revision-optimista]]"
origen: "Cierre de la diferencia de actualización de producto entre Python y C++"
numero: ADR-0021
decision: "Cambiar el grupo relacionado con el producto en C++ a través de una RPC atómica con revisión esperada y RLS de invocador"
---

# ADR-0021 · Actualización atómica del grupo de un producto

## Contexto

Python permite actualizar los metadatos de un producto y reasignar o quitar su
grupo en la multilista. C++ solo actualizaba metadatos. En Supabase, cambiar el
grupo modifica `producto_grupos` y puede combinarse con cambios en `productos`;
varias peticiones REST podrían dejar una relación parcial si alguna falla.

## Opciones consideradas

1. Encadenar PATCH/DELETE/POST REST desde C++: mantiene operaciones simples,
   pero no garantiza atomicidad ni evita estados intermedios.
2. Mantener la diferencia funcional: evita cambios de persistencia, pero deja
   incompleta la edición del producto frente a Python.
3. Crear una RPC con revisión esperada que actualice producto y relación en una
   transacción PostgreSQL, bajo RLS del usuario autenticado: añade una migración
   y un contrato de respuesta, pero resuelve la brecha sin privilegios
   adicionales. **Elegida.**

## Decisión

La multilista C++ debe reasignar o quitar el grupo y reparar sus enlaces
intragrupo. El servicio aplica el cambio local primero, persiste el producto y
su relación mediante `transaccion_actualizar_producto_grupo`, pasa la revisión
esperada y restaura la estructura si la RPC falla. La función usa
`SECURITY INVOKER`; las políticas RLS vigentes siguen decidiendo qué filas puede
modificar la sesión. La migración crea solo la función y no se aplica
automáticamente al proyecto remoto.

## Consecuencias

- Crear, cambiar y quitar el vínculo del producto queda disponible en la
  edición TUI; deshacer restaura el grupo anterior.
- La respuesta de la RPC devuelve la revisión final tras los triggers de las
  tablas afectadas.
- La migración debe aplicarse a `pea-prod` antes de usar la edición con datos
  remotos; no se desplegó ni se ejecutó una prueba autenticada en esta tarea.
- La atomicidad de esta ruta queda en PostgreSQL; no se reemplaza por
  escrituras REST encadenadas.
