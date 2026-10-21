---
tipo: bitacora
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[ADR-0019-Cpp-terminal-con-ftxui]]"
  - "[[TUI-Diseno-Cpp]]"
  - "[[Paridad-Python-Cpp]]"
  - "[[Matriz-cumplimiento-enunciado]]"
origen: "Continuación de implementación y QA de la aplicación C++ de terminal"
agente: "Copilot"
rama: "feat/python-cierre-francisco"
commit: ""
---

# Bitácora · Implementación C++ de terminal

## Objetivo

Avanzar la conversión C++ a terminal FTXUI, cerrar fallos acoplados en conexión,
persistencia y edición de productos, y dejar documentación/entregables con el
estado verificado en vez de asumir paridad.

## Qué se hizo

- Se integró el estado de conexión y el catálogo remoto en la TUI. Las vistas
  Inicio, Investigadores, Grupos y Productos distinguen el origen y muestran
  datos cargados; el resto conserva mensajes explícitos de funcionalidad
  incompleta.
- Se añadió validación de configuración HTTPS restringida al host oficial
  `pea-prod`, rechazo de claves secret/service-role y autenticación por Auth.
- Se bloquearon escrituras persistentes cuando no hay cliente o token de
  usuario. La CLI cancela importaciones CSV/escrituras de ejemplo sin conexión
  y cancela resumen/exportación si falla la recarga remota.
- Se rechaza persistir entidades sin ID remoto y se exige que Supabase devuelva
  el ID creado antes de confirmar grupos, investigadores o productos.
- Se hizo transaccional en memoria la recarga total: ante error de lectura se
  restauran las estructuras y la revisión previas.
- Se incorporó actualización de metadatos de producto con validación,
  compensación, sincronización del hipercubo y reversión por undo.
- `--autoprueba` guarda capturas de texto sin color para las 32 combinaciones
  de ocho pantallas y cuatro tamaños. La verificación exige pestañas, título
  de vista y etiquetas KPI de Inicio visibles; Inicio usa dos filas compactas
  en anchos menores a 100 columnas y prioriza los KPI en 80×24.
- Se agregó búsqueda textual insensible a mayúsculas en los directorios de
  investigadores, grupos y productos; la autoprueba valida coincidencias de
  los tres con prefijos sintéticos `PRUEBA-`.
- La vista estadística C++ de investigador ahora incluye
  `histograma_productos_por_anio`, con prueba sobre hipercubo que confirma la
  rebanada de investigador.
- Se actualizaron README, SPEC, arquitectura, índices, matriz de paridad y
  cumplimiento; se añadieron el diseño TUI, el fuente C++ de entrega y la
  sección C++ del DOCX.

## Comandos y resultados

- `cmake --build cpp\build --config Release`: correcto con
  `-Wall -Wextra -Wpedantic -Werror`.
- `ctest --test-dir cpp\build --output-on-failure`: correcto.
- `cpp\build\pruebas_cpp.exe --no-version`: 35 casos y 356 aserciones
  aprobados.
- `cpp\build\pea-cpp.exe --autoprueba`: 32 pantallas/tamaños, cero hallazgos;
  32 capturas generadas bajo `datos/capturas/terminal/`.
- `pea-cpp info`: correcto; identificó Qt Core/Network, TUI y estructuras
  manuales.
- `pea-cpp cargar-ejemplo` con variables de conexión vacías: rechazó la
  operación, código de salida 1, sin contactar un proyecto remoto.
- `g++ -std=c++17 -fsyntax-only -I cpp\include entrega\Taller2_FF_SM.cpp`:
  correcto.
- `git diff --check`: correcto; Git informó únicamente conversiones de fin de
  línea preexistentes/configuradas.
- `scripts/verificar.ps1`: correcto; 285 pruebas Python aprobadas, 3
  deseleccionadas, compilación y pruebas C++ aprobadas, bóveda con cero
  errores y autoprueba TUI con 32/32 pantallas sin hallazgos. Persiste una
  advertencia preexistente por una referencia a ADR-0016 no resuelta en una
  nota de Antigravity.
- `cpp\build\pea-cpp.exe --autoprueba`: además de las 32 combinaciones, pasó
  las búsquedas de investigadores, grupos y productos con código cero.

## Decisiones

- La TUI C++ se registra como parcial; la selección de FTXUI y la autoprueba de
  tamaño no se tratan como evidencia de paridad funcional.
- No se consultó ni modificó Supabase. Los conteos reales y la verificación
  cruzada con Python quedan sin confirmar.
- La configuración C++ usa variables del proceso y no carga `.env`; no se leen
  archivos de secretos durante esta tarea.

## Pendientes y siguiente paso

- Completar formularios CRUD y fichas; orden y filtros por campos; gráficos y
  análisis de coautoría; estados, modales y revisión remota periódica.
- Implementar exportación CSV/Markdown/JSON con contrato idéntico al de Python,
  y demostrar igualdad byte a byte de CLI/resumen.
- Cubrir en C++ importación responsable/reintentos, revisión remota y pruebas
  de fixtures compartidos; verificar conteos remotos solo con sesión normal.
- Completar modo ASCII `+ - |`, snapshots revisados y detección exhaustiva de
  truncamientos para todas las filas, y validar visualmente las demás vistas
  en tamaños estrechos.
