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
- Se amplió la búsqueda de los directorios para cubrir todos los atributos
  cargados y admitir filtros canónicos `campo:valor`; la autoprueba comprueba
  búsquedas sobre campos no visibles en las filas.
- La revisión normativa confirmó que las tablas se exportan a CSV y los
  gráficos a PNG; no se encontró requisito de exportación Markdown/JSON de
  vistas estadísticas, así que no se añadió esa función.

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
- Continuación posterior: compilación Release y 39 casos/375 aserciones C++
  aprobados, incluida una prueba HTTP local de RPC/meta con fallo explícito y
  fixtures CSV compartidos; `--autoprueba` cubrió 32 pantallas y seis consultas
  de búsqueda/filtro de atributos sin hallazgos.
- `scripts\verificar.ps1`: 289 pruebas Python aprobaron y 3 pruebas de red
  quedaron omitidas; compilación, CTest, autoprueba TUI y bóveda finalizaron
  correctamente. Permanece una advertencia previa por una referencia
  `ADR-0016` en otra bitácora.
- `git diff --check`: correcto. `ruff check` global mantiene el fallo I001
  preexistente de `entrega/Taller2_FF_SM.py`, no modificado aquí.

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
- Añadir comparación de exportadores completos y completar filtros/vistas
  estadísticas que estén respaldados por los requisitos.
