---
tipo: adr
estado: revisado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[_Indice]]"
  - "[[GUI-Diseno-Python]]"
  - "[[GUI-paridad]]"
  - "[[ADR-0012-Diseno-GUI-y-navegacion]]"
  - "[[Modelo-de-dominio]]"
  - "[[SPEC]]"
origen: "Contraste entre el boceto de referencia y el enunciado del Taller 2; pregunta abierta C-06 de AUDITORIA-DISENO-PEAI, 2026-10-03"
---

# ADR-0016 · Alcance de pantallas y datos que se toman del boceto

## Contexto
El boceto muestra nueve pestañas (incluidas Semilleros, Proyectos y Centros) y cifras como H-Index, ORCID, semilleristas o convocatorias. PEA-i, según el enunciado del taller y el [[Modelo-de-dominio]], gestiona **grupos, investigadores, integrantes, planes y productos**, filtra por años, ofrece operaciones de datos, importa desde SCIENTI/CSV/PDF y presenta estadísticas por grupo, investigador y producto. Además el pie del boceto contiene logos y texto legal de un tercero (Let Me Know / SIGIIP).

## Opciones consideradas
1. **Copiar las nueve pestañas y rellenar las que no tienen datos con «Próximamente»**: parece completo, pero muestra pantallas vacías y datos inventados. Descartada.
2. **Mostrar solo lo que PEA-i tiene y reemplazar cada dato inexistente por uno equivalente real**. **Elegida.**
3. **Ampliar el dominio con semilleros, centros, H-Index y ORCID**: sale del enunciado y del Modelo, y cambia el esquema compartido con C++. Descartada.

## Decisión
- **Pestañas**: Inicio, Investigadores, Grupos, Productos, Análisis de redes, Importar, Configuración. Además «Acerca de» y «Cerrar sesión» en la barra superior.
- **Semilleros y Centros**: fuera de alcance. **Proyectos**: la entidad existe pero no tiene servicio ni vista; queda como ampliación opcional posterior.
- **Reemplazos de datos**: se aplica la tabla de la sección 7 de [[GUI-Diseno-Python]] (por ejemplo, H-Index → «Promedio por integrante» o «Años con producción»; ORCID → «Código CvLAC»; gráfico de proyectos → «Producción por año y tipología»).
- **Pie**: identidad de la Universidad Popular del Cesar y estado de conexión. Los logos y el texto legal de terceros del boceto **no** se reproducen.
- **Nombre**: se usa el nombre oficial del taller, «Programa Estadístico de Análisis de Investigación», en una constante única (`NOMBRE_COMPLETO`).
- **Servicios nuevos necesarios** (los crea el rediseño de Python y quedan como deuda de paridad en [[GUI-paridad]]): `serie_anual_por_categoria`, `red_coautoria` y **`actualizar_producto`**. Este último cubre un requisito del taller (modificar cualquier dato de un producto, incluidas categoría y validación) que hoy no tiene servicio.

## Consecuencias
- **Positivas**: la interfaz es honesta con los datos; ninguna pantalla vacía; el diseño cumple el enunciado.
- **Costos**: tres servicios nuevos y sus pruebas; el boceto se adapta, no se copia.
- **Riesgos**: si el usuario quiere Proyectos, hay que añadir un servicio de lectura (`tabla_proyectos`) y una pestaña; el diseño lo admite sin cambios de estructura.
