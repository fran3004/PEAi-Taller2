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
origen: "Implementación oficial de la ingesta C++ para PEA-i (URL y CSV, sin PDF por contrato)"
agente: "Antigravity"
rama: "master"
commit: "feat: ingesta C++"
---

# Bitácora · Ingesta Oficial de Datos en C++ (URL y CSV)

## Objetivo
Implementar en C++17 el subsistema oficial de ingesta para PEA-i (`cpp/include/pea/ingesta/` y `cpp/src/ingesta/`), garantizando estricta paridad semántica y equivalencia estructural con el oráculo de datos oficial (`tests/fixtures/scienti/*.esperado.json`) y el contrato funcional desarrollado en Python. Se implementa extracción responsable vía URL (GrupLAC y CvLAC de Minciencias), lectura resiliente de archivos CSV (coma, punto y coma, UTF-8 BOM, filas corruptas toleradas) y orquestación asíncrona sobre la estructura enlazada a mano `Cola<TareaIngesta>`, respetando la prohibición contractual de implementar PDF en C++.

## Qué se hizo

1. **Modelos C++ de Ingesta (`cpp/include/pea/ingesta/modelos.hpp`)**:
   - Definición de tipos estructurados con serialización canónica `a_json()`: `MetadatosOrigen`, `InstitucionIngesta`, `LineaIngesta`, `IntegranteIngesta`, `FormacionIngesta`, `ProductoIngesta`, `GrupoIngesta`, `InvestigadorIngesta`, `FilaAutorCSV` e `InformeIngesta`.
   - Correspondencia exacta de campos y claves contra los oráculos `*.esperado.json` (incluyendo tipos opcionales mapeados a `null`).

2. **Parser HTML Tolerante C++ (`cpp/include/pea/ingesta/parser_html.hpp`, `cpp/src/ingesta/parser_html.cpp`)**:
   - Decodificación exhaustiva de entidades HTML: nombres comunes (`&aacute;`, `&ntilde;`, `&nbsp;`, `&quot;`, `&lt;`, etc.), numéricas decimales (`&#\d+;`) y hexadecimales (`&#x[0-9a-fA-F]+;`).
   - Limpieza y normalización de texto: preservación de saltos en etiquetas de bloque (`<br>`, `<p>`, `<div>`, `<tr>`, `<td>`), supresión de etiquetas inline y colapso de secuencias de espacios en blanco.
   - Extractor jerárquico de tablas `extraer_tablas`: seguimiento de profundidad (`depth`) para soportar correctamente tablas HTML anidadas sin truncar el contenido de las tablas contenedoras raíz.
   - Extracción resiliente de filas y celdas (`extraer_filas`, `extraer_celdas`, `extraer_primer_td_texto`), tolerante a omisión de etiquetas de cierre en el HTML crudo emitido por Minciencias.
   - Mapeo y procesamiento especializado de secciones GrupLAC (Datos básicos, Instituciones, Integrantes, Líneas, Artículos, Libros, Capítulos, Softwares, Trabajos dirigidos, Proyectos) y CvLAC (Hoja de vida, Formación académica, Áreas de actuación, Líneas, Artículos, Capítulos, Softwares, Trabajos dirigidos, Proyectos).
   - Generadores de transcripción integral en Markdown para GrupLAC y CvLAC (`generar_markdown_gruplac`, `generar_markdown_cvlac`).

3. **Lector CSV Resiliente (`cpp/include/pea/ingesta/lector_csv.hpp`, `cpp/src/ingesta/lector_csv.cpp`)**:
   - Autodetección y procesamiento transparente de delimitadores por coma (`,`) y punto y coma (`;`).
   - Detección y remoción automática de marca de orden de bytes (BOM) UTF-8 (`\xef\xbb\xbf`).
   - Analizador léxico de líneas con manejo de comillas dobles balanceadas y comillas escapadas `""`.
   - **Tolerancia a filas inválidas**: Las filas con errores estructurales o de formato son omitidas y registradas detalladamente en la lista de errores del informe, permitiendo que las filas válidas continúen su procesamiento con éxito.

4. **Extractor Web Responsable (`cpp/include/pea/ingesta/extractor_url.hpp`, `cpp/src/ingesta/extractor_url.cpp`)**:
   - Seguridad y cumplimiento institucional:
     - Host restringido exclusivamente a `scienti.minciencias.gov.co`.
     - Protocolo obligatorio `HTTPS`.
     - Identificador de cliente institucional `USER_AGENT_UPC`.
     - Control de tasa entre peticiones (`pausa_segundos >= 1.0`).
     - Caché local en `datos/cache/<hash>.html` y `.meta.json`.
   - Cliente de red reactivo basado en `QNetworkAccessManager` con timeout y soporte TLS/SSL de OpenSSL.

5. **Servicio de Ingesta y Cola FIFO Propia (`cpp/include/pea/ingesta/servicio_ingesta.hpp`, `cpp/src/ingesta/servicio_ingesta.cpp`)**:
   - Gestión integral del flujo de importación apoyado en la estructura de datos propia `Cola<TareaIngesta>`.
   - Transición determinista de estados: `Pendiente` → `Procesando` → `Terminada` (o `ConError` ante fallos sin corromper la cola).
   - Deduplicación automática e integración directa en memoria en `CatalogoInvestigacion` vinculando productos y autores en la `Multilista`.

6. **Integración en CLI (`cpp/src/cli.cpp`)**:
   - Incorporación del comando `importar-url -u <url> [--persistir] [--anonimizar]`.
   - Actualización del comando `importar-csv -a <archivo> -t <tipo>` para operar mediante `ServicioIngesta`.

7. **Cumplimiento Normativo (Sin PDF en C++)**:
   - Conforme a la regla del proyecto y la especificación del usuario, la extracción de archivos PDF se mantiene exclusivamente en Python; no se implementó PDF en C++.

## Pruebas y Verificación

1. **Suite de Pruebas Unitarias C++ (`cpp/tests/test_ingesta.cpp`)**:
   - **Paridad contra Oráculo**:
     - `gruplac_0000000002099` (GrupLAC vacío): validación exhaustiva de campos nulos y colecciones vacías.
     - `gruplac_00000000002099` (GrupLAC canónico GISICO): validación campo a campo de metadatos, integrantes (85), artículos (93), libros (14), capítulos (23), softwares (90), instituciones (2), líneas (8), trabajos dirigidos (136) y proyectos (32).
     - `cvlac_0000494917` (CvLAC canónico): validación de hoja de vida, par evaluador, formación académica (6), artículos (52), capítulos (13), softwares (9), trabajos dirigidos (49), proyectos (10), áreas de actuación (2) y líneas (5).
   - **Políticas de Seguridad URL**: Rechazo de HTTP, rechazo de dominios externos, rechazo de rutas desconocidas y aceptación de URLs oficiales.
   - **Lector CSV**: Delimitador coma, delimitador punto y coma, remoción de BOM UTF-8, comillas escapadas y tolerancia a filas corruptas.
   - **Cola Propia y Servicio**: Ciclo de vida FIFO de tareas, resiliencia ante errores y enlace a `Multilista`.
   - **Resultado Doctest**: 21 casos de prueba, 239 aserciones, 100% aprobadas.

2. **Verificación Integral (`scripts/verificar.ps1`)**:
   - Bóveda Obsidian: 69 notas íntegras, 0 errores, 0 advertencias.
   - Pruebas Python: 65 pruebas aprobadas, 0 fallos.
   - Pruebas C++: Compilación limpia (`-Werror`) y suites doctest aprobadas al 100%.

## Conclusión
El núcleo C++ de PEA-i dispone ahora de una capa de ingesta robusta, autónoma, tolerante y normativamente alineada con el oráculo de datos y la implementación de Python.
