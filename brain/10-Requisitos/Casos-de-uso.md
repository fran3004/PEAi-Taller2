---
tipo: caso-de-uso
estado: aprobado
creado: 2026-10-02
actualizado: 2026-10-02
relacionado:
  - "[[SPEC]]"
  - "[[Historias-de-usuario]]"
  - "[[00-Inicio]]"
origen: "Especificación Funcional PEA-i"
---

# Casos de Uso del Sistema (CU) · PEA-i

Este documento formaliza los casos de uso principales del sistema PEA-i, detallando los flujos de interacción, condiciones operativas, manejo de fallas y reversión transaccional.

---

## CU-01: Iniciar Sesión y Cargar Estado del Sistema
- **Actor Principal**: Usuario / Administrador
- **Punto del Taller**: R0, R11, C4
- **Requisitos Relacionados**: [[SPEC#RF-01: Control de Concurrencia y Detección de Cambios Remotos]], [[SPEC#RF-12: Persistencia Atómica y Resiliencia REST/RPC]], [[SPEC#RNF-04: Seguridad, Autenticación y Conexión HTTPS]].
- **Precondiciones**:
  1. Conexión a internet disponible hacia el endpoint HTTPS de Supabase.
  2. Variables de entorno o configuración con clave publishable configurada.
- **Disparador**: Apertura de la aplicación o acción manual "Conectar / Recargar".
- **Resultado Esperado (Postcondiciones)**:
  - Estado global de `meta.revision` almacenado localmente.
  - Grupos e Investigadores cargados en sus respectivas `ListaDoble` hechas a mano.
  - Productos e integrantes vinculados en la `Multilista`.
  - `Hipercubo` poblado con los productos activos.
  - Panel principal renderizado con estadísticas iniciales.

### Flujo Normal
1. El usuario inicia la aplicación o presiona "Conectar".
2. La capa de Servicios solicita al Repositorio REST consultar `meta.revision`.
3. El sistema recibe la revisión remota y la fija como referencia local.
4. El Repositorio REST consulta las tablas `grupos`, `investigadores`, `integrantes` y `productos` paginando adecuadamente.
5. Los Servicios instancian las entidades en la `ListaDoble` de grupos y la `ListaDoble` de investigadores.
6. Los Servicios crean los nodos únicos de productos y los integran en la `Multilista` enlazándolos con grupos y autores.
7. Los Servicios alimentan el `Hipercubo` registrando las frecuencias de productos activos por (Grupo, Investigador, Categoría, Año, Validación).
8. La GUI actualiza el Panel Principal y habilita la barra de navegación.

### Flujos Alternativos y Excepciones
- **A1. Falla de conexión a internet o timeout de Supabase**:
  1. El Repositorio REST atrapa la excepción de red.
  2. La GUI muestra una barra de aviso *"Sin conexión a la base de datos remota"*.
  3. El sistema bloquea todas las acciones de escritura y modificación.
  4. Si existen datos en caché local de sesión previa, se permite su consulta de solo lectura advirtiendo que pueden no estar actualizados.

---

## CU-02: Registrar y Vincular Producto de Investigación en Multilista
- **Actor Principal**: Investigador / Líder de Grupo
- **Punto del Taller**: R3, R4, R11
- **Requisitos Relacionados**: [[SPEC#RF-04: Gestión y Clasificación de Productos de Investigación]], [[SPEC#RF-05: Multilista Bidireccional de Coautoría y Pertenencia]], [[SPEC#RF-12: Persistencia Atómica y Resiliencia REST/RPC]].
- **Precondiciones**:
  1. El grupo de investigación declarante y al menos un investigador autor ya existen en el sistema.
  2. La aplicación está conectada con revisión remota sincronizada.
- **Disparador**: El usuario pulsa "Nuevo Producto" en la vista de Productos o de Grupo.
- **Resultado Esperado**:
  - Producto creado como nodo único en memoria.
  - Nodo enlazado en la lista del grupo y en las listas de los autores coautores.
  - Registro atómico persistido en PostgreSQL vía RPC.
  - Hipercubo incrementado en la celda correspondiente.
  - Registro de mutación apilado en la Pila de Deshacer.

### Flujo Normal
1. El usuario ingresa los datos del formulario: título, tipo mayor (GNC/DTI/ASC/FRH), subtipo, año, estado de validación y detalles bibliográficos.
2. El usuario selecciona el grupo y marca los autores coautores de la lista de investigadores disponibles.
3. El usuario presiona "Guardar Producto".
4. La capa de Servicios valida los datos obligatorios y la coherencia del año.
5. Los Servicios crean el nodo único `Producto` e insertan los enlaces cruzados en la `Multilista`.
6. Los Servicios actualizan el `Hipercubo` sumando 1 a la celda $(g, i, c, a, v)$ para cada coautor.
7. Los Servicios invocan la función RPC remota en Supabase para persistir en una sola transacción: producto, relación producto-grupo y relaciones producto-autor.
8. El servidor PostgreSQL confirma la transacción e incrementa `meta.revision`.
9. El sistema apila la operación en la `Pila` de deshacer y muestra notificación *"Producto registrado con éxito"*.

### Flujos Alternativos y Excepciones
- **A1. Falla de persistencia en Supabase (error de red o rechazo transaccional)**:
  1. El Repositorio REST recibe un código de error o pérdida de conexión.
  2. Los Servicios ejecutan rollback en memoria: desenlazan el nodo de la `Multilista`, restan la frecuencia en el `Hipercubo` y destruyen el nodo.
  3. No se apila nada en la `Pila` de deshacer.
  4. La GUI muestra diálogo modal de error *"No se pudo guardar el producto. Operación cancelada"* conservando el formulario abierto para no perder los datos ingresados.
- **A2. Conflicto de revisión concurrente**:
  1. La llamada RPC remota detecta que `meta.revision` cambió y aborta.
  2. El sistema revierte la memoria y ejecuta el flujo de conflicto [[#CU-07: Resolver Conflicto de Concurrencia por Revisión Remota]].

---

## CU-03: Desactivar o Modificar Entidad con Deshacer
- **Actor Principal**: Usuario / Líder
- **Punto del Taller**: R1, R2, R3, R6, C6
- **Requisitos Relacionados**: [[SPEC#RF-07: Pila de Deshacer Transaccional (Undo)]], [[SPEC#RNF-06: Semántica de Borrado Lógico vs. Físico y Reversibilidad]].
- **Precondiciones**: La entidad (Grupo, Investigador o Producto) existe y se encuentra en estado `activo=true`.
- **Disparador**: El usuario selecciona la entidad y hace clic en "Desactivar" o edita un campo.
- **Resultado Esperado**:
  - Atributo modificado en memoria (ej. `activo=false`).
  - Hipercubo decrementado en los productos afectados.
  - Cambio persistido en Supabase vía REST PATCH.
  - Delta inverso apilado en la Pila de Deshacer.

### Flujo Normal
1. El usuario selecciona un producto y pulsa "Desactivar".
2. La GUI solicita confirmación: *"¿Desea desactivar este producto? Dejará de contabilizarse en las estadísticas"*.
3. El usuario confirma.
4. Los Servicios guardan el estado anterior en el comando inverso (`reactivar`).
5. Los Servicios marcan el producto como `activo=false` y descuentan sus métricas del `Hipercubo`.
6. Los Servicios envían la actualización a Supabase (`PATCH /rest/v1/productos?id=eq.X`).
7. Supabase confirma la actualización y actualiza `meta.revision`.
8. Los Servicios apilan el comando inverso en la `Pila` de deshacer.
9. La GUI refresca la tabla y habilita el botón "Deshacer" en la barra de herramientas.

### Flujo de Deshacer (Undo)
1. El usuario presiona Ctrl+Z o pulsa "Deshacer".
2. Los Servicios desapilan el comando inverso superior de la `Pila`.
3. Se ejecuta la acción inversa: se restablece `activo=true` en el producto y se reincrementa el `Hipercubo`.
4. Se envía la sincronización a Supabase vía REST.
5. La GUI refresca el panel y las tablas.

---

## CU-04: Eliminar Físicamente con Validación de Cascada
- **Actor Principal**: Administrador del Sistema
- **Punto del Taller**: R1, R2, R3, C6
- **Requisitos Relacionados**: [[SPEC#RF-02: Gestión de Grupos de Investigación]], [[SPEC#RF-03: Gestión de Investigadores]], [[SPEC#RF-04: Gestión y Clasificación de Productos de Investigación]], [[SPEC#RNF-06: Semántica de Borrado Lógico vs. Físico y Reversibilidad]].
- **Precondiciones**: La entidad a eliminar existe en el sistema.
- **Disparador**: El usuario selecciona "Eliminar Definitivamente".
- **Resultado Esperado**:
  - Verificación de dependencias y reglas en cascada.
  - Remoción física del nodo en las estructuras en memoria y en la base de datos.
  - Registro de reconstrucción apilado en la Pila.

### Flujo Normal
1. El usuario solicita eliminar un Investigador.
2. El sistema analiza sus dependencias:
   - Si es el único Líder activo de un Grupo: el sistema **bloquea** la eliminación e informa: *"No se puede eliminar al investigador porque es el único Líder activo del grupo X. Asigne otro líder primero"*.
   - Si tiene productos con coautores: el sistema informa: *"El investigador es coautor de N productos. Al eliminarlo, se retirará su autoría pero los productos se conservarán en sus respectivos grupos"*.
3. El usuario confirma la eliminación.
4. Los Servicios remueven al investigador de la `ListaDoble` y retiran sus punteros de la `Multilista`.
5. Los Servicios ejecutan el `DELETE` en Supabase con integridad referencial controlada.
6. La operación inversa (recrear investigador con sus vínculos) se apila en la `Pila`.
7. La GUI actualiza la vista.

---

## CU-05: Consultar Estadísticas Multidimensionales en el Hipercubo
- **Actor Principal**: Directivo de Investigación / Analista
- **Punto del Taller**: R8, R9, R10, C3
- **Requisitos Relacionados**: [[SPEC#RF-09: Modelo de Hipercubo Multidimensional de Métricas]], [[SPEC#RF-10: Cálculo Estadístico y Agregaciones en Memoria]], [[SPEC#RF-11: Interfaz Gráfica de Usuario (GUI) y Vistas Estadísticas]], [[SPEC#RNF-03: Confinamiento Estadístico al Hipercubo]].
- **Precondiciones**: El Hipercubo contiene las frecuencias de los productos activos cargados.
- **Disparador**: El usuario ingresa a la pestaña "Estadísticas" o selecciona filtros en el Panel.
- **Resultado Esperado**:
  - Totales y distribuciones calculados en < 50 ms mediante algoritmos en memoria.
  - Cero consultas SQL emitidas a la red.
  - Renderizado de gráficos de barras y tortas en español.

### Flujo Normal
1. El usuario selecciona en la interfaz: Grupo = "Todos", Categoría = "GNC", Rango de Años = "2019-2024".
2. La GUI invoca al Servicio de Estadísticas con los criterios de filtrado.
3. El Servicio aplica una operación de `Subcubo` sobre el Hipercubo para aislar la ventana temporal y la categoría seleccionada.
4. El Servicio ejecuta `Roll-up` sumando a lo largo de las dimensiones de Investigador y Validación para obtener la serie anual agregada.
5. El Servicio retorna la estructura de datos con los totales anuales a la GUI.
6. La GUI dibuja el gráfico de barras temporales y la tabla resumen.

---

## CU-06: Procesar Lote de Importación desde Cola FIFO
- **Actor Principal**: Administrador del Sistema
- **Punto del Taller**: R7, R12
- **Requisitos Relacionados**: [[SPEC#RF-08: Cola FIFO de Importación y Procesamiento por Lotes]], [[SPEC#RF-13: Extracción e Importación de Fuentes Externas]].
- **Precondiciones**: URLs válidas de SCIENTI o archivos CSV disponibles en disco local.
- **Disparador**: El usuario añade 3 URLs o archivos a la lista de importación y pulsa "Iniciar Procesamiento".
- **Resultado Esperado**:
  - Tareas encoladas en la `Cola` FIFO hecha a mano.
  - Procesamiento secuencial respetando rate-limiting (1 s) y persistencia.
  - Resumen final de entidades importadas y errores registrados.

### Flujo Normal
1. El usuario encola dos URLs de GrupLAC y un archivo CSV.
2. Cada elemento se inserta al final de la `Cola` con estado `Pendiente`.
3. El hilo trabajador de importación desencola la primera tarea y marca su estado en `Procesando`.
4. El extractor descarga el HTML (o lee caché local), analiza el DOM con BeautifulSoup y valida con modelos Pydantic.
5. Los Servicios crean o actualizan las entidades en memoria y las persisten en Supabase.
6. La tarea se marca como `Terminada`.
7. El hilo espera 1 segundo (si fue petición de red) y toma la siguiente tarea de la `Cola`.
8. Al vaciarse la cola, la GUI emite sonido/notificación y actualiza las listas generales.

### Flujos Alternativos y Excepciones
- **A1. Error 404 o estructura corrupta en una fuente**:
  1. El extractor detecta el error y aborta la tarea actual.
  2. La tarea se marca como `Con error` registrando el detalle técnico en la bitácora.
  3. La cola no se interrumpe: el hilo continúa inmediatamente con la siguiente tarea encolada.

---

## CU-07: Resolver Conflicto de Concurrencia por Revisión Remota
- **Actor Principal**: Sistema (Automático) / Usuario
- **Punto del Taller**: R0, R11
- **Requisitos Relacionados**: [[SPEC#RF-01: Control de Concurrencia y Detección de Cambios Remotos]], [[SPEC#RF-12: Persistencia Atómica y Resiliencia REST/RPC]].
- **Precondiciones**: Dos instancias de la aplicación (o Python y C++) están abiertas simultáneamente sobre la misma base de datos.
- **Disparador**: La instancia B intenta guardar un cambio, pero la instancia A escribió previamente e incrementó `meta.revision`.
- **Resultado Esperado**:
  - Escritura de B bloqueada en el servidor.
  - Integridad en memoria de B protegida contra datos desfasados.
  - Notificación no destructiva y recarga limpia opcional.

### Flujo Normal
1. El usuario en la instancia B edita el nombre de un grupo y presiona "Guardar".
2. La capa de Servicios consulta `meta.revision` o envía la petición RPC incluyendo `revision_esperada`.
3. El servidor rechaza la transacción porque `meta.revision` remota (ej. 14) es mayor a la local de B (ej. 13).
4. Los Servicios de B descartan la mutación en memoria para mantener sincronía.
5. La GUI presenta diálogo modal:
   *"La base de datos cambió. Otro usuario o programa ha modificado los datos remotos. Sus cambios no se guardaron para evitar inconsistencias. ¿Desea recargar la base de datos ahora?"*.
6. El usuario selecciona "Recargar".
7. El sistema ejecuta el [[#CU-01: Iniciar Sesión y Cargar Estado del Sistema]], cargando el estado actualizado con la nueva revisión.
