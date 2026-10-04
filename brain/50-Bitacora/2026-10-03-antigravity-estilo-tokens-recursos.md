---
tipo: bitacora
estado: revisado
creado: 2026-10-03
actualizado: 2026-10-03
relacionado:
  - "[[_Indice]]"
  - "[[GUI-Diseno-Python]]"
  - "[[GUI-paridad]]"
  - "[[ADR-0016-Alcance-de-pantallas-y-datos-del-boceto]]"
  - "[[ADR-0017-Tecnologia-de-interfaz-Qt-Widgets]]"
origen: "Implementación de tokens de diseño, formateador regional y recursos gráficos según sección 4 de GUI-Diseno-Python.md"
agente: "antigravity"
rama: "feat/gui-rediseno-faf"
commit: "pendiente"
---

# Bitácora · Tokens de Estilo, Formateo Regional y Recursos Gráficos GUI

## Objetivo
Implementar la base visual, estilística y de recursos de la interfaz gráfica PySide6 según las especificaciones de la sección 4 de [[GUI-Diseno-Python]]:
1. Reescribir `src/pea/gui/estilo.py` con la totalidad de los tokens de color, tipografía, espaciado, radios, sombras y duraciones de animación, eliminando completamente la paleta obsoleta (`#003366`, `#0D47A1`).
2. Crear `src/pea/gui/formato.py` con soporte para el `QLocale` colombiano (`es_CO`), formateo de miles con punto y decimales con coma, porcentajes, extracción de iniciales para avatares y nomenclaturas oficiales de tipologías Minciencias 2024.
3. Generar y organizar los recursos gráficos vectoriales e institucionales en `src/pea/gui/recursos/`: 7 iconos de pestañas en SVG (24×24, trazo 1.75, un color), 5 iconos utilitarios, `logo_pea.svg` (átomo blanco institucional) y `logo_upc.png` recortado al contenido a partir del original sin alterar la fuente en `docs/entrada/identidad/logo_upc.png`.
4. Construir un cargador de recursos con `QtSvg.QSvgRenderer` y caché en memoria para renderizado nítido de pixmaps e iconos.
5. Desarrollar pruebas unitarias completas que verifiquen el contraste WCAG 2.1 (≥ 4.5:1) de cada par de la tabla 4.1, la precisión del formateador y la existencia y validez de todos los recursos gráficos.

## Qué se hizo

1. **Tokens de estilo (`src/pea/gui/estilo.py`)**:
   - Se definieron todas las constantes de color: degradado del encabezado (`ENCABEZADO_INICIO`, `ENCABEZADO_MEDIO`, `ENCABEZADO_FIN`), acento (`ACENTO`), primario y sus estados de hover/pulsado (`PRIMARIO`, `PRIMARIO_HOVER`, `PRIMARIO_PULSADO`), superficies (`SUPERFICIE`, `FICHA`, `PIE`, `FONDO_APP`), líneas (`LINEA`, `LINEA_FUERTE`), textos (`TEXTO`, `TEXTO_SECUNDARIO`, `TEXTO_SOBRE_OSCURO`, `TEXTO_SOBRE_OSCURO_SUAVE`, `ENLACE`), verde institucional UPC (`UPC_VERDE_OSCURO`, `UPC_VERDE`, `UPC_VERDE_CLARO`), estados semánticos (`EXITO`, `AVISO`, `ERROR`, `INFO`) y sus respectivos fondos.
   - Se incorporaron los colores canónicos de datos: tipologías (`GNC`, `DTI`, `ASC`, `FRH`), validaciones (`Avalado`, `Con soporte`, `No avalado`), categorías de investigador (`Emérito`, `Senior`, `Asociado`, `Junior`, sin categoría) y aristas de grafos.
   - Se implementaron las funciones `calcular_luminancia_relativa` y `calcular_radio_contraste` basadas en la fórmula oficial WCAG 2.1 para verificar programáticamente la tabla 4.1.
   - Se definieron los tokens tipográficos (familia del sistema `"Segoe UI"`, tamaños desde marca 30 pt hasta eslogan 9 pt, y pesos correspondientes), espaciados en escala de 4 (4, 8, 12, 16, 20, 24, 32), radios (8, 12, 16, 999), especificaciones de sombras y parámetros de animación.
   - Se implementó `generar_hoja_estilos()` generando el QSS global consolidado.
   - Se eliminaron por completo las referencias y valores hex de la paleta previa (`#003366`, `#0D47A1`).
   - Se adaptaron las importaciones en `src/pea/gui/componentes/graficos.py` hacia los nuevos tokens.

2. **Formateador regional y textual (`src/pea/gui/formato.py`)**:
   - `formatear_entero`: números enteros con separador de miles usando punto (`1.234.567`).
   - `formatear_decimal`: números en coma flotante con coma decimal y punto de miles (`1.234,56`).
   - `formatear_porcentaje`: formateo porcentual localizado con coma (`25,5 %`).
   - `iniciales_nombre`: extracción determinista de iniciales de personas o grupos para avatares (2 caracteres en mayúscula, manejo de cadenas vacías o con espacios con `"--"`).
   - `NOMBRES_TIPOLOGIAS` y `DESCRIPCIONES_TIPOLOGIAS`: equivalencias canónicas oficiales del Modelo Minciencias 2024 para GNC, DTI, ASC y FRH.
   - Funciones complementarias para nombres de validaciones y categorías de investigadores.

3. **Recursos gráficos (`src/pea/gui/recursos/`)**:
   - Se crearon los 7 iconos SVG de navegación: `inicio.svg`, `investigadores.svg`, `grupos.svg`, `productos.svg`, `redes.svg`, `importar.svg`, `configuracion.svg`.
   - Se crearon los iconos utilitarios: `deshacer.svg`, `cerrar_sesion.svg`, `buscar.svg`, `acerca.svg`, `limpiar.svg`.
   - Se diseñó el vector institucional `logo_pea.svg` con la estructura del átomo (núcleo y órbitas en trazo blanco).
   - Se generó `logo_upc.png` recortado al contenido visual útil (540×471 px) preservando intacto el archivo original en `docs/entrada/identidad/logo_upc.png`.
   - Se implementó el cargador `src/pea/gui/recursos/cargador.py` con resolución de rutas, caché en memoria de instancias `QSvgRenderer`, generación de `QPixmap` escalados y construcción de `QIcon`.

4. **Pruebas unitarias (`tests/unit/test_estilo_recursos.py`)**:
   - Se escribieron 15 pruebas unitarias verificando contraste WCAG 2.1 en todos los 21 pares de la tabla 4.1, ausencia de la paleta vieja, integridad de los tokens, generación del QSS, comportamiento de las funciones de formateo, extracción de iniciales, existencia física de los 14 archivos de recursos gráficos, carga de renderers SVG, pixmaps y creación de iconos con `pytest-qt` (`qapp`).

## Comandos y resultados
- `ruff check src tests`: validación sin errores (código limpio y formateo según estándares).
- `pytest tests/unit/test_estilo_recursos.py`: 15 de 15 pruebas aprobadas en 0.90 s.
- `pytest tests/unit`: 101 de 101 pruebas aprobadas (1 deseleccionada correspondiente a red) en 10.06 s.
- `python tools/brain/verificar_brain.py`: validación exitosa de la bóveda Obsidian (78 notas inspeccionadas, 0 errores, 0 advertencias).

## Decisiones
- Se utilizó el fixture `qapp` en las pruebas de `QPixmap` y `QIcon` para asegurar la inicialización adecuada del subsistema gráfico offscreen de Qt en Windows.
- La función de iniciales `iniciales_nombre` se diseñó de manera determinista basada en las primeras letras de las primeras palabras relevantes, garantizando consistencia en avatares personales e institucionales.

## Pendientes y siguiente paso
- Proceder con la construcción de los componentes de interfaz reutilizables (barra superior con pestañas y filete institucional de 3 px, barra de contexto con filtro de años global, tarjetas con sombra y barra lateral de acento, pie institucional, toasts y fichas KPI).
