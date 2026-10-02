---
tipo: fuente
estado: aprobado
creado: 2026-10-02
actualizado: 2026-10-02
relacionado:
  - "[[Modelo-2024-indice]]"
  - "[[Modelo-2024-original]]"
  - "[[Modelo-Grupos]]"
  - "[[Modelo]]"
origen: "docs/entrada/Modelo-2024.original.pdf (Anexo 5, pp. 240-244)"
---

# Modelo Minciencias 2024 · Clasificación de Áreas Científicas OCDE

Documento de referencia: **M601PR04G01 (Versión 02)**.  
Citas directas al documento original: [[Modelo-2024-original]].

---

## 1. Estructura Jerárquica OCDE

Minciencias adopta la taxonomía internacional de la **Organización para la Cooperación y el Desarrollo Económicos (OCDE)** para categorizar los Grupos de Investigación, los Investigadores y la producción científica en Colombia ([[Modelo-2024-original#Página 240]]–[[Modelo-2024-original#Página 244]]).

La jerarquía comprende tres niveles:
1. **Gran Área**: 6 grandes divisiones del conocimiento.
2. **Área**: 42 divisiones intermedias identificadas con letra/código.
3. **Disciplina**: Subdisciplinas específicas con código alfanumérico (ej. `1B01 Ciencias de la computación`).

---

## 2. Las 6 Grandes Áreas del Conocimiento (Tabla 8)

### 1. Ciencias Naturales ([[Modelo-2024-original#Página 240]]–[[Modelo-2024-original#Página 241]])
- **1A. Matemática**: Matemáticas puras, aplicadas, estadística y probabilidades.
- **1B. Ciencias de la computación e información**: Computación teórica, sistemas, software, IA.
- **1C. Ciencias físicas**: Física atómica, materia condensada, óptica, astronomía.
- **1D. Ciencias químicas**: Química orgánica, inorgánica, física, analítica.
- **1E. Ciencias de la tierra y medioambientales**: Geología, vulcanología, meteorología, oceanografía.
- **1F. Ciencias biológicas**: Biología celular, microbiología, genética, botánica, zoología, ecología, biodiversidad.
- **1G. Otras ciencias naturales**.

### 2. Ingeniería y Tecnología ([[Modelo-2024-original#Página 241]]–[[Modelo-2024-original#Página 242]])
- **2A. Ingeniería civil**: Estructuras, transporte, geotecnia.
- **2B. Ingeniería eléctrica, electrónica e informática**: Telecomunicaciones, control, hardware.
- **2C. Ingeniería mecánica**: Termodinámica, diseño mecánico, aeroespacial.
- **2D. Ingeniería química**: Procesos químicos, reactores.
- **2E. Ingeniería de materiales**: Cerámicos, polímeros, metalurgia.
- **2F. Ingeniería médica**: Biomédica, equipos de diagnóstico.
- **2G. Ingeniería ambiental**: Tratamiento de aguas, residuos, control de contaminación.
- **2H. Biotecnología ambiental**: Biorremediación, bioseguridad.
- **2I. Biotecnología industrial**: Bioproductos, biomateriales, biocombustibles.
- **2J. Nanotecnología**: Nanomateriales, nanoprocesos.
- **2K. Otras ingenierías y tecnologías**: Alimentos, producción, industrial.

### 3. Ciencias Médicas y de la Salud ([[Modelo-2024-original#Página 243]])
- **3A. Medicina básica**: Anatomía, farmacología, fisiología, inmunología, patología.
- **3B. Medicina clínica**: Cirugía, pediatría, oncología, cardiología, psiquiatría.
- **3C. Ciencias de la salud**: Epidemiología, salud pública, enfermería, nutrición.
- **3D. Biotecnología en salud**: Terapias génicas, vacunas, diagnóstico molecular.
- **3E. Otras ciencias médicas**.

### 4. Ciencias Agrícolas y Veterinarias ([[Modelo-2024-original#Página 243]])
- **4A. Agricultura, silvicultura y pesca**: Agronomía, suelos, horticultura, pesca.
- **4B. Producción animal y lechería**: Zootecnia, nutrición animal.
- **4C. Ciencias veterinarias**: Medicina y cirugía veterinaria.
- **4D. Biotecnología agrícola**: Clonación vegetal, fitomejoramiento.
- **4E. Otras ciencias agrícolas**.

### 5. Ciencias Sociales ([[Modelo-2024-original#Página 243]]–[[Modelo-2024-original#Página 244]])
- **5A. Psicología**: Psicología general, cognitiva, clínica, social.
- **5B. Economía y negocios**: Finanzas, administración, contabilidad, mercadeo.
- **5C. Ciencias de la educación**: Pedagogía, didáctica, educación especial.
- **5D. Sociología**: Sociología general, demografía, antropología.
- **5E. Derecho**: Derecho constitucional, penal, civil, internacional.
- **5F. Ciencia política**: Políticas públicas, relaciones internacionales.
- **5G. Geografía social y económica**: Planificación urbana, desarrollo regional.
- **5H. Periodismo y comunicaciones**: Medios masivos, teoría de la comunicación.
- **5I. Otras ciencias sociales**.

### 6. Humanidades y Artes ([[Modelo-2024-original#Página 244]])
- **6A. Historia y arqueología**: Historia nacional, universal, arqueología.
- **6B. Idiomas y literatura**: Lingüística, filología, literatura.
- **6C. Filosofía, ética y religión**: Ética aplicada, filosofía de la ciencia.
- **6D. Arte**: Música, artes visuales, artes escénicas, diseño y arquitectura.
- **6E. Otras humanidades**.

---

## 3. Impacto en la Arquitectura y Dominio de PEA-i

1. **Normalización en Base de Datos (PostgreSQL en Supabase)**:
   - Tabla de catálogo `areas_ocde` con columnas `codigo_area`, `gran_area`, `nombre_area`, `codigo_disciplina`, `nombre_disciplina`.
   - Llave foránea en `grupos` (`area_ocde_id`) para segmentar los grupos de la Universidad Popular del Cesar por disciplina y gran área.
2. **Dimensiones de Filtrado en la GUI**:
   - Selector en la vista de Resumen/Panel para filtrar la producción por Gran Área (ej. Ingeniería vs Ciencias Sociales).
   - Base para los gráficos comparativos de PySide6 y Qt 6 C++.
