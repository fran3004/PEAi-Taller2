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
origen: "docs/entrada/Modelo-2024.original.pdf (Capítulo II, pp. 41-65)"
---

# Modelo Minciencias 2024 · Reconocimiento de Investigadores

Documento de referencia: **M601PR04G01 (Versión 02)**.  
Citas directas al documento original: [[Modelo-2024-original]].

---

## 1. Definición y Tipos de Integrantes

El Modelo define al investigador como aquella persona que realiza actividades de CTeI vinculada al menos a un Grupo de Investigación, Desarrollo Tecnológico o de Innovación avalado por una institución del SNCTI ([[Modelo-2024-original#Página 41]]).

Los integrantes de un grupo se clasifican jerárquicamente en diez (10) modalidades ([[Modelo-2024-original#Página 42]]):
1. **Investigador Emérito (IE)**: Máxima distinción de trayectoria.
2. **Investigador Sénior (IS)**: Investigador consolidado con alta producción y formación de talento.
3. **Investigador Asociado (IA)**: Investigador en consolidación con producción continua.
4. **Investigador Junior (IJ)**: Investigador inicial con producción científica demostrable.
5. **Integrante vinculado con título de Doctorado**.
6. **Integrante vinculado con título de Maestría**.
7. **Integrante vinculado con título de Pregrado**.
8. **Estudiante de Doctorado**.
9. **Estudiante de Maestría**.
10. **Estudiante de Pregrado**.

---

## 2. Requisitos y Criterios por Categoría

### 2.1 Investigador Emérito (IE)
- **Requisitos ([[Modelo-2024-original#Página 42]]–[[Modelo-2024-original#Página 43]]):**
  - Poseer título de Doctorado o trayectoria equivalente con aportes extraordinarios al SNCTI.
  - Haber sido reconocido como Investigador Sénior en al menos tres (3) convocatorias previas o tener una trayectoria vitalicia destacada.
  - Producción científica de alta calidad (artículos A1/A2, libros de investigación, patentes concedidas).
  - Reconocimiento vitalicio (salvo pérdida por fraude o faltas éticas, [[Modelo-2024-original#Página 35]]).

### 2.2 Investigador Sénior (IS)
- **Requisitos de Formación y Producción ([[Modelo-2024-original#Página 43]]–[[Modelo-2024-original#Página 45]]):**
  - Título de Doctorado (o Maestría con producción compensatoria significativa).
  - Haber dirigido al menos una (1) tesis de Doctorado finalizada o cuatro (4) trabajos de Maestría.
  - Cumplir con un mínimo de producción en actividades de Generación de Nuevo Conocimiento (GNC) y/o Desarrollo Tecnológico e Innovación (DTI) en la ventana de observación (mínimo 10 productos de calidad tipo Top o A).
  - Puntaje mínimo acumulado según la escala ponderada de productos.

### 2.3 Investigador Asociado (IA)
- **Requisitos de Formación y Producción ([[Modelo-2024-original#Página 45]]–[[Modelo-2024-original#Página 47]]):**
  - Título de Doctorado o Maestría.
  - Haber dirigido al menos un (1) trabajo de grado de Maestría o dos (2) de Pregrado.
  - Contar con al menos cuatro (4) productos de GNC/DTI reconocidos en la ventana de observación.

### 2.4 Investigador Junior (IJ)
- **Requisitos de Formación y Producción ([[Modelo-2024-original#Página 47]]–[[Modelo-2024-original#Página 49]]):**
  - Título de Doctorado, Maestría o Pregrado con producción relevante.
  - Contar con al menos un (1) producto de GNC tipo A1, A o B en la ventana de observación.

---

## 3. Ventana de Observación para Investigadores

- La producción de los investigadores se evalúa dentro de ventanas temporales específicas ([[Modelo-2024-original#Página 54]]):
  - **Artículos científicos y notas**: últimos 5 años (con consideraciones especiales para convocatorias específicas).
  - **Libros de investigación y patentes**: últimos 10 años.
  - **Tesis de doctorado dirigidas**: últimos 10 años.
  - **Apropiación social y divulgación**: últimos 5 años.

---

## 4. Impacto en la Arquitectura y Dominio de PEA-i

1. **Entidad `Investigador`**:
   - `id_investigador` (UUID / clave primaria en BD).
   - `identificacion` / `codigo_cvlac` (String).
   - `nombre_completo` (String).
   - `categoria_investigador` (Enum: `EMERITO`, `SENIOR`, `ASOCIADO`, `JUNIOR`, `SIN_RECONOCIMIENTO`).
   - `nivel_formacion` (Enum: `DOCTORADO`, `MAESTRIA`, `PREGRADO`).
   - `activo` (Boolean).
2. **Estructuras en Memoria**:
   - Cada `Investigador` es un nodo en la `ListaDoble` de investigadores.
   - Conexión mediante `Multilista`: un investigador enlaza a sus grupos de pertenencia y a sus productos coautorados.
3. **Persistencia en PostgreSQL (Supabase)**:
   - Tabla `investigadores` sujeta a RLS y control de versión con `meta.revision`.
