---
tipo: bitacora
estado: revisado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[00-Inicio]]"
  - "[[Estructuras]]"
  - "[[Multilista]]"
  - "[[Pila-deshacer]]"
  - "[[Cola-importacion]]"
  - "[[Interoperabilidad]]"
origen: "Núcleo C++17 con estructuras hechas a mano y paridad de contrato con Python"
agente: "Antigravity"
rama: "master"
commit: "794126f"
---

# Bitácora · Núcleo C++17 y Paridad Funcional

## Objetivo
Implementar el mismo contrato funcional de Python en C++17 sin GUI: estructuras de datos hechas a mano (`ListaDoble<T>`, `Multilista`, `Pila<T>`, `Cola<T>`), modelos de dominio (`Grupo`, `Investigador`, `IntegranteGrupo`, `Producto`, `Proyecto`, `Plan`), acceso a datos (`Sesion`, `ControladorRevision`, `RepositorioGrupos`, `RepositorioInvestigadores`, `RepositorioIntegrantes`, `RepositorioProductos`, `RepositorioProyectos`), servicios (`CatalogoInvestigacion`) y CLI institucional (`pea-cpp`), garantizando paridad byte-a-byte en el JSON de resumen y cumplimiento estricto de la regla de memoria (regla de los cinco, sin fugas ni punteros colgantes).

## Qué se hizo
- **Estructuras de datos hechas a mano**:
  - `ListaDoble<T>`: Implementación con regla de los cinco, iteradores bidireccionales, inserción $O(1)$ en extremos y por índice, eliminación limpia y alias en snake_case/camelCase.
  - `Multilista`: Gestión del nodo único lógico compartido (`NodoProductoMultilista`) con `std::shared_ptr<Producto>`, enlaces de grupo y lista de autores (`std::shared_ptr<Investigador>`). Desenlace seguro sin doble delete ni punteros colgantes.
  - `Pila<T>`: Pila LIFO acotada a capacidad máxima (50) para historial de deshacer con `ComandoInverso` y descarte del fondo.
  - `Cola<T>`: Cola FIFO para ingesta por lotes con `TareaIngesta` y `EstadoTarea`.
- **Modelos de Dominio**:
  - `Grupo`, `Investigador`, `IntegranteGrupo`, `Producto`, `Proyecto`, `Plan` con serialización bidireccional Qt JSON (`aJson`, `desdeJson`).
- **Capa de Datos**:
  - `Sesion`: Gestión de estado de autenticación y tokens en RAM volátil, con detección y expiración automática.
  - `ControladorRevision`: Concurrencia optimista sobre `meta.revision` con RPC y fallback REST.
  - Repositorios: `RepositorioGrupos`, `RepositorioInvestigadores`, `RepositorioIntegrantes`, `RepositorioProductos`, `RepositorioProyectos` con paginación, transacciones RPC y llamadas REST.
- **Servicios (`CatalogoInvestigacion`)**:
  - Almacenamiento maestro en estructuras propias (no STL en entidades centrales).
  - Operaciones CRUD completas con transaccionalidad local y compensación en RAM ante fallos de persistencia remota.
  - Reglas de cascada: desenlace en Multilista y eliminación de membresías al suprimir grupos o investigadores.
  - Mecanismo de Deshacer (Undo LIFO) con inversión de mutaciones.
  - Recarga remota total y sincronización de revisión.
  - Emisión de resumen y paridad canónica byte-a-byte con Python.
- **CLI Institucional (`pea-cpp`)**:
  - Subcomandos: `info`, `verificar`, `ping`, `resumen` (con flag `--json`), `importar-csv`, `exportar-csv`, `cargar-ejemplo`, `aplicar-escenario`, `--autoprueba`.
- **Pruebas Unitarias doctest**:
  - 17 suites con 125 aserciones cubriendo estructuras, cascadas, deshacer, memoria, concurrencia, resiliencia y paridad.

## Comandos y resultados
- `cmake -B cpp/build -S cpp -G Ninja`: Generación de build Ninja para C++17 con flags estrictos (`-Wall -Wextra -Wpedantic -Werror`).
- `cmake --build cpp/build`: Compilación 100% limpia de `libpea_core.a`, `pea-cpp.exe` y `pruebas_cpp.exe` sin advertencias.
- `.\cpp\build\pruebas_cpp.exe`: 17 suites ejecutadas, 17 aprobadas (125 aserciones OK).
- Paridad byte-a-byte validada entre Python y C++:
  `{"grupos_activos":0,"grupos_totales":0,"investigadores_activos":0,"investigadores_totales":0,"pila_deshacer_tamano":0,"productos_activos":0,"productos_totales":0}`
  Comprobación de igualdad estricta: `True`.
- `.\scripts\verificar.ps1`:
  - Bóveda Obsidian: 68 notas íntegras, 0 errores, 0 advertencias.
  - Pruebas Python: 51 aprobadas.
  - Pruebas C++: 17 suites doctest aprobadas.
  - Estado: Todo en verde.

## Decisiones
- Se adoptó `std::shared_ptr<Producto>` y `std::shared_ptr<Grupo>` en el catálogo y la multilista para modelar fielmente el principio de nodo único compartido en memoria exigido por la SPEC y la cátedra de Estructuras de Datos.
- La Pila LIFO implementa política de descarte de fondo al alcanzar 50 elementos para garantizar el uso acotado de memoria en aplicaciones de escritorio de larga duración.
- El JSON de resumen utiliza ordenamiento lexicográfico estricto de claves y formato compacto, logrando equivalencia exacta a nivel de bytes entre Python y C++.

## Pendientes y siguiente paso
- Integrar la capa visual GUI (PySide6 y Qt6 Widgets) consumiendo exclusivamente los servicios del catálogo sin tocar estructuras ni red directamente.
