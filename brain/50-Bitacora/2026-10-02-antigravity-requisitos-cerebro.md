---
tipo: bitacora
estado: aprobado
creado: 2026-10-02
actualizado: 2026-10-02
relacionado:
  - "[[00-Inicio]]"
  - "[[SPEC]]"
  - "[[Glosario]]"
  - "[[Variables-entrada-salida]]"
  - "[[Historias-de-usuario]]"
  - "[[Casos-de-uso]]"
  - "[[Matriz-modelo-requisitos]]"
  - "[[Preguntas-abiertas]]"
origen: "Sesión de análisis y formalización de requisitos"
agente: "Antigravity"
rama: "master"
commit: "docs: requisitos y cerebro base"
---

# Bitácora · Formalización de Requisitos y Cerebro Base de PEA-i

## Objetivo
Completar el cerebro funcional que gobernará todas las decisiones de desarrollo de PEA-i, formalizando la especificación de requisitos en `brain/10-Requisitos/` con trazabilidad unívoca a los puntos del taller (R0–R12 y C1–C6), el Modelo Minciencias 2024 y las fuentes SCIENTI capturadas, sin escribir código de aplicación ni esquemas SQL.

## Qué se hizo
1. **Completitud de Navegación**:
   - Se actualizó [[00-Inicio]] con mapa mental de navegación mermaid y enlaces relativos unívocos hacia los índices por módulo.
   - Se creó `brain/40-Fuentes/_Indice.md` organizando el corpus normativo del Modelo 2024 y las fuentes de datos SCIENTI.
   - Se creó `brain/10-Requisitos/_Indice.md` vinculando los 7 documentos analíticos.
2. **Construcción del Núcleo de Requisitos en `brain/10-Requisitos/`**:
   - [[SPEC]]: Especificación formal de 13 Requisitos Funcionales (RF-01 a RF-13) mapeados 1 a 1 con R0–R12, y 6 Requisitos No Funcionales (RNF-01 a RNF-06) mapeados con C1–C6, con criterios de aceptación comprobables y citas exactas.
   - [[Glosario]]: Definiciones canónicas de términos del dominio científico, estructuras de datos hechas a mano y patrones arquitecturales.
   - [[Variables-entrada-salida]]: Diccionario exhaustivo de atributos para Grupos, Investigadores, Integrantes, Productos y Métricas del Hipercubo, citando las páginas del Modelo y los selectores del mapa de campos de SCIENTI.
   - [[Historias-de-usuario]]: 10 historias de usuario (HU-01 a HU-10) cubriendo los roles de Administrador, Líder de Grupo, Investigador y Directivo, con criterios estilo checklist.
   - [[Casos-de-uso]]: 7 casos de uso detallados (CU-01 a CU-07) con flujos normales, alternativos, precondiciones, postcondiciones y manejo de fallas de red y concurrencia.
   - [[Matriz-modelo-requisitos]]: Matriz integral de trazabilidad cruzada bidireccional entre puntos de taller, RF/RNF, Modelo 2024, SCIENTI, HU, CU, estructuras de datos y estrategia de pruebas.
   - [[Preguntas-abiertas]]: Registro de 6 dudas metodológicas y supuestos de partida (`[SUPUESTO]`) sometidos a decisión del usuario antes del diseño técnico.
3. **Verificación de Bóveda y Calidad**:
   - Se ejecutó `tools/brain/verificar_brain.py` validando 30 notas inspeccionadas con 0 errores y 0 advertencias.
   - Se ejecutó la suite de pruebas unitarias (`pytest`) comprobando que las 5 pruebas de fuentes SCIENTI siguen pasando al 100%.

## Comandos y resultados
- `.venv\Scripts\python.exe tools\brain\verificar_brain.py` -> 30 notas inspeccionadas, 0 errores, 0 advertencias.
- `.venv\Scripts\python.exe -m pytest -v` -> 5 passed in 0.38s.

## Decisiones
- No se crearon tablas de base de datos ni migraciones en `supabase/migrations/` conforme a la restricción estricta de la tarea.
- Toda variable no presente de forma directa en las fuentes fue tipificada explícitamente bajo la etiqueta `[SUPUESTO]`.
- Se estructuró el hipercubo con 5 dimensiones canónicas: Grupo, Investigador, Categoría, Año y Validación.

## Pendientes y siguiente paso
- Esperar retroalimentación del usuario respecto a las 6 preguntas abiertas planteadas en [[Preguntas-abiertas]].
- Proceder con la fase de Diseño Arquitectural (`brain/20-Diseno/`) y Decisiones de Arquitectura (`brain/30-Decisiones/` - ADRs).
