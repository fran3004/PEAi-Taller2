---
tipo: bitacora
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[TUI-Diseno-Cpp]]"
  - "[[Paridad-Python-Cpp]]"
  - "[[ADR-0019-Cpp-terminal-con-ftxui]]"
origen: "Cierre de funcionalidades de gestión C++, exportación CSV y manejo de exportación desconectada en Python"
agente: "Copilot"
rama: "feat/python-cierre-francisco"
commit: ""
---

# Bitácora · CRUD y exportación CSV

## Objetivo

Completar y describir las funciones de gestión C++ implementadas en esta
continuación, alinear la exportación CSV y evitar exportaciones Python con
catálogo desconectado o incompleto.

## Qué se hizo

- Se añadieron a la TUI formularios por teclado para crear, editar metadatos,
  activar/desactivar y eliminar grupos, investigadores y productos; fichas JSON
  y confirmación textual para eliminación física.
- Se añadieron análisis institucional anual y pares de coautoría calculados
  desde el catálogo y la multilista cargados.
- Se completó el modo de marcos ASCII y la autoprueba de renderizado para los
  15 formularios, tres búsquedas y un caso de coautoría además de las 32
  combinaciones de pantalla/tamaño.
- Se creó un serializador CSV C++ compartido con escape de campos, UTF-8,
  terminadores CRLF y escritura atómica por archivo. Los encabezados y el orden
  corresponden a la exportación Python.
- La CLI C++ crea el directorio de exportación solo después de conectar y
  recargar correctamente el catálogo.
- La exportación Python ahora cancela si falta conexión o falla la recarga
  remota; se añadieron pruebas para desconexión, error de recarga y esquema/
  escape con datos sintéticos PRUEBA-.
- Se detiene el temporizador de revisión remota al cerrar la ventana y se
  descartan sus callbacks en vuelo para evitar que actualicen widgets ya
  destruidos.
- Se actualizaron README, diseño TUI y matriz de paridad sin declarar
  equivalencia funcional completa.

## Comandos y resultados

- `.venv\Scripts\python.exe -m pytest tests\unit\test_cli_exportacion.py -q`:
  3 pruebas aprobadas.
- La prueba de diálogo de cierre junto con las tres pruebas de exportación:
  4 aprobadas. La prueba de cierre detectó una actualización asíncrona de la
  franja de revisión después de destruir la ventana; el cierre ahora detiene
  el temporizador y los callbacks verifican el ciclo de vida.
- `cmake --build cpp\build --config Release`: compilación correcta; no había
  trabajo pendiente al ejecutar.
- `cpp\build\pruebas_cpp.exe --no-version`: 36 casos y 361 aserciones
  aprobados.
- Exportación C++ con las variables de conexión vacías: código 1, mensaje
  explícito de conexión requerida y destino de salida inexistente.
- `scripts\verificar.ps1`: OK; 288 pruebas Python aprobadas y 3 de red
  deseleccionadas, compilación y pruebas C++ aprobadas, bóveda con cero errores
  y autoprueba TUI aprobada. Una primera pasada expuso un callback de revisión
  tras el cierre; se corrigió y la repetición integral quedó en verde.
- `.venv\Scripts\ruff.exe check src\pea\cli.py src\pea\gui\ventana_principal.py
  tests\unit\test_cli_exportacion.py`: todos los chequeos aprobados.
- `git diff --check`: correcto; Git reporta una conversión de fin de línea
  configurada en el archivo TUI.

## Decisiones

- La exportación se cancela ante fallo remoto en lugar de producir archivos
  vacíos o parcialmente basados en datos obsoletos.
- La escritura CSV es atómica por archivo; no se afirma que los tres archivos
  formen una única transacción.
- No se consultó ni modificó Supabase y no se leyeron secretos.

## Pendientes y siguiente paso

- Agregar prueba diferencial real de CSV Python/C++ y pruebas de eventos/
  persistencia CRUD; la autoprueba actual comprueba renderizado de formularios,
  no la interacción completa ni la persistencia remota.
- Completar filtros avanzados, importación interactiva, vistas JSON/Markdown y
  revisión remota periódica antes de afirmar paridad total.
