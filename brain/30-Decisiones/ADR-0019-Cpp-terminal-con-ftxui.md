---
tipo: adr
estado: aprobado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[Arquitectura]]"
  - "[[GUI-paridad]]"
  - "[[ADR-0017-Tecnologia-de-interfaz-Qt-Widgets]]"
origen: "Cambio de rumbo del proyecto: C++ ya no será una gui de escritorio Qt, sino una terminal moderna con FTXUI"
numero: ADR-0019
decision: "C++ pasa a ser una aplicación de terminal; se retira Qt Widgets/Gui y se conserva Qt Core + Network para HTTPS y JSON"
---

# ADR-0019 · C++ pasa a ser una aplicación de terminal

## Contexto

El proyecto original fijaba una estrategia de paridad basada en una interfaz gráfica Qt para C++; sin embargo, el alcance del taller exige una solución terminal moderna, con pantallas, tablas, tarjetas, atajos y capacidad interactiva, sin abrir una ventana gráfica. Esto obliga a replantear la capa de presentación de C++ sin tocar la lógica funcional compartida con Python.

## Opciones consideradas
1. **Mantener Qt Widgets para C++**: conserva una interfaz visual conocida, pero contradice el nuevo alcance del taller y deja obsoleta la estrategia de terminal.
2. **Usar una librería de consola moderna**: ofrece renderizado más completo, acceso a teclado/mouse y mejor ajuste al requisito de terminal versátil. **Elegida.**
3. **Implementar una consola básica sin dependencias**: reduce complejidad, pero no cumple la exigencia de una aplicación completa, moderna y vistosa.

## Decisión

C++ se reorienta a una aplicación de terminal interactiva. La capa de interfaz se implementa con **FTXUI `v5.0.0`**, con renderizado Unicode, colores, componentes y soporte de teclado/mouse. Cuando la dependencia no está instalada, se integra con `FetchContent` usando esa etiqueta exacta, nunca `latest` ni una rama dinámica.

La dependencia del entorno no estaba disponible en MSYS2 UCRT64, así que CMake obtiene **FTXUI `v5.0.0`** mediante `FetchContent`, con etiqueta exacta y clon superficial. La parte de red y JSON se conserva en **Qt6::Core + Qt6::Network** porque ya está validada para HTTPS, TLS y comunicación con Supabase. Esto no implica una interfaz gráfica; solo mantiene la infraestructura de transporte y serialización necesaria para la capa de servicios.

La primera entrega de la TUI no equivale todavía a una paridad visual completa: incluye navegación por ocho secciones, resumen y directorios de lectura; las pantallas de redes, importación y algunas acciones siguen pendientes. La matriz de paridad registra esas brechas y no se debe interpretar la selección de FTXUI como prueba de aceptación de la interfaz.

## Consecuencias
- La base funcional de C++ conserva las estructuras hechas a mano y la arquitectura por capas; la equivalencia concreta con Python se mantiene como trabajo verificable en `Paridad-Python-Cpp.md`.
- El código de la vieja GUI en `cpp/src/gui/` y `cpp/include/pea/gui/` queda descartado y se reemplaza por una entrada `pea::ejecutar_aplicacion` orientada a terminal.
- El proyecto gana una línea de ejecución compatible con CLI no interactiva y TUI interactiva, sin introducir dependencias de `Qt Widgets` o `QApplication` para la pantalla.
- Si en una iteración posterior FTXUI no cubre un caso concreto, se registra una alternativa explícita antes de sustituir la decisión.
- La importación PDF continúa delegada a Python; C++ debe comunicarlo explícitamente en su flujo de importación.
