---
tipo: bitacora
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[TUI-Diseno-Cpp]]"
  - "[[Paridad-Python-Cpp]]"
  - "[[ADR-0019-Cpp-terminal-con-ftxui]]"
  - "[[ADR-0020-Revision-remota-periodica-cpp]]"
origen: "Continuación del cierre funcional de la aplicación C++ PEA-i"
agente: "Copilot"
rama: "feat/python-cierre-francisco"
commit: ""
---

# Bitácora · Importación y filtros temporales C++

## Objetivo

Habilitar flujos de importación en la TUI y hacer utilizables los filtros
temporales ya disponibles en el servicio estadístico C++.

## Qué se hizo

- Se incorporó en la pestaña Importar un formulario de CSV con detección
  automática opcional o selección explícita de grupos, investigadores,
  productos o autores. Se requiere una conexión remota autenticada.
- Se incorporó importación de URL SCIENTI con opción obligatoria de anonimizar
  los datos personales; la validación del host y HTTPS permanece a cargo del
  extractor existente.
- El formulario informa registros procesados, filas erróneas y advertencias.
  Los tipos CSV no reconocidos ahora se rechazan explícitamente, evitando una
  tarea que pareciera exitosa sin procesar datos.
- Se añadieron controles `f` para alternar Todos/Últimos 5/Modelo 2024 y `g`
  para configurar rango personalizado. El rango filtra las series anuales y
  los productos considerados en coautoría.
- Se extendió la autoprueba para verificar renderizado de formularios CSV,
  URL, rango personalizado y el efecto de exclusión del filtro Modelo 2024.
- Se actualizaron README, diseño TUI y matriz de paridad, manteniendo
  explícitas las brechas que siguen pendientes.
- Se creó un fixture JSON común para contrastar el escape de filas entre C++ y
  Python, incluyendo UTF-8, comas, comillas, CR/LF y CRLF; las pruebas cubren el
  serializador/escritor, no todavía los exportadores completos.
- Se corrigió el lector CSV C++ para conservar saltos de línea dentro de campos
  entrecomillados y se agregó un fixture de importación de grupos compartido
  con Python para verificar valores UTF-8, delimitador, comillas y salto
  interno.
- Se completaron fixtures de importación CSV compartidos para investigadores,
  productos y autores. Se ampliaron los campos C++ importados y se alinearon
  requisitos de nombre, año, estado de validación y valores booleanos con los
  modelos Pydantic.
- Se agregó también un fixture con una fila inválida intercalada. Python y C++
  conservan los mismos dos productos válidos y apuntan el error a la fila 3.
- Se amplió la búsqueda de los directorios para cubrir todos los atributos
  cargados y admitir filtros canónicos `campo:valor`; la autoprueba comprueba
  búsquedas sobre campos no visibles en las filas.
- La revisión normativa confirmó que las tablas se exportan a CSV y los
  gráficos a PNG; no se encontró requisito de exportación Markdown/JSON de
  vistas estadísticas, así que no se añadió esa función.
- Se extrajo el serializador del catálogo C++ para que lo use el CLI y se
  añadieron fixtures compartidos de exportación completa para grupos,
  investigadores y productos. Python ejecuta el comando real de exportación;
  C++ compara los bytes producidos por el serializador común.

## Comandos y resultados

- `cmake --build cpp\build --config Release`: correcto, con advertencias
  tratadas como errores.
- `cpp\build\pruebas_cpp.exe --no-version`: 37 casos y 363 aserciones
  aprobados, incluyendo tipo CSV desconocido.
- `cpp\build\pea-cpp.exe --autoprueba`: 32 combinaciones de pantalla/tamaño,
  búsquedas y formularios de CRUD/importación/rango sin hallazgos; filtro
  Modelo 2024 validado con el fixture PRUEBA-.
- `ruff check` global: falla por un diagnóstico I001 en
  `entrega/Taller2_FF_SM.py`, archivo ajeno y no modificado en esta tarea; el
  lint de los archivos Python tocados en la tarea anterior había pasado.
- `git diff --check`: correcto salvo aviso de normalización de CRLF de Git en
  el fuente TUI.
- Suite C++: 40 casos/432 aserciones aprobados, incluyendo fixtures compartidos
  de importación de las cuatro entidades y omisión de filas inválidas.
- Pruebas de paridad Python CSV: 3 aprobadas; Ruff pasó para el archivo nuevo.
- Pruebas Python de exportación: 4 aprobadas; Ruff pasó para el test actualizado.
- Pruebas C++: 41 casos/439 aserciones aprobados, incluidos los tres CSV
  completos y sus encabezados/filas/escapes.
- El build integral de `pea-cpp.exe` no pudo relinkearse porque un proceso
  previo de ese ejecutable (PID 12324) mantiene el archivo bloqueado; no se
  terminó ese proceso. `pea_core` y `pruebas_cpp.exe` compilaron correctamente.
- `scripts\verificar.ps1`: 291 pruebas Python aprobadas y 3 pruebas de red
  omitidas; compilación C++ con `-Werror`, CTest, autoprueba TUI y bóveda
  correctos. La bóveda conserva una advertencia previa por el enlace
  `ADR-0016` de otra bitácora.
- `git diff --check`: correcto.
- `git diff --check`: correcto. `ruff check` global mantiene el fallo I001
  preexistente de `entrega/Taller2_FF_SM.py`, no modificado aquí.
- Build independiente en `%TEMP%\pea-taller2-export-qa`: compilación de
  `pea-cpp.exe` y `pruebas_cpp.exe` aprobada; CTest aprobó 1/1 suite y doctest
  reportó 41 casos/439 aserciones aprobados. La ruta fija de los fixtures
  SCIENTI evita depender del directorio de trabajo.
- `pea-cpp.exe --autoprueba` desde el build independiente: 32 combinaciones de
  pantalla/tamaño y formularios sin hallazgos.
- `.venv\Scripts\python.exe -m pytest tests\unit\test_cli_exportacion.py -q`:
  4 pruebas aprobadas; `.venv\Scripts\python.exe -m ruff check
  tests\unit\test_cli_exportacion.py`: correcto. El Python global no tiene
  pytest instalado; se usó el entorno virtual del proyecto.
- `python tools\brain\verificar_brain.py`: 158 notas, 0 errores y 1 aviso
  preexistente por `ADR-0016` en otra bitácora.

## Decisiones

- No se permite importación desde modo demo ni modo sin conexión para evitar
  presentar datos locales como actuales.
- La importación sigue siendo síncrona en la TUI; una URL lenta puede bloquear
  temporalmente la interfaz.
- La revisión periódica usa un cliente HTTPS exclusivo del hilo trabajador y
  comunica resultados con eventos FTXUI; no accede al catálogo desde ese hilo.
- Si fallan tanto la RPC como la lectura de `meta`, la verificación propaga un
  error explícito y ya no simula éxito con la revisión local.
- El filtro Modelo 2024 usa los límites definidos por `FiltroAnios` y la
  clasificación de subtipo usada por el hipercubo.
- No se accedió a Supabase ni se leyeron secretos.

## Pendientes y siguiente paso

- Añadir pruebas de interacción de teclado y expiración de sesión del trabajador
  periódico.
- Probar invocación de extremo a extremo del exportador C++ y fallos de
  escritura atómica cuando la compilación pueda relinkear el ejecutable.
- Ampliar la paridad de los textos de informes y alias de importación CSV.
