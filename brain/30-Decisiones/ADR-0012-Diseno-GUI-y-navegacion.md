---
tipo: adr
estado: revisado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[_Indice]]"
  - "[[GUI-Diseno-Python]]"
  - "[[GUI-paridad]]"
  - "[[ADR-0016-Alcance-de-pantallas-y-datos-del-boceto]]"
  - "[[ADR-0017-Tecnologia-de-interfaz-Qt-Widgets]]"
  - "[[SPEC]]"
origen: "Boceto de referencia del usuario (brain/_adjuntos/ref-*) — rediseño de la interfaz de Python, 2026-10-03"
---

# ADR-0012 · Diseño visual institucional y navegación por barra superior

## Contexto
La interfaz necesita presentar estadísticas de investigación de forma agradable y permitir pasar rápido entre la visión de conjunto (institución o grupo) y el detalle (investigador, producto). El usuario aportó un boceto con una barra superior de pestañas, tarjetas con gráficos y fichas laterales. La primera versión implementada no seguía ese boceto y la documentación describía otras estructuras distintas, de modo que había más de un diseño en conflicto.

## Opciones consideradas
1. **Cuatro zonas con árbol de navegación y paneles divisibles (`QSplitter`)**: densa y flexible, pero exige entender un árbol y arrastrar divisores; no corresponde al boceto. Descartada.
2. **Barra lateral con una lista de nueve pantallas**: es lo que se había implementado; mezcla tareas de uso diario (consultar) con tareas técnicas (conectar, verificación cruzada) al mismo nivel. Descartada.
3. **Barra superior con pestañas, contenido en tarjetas y fichas laterales de detalle, más un pie institucional**: sigue el boceto, concentra la navegación en un solo lugar y deja la pantalla libre para los datos. **Elegida.**

## Decisión
Se adopta la opción 3, descrita al detalle en [[GUI-Diseno-Python]]:

- Barra superior con degradado, marca de PEA-i, **siete pestañas** (Inicio, Investigadores, Grupos, Productos, Análisis de redes, Importar, Configuración), Deshacer, avatar, «Cerrar sesión» y «Acerca de».
- Filete institucional de la UPC bajo la barra y pie con identidad de la UPC y estado de conexión.
- Directorios con **tabla + ficha lateral**; la gestión de datos (crear, editar, activar/desactivar, eliminar) está dentro de cada directorio.
- Un único **filtro de años** compartido entre pantallas.
- Terminología en español correcto y colores, tipografías y espaciados definidos como tokens.

## Consecuencias
- **Positivas**: navegación clara y reconocible; menos pantallas; identidad visual coherente; el diseño se puede verificar contra imágenes.
- **Costos**: hay que migrar las nueve pantallas existentes y actualizar las pruebas de interfaz, que dependían de la estructura anterior.
- **Riesgos**: el boceto incluye elementos sin respaldo en los datos; se resuelven en [[ADR-0016-Alcance-de-pantallas-y-datos-del-boceto]].
