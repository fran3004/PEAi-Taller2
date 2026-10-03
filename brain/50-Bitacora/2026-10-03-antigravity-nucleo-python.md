---
tipo: bitacora
estado: aprobado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[00-Inicio]]"
  - "[[SPEC]]"
  - "[[Estructuras]]"
  - "[[Multilista]]"
  - "[[Pila-deshacer]]"
  - "[[Cola-importacion]]"
  - "[[Modelo-de-dominio]]"
  - "[[Contrato-de-datos]]"
  - "[[ADR-0005-Multilista-producto-compartido]]"
  - "[[ADR-0007-Compensacion-de-persistencia-reversion]]"
  - "[[ADR-0009-RPC-y-control-de-revision-optimista]]"
  - "[[ADR-0011-Paridad-arquitectural-Python-Cpp]]"
  - "[[Trazabilidad]]"
origen: "Implementación del núcleo Python de PEA-i (estructuras, dominio, datos, servicios y CLI)"
agente: "Antigravity"
rama: "master"
commit: "feat: nucleo Python"
---

# Bitácora · Implementación del Núcleo Python de PEA-i

## Objetivo
Implementar la arquitectura completa del núcleo de Python (sin GUI) cumpliendo la regla académica fundamental: almacenamiento de entidades maestras exclusivamente en estructuras hechas a mano (`ListaDoble`, `Multilista`, `Pila`, `Cola`), entidades del dominio (`Grupo`, `Investigador`, `IntegranteGrupo`, `Plan`, `Producto`, `Proyecto`), capa de datos (`Sesion`, `ControladorRevision`, repositorios REST/RPC), capa de servicios (`CatalogoInvestigacion`) con transaccionalidad local, compensación ante persistencia fallida, reglas de cascada, mecanismo de Deshacer (Undo LIFO) y subcomandos CLI.

## Qué se hizo

1. **Estructuras Hechas a Mano (`src/pea/estructuras/`)**:
   - `NodoDoble[T]` y `NodoSimple[T]`: Nodos genéricos parametrizados con PEP 695 (Python 3.12).
   - `ListaDoble[T]`: Lista doblemente enlazada con inserciones en $O(1)$, eliminación de nodo conocido en $O(1)$, búsqueda $O(n)$, protocolos `__iter__`, `__len__`, `__getitem__` y método de limpieza anti-ciclos.
   - `Multilista`: Modela el producto como **un único nodo en memoria** (`NodoProductoMultilista`) referenciado concurrentemente desde el grupo y desde todos sus coautores. Incluye desvinculaciones limpias sin punteros colgantes.
   - `Pila[T]`: Estructura LIFO con límite de capacidad (50 por defecto) y modelo `ComandoInverso` para el historial de reversión.
   - `Cola[T]`: Estructura FIFO en tiempo $O(1)$ para tareas de ingesta e importación (`TareaIngesta`, `EstadoTarea`).

2. **Entidades del Dominio (`src/pea/dominio/`)**:
   - `Grupo`: Atributos normados (código GrupLAC único, nombre, categoría Minciencias, OCDE, institución).
   - `Investigador`: Hoja de vida (código RH CvLAC único, nombre, categoría oficial, formación académica).
   - `IntegranteGrupo`: Membresía temporal entre grupo e investigador con rol (Líder, Investigador, Estudiante).
   - `Producto`: Resultado de CTeI bajo las 4 tipologías mayores (GNC, DTI, ASC, FRH), año, validación y atributos.
   - `Plan` y `Proyecto`: Entidades asociadas según la SPEC y el esquema relacional `proyectos`.

3. **Capa de Datos y Persistencia (`src/pea/datos/`)**:
   - `Sesion`: Gestión de estado de autenticación exclusivamente en memoria volátil (nunca persistida en disco) con detección de expiración.
   - `ControladorRevision`: Consulta y verificación optimista de `meta.revision` con detección preventiva de conflictos concurrentes.
   - Repositorios: `RepositorioGrupos`, `RepositorioInvestigadores`, `RepositorioIntegrantes`, `RepositorioProductos` (con llamadas RPC `transaccion_crear_producto`, `transaccion_desactivar_nodo`, `transaccion_eliminar_cascada`) y `RepositorioProyectos`, todos con soporte de paginación automática PostgREST.

4. **Capa de Servicios (`src/pea/servicios/`)**:
   - `CatalogoInvestigacion`: Almacenamiento maestro en memoria en estructuras hechas a mano.
   - CRUD completo para todas las entidades.
   - Desactivación lógica reversible (`activo=false`) sin romper enlaces de la multilista.
   - Eliminación física con reglas de cascada sobre listas, multilista y Supabase.
   - **Compensación automática**: Reversión de estructuras en memoria ante cualquier fallo de red o error HTTP en Supabase.
   - **Deshacer (Undo)**: Desapilado del comando inverso en LIFO y compensación simétrica en memoria y base remota.
   - Recarga completa paginada y verificación de revisión.

5. **Línea de Comandos (`src/pea/cli.py`)**:
   - Subcomandos implementados: `verificar`, `resumen`, `importar-csv`, `exportar-csv`, `cargar-ejemplo`, `aplicar-escenario` e `info`.

6. **Batería de Pruebas Unitarias y de Integración (`tests/unit/`)**:
   - `test_estructuras.py`: Operaciones básicas de ListaDoble, Multilista (identidad `id(p1) == id(p2)`), Pila y Cola.
   - `test_estructuras_borde.py`: Estructuras vacías, un solo elemento, índices fuera de rango, inserción masiva de 10,000 elementos.
   - `test_cascadas.py`: Desactivación reversible y cascada al eliminar productos, investigadores y grupos.
   - `test_deshacer.py`: Reversión de creación, edición, desactivación y reactivación.
   - `test_resiliencia_persistencia.py`: Compensación ante fallo de red, sesión expirada bloqueante, conflicto de revisión y paginación.

## Comandos y resultados
- `ruff check src tests/unit`: 0 errores (All checks passed!).
- `pytest tests/unit -v`: 38 pruebas unitarias pasando al 100%.
- `powershell -ExecutionPolicy Bypass -File .\scripts\verificar.ps1`:
  - Bóveda Obsidian: 66 notas inspeccionadas, 0 errores, 0 advertencias.
  - Pruebas Python: 51 pruebas pasadas (27 contrato/fuentes/cimientos + 24 núcleo nuevas).
  - Pruebas C++: 5 pruebas pasadas (doctest).
  - Resultado global: Todo en verde.

## Decisiones
- Se utilizó la sintaxis nativa de tipos genéricos de Python 3.12 (PEP 695: `class ListaDoble[T]:`, `class Pila[T]:`, `class Cola[T]:`).
- La multilista vincula las entidades `Investigador` como coautores directamente sobre el nodo único del producto, logrando que cualquier mutación sea inmediatamente visible desde las consultas de grupo o autor sin duplicar almacenamiento.
- Se implementó la compensación estricta en el bloque `try...except` del `CatalogoInvestigacion`: si la persistencia falla, se revierte el nodo insertado o el atributo modificado antes de propagar la excepción.

## Pendientes y siguiente paso
- Proceder con la implementación equivalente en C++17 (`ListaDoble.hpp`, `Multilista.hpp`, `Pila.hpp`, `Cola.hpp`, dominio, repositorios Qt Network y servicios).
- Avanzar con la estructura del Hipercubo multidimensional para el cálculo de estadísticas en memoria.
