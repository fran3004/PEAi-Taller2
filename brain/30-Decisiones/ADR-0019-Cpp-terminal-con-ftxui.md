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

C++ se reorienta a una aplicación de terminal interactiva. La capa de interfaz se implementa con **FTXUI** (versión exacta fijada en la integración, por ejemplo `5.0.0` o la del paquete MSYS2 equivalente si está disponible), con renderizado compatible con Unicode, colores de 24 bits, tablas, widgets de estado y soporte de teclado/mouse. Cuando la dependencia no está instalada, se integra con `FetchContent` usando una versión exacta y estable, nunca `latest` ni una rama dinámica.

La parte de red y JSON se conserva en **Qt6::Core + Qt6::Network** porque ya está validada para HTTPS, TLS y comunicación con Supabase. Esto no implica una interfaz gráfica; solo mantiene la infraestructura de transporte y serialización necesaria para la capa de servicios.

## Consecuencias
- La base funcional de C++ sigue siendo comparable con Python y sigue usando las mismas estructuras hechas a mano y la misma arquitectura por capas.
- El código de la vieja GUI en `cpp/src/gui/` y `cpp/include/pea/gui/` queda descartado y se reemplaza por una entrada `pea::ejecutar_aplicacion` orientada a terminal.
- El proyecto gana una línea de ejecución compatible con CLI no interactiva y TUI interactiva, sin introducir dependencias de `Qt Widgets` o `QApplication` para la pantalla.
- Si en una iteración posterior FTXUI no cubre un caso concreto, se registra una alternativa explícita antes de sustituir la decisión.
