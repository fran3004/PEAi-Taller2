---
tipo: fuente
estado: aprobado
creado: 2026-10-02
actualizado: 2026-10-02
relacionado:
  - "[[Modelo-2024-indice]]"
  - "[[Modelo-2024-original]]"
  - "[[Modelo-Investigadores]]"
  - "[[Modelo-Productos]]"
  - "[[Modelo]]"
origen: "docs/entrada/Modelo-2024.original.pdf (Capítulo III, pp. 66-130)"
---

# Modelo Minciencias 2024 · Reconocimiento y Clasificación de Grupos

Documento de referencia: **M601PR04G01 (Versión 02)**.  
Citas directas al documento original: [[Modelo-2024-original]].

---

## 1. Definición y Requisitos de Reconocimiento

Un **Grupo de Investigación, Desarrollo Tecnológico o de Innovación** es el conjunto de dos o más personas que interactúan para investigar y generar productos de conocimiento en uno o varios temas, de acuerdo con un plan de trabajo y un proyecto institucional avalado ([[Modelo-2024-original#Página 41]], [[Modelo-2024-original#Página 66]]).

Para ser **Reconocido** por Minciencias, el grupo debe cumplir concurrentemente ([[Modelo-2024-original#Página 67]]–[[Modelo-2024-original#Página 68]]):
1. Estar registrado en el aplicativo **GrupLAC** de la plataforma ScienTI.
2. Tener un mínimo de **dos (2) integrantes**.
3. Tener un **Líder de Grupo** formalmente designado.
4. Contar con el **aval institucional** de al menos una institución registrada (ej. Universidad Popular del Cesar).
5. Tener al menos un (1) **proyecto de investigación** en ejecución o terminado dentro de la ventana de observación.
6. Demostrar una trayectoria de producción científica con al menos un producto tipo GNC o DTI validado en la ventana de observación.

---

## 2. Categorías de Clasificación de Grupos

Los grupos reconocidos son clasificados jerárquicamente en cuatro categorías de excelencia o quedan como reconocidos no categorizados ([[Modelo-2024-original#Página 123]]–[[Modelo-2024-original#Página 126]]):

| Categoría | Descripción y Nivel de Madurez | Criterios Clave ([[Modelo-2024-original#Página 124]]–[[Modelo-2024-original#Página 125]]) |
|---|---|---|
| **A1** | Máximo nivel de excelencia internacional y nacional | Cuartil superior en producción normalizada, alta concentración de productos Top/A, integrantes con doctorado e investigadores Sénior/Asociados, proyectos vigentes y dirección de tesis doctorales. |
| **A** | Alto nivel de producción y madurez consolidada | Producción regular de alta calidad en GNC y DTI, integrantes con posgrado y formación de recurso humano sostenida. |
| **B** | Grupos consolidados en fase de crecimiento | Producción continua de artículos y formación de recurso humano (maestría/pregrado), con proyectos activos. |
| **C** | Grupos en desarrollo con producción inicial verificada | Cumplimiento de umbrales básicos de producción de nuevo conocimiento y vinculación activa de estudiantes. |
| **Reconocido** | Cumple requisitos de existencia pero sin categoría | Grupos que superan las condiciones mínimas del numeral 1 pero no alcanzan los cuartiles o puntajes mínimos de producción. |

---

## 3. Ventana de Observación y Escala Logarítmica

- **Ventana de Observación ([[Modelo-2024-original#Página 115]]):**
  - Período estándar de **5 años** previos al corte de la convocatoria para artículos científicos, software, innovaciones y eventos.
  - Período ampliado de **10 años** para libros de investigación, capítulos, patentes y variedades vegetales/animales.
- **Eliminación de Efectos de Escala y Normalización ([[Modelo-2024-original#Página 115]]–[[Modelo-2024-original#Página 116]]):**
  - El modelo utiliza la función logaritmo natural ($\ln$) sobre la producción ponderada para evitar distorsiones por el tamaño desproporcionado de integrantes o antigüedad de los grupos:
    $$\text{Producción Normalizada} = \sum \ln(1 + \text{Puntaje Subtipo})$$
- **Pesos Globales (Tabla 6, [[Modelo-2024-original#Página 116]]–[[Modelo-2024-original#Página 118]]):**
  - Los productos se ponderan según su calidad: Patentes ($500$), Libros A1 ($300$), Artículos A1 ($100$), Software ($35$), etc.

---

## 4. Impacto en la Arquitectura y Dominio de PEA-i

1. **Entidad `Grupo`**:
   - `id_grupo` (UUID / Clave primaria).
   - `codigo_gruplac` (String único, ej. `COL0001234`).
   - `nombre_grupo` (String).
   - `gran_area_ocde` / `area_conocimiento` (Referencias al catálogo OCDE).
   - `categoria_grupo` (Enum: `A1`, `A`, `B`, `C`, `RECONOCIDO`, `AVALADO_NO_RECONOCIDO`).
   - `ano_creacion` (Integer).
   - `activo` (Boolean).
2. **Estructuras en Memoria**:
   - Colección principal almacenada en `ListaDoble` de grupos.
   - Punteros en `Multilista`: cada nodo `Grupo` apunta a la lista de sus `Investigador`es vinculados y a su lista de `Producto`s asociados.
3. **Cálculos Analíticos**:
   - Las métricas de producción por año, área y tipología se extraen del **Hipercubo**, respetando los pesos de la Tabla 6 sin requerir agregaciones SQL directas en Supabase.
