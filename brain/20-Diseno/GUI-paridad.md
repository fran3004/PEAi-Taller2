---
tipo: nota-de-diseno
estado: revisado
creado: 2026-10-03
actualizado: 2026-10-20
relacionado:
  - "[[_Indice]]"
  - "[[GUI-Diseno-Python]]"
  - "[[TUI-Diseno-Cpp]]"
  - "[[Arquitectura]]"
  - "[[Interoperabilidad]]"
  - "[[ADR-0011-Paridad-arquitectural-Python-Cpp]]"
  - "[[ADR-0019-Cpp-terminal-con-ftxui]]"
  - "[[SPEC]]"
origen: "Cambio de rumbo de C++: dejar la GUI Qt y volver a una terminal moderna (2026-10-20)"
---

# Diseño · Contrato de paridad entre Python y C++ terminal

## Propósito

Esta nota redefine la relación entre la versión Python y la versión C++ tras el cambio de rumbo del proyecto.

- La **fuente de verdad funcional** sigue siendo la lógica de Python y sus servicios, no la primera versión de la GUI de C++.
- La interfaz de C++ ya no intenta emular una ventana gráfica con Qt Widgets; ahora es una **aplicación de terminal** moderna con pestañas, paneles, tablas, avisos y teclado/mouse.
- La paridad arquitectónica y funcional persiste: mismas capas, mismas estructuras, mismos resultados y la misma base de datos de Supabase.

## Estado

| Elemento | Python | C++ |
|---|---|---|
| Interfaz principal | PySide6 / GUI | Terminal TUI con FTXUI 5.0.0 |
| Red de datos | HTTPS + cliente Supabase | HTTPS + cliente Supabase |
| Estructuras | Lista doble, multilista, pila, cola, hipercubo | Mismas estructuras escritas a mano |
| Pruebas funcionales | Python | C++ CLI y pruebas unitarias |
| Referencia visual | [[GUI-Diseno-Python]] | Reubicada en las pantallas TUI, no en `Qt Widgets` |

La TUI C++ disponible es una implementación parcial: navegación, resumen,
directorios de lectura y autoprueba de tamaños. No se considera paridad visual
ni funcional completa. Las vistas pendientes se enumeran en [[TUI-Diseno-Cpp]]
y las diferencias funcionales en [[Paridad-Python-Cpp]].

## Lo que C++ debe igualar

1. **Lógica funcional**: CRUD completo, estadísticas, filtros, persistencia, deshacer y validaciones del dominio.
2. **Misma fuente de datos**: Supabase mediante HTTPS, REST/RPC y control de revisión.
3. **Mismas reglas de negocio**: cascadas, desactivación reversible, eliminación de estructuras y respaldo en memoria al error de persistencia.
4. **Estadísticas desde el hipercubo**: la agregación vuelve a derivarse del `Hipercubo5D`, no desde consultas SQL.
5. **Salida y navegación terminal**: pantallas, tablas, menús, visibilidad de estado y atajos de teclado equivalentes a los de la GUI de Python, aunque la implementación se haga en consola.

## Lo que C++ no debe intentar

- Reusar la vieja GUI de Qt Widgets como referencia.
- Duplicar la lógica de pantallas en la capa de renderizado.
- Mezclar SQL directo, estructuras nativas de contenedor como almacenamiento principal de entidades y datos inventados.

## Decisiones relacionadas
- [[ADR-0011-Paridad-arquitectural-Python-Cpp]]
- [[ADR-0019-Cpp-terminal-con-ftxui]]
- [[ADR-0017-Tecnologia-de-interfaz-Qt-Widgets]] (quedó reemplazada por la terminal)

## Riesgos y casos borde
- Si se mantiene la referencia a Qt Widgets, se reintroduce una dependencia visual que ya no corresponde al proyecto.
- La terminal debe conservar la misma información que la GUI de Python sin perder consistencia en textos o columnas.
- Cualquier diferencia funcional entre Python y C++ debe registrarse y no corregirse en silencio.
