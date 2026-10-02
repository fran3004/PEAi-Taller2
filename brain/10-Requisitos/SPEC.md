---
tipo: requisito
estado: aprobado
creado: 2026-10-02
actualizado: 2026-10-02
relacionado:
  - "[[00-Inicio]]"
  - "[[Glosario]]"
  - "[[Variables-entrada-salida]]"
  - "[[Historias-de-usuario]]"
  - "[[Casos-de-uso]]"
  - "[[Matriz-modelo-requisitos]]"
  - "[[Preguntas-abiertas]]"
  - "[[Modelo]]"
origen: "Contrato de Taller 2 (AGENTS.md), Modelo Minciencias 2024 y Plataforma SCIENTI"
---

# Especificación Formal de Requisitos del Sistema (SPEC) · PEA-i

## 1. Propósito y Alcance

El **Programa Estadístico de Análisis de Investigación (PEA-i)** es una plataforma de software diseñada para el Taller 2 de la asignatura Estructuras de Datos de la Universidad Popular del Cesar (UPC). Su objetivo es modelar, consultar, procesar, analizar y visualizar la actividad investigativa (grupos de investigación, investigadores y productos categorizados) a partir del marco normativo del **Modelo Minciencias 2024** (Código M601PR04G01) y los datos de la plataforma **SCIENTI** (GrupLAC y CvLAC).

El sistema consta de dos aplicaciones de escritorio nativas con interfaz gráfica de usuario:
- Implementación en **Python 3.12** utilizando **PySide6** (Qt for Python).
- Implementación en **C++17** utilizando **Qt 6 Widgets**.

Ambas aplicaciones comparten de manera concurrente una única base de datos relacional PostgreSQL alojada en la nube mediante **Supabase**, accediendo estrictamente vía HTTPS a través de su API PostgREST y RPC.

---

## 2. Requisitos Funcionales (RF) · Trazabilidad R0 a R12

### RF-01: Control de Concurrencia y Detección de Cambios Remotos
| Campo | Valor |
|---|---|
| Identificador | **RF-01** |
| Prioridad | Alta |
| Punto del taller | **R0** (Carga inicial y control de concurrencia) |

- **Descripción**: La aplicación debe mantener un registro de la versión del estado global de la base de datos remota mediante el campo `meta.revision`. Al iniciar sesión, la aplicación consulta `meta.revision` y carga el estado actual. Periódicamente (mediante sondeo en segundo plano) y de manera obligatoria antes de ejecutar cualquier mutación o escritura hacia la base de datos, la aplicación debe consultar el valor actual de `meta.revision`. Si el valor remoto es mayor al valor local esperado, el sistema debe bloquear la escritura, notificar visualmente al usuario con el mensaje *"La base de datos cambió"* y ofrecer la recarga completa del estado en memoria.
- **Criterio de aceptación**:
  1. Si la revisión remota coincide con la local, las mutaciones se persisten con éxito y la revisión remota se incrementa en una unidad atómicamente.
  2. Si la revisión remota difiere (por mutación previa desde otra instancia o lenguaje), la solicitud de escritura es rechazada por el servidor con código de error de conflicto, la aplicación muestra una alerta modal no bloqueante *"La base de datos cambió"* y no corrompe las estructuras en memoria.
- **Origen**: `AGENTS.md` (Base de datos compartida: meta.revision); regla `03-base-de-datos.md`.
- **Supuesto**: `[SUPUESTO]` El sondeo de `meta.revision` se realiza con un temporizador en segundo plano cada 30 segundos si la ventana tiene foco, sin saturar la cuota gratuita de PostgREST.

---

### RF-02: Gestión de Grupos de Investigación
| Campo | Valor |
|---|---|
| Identificador | **RF-02** |
| Prioridad | Alta |
| Punto del taller | **R1** (Gestión de Grupos de Investigación) |

- **Descripción**: El sistema debe permitir registrar, consultar, filtrar, actualizar datos, desactivar lógicamente (`activo=false`) y eliminar grupos de investigación. Cada grupo debe contener: código GrupLAC institucional, nombre oficial, fecha de formación, institución avaladora principal, gran área OCDE, área OCDE específica, categoría Minciencias (A1, A, B, C o Reconocido) y estado activo. Asimismo, debe mantener la lista de integrantes vinculados con su rol institucional (Líder, Investigador, Estudiante) y periodo de vinculación (fecha inicio y fecha fin).
- **Criterio de aceptación**:
  1. No se permite el registro de dos grupos con el mismo código GrupLAC.
  2. Todo grupo registrado debe cumplir con la regla de existencia del Modelo: al menos 1 integrante en rol Líder ([[Modelo-Grupos#Condiciones de existencia de un Grupo de Investigación]]).
  3. La desactivación de un grupo cambia `activo=false` sin eliminarlo de la lista doblemente enlazada ni de la base de datos.
- **Origen**: [[Modelo-Grupos#Categorías de Grupos de Investigación]]; [[SCIENTI-Mapa-de-campos#1. Entidad Grupo de Investigación]].

---

### RF-03: Gestión de Investigadores
| Campo | Valor |
|---|---|
| Identificador | **RF-03** |
| Prioridad | Alta |
| Punto del taller | **R2** (Gestión de Investigadores) |

- **Descripción**: El sistema debe permitir registrar, consultar, filtrar, actualizar datos, desactivar lógicamente y eliminar investigadores. Cada investigador se caracteriza por: identificador único del sistema, código RH (CvLAC), documento de identidad, nombre completo (con nombres y apellidos), categoría oficial Minciencias (Investigador Emérito, Investigador Senior, Investigador Asociado, Investigador Junior o Sin categoría / Integrante vinculado), nivel de formación académica máxima alcanzada, nacionalidad, sexo y estado activo.
- **Criterio de aceptación**:
  1. No se permite duplicar el código RH o documento de identidad en dos investigadores diferentes.
  2. Al consultar un investigador, el sistema debe desplegar su categoría vigente y el listado de grupos de investigación a los que pertenece actualmente o en los que ha tenido vinculación histórica.
- **Origen**: [[Modelo-Investigadores#Requisitos para el reconocimiento de investigadores]]; [[SCIENTI-Mapa-de-campos#2. Entidad Investigador]].

---

### RF-04: Gestión y Clasificación de Productos de Investigación
| Campo | Valor |
|---|---|
| Identificador | **RF-04** |
| Prioridad | Alta |
| Punto del taller | **R3** (Gestión de Productos de Investigación) |

- **Descripción**: El sistema debe gestionar el inventario de productos de investigación, clasificándolos de acuerdo con las cuatro tipologías mayores del Modelo Minciencias 2024:
  1. **GNC**: Generación de Nuevo Conocimiento (Artículos A1, A2, B, C; Libros resultado de investigación; Capítulos de libro; Patentes de invención).
  2. **DTI**: Desarrollo Tecnológico e Innovación (Diseños industriales, Software, Plantas piloto, Prototipos, Secretos empresariales).
  3. **ASC**: Apropiación Social del Conocimiento y Divulgación Pública de la Ciencia (Estrategias pedagógicas, Eventos científicos, Informes técnicos finales, Obras de arte/diseño).
  4. **FRH**: Formación de Recurso Humano para la CTeI (Tesis de doctorado, Trabajos de grado de maestría, Trabajos de pregrado, Proyectos de investigación y desarrollo).
  Cada producto incluye: código/id, título, tipo mayor, subtipo específico, año de obtención, mes, estado de validación institucional (Avalado, Con soporte, No avalado) y estado de activación (`activo=true/false`).
- **Criterio de aceptación**:
  1. El sistema restringe la asignación de subtipos exclusivamente a los tipos mayores normados en el Modelo 2024.
  2. Todo producto debe estar asociado obligatoriamente a un año de producción válido (entero entre 1970 y el año en curso).
- **Origen**: [[Modelo-Productos#Clasificación tipológica y pesos ponderados]]; [[SCIENTI-Mapa-de-campos#4. Entidad Producto de Investigación]].

---

### RF-05: Multilista Bidireccional de Coautoría y Pertenencia
| Campo | Valor |
|---|---|
| Identificador | **RF-05** |
| Prioridad | Alta |
| Punto del taller | **R4** (Estructura de Multilista) |

- **Descripción**: Cada producto de investigación debe instanciarse en la memoria del programa como **un único nodo**. Este nodo debe estar referenciado de manera concurrente y cruzada:
  - Desde la lista de productos propios del grupo de investigación que declara el producto.
  - Desde la lista de productos de cada uno de los investigadores autores vinculados al producto.
  La estructura de multilista debe permitir navegar desde un grupo hacia todos sus productos y de allí a sus coautores; y viceversa, desde un investigador hacia todos sus productos y de allí a los grupos involucrados, sin replicar los datos del producto en memoria.
- **Criterio de aceptación**:
  1. La modificación en memoria de cualquier atributo de un producto (ej. actualización de título o estado de validación) se refleja instantáneamente en la vista del grupo y en la vista de todos los investigadores coautores, verificándose mediante identidad de puntero o referencia (`id(p1) == id(p2)` en Python, `&p1 == &p2` en C++).
  2. Al eliminar un producto, el nodo se desenlaza limpiamente tanto de la lista del grupo como de las listas de todos los investigadores coautores, sin dejar punteros colgantes (*dangling pointers*) ni fugas de memoria.
- **Origen**: `AGENTS.md` (Arquitectura: multilista); `.agent/skills/estructuras-de-datos/SKILL.md#Multilista`.

---

### RF-06: Gestión de Colecciones mediante Lista Doblemente Enlazada Manual
| Campo | Valor |
|---|---|
| Identificador | **RF-06** |
| Prioridad | Alta |
| Punto del taller | **R5** (Lista Doblemente Enlazada) |

- **Descripción**: Las colecciones maestras en memoria de Grupos e Investigadores deben ser almacenadas y gestionadas exclusivamente mediante una implementación manual propia de **Lista Doblemente Enlazada**. La estructura debe constar de nodos con punteros `anterior` (*prev*) y `siguiente` (*next*), y la cabecera de la lista debe mantener referencias al primer nodo (`cabeza`), último nodo (`cola`) y la cantidad de elementos (`tamano`). Debe proveer operaciones de inserción al inicio, inserción al final, inserción en índice, eliminación de nodo específico en $O(1)$ cuando se dispone de la referencia, búsqueda secuencial en $O(n)$ y recorrido bidireccional mediante iteradores.
- **Criterio de aceptación**:
  1. Inserción al inicio y al final operan en tiempo $O(1)$.
  2. La eliminación del primer, último o único nodo de la lista preserva la consistencia de los punteros cabeza y cola.
  3. En Python la lista implementa los protocolos `__iter__` y `__len__`. En C++ se implementa como clase de plantilla (*template*) con cumplimiento estricto de la regla de los cinco (destructor, constructor/operador de copia y de movimiento).
- **Origen**: `AGENTS.md` (Arquitectura: estructuras hechas a mano); `.agent/skills/estructuras-de-datos/SKILL.md#Lista doblemente enlazada`.

---

### RF-07: Pila de Deshacer Transaccional (Undo)
| Campo | Valor |
|---|---|
| Identificador | **RF-07** |
| Prioridad | Alta |
| Punto del taller | **R6** (Estructura de Pila / Deshacer) |

- **Descripción**: El sistema debe registrar en una estructura propia de **Pila (LIFO)** hecha a mano cada operación de mutación ejecutada por el usuario (creación de entidad, edición de campos, cambio de estado de activación `activo` y eliminación lógica o física). Cada elemento apilado debe encapsular el comando inverso o estado anterior (*delta inverso*). Al invocar la acción "Deshacer" (Ctrl+Z o botón en la interfaz), el sistema extrae el elemento superior de la pila, aplica la mutación inversa sobre las estructuras de memoria y seguidamente sincroniza el cambio en la base de datos remota Supabase.
- **Criterio de aceptación**:
  1. Si la pila está vacía, la acción "Deshacer" se encuentra deshabilitada y no genera errores en tiempo de ejecución.
  2. Si se realiza una desactivación accidental de un investigador, al accionar "Deshacer" se restaura su estado a `activo=true` tanto en la estructura en memoria como en PostgreSQL vía REST.
  3. Si la base de datos remota rechaza la reversión por conflicto de revisión concurrente, la estructura en memoria no se revierte y se alerta al usuario.
- **Origen**: `AGENTS.md` (Arquitectura: pila de deshacer); `.agent/skills/estructuras-de-datos/SKILL.md#Pila (deshacer)`.

---

### RF-08: Cola FIFO de Importación y Procesamiento por Lotes
| Campo | Valor |
|---|---|
| Identificador | **RF-08** |
| Prioridad | Alta |
| Punto del taller | **R7** (Estructura de Cola / Importación) |

- **Descripción**: La recepción y procesamiento de solicitudes de importación (ya sea descarga scraping desde URLs de GrupLAC/CvLAC o carga masiva desde archivos CSV) debe administrarse mediante una estructura propia de **Cola (FIFO)** hecha a mano. La cola encola tareas que representan un archivo o URL a procesar, gestionando los estados del ciclo de vida: `Pendiente`, `Procesando`, `Terminada` y `Con error`.
- **Criterio de aceptación**:
  1. Las tareas se procesan estrictamente en el orden en que fueron ingresadas (*First-In, First-Out*).
  2. Si una tarea en la cola experimenta un error de red o de formato de archivo, el sistema registra el fallo en la bitácora de la tarea, marca su estado como `Con error` y procede inmediatamente con la siguiente tarea sin interrumpir la cola.
- **Origen**: `AGENTS.md` (Arquitectura: cola); `.agent/skills/estructuras-de-datos/SKILL.md#Cola (importacion)`.

---

### RF-09: Modelo de Hipercubo Multidimensional de Métricas
| Campo | Valor |
|---|---|
| Identificador | **RF-09** |
| Prioridad | Alta |
| Punto del taller | **R8** (Estructura de Hipercubo) |

- **Descripción**: El sistema debe instanciar en memoria un **Hipercubo Multidimensional** propio (estructura tensorial n-dimensional hecha a mano) para almacenar la consolidación de productos científicos. Las 5 dimensiones canónicas del hipercubo son:
  - **Dimensión 1 (Grupo)**: Identificador del Grupo de Investigación.
  - **Dimensión 2 (Investigador)**: Código del Investigador.
  - **Dimensión 3 (Categoría)**: Tipo mayor de producto (GNC, DTI, ASC, FRH).
  - **Dimensión 4 (Año)**: Año de producción científica.
  - **Dimensión 5 (Validación)**: Estado de validación (Avalado, Con soporte, No avalado).
  La medida contenida en cada celda $(d_1, d_2, d_3, d_4, d_5)$ es un escalar entero que representa la **cantidad de productos ACTIVOS**.
- **Criterio de aceptación**:
  1. Los productos con estado `activo=false` no se computan en el hipercubo o se excluyen de la medida activa.
  2. La estructura soporta celdas dispersas (*sparse*) sin consumo desmedido de memoria.
- **Origen**: `AGENTS.md` (Arquitectura: hipercubo); `.agent/skills/estructuras-de-datos/SKILL.md#Hipercubo`.

---

### RF-10: Cálculo Estadístico y Agregaciones en Memoria
| Campo | Valor |
|---|---|
| Identificador | **RF-10** |
| Prioridad | Alta |
| Punto del taller | **R9** (Cálculo estadístico desde Hipercubo) |

- **Descripción**: Todos los cálculos analíticos, totales agregados, medias anuales y perfiles de investigación solicitados por la interfaz gráfica deben derivarse **exclusivamente a partir de operaciones algorítmicas sobre el Hipercubo en memoria**, quedando estrictamente prohibido realizar consultas SQL con cláusulas agregadas (`SUM`, `COUNT`, `GROUP BY`) contra la base de datos remota durante el funcionamiento regular. Las operaciones soportadas son:
  - **Rebanada (*Slice*)**: Fijar una dimensión en un valor específico (ej. todos los productos del Grupo $G_1$).
  - **Subcubo (*Dice*)**: Filtrar rangos multidimensionales (ej. ventana de observación 2019–2024 para la categoría GNC).
  - **Enrollar (*Roll-up*)**: Proyectar y sumarizar colapsando una o más dimensiones (ej. totalizar por año colapsando investigadores y validaciones).
- **Criterio de aceptación**:
  1. Los resultados numéricos arrojados por el hipercubo para cualquier corte dimensional deben ser idénticos a los arrojados por una consulta SQL `GROUP BY` de verificación ejecutada en las suites de prueba automáticas.
  2. El cálculo estadístico en memoria se ejecuta en un tiempo menor a 50 milisegundos para una colección de hasta 10,000 productos.
- **Origen**: `AGENTS.md` (Arquitectura: estadísticas desde el hipercubo); `.agent/rules/02-estructuras-y-capas.md`.

---

### RF-11: Interfaz Gráfica de Usuario (GUI) y Vistas Estadísticas
| Campo | Valor |
|---|---|
| Identificador | **RF-11** |
| Prioridad | Alta |
| Punto del taller | **R10** (Interfaz Gráfica) |

- **Descripción**: La aplicación de escritorio debe proporcionar una GUI completa y ergonómica construida sobre Qt 6, compuesta por:
  - **Barra Lateral de Navegación**: Acceso directo al Panel Principal (*Dashboard*), Gestión de Grupos, Gestión de Investigadores, Inventario de Productos, Importación por Lotes y Configuración de Conexión.
  - **Panel Principal (Resumen/Dashboard)**: Tarjetas resumen con métricas clave (total de grupos activos, investigadores, total de productos clasificados GNC/DTI/ASC/FRH) y gráficos estadísticos (distribución por categorías, evolución temporal por año).
  - **Vistas Maestras con Búsqueda y Filtros**: Tablas interactivas con paginación local, ordenamiento por columnas y filtros reactivos.
  - **Gráficos Integrados**: Visualización mediante `matplotlib` embebido en PySide6 y gráficos con `QPainter` / Qt Charts en C++.
  - **Internacionalización y Ortografía**: Todos los textos, etiquetas, títulos de gráficos, mensajes de diálogo y advertencias deben presentarse en idioma **español correcto**, con renderizado adecuado de tildes y caracteres especiales (ñ, comillas). Queda prohibida la presencia de etiquetas en inglés ("Dashboard", "Summary", etc.).
- **Criterio de aceptación**:
  1. La GUI nunca realiza llamadas directas a la base de datos ni manipula las estructuras de datos nativas directamente; interactúa únicamente a través de la capa de Servicios.
  2. Todos los textos en pantalla cumplen con la regla de idioma español estricto sin excepciones.
- **Origen**: `AGENTS.md` (Misión, Idioma y estilo); `.agent/rules/01-idioma-y-estilo.md`.

---

### RF-12: Persistencia Atómica y Resiliencia REST/RPC
| Campo | Valor |
|---|---|
| Identificador | **RF-12** |
| Prioridad | Alta |
| Punto del taller | **R11** (Persistencia atómica y reversión) |

- **Descripción**: Las operaciones que involucren mutaciones compuestas sobre múltiples tablas (ej. creación de un producto con sus vínculos simultáneos al grupo y a múltiples autores coautores) deben ejecutarse mediante **funciones de Procedimiento Almacenado Remoto (RPC)** en PostgreSQL para garantizar la atomicidad transaccional ($ACID$). Si la petición HTTPS falla (por desconexión de red, error 4xx o 5xx del servicio Supabase), la capa de Servicios debe atrapar la excepción, revertir inmediatamente el cambio aplicado sobre las estructuras en memoria para evitar discrepancias, y presentar un diálogo de error al usuario informando la causa del fallo.
- **Criterio de aceptación**:
  1. Si se simula un corte de red durante una operación de guardado, la estructura en memoria permanece en el estado previo exacto a la operación.
  2. No existen estados intermedios en la base de datos (o se persisten todos los registros relacionados o ninguno).
- **Origen**: `AGENTS.md` (Base de datos compartida: PostgREST/RPC); `.agent/rules/03-base-de-datos.md`.

---

### RF-13: Extracción e Importación de Fuentes Externas
| Campo | Valor |
|---|---|
| Identificador | **RF-13** |
| Prioridad | Alta |
| Punto del taller | **R12** (Importación y extracción) |

- **Descripción**: El sistema debe proveer dos mecanismos de ingesta de datos:
  1. **Scraping Web Responsable**: Módulo extractor para URLs públicas de GrupLAC y CvLAC bajo el dominio oficial `scienti.minciencias.gov.co`. Debe operar bajo HTTPS, respetar una pausa mínima de 1 segundo entre solicitudes consecutivas, establecer un límite de 3 reintentos con retraso creciente, configurar un `User-Agent` institucional universitario identificable y almacenar las respuestas crudas en caché local (`datos/cache/`).
  2. **Importación Masiva desde CSV Canónico**: Mecanismo de carga de contingencia para operar en ambientes desconectados a partir de archivos delimitados por comas que estructuran grupos, investigadores y productos.
- **Criterio de aceptación**:
  1. Si un recurso web retorna error 404 o 500 tras 3 reintentos, el sistema reporta el fallo con claridad al usuario sin inventar ni simular información, sugiriendo la carga mediante el archivo CSV alternativo.
  2. La importación mediante CSV procesa y valida los esquemas mediante modelos Pydantic en Python y analizadores equivalentes en C++.
- **Origen**: `AGENTS.md` (Extracción de fuentes); `.agent/rules/06-fuentes-y-secretos.md`.

---

## 3. Requisitos No Funcionales (RNF) · Trazabilidad C1 a C6

### RNF-01: Prohibición de Contenedores Nativos como Almacenamiento Principal
| Campo | Valor |
|---|---|
| Identificador | **RNF-01** |
| Prioridad | Alta |
| Punto del taller | **C1** (Estructuras de datos hechas a mano) |

- **Descripción**: Las entidades maestras del dominio (Grupos, Investigadores, Productos e Integrantes) no pueden almacenarse en contenedores nativos del lenguaje (`list`, `dict`, `set` en Python; `std::vector`, `std::map`, `std::unordered_map`, `std::deque` en C++) como repositorio principal en memoria. Estos contenedores nativos se permiten únicamente como variables locales auxiliares de corta duración para ordenamientos temporales, parseo de JSON o retornos de vistas, debiendo registrarse cualquier excepción estructural en un documento de Decisión de Arquitectura (ADR).
- **Criterio de aceptación**: Auditoría estática de código comprueba que las colecciones en las clases de Servicio son instancias de `ListaDoble`, `Multilista`, `Pila`, `Cola` o `Hipercubo`.
- **Origen**: `AGENTS.md` (Arquitectura: estructuras hechas a mano); `.agent/rules/02-estructuras-y-capas.md`.

---

### RNF-02: Paridad Arquitectural y Funcional Multiplataforma
| Campo | Valor |
|---|---|
| Identificador | **RNF-02** |
| Prioridad | Alta |
| Punto del taller | **C2** (Paridad multi-lenguaje Python y C++) |

- **Descripción**: La arquitectura del sistema debe ser homóloga e idéntica en las dos implementaciones (Python y C++), respetando el desacoplamiento por capas:
  $$\text{GUI} \longrightarrow \text{Servicios} \longrightarrow \text{Estructuras Propias} \longrightarrow \text{Repositorios REST/RPC} \longrightarrow \text{HTTPS} \longrightarrow \text{Supabase (PostgreSQL)}$$
  Ningún componente de la GUI podrá interactuar directamente con estructuras internas, sockets de red o consultas SQL.
- **Criterio de aceptación**: Los flujos funcionales, la disposición visual de controles y los resultados numéricos de estadísticas ante los mismos datos de prueba deben ser indistinguibles entre la versión de Python y la de C++.
- **Origen**: `AGENTS.md` (Misión y Arquitectura).

---

### RNF-03: Confinamiento Estadístico al Hipercubo
| Campo | Valor |
|---|---|
| Identificador | **RNF-03** |
| Prioridad | Alta |
| Punto del taller | **C3** (Estadísticas exclusivas desde el hipercubo) |

- **Descripción**: Ninguna pantalla, reporte o diálogo podrá obtener métricas numéricas agregadas mediante peticiones SQL directas a la base de datos o APIs analíticas externas. Todo indicador de grupo, distribución de categorías o promedio temporal se extrae computacionalmente recorriendo el Hipercubo en memoria.
- **Criterio de aceptación**: En modo desconectado de la red, una vez cargados los datos iniciales, el usuario puede explorar, filtrar y graficar todas las métricas del hipercubo sin emitir una sola petición HTTP.
- **Origen**: `AGENTS.md` (Arquitectura: estadísticas); `.agent/rules/02-estructuras-y-capas.md`.

---

### RNF-04: Seguridad, Autenticación y Conexión HTTPS
| Campo | Valor |
|---|---|
| Identificador | **RNF-04** |
| Prioridad | Alta |
| Punto del taller | **C4** (Seguridad y Supabase) |

- **Descripción**: La comunicación con Supabase se realiza exclusivamente bajo cifrado TLS 1.3 vía HTTPS. Los clientes de escritorio deben utilizar únicamente la clave pública de Supabase (*publishable key* / `anon key`) y mecanismos de autenticación de usuario (Supabase Auth). Queda terminantemente prohibido incluir o compilar la clave secreta (*secret key* o `service_role`) en el código fuente, archivos `.env` versionados, notas de documentación o ejecutables binarios distribuidos. Queda prohibida la conexión directa al puerto 5432 de PostgreSQL.
- **Criterio de aceptación**: El análisis de secretos mediante `git log`, inspección de binarios con `strings` y escáner de variables de entorno garantiza cero apariciones de credenciales `service_role` o contraseñas de conexión TCP a base de datos.
- **Origen**: `AGENTS.md` (Base de datos compartida y Secretos); `.agent/rules/03-base-de-datos.md`; `.agent/rules/06-fuentes-y-secretos.md`.

---

### RNF-05: Calidad, Idioma Español y Pruebas Desconectadas
| Campo | Valor |
|---|---|
| Identificador | **RNF-05** |
| Prioridad | Alta |
| Punto del taller | **C5** (Calidad y Verificación) |

- **Descripción**: El código base en Python 3.12 debe cumplir validaciones de tipado estricto (`mypy`) y formato sin errores de linter (`ruff`). El código base en C++17 debe compilar sin advertencias bajo `-Wall -Wextra -Wpedantic`. Toda la documentación, comentarios, interfaces de usuario y mensajes de consola deben estar en español normativo en codificación UTF-8 sin BOM. Las suites de prueba automatizadas deben ejecutarse por defecto sin conexión a internet mediante fixtures locales pregrabados y anonimizados.
- **Criterio de aceptación**: La ejecución del script `scripts/verificar.ps1` culmina con estado `OK` en la compilación y pruebas de ambos lenguajes sin requerir conectividad de red.
- **Origen**: `AGENTS.md` (Idioma y estilo, Pruebas y verificación); `.agent/rules/01-idioma-y-estilo.md`; `.agent/rules/05-verificacion.md`.

---

### RNF-06: Semántica de Borrado Lógico vs. Físico y Reversibilidad
| Campo | Valor |
|---|---|
| Identificador | **RNF-06** |
| Prioridad | Alta |
| Punto del taller | **C6** (Desactivar vs Eliminar y Deshacer) |

- **Descripción**: El sistema debe separar conceptual y técnicamente dos operaciones de supresión:
  1. **Desactivar (Borrado Lógico)**: Asigna `activo=false` a la entidad. La entidad permanece en la lista doblemente enlazada, conserva sus enlaces en la multilista y persiste en PostgreSQL. El hipercubo la excluye de las métricas activas. Esta operación es completamente reversible en cualquier momento.
  2. **Eliminar (Borrado Físico)**: Remueve la entidad de la lista doblemente enlazada, desenlaza sus nodos de la multilista y ejecuta un `DELETE` en la base de datos aplicando reglas de integridad referencial en cascada controladas. Todo cambio de borrado físico o lógico se registra en la Pila de Deshacer para posibilitar su restitución.
- **Criterio de aceptación**: Al desactivar un producto, este deja de aparecer en los gráficos y sumatorias del panel, pero sigue listándose en la tabla de productos bajo el filtro "Inactivos", permitiendo su reactivación inmediata.
- **Origen**: `AGENTS.md` (Arquitectura: desactivar vs eliminar); `.agent/rules/02-estructuras-y-capas.md`.
