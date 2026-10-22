---
tipo: bitacora
estado: revisado
creado: 2026-10-19
actualizado: 2026-10-19
relacionado:
  - "[[SPEC]]"
  - "[[Modelo]]"
  - "[[Arquitectura]]"
  - "[[Contrato-de-datos]]"
  - "[[Seguridad-y-credenciales]]"
  - "[[GUI-Diseno-Python]]"
origen: "Auditoria local de Python, migraciones Supabase y requisitos; solo lectura"
agente: "Copilot"
rama: "feat/gui-inicio-graficos-copilot"
commit: "f8beb26ce4f5d2997a5c90c414a675b7ee5b75aa (revision auditada)"
---

# Bitacora · Auditoria integral Python y Supabase

## Objetivo

Evaluar, en modo de solo lectura, la aplicacion Python/PySide6, las migraciones locales de Supabase/PostgreSQL y su correspondencia con los requisitos del proyecto. Identificar riesgos de integridad, persistencia, estructuras, importacion, GUI y pruebas, sin corregir codigo ni modificar datos remotos.

## Resumen ejecutivo

- **Resultado:** auditoria local parcial. Se hallaron defectos concretos de consistencia, atomicidad, deshacer, integracion de productos, limpieza de datos de ejemplo y adaptacion de la GUI.
- **Cambios de aplicacion:** ninguno. El unico archivo nuevo de esta tarea es este informe.
- **Supabase:** no se establecio conexion, no se usaron credenciales y no se ejecutaron lecturas, escrituras, RPC ni migraciones remotas. Por tanto, no se afirma que el esquema o las ACL locales coincidan con el estado efectivo del proyecto remoto.
- **Pruebas:** la compilacion sintactica Python termino correctamente; la suite completa tuvo 236 pruebas aprobadas, 1 fallida y 2 excluidas. La prueba fallida pasa al ejecutarse sola, por lo que su dependencia del orden no tiene causa demostrada.
- **Prioridad:** atender primero el control atomico de revision, las actualizaciones compuestas de producto y la limpieza de datos de prueba. Despues, corregir la perdida de comandos al deshacer, los valores invalidos de ingesta y los desacuerdos dominio/esquema.
- **Credenciales:** el valor compartido en la conversacion no se utilizo ni se copio al repositorio. Si corresponde a una credencial activa, revocarla y generar otra es la medida prudente. `.env` no se leyo; `.env.example` solo se verifico de forma redactada y contenia nombres de variables con valores vacios o marcadores.

## Alcance y metodo

### Revision realizada

- Estado Git, rama `feat/gui-inicio-graficos-copilot`, revision auditada `f8beb26ce4f5d2997a5c90c414a675b7ee5b75aa` y estado previo del arbol.
- Contrato del proyecto, `SPEC.md`, matriz de trazabilidad, variables de entrada/salida, preguntas abiertas y reglas locales pertinentes.
- ADR de persistencia/compensacion, RPC/control de revision, limites de ingesta, autenticacion/RLS, proyecto Supabase unico, tecnologia y alcance visual.
- Modulos Python de repositorios, cliente HTTP, revision, servicios, dominio, estructuras, ingesta y pantallas relevantes; migraciones locales y script de reinicio de pruebas.
- Pruebas unitarias y de contrato, linters, compilacion sintactica y autoprueba visual offscreen en tres resoluciones.
- Sondeos sinteticos, sin red, para revision remota vacia, respuesta vacia de alta, fallo al deshacer y eliminacion de un nodo ajeno a una lista.

### Limites

- No se hizo una lectura linea por linea de los 82 modulos Python, todas las pruebas, todo el documento normativo original ni todas las fuentes SCIENTI. No se inspeccionaron datos personales de integrantes ni se abrio `.env`.
- La auditoria no cubre la implementacion C++; tampoco se ejecuto `scripts/verificar.ps1`, porque incluye la compilacion y pruebas de C++.
- No se ejecutaron pruebas marcadas `red`, no se accedio al proyecto `pea-prod`, ni se comprobaron ACL efectivas, politicas RLS instaladas, triggers efectivos, usuarios, datos o estado de migraciones remotas.
- Los resultados de esquema describen exclusivamente las migraciones versionadas localmente; no prueban el esquema desplegado.
- La matriz de requisitos es una evaluacion de evidencia muestreada, no una certificacion de cumplimiento exhaustivo.

## Hallazgos priorizados

| ID | Prioridad | Hallazgo | Confianza | Referencias principales |
|---|---|---|---|---|
| F-01 | Alta | El control de revision no es atomico y puede aceptar escrituras concurrentes con una revision obsoleta. | Alta | `src/pea/datos/revision.py:23-40`; migracion `20261003055532_001_esquema_inicial.sql:354-356` |
| F-02 | Alta | Editar un producto y sus relaciones puede dejar cambios parciales en el servidor. | Alta | `src/pea/servicios/servicio_dominio.py:564-615`; `src/pea/datos/repositorios.py` |
| F-03 | Alta | El RPC de limpieza puede borrar todas las membresias de ejemplo, no solo las de prueba con prefijo. Su permiso efectivo remoto no esta comprobado. | Alta para el alcance del borrado; media para explotabilidad remota | Migracion `20261003055532_001_esquema_inicial.sql:484-525,568` |
| F-04 | Alta | La ingesta crea productos con un estado rechazado por el `CHECK` SQL y sustituye anos faltantes por 2024. | Alta | `src/pea/ingesta/servicio_ingesta.py:202-203,240-241`; migracion `:117-126` |
| F-05 | Media | Se desapila el comando de deshacer antes de persistir; ante un error se pierde la accion recuperable. | Alta | `src/pea/servicios/servicio_dominio.py:738-788` |
| F-06 | Media | Las altas REST aceptan una respuesta vacia como exito y pueden dejar entidades locales sin ID remoto. | Alta | `src/pea/datos/repositorios.py:32-37,80-85`; `src/pea/cliente_http.py:156-175` |
| F-07 | Media | La revision local aumenta en uno aunque la creacion RPC de producto dispare varios incrementos por las relaciones. | Alta | `src/pea/servicios/servicio_dominio.py:507-548`; migracion `:254-287,365-385` |
| F-08 | Media | El modelo Investigador expone `documento_identidad`, pero la tabla de la migracion no tiene esa columna; hay mas diferencias de opcionalidad. | Alta | `src/pea/dominio/investigador.py:8-20`; migracion `:71-92` |
| F-09 | Media | El alta de Grupo guarda el nombre del lider, pero no crea ni garantiza la membresia de ese lider. | Alta | `src/pea/servicios/servicio_dominio.py:75-112`; migracion `:57-107` |
| F-10 | Media | La Multilista no mantiene enlaces de productos desde cada investigador; esa consulta recorre todos los productos. | Alta | `src/pea/estructuras/multilista.py:10-25,145-158` |
| F-11 | Media | `ListaDoble.eliminar_nodo` no valida que el nodo pertenezca a la lista receptora. | Alta | `src/pea/estructuras/lista_doble.py:117-140` |
| F-12 | Media | La limpieza Python devuelve exito aunque fallen los borrados REST de respaldo. | Alta | `tools/db/reiniciar_prueba.py:55-93` |
| F-13 | Media | Hay defectos de distribucion visual a 1100x700 en directorios y analisis de redes. | Media-alta | Capturas temporales de la autoprueba; `brain/20-Diseno/GUI-Diseno-Python.md:426` |
| F-14 | Baja/Media | La prueba de temporizador de toast falla dentro de la suite completa, pero pasa aislada; causa no determinada. | Alta para la discrepancia, baja para su causa | `tests/unit/test_componentes_gui.py:436` |
| F-15 | Baja | Las pruebas de contrato y paginacion no prueban varios comportamientos que dicen cubrir. | Alta | `tests/contrato/test_contrato_postgresql.py:86-88,121+`; `tests/unit/test_cliente_http.py:104-119` |

### F-01 · Control de revision no atomico y tolerante a una lectura incompleta

`ControladorRevision.consultar_remota` captura cualquier excepcion de la RPC, intenta REST y, si REST devuelve una lista vacia, usa la revision local como si fuera la revision remota. Un sondeo sintetico con revision local 17, RPC fallida y REST `[]` devolvio 17. El resultado permite que `verificar_consistencia` declare consistencia sin haber leido una revision vigente.

Ademas, la RPC de creacion de producto compara `meta.revision` con `p_revision_esperada` mediante un `SELECT` ordinario sin bloqueo ni actualizacion condicional. Dos transacciones concurrentes pueden leer la misma revision antes de que alguna escriba y ambas superar la comprobacion. En las mutaciones REST, la lectura de revision y la escritura son peticiones separadas, con la misma ventana de carrera.

**Impacto:** no se garantiza el rechazo de escrituras obsoletas ni el aviso fiable «La base de datos cambió». El comportamiento remoto concurrente no se reprodujo; la conclusion se basa en el flujo local y la semantica transaccional del SQL.

**Correccion sugerida:** hacer que cada escritura compare y reserve/actualice la revision en la misma transaccion (por ejemplo, bloqueo de la fila `meta` o compare-and-swap), y tratar una lectura ausente o fallida como error explicito, nunca como igualdad.

### F-02 · Actualizacion compuesta de producto sin atomicidad remota

`actualizar_producto` puede ejecutar un `PATCH` de metadatos, luego borrar las asociaciones de grupo y despues crear una nueva asociacion, mediante solicitudes REST independientes. El `except` restaura el estado en memoria, pero no puede deshacer una solicitud anterior que ya fue aceptada por el servidor. Por ejemplo, si el `PATCH` y el borrado de asociaciones terminan bien y el alta de la asociacion falla, el estado remoto queda parcialmente actualizado mientras la memoria vuelve a los valores anteriores.

**Impacto:** divergencia permanente entre cliente y Supabase tras un fallo intermedio; contradice la atomicidad de cambios compuestos.

**Correccion sugerida:** encapsular la edicion del producto y sus relaciones en una sola RPC transaccional, con revision esperada y respuesta que confirme todos los cambios.

### F-03 · Alcance y permisos del RPC de limpieza de pruebas

La funcion `reiniciar_datos_prueba` es `SECURITY DEFINER` y se concede a `authenticated`. Sus borrados de productos, investigadores y grupos tienen filtros `es_ejemplo = true` y prefijo `PRUEBA-`, pero el borrado de `integrantes_grupo` usa solo `es_ejemplo = true`. Por ello puede quitar vinculos de todos los datos de ejemplo, incluidos los oficiales que no tengan prefijo `PRUEBA-`. La confirmacion exigida es una frase fija presente en el propio codigo.

La migracion no contiene una revocacion explicita de `EXECUTE` a `PUBLIC`/`anon`. PostgreSQL normalmente concede ejecucion de funciones a `PUBLIC` por defecto; sin embargo, no se verificaron los privilegios efectivos del proyecto Supabase ni defaults globales. Por tanto, el posible acceso anonimo se registra como riesgo de ACL, no como explotabilidad remota confirmada.

**Impacto:** perdida de relaciones de datos de ejemplo fuera del conjunto permitido por el contrato; si la ACL efectiva permite llamantes no autenticados, exposicion de una operacion destructiva sobre esos ejemplos.

**Correccion sugerida:** filtrar membresias por referencias a entidades `PRUEBA-`, revocar explicitamente ejecucion publica/anonima y concederla solo al rol necesario; revisar con una consulta de ACL autorizada antes de cualquier ejecucion. La funcion no se ejecuto.

### F-04 · Ingesta con estados y anos no validos

La ingesta GrupLAC/CvLAC asigna `estado_validacion="Aprobado"`, pero la migracion solo permite `Avalado`, `Con soporte` o `No avalado`. El alta atomica del producto debe ser rechazada por la restriccion SQL. Ademas, un ano ausente o cero se reemplaza por 2024; el extractor URL tambien emplea ese valor al fabricar el codigo de producto. Esto oculta el dato ausente en vez de pedir validacion o registrar una excepcion.

La validacion de servicio acepta anos 1900 a ano actual + 1, mientras `SPEC` exige 1970 a ano actual y la migracion admite 1970 a 2100. Las tres capas, por tanto, no comparten una sola regla.

**Correccion sugerida:** usar un estado permitido y respaldado por la fuente o dejar la importacion pendiente de validacion; no inventar el ano y alinear los limites en requisito, dominio, servicio y SQL mediante migracion nueva si hiciera falta.

### F-05 · Perdida del comando de deshacer ante error

`deshacer` desapila primero la operacion y luego intenta aplicar/persistir el inverso. Si esa accion lanza una excepcion, no se vuelve a introducir el comando original en la pila. Un sondeo sintetico con fallo de persistencia dejo la pila vacia.

**Impacto:** el usuario pierde la posibilidad de reintentar la accion inversa, aunque la estructura se haya restaurado parcialmente o el servidor haya rechazado el cambio.

**Correccion sugerida:** conservar el comando hasta confirmar la operacion completa y limpiar de forma explicita los comandos auxiliares generados por el propio undo solo despues del exito.

### F-06 · Respuesta vacia de altas tratada como persistencia correcta

Los repositorios de grupos e investigadores, y las rutas REST equivalentes, devuelven la entidad original cuando el `POST` devuelve una lista vacia. El sondeo sintetico obtuvo un Grupo con `id=None` sin elevar error. Las operaciones posteriores que requieren el ID pueden no persistirse o fallar de forma tardia, aunque el alta inicial se haya presentado como exitosa.

**Correccion sugerida:** requerir la representacion del registro creado o recuperar y validar el registro por una clave natural; si no es posible confirmar el ID remoto, devolver un error explicito y revertir memoria.

### F-07 · Revision local desfasada tras crear producto con relaciones

La creacion de producto en RPC inserta el producto, la relacion con el grupo y cada relacion de autor en instrucciones separadas. Los triggers locales incrementan `meta.revision` por sentencia; el servicio, en cambio, suma exactamente uno a la revision local al terminar. Una creacion con grupo y varios autores puede dejar al cliente con una revision menor que la remota.

**Corrección aplicada en migración 008:** los triggers incrementan `meta.revision` una sola vez por transacción aunque un RPC ejecute varias sentencias en tablas relacionadas. De este modo, el incremento local de una unidad vuelve a coincidir con una escritura transaccional. Si una escritura externa causa un conflicto real, Python y C++ detienen el procesamiento masivo de la cola y preservan las tareas que aún no se ejecutaron.

### F-08 · Desacuerdo entre dominio y esquema

El modelo `Investigador` declara `documento_identidad`, pero la tabla `investigadores` de la migracion no contiene esa columna ni una restriccion de unicidad asociada. El requisito RF-03 solicita el dato y la unicidad del documento. Tambien hay atributos opcionales en modelos Pydantic que corresponden a columnas `NOT NULL` en el esquema, lo que deja la validacion final a errores de persistencia.

**Impacto:** el requisito de documento no puede cumplirse contra el esquema local versionado; objetos aceptados por Pydantic pueden rechazarse en SQL. El estado de migracion remota no fue comprobado.

**Correccion sugerida:** resolver la discrepancia con la fuente normativa y agregar una migracion nueva solo si se confirma que el campo es requisito; alinear obligatoriedad y mensajes entre modelo, servicio y base.

### F-09 · Lider de Grupo no ligado a membresia

La tabla `grupos` guarda `lider` como texto obligatorio. La tabla `integrantes_grupo` es independiente y el metodo de creacion de grupo persiste unicamente el grupo; no registra la membresia del lider ni verifica que haya un integrante con rol `Líder`. No se encontro una restriccion SQL que garantice esa relacion.

**Impacto:** puede existir un grupo con un nombre de lider pero sin el correspondiente investigador vinculado, incumpliendo la condicion RF-02 del lider integrante.

**Correccion sugerida:** resolver la identidad del lider, crear grupo y membresia en una RPC atomica y aplicar una regla de integridad coherente con el Modelo.

### F-10 · Navegacion de la Multilista incompleta por investigador

Cada nodo mantiene enlaces globales y de grupo, y una lista de objetos autores. No hay una cadena de productos asociada a cada investigador. `obtener_productos_investigador` recorre todos los nodos globales y busca el autor en cada lista, en lugar de navegar desde el investigador a sus productos.

**Impacto:** la estructura cumple parcialmente la consulta cruzada pero no la multilista bidireccional exigida; la consulta por investigador escala con el total de productos y coautores.

**Correccion sugerida:** implementar y probar los enlaces por investigador conservando la identidad del nodo Producto, o documentar una decision normativa si se aprueba otra estructura.

### F-11 · Eliminacion de nodo ajeno a `ListaDoble`

`eliminar_nodo` solo comprueba que el argumento no sea `None`. Si recibe un nodo de otra lista, puede mutar los enlaces de aquella lista y disminuir el tamano de la lista receptora. Un sondeo sintetico confirmo que el tamano destino paso a cero mientras su cabeza seguia presente.

**Impacto:** se rompe el invariante cabeza/cola/tamano y pueden corromperse listas de dominio ante uso incorrecto de una referencia.

**Correccion sugerida:** asegurar pertenencia al contenedor antes de modificar enlaces, mediante pertenencia comprobable o encapsulamiento del nodo; rechazar nodos externos sin modificar ninguna lista.

### F-12 · Falso exito en el script de reinicio Python

Si falla la RPC, `tools/db/reiniciar_prueba.py` intenta borrados REST por tabla. Los errores de esos borrados se imprimen, pero al final el script muestra un mensaje de finalizacion exitosa y devuelve `0` incluso si todos fallaron. El fallback tambien divide una operacion que la RPC pretendia hacer atomica.

**Impacto:** automatizaciones y operadores pueden creer que el reinicio termino cuando quedaron filas; ejecucion parcial puede dejar datos de prueba inconsistentes.

**Correccion sugerida:** acumular resultados, devolver codigo distinto de cero ante cualquier fallo y evitar un fallback no atomico salvo que el usuario haya autorizado expresamente ese modo.

### F-13 · Defectos de GUI observados a 1100x700

La autoprueba offscreen cubrio ocho ventanas/pantallas y tres resoluciones, sin barras horizontales. La inspeccion visual de las capturas de 1100x700 mostro fichas laterales junto a las tablas en lugar de debajo como define el breakpoint; en Investigadores se solapan avatar y titulo; en Redes hay etiquetas/celdas del panel de metricas recortadas.

Las advertencias de widgets fuera de limites no se consideran por si solas prueba de defecto, pues algunos controles estan dentro de areas desplazables. Los defectos anteriores se observaron directamente en capturas, pero no se valido el comportamiento en un escritorio Windows interactivo.

**Correccion sugerida:** corregir el breakpoint/maquetacion y verificar visualmente esas pantallas en 1100x700; conservar las capturas como evidencia en una futura tarea de interfaz, no como datos persistentes.

### F-14 · Prueba de temporizador dependiente del orden

En la suite completa, `test_toasts_consecutivos_se_conservan_al_interactuar_y_cambiar_pantalla` fallo porque esperaba que el temporizador se pausara al pasar el raton. Ejecutada aisladamente, la misma prueba paso. La causa no esta demostrada y no se concluye que el comportamiento de produccion falle.

**Correccion sugerida:** aislar estado global/temporizadores Qt, revisar limpieza de widgets entre pruebas y repetir con orden aleatorio y repeticiones.

### F-15 · Cobertura de contrato y paginacion insuficiente

La prueba de contrato de triggers comprueba una expresion regular sin asociar el resultado a la tabla iterada. Las verificaciones RLS son esencialmente comprobaciones textuales y no prueban privilegios efectivos. La prueba de paginacion simula dos paginas pequenas; no cubre el limite de 1000 filas ni cambios concurrentes durante la lectura.

**Correccion sugerida:** relacionar cada asercion con cada tabla/trigger esperado; probar el cliente con mas de 1000 filas simuladas y errores en paginas intermedias; reservar una comprobacion remota marcada `red` para un entorno autorizado, con datos de prueba estrictamente aislados.

## Matriz de requisitos

| Requisito | Evaluacion | Evidencia o limite |
|---|---|---|
| RF-01 Concurrencia y revision | No conforme en la evidencia examinada | F-01; la lectura remota vacia puede usar la revision local y la comparacion/escritura no es atomica. |
| RF-02 Grupos | Parcial | CRUD presente; F-09 muestra que el lider no queda garantizado como integrante. |
| RF-03 Investigadores | Parcial / discrepancia normativa | F-08: `documento_identidad` no existe en la migracion local. No se audito cada filtro ni categoria. |
| RF-04 Productos | No conforme en ingesta | F-04: estado invalido y ano inventado; los limites de ano difieren entre capas. |
| RF-05 Multilista | Parcial | Nodo compartido, enlaces globales/grupo y autores; F-10: falta navegacion de productos desde cada investigador. |
| RF-06 Lista doble | Parcial | Estructura manual presente; F-11 rompe invariantes si se entrega un nodo ajeno. |
| RF-07 Deshacer | No conforme ante error de persistencia | F-05: el comando se pierde al fallar el inverso. |
| RF-08 Cola FIFO | No verificado de extremo a extremo | La cola propia existe; no se auditaron exhaustivamente los estados, orden y continuacion tras fallo. |
| RF-09 Hipercubo | Parcial | Hipercubo 5D existe y se alimenta desde la multilista; no se verificaron todos los casos de inactivos/dispersidad. |
| RF-10 Estadisticas | Parcial | El servicio usa el hipercubo; la comparacion independiente con SQL y el umbral de rendimiento no quedaron demostrados. |
| RF-11 GUI | Parcial | Ocho pantallas probadas en tres resoluciones; F-13 en 1100x700; no se auditaron todos los textos/criterios. |
| RF-12 Persistencia atomica | No conforme en operaciones compuestas examinadas | F-02 y F-06; la creacion de producto usa RPC, pero la edicion de relaciones usa varias llamadas REST. |
| RF-13 Ingesta externa | Parcial | Se observaron modulos de URL/CSV y pruebas offline; F-04 invalida el estado del producto. No se hicieron peticiones web. |
| RNF-01 Estructuras propias | Parcial | Las colecciones principales del catalogo usan ListaDoble, Multilista, Pila, Cola e Hipercubo; no se revisaron todos los 82 modulos. |
| RNF-02 Paridad Python/C++ | No evaluado | C++ fuera de alcance y sin ejecucion de build. |
| RNF-03 Estadisticas desde hipercubo | Parcial | Los servicios estadisticos examinados reciben el hipercubo; las pruebas de contrato no son un oraculo robusto. |
| RNF-04 Auth, RLS, HTTPS | Parcial / remoto no verificado | Migraciones locales incluyen RLS y roles; F-03 plantea ACL de funcion. No se verificaron ACL, politicas ni transporte configurado en remoto. |
| RNF-05 Espanol y pruebas offline | Parcial | Suite offline ejecutada; hay un fallo contextual. La inspeccion de textos GUI fue visual y no exhaustiva. |
| RNF-06 Borrado y reversibilidad | Parcial | Hay desactivacion y borrado separados; F-05 rompe la recuperacion ante error. No se validaron todas las cascadas en Supabase. |

## Esquema, persistencia y seguridad

- Las dos migraciones locales crean las tablas de dominio, habilitan RLS y declaran RPCs de producto, desactivacion, eliminacion y limpieza. No se hizo `db push`, `db pull` ni una consulta al proyecto remoto.
- La creacion de producto es atomica a nivel de una RPC en PostgreSQL, pero el bloqueo optimista tiene la carrera descrita en F-01 y la revision local puede quedar desfasada segun F-07.
- Crear/actualizar grupos e investigadores usa REST directo. El cambio de grupo en un producto requiere varias solicitudes y no esta cubierto por una transaccion remota.
- La tabla `investigadores` no declara `documento_identidad`; la tabla `grupos` conserva el lider como texto, separado de `integrantes_grupo`.
- La migracion habilita RLS, pero leer el archivo SQL no demuestra que esas politicas esten desplegadas ni que no existan privilegios adicionales. La ACL de la funcion `SECURITY DEFINER` exige verificacion remota autorizada antes de considerar segura su exposicion.
- `.env` existe, esta ignorado por Git y no se leyo. `.env.example` tiene variables vacias/de ejemplo segun comprobacion que no mostro valores. No se hizo un escaneo exhaustivo del historial Git en busca de secretos; por tanto, no se certifica ausencia de credenciales fuera de lo inspeccionado.
- Las fuentes SCIENTI pueden contener datos personales; no se leyeron archivos de integrantes ni se verifico en esta auditoria retencion, permisos locales o limpieza de `datos/cache/`.

## GUI y estructuras

- La autoprueba genero capturas temporales para ocho pantallas/ventanas por resolucion 1100x700, 1366x768 y 1920x1080. Salio con codigo 0 y no detecto barras horizontales. La ausencia de barras no prueba que todos los controles sean visibles; se identificaron los defectos de F-13.
- No se encontro evidencia de SQLite como base local en las rutas examinadas; la auditoria no ejecuta un escaneo exhaustivo del repositorio completo.
- Las estructuras maestras revisadas son implementaciones manuales y el catalogo conecta el servicio estadistico al hipercubo. Las limitaciones de identidad cruzada y pertenencia se describen en F-10 y F-11.
- El directorio temporal de capturas de esta auditoria se elimino despues de documentar las observaciones; no se guardaron capturas con datos personales en la boveda.

## Verificacion ejecutada

Entorno local observado: Python 3.14.6, requests 2.34.2, Pydantic 2.13.5, PySide6 6.11.2, pytest 9.1.1 y Ruff 0.16.10. El proyecto establece Python >=3.12; no se encontro Python 3.12 instalado, por lo que esa version minima no fue validada.

| Comando / actividad | Resultado |
|---|---|
| `.venv\Scripts\python.exe -m compileall -q src\pea tests tools` | OK, codigo 0. |
| `ruff check src\pea` | OK. |
| `ruff check tests` | OK. |
| `ruff check tools` | FALLA: 77 diagnosticos; 75 reportados como corregibles automaticamente. No se corrigieron por estar fuera de alcance. |
| `pytest -q tests` | 236 aprobadas, 1 fallida y 2 excluidas. |
| Prueba aislada `test_toasts_consecutivos_se_conservan_al_interactuar_y_cambiar_pantalla` | 1 aprobada; no explica el fallo dentro de la suite. |
| `pytest` focalizado (`tests/unit tests/contrato`) | 231 aprobadas, 1 fallida y 2 excluidas. |
| Autoprueba GUI offscreen | Codigo 0; 24 capturas temporales, sin barras horizontales en las resoluciones verificadas. F-13 se observo visualmente. |
| Sondeos sinteticos de revision, alta vacia, deshacer y nodo ajeno | Reprodujeron los cuatro comportamientos documentados; sin red ni escrituras. |
| `coverage`, Bandit y `pip-audit` | No instalados; no se instalaron durante esta tarea. |
| Pruebas marcadas `red`, `scripts/verificar.ps1`, Supabase remoto | No ejecutados. |

## Plan recomendado de correccion

1. **Integridad y control de escritura:** implementar una compare-and-write atomica de revision, devolver la revision final desde RPC y eliminar el fallback silencioso a revision local.
2. **Atomicidad de edicion:** convertir en RPC la actualizacion de producto y sus relaciones; cubrir los fallos parciales con pruebas de rollback local/remoto.
3. **Datos de prueba y permisos:** corregir el filtro de `integrantes_grupo`, revocar privilegios PUBLIC/anon de la funcion, validar ACL efectivas en el panel/entorno autorizado y cambiar el script para que nunca comunique exito parcial.
4. **Dominio e ingesta:** alinear campos y opcionalidad con el Modelo, resolver documento de identidad y pertenencia del lider, rechazar anos faltantes y usar estados admitidos.
5. **Estructuras y reversibilidad:** no perder comandos de undo tras fallos; comprobar pertenencia de nodos; completar enlaces de la multilista por investigador.
6. **Calidad y GUI:** aislar la prueba flaky, fortalecer contratos y paginacion, y ajustar los tres defectos visuales a 1100x700.
7. **Reauditoria QA:** ejecutar pruebas focalizadas y luego `scripts/verificar.ps1` en un entorno que soporte el build C++; para cualquier prueba remota, limitarse a filas `es_ejemplo=true` con prefijo `PRUEBA-` y credenciales de usuario normales. No ejecutar limpieza global de ejemplos.

## Comandos y decisiones de esta tarea

- Se ejecutaron verificaciones locales de Python, Ruff, pytest y la autoprueba GUI; los resultados estan resumidos arriba.
- Se verifico `git status` antes y despues. El cambio preexistente en `brain/.obsidian/graph.json` no se modifico ni se incluyo.
- No se uso el token compartido, no se leyo `.env`, no se contactaron hosts externos y no se altero ninguna fila, politica o migracion remota.
- No se corrigio codigo porque el alcance solicitado era auditoria e informe de solo lectura.
- No se hizo push a GitHub.

## QA

La auditoria deja evidencia reproducible para los defectos locales identificados y separa las inferencias sobre PostgreSQL/ACL de los hechos verificables en archivos. El cambio de la aplicacion se mantiene intacto. La evaluacion no debe presentarse como certificacion de la base remota ni como aprobacion total de los 13 requisitos funcionales y 6 no funcionales.

## Pendientes y siguiente paso

- Ejecutar el plan priorizado como tareas de correccion separadas y volver a auditar cada criterio afectado.
- Verificar en el proyecto remoto, con autorizacion y consultas de solo lectura, la revision desplegada, ACL de funciones `SECURITY DEFINER`, politicas RLS y migraciones aplicadas.
- Si la credencial compartida es activa, revocarla/rotarla. No reutilizarla en archivos, comandos registrados ni notas.
