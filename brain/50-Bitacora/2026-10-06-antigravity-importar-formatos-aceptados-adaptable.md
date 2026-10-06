---
tipo: bitacora
estado: revisado
creado: 2026-10-06
actualizado: 2026-10-06
relacionado:
  - "[[GUI-Diseno-Python]]"
  - "[[2026-10-06-antigravity-botones-deshabilitados-importar-configuracion]]"
origen: "Corrección de Formatos aceptados y adaptabilidad en zona de arrastrar y soltar de Importar"
agente: "Antigravity"
rama: "master"
commit: "fix: corregir texto de formatos aceptados y adaptabilidad en zona de arrastrar y soltar"
---

# Bitácora · Adaptabilidad y Corrección de «Formatos Aceptados» en Importar

## Objetivo
Corregir [`src/pea/gui/pantallas/importar.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/pantallas/importar.py) para que la etiqueta informativa «Formatos aceptados: ...» nunca quede cortada ni truncada en la zona interactiva de arrastrar y soltar ([`ZonaSoltarArchivo`](file:///c:/dev/PEAi-Taller2/src/pea/gui/pantallas/importar.py#L55-L130)):
1. Configurar el QLabel de ayuda con ancho adaptable (`setMinimumWidth(0)`), envoltura de línea activa (`setWordWrap(True)`) y política de tamaño elástica (`QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred`).
2. Conservar la altura oficial de 88 px de la tarjeta sin aumentarla innecesariamente, optimizando los márgenes internos (`12, 6, 12, 6`) y espaciado (`8 px`) para brindar 76 px de holgura vertical interior.
3. Preservar plenamente visible el botón «Examinar...» y operativa la funcionalidad de arrastrar y soltar (Drag and Drop).
4. Corregir el selector de estilo en arrastre para aplicar `estilo.INFO_FONDO` correctamente.
5. Verificar la armonía visual y proporciones en las tarjetas CSV, PDF y URL en las tres resoluciones oficiales (1100×700, 1366×768 y 1920×1080).
6. Añadir pruebas de regresión unitarias automatizadas que inspeccionen las propiedades y geometrías.

## Diagnóstico y Causa Raíz
1. **Truncamiento Horizontal y Falta de Envoltura**:
   - `_lbl_subtexto` no tenía habilitado `setWordWrap(True)` ni poseía una política de tamaño expansiva con ancho mínimo cero.
   - En 1100×700, la columna de texto de `ZonaSoltarArchivo` quedaba reducida a ~103 px. Al carecer de wordWrap, el texto «Formatos aceptados: .CSV» requería más de 160 px en una sola línea, por lo que Qt truncaba el texto horizontalmente como «Formatos aceptad».
2. **Distribución Vertical en 88 px**:
   - Los márgenes de la zona eran `(14, 10, 14, 10)`, dejando solo 68 px libres.
   - Con márgenes ajustados a `(12, 6, 12, 6)` y espaciado de 8 px, el área útil vertical asciende a 76 px, permitiendo que tanto el texto principal como la ayuda convivan en múltiples líneas (2 líneas cada uno) ocupando ~64 px con 12 px de margen de respiración simétrico.
3. **Sintaxis de Estilo en Drag Over**:
   - En `_establecer_estilo`, `fondo` durante el arrastre tenía una cadena literal `"{estilo.INFO_FONDO}"` sin prefijo f-string, lo que generaba un estilo CSS inválido. Se corrigió a `estilo.INFO_FONDO`.

## Qué se hizo
- En [`src/pea/gui/pantallas/importar.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/pantallas/importar.py):
  - En `ZonaSoltarArchivo._construir_ui()`:
    - Se redujeron los márgenes de contenido a `(12, 6, 12, 6)` y el espaciado a `8` px.
    - Se asignó `setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)` al ícono decorativo.
    - Se alineó `col_textos` verticalmente al centro (`Qt.AlignmentFlag.AlignVCenter`).
    - En `_lbl_principal`: se activó `setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)` y `setMinimumWidth(0)`.
    - En `_lbl_subtexto`: se asignó `setObjectName("ayuda")`, `setWordWrap(True)`, `setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)` y `setMinimumWidth(0)`.
    - En `btn_examinar`: se configuró `setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)`.
  - En `ZonaSoltarArchivo._establecer_estilo()`:
    - Se corrigió el uso de `estilo.INFO_FONDO` en el estado de arrastre.
  - En `ZonaSoltarArchivo._actualizar_nombre_visible()`:
    - Se protegió el cálculo ante anchos iniciales no positivos (`ancho <= 0`).
- En [`tests/unit/test_pantallas_finales.py`](file:///c:/dev/PEAi-Taller2/tests/unit/test_pantallas_finales.py):
  - Se agregó la prueba de regresión `test_zona_soltar_archivo_formatos_aceptados_adaptable`, validando:
    - `acceptDrops() == True` en CSV y PDF.
    - Altura fija de 88 px en las zonas.
    - `wordWrap() == True`, política horizontal `Expanding` y `minimumWidth() == 0`.
    - En 1100×700, 1366×768 y 1920×1080: visibilidad de CSV, PDF y URL; altura de `_lbl_subtexto` ($\ge 24$ px en resoluciones compactas/medias por envoltura a 2 líneas, $\ge 12$ px en amplia); inclusión estricta dentro del límite inferior de 88 px (`bottom < 88`); y botón «Examinar...» visible y acotado.

## Comandos y resultados
- `ruff check src tests`: Todos los archivos aprobados (0 errores, 0 advertencias).
- `pytest tests/unit/test_pantallas_finales.py -v`: 7/7 pruebas aprobadas en 4.27s.
- `pytest tests/unit -v`: **207 pasadas**, 1 deseleccionada (red) en 82.75s.
- `python -m pea.gui --autoprueba`: 24 capturas generadas satisfactoriamente en `datos/capturas/oficiales/`. 0 barras horizontales en todas las resoluciones.
- `scripts/diagnostico_desborde.py`: `Areas con barra horizontal visible: ninguna` en 1100×700, 1366×768 y 1920×1080.
- `pytest tests/unit/test_estilo_recursos.py::test_guardian_estilos_sin_literales_en_gui`: Aprobado (1/1 OK).
- `tools/brain/verificar_brain.py`: Bóveda validada sin errores (110 notas inspeccionadas).

## Decisiones
- Se conservó la altura exacta de 88 px de la tarjeta de arrastrar y soltar requerida por el diseño, ganando holgura vertical interior mediante la optimización de márgenes y espaciado.
- Se mantuvieron los tokens oficiales sin introducir colores literales.

## Pendientes y siguiente paso
- Continuar con las pruebas de integración y el flujo del proyecto.

