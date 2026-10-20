---
tipo: bitacora
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[00-Inicio]]"
  - "[[GUI-paridad]]"
  - "[[ADR-0019-Cpp-terminal-con-ftxui]]"
origen: "Cambio de rumbo del proyecto: C++ deja Qt Widgets y se convierte en terminal moderna"
agente: "copilot"
rama: "feat/python-cierre-francisco"
commit: "pendiente"
---

# Bitácora · Rediseño de C++ a terminal

## Objetivo
Actualizar la dirección del proyecto para que C++ sea una aplicación de terminal moderna sin GUI, dejando claro que la lógica funcional de Python sigue siendo la referencia y preservando la arquitectura de red y servicios.

## Qué se hizo
- Ajusté la documentación del contrato del proyecto y el registro de decisiones para reflejar el nuevo rumbo terminal de C++.
- Reescribí la nota de paridad de interfaz en [[GUI-paridad]] para reflejar la terminal TUI de C++.
- Añadí el ADR-0019 en [[ADR-0019-Cpp-terminal-con-ftxui]] documentando la decisión de retirar Qt Widgets/Gui.
- Modifiqué la configuración de CMake para eliminar dependencias gráficas Qt y dejar la capa de red con Qt Core + Qt Network.
- Reemplacé el punto de entrada de C++ por una aplicación que ejecuta la CLI sin depender de `QApplication` o `QMainWindow`.

## Comandos y resultados
- `git --no-pager status --short --branch` → comprobación inicial del estado del repositorio.
- `py -m pip install pytest ruff ...` → se instalaron dependencias de Python necesarias para validación local.
- `py -m pytest -q` → se ejecutó la suite de Python para verificar el estado del proyecto.
- `py -m ruff check src tests tools scripts` → pendiente de resolución si se requiere una validación más estricta del código Python del proyecto.
- `cmake -S cpp -B cpp/build -G Ninja -DCMAKE_BUILD_TYPE=Debug` → preparación de la compilación del módulo C++.
- `cmake --build cpp/build` → pendiente de confirmación final tras ajustar los artefactos del ejemplo.

## Decisiones
- Se conserva Qt Core + Qt Network porque la capa de transporte HTTPS, TLS y JSON sigue siendo necesaria.
- Se elimina la referencia a Qt Widgets/Gui para no seguir construyendo una interfaz de escritorio obsoleta.
- La capa funcional de C++ se intenta mantener paralela a Python sin cambiar la lógica del dominio ni la persistencia en Supabase.

## Pendientes y siguiente paso
- Validar la compilación completa de C++ con la nueva estructura terminal y revisar si hay más referencias a `QApplication` o `Qt Widgets` en el proyecto.
- Realizar la validación de Python completa y ajustar cualquier fallo que impida la ejecución de la suite del proyecto.
