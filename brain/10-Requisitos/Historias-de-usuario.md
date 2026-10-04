---
tipo: historia-de-usuario
estado: aprobado
creado: 2026-10-02
actualizado: 2026-10-02
relacionado:
  - "[[SPEC]]"
  - "[[Casos-de-uso]]"
  - "[[00-Inicio]]"
origen: "Roles del sistema PEA-i (Investigador, Líder de Grupo, Directivo de Investigación, Administrador)"
---

# Historias de Usuario (HU) · PEA-i

Este documento define las Historias de Usuario que describen las capacidades del sistema desde la perspectiva de los diferentes actores involucrados en la gestión y análisis de investigación.

---

## HU-01: Inicialización y Sincronización Segura con Supabase
- **Identificador**: HU-01
- **Rol**: Administrador del Sistema
- **Narrativa**: **Como** administrador del sistema, **quiero** iniciar la aplicación conectándome a Supabase mediante HTTPS para cargar los datos en las estructuras en memoria de forma segura y verificar la revisión remota.
- **Criterios de Aceptación**:
  - [ ] El sistema utiliza exclusivamente la clave pública (*publishable key*) y HTTPS sin exponer el puerto 5432.
  - [ ] Al conectar con éxito, el sistema descarga las entidades maestras (Grupos, Investigadores, Productos e Integrantes) y las puebla en la `ListaDoble` y la `Multilista`.
  - [ ] Se registra localmente el valor actual de `meta.revision` para control de concurrencia.
  - [ ] Si no hay conectividad a internet, el sistema bloquea los módulos de escritura y notifica con claridad el estado de desconexión sin simular datos falsos.
- **Requisitos Relacionados**: [[SPEC#RF-01: Control de Concurrencia y Detección de Cambios Remotos]], [[SPEC#RF-12: Persistencia Atómica y Resiliencia REST/RPC]], [[SPEC#RNF-04: Seguridad, Autenticación y Conexión HTTPS]].

---

## HU-02: Registro y Mantenimiento de Grupo de Investigación
- **Identificador**: HU-02
- **Rol**: Líder de Grupo / Administrador
- **Narrativa**: **Como** líder de grupo, **quiero** registrar o actualizar los datos institucionales de mi grupo de investigación (código GrupLAC, nombre, fecha de fundación, área OCDE, categoría), **para** mantener actualizado el perfil formal del colectivo.
- **Criterios de Aceptación**:
  - [ ] No permite registrar códigos de GrupLAC duplicados.
  - [ ] Permite seleccionar una de las 6 Grandes Áreas OCDE y sus 42 subáreas normalizadas.
  - [ ] Al guardar, el grupo se inserta en la `ListaDoble` de grupos en memoria y se persiste vía REST en Supabase.
  - [ ] La operación de registro se registra en la `Pila` de deshacer.
- **Requisitos Relacionados**: [[SPEC#RF-02: Gestión de Grupos de Investigación]], [[SPEC#RF-06: Gestión de Colecciones mediante Lista Doblemente Enlazada Manual]], [[SPEC#RF-07: Pila de Deshacer Transaccional (Undo)]].

---

## HU-03: Consulta y Edición de Perfil de Investigador
- **Identificador**: HU-03
- **Rol**: Investigador
- **Narrativa**: **Como** investigador, **quiero** consultar y modificar mi perfil académico (código RH, nombre, formación máxima, categoría Minciencias), **para** que mis credenciales y clasificación se reflejen fielmente en los reportes.
- **Criterios de Aceptación**:
  - [ ] La categoría seleccionable se restringe estrictamente a: Emérito, Senior, Asociado, Junior o Sin categoría / Vinculado.
  - [ ] Al consultar un investigador, el sistema lista los grupos en los que participa y los productos donde es autor.
  - [ ] La entidad se aloja en la `ListaDoble` de investigadores sin usar contenedores nativos como almacenamiento maestro.
- **Requisitos Relacionados**: [[SPEC#RF-03: Gestión de Investigadores]], [[SPEC#RF-06: Gestión de Colecciones mediante Lista Doblemente Enlazada Manual]], [[SPEC#RNF-01: Prohibición de Contenedores Nativos como Almacenamiento Principal]].

---

## HU-04: Vinculación de Integrantes al Grupo de Investigación
- **Identificador**: HU-04
- **Rol**: Líder de Grupo
- **Narrativa**: **Como** líder de grupo, **quiero** vincular investigadores y estudiantes a mi grupo asignándoles un rol institucional y fechas de inicio y fin, **para** formalizar la composición del equipo de trabajo.
- **Criterios de Aceptación**:
  - [ ] Solo se pueden vincular investigadores que ya existan previamente en la `ListaDoble` de investigadores.
  - [ ] El rol asignado debe ser Líder, Investigador o Estudiante.
  - [ ] Debe existir al menos un integrante con rol Líder activo en todo momento.
  - [ ] La vinculación se persiste atómicamente y actualiza la vista de integrantes del grupo.
- **Requisitos Relacionados**: [[SPEC#RF-02: Gestión de Grupos de Investigación]], [[SPEC#RF-03: Gestión de Investigadores]], [[SPEC#RF-12: Persistencia Atómica y Resiliencia REST/RPC]].

---

## HU-05: Registro de Producto con Coautoría Compartida (Multilista)
- **Identificador**: HU-05
- **Rol**: Investigador / Líder de Grupo
- **Narrativa**: **Como** autor de una publicación, **quiero** registrar un nuevo producto de investigación seleccionando su tipología Minciencias y asignando múltiples coautores e integrantes de un grupo, **para** que el producto figure en el grupo y en la hoja de vida de cada coautor sin duplicar datos.
- **Criterios de Aceptación**:
  - [ ] El producto se crea como un único nodo en la memoria del sistema.
  - [ ] El nodo queda enlazado a la lista de productos del grupo y a las listas de productos de cada autor seleccionado.
  - [ ] La clasificación de tipo mayor se restringe a GNC, DTI, ASC y FRH.
  - [ ] La persistencia multi-tabla (producto + vínculos de autoría + vínculos de grupo) se realiza mediante un RPC atómico en PostgreSQL.
- **Requisitos Relacionados**: [[SPEC#RF-04: Gestión y Clasificación de Productos de Investigación]], [[SPEC#RF-05: Multilista Bidireccional de Coautoría y Pertenencia]], [[SPEC#RF-12: Persistencia Atómica y Resiliencia REST/RPC]].

---

## HU-06: Visualización del Panel de Control con Métricas del Hipercubo
- **Identificador**: HU-06
- **Rol**: Directivo de Investigación / Decano
- **Narrativa**: **Como** directivo de investigación, **quiero** abrir la pestaña Inicio para visualizar las métricas consolidadas institucionales (total de grupos, investigadores activos, desglose GNC/DTI/ASC/FRH y gráficos temporales), **para** evaluar el rendimiento científico de la institución.
- **Criterios de Aceptación**:
  - [ ] Todos los indicadores numéricos y gráficos se calculan directamente desde el `Hipercubo` en memoria mediante operaciones de `Roll-up`.
  - [ ] No se emiten consultas SQL agregadas (`GROUP BY`) a Supabase para armar el panel.
  - [ ] Todos los textos y etiquetas están en español correcto ("Panel", "Resumen", "Productos").
  - [ ] Los gráficos se renderizan fluidamente en PySide6 con `QPainter` ([[ADR-0017-Tecnologia-de-interfaz-Qt-Widgets]]); la interfaz de C++ se definirá aparte.
- **Requisitos Relacionados**: [[SPEC#RF-09: Modelo de Hipercubo Multidimensional de Métricas]], [[SPEC#RF-10: Cálculo Estadístico y Agregaciones en Memoria]], [[SPEC#RF-11: Interfaz Gráfica de Usuario (GUI) y Vistas Estadísticas]], [[SPEC#RNF-03: Confinamiento Estadístico al Hipercubo]].

---

## HU-07: Análisis Multidimensional con Filtros Temporales y de Categoría
- **Identificador**: HU-07
- **Rol**: Analista de Investigación
- **Narrativa**: **Como** analista de investigación, **quiero** aplicar filtros por ventana de años (ej. últimos 5 años) y por tipología específica a un grupo de investigación, **para** estudiar su evolución frente a los requerimientos de la convocatoria Minciencias.
- **Criterios de Aceptación**:
  - [ ] El filtrado ejecuta operaciones de `Rebanada` (*slice*) y `Subcubo` (*dice*) sobre el Hipercubo.
  - [ ] La actualización de la vista y de los gráficos es reactiva e instantánea (< 50 ms).
  - [ ] Los productos con `activo=false` se excluyen automáticamente de los cálculos.
- **Requisitos Relacionados**: [[SPEC#RF-09: Modelo de Hipercubo Multidimensional de Métricas]], [[SPEC#RF-10: Cálculo Estadístico y Agregaciones en Memoria]].

---

## HU-08: Deshacer Acciones Involuntarias con la Pila de Deshacer
- **Identificador**: HU-08
- **Rol**: Usuario General
- **Narrativa**: **Como** usuario del sistema, **quiero** presionar "Deshacer" (Ctrl+Z) tras haber desactivado o modificado accidentalmente una entidad, **para** restituir su estado anterior de manera inmediata sin perder información.
- **Criterios de Aceptación**:
  - [ ] Cada mutación en el sistema apila el estado inverso en la `Pila`.
  - [ ] Al accionar "Deshacer", se desapila la operación inversa, se aplica a las estructuras de datos en memoria y se sincroniza con la base de datos remota.
  - [ ] Si la pila está vacía, el botón "Deshacer" permanece deshabilitado.
- **Requisitos Relacionados**: [[SPEC#RF-07: Pila de Deshacer Transaccional (Undo)]], [[SPEC#RNF-06: Semántica de Borrado Lógico vs. Físico y Reversibilidad]].

---

## HU-09: Procesamiento por Lotes de Importaciones desde Cola FIFO
- **Identificador**: HU-09
- **Rol**: Administrador del Sistema
- **Narrativa**: **Como** administrador, **quiero** encolar múltiples URLs de GrupLAC/CvLAC o archivos CSV para su extracción e importación desatendida, **para** poblar la base de datos institucional sin congelar la interfaz.
- **Criterios de Aceptación**:
  - [ ] Las solicitudes se agregan a una estructura propia de `Cola` (FIFO).
  - [ ] Cada tarea muestra su estado en tiempo real: `Pendiente`, `Procesando`, `Terminada` o `Con error`.
  - [ ] El fallo de una tarea de red no bloquea el procesamiento de las tareas subsecuentes.
  - [ ] El scraping respeta la pausa de 1 segundo entre peticiones y caché local.
- **Requisitos Relacionados**: [[SPEC#RF-08: Cola FIFO de Importación y Procesamiento por Lotes]], [[SPEC#RF-13: Extracción e Importación de Fuentes Externas]].

---

## HU-10: Detección Oportuna de Conflictos de Concurrencia
- **Identificador**: HU-10
- **Rol**: Usuario General
- **Narrativa**: **Como** usuario en una sesión concurrente, **quiero** que el sistema me advierta oportunamente si otro usuario modificó la base de datos desde otra instancia, **para** evitar sobreescribir datos ajenos y mantener la integridad.
- **Criterios de Aceptación**:
  - [ ] Antes de escribir, el sistema valida que el `meta.revision` local coincida con el de Supabase.
  - [ ] Si el valor remoto es mayor, se cancela la escritura, se muestra el diálogo modal *"La base de datos cambió"* y se ofrece la opción *"Recargar datos"*.
  - [ ] Al recargar, las estructuras en memoria se refrescan con el estado actual remoto sin inconsistencias.
- **Requisitos Relacionados**: [[SPEC#RF-01: Control de Concurrencia y Detección de Cambios Remotos]], [[SPEC#RF-12: Persistencia Atómica y Resiliencia REST/RPC]].
