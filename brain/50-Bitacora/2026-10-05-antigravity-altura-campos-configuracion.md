---
tipo: bitacora
estado: revisado
creado: 2026-10-05
actualizado: 2026-10-05
relacionado:
  - "[[GUI-Diseno-Python]]"
  - "[[2026-10-05-antigravity-auditoria-qa-gui]]"
origen: "Corrección de altura mínima y maquetación de campos en pantalla de Configuración"
agente: "Antigravity"
rama: "master"
commit: "fix: establecer altura minima de 36 px en campos de configuracion"
---

# Bitácora · Altura Mínima de 36 px y Responsividad en Pantalla de Configuración

## Objetivo
Corregir los defectos detectados en la pantalla de Configuración (`src/pea/gui/pantallas/configuracion.py`):
1. Asegurar que los cuatro campos `QLineEdit` de acceso a Supabase (URL, clave publicable, correo de usuario y contraseña) posean una altura mínima garantizada de 36 px (`ALTURA_CAMPO_MINIMA = 36`), de modo que el texto y los placeholders nunca se corten verticalmente en ninguna resolución.
2. Centralizar la medida de altura en tokens de estilo oficiales en `src/pea/gui/estilo.py` (`ALTURA_CAMPO_MINIMA: Final[int] = 36`, `ALTURA_CAMPO: Final[int] = ALTURA_CAMPO_MINIMA`), respetando el guardián de estilos y evitando números mágicos fuera de la capa de diseño.
3. Preservar la tipografía oficial de 11 pt (`estilo.TAMANO_CUERPO`), la hoja de estilos global y el comportamiento responsive sin barras de desplazamiento horizontal.
4. Envolver la sección de conexión en un contenedor desplazable vertical (`QScrollArea` sin barra horizontal) para evitar que en resolución compacta (1100×700) el `QFormLayout` colapse o solape verticalmente los campos de entrada.
5. Incorporar pruebas de regresión unitarias que verifiquen las alturas mínimas y alturas efectivas ($\ge 36$ px) y la tipografía de los cuatro campos en resoluciones estándar y compactas.

## Qué se hizo
- En [`src/pea/gui/estilo.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/estilo.py):
  - Se agregaron los tokens oficiales `ALTURA_CAMPO_MINIMA: Final[int] = 36` y `ALTURA_CAMPO: Final[int] = ALTURA_CAMPO_MINIMA` en la sección de radios de esquina y dimensiones de controles (sección 4.3).
- En [`src/pea/gui/pantallas/configuracion.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/pantallas/configuracion.py):
  - Se importó `ALTURA_CAMPO_MINIMA` y se aplicó explícitamente `setMinimumHeight(ALTURA_CAMPO_MINIMA)` a los cuatro campos: `self.txt_url`, `self.txt_clave`, `self.txt_correo` y `self.txt_pass`.
  - En `_crear_seccion_conexion()`, se envolvió el contenedor en un `QScrollArea` responsive con `setWidgetResizable(True)`, `setFrameShape(QFrame.Shape.NoFrame)`, `setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)` y fondo transparente, garantizando que en alturas reducidas (como 700 px) las dos tarjetas («Estado de la Conexión» y «Parámetros de Acceso a Supabase (HTTPS)») mantengan su altura natural sin comprimir ni solapar los controles.
- En [`tests/unit/test_pantallas_finales.py`](file:///c:/dev/PEAi-Taller2/tests/unit/test_pantallas_finales.py):
  - Se agregó la prueba unitaria `test_pantalla_configuracion_altura_minima_campos`, comprobando que `minimumHeight() >= 36`, `minimumHeight() == estilo.ALTURA_CAMPO_MINIMA`, `height() >= 36` y `font().pointSize() >= estilo.TAMANO_CUERPO` para los cuatro `QLineEdit`.
- En [`tests/unit/test_pantallas_compactas.py`](file:///c:/dev/PEAi-Taller2/tests/unit/test_pantallas_compactas.py):
  - Se extendió `test_configuracion_sin_desborde_y_splitter_separado` verificando `minimumHeight() >= 36` y `height() >= 36` en resoluciones 1100×700 y 1366×768 para los cuatro campos.

## Comandos ejecutados y resultados
- `ruff check src tests`: Todos los archivos aprobados (0 advertencias, 0 errores).
- `pytest tests/unit/test_pantallas_finales.py tests/unit/test_pantallas_compactas.py tests/unit/test_estilo_recursos.py -v`: 32/32 pruebas aprobadas en 4.20s.
- `python -m pea.gui --autoprueba`: 24 capturas generadas satisfactoriamente. En `pantalla_06_configuracion_*.png`:
  - En 1100×700, 1366×768 y 1920×1080 los cuatro campos miden $\ge 36$ px de alto, los placeholders son legibles y centrados, no hay solapamiento ni recorte vertical, y no existe barra horizontal (0 barras reportadas).
- `scripts/diagnostico_desborde.py`: «Areas con barra horizontal visible: ninguna» en las tres resoluciones.
- `pytest tests/unit -v`: 204 pruebas unitarias aprobadas (204 passed, 1 deselected en 79.11s).
