---
tipo: bitacora
estado: revisado
creado: 2026-10-19
actualizado: 2026-10-19
relacionado:
  - "[[2026-10-19-auditoria-integral-python-supabase]]"
  - "[[SPEC]]"
  - "[[Matriz-modelo-requisitos]]"
  - "[[GUI-Diseno-Python]]"
  - "[[Contrato-de-datos]]"
origen: "Auditoría complementaria local, de solo lectura, solicitada el 2026-10-19"
agente: "Copilot · auditoría complementaria"
rama: "feat/gui-inicio-graficos-copilot"
commit: "Commit local de esta bitácora; sin push"
---

# Bitácora · Auditoría complementaria Python PEA-i

## Objetivo y conclusión ejecutiva

Completar la evidencia de la auditoría previa, contrastar el estado local actual, recorrer el inventario de Python, revisar la trazabilidad de RF/RNF, ejecutar verificaciones locales seguras y dejar una relación explícita de lo cubierto y lo que sigue sin poder certificarse.

**Conclusión:** la auditoría complementaria amplía la evidencia, pero **no certifica que PEA-i esté listo ni cierra todas las lagunas solicitadas**. La suite Python vuelve a mostrar una prueba intermitente; Ruff informa 78 infracciones; no hay intérprete Python 3.12 ni mypy; hay requisitos sin prueba de aceptación; el modelo oficial completo y el corpus SCIENTI no se revisaron línea por línea; y no hubo interacción real de escritorio, conexión ni verificación de ACL en Supabase. No se corrigió código, pruebas, datos ni configuración.

## Estado Git y protección del estado local

- Rama: `feat/gui-inicio-graficos-copilot`.
- HEAD: `a3488c04dea486b1ab293701296d3ae4253a1619`.
- El commit de referencia comunicado (`f8beb26ce4f5d2997a5c90c414a675b7ee5b75aa`) es ancestro de HEAD. `git diff --name-status f8beb26...HEAD` muestra únicamente la adición del informe anterior; no hay cambios de código entre esa referencia y HEAD.
- `git status --short --untracked-files=all`, antes de esta nota: `M brain/.obsidian/graph.json`. Es un cambio local preexistente y **se dejó intacto**.
- No se cambió de rama, no se descartó trabajo, no se hizo push ni se usó el token compartido anteriormente.
- Los 24 PNG que el test GUI generó en `datos/capturas/oficiales/` durante la primera ejecución unitaria fueron identificados por nombre y fecha de esta ejecución y eliminados individualmente. Los otros 21 archivos preexistentes de esa carpeta se conservaron. La autoprueba dedicada posterior escribió solamente en un directorio temporal, que se eliminó.
- El archivo de esta bitácora es el único archivo nuevo permitido en el repositorio.

## Método y límites de privacidad

- No se abrió `.env`, no se leyó ni imprimió ninguna clave, no se autenticó contra Supabase y no se hizo ninguna petición a Supabase.
- No se ejecutaron `reiniciar_prueba.py`, `test_reset()`, limpiadores, sembradores, respaldos completos ni escrituras remotas. `sembrar.py`, `reiniciar_prueba.py`, `volcar.py`, `ping.py` y `respaldar.py` se inspeccionaron de forma estática; solo se invocó `descargar_tabla()` con `urlopen` reemplazado por un mock que devuelve HTTP 403 sintético.
- No se descargó nada de SCIENTI. Las pruebas con red continuaron excluidas.
- Las reproducciones nuevas usaron hosts `.invalid`, nombres/correos sintéticos y respuestas mock; no usaron datos reales.
- La inspección de patrones de privacidad contó coincidencias sin mostrar los valores encontrados. No se copiaron datos personales a esta nota.
- `scripts/verificar.ps1` no se ejecutó: invoca pruebas y compilación de C++, por lo que puede alterar artefactos de build. `scripts/restaurar.ps1` no se ejecutó: contiene una operación `git restore .`.

## Inventario y cobertura por ruta

### Código Python `src/pea/`

Se enumeraron **82 módulos `.py`** (dentro de 102 rutas rastreadas bajo `src/pea`, de las que las otras 20 son recursos). Los 82 se analizaron con AST y Ruff. La columna indica el nivel manual real: **F** = lectura focalizada de líneas/rutinas, no lectura integral; **A** = solo análisis automatizado, sin lectura manual completa de ese archivo. La evidencia automatizada común es `ast.parse` (124 archivos Python de `src/pea`, `tests`, `tools` y `scripts`, todos válidos) y Ruff (78 hallazgos en el conjunto analizado). No debe interpretarse la cobertura automatizada como revisión manual línea por línea.

| Ruta | Cobertura |
|---|---|
| `src/pea/__init__.py` | A |
| `src/pea/cli.py` | F |
| `src/pea/cliente_http.py` | F |
| `src/pea/excepciones.py` | A |
| `src/pea/version.py` | A |
| `src/pea/datos/__init__.py` | A |
| `src/pea/datos/repositorios.py` | F, también hallazgo previo |
| `src/pea/datos/revision.py` | F |
| `src/pea/datos/sesion.py` | F |
| `src/pea/dominio/__init__.py` | A |
| `src/pea/dominio/grupo.py` | A |
| `src/pea/dominio/integrante.py` | A |
| `src/pea/dominio/investigador.py` | F, también hallazgo previo |
| `src/pea/dominio/plan.py` | A |
| `src/pea/dominio/producto.py` | A |
| `src/pea/dominio/proyecto.py` | A |
| `src/pea/estructuras/__init__.py` | A |
| `src/pea/estructuras/cola.py` | A |
| `src/pea/estructuras/hipercubo.py` | A |
| `src/pea/estructuras/lista_doble.py` | F, también hallazgo previo |
| `src/pea/estructuras/multilista.py` | F, también hallazgo previo |
| `src/pea/estructuras/nodo.py` | A |
| `src/pea/estructuras/pila.py` | A |
| `src/pea/gui/__init__.py` | F |
| `src/pea/gui/__main__.py` | A |
| `src/pea/gui/ventana_principal.py` | F, autoprueba y geometría |
| `src/pea/gui/dialogos.py` | A |
| `src/pea/gui/ejecutor.py` | F |
| `src/pea/gui/estilo.py` | A |
| `src/pea/gui/formato.py` | A |
| `src/pea/gui/componentes/__init__.py` | A |
| `src/pea/gui/componentes/animacion.py` | A |
| `src/pea/gui/componentes/avatar.py` | A |
| `src/pea/gui/componentes/campo_busqueda.py` | A |
| `src/pea/gui/componentes/estado_vacio.py` | A |
| `src/pea/gui/componentes/ficha_lateral.py` | A |
| `src/pea/gui/componentes/filtro_anios.py` | A |
| `src/pea/gui/componentes/modelo_tabla.py` | A |
| `src/pea/gui/componentes/pildora.py` | A |
| `src/pea/gui/componentes/popover_historial.py` | A |
| `src/pea/gui/componentes/selector_segmentado.py` | A |
| `src/pea/gui/componentes/tabla.py` | A |
| `src/pea/gui/componentes/tarjeta.py` | A |
| `src/pea/gui/componentes/tarjeta_kpi.py` | A |
| `src/pea/gui/componentes/toast.py` | A, test intermitente relacionado |
| `src/pea/gui/componentes/graficos/__init__.py` | A |
| `src/pea/gui/componentes/graficos/barras_apiladas.py` | A |
| `src/pea/gui/componentes/graficos/base.py` | A |
| `src/pea/gui/componentes/graficos/dona_doble.py` | A |
| `src/pea/gui/componentes/graficos/mini_red.py` | A |
| `src/pea/gui/componentes/graficos/minigrafico.py` | A |
| `src/pea/gui/componentes/graficos/serie_anual.py` | A |
| `src/pea/gui/pantallas/__init__.py` | A |
| `src/pea/gui/pantallas/acerca.py` | A |
| `src/pea/gui/pantallas/configuracion.py` | A |
| `src/pea/gui/pantallas/grupos.py` | A |
| `src/pea/gui/pantallas/importar.py` | A |
| `src/pea/gui/pantallas/inicio.py` | A |
| `src/pea/gui/pantallas/investigadores.py` | A |
| `src/pea/gui/pantallas/productos.py` | A |
| `src/pea/gui/pantallas/redes.py` | A |
| `src/pea/gui/recursos/__init__.py` | A |
| `src/pea/gui/recursos/cargador.py` | A |
| `src/pea/gui/red/__init__.py` | A |
| `src/pea/gui/red/arista.py` | A |
| `src/pea/gui/red/disposicion.py` | A |
| `src/pea/gui/red/nodo.py` | A |
| `src/pea/gui/red/vista_red.py` | A |
| `src/pea/ingesta/__init__.py` | A |
| `src/pea/ingesta/extractor_pdf.py` | F |
| `src/pea/ingesta/extractor_url.py` | F |
| `src/pea/ingesta/lector_csv.py` | F |
| `src/pea/ingesta/modelos.py` | F |
| `src/pea/ingesta/servicio_ingesta.py` | F, también hallazgo previo |
| `src/pea/servicios/__init__.py` | A |
| `src/pea/servicios/datos_demostracion.py` | A |
| `src/pea/servicios/servicio_aplicacion.py` | F |
| `src/pea/servicios/servicio_dominio.py` | F, también hallazgos previos |
| `src/pea/servicios/servicio_estadisticas.py` | A |
| `src/pea/servicios/servicio_exportacion.py` | F |
| `src/pea/servicios/servicio_verificacion_cruzada.py` | F |
| `src/pea/servicios/vistas.py` | A |

### Recursos rastreados bajo `src/pea/` (no Python)

Inventariados por ruta; no se hizo revisión visual/licencia individual de todos ellos:

`gui/recursos/fuentes/Inter-Bold.ttf`, `Inter-ExtraBold.ttf`, `Inter-Medium.ttf`, `Inter-Regular.ttf`, `Inter-SemiBold.ttf`, `OFL.txt`; `gui/recursos/iconos/acerca.svg`, `buscar.svg`, `cerrar_sesion.svg`, `configuracion.svg`, `deshacer.svg`, `grupos.svg`, `importar.svg`, `inicio.svg`, `investigadores.svg`, `limpiar.svg`, `productos.svg`, `redes.svg`; `gui/recursos/logo_pea.svg`, `logo_upc.png`.

### Pruebas, herramientas, scripts y migraciones

- Se rastrearon 31 rutas bajo `tests`: 25 `.py` (todas participaron en la colección/ejecución de pytest) y 6 fixtures SCIENTI. Los 25 módulos de prueba son: `tests/conftest.py`; `tests/contrato/test_contrato_postgresql.py`; `tests/fuentes/test_extraer_scienti.py`; `tests/unit/test_cascadas.py`; `test_cli_gui.py`; `test_cliente_http.py`; `test_componentes_gui.py`; `test_deshacer.py`; `test_estructuras.py`; `test_estructuras_borde.py`; `test_estilo_recursos.py`; `test_graficos_seccion9.py`; `test_gui_completa.py`; `test_hipercubo.py`; `test_ingesta.py`; `test_pantalla_grupos.py`; `test_pantalla_inicio.py`; `test_pantalla_investigadores.py`; `test_pantalla_productos.py`; `test_pantalla_redes.py`; `test_pantallas_compactas.py`; `test_pantallas_finales.py`; `test_resiliencia_persistencia.py`; `test_servicios_nuevos.py`; `test_tabla_ficha_dialogos.py`. La suite se ejecutó; no se hizo una lectura manual exhaustiva de cada aserción.
- Los seis fixtures de `tests/fixtures/scienti/` se enumeraron y procesaron en las pruebas offline. Se evitó divulgar nombres/identificadores de sus archivos y su contenido. El escaneo de patrones se limita a conteos y no certifica anonimización.
- Herramientas Python inventariadas en `tools/`: `brain/verificar_brain.py`, `captura_directorio_tabla_ficha.py`, `db/comparar.py`, `db/ping.py`, `db/reiniciar_prueba.py`, `db/respaldar.py`, `db/sembrar.py`, `db/volcar.py`, `fuentes/descargar_scienti.py`, `fuentes/extraer_scienti.py`, `fuentes/modelos_scienti.py`, `galeria_graficos.py`, `galeria_gui.py`, `modelo/extraer_modelo.py`, `modelo/probar_completitud.py`, `modelo/procesar_modelo_2024.py`. También se inventarió `tools/requirements.txt`. Todos los `.py` entraron en AST/Ruff; se leyeron de forma focalizada los scripts de respaldo, sembrado, extracción SCIENTI y validación Obsidian. No se ejecutaron utilidades con efectos laterales.
- Scripts inventariados: `scripts/diagnostico_desborde.py`, `scripts/restaurar.ps1`, `scripts/verificar.ps1`. El restaurador se inspeccionó y no se ejecutó; el verificador se inspeccionó y no se ejecutó.
- Migraciones inventariadas y relacionadas con la auditoría previa: `supabase/migrations/20261003055532_001_esquema_inicial.sql` y `supabase/migrations/20261003061247_002_permisos_meta_y_ping.sql`. Los tests de contrato locales se ejecutaron; no certifican ACL ni estado remoto.

### Fuentes normativas y diseño

Se revisaron `AGENTS.md`, las siete reglas `.agent/rules/`, las skills pertinentes (PySide6, estructuras, seguridad, Supabase, fuentes SCIENTI, pruebas y flujo Git), SPEC, matriz, casos de uso, historias, variables de entrada/salida, preguntas abiertas, arquitectura, estructuras, modelo de dominio, contrato de datos, seguridad/credenciales, diseño GUI, decisiones de paridad, ingesta, hipercubo, multilista, pila, cola y los 17 ADR.

**Cobertura del Modelo Minciencias:** `docs/entrada/Modelo-2024.md` tiene 12.158 líneas, 716.618 caracteres y encabezados para 252 páginas. Se generó índice de todos los encabezados, y se leyeron focalmente páginas 41–43, 66–68, 115–119, 131–132, además de las notas organizadas del cerebro. **No se leyó línea por línea el texto completo de las 252 páginas**; las páginas restantes no se dan por revisadas. La copia `brain/40-Fuentes/Modelo-2024-original.md` tiene 12.174 líneas y hash distinto; no se comparó íntegramente para certificar fidelidad.

**Fuentes SCIENTI:** no se descargó ni se leyó línea por línea el conjunto de datos completo, páginas fuente, notas privadas ni HTML personal. Se inspeccionaron el mapa de campos público, rutas de generación, extractores y fixtures mediante pruebas locales y conteos sin valores. La revisión de datos personales queda limitada expresamente a esas comprobaciones.

## Matriz de requisitos y evidencia

La evidencia de pytest se refiere a la suite offline indicada abajo. “Parcial” significa que hay tests locales aprobados, pero no prueban todo el criterio de aceptación; “No demostrado” indica falta de evidencia segura o de cobertura. Los hallazgos previos F-01…F-15 se mantienen según la comparación de código.

| Requisito / punto | Evidencia revisada | Evaluación |
|---|---|---|
| RF-01 / R0 · revisión y concurrencia | `test_resiliencia_persistencia.py` incluye una simulación de conflicto; `src/pea/datos/revision.py` fue leído. F-01 demuestra fallback a revisión local ante lecturas no concluyentes y carrera remota no probada. No se usaron dos clientes contra Supabase ni se probó el sondeo periódico. | **No satisfecho / sin certificación remota.** |
| RF-02 / R1 · grupos | CRUD/cascadas y GUI se cubren parcialmente en pruebas locales; F-09 encuentra que asignar `lider` no crea/garantiza la membresía líder. El Modelo (p. 41) exige además condiciones de reconocimiento no expresadas por la aceptación actual. | **Parcial; requisitos normativos incompletos.** |
| RF-03 / R2 · investigadores | Tests de servicios, cascadas y GUI ejecutados; F-08 identifica `documento_identidad` en dominio sin columna correspondiente en migración. La lectura/consulta remota de membresías no se probó en base viva. | **Parcial; discrepancia de contrato.** |
| RF-04 / R3 · productos | Pruebas de validación e ingesta locales; F-04 acredita estados y años producidos por ingesta que no concuerdan con restricciones/criterios. Los tests no prueban aceptación de todas las subtipologías del Modelo ni su validación documental. | **No satisfecho para el flujo de ingesta; restante parcial.** |
| RF-05 / R4 · multilista | Pruebas de estructuras/cascadas ejecutadas; F-10 indica que no hay enlaces de producto por investigador y se recurre a recorrer productos. No se probó aceptación cruzada con una instancia remota. | **No satisfecho en la navegación por investigador.** |
| RF-06 / R5 · lista doble | `test_estructuras.py` y `test_estructuras_borde.py` ejecutados; F-11 confirma que `eliminar_nodo` no verifica pertenencia a la lista receptora. | **Parcial; caso de lista ajena falla.** |
| RF-07 / R6 · deshacer | `test_deshacer.py` y resiliencia local ejecutados; F-05 reproduce pérdida del comando al fallar la persistencia del inverso. No se prueba rollback transaccional contra PostgreSQL. | **No satisfecho ante fallo de persistencia.** |
| RF-08 / R7 · cola FIFO | `test_ingesta.py` incluye el ciclo de estados y que una tarea fallida no detenga la siguiente; se ejecutó sin red. No se certificaron rate-limit efectivo con varias peticiones ni comportamiento sostenido del hilo en Windows. | **Parcial; casos unitarios offline aprobados.** |
| RF-09 / R8 · hipercubo | `test_hipercubo.py` y pruebas de estadísticas ejecutadas. No se ejecutó prueba de carga hasta 10.000 productos ni comparación exhaustiva de celdas contra SQL; no hubo base de verificación disponible/permitida. | **Parcial; rendimiento y paridad sin evidencia.** |
| RF-10 / R9 · estadísticas | Tests verifican resultados de servicios con datos locales. La búsqueda estática no encontró implementación de pesos/ponderaciones ni de `cumple_existencia`/`cumple_calidad` en `src/pea`; no hay prueba oráculo SQL para todas las dimensiones ni medición <50 ms. | **Parcial; no certifica cálculos completos del Modelo.** |
| RF-11 / R10 · GUI Python | Suite offscreen y autoprueba recorrieron 8 vistas en 3 resoluciones. La autoprueba dio 14 advertencias de widgets fuera; el estado final fue 0 porque dichas advertencias no son fallas. No se compararon capturas con referencias ni se hizo interacción real de Windows, contraste sistemático o prueba integral de teclado/foco. | **Parcial; geometría visual no certificada.** |
| RF-12 / R11 · persistencia atómica | Tests de compensación usan mocks. F-02 documenta edición compuesta con varias solicitudes REST; F-06 respuestas de alta vacías; F-07 cálculo local de revisión no alineado con triggers. No se hicieron escrituras remotas. | **No satisfecho para transacciones compuestas; remoto sin probar.** |
| RF-13 / R12 · ingesta | `test_ingesta.py` y `test_extraer_scienti.py` ejercitan fixtures offline. Las dos pruebas de red permanecieron excluidas; F-04 y F-19/F-20 identifican validación y privacidad insuficientes. | **Parcial; extracción real prohibida por alcance.** |
| RNF-01 / C1 · estructuras propias | AST/Ruff cubrieron los 82 módulos, pero no se ejecutó un verificador exhaustivo de cada atributo de cada servicio; F-10/F-11 son contraejemplos de semántica/integridad. | **No certificado.** |
| RNF-02 / C2 · paridad Python/C++ | No se ejecutó CTest/build, no se compararon flujos/valores equivalentes y el diseño declara que la GUI C++ aún no sigue la GUI Python. | **No demostrado.** |
| RNF-03 / C3 · estadísticas en hipercubo | Los tests locales pasan para escenarios concretos; no se instaló interceptor para certificar cero HTTP en todas las métricas. F-25 amplía la brecha de modelo/pesos. | **Parcial.** |
| RNF-04 / C4 · seguridad/Supabase | Código estático, tests mock y hallazgos F-16/F-17/F-19/F-20. No se validó TLS 1.3 efectivo, autenticación, RLS, funciones/ACL ni secretos del entorno. No se usó la credencial compartida. | **No certificado; hay vulnerabilidades de cliente.** |
| RNF-05 / C5 · calidad/idioma/pruebas offline | Ruff = 78 hallazgos; Python 3.12 y mypy no disponibles; suite con un fallo intermitente; `scripts/verificar.ps1` no se ejecutó. Dos tests `red` se excluyeron como corresponde. | **No satisfecho.** |
| RNF-06 / C6 · borrado y reversibilidad | El flujo lógico/físico tiene pruebas, pero F-05 demuestra que undo no conserva el comando tras ciertos errores; F-03 no tiene ACL efectiva comprobada. | **No satisfecho / sin certificación remota.** |

## Verificaciones ejecutadas

### Versiones y herramientas

- `py -0p`: únicamente `Python314` global en `C:\Users\frani\AppData\Local\Programs\Python\Python314\python.exe`.
- `python --version`: `Python 3.14.7`.
- `.venv\Scripts\python.exe --version`: `Python 3.14.6`.
- `py -3.12 --version`: `No suitable Python runtime found`, código de salida 103. No se alteró Python global, no se instaló un runtime y `uv` no está disponible.
- Paquetes de `.venv`: pytest 9.1.1; pytest-qt 4.5.0; PySide6 6.11.2; Ruff 0.16.10; Pydantic 2.13.5; requests 2.34.2; BeautifulSoup 4.15.0; lxml 6.1.3; pdfplumber 0.11.10.
- `mypy` no está instalado (ejecutable ausente y `python -m mypy` devuelve “No module named mypy”). `pytest-cov` no está instalado, por lo que no se obtuvo porcentaje de cobertura de líneas.

### AST, Ruff y Pylance

1. AST, sin importar módulos ni generar bytecode:

   ```powershell
   $env:PYTHONDONTWRITEBYTECODE='1'
   # ast.parse sobre src/pea, tests, tools y scripts
   ```

   Resultado: **124 archivos `.py`, 124 parseados, 0 errores de sintaxis**.

2. Linter:

   ```powershell
   .venv\Scripts\ruff.exe check --no-cache --statistics src\pea tests tools scripts
   ```

   Resultado: **código 1; 78 errores**: 37 UP045, 17 UP006, 6 UP015, 5 I001, 4 F401, 3 W293, 2 UP017, 2 F541, 1 UP035 y 1 F841. 76 se marcaron como auto-corregibles; no se aplicaron.

3. Diagnóstico Pylance del workspace guardado y resumido: **48 archivos, 205 diagnósticos (127 severidad error, 0 warning)**. Los códigos identificados suman 127: `reportOptionalMemberAccess` 76, `reportAttributeAccessIssue` 22, `reportArgumentType` 18, `reportCallIssue` 4, `reportOptionalSubscript` 4 y `reportReturnType` 3; los otros 78 diagnósticos no traen código. Esos diagnósticos requieren triage; no se trataron automáticamente como fallos de runtime.

4. Validador de bóveda, sin `--restaurar`:

   ```powershell
   $env:PYTHONDONTWRITEBYTECODE = '1'
   .venv\Scripts\python.exe tools\brain\verificar_brain.py
   ```

   Resultado tras crear y normalizar esta nota: **126 notas inspeccionadas, 0 errores, 0 advertencias, código 0**. La bitácora quedó en UTF-8 sin BOM, finales LF y sin espacios finales.

### Suite unitaria

La primera invocación contenía `$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='0'`; pytest interpreta cualquier valor no vacío como desactivación del autoload, generó errores de setup por fixtures como `qtbot` y se descartó como ejecución inválida. La repetición corrigió esa variable y eliminó del proceso las variables `PEA_SUPABASE_*` y `PEA_USUARIO_*` sin leer sus valores.

Comando efectivo:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
Remove-Item Env:PYTEST_DISABLE_PLUGIN_AUTOLOAD -ErrorAction SilentlyContinue
# Remove-Item Env: para las variables PEA_SUPABASE_* y PEA_USUARIO_*
.venv\Scripts\python.exe -m pytest -p no:cacheprovider -m 'not red' -q -ra tests
```

Resultado: **236 passed, 1 failed, 2 deselected, 104.76 s, código 1**. El fallo fue `tests/unit/test_componentes_gui.py::test_toasts_consecutivos_se_conservan_al_interactuar_y_cambiar_pantalla`; los dos tests de red excluidos fueron `tests/unit/test_ingesta.py::test_conexion_real_scienti_red` y `tests/contrato/test_contrato_postgresql.py::test_ping_remoto_supabase`.

Repetición aislada:

```powershell
.venv\Scripts\python.exe -m pytest -p no:cacheprovider -m 'not red' -q tests\unit\test_componentes_gui.py::test_toasts_consecutivos_se_conservan_al_interactuar_y_cambiar_pantalla
```

Resultado: **1 passed en 1.19 s, código 0**. La diferencia confirma intermitencia, no la causa. No se marca la suite como verde.

### GUI offscreen

Se ejecutó `.venv\Scripts\python.exe -m pea.gui --autoprueba` con `QT_QPA_PLATFORM=offscreen`, `PYTHONPATH` apuntando a `src`, credenciales PEA eliminadas del proceso y CWD temporal. Resultado: **código 0, 24 capturas, 8 vistas × 3 tamaños (1100×700, 1366×768, 1920×1080)**. Hubo **14 advertencias** (suma de 402 geometrías de widgets reportadas fuera del rectángulo de la ventana); no se informó barra horizontal visible. La rutina solo retorna fallo cuando encuentra barras horizontales y no falla por `fuera`; por eso el código 0 **no prueba ausencia de recortes**. Las capturas temporales se eliminaron.

Esto es una prueba Qt **offscreen**, no una sesión de escritorio real de Windows ni una comparación visual con las referencias.

### Reproducciones locales sintéticas

- **URL Supabase:** `ServicioAplicacion._validar_parametros_conexion("https://attacker.invalid", "publishable-placeholder")` terminó aceptando el host. No hubo conexión.
- **CSV:** `_celda_csv("=1+1")` devolvió `'=1+1'`.
- **Redirección SCIENTI:** `requests.get` se sustituyó por un mock que devolvía `response.url=https://other.invalid/internal`. El extractor no estableció `allow_redirects=False`, no comprobó la URL final y guardó el cuerpo sintético.
- **Anonimización:** con un registro sintético de CvLAC y `anonimizar=True`, Markdown quedó enmascarado pero JSON y CSV conservaron el nombre sintético. La función de texto eliminó el correo sintético, pero dejó nombre y teléfono sintéticos.
- **Respaldo:** `descargar_tabla()` con `urlopen` mock HTTP 403 devolvió `[]` como si fuera tabla vacía. No se ejecutó `respaldar()` ni se creó archivo de respaldo.
- **CLI JSON:** con un catálogo sintético cuya recarga lanza error, `comando_resumen(salida_json=True)` devolvió código 0 y JSON válido con ceros, sin aviso.
- **Privacidad de artefactos SCIENTI:** escaneo local sin emitir valores: 2 líneas con patrón de correo y 18 con identificadores numéricos largos en `brain/40-Fuentes/publicado/`; 1 y 98, respectivamente, en los seis fixtures de `tests/fixtures/scienti/`. Son indicadores, no certificación de identidad; los valores no se imprimieron.

## Hallazgos adicionales

Los hallazgos siguientes son adicionales a F-01…F-15. La severidad expresa impacto potencial, no prueba de explotación remota. Ninguna reproducción abrió conexiones externas.

### F-16 · Host de Supabase sin allowlist: posible envío de credenciales a destino arbitrario

- **Severidad / confianza:** Alta / 9 de 10.
- **Ruta:** `src/pea/servicios/servicio_aplicacion.py:187-195`.
- **Evidencia:** la validación comprueba `startswith("https://")`, existencia de clave y rechazo de clave secreta, pero no restringe hostname a Supabase ni a un host esperado. `conectar()` usa después esa URL para construir el cliente y, si se introduce correo/contraseña, autentica contra ella.
- **Reproducción:** la llamada sintética indicada arriba aceptó `https://attacker.invalid`; no se conectó. En una configuración así, la petición de autenticación puede enviar la contraseña del usuario al destino introducido.
- **Impacto:** exposición de credenciales de cuenta si el URL se manipula por configuración, error de entrada o intermediario. La clave publishable no es el secreto principal en este escenario; la contraseña sí.
- **Criterio de aceptación:** rechazar todo hostname que no pertenezca al proyecto Supabase autorizado (y validar estructura URL/puerto/path), con tests para hosts falsos, userinfo, puerto y esquema; probar que autenticación nunca entrega la contraseña a otro host.
- **Relación F-01…F-15:** nuevo; no sustituye un hallazgo anterior.

### F-17 · Redirección HTTP puede evadir el allowlist de SCIENTI

- **Severidad / confianza:** Media / 8 de 10.
- **Ruta:** `src/pea/ingesta/extractor_url.py:78-86, 96-141`.
- **Evidencia:** `validar_url()` permite inicialmente solo HTTPS y el host exacto SCIENTI; `requests.get()` usa el comportamiento por defecto que sigue redirecciones y no se verifica que `resp.url` permanezca en el host permitido.
- **Reproducción:** el mock sintético dirigido a una ruta SCIENTI devolvió una URL final externa; el cuerpo se aceptó y se almacenó en caché sin validación de URL final.
- **Impacto:** se rompe la restricción de host de la política de extracción; un redirect externo puede hacer que el programa descargue y procese contenido ajeno (y, según el redirector, abrir un vector SSRF de solo lectura).
- **Criterio de aceptación:** no seguir redirecciones o validar cada salto y URL final contra HTTPS/host permitido; test con redirect externo sin tráfico real.
- **Relación F-01…F-15:** nuevo.

### F-18 · Exportación CSV vulnerable a inyección de fórmulas

- **Severidad / confianza:** Media / 9 de 10.
- **Ruta:** `src/pea/servicios/servicio_exportacion.py:12-17, 26-37`.
- **Evidencia:** `_celda_csv()` convierte valores a cadena sin neutralizar prefijos interpretables por hojas de cálculo (`=`, `+`, `-`, `@`, incluidos prefijos con espacios/control).
- **Reproducción:** `_celda_csv("=1+1")` devuelve `'=1+1'`.
- **Impacto:** al abrir con Excel u otra hoja de cálculo un CSV que contiene datos editables/importados, celdas pueden interpretarse como fórmulas.
- **Criterio de aceptación:** neutralizar conforme a una política CSV segura y verificar por exportación real sintética el contenido resultante para cada prefijo peligroso, conservando la importación de datos legítimos.
- **Relación F-01…F-15:** nuevo.

### F-19 · La opción de anonimización no se aplica a JSON/CSV ni a todos los textos

- **Severidad / confianza:** Media / 9 de 10.
- **Ruta:** `src/pea/ingesta/extractor_url.py:59-64, 682-720, 778-857`.
- **Evidencia:** el texto Markdown se enmascara en partes del parser, pero `procesar_url()` serializa el modelo original con `model_dump_json()` y genera CSV canónico sin parámetro de anonimización. En CvLAC el nombre original permanece en el modelo Pydantic; además, `es_privado` selecciona carpeta solamente para el Markdown. La función genérica de anonimización solo reemplaza correos, no nombres o teléfonos en texto libre.
- **Reproducción:** con una persona sintética y `anonimizar=True`, el Markdown resultó enmascarado mientras el JSON y CSV del directorio de salida conservaron el nombre sintético; una entrada de texto libre conservó nombre y teléfono.
- **Impacto:** la opción “anonimizar” puede dejar identificadores personales en archivos estructurados que quedan junto a la salida publicada o se comparten/commitean.
- **Criterio de aceptación:** una prueba con datos sintéticos debe verificar que cada salida generada (Markdown, JSON, CSV e informe), también en `es_privado=False`, no contiene campos personales protegidos; o la herramienta debe separar explícitamente los artefactos privados con una política inequívoca.
- **Relación F-01…F-15:** nuevo, relacionado temáticamente con F-04 (ingesta), pero causa distinta.

### F-20 · Posibles datos personales en fuentes y fixtures publicados

- **Severidad / confianza:** Media / 7 de 10.
- **Rutas:** `tools/fuentes/extraer_scienti.py:44-51, 619-620, 690-691`; `brain/40-Fuentes/publicado/SCIENTI-Mapa-de-campos.md:32,43,45`; `tests/fixtures/scienti/` (6 archivos).
- **Evidencia:** `anonymize_text()` reemplaza correos pero no nombres ni identificadores; el generador aplica esa función al HTML antes de guardarlo como fixture. Las notas bajo `publicado` contienen filas de campos identificativos; el escaneo silencioso encontró patrones de correo/identificadores en las notas y fixtures.
- **Reproducción:** revisión estática del generador y escaneo local que solo imprimió conteos (2 líneas con patrón de correo y 18 con secuencias numéricas largas en las notas publicadas; 1 y 98 en fixtures). No se imprimieron valores y no se puede asegurar solo por regex qué coincidencias son datos reales.
- **Impacto:** persistencia versionada de posibles datos identificables contraria al requisito de minimización/anonimización. La visibilidad del repositorio no se comprobó.
- **Criterio de aceptación:** sustituir datos por fixtures sintéticos y escanear archivos versionados con un proceso de privacidad que no imprima valores; revisión autorizada de los pocos casos dudosos antes de publicar. No poner valores personales en la bitácora.
- **Relación F-01…F-15:** nuevo; relacionado con F-04 por los flujos de ingesta, pero no es duplicado.

### F-21 · El seeder informa éxito pese a respuestas HTTP de error

- **Severidad / confianza:** Media / 9 de 10 (estática).
- **Ruta:** `tools/db/sembrar.py:89-126`.
- **Evidencia:** errores HTTP de los POST de grupo e investigadores se capturan y se reportan como `[INFO]`; después el programa imprime finalización satisfactoria y retorna 0 sin comprobar cuántas inserciones se confirmaron.
- **Reproducción:** no ejecutada: está prohibido ejecutar el seeder en esta auditoría. La ruta estática de dos respuestas HTTP 4xx conduce al mensaje final y código 0.
- **Impacto:** automatización/usuario puede interpretar una siembra incompleta o rechazada como exitosa.
- **Criterio de aceptación:** acumular resultado por entidad, devolver código no cero si una mutación no se confirma y diferenciar duplicado idempotente de error; pruebas con `urlopen` mockeado sin red.
- **Relación F-01…F-15:** patrón relacionado con F-12 (falso éxito de limpieza), pero herramienta y operación diferentes.

### F-22 · El respaldo puede ser parcial y terminar como éxito

- **Severidad / confianza:** Media / 9 de 10.
- **Ruta:** `tools/db/respaldar.py:77-118,121-155`.
- **Evidencia:** 401/403/404 se convierten en lista vacía y otros errores de tabla también cortan la descarga sin hacer fallar `respaldar()`. El flujo agrega ese resultado, escribe el JSON y retorna 0 con “Respaldo completado exitosamente”.
- **Reproducción:** `descargar_tabla()` con HTTP 403 sintético devolvió una lista vacía; el flujo padre no conserva un estado de error por tabla. El respaldo completo no se ejecutó por su efecto de escritura y lectura de configuración.
- **Impacto:** archivo incompleto puede considerarse respaldo válido y no servir para recuperación.
- **Criterio de aceptación:** salida de respaldo debe registrar éxito solo si todas las tablas se descargaron o se justificaron expresamente como inexistentes; errores RLS/red deben hacer el estado final no exitoso y quedar legibles por máquina.
- **Relación F-01…F-15:** nuevo; patrón análogo a F-12.

### F-23 · CLI JSON puede presentar un catálogo obsoleto como éxito

- **Severidad / confianza:** Media / 9 de 10.
- **Ruta:** `src/pea/cli.py:129-143`; exportación relacionada en `272-283`.
- **Evidencia:** si `recargar_todo()` falla, `comando_resumen()` solo imprime el aviso cuando no es JSON. En modo JSON emite `resumen_json()` del catálogo local y devuelve 0. `comando_exportar_csv()` también advierte por un fallo remoto y continúa escribiendo el catálogo local.
- **Reproducción:** mock de catálogo sintético con `recargar_todo()` que lanza `RuntimeError`: `comando_resumen(True)` retornó 0 y emitió JSON válido con conteos cero, sin aviso.
- **Impacto:** scripts consumidores pueden tratar estado vacío/obsoleto como información remota actual.
- **Criterio de aceptación:** ante fallo de recarga, JSON debe contener estado explícito de error/obsoleto y el proceso devolver un código distinto de 0, o requerir una opción explícita para permitir datos locales; mismo contrato para exportar.
- **Relación F-01…F-15:** nuevo; conexo con F-01 por fallos de lectura, no duplicado.

### F-24 · La autoprueba GUI no hace fallar la aceptación por widgets fuera de ventana

- **Severidad / confianza:** Baja / 9 de 10 (brecha de prueba).
- **Ruta:** `src/pea/gui/ventana_principal.py:1382-1406`.
- **Evidencia:** las geometrías fuera se imprimen como `[AUTOPRUEBA] ADVERTENCIA`; el código de salida solo pasa a 3 si hubo barras horizontales. La ejecución reportó 14 grupos de advertencias, pero salida 0.
- **Reproducción:** ejecución offscreen en tres tamaños, 24 capturas temporales, 14 advertencias (402 instancias de widgets) y código 0. La detección también puede contar widgets dentro de áreas de desplazamiento; no prueba por sí sola que los píxeles visibles estén recortados.
- **Impacto:** criterio GUI de “sin recortes ni desbordes” no está impuesto por la autoprueba; salida exitosa no es evidencia suficiente de ese criterio.
- **Criterio de aceptación:** pruebas geométricas que midan el área realmente visible (considerando viewports/scroll areas) y fallen solo ante desbordes visibles; revisar capturas contra referencias a los tres tamaños y registrar resultado.
- **Relación F-01…F-15:** amplía F-13 y F-15; no confirma por sí sola cada defecto visual previo.

### F-25 · No hay evidencia de implementación de ponderaciones/validación completa del Modelo

- **Severidad / confianza:** Media / 8 de 10 como brecha de alcance/evidencia.
- **Rutas:** `docs/entrada/Modelo-2024.md:1965-2029,5348-5453,6182-6265`; `brain/10-Requisitos/SPEC.md:50-99,169-203`; `src/pea/` (búsqueda estática de `peso_relativo`, `peso_global`, `cumple_existencia`, `cumple_calidad`).
- **Evidencia:** las páginas fuente consultadas definen requisitos de existencia del grupo, ventana general de cinco años con excepciones por producto, pesos globales/relativos y criterios de existencia/calidad. RF-02/RF-04/RF-09/RF-10, en cambio, describen principalmente conteos, tres estados internos de validación y criterios acotados; la búsqueda en el código no encontró los campos/algoritmos de ponderación y existencia/calidad.
- **Reproducción:** contraste estático entre páginas/citas del Modelo y SPEC/código; no se ejecutó un benchmark normativo ni una clasificación de convocatoria.
- **Impacto:** con la evidencia actual no se puede afirmar que los resultados de PEA-i repliquen el cálculo/categorización oficial Minciencias. El alcance podría ser intencionalmente analítico y más acotado, pero no queda demostrado ni cerrado frente a la fuente de verdad.
- **Criterio de aceptación:** definir formalmente qué indicadores del Modelo quedan fuera del alcance; para los incluidos, añadir casos oráculo con fórmulas, ventanas por producto, pesos, existencia/calidad y resultados esperados trazables a páginas del original. No inferir valores ausentes.
- **Relación F-01…F-15:** nuevo; se conecta con F-04 y F-08 en la necesidad de alinear dominio, requisitos y esquema, pero no los reemplaza.

## Relación de F-01…F-15 del informe previo

No se descartó ningún hallazgo anterior porque el código no cambió desde la revisión indicada. Los que no se reejecutaron se marcan como persistentes según evidencia previa, no como recién reproducidos. La bitácora anterior es [[2026-10-19-auditoria-integral-python-supabase]].

| Hallazgo previo | Estado complementario |
|---|---|
| F-01 revisión/race y fallback | Persiste según código/evidencia previa; revisión local de `revision.py`; sin servidor concurrente ni ACL remota. |
| F-02 atomicidad de edición | Persiste; no se ejecutó escritura ni simulación nueva multi-tabla remota. |
| F-03 alcance/ACL de limpieza | Persiste como riesgo SQL; privilegios efectivos siguen no verificados y limpiador no ejecutado. |
| F-04 validación de ingesta | Persiste; no se descargó SCIENTI. F-19 agrega riesgo de anonimización en salidas. |
| F-05 pérdida del undo | Persiste; no se volvió a provocar fallo remoto. |
| F-06 respuesta vacía en altas | Persiste según evidencia previa; sin Supabase remoto. |
| F-07 revisión tras creación producto | Persiste; trigger remoto no fue ejercitado. |
| F-08 dominio/esquema | Persiste; contrato local ejecutado, sin alterar migraciones. |
| F-09 líder no ligado a membresía | Persiste según evidencia previa; sin cambio de código. |
| F-10 multilista sin índice de productos por investigador | Persiste; tests de estructura pasaron, no refutan el defecto semántico. |
| F-11 eliminación de nodo ajeno | Persiste; test estructural existente no corrige la precondición. |
| F-12 falso éxito del reinicio Python | Persiste; herramienta no ejecutada. F-21/F-22 documentan patrones en otros scripts. |
| F-13 defectos GUI a 1100×700 | Se hizo autoprueba offscreen; hay advertencias, pero no prueba visual de clipping ni revisión de escritorio. No se descarta. |
| F-14 test de toast dependiente del orden | Reproducido: suite completa falla y ejecución aislada pasa. Causa sin determinar. |
| F-15 cobertura débil de contrato/paginación | Persiste; suite pasa esos tests, pero siguen siendo pruebas locales/mock y no acreditan integración real. |

## Limitaciones y evidencia pendiente

1. No lectura línea por línea de los 12.158 renglones del Modelo ni de las fuentes SCIENTI; solo índice completo de sus 252 encabezados y revisión focalizada de páginas citadas.
2. No inspección de cada instrucción en los 82 módulos: todos tuvieron AST/Ruff; los marcados A no recibieron lectura manual completa. Tampoco se leyó exhaustivamente cada test ni cada uno de los 16 scripts/herramientas.
3. No se comprobó Python 3.12, mypy, porcentaje de cobertura, compilación C++/CTest ni `scripts/verificar.ps1`.
4. No se conectó a Supabase: RLS, ACL de funciones, estado de migraciones aplicadas, TLS real, límites/paginación efectiva y consistencia multiusuario siguen sin prueba.
5. No se inspeccionó `.env`, no se usó la credencial compartida y no se escanearon valores de variables de entorno.
6. No hubo interacción real de escritorio Windows ni comparación visual con referencias; offscreen no sustituye a esa prueba.
7. La privacy scan es una señal por patrones, no un análisis autorizado de identidad. Las fuentes/fixtures con datos sensibles requieren revisión segura fuera de esta nota.
8. Las seis preguntas abiertas en `Preguntas-abiertas.md` sobre cohesión/cooperación, cascadas, ventanas, validación inicial, CSV y autenticación permanecen como decisiones/assumptions pendientes de cierre.

## Archivos modificados

- Nuevo: esta bitácora complementaria.
- Sin cambios en código, pruebas, migraciones o datos.
- Cambio preexistente preservado: `brain/.obsidian/graph.json`.
- Los artefactos temporales de capturas de esta sesión fueron eliminados individualmente; no se alteraron los otros archivos de captura preexistentes.

## Siguiente paso de auditoría (sin reparar en esta tarea)

Resolver primero la prueba intermitente y las discrepancias de persistencia ya descritas; ejecutar la validación de Python 3.12 en un entorno aislado cuando esté disponible; y preparar evidencias autorizadas para los criterios normativos pendientes. Para Supabase, la comprobación de ACL/estado debe realizarla el usuario con credenciales rotadas y una consulta de solo lectura aprobada; esta auditoría no las usa. No declarar PEA-i listo hasta que cada RF/RNF tenga evidencia de aceptación y se cierre el alcance del Modelo.
