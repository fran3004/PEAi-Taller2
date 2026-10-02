---
tipo: requisito
estado: aprobado
creado: 2026-10-02
actualizado: 2026-10-02
relacionado:
  - "[[SPEC]]"
  - "[[Variables-entrada-salida]]"
  - "[[Modelo]]"
  - "[[00-Inicio]]"
origen: "Modelo Minciencias 2024, SCIENTI y Literatura de Estructuras de Datos"
---

# Glosario Oficial de Términos · PEA-i

Este glosario establece las definiciones canónicas y unívocas de los términos del dominio científico, estructuras de datos, patrones de arquitectura y persistencia empleados en el proyecto **PEA-i**.

---

## 1. Términos del Dominio Científico (Modelo Minciencias 2024 y SCIENTI)

### Grupo de Investigación
Unidad fundamental de investigación científica, tecnológica o de innovación reconocida por Minciencias. Debe contar con al menos dos integrantes, un proyecto de investigación registrado, al menos un año de existencia verificable, aval de una institución reconocida y producción científica demostrada ([[Modelo-Grupos#Condiciones de existencia de un Grupo de Investigación]]).

### Investigador
Persona natural vinculada formalmente a actividades de Ciencia, Tecnología e Innovación (CTeI) con hoja de vida registrada en la plataforma CvLAC. Se clasifica en las categorías normadas: **Investigador Emérito**, **Investigador Senior**, **Investigador Asociado**, **Investigador Junior** o **Sin categoría / Integrante vinculado** ([[Modelo-Investigadores#Categorías de investigadores]]).

### Líder de Grupo
Investigador reconocido que ostenta la representación académica y administrativa del grupo ante la institución avaladora y Minciencias. Es responsable de la veracidad y actualización de la información consignada en GrupLAC.

### Integrante de Grupo
Investigador, profesional, técnico o estudiante que mantiene una vinculación activa o histórica con el grupo de investigación. Se registra con un rol (Líder, Investigador, Estudiante) y un periodo temporal delimitado por fecha de inicio y fecha de fin.

### Tipologías Mayores de Producto (CTeI)
Las cuatro grandes agrupaciones de resultados científicos reguladas en el Modelo Minciencias 2024 ([[Modelo-Productos#Clasificación tipológica y pesos ponderados]]):
- **GNC (Generación de Nuevo Conocimiento)**: Aportes originales y significativos al avance de la ciencia (Artículos en revistas indexadas A1, A2, B, C; Libros y capítulos de investigación; Patentes concedidas o solicitadas; Variedades vegetales y animales).
- **DTI (Desarrollo Tecnológico e Innovación)**: Productos técnicos y aplicados dirigidos al sector productivo o social (Diseños industriales, Software con registro de soporte lógico, Plantas piloto, Prototipos industriales, Secretos empresariales, Regulaciones, normas o reglamentos técnicos).
- **ASC / DPC (Apropiación Social del Conocimiento y Divulgación Pública de la Ciencia)**: Procesos de intercambio y transferencia de conocimiento científico con comunidades (Estrategias pedagógicas, Eventos científicos organizados, Informes técnicos finales de investigación, Redes de conocimiento, Obras artísticas de diseño y creación).
- **FRH (Formación de Recurso Humano para la CTeI)**: Dirección o tutoría de trabajos conducentes a grado académico (Tesis de doctorado, Trabajos de maestría, Trabajos de pregrado, Proyectos de semilleros de investigación).

### Estado de Validación de Producto
Condición jurídica y metodológica asignada a un producto de investigación:
- **Avalado**: El producto cuenta con el respaldo formal de la institución y cumple con las guías de revisión documental de Minciencias.
- **Con soporte**: El producto dispone de evidencias digitales adjuntas (enlaces, actas, certificados) pendientes de validación institucional.
- **No avalado**: El producto fue rechazado por inconsistencias documentales o falta de pertinencia temática.

### Áreas OCDE / FORD
Clasificación internacional estandarizada de la Organización para la Cooperación y el Desarrollo Económicos (OCDE) que categoriza el conocimiento en 6 Grandes Áreas (Ciencias Naturales, Ingeniería y Tecnología, Ciencias Médicas y de la Salud, Ciencias Agrícolas, Ciencias Sociales, Humanidades) y 42 Subáreas específicas ([[Modelo-Areas-OCDE]]).

### Cohesión y Cooperación de Grupo
Indicadores métricos del Modelo 2024:
- **Cohesión**: Proporción de productos generados en coautoría conjunta entre los miembros de un mismo grupo.
- **Cooperación**: Proporción de productos generados en colaboración con investigadores o grupos externos nacionales o internacionales ([[Modelo-Estadisticas]]).

---

## 2. Términos de Estructuras de Datos Hechas a Mano

### Lista Doblemente Enlazada (ListaDoble)
Estructura de datos lineal compuesta por nodos que poseen un campo de información (`dato`) y dos punteros o referencias: `anterior` (*prev*) y `siguiente` (*next*). La estructura administra la referencia a la `cabeza` (primer elemento), la `cola` (último elemento) y el contador `tamano`. Permite recorridos bidireccionales y eliminación en tiempo constante $O(1)$ cuando se tiene acceso directo al nodo.

### Multilista
Estructura de datos no lineal en la cual un único nodo de datos (en PEA-i, una entidad `Producto`) pertenece de forma simultánea a múltiples listas enlazadas independientes a través de distintos punteros. En PEA-i, el nodo `Producto` está enlazado a la lista de productos de su `Grupo` y a las listas de productos de cada uno de sus autores (`Investigador`), evitando duplicación en memoria.

### Pila de Deshacer (Undo Stack)
Estructura de datos basada en la disciplina LIFO (*Last-In, First-Out*, último en entrar, primero en salir) que almacena el historial de operaciones de mutación. Cada entrada apilada almacena un **Delta Inverso** (la acción inversa requerida para restituir el estado inmediatamente anterior: ej. si se eliminó una entidad, la inversa es reinsertarla con sus mismos atributos e identificador).

### Cola de Importación (FIFO Queue)
Estructura de datos basada en la disciplina FIFO (*First-In, First-Out*, primero en entrar, primero en salir) utilizada para serializar y procesar de manera secuencial y ordenada las tareas de importación por lotes (descarga de páginas GrupLAC/CvLAC o lectura de archivos CSV).

### Hipercubo Multidimensional (OLAP Tensor)
Estructura de datos n-dimensional construida a medida para el almacenamiento y cálculo estadístico en memoria. En PEA-i cuenta con 5 dimensiones discretas: Grupo, Investigador, Categoría, Año y Validación. Cada coordenada $(g, i, c, a, v)$ almacena un valor numérico escalar entero que representa el conteo de productos activos.

### Operaciones de Hipercubo
- **Rebanada (*Slice*)**: Operación que fija el valor de una dimensión para obtener un hiperplano de dimensión $(N-1)$.
- **Subcubo (*Dice*)**: Operación que selecciona subconjuntos específicos o rangos en múltiples dimensiones simultáneamente (ej. ventana temporal de años y subconjunto de categorías).
- **Enrollar (*Roll-up*)**: Operación de agregación y colapso de una o más dimensiones mediante sumatoria, proyectando los datos hacia niveles de resumen superiores.

---

## 3. Términos de Arquitectura y Base de Datos

### Supabase / PostgREST
Plataforma que proporciona una base de datos relacional PostgreSQL accesible vía web a través de la especificación PostgREST, convirtiendo el esquema relacional en una API RESTful con soporte de filtros, paginación y ordenamiento sobre HTTPS.

### Procedimiento Almacenado Remoto (RPC)
Función PL/pgSQL ejecutada en el motor de base de datos PostgreSQL, invocable desde el cliente vía HTTPS POST a `/rpc/<nombre_funcion>`. Permite encapsular transacciones complejas que afectan múltiples tablas con garantías de atomicidad ($ACID$).

### Control de Revisión (`meta.revision`)
Mecanismo de control de concurrencia optimista implementado mediante un campo entero en la tabla de metadatos del sistema. Cada escritura exitosa incrementa este contador atómicamente a través de un disparador (*trigger*). Las aplicaciones consultan este valor antes de persistir para asegurar que ningún otro cliente haya alterado la base de datos concurrentemente.

### Borrado Lógico vs. Físico
- **Borrado Lógico (Desactivar)**: Modificación del atributo `activo=false`. La fila no se elimina de la base de datos ni de la lista enlazada, pero se excluye de las consultas activas y de los cálculos del hipercubo.
- **Borrado Físico (Eliminar)**: Eliminación permanente del registro en la base de datos mediante sentencia `DELETE` y remoción completa del nodo de las listas en memoria. Requiere resolución de cascada para evitar referencias huérfanas.
