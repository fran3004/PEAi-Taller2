---
tipo: adr
estado: aprobado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[_Indice]]"
  - "[[Ingesta]]"
  - "[[Cola-importacion]]"
origen: "AGENTS.md y AUDITORIA-DISENO-PEAI.md - Fase 12"
---

# ADR-0010 · Límites Éticos y Responsabilidad Técnica en la Ingesta de Datos

## Contexto
La recolección automatizada de datos desde portales públicos gubernamentales como SCIENTI Minciencias (GrupLAC y CvLAC) puede sobrecargar los servidores institucionales si se ejecuta sin control de frecuencia. Además, cambios imprevistos en la estructura HTML o caídas de conectividad pueden provocar comportamientos erráticos o bloqueos por IP si no se aplican políticas responsables.

## Opciones consideradas
1. **Extracción masiva agresiva sin restricciones de velocidad**: Descarga rápida pero con alto riesgo de denegación de servicio (DoS) involuntario, baneo de IP institucional y colapso de la aplicación.
2. **Scraping responsable con límites estrictos, caché local y alternativa tabular (CSV)**: Conexión HTTPS exclusiva a hosts autorizados (`scienti.minciencias.gov.co`), pausas forzadas de mínimo 1 segundo, retroceso exponencial ante errores, User-Agent identificativo y respaldo por archivos CSV locales.

## Decisión
Se adoptan las **reglas de extracción responsable y límites éticos** detalladas en [[Ingesta]].
El extractor web respeta estrictamente:
- Pausa mínima de 1.0 segundo entre peticiones.
- Máximo 3 reintentos con backoff exponencial.
- User-Agent que acredita el proyecto académico de la Universidad Popular del Cesar.
- Caché local en disco en `datos/cache/`.
- Ante fallo irrecuperable de la fuente web, la aplicación no simula datos ni inventa campos: informa el error y habilita la vía de importación por archivos CSV canónicos.

## Consecuencias
- **Positivas**: Respeto a los servidores públicos; prevención de bloqueos de red; confiabilidad y reproducibilidad de las pruebas mediante caché.
- **Costos**: La descarga de conjuntos amplios de investigadores toma tiempo perceptible, mitigado mediante ejecución asíncrona en hilos secundarios controlados por la [[Cola-importacion]].
