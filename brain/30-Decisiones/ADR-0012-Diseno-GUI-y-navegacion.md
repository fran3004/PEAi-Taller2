---
tipo: adr
estado: aprobado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[_Indice]]"
  - "[[GUI-paridad]]"
  - "[[SPEC]]"
origen: "AGENTS.md y AUDITORIA-DISENO-PEAI.md - Fase 12"
---

# ADR-0012 · Diseño Visual Institucional y Navegación Ergonómica en Cuatro Zonas

## Contexto
El usuario del sistema PEA-i requiere analizar grandes volúmenes de datos académicos de forma ágil, comparando métricas agregadas globales con registros individuales detallados. Interfaces sobrecargadas de modales emergentes o ventanas flotantes dispersas aumentan la carga cognitiva y fragmentan la experiencia de usuario.

## Opciones consideradas
1. **Navegación basada en múltiples ventanas modales o páginas inconexas**: Dificulta la correlación entre la visión de conjunto (grupo) y los detalles específicos (productos e investigadores).
2. **Diseño integrado en ventana única con cuatro zonas ergonómicas y divisores ajustables (*QSplitter*)**: Una sola ventana principal estructurada en:
   - Zona 1: Barra superior institucional con identidad UPC.
   - Zona 2: Tarjetas KPI con métricas resumen del [[Hipercubo]].
   - Zona 3: Área central dividida en navegación arbórea, tabla detallada y panel de estadísticas.
   - Zona 4: Barra de estado con revisión y control de sincronización.

## Decisión
Se adopta el **diseño integrado en cuatro zonas con paneles divisibles** formalizado en [[GUI-paridad]].
La interfaz utiliza la paleta de colores institucional de la Universidad Popular del Cesar (`#003366`), el logo oficial y una disposición ergonómica que permite filtrar la información en el panel izquierdo y ver la actualización simultánea en la tabla central y las tarjetas superiores. Toda la terminología se expresa en español correcto sin anglicismos.

## Consecuencias
- **Positivas**: Alta densidad informativa sin saturación; fluidez en la navegación; coherencia visual institucional profesional.
- **Costos**: Exige sincronización cuidadosa de señales y eventos entre vistas desacopladas mediante el patrón observador / modelo-vista de Qt.
