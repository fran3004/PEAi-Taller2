---
tipo: adr
estado: aprobado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[_Indice]]"
  - "[[Hipercubo]]"
  - "[[Estructuras]]"
origen: "AGENTS.md y AUDITORIA-DISENO-PEAI.md - Fase 12"
---

# ADR-0006 · Cálculo Estadístico Exclusivo en Hipercubo 5D en Memoria

## Contexto
El taller exige implementar un Hipercubo como estructura de datos propia para calcular estadísticas agregadas y responder consultas analíticas multidimensionales. Existe la tentación común de delegar estas operaciones a consultas SQL con `GROUP BY`, `SUM`, `COUNT` o vistas materializadas en la base de datos remota de Supabase, lo cual elude el propósito formativo del proyecto y satura las llamadas de red.

## Opciones consideradas
1. **Consultas de agregación SQL directas a PostgreSQL**: Facilita la implementación pero viola el contrato de AGENTS.md ("las estadísticas se calculan desde el hipercubo, no con consultas SQL").
2. **Cálculo en Hipercubo 5D en memoria local**: Toda la agregación se ejecuta dentro de un tensor de 5 dimensiones (*Grupo $\times$ Investigador $\times$ Categoría $\times$ Año $\times$ Validación*) implementado a mano en el cliente. La base de datos solo almacena las entidades atómicas y las envía paginadas.

## Decisión
Se adopta el **cálculo estadístico exclusivo en el Hipercubo 5D en memoria**.
La capa de persistencia (Supabase) únicamente entrega registros atómicos mediante llamadas REST paginadas. Al recibirlos, el cliente puebla el Hipercubo y ejecuta todas las operaciones OLAP (*Slice*, *Dice*, *Roll-up*, *Drill-down*, *Pivot*) directamente en RAM. SQL solo se utiliza en pruebas de verificación automatizadas para corroborar la exactitud matemática del hipercubo.

## Consecuencias
- **Positivas**: Tiempos de respuesta de sub-milisegundo en la GUI para filtros interactivos; operatividad de análisis incluso ante pérdida transitoria de conexión; cumplimiento pleno del contrato del taller.
- **Costos**: Mayor consumo de memoria RAM local en el cliente y necesidad de algoritmos de actualización incremental al mutar entidades.
