---
tipo: adr
estado: aprobado
creado: 2026-10-25
actualizado: 2026-10-25
relacionado:
  - "[[00-Inicio]]"
  - "[[Arquitectura]]"
  - "[[Modelo-Productos]]"
  - "[[Paridad-Python-Cpp]]"
origen: "Solicitud del propietario: implementar Parcial 2, excluir Word/UML/video y publicar una nueva entrega"
numero: 26
decision: "Catálogo normativo compartido, indicadores en memoria y persistencia local interoperable"
---

# ADR · Indicadores del Parcial 2 y archivos locales

La versión 0.2.0 incorpora los nueve componentes del indicador del parcial.
La fuente numérica es el PDF original del Modelo, secciones 3.5–3.10 y Anexo 1.
Un JSON reproducible conserva 169 categorías; C++ lo incorpora como recurso Qt
y Python lo distribuye como dato del paquete. No se duplican tablas de pesos.

El puntaje individual, el indicador logarítmico por clase y el índice normalizado
son valores distintos. Los máximos locales se identifican como comparación del
catálogo; se admite una referencia externa con procedencia y periodo explícitos.
No se deduce la calidad de un producto de su título ni se presenta una comparación
local como clasificación nacional. El resultado enumera exclusiones.

Las estadísticas descriptivas continúan en el hipercubo. El nuevo servicio de
indicadores proyecta los nodos únicos de producto y los vínculos temporales de la
multilista en memoria, porque las dimensiones históricas del hipercubo no retienen
la categoría de calidad necesaria para este cálculo. No realiza agregaciones SQL
ni altera los conteos descriptivos existentes.

La categoría complementaria se guarda en `productos.detalles`, conservando los
metadatos de extracción y los contratos REST/RPC. No se requiere migración.
Los catálogos locales son instantáneas JSON de datos de dominio sin credenciales;
se validan antes de instalarse y se guardan atómicamente. El usuario decide abrir
un archivo o comenzar vacío y guarda los cambios mediante la acción explícita.

Las tareas de servicio de la GUI se serializan para respetar el catálogo mutable
compartido. Los documentos PDF de C++ se procesan con Poppler incluido en el
portable. La guía vigente y el alcance están en `docs/parcial-2.md`.

Se excluyen Word, UML y video por solicitud del propietario. Los fuentes
académicos con iniciales son entradas del proyecto modular, no archivos autónomos.
