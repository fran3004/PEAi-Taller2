---
tipo: adr
estado: aprobado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[_Indice]]"
  - "[[Contrato-de-datos]]"
  - "[[Arquitectura]]"
origen: "AGENTS.md y AUDITORIA-DISENO-PEAI.md - Fase 12"
---

# ADR-0009 · Procedimientos Almacenados (RPC) y Bloqueo Optimista por Revisión

## Contexto
En un entorno multi-usuario con aplicaciones de escritorio concurrentes escritas en Python y C++, dos usuarios pueden intentar modificar la misma entidad o relaciones simultáneamente. Asimismo, la creación o eliminación de productos y sus enlaces de coautoría requiere modificar múltiples tablas (`productos`, `autores_producto`, `meta`). Ejecutar esto con múltiples llamadas REST atómicas individuales desde el cliente arriesga estados intermedios inconsistentes si falla la red entre llamadas.

## Opciones consideradas
1. **Llamadas REST encadenadas desde el cliente**: El cliente envía primero el producto y luego cada relación de autoría. Si la segunda petición falla, la base de datos queda corrupta con un producto huérfano sin autores.
2. **Procedimientos RPC atómicos en PostgreSQL con control de concurrencia optimista (`meta.revision`)**: Las operaciones complejas se encapsulan en funciones PL/pgSQL ejecutadas en una sola transacción en el servidor. La tabla `meta.revision` incrementa monotónicamente con triggers; cada RPC exige la `revision_esperada`.

## Decisión
Se adoptan **funciones almacenadas RPC y control de concurrencia optimista** formalizados en [[Contrato-de-datos]].
Cualquier mutación estructural (crear producto con autores, eliminar cascada, desactivar) se implementa como función RPC con transacción atómica garantizada por PostgreSQL. Si `meta.revision` remota no coincide con la esperada por el cliente, la RPC aborta de inmediato con código de conflicto de revisión (`409`), previniendo sobreescrituras ciegas.

## Consecuencias
- **Positivas**: Integridad referencial atómica absoluta; protección contra condiciones de carrera entre clientes; disminución sustancial del número de peticiones de red por operación.
- **Costos**: Requiere escribir y versionar funciones PL/pgSQL en las migraciones de Supabase.
