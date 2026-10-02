---
tipo: fuente
estado: aprobado
creado: 2026-10-02
actualizado: 2026-10-02
relacionado:
  - "[[Modelo-2024-indice]]"
  - "[[Modelo-2024-original]]"
  - "[[Modelo-Grupos]]"
  - "[[Modelo-Productos]]"
  - "[[Modelo]]"
origen: "docs/entrada/Modelo-2024.original.pdf (Anexos 2 y 3, pp. 170-201)"
---

# Modelo Minciencias 2024 · Indicadores y Modelos Estadísticos

Documento de referencia: **M601PR04G01 (Versión 02)**.  
Citas directas al documento original: [[Modelo-2024-original]].

---

## 1. Perfiles de Grupos de Investigación (Anexo 2)

El Modelo establece un sistema de caracterización multidimensional de los grupos basado en siete (7) perfiles analíticos ([[Modelo-2024-original#Página 170]]–[[Modelo-2024-original#Página 182]]):

1. **Perfil de Integrantes ([[Modelo-2024-original#Página 177]]):**
   - Distribución de los integrantes según su nivel de formación (Doctores, Magísteres, Profesionales, Estudiantes) y su categoría de investigador (Emérito, Sénior, Asociado, Junior, Sin reconocimiento).
2. **Perfil de Colaboración ([[Modelo-2024-original#Página 178]]):**
   - Medición de la coautoría y proyectos conjuntos inter-grupales, inter-institucionales e internacionales.
3. **Perfil de Trayectoria y Permanencia ([[Modelo-2024-original#Página 179]]):**
   - Años de actividad continuada del grupo, estabilidad de sus líneas de investigación y retención de investigadores principales.
4. **Perfil de Producción GNC ([[Modelo-2024-original#Página 180]]):**
   - Concentración y volumen de productos de Generación de Nuevo Conocimiento (artículos en cuartiles superiores, libros A1, patentes concedidas).
5. **Perfil de Producción DTI ([[Modelo-2024-original#Página 181]]):**
   - Generación de patentes tecnológicas, software registrado, prototipos industriales y spin-offs.
6. **Perfil de Apropiación Social ([[Modelo-2024-original#Página 182]]):**
   - Vinculación comunitaria y procesos de co-creación científica.
7. **Perfil de Divulgación Pública ([[Modelo-2024-original#Página 182]]):**
   - Eventos de difusión, publicaciones no especializadas y estrategias transmedia.

---

## 2. Visualización y Conteos Institucionales (Anexo 2)

Para instituciones avaladoras como universidades, el modelo provee esquemas de consolidación ([[Modelo-2024-original#Página 183]]–[[Modelo-2024-original#Página 193]]):
- **Conteos Generales ([[Modelo-2024-original#Página 186]]):**
  - Total de grupos reconocidos y categorizados ($A1, A, B, C$).
  - Total de investigadores reconocidos ($IE, IS, IA, IJ$).
  - Total de productos válidos por gran tipología.
- **Conteos por Gran Área OCDE ([[Modelo-2024-original#Página 188]]–[[Modelo-2024-original#Página 193]]):**
  - Distribución de grupos y productos en las 6 áreas del conocimiento (Ciencias Naturales, Ingeniería, Salud, Agrícolas, Sociales, Humanidades).

---

## 3. Modelo Estadístico de Trayectoria (Anexo 3)

El Anexo 3 formaliza el modelo probabilístico que evalúa el progreso temporal de los grupos ([[Modelo-2024-original#Página 194]]–[[Modelo-2024-original#Página 201]]):
- **Distribución Logística Ordenada ([[Modelo-2024-original#Página 197]]):**
  - Modela la probabilidad de que un grupo ascienda o descienda entre las categorías $C \to B \to A \to A1$ en función de su edad, volumen de producción acumulado y calidad relativa.
  - Permite estimar la probabilidad condicional de transición de un grupo en convocatorias sucesivas.

---

## 4. Impacto en la Arquitectura y Dominio de PEA-i

1. **Hipercubo Estadístico Hecho a Mano**:
   - Según el contrato ([AGENTS.md](file:///c:/dev/PEAi-Taller2/AGENTS.md) y regla [02-estructuras-y-capas.md](file:///c:/dev/PEAi-Taller2/.agent/rules/02-estructuras-y-capas.md)), **las estadísticas de la aplicación se calculan en memoria desde la estructura de Hipercubo**, no mediante consultas SQL repetitivas en Supabase.
   - El Hipercubo indexa las 4 dimensiones cardinales: $\text{Grupo} \times \text{Categoría} \times \text{Año} \times \text{Subtipo}$.
   - Provee en tiempo $O(1)$ los cortes por año, gran área o tipología requeridos para las vistas gráficas.
2. **Interfaz Gráfica (Python PySide6 y C++ Qt 6)**:
   - Panel de Control institucional que muestra:
     - Gráficos de barras de distribución por categoría de grupo.
     - Gráficos de pastel o líneas de producción temporal (ventana de 5 y 10 años).
     - Tabla cruzada de grupos vs áreas OCDE.
