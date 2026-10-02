---
tipo: bitacora
estado: aprobado
creado: 2026-10-02
actualizado: 2026-10-02
relacionado:
  - "[[00-Inicio]]"
  - "[[SCIENTI-GrupLAC]]"
  - "[[SCIENTI-CvLAC]]"
  - "[[SCIENTI-Mapa-de-campos]]"
  - "[[SCIENTI-Informe-extraccion]]"
origen: "Captura integral y estructuración de fuentes SCIENTI"
agente: "antigravity"
rama: "master"
commit: "f82df22"
---

# Bitácora · 2026-10-02-antigravity-fuentes-scienti

## Objetivo
Realizar la descarga responsable, análisis estructural, modelos Pydantic y transcripción documental de las dos fuentes de Minciencias SCIENTI (GrupLAC y CvLAC) provistas por el proyecto, garantizando el aislamiento de datos personales en notas privadas no versionadas y publicando fixtures anonimizados con su respectivo oráculo `esperado.json`.

## Qué se hizo
- Implementación de `tools/fuentes/descargar_scienti.py` con validación estricta de host (`scienti.minciencias.gov.co`), HTTPS, timeout (10s conexión, 30s lectura), máximo 3 reintentos con backoff exponencial, pausa de 1.5s entre peticiones, User-Agent institucional UPC y caché en `datos/cache/`.
- Descarga real y exitosa en primer intento de ambas fuentes:
  - GrupLAC literal `0000000002099` (20,934 bytes, esqueleto) y GrupLAC canónico `00000000002099` (625,613 bytes, grupo GISICO UPC con 83 tablas).
  - CvLAC `0000494917` (450,831 bytes, hoja de vida completa con 39 tablas).
- Definición de modelos Pydantic v2 en `tools/fuentes/modelos_scienti.py`.
- Generación de notas privadas no versionadas (`.gitignore`) con la transcripción completa íntegra sin omisiones:
  - `brain/40-Fuentes/privado/SCIENTI-GrupLAC-completo.md`
  - `brain/40-Fuentes/privado/SCIENTI-CvLAC-completo.md`
- Generación de notas públicas versionables anonimizadas:
  - `brain/40-Fuentes/publicado/SCIENTI-GrupLAC.md`
  - `brain/40-Fuentes/publicado/SCIENTI-CvLAC.md`
- Creación de la especificación técnica de mapeo en `brain/40-Fuentes/publicado/SCIENTI-Mapa-de-campos.md`.
- Creación del informe de auditoría técnica en `brain/40-Fuentes/publicado/SCIENTI-Informe-extraccion.md`.
- Generación de fixtures y oráculos esperados en `tests/fixtures/scienti/`:
  - `gruplac_0000000002099.html` & `.esperado.json`
  - `gruplac_00000000002099.html` & `.esperado.json`
  - `cvlac_0000494917.html` & `.esperado.json`
- Creación y ejecución de la suite de pruebas offline `tests/fuentes/test_extraer_scienti.py` (5 pruebas, 100% verde).
- Validación de la bóveda con `tools/brain/verificar_brain.py` (20 notas, 0 errores, 0 advertencias).

## Comandos y resultados
- `.venv\Scripts\python.exe tools/fuentes/descargar_scienti.py`: Descarga y almacenamiento en caché exitoso con SHA256 verificado.
- `.venv\Scripts\python.exe tools/fuentes/extraer_scienti.py`: Parseo completo y generación de notas y fixtures.
- `.venv\Scripts\python.exe -m pytest tests/fuentes/ -v`: 5 pruebas pasadas (oráculos validados, seguridad de host y protocolo).
- `.venv\Scripts\python.exe tools/brain/verificar_brain.py`: Bóveda íntegra (0 errores, 0 advertencias).

## Decisiones
- Se documentó el hallazgo del padding en el parámetro `nro` de Minciencias (9 ceros genera esqueleto vacío; 10 ceros genera grupo GISICO UPC completo), conservando y testeando ambas respuestas en el sistema.
- Se añadió la regla `brain/40-Fuentes/privado/` al archivo `.gitignore` para proteger los datos personales reales no anonimizados según el contrato de `AGENTS.md`.

## Pendientes y siguiente paso
- Incorporar el archivo del Enunciado del Taller 2 en `docs/entrada/`.
- Definir la estrategia de ramas (`main` y `dev`).
- Avanzar hacia la especificación formal de requisitos `brain/10-Requisitos/SPEC.md`.
