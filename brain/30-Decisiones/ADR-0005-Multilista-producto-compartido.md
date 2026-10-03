---
tipo: adr
estado: aprobado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[_Indice]]"
  - "[[Multilista]]"
  - "[[Estructuras]]"
  - "[[Modelo-de-dominio]]"
origen: "AGENTS.md y AUDITORIA-DISENO-PEAI.md - Fase 12"
---

# ADR-0005 · Multilista con Nodo Único Compartido de Producto

## Contexto
En la actividad científica real, un producto de investigación (artículo, patente, libro) suele ser coautorado por múltiples investigadores pertenecientes a uno o varios grupos de investigación. Si una estructura de datos clona el producto para insertarlo en la lista de cada autor, se produce duplicación de memoria, inconsistencias al editar metadatos y sobreconteo erróneo en las estadísticas globales.

## Opciones consideradas
1. **Duplicación de nodos producto**: Cada investigador o grupo posee una copia independiente del producto. Esto genera redundancia y desincronización si uno de los autores modifica el título o la categoría.
2. **Tablas relacionales planas en memoria (`dict`/`map`)**: Utilizar identificadores UUID en tablas hash nativas. Esto contraviene el requisito pedagógico y normativo del taller sobre estructuras de datos hechas a mano.
3. **Multilista ortogonal con nodo único compartido**: El producto existe como **un único nodo en memoria**. Contiene punteros multidireccionales: pertenece a la lista de productos de su grupo principal y mantiene una lista enlazada interna de referencias a sus investigadores coautores.

## Decisión
Se adopta la **Multilista con nodo único compartido** formalizada en [[Multilista]].
Un producto científico se instancia exactamente una sola vez en el montículo (*heap*). Múltiples investigadores apuntan al mismo nodo mediante enlaces ortogonales. Cualquier mutación (activación, cambio de categoría) se refleja inmediatamente para todos los autores sin duplicar memoria.

## Consecuencias
- **Positivas**: Cero redundancia de datos; coherencia inmediata en el grafo de relaciones; cumplimiento estricto del requisito de estructuras hechas a mano.
- **Riesgos / Mitigaciones**: Complejidad en la gestión de memoria en C++ (requiere punteros inteligentes compartidos `std::shared_ptr` o conteo de referencias) y cuidado al desenlazar durante eliminaciones en cascada.
