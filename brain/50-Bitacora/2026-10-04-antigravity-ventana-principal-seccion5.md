---
tipo: bitacora
estado: revisado
creado: 2026-10-04
actualizado: 2026-10-04
relacionado:
  - "[[00-Inicio]]"
  - "[[GUI-Diseno-Python]]"
  - "[[ADR-0012-Diseno-GUI-y-navegacion]]"
  - "[[ADR-0017-Tecnologia-de-interfaz-Qt-Widgets]]"
origen: "Prompt 12: Ventana principal institucional segun seccion 5"
agente: "Antigravity"
rama: "feat/gui-rediseno-faf"
commit: "feat: ventana principal institucional segun seccion 5"
---

# Bitácora · Ventana principal institucional según sección 5

## Objetivo
Reescribir integralmente la ventana principal de la aplicación (`src/pea/gui/ventana_principal.py`) alineándola con las especificaciones de la sección 5 y responsividad de la sección 11 de [[GUI-Diseno-Python]]:
1. **Barra superior institucional (88 px)**:
   - Fondo con degradado horizontal institucional (`#002438` → `#003D5C` → `#004F70`).
   - Bloque de marca izquierda: ícono de átomo vectorial blanco (`logo_pea.svg`), logotipo textual «PEA-i», eslogan institucional en dos líneas («Plataforma de Estadística y Análisis de Investigación» / «Facultad de Ingenierías y Tecnológicas · Universidad Popular del Cesar») y píldora ámbar «Datos de demostración» cuando aplica.
   - Siete pestañas centrales con íconos SVG propios de 24 px (`BotonPestanaSuperior`): Inicio, Investigadores, Grupos, Productos, Análisis de redes, Importar, Configuración. Estado seleccionado con indicador inferior `#35B6E8` de 3 px al 40 % de ancho y anillo de foco accesible.
   - Bloque derecho: botón circular de 40 px para Deshacer (`BotonDeshacerSuperior`) con contador reactivo y desplegable `PopoverHistorial`, avatar circular con iniciales del usuario autenticado, botón «Cerrar sesión» con diálogo de confirmación y enlace «ⓘ Acerca de».
   - Filete institucional inferior de 3 px (`FileteInstitucionalUPC`) dividido en tres segmentos (`#005A36`, `#00843D`, `#A4C639`).
2. **Franjas reactivas de estado**:
   - Franja superior de advertencia de revisión remota (`#FFF8E1`) con mensaje descriptivo y botón «Recargar ahora».
   - Franja de error de red sin conexión (`#FDF2F2`) cuando el servicio opera desconectado.
3. **Área central apiladora**:
   - `QStackedWidget` con transición de desvanecimiento animada de 200 ms (`animar_desvanecimiento`), respetando `PEA_SIN_ANIMACIONES`.
   - Enumeración tipada `Pantalla` (`INICIO=0` a `ACERCA=7`) y navegación programática vía `seleccionar_pantalla`.
   - Marcadores contextuales (`MarcadorPantalla`) de 56 px con `ChipVentana` integrado (filtro global de años) y estado vacío estructurado para pantallas en construcción, manteniendo operativas las pantallas existentes.
4. **Pie institucional (72 px / 44 px)**:
   - Contenedor en color `#F3F7FB` con filete superior `#D2E4F0`.
   - Pastilla blanca redondeada de 52×52 px con el escudo oficial de la Universidad Popular del Cesar (`logo_upc.png`) y rótulo «PEA-i».
   - Dos líneas de texto institucional de la Universidad Popular del Cesar, Facultad y programa de Ingeniería de Sistemas.
   - Indicadores vivos a la derecha: estado de conexión con punto coloreado (verde/ámbar/rojo), chips de revisión, contador de deshacer y cola de tareas asíncronas.
5. **Responsividad (sección 11)**:
   - Adaptación dinámica de ancho: oculta el eslogan cuando ancho < 1240 px, compacta las pestañas a solo ícono cuando ancho < 1120 px.
   - Adaptación dinámica de alto: reduce el pie a 44 px y oculta el texto secundario cuando alto < 760 px.
   - Barra de título oscura nativa en Windows mediante DWM (`DWMWA_USE_IMMERSIVE_DARK_MODE`).
   - Atajos globales de teclado: `Ctrl+1..7`, `Ctrl+Z`, `Ctrl+F`, `F5`, `Ctrl+S`, `Alt+←`, `Esc`.

## Qué se hizo
- En `src/pea/version.py`: se agregaron las constantes oficiales `NOMBRE_COMPLETO`, `ESLOGAN_LINEA_1` y `ESLOGAN_LINEA_2`.
- En `src/pea/gui/ventana_principal.py`: se rediseñó completamente la arquitectura de la ventana con las clases `FileteInstitucionalUPC`, `BotonPestanaSuperior`, `BotonDeshacerSuperior`, `MarcadorPantalla`, `Pantalla` y `VentanaPrincipal`. Se conservaron los atributos públicos de retrocompatibilidad `_btn_deshacer`, `_apilador`, `_pestanas` y `_pie`.
- En `src/pea/gui/__init__.py`: se exportó la enumeración `Pantalla` para uso público.
- En `tests/unit/test_gui_completa.py`: se modernizaron las pruebas unitarias para validar las 8 pantallas de la nueva arquitectura, navegación por atajos, cambios de tamaño responsivos, actualización de estado global y franjas de advertencia.
- Se ejecutó `python -m pea.gui --autoprueba`, generando y validando capturas offscreen en `datos/capturas/` (`pantalla_inicio_1360x820.png`, `pantalla_inicio_1100x700.png`, `pantalla_inicio_1600x900.png`) frente al diseño de referencia `ref-inicio.png` y `ref-inicio-acabado.jpg`.

## Comandos y resultados
- `ruff check src tests`: 0 errores y advertencias.
- `pytest tests/unit`: 121 pruebas unitarias aprobadas (0 fallas, 1 deseccionada de red).
- `python -m pea.gui --autoprueba`: generación exitosa de las 3 resoluciones responsivas.
- `python tools/brain/verificar_brain.py`: validación de la bóveda sin errores ni advertencias.

## Decisiones
- **Manejo exclusivo en QButtonGroup al alternar con pantallas externas**: Para permitir desmarcar todas las pestañas superiores al navegar a la pantalla «Acerca de», se conmuta temporalmente `setExclusive(False)` sobre el grupo de botones, se desmarcan y se restablece `setExclusive(True)`.
- **Integración de filtro de años en la barra de contexto**: Cada pantalla cuenta en su encabezado contextual con un `ChipVentana` que despliega el popover de selección de período (Modelo 2024, quinquenio, todos o rango personalizado) sincronizado con el modelo global `FiltroAnios`.
- **Detección tolerante de modo oscuro en Windows**: Se invoca `DwmSetWindowAttribute` con manejo seguro de excepciones para evitar cualquier fallo de arranque en plataformas que no sean Windows o versiones anteriores a Windows 10/11.

## Pendientes y siguiente paso
- Desarrollar la pantalla de Inicio completa integrando los componentes de gráficos (barras apiladas, dona doble, minigráfico y mini red de coautoría) consumiendo directamente `ServicioAplicacion`.
