---
tipo: bitacora
estado: aprobado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[00-Inicio]]"
  - "[[Ingesta]]"
  - "[[Cola-importacion]]"
  - "[[Multilista]]"
  - "[[SCIENTI-GrupLAC]]"
  - "[[SCIENTI-CvLAC]]"
  - "[[SCIENTI-Mapa-de-campos]]"
  - "[[Modelo]]"
  - "[[ADR-0010-Limites-y-responsabilidad-de-ingesta]]"
  - "[[SPEC]]"
origen: "Implementación oficial de la ingesta Python para PEA-i (URL, PDF y CSV)"
agente: "Antigravity"
rama: "master"
commit: "feat: ingesta Python URL PDF CSV"
---

# Bitácora · Ingesta Oficial de Datos en Python (URL, PDF, CSV)

## Objetivo
Implementar el subsistema integral de ingesta oficial de datos en Python para PEA-i (`src/pea/ingesta/`), dando cumplimiento a los requerimientos de extracción web responsable (GrupLAC y CvLAC de Minciencias), extracción estructurada de documentos PDF mediante `pdfplumber` con análisis página por página, tablas y detección de escaneado, lectura tolerante de archivos CSV (coma, punto y coma, UTF-8 BOM, filas corruptas toleradas), procesamiento asíncrono sobre la `Cola` FIFO propia y persistencia transaccional atómica sobre el catálogo de dominio y Supabase.

## Qué se hizo

1. **Modelos Pydantic de Ingesta (`src/pea/ingesta/modelos.py`)**:
   - Modelos de validación estricta y trazabilidad: `MetadatosOrigen`, `IntegranteIngesta`, `LineaIngesta`, `InstitucionIngesta`, `FormacionIngesta`, `ProductoIngesta`, `GrupoIngesta`, e `InvestigadorIngesta`.
   - Modelos de mapeo CSV canónico: `FilaGrupoCSV`, `FilaInvestigadorCSV`, `FilaProductoCSV`, `FilaAutorCSV`.
   - Modelos de reporte y análisis PDF: `PaginaPDF`, `DocumentoPDF` e `InformeIngesta`.

2. **Extractor Web Responsable (`src/pea/ingesta/extractor_url.py`)**:
   - Cumplimiento de políticas normativas:
     - Host exclusivo: `scienti.minciencias.gov.co` (bloqueo preventivo de cualquier otro dominio).
     - Protocolo obligatorio: `HTTPS`.
     - User-Agent institucional UPC: `PEAi-Taller2-UPC/1.0 (Proyecto Academico Estructura de Datos; Universidad Popular del Cesar...)`.
     - Timeouts (10 s conexión, 30 s lectura), retroceso exponencial ante 5xx (máx. 3 reintentos) y pausa de cortesía mínima de 1.0 s.
     - Caché local en `datos/cache/<hash>.html` y `.meta.json`.
   - Analizador HTML con `BeautifulSoup` y `lxml`, normalización de texto Unicode NFC y remoción de caracteres de control.
   - Generación de transcripción integral en Markdown (soporte para notas públicas anonimizadas en `brain/40-Fuentes/publicado/` y privadas en `brain/40-Fuentes/privado/`).
   - Exportación a JSON y sincronización con los 4 archivos CSV canónicos oficiales (`grupos.csv`, `investigadores.csv`, `productos.csv`, `autores.csv`).

3. **Extractor de Documentos PDF (`src/pea/ingesta/extractor_pdf.py`)**:
   - Procesamiento página a página con `pdfplumber`.
   - Extracción de texto estructurado y tablas tabulares (`page.extract_tables()`).
   - Detección rigurosa de documentos escaneados/rasterizados (imágenes sin texto seleccionable) con generación de alertas `AvisoDocumentoEscaneado`.
   - Regla normativa: Jamás inventar datos ni asumir valores ausentes.

4. **Lector de Archivos CSV Tolerante a Fallos (`src/pea/ingesta/lector_csv.py`)**:
   - Detección automática y soporte transparente de delimitadores coma (`,`) y punto y coma (`;`).
   - Detección automática de BOM UTF-8 (`\xef\xbb\xbf`) decodificando con `utf-8-sig`.
   - Manejo adecuado de comillas dobles, comillas escapadas `""` y campos con comas o saltos de línea.
   - **Tolerancia a filas inválidas**: Las filas corruptas o con tipos incompatibles se capturan individualmente en una lista de errores sin detener ni corromper el procesamiento del resto del archivo.

5. **Servicio de Ingesta y Cola Propia FIFO (`src/pea/ingesta/servicio_ingesta.py`)**:
   - Orquestación mediante la estructura enlazada a mano `Cola[TareaIngesta]`.
   - Ciclo de vida estricto de tareas: `pendiente` → `procesando` → `terminada` / `con_error`.
   - Integración con el catálogo `CatalogoInvestigacion`: inserción de grupos e investigadores en sus `ListaDoble` y de productos en la `Multilista` de nodos compartidos.
   - Desduplicación inteligente: no duplica nodos existentes en memoria; enlaza coautores adicionales en la multilista.
   - Persistencia atómica por lote con control optimista de `revision_esperada` y llamadas RPC.

6. **Extensión del CLI Institucional (`src/pea/cli.py`)**:
   - Añadidos subcomandos `importar-url` e `importar-pdf`.
   - Mejorado el subcomando `importar-csv` para delegar en `ServicioIngesta` con tolerancia a formatos y reporte de filas fallidas.

7. **Pruebas y Verificación (`tests/unit/test_ingesta.py`)**:
   - 14 pruebas unitarias sin red: validación de seguridad de host/HTTPS, normalización, parseo offline de GrupLAC y CvLAC usando fixtures reales de `tests/fixtures/scienti/`, extracción de PDF vectorial y detección de PDF escaneado (usando imagen Pillow), delimitadores `,` y `;`, UTF-8 BOM, filas corruptas toleradas, estados de la cola propia y enlaces en multilista.
   - 1 prueba de integración real con `scienti.minciencias.gov.co` marcada con `@pytest.mark.red`, ejecutada y verificada exitosamente con `-m red`.

## Validación
- `.\.venv\Scripts\ruff check src tests`: Aprobado (0 advertencias).
- `.\.venv\Scripts\pytest`: 65 pruebas aprobadas, 2 deseleccionadas (0 fallas).
- `.\.venv\Scripts\pytest -m red tests/unit/test_ingesta.py`: 1 prueba con red aprobada (14 deseleccionadas).
- `.\scripts\verificar.ps1`: Bóveda Obsidian OK (68 notas integras, 0 errores), Pruebas Python OK, Pruebas C++ OK (compilación limpia y doctest aprobado).
