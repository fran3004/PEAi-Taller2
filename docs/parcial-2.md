# Parcial 2: funcionamiento y trazabilidad

Fuente: «Parcial 2 EdD (2026-10-19)», páginas 1–3, y el Modelo
M601PR04G01 versión 02 de 2024 conservado en `docs/entrada/Modelo-2024.original.pdf`.
La especificación Word, los diagramas UML y el video están excluidos por indicación
del propietario. Esta entrega conserva la arquitectura modular Python/C++.

## Uso de la nueva sección

1. Al abrir Python, elija Supabase, un archivo local o iniciar sin datos.
2. Abra **Indicadores**. Seleccione grupo o investigador y una entidad del catálogo.
3. Elija el año de corte; 2023 corresponde al cierre de la convocatoria del Modelo
   2024. Se puede indicar otro corte o un límite inicial adicional para explorar
   periodos distintos. Las ventanas diferenciadas del Modelo siguen limitando
   los productos elegibles.
4. Pulse **Calcular catálogo**. También puede introducir una URL oficial de
   GrupLAC/CvLAC y pulsar **Calcular desde URL**. Esta descarga se calcula en memoria
   y no modifica Supabase. **Guardar catálogo local** conserva la descarga; abra
   después ese archivo si quiere completar sus datos y recalcular.
5. Consulte los nueve componentes, sus indicadores brutos, máximos de referencia,
   índices, coeficientes y aportes al resultado. Las exclusiones se enumeran.
6. En la tabla de productos del catálogo, seleccione un producto y asigne una
   categoría de calidad respaldada por los requisitos del Modelo. Se conserva en
   `producto.detalles.categoria_minciencias`, junto a los metadatos originales.
   La operación usa el servicio habitual, admite deshacer y persiste por REST/RPC
   cuando el origen es Supabase. En modo local, guarde el archivo para conservarla.
7. Exporte el desglose JSON para revisar todas las inclusiones y exclusiones.

La edición de campos adicionales permite modificar atributos complementarios de
grupos, investigadores y productos. Los códigos que enlazan entidades y los IDs de
persistencia conservan su identidad; la activación y el borrado usan sus acciones
de dominio para mantener relaciones y deshacer.

En C++, la pestaña **9 Indicadores** ofrece `c` para el cálculo; `s` guarda el
catálogo y `o` abre un archivo cuando se está trabajando en memoria. En los
directorios, `a` abre la edición de campos complementarios como objeto JSON.
Las CLI permiten exportar el detalle completo y utilizar referencias externas.

## Fórmulas y origen de los valores

El catálogo compartido `src/pea/recursos/modelo_2024.json` contiene 169 categorías.
Python lee ese archivo y C++ incorpora exactamente el mismo mediante un recurso
Qt. `tools/modelo/generar_catalogo_puntajes.py` lo reproduce desde el PDF original:
clases de la sección 3.7, pesos base de la Tabla 6 y pesos relativos de las tablas
del Anexo 1. Cada categoría conserva la página de su peso relativo. No se utiliza
como fuente de puntajes el resumen histórico de la bóveda, que contenía valores
distintos del documento original.

Para cada subtipo:

```
puntaje_unitario = peso_base × peso_relativo
lambda = ln(1 + productos_unicos_del_subtipo / periodo_observacion)
indicador_bruto_de_clase = suma(lambda × puntaje_unitario)
indice_de_componente = indicador_bruto / maximo_de_referencia
```

Ejemplos de la sección 3.6: `ART_A2 = 100 × 5,5 = 550`,
`CAP_LIB_B = 60 × 8 = 480` y `PA1 = 500 × 10 = 5000`.
`SF = 35 × 8 = 280`, conforme a la tabla de la página 147.

Ventanas de la Tabla 5: artículos A1/A2/B/C y libros resultado de investigación,
7 años; patentes, variedades/razas y creación/investigación-creación, 10 años;
capítulos, notas y demás productos, 5 años. El periodo anual efectivo se limita
además por la edad del grupo expresada en años de calendario inclusivos y por el
límite inicial elegido. Para investigadores se aplica la ventana al conjunto de
sus productos, conforme a la adaptación pedida por el parcial.

En los productos GNC/DTI elegibles, la cohesión usa la suma de autores internos
por producto dividida entre productos, menos uno. La cooperación usa la suma de
grupos relacionados por producto dividida entre productos, menos uno. Se
consideran las fechas históricas de vinculación; las relaciones se deduplican en
cada producto. Para el investigador, se consideran todos los coautores de sus
productos. Este último alcance es una adaptación académica explícita: el Modelo
define el indicador para grupos, mientras el parcial pide reutilizar la fórmula
en investigadores.

```
Indicador = 3,7 Nc.Top + 2,3 Nc.A + 0,4 Nc.B + 1,5 AP + 0,5 DPC
          + 1 Fr.A + 0,2 Fr.B + 0,1 Cohe + 0,3 Coop
```

Los índices tienen máximo uno en la población usada y el indicador tiene máximo
10. Cuando un componente observado y su máximo son cero, su aporte es cero.
Se rechazan máximos negativos, no finitos, incompletos o menores al observado.

## Referencia y calidad de los datos

Por defecto, la comparación usa los máximos de los grupos activos cargados de la
misma gran área OCDE; si el área no está disponible, usa el catálogo cargado y lo
declara. Para investigadores se usa la población de investigadores del catálogo.
El sujeto seleccionado se incluye en la referencia aunque esté desactivado.
Los grupos creados después del corte no entran en esa población.

Este resultado es una comparación del catálogo, no una clasificación nacional
oficial. Para reproducir una referencia más amplia, ambas aplicaciones admiten un
JSON con los nueve máximos, su fuente y el mismo periodo:

```json
{
  "fuente": "Descripción y procedencia de la población de referencia",
  "corte": 2023,
  "desde": null,
  "maximos": {
    "Nc.Top": 10000, "Nc.A": 10000, "Nc.B": 10000,
    "AP": 10000, "DPC": 10000, "Fr.A": 10000, "Fr.B": 10000,
    "Cohe": 10, "Coop": 10
  }
}
```

Los números del ejemplo anterior son ilustrativos, no máximos nacionales.
Un perfil público puede informar «Artículo» sin publicar el cuartil, acceso
abierto, categoría de libro o soportes de validación. El programa conserva ese
producto, lo identifica como no puntuable y enumera la información faltante.
Solo incluye productos activos, avalados y con categoría compatible con su
tipología mayor; no inventa una categoría ni rellena un año ausente. El indicador
se marca incompleto si se excluyen productos por falta de categoría/validación o
si faltan vínculos para los componentes de colaboración o la antigüedad del grupo.
Sin fecha de creación se usa la ventana del subtipo como periodo provisional y
se identifica esa limitación. Un cero acompañado de
exclusiones no prueba ausencia de producción.

## Comandos equivalentes

Desde el código fuente, use `.venv\Scripts\python.exe -m pea.cli` para Python y
`cpp\build\pea-cpp.exe` para C++. En el portable, los ejecutables son
`PEAi-Python\pea-cli.exe` y `PEAi-Cpp\pea-cpp.exe`.

Ejemplo sin red (los mismos argumentos sirven en ambos):

```powershell
.\PEAi-Python\pea-cli.exe indicador --archivo datos/ejemplo-parcial.json --ambito grupo --codigo PRUEBA-G1 --corte 2023 --salida indicador-grupo.json
.\PEAi-Cpp\pea-cpp.exe indicador --archivo datos/ejemplo-parcial.json --ambito investigador --codigo PRUEBA-I1 --corte 2023 --salida indicador-investigador.json
```

El catálogo sintético de ejemplo produce `4,5` para `PRUEBA-G1` en 2023, con tres
productos incluidos, dos excluidos y avisos explícitos. Permite practicar la
asignación de calidad sin alterar datos reales.

Descarga de un investigador sin escritura remota:

```powershell
.\PEAi-Python\pea-cli.exe indicador --ambito investigador --url "https://scienti.minciencias.gov.co/cvlac/visualizador/generarCurriculoCv.do?cod_rh=0000494917" --corte 2023 --guardar-catalogo cvlac.json --salida indicador.json
```

`--referencia referencia.json` selecciona máximos externos. `--json` muestra el
resultado completo. `guardar-local --salida catalogo.json` conserva una lectura
del catálogo remoto. `pea-cpp.exe --archivo catalogo.json` y
`python -m pea.gui --archivo catalogo.json` abren ese archivo sin conexión;
`--vacio` abre un catálogo editable sin registros.

El formato `pea-catalogo` versión 1 conserva grupos, investigadores, membresías,
productos y sus relaciones. Reconstruye las listas y los nodos compartidos, valida
referencias y rechaza duplicados antes de sustituir el catálogo. Los guardados
son atómicos y no incluyen tokens, claves ni variables de entorno. No se usa un
archivo local como sincronización automática hacia Supabase.

## Procesamiento PDF

Python conserva su extractor por páginas y tablas con pdfplumber. C++ incorpora
Poppler `pdftotext` en el portable y extrae páginas, texto alineado, huella SHA-256
y advertencias de páginas sin texto suficiente:

```powershell
.\PEAi-Cpp\pea-cpp.exe importar-pdf --archivo pruebas/texto.pdf --salida extraccion.json
```

Procesar un documento no equivale a registrar automáticamente entidades. Las
tablas se conservan como texto alineado en C++; en Python también se extraen
celdas. La carga estructurada de entidades se realiza mediante CSV canónico o
SCIENTI. Los PDF escaneados requieren OCR previo; no se simula una extracción.

## Correspondencia con el enunciado

| Requisito | Implementación y comprobación |
|---|---|
| Dos programas Python/C++ | GUI/CLI Python y TUI/CLI C++ independientes; la sección de indicadores se compara entre procesos |
| Puntos 1, 3, 8: grupos, integrantes y listas | Catálogos, lista doble y multilista propias; identidad compartida verificada al cargar archivos |
| Puntos 2, 4 y PARCIAL 1–2 | Catálogo de calidad, puntaje por producto, indicador grupal e individual, desglose y referencia explícita |
| Puntos 5–6 | Modelo original, catálogo reproducible y entradas/salidas descritas en esta guía y diccionario existente |
| Punto 7 | URL/CSV en ambos; procesamiento PDF en ambos con sus diferencias documentadas |
| Puntos 9 y 11 | CRUD, validación, activación, borrado, edición complementaria y deshacer mediante servicios |
| Punto 10 | Filtros descriptivos existentes y corte/límite inicial para indicadores |
| Punto 12 | Dashboard, histogramas y barras Python; resúmenes, tablas e indicadores C++ |
| Notas 1, 4 y 8 | Entradas académicas `Parcial2_FF_SM.py/.cpp` e identificación existente; requieren el código modular completo |
| Notas 9–10 | Catálogo JSON interoperable, ejemplo sintético, elección de archivo o inicio vacío |
| Notas 5–7 | Publicación GitHub y paquete descargable; el envío por correo y los plazos del docente son acciones de entrega externas |

No se inventa un tercer integrante: el archivo de identificación conserva los dos
autores que figuran en el proyecto. La nota del PDF que habla de tres estudiantes
no permite deducir otro nombre.

## Validación reproducible

`scripts/verificar.ps1` ejecuta la suite Python, CTest, la autoprueba TUI, las
27 combinaciones de pantalla/tamaño de la GUI y la comparación de las CLI del
parcial. Los casos del indicador verifican fórmulas numéricas independientes,
ventanas, coautoría, referencias, formatos inválidos y lectura cruzada de archivos.
El empaquetado repite los escenarios principales con los ejecutables extraídos
en un directorio temporal y sin herramientas de desarrollo en PATH.
