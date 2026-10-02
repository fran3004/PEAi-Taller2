---
tipo: informe-de-extraccion
estado: aprobado
creado: 2026-10-02
actualizado: 2026-10-02
relacionado:
  - "[[SCIENTI-GrupLAC]]"
  - "[[SCIENTI-CvLAC]]"
  - "[[SCIENTI-Mapa-de-campos]]"
  - "[[00-Inicio]]"
origen: "Descargas oficiales SCIENTI en datos/cache/"
---

# Informe de Extracción y Calidad · Fuentes SCIENTI (GrupLAC y CvLAC)

Informe técnico de auditoría y extracción de las fuentes provistas por Minciencias para el proyecto **PEA-i**.

---

## 1. Fuentes Oficiales

| Fuente | URL Oficial | Fecha / Hora (UTC) | Código HTTP | Codificación | Longitud (Bytes) | SHA256 |
|---|---|:---:|:---:|:---:|:---:|---|
| **GrupLAC (Literal)** | `...visualizagr.jsp?nro=0000000002099` | 2026-10-02T21:47:29Z | 200 | ISO-8859-1 | 20,934 | `69b5e3001b1bf9921859e0ef368ee39ae95c2ffec9f1f992ba56696d3193f37c` |
| **GrupLAC (Canónico)** | `...visualizagr.jsp?nro=00000000002099` | 2026-10-02T21:49:09Z | 200 | ISO-8859-1 | 625,613 | `a8bc656b82200bbd504e61322daa90efcdc574b0720641cd46e576759522236b` |
| **CvLAC** | `...generarCurriculoCv.do?cod_rh=0000494917` | 2026-10-02T21:47:32Z | 200 | ISO-8859-1 | 450,831 | `cb31edf9ead8444366726db5fb3ffbbec289d3f6c9af6d1a75696f5c3c2df828` |

---

## 2. Hallazgo Crítico en la URL de GrupLAC

Al consultar la URL literal suministrada (`?nro=0000000002099`, con 9 ceros):
- El servidor JSP de Minciencias responde HTTP 200 pero genera una página esqueleto vacía (20,934 bytes) con 83 tablas que carecen de filas de datos.
- **Causa técnica**: La base de datos de Minciencias almacena los códigos numéricos de grupo con relleno de ceros a 14 dígitos (`00000000002099`, 10 ceros). Al consultar con el formato canónico de 14 dígitos, se recupera el grupo oficial completo: **GISICO (Universidad Popular del Cesar)** con 625,613 bytes y miles de registros.
- **Acción implementada**: Se capturaron y preservaron ambas versiones en `datos/cache/` y en los fixtures de prueba (`tests/fixtures/scienti/`) para garantizar total transparencia y evitar fallas en escenarios con padding variable.

---

## 3. Resultado de Extracción por Fuente

### 3.1 GrupLAC (Grupo GISICO - Universidad Popular del Cesar)
- **Secciones encontradas (83 tablas analizadas)**:
  - *Datos básicos*: Año y mes de formación (2001-2), Ciudad (Valledupar, Cesar), Líder, Clasificación (C), Área OCDE (Ingeniería de Sistemas y Comunicaciones), Programa Nacional de TIC.
  - *Instituciones avaladoras*: Universidad Popular del Cesar (UPC).
  - *Integrantes del grupo*: 87 filas de integrantes con nombre, vinculación, horas y rango temporal.
  - *Líneas de investigación*: 8 líneas activas declaradas.
  - *Producción bibliográfica*: 94 artículos publicados, 14 libros, 24 capítulos de libro.
  - *Producción técnica*: 91 softwares registrados, 2 diseños industriales, 3 otros productos tecnológicos.
  - *Formación y apropiación*: 151 trabajos dirigidos/tutorías, 96 comisiones evaluadoras de grado, 85 eventos científicos, 33 proyectos de investigación.
- **Secciones vacías**:
  - Traducciones filológicas, cartas/mapas, regulaciones técnicas, protocolos epidemiológicos, variedades vegetales/animales (no aplican al perfil del grupo de ingeniería de software).

### 3.2 CvLAC (Investigador Asociado - UPC)
- **Secciones encontradas (39 tablas analizadas)**:
  - *Datos generales*: Hoja de vida completa, Par evaluador reconocido, Categoría Minciencias (Investigador Asociado I).
  - *Formación académica*: Doctorat en Informatique (Ecole Centrale París), Pregrado/Maestría.
  - *Áreas de actuación*: Ciencias Naturales (Computación) e Ingeniería Industrial.
  - *Producción de nuevo conocimiento*: 53 artículos científicos, 14 capítulos de libro.
  - *Desarrollo tecnológico*: 19 registros de software, 9 secretos empresariales, 3 empresas de base tecnológica.
  - *Formación*: 99 trabajos de grado dirigidos/tutorías (pregrado y maestría), 83 participaciones como jurado.
  - *Proyectos*: 11 proyectos de I+D formalizados.
- **Secciones vacías**:
  - Patentes de invención, variedades vegetales/animales.

---

## 4. Calidad, Codificación y Privacidad

1. **Codificación de Caracteres**:
   - Ambas páginas fueron emitidas por el servidor en `ISO-8859-1`.
   - Se decodificaron y normalizaron a `UTF-8` en forma canónica NFC para evitar errores en caracteres especiales (tildes, `ñ`, diéresis, símbolos matemáticos).
2. **Protección de Datos Personales**:
   - **Copia Privada**: Preservada íntegramente en `brain/40-Fuentes/privado/` (excluida del control de versiones mediante `.gitignore`).
   - **Copia Pública y Fixtures**: Publicada en `brain/40-Fuentes/publicado/` y `tests/fixtures/scienti/` con nombres propios de investigadores no líderes y correos personales anonimizados.

---

## 5. Cómo Repetirlo

```powershell
# Descarga automática con validación de host, timeout y caché:
.venv\Scripts\python.exe tools/fuentes/descargar_scienti.py

# Extracción, anonimización y generación de transcripciones y fixtures:
.venv\Scripts\python.exe tools/fuentes/extraer_scienti.py
```
