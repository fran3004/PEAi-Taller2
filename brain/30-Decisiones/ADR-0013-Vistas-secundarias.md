---
tipo: adr
estado: revisado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[_Indice]]"
  - "[[GUI-Diseno-Python]]"
  - "[[GUI-paridad]]"
  - "[[Pila-deshacer]]"
  - "[[Cola-importacion]]"
origen: "Rediseño de la interfaz de Python, 2026-10-03"
---

# ADR-0013 · Vistas secundarias: historial, cola, formularios y verificación cruzada

## Contexto
Además de consultar datos, la persona necesita ver qué puede deshacer, cómo avanza la importación, crear o corregir registros y, para el taller, comprobar que Python y C++ dan el mismo resultado. Dejar estas tareas ocultas genera incertidumbre; ponerlas todas en la navegación principal la satura.

## Opciones consideradas
1. **Paneles acoplables (`QDockWidget`) y una pantalla por tarea**: flexible, pero fragmenta la ventana y no encaja con el diseño de barra superior.
2. **Cada vista secundaria donde se usa**: el historial junto al botón Deshacer, la cola dentro de Importar, los formularios como diálogos y la verificación cruzada dentro de Configuración. **Elegida.**

## Decisión
| Vista | Dónde vive |
|---|---|
| Historial de operaciones ([[Pila-deshacer]]) | Popover del botón Deshacer en la barra superior |
| Monitor de la [[Cola-importacion]] | Pantalla **Importar**, tarjeta «Cola de importación» (con estados y progreso) |
| Altas y ediciones de grupos, investigadores y productos | Diálogos modales con el estilo del sistema, abiertos desde cada directorio |
| Activar/desactivar y eliminar con cascada | Botones de la ficha lateral de cada directorio |
| Verificación cruzada Python / C++ | **Configuración › Verificación cruzada** |
| Conexión con Supabase | **Configuración › Conexión** |

## Consecuencias
- **Positivas**: la navegación principal queda limpia; cada herramienta está junto a lo que afecta.
- **Costos**: la antigua pantalla «Gestión de datos» desaparece y sus diálogos se reubican en `src/pea/gui/dialogos.py`.
