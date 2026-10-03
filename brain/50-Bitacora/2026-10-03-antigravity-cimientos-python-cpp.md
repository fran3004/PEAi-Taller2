---
tipo: bitacora
estado: aprobado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[00-Inicio]]"
  - "[[Arquitectura]]"
  - "[[ADR-0011-Paridad-arquitectural-Python-Cpp]]"
  - "[[ADR-0008-Modelo-de-autenticacion-y-rls]]"
  - "[[ADR-0009-RPC-y-control-de-revision-optimista]]"
  - "[[Trazabilidad]]"
origen: "Creación de los esqueletos ejecutables de Python y C++"
agente: "Antigravity"
rama: "master"
commit: "chore: cimientos Python C++"
---

# Bitácora · Cimientos y Esqueletos Ejecutables Python y C++

## Objetivo
Establecer los esqueletos ejecutables mínimos y la infraestructura de desarrollo para los entornos Python 3.12 (PySide6) y C++17 (Qt 6 Widgets / CMake / Ninja), incluyendo clientes HTTPS REST/RPC para Supabase con soporte TLS, paginación, manejo tipado de errores, tokens volátiles en memoria y suites de pruebas automatizadas.

## Qué se hizo

1. **Infraestructura Python**:
   - `pyproject.toml`: Configurado con backend `hatchling`, metadata institucional UPC y dependencias obligatorias (`requests`, `pydantic`, `pdfplumber`, `beautifulsoup4`, `lxml`, `PySide6`, `pytest`, `pytest-qt`, `ruff`, `responses`).
   - `src/pea/version.py` y `src/pea/__init__.py`: Constantes institucionales (`APP_NAME`, `APP_VERSION`, `INSTITUCION`) y función `obtener_version()`.
   - `src/pea/excepciones.py`: Jerarquía de excepciones tipadas derivada de `ErrorPEA` (`ErrorConexion`, `ErrorAutenticacion`, `ErrorAutorizacion`, `RecursoNoEncontrado`, `ConflictoRevision`, `ErrorValidacion`, `ErrorServidor`).
   - `src/pea/cliente_http.py`: Cliente HTTPS basado en `requests.Session` que soporta GET, POST, PATCH, DELETE, RPC, paginación PostgREST (`Range-Unit: items`), timeout configurable y aislamiento estricto de tokens en memoria volátil (nunca persistidos en disco).
   - `src/pea/cli.py`: Interfaz de consola con subcomandos `info`, `ping` y soporte `-v/--version`.
   - `src/pea/gui.py`: Ventana principal en PySide6 (`VentanaPrincipal`) con paleta institucional UPC (`#003366`, `#006633`), resolución base 1280x720 y modo `--autoprueba` offscreen para integración continua.
   - Pruebas unitarias en `tests/unit/test_cliente_http.py` y `tests/unit/test_cli_gui.py`: 14 pruebas pasando con `pytest` y `pytest-qt`.
   - Validación estática con `ruff check`: 100% aprobado sin advertencias.

2. **Infraestructura C++**:
   - `cpp/CMakeLists.txt`: Configurado para C++17 con CMake 3.20+, Ninja, AUTOMOC/AUTORCC/AUTOUIC, enlaces a `Qt6::Core`, `Qt6::Gui`, `Qt6::Widgets`, `Qt6::Network` y `doctest`. Compilación estricta con banderas de calidad (`-Wall -Wextra -Wpedantic -Werror`).
   - `cpp/include/pea/version.hpp`: Identidad y versión C++.
   - `cpp/include/pea/excepciones.hpp`: Jerarquía de excepciones derivada de `std::runtime_error`.
   - `cpp/include/pea/cliente_http.hpp` y `cpp/src/cliente_http.cpp`: Cliente `ClienteHTTPSupabase` implementado con `QNetworkAccessManager`, `QEventLoop`, timeout por `QTimer`, paginación por cabeceras `Range-Unit: items`, verificación de TLS nativo (`QSslSocket`) y almacenamiento de JWT en memoria volátil.
   - `cpp/include/pea/gui/ventana_principal.hpp` y `cpp/src/gui/ventana_principal.cpp`: Ventana `QMainWindow` con diseño institucional UPC y estado de subsistemas.
   - `cpp/src/main.cpp`: CLI con `-v/--version`, `-h/--help` y `--autoprueba` offscreen.
   - `cpp/tests/`: Pruebas unitarias doctest en `test_version.cpp`, `test_cliente_http.cpp` y `test_gui.cpp` (5 suites, 19 aserciones, 0 fallos).

3. **Verificación Integral**:
   - Actualización de `scripts/verificar.ps1` para integrar la compilación y ejecución automática del núcleo C++ con CTest.
   - Verificación ejecutada exitosamente: Bóveda Obsidian (65 notas íntegras), Pruebas Python (27 pasadas), Pruebas C++ (5 pasadas).

## Comandos y resultados
- `ruff check src tests/unit`: 0 errores.
- `pytest tests/unit -v`: 14 passed in 0.52s.
- `cmake -S cpp -B cpp/build -G Ninja -DCMAKE_BUILD_TYPE=Debug`: Éxito.
- `cmake --build cpp/build`: Éxito (0 warnings, compilado con `-Werror`).
- `ctest --test-dir cpp/build --output-on-failure`: 100% tests passed.
- `pea-cpp.exe --version`: Muestra versión y OpenSSL 3.6.3 activo.
- `powershell -ExecutionPolicy Bypass -File .\scripts\verificar.ps1`: Todo en verde.

## Decisiones
- Mantener la API y jerarquía de excepciones idéntica en Python y C++ para consistencia inter-lenguaje.
- Implementar la ejecución síncrona en el cliente C++ mediante `QEventLoop` local con cancelación por timeout en `QTimer`, garantizando una interfaz directa para la capa de servicios posterior.
- Uso del modo offscreen (`QT_QPA_PLATFORM=offscreen`) en ambos lenguajes mediante el flag `--autoprueba` para permitir pruebas automatizadas de GUI sin requerir servidor X11/Desktop interactivo.

## Pendientes y siguiente paso
- Proceder con la implementación de las estructuras de datos propias hechas a mano (lista doblemente enlazada, multilista, pila, cola e hipercubo) según `brain/20-Diseno/Estructuras-de-datos.md`.
