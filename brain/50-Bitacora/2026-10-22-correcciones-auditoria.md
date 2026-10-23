---
tipo: bitacora
estado: revisado
creado: 2026-10-22
actualizado: 2026-10-22
relacionado:
  - "[[00-Inicio]]"
  - "[[2026-10-19-auditoria-complementaria]]"
  - "[[2026-10-19-auditoria-integral-python-supabase]]"
origen: "Plan de remediación y corrección de hallazgos de auditoría integral PEA-i"
agente: "Antigravity"
rama: "fix/auditoria-2026-10-22"
commit: "0d17144"
---

# Bitácora · Línea base y preparación de correcciones de auditoría

## Objetivo

Preparar el entorno de trabajo, generar el respaldo íntegro de la base de datos de producción Supabase (`pea-prod`) y registrar la línea base de todas las suites y diagnósticos del sistema antes de iniciar las correcciones puntuales de los hallazgos de auditoría.

## Rama de trabajo

- **Rama base:** `master` en commit `0d17144` (*fix: stabilize SCIENTI imports and reporting*).
- **Rama creada para correcciones:** `fix/auditoria-2026-10-22`.
- **Árbol de trabajo:** Limpio, sin modificaciones en código fuente ni archivos de desarrollo.

## Respaldo de la base de datos Supabase

Se ejecutó `tools/db/respaldar.py` utilizando credenciales de solo lectura autenticadas bajo RLS:

- **Archivo de respaldo:** `datos/respaldos/respaldo_20261022_215421_346750.json` (directorio ignorado por Git).
- **Integridad:** SHA-256 `453b2e6fefeb85b937f15872be7fa3b20073cfb78002c3639cbbba641e7571a6`.
- **Total de filas respaldadas:** 6458 filas a través de 20 tablas.
- **Conteos de entidades clave confirmados:**
  - `grupos`: 4 filas
  - `investigadores`: 291 filas
  - `productos`: 2352 filas
  - `integrantes_grupo`: 291 filas
  - `producto_autores`: 2356 filas
  - `producto_grupos`: 1059 filas
- **Tablas secundarias y de metadatos:**
  - `meta`: 1 fila (revisión remota verificada)
  - `grupo_instituciones`: 2 filas
  - `grupo_plan_estrategico`: 1 fila
  - `lineas_investigacion`: 13 filas
  - `proyectos`: 42 filas
  - `semilleros`: 2 filas
  - `investigador_formacion`: 11 filas
  - `investigador_experiencia`: 14 filas
  - `investigador_areas_actuacion`: 2 filas
  - `investigador_idiomas`: 3 filas
  - `investigador_reconocimientos`: 4 filas
  - `investigador_redes_identificadores`: 9 filas
  - `auditoria_cambios`: 0 filas
  - `usuarios_autorizados`: 1 fila

## Línea base de comprobaciones

Se ejecutó y validó la totalidad de herramientas diagnósticas antes de introducir cualquier cambio:

1. **Ruff linter:**
   - Comando: `.\.venv\Scripts\ruff.exe check .`
   - Resultado: 0 advertencias, 0 errores (`All checks passed!`).
2. **Suite de pruebas Python:**
   - Comando: `.\.venv\Scripts\python.exe -m pytest -m "not red"`
   - Resultado: 325 pruebas aprobadas, 3 omitidas por requerir red (`325 passed, 3 deselected`).
3. **Compilación C++:**
   - Directorio: `build/entrega`
   - Comando: `cmake --build build/entrega`
   - Resultado: Compilación limpia sin errores ni advertencias (`-Werror`).
4. **Pruebas unitarias CTest / doctest:**
   - Comando: `ctest --test-dir build/entrega --output-on-failure`
   - Ejecutable: `build/entrega/pruebas_cpp.exe`
   - Resultado: 100% pruebas aprobadas (62 casos de prueba doctest, 862 aserciones).
5. **Autoprueba TUI C++:**
   - Comando: `.\build\entrega\pea-cpp.exe --autoprueba`
   - Resultado: 0 hallazgos en las 32 combinaciones de pantalla y terminal (80x24, 100x28, 120x35, 160x50).
6. **Autoprueba GUI PySide6:**
   - Comando: `.\dist\PEAi-Windows-x64\PEAi-Python\pea-cli.exe --autoprueba-gui`
   - Resultado: 0 hallazgos en las 24 combinaciones de pantalla y resolución (1100x700, 1366x768, 1920x1080).
7. **Verificación cruzada Python/C++:**
   - Comando: `.\dist\PEAi-Windows-x64\PEAi-Python\pea-cli.exe --verificar-cruzada`
   - Resultado: 3 de 3 comprobaciones coincidentes (versión de aplicación, resumen JSON canónico y mutaciones/deshacer).

## Corrección 1: Validación de rango de año en entidad Producto (esquema Supabase)

- **Problema:** En `src/pea/dominio/producto.py`, la entidad `Producto` aceptaba cualquier año (por ejemplo 1800), fallando únicamente en persistencia si Supabase rechazaba el valor por la restricción `CHECK (ano >= 1970 AND ano <= 2100)`.
- **Acciones realizadas:**
  1. **TDD:** Se crearon pruebas unitarias en `tests/unit/test_dominio_producto.py` reproduciendo la falla con años 1800, 1969 y 2101, validando aceptación de 1970 y 2100, y rechazo de tipos no enteros o booleanos (`True`/`False`).
  2. **Modelo de dominio:** Se definieron las constantes `ANO_MINIMO_BASE = 1970` y `ANO_MAXIMO_BASE = 2100` (`ANO_MINIMO_PRODUCTO` / `ANO_MAXIMO_PRODUCTO`), y se añadió `@field_validator("ano", mode="before")` en `Producto` alineado con la base de datos sin restringir al año actual en el modelo. Se conservó `validar_ano_producto` con el límite del año actual para flujos de ingesta/importación.
  3. **Manejo en GUI / Servicio de Aplicación:** Se mejoró `_mensaje_validacion` en `servicio_aplicacion.py` para traducir `ValidationError` de Pydantic a `ErrorValidacion` con mensajes amables y claros en español ante formularios con campos inválidos.
  4. **Paridad Python/C++:** Se verificó que en C++ `validar_ano_producto` valida enteros y el rango 1970 a año actual en el catálogo, mientras `Producto` en Python valida contra el esquema de base de datos (1970-2100). Se añadió prueba de paridad de casos compartidos en `test_dominio_producto.py`.
- **Resultados de validación:**
  - `ruff check .`: Limpio (0 errores).
  - `pytest -m "not red"`: 332 aprobadas, 3 omitidas.
  - C++ build y CTest: 100% aprobado (62 casos doctest, 862 aserciones).
  - `pea-cpp --autoprueba`: 0 hallazgos en 32 pantallas.
  - `pea-cli --autoprueba-gui`: 0 hallazgos en 24 combinaciones de pantalla.
  - `pea-cli --verificar-cruzada`: 3 de 3 comprobaciones coincidentes.

## Corrección 2: Control de revisión remota estricto y detección de pérdida de conexión

- **Problema:** En `src/pea/datos/revision.py`, `ControladorRevision.consultar_remota` devolvía `self._revision_local` cuando tanto la RPC rápida como la consulta REST a `meta` fallaban o devolvían valores inválidos (por ejemplo, lista vacía o `.get("revision", 1)`). Esto causaba un falso éxito en `verificar_consistencia` simulando sincronización cuando no había conectividad.
- **Acciones realizadas:**
  1. **TDD:** Se crearon pruebas unitarias en `tests/unit/test_revision_remota.py` con un cliente falso para los 4 casos: (a) RPC exitosa devuelve valor; (b) RPC fallida pero meta exitosa devuelve meta; (c) RPC y meta fallidas lanza `ErrorConexion` detallando ambos fallos; (d) meta vacía, nula o revisión no positiva lanza `ErrorConexion`.
  2. **Paridad Python/C++:** Se implementó `_revision_valida` y se refactorizó `consultar_remota` para exigir enteros mayores que cero y lanzar `ErrorConexion` con la misma estructura diagnóstica de C++ (`cpp/src/datos/revision.cpp`). Se añadió caso de prueba idéntico en C++ (`cpp/tests/test_resiliencia.cpp`).
  3. **Manejo en GUI y CLI:** Se añadieron pruebas en `tests/unit/test_revision_sin_conexion.py` verificando el comportamiento sin red de los llamadores (`cli.py`, `servicio_aplicacion.py`, `servicio_dominio.py`). En `ventana_principal.py`, se conectó `actualizar_estado_global()` en el callback de la verificación periódica para desplegar la franja roja de sin conexión y bloquear escrituras sin congelar la ventana.
  4. **Modo demostración y resiliencia:** Se verificó que el modo demo utiliza `_revision_demo_remota` sin consultar la red y que `test_resiliencia_persistencia.py` mantiene el 100% de aprobación.
  5. **Prueba manual con Supabase real y corte simulado:** Se comprobó conexión real obteniendo la revisión remota vigente (revisión 4368) y se simuló caída de red validando la captura inmediata de `ErrorConexion`, activación de `sin_conexion = True` y motivo de bloqueo de mutaciones.
- **Resultados de validación:**
  - `ruff check .`: Limpio (0 errores).
  - `pytest -m "not red"`: 362 aprobadas, 3 omitidas.
  - C++ build y CTest: 100% aprobado (63 casos doctest, 879 aserciones).
  - `pea-cpp --autoprueba`: 0 hallazgos en 32 pantallas.
  - `pea-cli --autoprueba-gui`: 0 hallazgos en 24 combinaciones de pantalla.
  - `pea-cli --verificar-cruzada`: 3 de 3 comprobaciones coincidentes.

## Corrección 3: Persistencia, idempotencia y reporte de autorías CSV

- **Problema:**
  - En Python (`src/pea/ingesta/servicio_ingesta.py`), en la rama `tipo == "autores"` de `_procesar_tarea_csv`, ante un fallo en `asociar_autor` se capturaba genéricamente con `except Exception: pass` e incrementaba erróneamente `informe.autores_procesados`, mostrando al usuario autorías procesadas cuando nada se persistía en Supabase.
  - En C++ (`cpp/src/ingesta/servicio_ingesta.cpp`), la rama `"autores"` solo agregaba la arista en el grafo en memoria y nunca llamaba a `RepositorioProductos::asociar_autor` ni persistía en base aunque `persistir=true`.
- **Acciones realizadas:**
  1. **TDD:**
     - En Python (`tests/unit/test_ingesta_autores.py`), se crearon 13 pruebas unitarias exhaustivas:
       - Falla en repositorio no suma autores procesados y añade error a `filas_erroneas` y advertencias.
       - Persistencia remota previa a la adición al grafo en memoria.
       - Manejo con reintento acotado de `ConflictoRevision` vía `_ejecutar_con_reintento_revision`.
       - Captura estricta de jerarquía `ErrorPEA` (no genérica `Exception`).
       - Idempotencia ante violaciones de unicidad (PostgREST código `23505`).
       - Detección y advertencia clara ("sin identificador remoto") si `prod.id` o `inv.id` están ausentes en modo persistente.
       - Estados de tarea: `ConError` si fallan todas las relaciones; `Terminada` con advertencias si fallan algunas, con mensaje `"N de M relaciones guardadas"`.
     - En C++ (`cpp/tests/test_ingesta.cpp`), se añadió el caso de prueba `"Autorias CSV persisten antes de contar y conservan errores por fila"` con 202 aserciones validando persistencia, idempotencia (23505), preservación de errores por número de fila y estados finales de tarea.
  2. **Persistencia e idempotencia:**
     - En Python: `RepositorioProductos.asociar_autor` en `src/pea/datos/repositorios.py` captura `ConflictoRevision` e ignora código `23505` para soportar ejecuciones idempotentes. `servicio_ingesta.py` persiste antes de enlazar en `multilista_productos`.
     - En C++: `RepositorioProductos::asociar_autor` en `cpp/src/datos/repositorios.cpp` ignora código `23505`. `CatalogoInvestigacion` expone `asociar_autor_producto` y `cpp/src/ingesta/servicio_ingesta.cpp` replica el flujo llamando a `asociar_autor` con `ejecutar_con_reintento_revision`.
  3. **Rastreo de número de fila:**
     - Se añadió el campo `fila` a `FilaAutorCSV` en `src/pea/ingesta/modelos.py` y `cpp/include/pea/ingesta/modelos.hpp`.
     - `src/pea/ingesta/lector_csv.py` y `cpp/src/ingesta/lector_csv.cpp` asignan el número de fila (base 1) para reportar errores y advertencias contextualizados al usuario.
  4. **Presentación en interfaces:**
     - En PySide6 (`src/pea/gui/pantallas/importar.py`) y TUI FTXUI (`cpp/src/tui/aplicacion_tui.cpp`), se visualizan los mensajes detallados de avance y advertencias de filas con fallos.
  5. **Prueba sintética en Supabase real y verificación de invariantes:**
     - Se limpió el registro huérfano preliminar id=302 y se verificaron los conteos base (4 grupos, 291 investigadores, 2352 productos, 2356 producto_autores).
     - Se insertaron sintéticos `Investigador` (`PRUEBA-INV-CSV-01`) y `Producto` (`PRUEBA-PROD-CSV-01`) con `es_ejemplo=true`.
     - Se ejecutó la ingesta CSV de autoría comprobando `autores_procesados == 1`, persistencia efectiva en `producto_autores`, e idempotencia en segunda ejecución sin duplicados.
     - Se eliminaron todos los registros sintéticos y se certificaron los conteos idénticos al punto de partida (4, 291, 2352, 2356).
- **Resultados de validación:**
  - `ruff check .`: Limpio (0 errores).
  - `pytest -m "not red"`: 375 aprobadas, 3 omitidas.
  - C++ build y CTest: 100% aprobado (64 casos doctest, 1081 aserciones).
  - `pea-cpp --autoprueba`: 0 hallazgos en 32 pantallas.
  - `pea-cli --autoprueba-gui`: 0 hallazgos en 24 combinaciones de pantalla.
  - `pea-cli --verificar-cruzada`: 3 de 3 comprobaciones coincidentes.

## Corrección 4: Seguimiento seguro y validado de redirecciones HTTP en ExtractorURL

- **Problema:** En `src/pea/ingesta/extractor_url.py`, `descargar_o_cargar_cache` utilizaba `requests.get(url, ...)` que seguía redirecciones de forma automática sin verificar si el destino final cambiaba de host o degradaba a protocolo no seguro (`http://`). Asimismo, el ciclo de reintentos envolvía toda la operación bajo `except Exception:`, provocando que cualquier fallo de validación (`ValueError`) se reintentara 3 veces con pausas exponenciales innecesarias. En C++ (`cpp/src/ingesta/extractor_url.cpp`), se rechazaba de plano cualquier código 301/302.
- **Acciones realizadas:**
  1. **TDD:**
     - En Python (`tests/unit/test_extractor_redirecciones.py`), se añadieron 8 pruebas unitarias con simulación de peticiones (monkeypatch):
       - (a) Redirección 302 hacia otro host rechazada de inmediato (`ValueError`) y sin reintentos (1 sola llamada de red).
       - (b) Redirección hacia `http://` rechazada de inmediato (`ValueError`) sin reintentos.
       - (c) Redirección relativa en el mismo host y con ruta válida (`/gruplac/...`) seguida correctamente, resolviendo URL absoluta y guardando `url_final` en metadatos, conservando la clave de caché original.
       - (d) Límite de 3 saltos de redirección: falla con excepción tras superar el umbral.
       - (e) Caso normal 200 sin redirección conserva comportamiento intacto (`url_final == url`).
       - Redirección a ruta no reconocida como GrupLAC/CvLAC rechazada sin reintentos.
       - Ausencia de cabecera `Location` en 302 lanza `RuntimeError` explicativo.
       - Errores de red temporales (`ConnectionError`) y HTTP 5xx sí se reintentan hasta 3 veces con retroceso exponencial.
     - En C++ (`cpp/tests/test_ingesta.cpp`), se añadieron pruebas doctest de `ExtractorURL::validar_redireccion` para los mismos escenarios: rechazo de host ajeno, rechazo de esquema HTTP, rechazo de rutas desconocidas y resolución correcta de rutas relativas y absolutas oficiales.
  2. **Implementación de redirección manual y metadatos:**
     - En Python (`src/pea/ingesta/extractor_url.py`): se configuró `allow_redirects=False`, seguimiento manual de `Location` resolviendo con `urljoin`, validación estricta de cada salto con `self.validar_url`, respeto de la pausa de cortesía entre saltos (`_esperar_pausa_cortesia`), escape inmediato de `ValueError` fuera del ciclo de reintentos, y almacenamiento de `url_final` en metadatos.
     - En C++ (`cpp/include/pea/ingesta/extractor_url.hpp` y `cpp/src/ingesta/extractor_url.cpp`): se expuso la función pura `validar_redireccion(origen, location)`, se configuró `QNetworkRequest::ManualRedirectPolicy` y se implementó el bucle de seguimiento de hasta 3 saltos con validación por paso y registro de `url_final` en metadatos y en `MetadatosOrigen`.
  3. **Prueba real de solo lectura contra Minciencias SCIENTI:**
     - Se ejecutó consulta real contra los portales oficiales de GrupLAC (nro=00000000002099) y CvLAC (cod_rh=0000494917).
     - Ambos respondieron HTTP 200 con éxito, confirmando que la descarga responsable mantiene total compatibilidad con las fuentes institucionales vigentes.
- **Resultados de validación:**
  - `ruff check .`: Limpio (0 errores).
  - `pytest -m "not red"`: 383 aprobadas, 3 omitidas.
  - C++ build y CTest: 100% aprobado (64 casos doctest, 1087 aserciones).
  - `pea-cpp --autoprueba`: 0 hallazgos en 32 pantallas.
  - `pea-cli --autoprueba-gui`: 0 hallazgos en 24 combinaciones de pantalla.
  - `pea-cli --verificar-cruzada`: 3 de 3 comprobaciones coincidentes.

## Corrección 5: Filtrado de celdas de tipo/etiqueta en extracción HTML de CvLAC y paridad Python/C++

- **Problema:** En el fixture `tests/fixtures/scienti/cvlac_0000494917.html`, `parsear_cvlac` devolvía 52 artículos: 26 artículos reales y 26 registros espurios generados a partir de las filas que indican la categoría (`Producción bibliográfica - Artículo - Publicado en revista especializada`). Esto ocurría porque la tabla alterna filas de etiqueta con filas de cita y el filtro comprobaba únicamente si la cadena contenía `"Artículos"` (en plural con tilde), mientras que la etiqueta contiene la palabra en singular (`"Artículo"`). El mismo patrón se presentaba en C++ (`cpp/src/ingesta/parser_html.cpp`).
- **Acciones realizadas:**
  1. **TDD:**
     - En Python (`tests/unit/test_ingesta.py`), se escribió primero la prueba `test_parsear_cvlac_articulos_descarta_etiquetas_y_extrae_26_reales` verificando:
       - Extracción de exactamente 26 artículos reales.
       - Ningún artículo con título que inicie por `"Producción"`.
       - Cada artículo con su año extraído.
     - Se confirmó el fallo inicial (52 != 26) antes de modificar el código de producción.
     - En C++ (`cpp/tests/test_ingesta.cpp`), se añadió en el subcaso de CvLAC la verificación explícita de `CHECK(res_art.size() == 26)` y la comprobación de que ningún artículo comienza con `"Producción"`.
  2. **Implementación de filtrado:**
     - En Python (`src/pea/ingesta/extractor_url.py`): se implementó `_es_etiqueta_tipo_cvlac` para descartar celdas de encabezado/categoría (`Producción bibliográfica...`, `Producción técnica...`), se cambió la iteración de filas a `recursive=False` en celdas directas, y se aseguró la preservación de citas completas sin filtrar por `ano is not None`. Se verificó que las demás secciones de CvLAC y GrupLAC mantienen su estructura y que los conteos de `gruplac_00000000002099.html` se mantienen exactamente intactos: 85 integrantes, 93 artículos, 14 libros, 23 capítulos, 90 softwares, 151 trabajos dirigidos, 32 proyectos.
     - En C++ (`cpp/src/ingesta/parser_html.cpp`): se incorporó la función equivalente `es_etiqueta_tipo_cvlac` aplicada a las secciones de productos de CvLAC y GrupLAC.
  3. **Actualización de oráculo bajo Regla Común 4:**
     - Con autorización explícita del usuario, se actualizó `tests/fixtures/scienti/cvlac_0000494917.esperado.json` eliminando las 26 etiquetas espurias y conservando los 26 artículos reales.
- **Resultados de validación:**
  - `ruff check .`: Limpio (0 errores).
  - `pytest -m "not red"`: 384 aprobadas, 3 omitidas.
  - C++ build y CTest: 100% aprobado (64 casos doctest, 1087 aserciones).
  - `pea-cpp --autoprueba`: 0 hallazgos en 32 pantallas.
  - `pea-cli --autoprueba-gui`: 0 hallazgos en 24 combinaciones de pantalla.
  - `pea-cli --verificar-cruzada`: 3 de 3 comprobaciones coincidentes.
  - Artículos sin año en CvLAC fixture: 0 (todos los 26 artículos disponen de año válido en el rango 2008-2023).

## Corrección 6: Identificadores estables para productos CvLAC y conciliación segura en Supabase

- **Problema:** Los productos de CvLAC se identificaban originalmente mediante códigos posicionales volátiles (`PROD-CVLAC-{codigo_rh}-{posición de 4 dígitos}`). Al corregir el lector de HTML (eliminando 26 etiquetas espurias como artículos fantasma), las posiciones cambiaron: una re-importación crearía duplicados o asociaría artículos distintos bajo códigos viejos.
- **Acciones realizadas:**
  1. **TDD:**
     - Pruebas unitarias en Python (`tests/unit/test_ingesta.py`):
       - (a) `test_importar_dos_veces_cvlac_en_memoria_no_duplica_productos`: confirma idempotencia en memoria.
       - (b) `test_importar_cvlac_reconoce_producto_existente_con_codigo_antiguo_posicional`: comprueba que productos existentes con códigos antiguos posicionales (`PROD-CVLAC-0000494917-0002` o similares) no se duplican y son reutilizados sin modificar su código.
       - (c) `test_dos_citas_identicas_mismo_cv_reciben_codigos_distintos_y_estables`: verifica asignación determinista de sufijos `-2`, `-3` para citas repetidas dentro del mismo CV.
       - `test_paridad_codigo_estable_cvlac_con_tildes`: pruebas de paridad con 3 citas de ejemplo con tildes y caracteres especiales, verificando hashes exactos `9d80335576e1`, `d4966c27ca0c`, `998b196deec0`.
       - `test_normalizar_cita_y_generar_codigo_casos_borde`: casos borde de normalización Unicode (NFC vs NFD, espacios colapsados, mayúsculas, comillas tipográficas, fallback a título si la cita está vacía).
     - Pruebas unitarias en C++ (`cpp/tests/test_ingesta.cpp`):
       - Doctest `Paridad de hash y código estable de CvLAC con tildes`: 7 aserciones comprobando igualdad de caracteres hex contra Python.
       - Doctest `Casos borde de normalización y código CvLAC en C++`: normalización de espacios múltiples y tabulaciones, fallback a título.
  2. **Implementación de funciones puras de código estable:**
     - En Python (`src/pea/dominio/producto.py`): `normalizar_cita(cita)`, `calcular_hash_cita(cita)`, `generar_codigo_producto_cvlac(codigo_rh, cita, ocurrencia, titulo)`.
     - En C++ (`cpp/include/pea/dominio/producto.hpp`): funciones inline homólogas usando `QString::normalized(QString::NormalizationForm_C).toLower()` y `QCryptographicHash::Sha1`.
  3. **Lógica de deduplicación en la ingesta:**
     - En Python (`src/pea/ingesta/servicio_ingesta.py`) y C++ (`cpp/src/ingesta/servicio_ingesta.cpp`):
       - Genera el código estable con conteo de ocurrencias por cita normalizada.
       - Busca primero por el código estable en el catálogo.
       - Si no existe, busca entre los productos asociados al investigador (`obtener_productos_investigador`): primero por coincidencia de título existente contenido en la cita, luego por coincidencia de cita normalizada (`referencia_original` o `texto_completo`).
       - Si se encuentra un producto existente (antiguo), se reutiliza su código identificador para preservar su identidad, asociando el autor de forma idempotente tanto en memoria como en Supabase si `persistir=True`.
  4. **Herramienta de conciliación segura de códigos en base de datos:**
     - Creado `tools/db/reconciliar_codigos_cvlac.py` con pruebas en `tests/unit/test_reconciliacion_codigos_cvlac.py`.
     - Identifica códigos antiguos `PROD-CVLAC-{rh}-\d{4}` y calcula el código estable a partir de `referencia_original`.
     - Genera reporte CSV en `datos/respaldos/reconciliacion_codigos_cvlac_<timestamp>.csv` (`id,codigo_anterior,codigo_nuevo,estado`).
     - Protocolo estricto de seguridad para `--aplicar`:
       - Verifica existencia de respaldo JSON íntegro menor a 1 hora en `datos/respaldos/`.
       - Solicita confirmación textual `RECONCILIAR`.
       - Verifica conteos de `productos`, `producto_autores`, `producto_grupos` antes y después.
       - Flujo de revisión con reintentos acotados.
  5. **Ejecución y migración en base de datos real (Regla 5):**
     - Generado respaldo fresco `respaldo_20261023_130307_074023.json` (6,458 filas verificadas).
     - Simulación inicial en Supabase real: 1,293 productos antiguos encontrados, 1,293 listos para conciliar (`OK`), 0 `SIN_CITA`, 0 `COLISION`.
     - Ejecución de reconciliación con `--aplicar --confirmacion RECONCILIAR`:
       - 1,293 productos actualizados con éxito, 0 errores.
       - Conteos antes y después idénticos: Productos: 2352, Autores: 2356, Grupos: 1059. Integridad referencial 100% verificada.
  6. **Prueba de extremo a extremo:**
     - Creada herramienta `tools/db/simular_ingesta_oraculo.py`.
     - Carga el catálogo completo de la base real en memoria (2,352 productos, 291 investigadores, 4 grupos).
     - Simula la ingesta del fixture `cvlac_0000494917.html` con `persistir=False`.
     - Resultado: se reconocen los 26 artículos reales, 0 productos duplicados o creados (conteo en memoria: 2352 inicial == 2352 final), productos de otros tipos preservados intactos.

## Próximos pasos

Continuar con la resolución progresiva de los siguientes hallazgos de auditoría en la rama `fix/auditoria-2026-10-22` siguiendo estrictamente la metodología TDD.



