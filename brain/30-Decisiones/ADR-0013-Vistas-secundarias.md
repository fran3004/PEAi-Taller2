---
tipo: adr
estado: aprobado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[_Indice]]"
  - "[[GUI-paridad]]"
  - "[[Pila-deshacer]]"
  - "[[Cola-importacion]]"
origen: "AGENTS.md y AUDITORIA-DISENO-PEAI.md - Fase 12"
---

# ADR-0013 · Integración de Vistas Secundarias: Historial, Cola y Gestión

## Contexto
Además de la consulta analítica y visualización de productos, el sistema PEA-i debe proveer visibilidad sobre las operaciones en curso: tareas asíncronas de importación web, historial de mutaciones para deshacer/rehacer y formularios de gestión de entidades. Esconder estas operaciones o dejarlas sin interfaz visual genera incertidumbre en el usuario sobre el estado de sus datos.

## Opciones consideradas
1. **Ocultar el estado en segundo plano y limitar la interacción a atajos ciegos (Ctrl+Z)**: El usuario desconoce cuántos cambios puede deshacer o si una descarga web de CvLAC continúa ejecutándose.
2. **Diálogos modales y paneles secundarios acoplables (*QDockWidget* o pestañas de vista)**: Integrar vistas secundarias dedicadas para:
   - Panel de Historial de Operaciones: Visualiza el contenido de la [[Pila-deshacer]].
   - Monitor de la Cola de Importación: Muestra el progreso de la [[Cola-importacion]] con estado de reintentos y tiempo transcurrido.
   - Vistas de Formulario: Creación y edición validada de grupos, investigadores y productos.

## Decisión
Se adopta la **integración de vistas secundarias acoplables y paneles de monitoreo** formalizada en [[GUI-paridad]].
El usuario puede inspeccionar en cualquier momento el historial de deshacer y el avance de las colas de importación asíncronas, garantizando transparencia operativa total sin bloquear el uso regular del panel principal.

## Consecuencias
- **Positivas**: Control absoluto del usuario sobre los procesos en segundo plano y el historial de cambios reversibles.
- **Costos**: Requiere la implementación de modelos de tabla adicionales para alimentar las vistas secundarias a partir de la pila y la cola.
