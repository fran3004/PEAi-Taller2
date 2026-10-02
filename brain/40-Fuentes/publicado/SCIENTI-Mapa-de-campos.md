---
tipo: fuente
estado: aprobado
creado: 2026-10-02
actualizado: 2026-10-02
relacionado:
  - "[[SCIENTI-GrupLAC]]"
  - "[[SCIENTI-CvLAC]]"
  - "[[Modelo]]"
  - "[[Modelo-Grupos]]"
  - "[[Modelo-Investigadores]]"
  - "[[Modelo-Productos]]"
origen: "Inspección DOM de páginas oficiales ScienTI (GrupLAC y CvLAC)"
---

# Mapa de Campos SCIENTI · GrupLAC y CvLAC

Documento técnico de especificación de mapeo entre el HTML de los aplicativos ScienTI de Minciencias, los modelos de validación Pydantic (`tools/fuentes/modelos_scienti.py`) y las variables de dominio del Modelo 2024 ([[Modelo]]).

---

## 1. Mapeo de Entidad Grupo (GrupLAC)

| Fuente | Selector / Origen DOM | Texto Visible | Modelo Pydantic | Variable del Modelo | Requerido | Observaciones |
|---|---|---|---|---|:---:|---|
| **GrupLAC** | URL query parameter `?nro=...` | `00000000002099` | `GrupoGrupLAC.codigo_gruplac` | `Grupo.codigo_gruplac` | **Sí** | Identificador único. Minciencias exige padding a 14 dígitos (10 ceros). |
| **GrupLAC** | `table:contains("Datos básicos") tr:contains("Año y mes") td:nth-child(2)` | `2001 - 2` | `GrupoGrupLAC.ano_mes_formacion` | `Grupo.ano_fundacion` | **Sí** | Se extrae el año (ej. 2001) para la edad del grupo. |
| **GrupLAC** | `table:contains("Datos básicos") tr:contains("Departamento - Ciudad") td:nth-child(2)` | `CESAR - VALLEDUPAR` | `GrupoGrupLAC.departamento_ciudad` | `Grupo.ubicacion` | No | Filtro geográfico. |
| **GrupLAC** | `table:contains("Datos básicos") tr:contains("Líder") td:nth-child(2)` | `john jairo PATIÑO VANEGAS` | `GrupoGrupLAC.lider` | `Grupo.lider_id` | **Sí** | Nombre del líder. Requiere resolución hacia la entidad `Investigador`. |
| **GrupLAC** | `table:contains("Datos básicos") tr:contains("Clasificación") td:nth-child(2)` | `C con vigencia...` | `GrupoGrupLAC.clasificacion` | `Grupo.categoria` | **Sí** | Categoría oficial: A1, A, B, C o Reconocido. |
| **GrupLAC** | `table:contains("Datos básicos") tr:contains("Área de conocimiento") td:nth-child(2)` | `Ingeniería y Tecnología -- ...` | `GrupoGrupLAC.area_conocimiento` | `Grupo.gran_area_ocde` | **Sí** | Se mapea a la jerarquía de 6 Grandes Áreas OCDE ([[Modelo-Areas-OCDE]]). |
| **GrupLAC** | `table:contains("Datos básicos") tr:contains("E-mail") td:nth-child(2)` | `gisico@unicesar.edu.co` | `GrupoGrupLAC.email` | `Grupo.email` | No | Correo institucional de contacto. |
| **GrupLAC** | `table:contains("Instituciones") tr td` | `Universidad Popular del Cesar - UPC` | `InstitucionAval.nombre` | `Grupo.institucion_aval` | **Sí** | Acreditación de vinculación institucional. |
| **GrupLAC** | `table:contains("Integrantes del grupo") tr td` | Nombre, Vinculación, Horas, Fechas | `IntegranteGrupo` | `Integrante` | **Sí** | Vínculo bidireccional en la estructura `Multilista`. |
| **GrupLAC** | `table:contains("Líneas de investigación") tr td` | `Ingeniería de Software...` | `LineaInvestigacion.nombre` | `Grupo.lineas_investigacion` | No | Caracterización temática del grupo. |

---

## 2. Mapeo de Entidad Investigador (CvLAC)

| Fuente | Selector / Origen DOM | Texto Visible | Modelo Pydantic | Variable del Modelo | Requerido | Observaciones |
|---|---|---|---|---|:---:|---|
| **CvLAC** | URL query parameter `?cod_rh=...` | `0000494917` | `InvestigadorCvLAC.codigo_rh` | `Investigador.codigo_cvlac` | **Sí** | Identificador de hoja de vida en ScienTI. |
| **CvLAC** | `table:first tr:contains("Nombre") td:nth-child(2)` | `Adith Bismarck Pérez Orozco` | `InvestigadorCvLAC.nombre_completo` | `Investigador.nombre_completo` | **Sí** | Nombres oficiales del investigador. |
| **CvLAC** | `table:first tr:contains("Nombre en citaciones") td:nth-child(2)` | `PÉREZ OROZCO, ADITH BISMARCK` | `InvestigadorCvLAC.nombre_citaciones` | `Investigador.nombre_citaciones` | No | Útil para desambiguación en coautorías de artículos. |
| **CvLAC** | `table:first tr:contains("Nacionalidad") td:nth-child(2)` | `Colombiana` | `InvestigadorCvLAC.nacionalidad` | `Investigador.nacionalidad` | No | Atributo demográfico. |
| **CvLAC** | `table:first tr:contains("Categoría") td:nth-child(2)` | `Investigador Asociado (I)...` | `InvestigadorCvLAC.categoria_declarada` | `Investigador.categoria` | **Sí** | Categoría Minciencias: Emérito, Sénior, Asociado, Junior. |
| **CvLAC** | `table:first tr:contains("Par evaluador")` | Texto presente | `InvestigadorCvLAC.par_evaluador` | `Investigador.es_par_evaluador` | No | Booleano que indica acreditación como par evaluador. |
| **CvLAC** | `table:contains("Formación Académica") tr` | Nivel, Título, Institución, Año | `FormacionAcademica` | `Investigador.nivel_formacion` | **Sí** | Se toma el máximo nivel alcanzado (Doctorado, Maestría, Pregrado). |
| **CvLAC** | `table:contains("Áreas de actuación") tr td` | `Ciencias Naturales -- Computación...` | `InvestigadorCvLAC.areas_actuacion` | `Investigador.areas_actuacion` | No | Áreas de especialidad según OCDE. |

---

## 3. Mapeo de Entidad Producto (GrupLAC y CvLAC)

| Fuente | Selector / Origen DOM | Texto Visible | Modelo Pydantic | Variable del Modelo | Requerido | Observaciones |
|---|---|---|---|---|:---:|---|
| **Ambos** | Tabla de sección específica (`Artículos publicados`, `Softwares`, etc.) | Encabezado de la tabla | `ProductoBibliografico.tipo` / `ProductoSoftware.tipo` | `Producto.categoria_principal` | **Sí** | Mapea a `GNC`, `DTI`, `ASC_DPC` o `FRH` según [[Modelo-Productos]]. |
| **Ambos** | Texto de la celda de producto | `1.- Nombre del artículo... En: Revista...` | `ProductoBibliografico.titulo` | `Producto.titulo` | **Sí** | Título normalizado del producto. |
| **Ambos** | Expresión regular sobre celda `\b(19\d{2}\|20\d{2})\b` | `2021`, `2023`, etc. | `ProductoBibliografico.ano` | `Producto.ano` | **Sí** | Año de publicación para cálculo en la ventana de observación. |
| **Ambos** | Patrón `DOI:` o `ISSN:` o `ISBN:` | `DOI: 10.1016/...` | `ProductoBibliografico.doi_o_isbn` | `Producto.identificador` | No | Clave para evitar duplicados en la `Multilista`. |
| **GrupLAC** | Icono o marca de aval institucional | Icono de certificación en tabla | `ProductoBibliografico.categoria_declarada` | `Producto.cumple_calidad` | No | Acreditación de cumplimiento de requisitos de calidad en convocatoria. |

---

## 4. Reglas de Desambiguación y Multilista

1. **Unicidad de Nodos de Producto**:
   - Cuando un artículo o software listado en el CvLAC de un investigador coincide con el listado en el GrupLAC de su grupo, el sistema genera **un único nodo en memoria**.
   - Se enlazan los punteros: `Grupo -> Producto` y `Investigador -> Producto`.
2. **Normalización de Texto**:
   - Todo texto se normaliza a forma canónica Unicode NFC, eliminando espacios duplicados y caracteres de control HTML.
