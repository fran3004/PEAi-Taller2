---
tipo: resultado-de-pruebas
estado: revisado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[_Indice]]"
  - "[[SPEC]]"
  - "[[Matriz-modelo-requisitos]]"
  - "[[Arquitectura]]"
  - "[[Estructuras]]"
  - "[[Multilista]]"
  - "[[Hipercubo]]"
  - "[[Pila-deshacer]]"
  - "[[Cola-importacion]]"
  - "[[Contrato-de-datos]]"
  - "[[Interoperabilidad]]"
  - "[[Ingesta]]"
  - "[[GUI-paridad]]"
  - "[[GUI-Diseno-Python]]"
  - "[[Seguridad-y-credenciales]]"
  - "[[Despliegue]]"
origen: "AUDITORIA-DISENO-PEAI.md - Fase 15"
---

# Matriz de Trazabilidad Integral: Requisitos, Diseño y Pruebas

Esta matriz establece el vínculo verificable entre los requisitos formales de la [[SPEC]], las notas de diseño en [[_Indice|brain/20-Diseno/]], las decisiones arquitectónicas ([[ADR-0001-Boveda-viva|ADRs]]) y las estrategias de prueba automatizadas.

## 1. Requisitos Fundacionales y de Estructuras (R0 – R4)

| ID | Requisito | Nota de Diseño | ADR Asociado | Estrategia de Prueba | Archivo de Prueba / Verificación |
|---|---|---|---|---|---|
| **R0** | Persistencia exclusiva en PostgreSQL Supabase vía HTTPS | [[Contrato-de-datos]], [[Seguridad-y-credenciales]] | [[ADR-0002-Unico-proyecto-Supabase]], [[ADR-0008-Modelo-de-autenticacion-y-rls]] | Inspección estricta de red; pruebas de integración con sesión Auth | `tests/test_repositorio_supabase.py` |
| **R1** | Estructuras de datos hechas a mano | [[Estructuras]], [[Multilista]], [[Hipercubo]], [[Pila-deshacer]], [[Cola-importacion]] | [[ADR-0005-Multilista-producto-compartido]], [[ADR-0006-Hipercubo-estadisticas-en-memoria]] | Pruebas unitarias de manipulación de punteros y memoria | `tests/test_estructuras_lista.py`, `tests/test_estructuras_multilista.py` |
| **R2** | Nodo único de producto en Multilista | [[Multilista]], [[Modelo-de-dominio]] | [[ADR-0005-Multilista-producto-compartido]] | Comprobación de identidad de punteros (`id(nodo1) == id(nodo2)`) | `tests/test_multilista_coautoria.py` |
| **R3** | Pila de deshacer (LIFO) de tamaño acotado | [[Pila-deshacer]], [[Arquitectura]] | [[ADR-0007-Compensacion-de-persistencia-reversion]] | Pruebas de inversión de deltas y límite máximo de capacidad | `tests/test_pila_deshacer.py` |
| **R4** | Hipercubo 5D para agregaciones estadísticas en memoria | [[Hipercubo]] | [[ADR-0006-Hipercubo-estadisticas-en-memoria]] | Comparación contra oráculo matemático | `tests/test_hipercubo_olap.py`, `tests/fixtures/esperado.json` |

## 2. Requisitos de Ingesta, Concurrencia y UI (R5 – R12)

| ID | Requisito | Nota de Diseño | ADR Asociado | Estrategia de Prueba | Archivo de Prueba / Verificación |
|---|---|---|---|---|---|
| **R5** | Cola de importación FIFO asíncrona | [[Cola-importacion]], [[Ingesta]] | [[ADR-0010-Limites-y-responsabilidad-de-ingesta]] | Pruebas de orden de despacho y recuperación tras error | `tests/test_cola_importacion.py` |
| **R6** | Extracción web responsable SCIENTI con pausas y caché | [[Ingesta]], [[Seguridad-y-credenciales]] | [[ADR-0010-Limites-y-responsabilidad-de-ingesta]], [[ADR-0004-Privacidad-de-fuentes-reales]] | Mocking de respuestas HTTP; verificación de User-Agent y pausas | `tests/test_ingesta_scienti.py` |
| **R7** | Carga masiva por archivos CSV | [[Ingesta]] | [[ADR-0010-Limites-y-responsabilidad-de-ingesta]] | Parseo y validación de fixtures tabulares canónicos | `tests/test_ingesta_csv.py` |
| **R8** | Bloqueo optimista por revisión de base de datos | [[Contrato-de-datos]], [[Arquitectura]] | [[ADR-0009-RPC-y-control-de-revision-optimista]] | Simulación de conflicto de concurrencia concurrent write (409) | `tests/test_concurrencia_revision.py` |
| **R9** | Compensación y reversión local tras fallo remoto | [[Arquitectura]], [[Pila-deshacer]] | [[ADR-0007-Compensacion-de-persistencia-reversion]] | Inyección de fallo de red tras mutación local | `tests/test_servicio_compensacion.py` |
| **R10** | Interfaz gráfica de Python según el diseño de referencia (paridad con C++ pendiente) | [[GUI-Diseno-Python]], [[GUI-paridad]] | [[ADR-0012-Diseno-GUI-y-navegacion]], [[ADR-0013-Vistas-secundarias]], [[ADR-0016-Alcance-de-pantallas-y-datos-del-boceto]], [[ADR-0017-Tecnologia-de-interfaz-Qt-Widgets]] | Pruebas de interfaz offscreen con `pytest-qt` | `tests/test_gui_paridad.py` |
| **R11** | Visualizador nativo de grafo de coautoría | [[GUI-Diseno-Python]], [[Multilista]] | [[ADR-0015-Analisis-de-red-nativo]] | Verificación de generación de nodos y aristas en QGraphicsScene | `tests/test_grafo_coautoria.py` |
| **R12** | Empaquetado Windows y ejecución portátil | [[Despliegue]] | [[ADR-0011-Paridad-arquitectural-Python-Cpp]] | Pruebas de artefactos generados en entorno limpio | `scripts/empaquetar-python.ps1`, `scripts/empaquetar-cpp.ps1` |

## 3. Criterios Normativos de Calidad y Verificación (C1 – C6)

| Criterio | Descripción | Mecanismo de Control | Verificación Automatizada |
|---|---|---|---|
| **C1** | Cero fugas de memoria y control RAII en C++ | Uso de `std::shared_ptr`, `std::unique_ptr` | Valgrind / sanitizers (`-fsanitize=address`) |
| **C2** | Tipado estricto y linting en Python 3.12 | Type hints en 100% de firmas públicas | `ruff check`, `mypy --strict` |
| **C3** | Trazabilidad del Modelo Minciencias 2024 | Citas a páginas de `Modelo-2024-original.md` | `python tools/brain/verificar_brain.py` |
| **C4** | Cero anglicismos en la interfaz de usuario | Auditoría léxica en catálogos de cadenas | Pruebas de internacionalización / UI inspection |
| **C5** | Privacidad de datos personales | Exclusión de datos sensibles en commits | `tools/brain/verificar_brain.py`, filtros git |
| **C6** | Verificación unificada mediante script maestro | Compilación C++, pruebas y bóveda | `scripts/verificar.ps1` |
