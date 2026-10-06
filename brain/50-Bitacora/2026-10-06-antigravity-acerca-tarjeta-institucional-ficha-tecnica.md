---
tipo: bitacora
estado: revisado
creado: 2026-10-06
actualizado: 2026-10-06
relacionado:
  - "[[GUI-Diseno-Python]]"
  - "[[2026-10-06-antigravity-importar-formatos-aceptados-adaptable]]"
origen: "Corrección de tarjeta institucional y ficha técnica responsive en pantalla Acerca"
agente: "Antigravity"
rama: "master"
commit: "fix: corregir tarjeta institucional y ficha tecnica responsive en acerca"
---

# Bitácora · Tarjeta Institucional y Ficha Técnica Responsive en Acerca

## Objetivo
Corregir [`src/pea/gui/pantallas/acerca.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/pantallas/acerca.py) para resolver tres problemas visuales y de accesibilidad identificados en la pantalla «Acerca de»:
1. **Eliminación de bordes residuales en tarjeta institucional**: Suprimir cualquier borde y recuadro residual en los [`QLabel`](file:///c:/dev/PEAi-Taller2/src/pea/gui/pantallas/acerca.py) del banner institucional UPC, forzando fondo transparente y `border: none`.
2. **Contraste accesible (WCAG AAA)**: Mejorar el contraste de la línea «Facultad de Ingenierías y Tecnológicas — Programa de Ingeniería de Sistemas» sobre el banner institucional oscuro ([`ENCABEZADO_INICIO`](file:///c:/dev/PEAi-Taller2/src/pea/gui/estilo.py)), utilizando un token accesible sin colores literales.
3. **Ficha técnica responsive sin truncamiento**: Evitar que «Estructuras de datos en memoria» o cualquier etiqueta larga de viñeta se corte, sustituyendo el ancho rígido `setFixedWidth(240)` por una distribución en [`QGridLayout`](file:///c:/dev/PEAi-Taller2/src/pea/gui/pantallas/acerca.py) responsive con `wordWrap`, ancho mínimo reglamentario y proporciones elásticas.
4. Conservar intactas todas las funciones y la API de [`PantallaAcerca`](file:///c:/dev/PEAi-Taller2/src/pea/gui/pantallas/acerca.py) (`refrescar`, `actualizar_vista`, `establecer_filtro`, `volver_solicitado`).
5. Añadir pruebas de regresión unitarias automatizadas y verificar la armonía visual en las resoluciones oficiales (1100×700, 1366×768 y 1920×1080).

## Diagnóstico y Causa Raíz
1. **Bordes y recuadros residuales en el banner institucional**:
   - `tarjeta_institucional` aplicaba estilo únicamente mediante cadena simple a `QFrame#tarjetaInstitucional`. En ciertos motores de renderizado de Qt Widgets y hojas de estilo heredadas, los `QLabel` hijos podían pintar bordes de marco predeterminados.
   - Solución: Especificar reglas explícitas en el QSS del contenedor (`QFrame#tarjetaInstitucional { border: none; }` y `QFrame#tarjetaInstitucional QLabel { background-color: transparent; border: none; }`), y aplicar `background-color: transparent; border: none;` explícitamente en el stylesheet inline de cada etiqueta (`lbl_upc`, `lbl_facultad`, `lbl_materia`, `lbl_img_upc`).
2. **Bajo contraste en la línea de Facultad**:
   - Se utilizaba el token `TEXTO_SOBRE_OSCURO_SUAVE` (`#C9D8EA`). Si bien proporcionaba un contraste respetable, en pantallas no calibradas y tipografía regular de 11 pt era susceptible de verse atenuado.
   - Con `TEXTO_SOBRE_OSCURO` (`#FFFFFF`), el radio de contraste contra `ENCABEZADO_INICIO` (`#0A2045`) asciende a 16.08:1, superando con holgura los criterios WCAG AAA (7:1).
3. **Truncamiento de etiquetas de viñeta en Ficha Técnica**:
   - Cada viñeta de la ficha técnica se maquetaba en un `QHBoxLayout` horizontal donde la etiqueta clave tenía `lbl_c.setFixedWidth(240)` y `wordWrap=False`.
   - La etiqueta «• Estructuras de datos en memoria:» con tipografía Inter/Sans de 11 pt negrita requiere ~270 px de avance. Al estar confinada a 240 px fijos sin envoltura de línea, Qt la truncaba como «• Estructuras de datos en memor».
   - Solución: Reemplazar los múltiples `QHBoxLayout` independientes por un único [`QGridLayout`](file:///c:/dev/PEAi-Taller2/src/pea/gui/pantallas/acerca.py) de dos columnas con `setColumnMinimumWidth(0, 220)`, `setColumnStretch(0, 1)` y `setColumnStretch(1, 3)`, habilitando `setWordWrap(True)` y `QSizePolicy.Policy.Preferred` en las claves, y `setWordWrap(True)` con `QSizePolicy.Policy.Expanding` en los valores.

## Qué se hizo
- En [`src/pea/gui/pantallas/acerca.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/pantallas/acerca.py):
  - Se añadieron `QGridLayout` y `QSizePolicy` a los imports de `PySide6.QtWidgets`.
  - Se removió el token no utilizado `TEXTO_SOBRE_OSCURO_SUAVE`.
  - En `tarjeta_institucional`:
    - Se agregó `border: none` al selector del frame y regla para `QLabel` hijos en QSS.
    - Se reforzó `background-color: transparent; border: none;` en todos los labels y pastilla interior.
    - Se actualizó el color de `lbl_facultad` a `TEXTO_SOBRE_OSCURO` y se habilitó `setWordWrap(True)`.
    - Se habilitó `setWordWrap(True)` en `lbl_materia`.
  - En `tarjeta_tecnica`:
    - Se implementó `disp_ficha = QGridLayout()` con espaciado horizontal de 16 px, vertical de 10 px, ancho mínimo de columna 0 en 220 px y stretches `1` y `3`.
    - Cada `lbl_c` tiene `setWordWrap(True)`, alineación superior izquierda y política `Preferred`.
    - Cada `lbl_v` tiene `setWordWrap(True)`, alineación superior izquierda y política `Expanding`.
- En [`tests/unit/test_pantallas_finales.py`](file:///c:/dev/PEAi-Taller2/tests/unit/test_pantallas_finales.py):
  - Se añadió la prueba [`test_pantalla_acerca_tarjeta_institucional_y_ficha_tecnica_responsive`](file:///c:/dev/PEAi-Taller2/tests/unit/test_pantallas_finales.py#L297-L345) que valida:
    1. Tarjeta institucional con `border: none` y ausencia de bordes en todos los `QLabel`.
    2. Contraste de texto institucional sobre `ENCABEZADO_INICIO` >= 4.5:1.
    3. Distribución en `QGridLayout` con ancho mínimo de 220 px y factores de estiramiento 1 y 3.
    4. Envoltura de texto activa (`wordWrap()`) y ausencia de restricción fija en etiquetas de clave (`maximumWidth() > 240`).
    5. Adaptabilidad en 1100×700, 1366×768 y 1920×1080 sin pérdida de texto ni colapso de dimensiones.

## Comandos y resultados
- `.\.venv\Scripts\python.exe -m ruff check src tests` → `All checks passed!`
- `.\.venv\Scripts\python.exe -m pytest tests/unit/test_pantallas_finales.py -v` → `8 passed in 4.27s`
- `.\.venv\Scripts\python.exe -m pytest tests/unit` → `208 passed, 1 deselected in 83.98s`
- `.\.venv\Scripts\python.exe -m pea.gui --autoprueba` → 24 capturas generadas, todas sin barras horizontales (0 barras).
- Inspección visual de capturas oficiales:
  - `datos\capturas\oficiales\pantalla_07_acerca_1100x700.png`
  - `datos\capturas\oficiales\pantalla_07_acerca_1366x768.png`
  - `datos\capturas\oficiales\pantalla_07_acerca_1920x1080.png`

## Decisiones
- Se utilizó el token institucional [`TEXTO_SOBRE_OSCURO`](file:///c:/dev/PEAi-Taller2/src/pea/gui/estilo.py) (`#FFFFFF`) para `lbl_facultad`, garantizando cumplimiento estricto de accesibilidad WCAG AAA y evitando la introducción de cualquier color literal.
- En la ficha técnica, un único `QGridLayout` con `columnStretch(0, 1)` y `columnStretch(1, 3)` proporciona una alineación vertical perfecta entre todas las filas, superando la dispersión que producían los `QHBoxLayout` independientes anteriores.

## Pendientes y siguiente paso
- Ejecutar verificación del cerebro con `python tools/brain/verificar_brain.py`.
- Realizar commit con prefijo `fix:`.
