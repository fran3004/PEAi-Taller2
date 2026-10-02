---
tipo: fuente
estado: aprobado
creado: 2026-10-02
actualizado: 2026-10-02
relacionado:
  - "[[Modelo-2024-indice]]"
  - "[[Modelo-2024-original]]"
  - "[[Modelo-Productos]]"
  - "[[Modelo]]"
origen: "docs/entrada/Modelo-2024.original.pdf (Anexo 4, pp. 202-239)"
---

# Modelo Minciencias 2024 · Guías de Revisión y Validación Documental

Documento de referencia: **M601PR04G01 (Versión 02)**.  
Citas directas al documento original: [[Modelo-2024-original]].

---

## 1. Alcance de las Guías de Revisión (Anexo 4)

El Anexo 4 contiene los lineamientos técnicos y documentales que utiliza Minciencias para validar la veracidad y calidad de los productos ingresados en los aplicativos CvLAC y GrupLAC ([[Modelo-2024-original#Página 202]]–[[Modelo-2024-original#Página 239]]).

Para el proyecto **PEA-i**, estas guías definen las reglas de saneamiento que el módulo extractor/analizador (`fuentes-scienti`) debe aplicar al parsear páginas HTML de CvLAC y GrupLAC, asegurando que ningún producto con datos ficticios o incompletos contamine el repositorio o las estructuras.

---

## 2. Criterios de Verificación por Tipología

### 2.1 Artículos en Revistas Especializadas ([[Modelo-2024-original#Página 202]]–[[Modelo-2024-original#Página 204]])
- Debe verificarse:
  - Nombre exacto de la revista e ISSN (impreso o electrónico).
  - Título del artículo, autores coincidentes con integrantes del grupo, año, volumen, fascículo, páginas inicial y final.
  - Enlace web y DOI válido para artículos electrónicos.
  - Para cuartiles A1, A2, B, C: cotejo con el histórico oficial de Publindex, WoS (JCR) o Scopus (SJR).

### 2.2 Libros y Capítulos de Investigación ([[Modelo-2024-original#Página 205]]–[[Modelo-2024-original#Página 220]])
- Verificación de tipología:
  - ISBN válido registrado en la Cámara del Libro correspondiente.
  - Certificación de evaluación por al menos dos pares ciegos externos independientes.
  - Créditos institucionales del grupo y constancia de filiación institucional de los autores.
  - Diferenciación estricta entre libro de investigación, libro de texto o manual pedagógico y memoria de evento.

### 2.3 Patentes y Modelos de Utilidad ([[Modelo-2024-original#Página 221]]–[[Modelo-2024-original#Página 223]])
- Número de solicitud oficial radicado ante la Superintendencia de Industria y Comercio (SIC) o tratado PCT internacional.
- Para estado "Concedida": Resolución oficial de concesión emitida por la oficina nacional o internacional competente.
- Fecha de concesión dentro de la ventana de 10 años.

### 2.4 Software y Prototipos Tecnológicos ([[Modelo-2024-original#Página 227]]–[[Modelo-2024-original#Página 230]])
- Número de registro de soporte lógico ante la Dirección Nacional de Derecho de Autor (DNDA).
- Certificación emitida por entidad externa (usuario final o empresa beneficiaria) que constate la implementación y operación real del aplicativo o prototipo.

### 2.5 Trabajos de Grado y Tesis de Posgrado ([[Modelo-2024-original#Página 235]]–[[Modelo-2024-original#Página 237]])
- Acta formal de sustentación aprobada emitida por la secretaría académica de la institución educativa.
- Nombre del estudiante graduado y coincidencia del tutor/director con el investigador evaluado.
- Copia digital alojada en el repositorio institucional institucional de la universidad (ej. repositorio UPC).

---

## 3. Impacto en la Normalización de Datos en PEA-i

1. **Validador Pydantic en `fuentes-scienti`**:
   - Campos obligatorios mínimos derivados de las guías de existencia (título, año, identificador).
   - Manejo de anomalías: Si un producto no presenta año o identificador básico, se marca como `cumple_existencia = False`.
2. **Auditoría de Integridad**:
   - Los datos descargados se cotejan contra los fixtures y el oráculo `esperado.json` sin alterar los campos ni fabricar valores ausentes.
