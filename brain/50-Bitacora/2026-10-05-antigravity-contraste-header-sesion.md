---
tipo: bitacora
estado: revisado
creado: 2026-10-05
actualizado: 2026-10-05
relacionado:
  - "[[GUI-Diseno-Python]]"
  - "[[2026-10-05-antigravity-auditoria-qa-gui]]"
  - "[[2026-10-05-antigravity-maquetacion-productos]]"
origen: "Corrección de contraste WCAG y estilos QSS del bloque superior derecho en ventana_principal.py"
agente: "Antigravity"
rama: "master"
commit: "fix: corregir contraste wcag y estilos qss en bloque superior derecho del header"
---

# Bitácora · Corrección de Contraste WCAG y Estilos QSS en Bloque Superior Derecho del Header

## Objetivo
Corregir de forma integral el bloque superior derecho de la barra de encabezado institucional en [`src/pea/gui/ventana_principal.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/ventana_principal.py):
1. Asegurar que los botones «Cerrar sesión» y «Acerca de» cumplan con el contraste WCAG ($\ge 4.5:1$ en nivel AA y $\ge 7.0:1$ en nivel AAA) en todos sus estados: normal, hover y foco con teclado.
2. Eliminar cadenas QSS mal formadas sin interpolación `f""` en `btn_cerrar_sesion`, `btn_accion` y `_pastilla_logo` que pasaban nombres de tokens de Python como texto plano `{estilo.SUPERFICIE}` sin evaluar.
3. Garantizar coherencia entre el fondo institucional oscuro (`ENCABEZADO_FIN` = `#0E405C`) y el texto claro, evitando que los contenedores hijos de la barra hereden fondos opacos claros del widget central de la aplicación.
4. Verificar el resultado visual en las tres resoluciones oficiales: 1100×700, 1366×768 y 1920×1080.

## Qué se hizo
- En [`src/pea/gui/ventana_principal.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/ventana_principal.py):
  - En `_construir_ui()`, se asignó `setObjectName("fondo")` a `widget_central` en lugar de una regla en línea `setStyleSheet("background-color: ...")` sin selector que se propagaba indebidamente en cascada a todos los widgets descendientes, pintando recuadros claros no deseados sobre la barra superior.
  - En `BotonDeshacerSuperior`, se corrigió la hoja de estilo de `btn_accion` para que utilice un f-string válido con interpolación de `{estilo.SUPERPOSICION_CLARA_*}` y se añadió el estado de foco `:focus` con borde de acento accesible (`{ACENTO}`).
  - En `_crear_barra_superior()`:
    - Se asignó `setObjectName("btnCerrarSesion")`, `accessibleName("Cerrar sesión")`, tamaño de ícono explícito de 14×14 px y `FocusPolicy.StrongFocus` a `btn_cerrar_sesion`.
    - Se formateó la hoja de estilos de `btn_cerrar_sesion` mediante f-string con tokens institucionales: texto blanco `{TEXTO_SOBRE_OSCURO}` (11.01:1 sobre el fondo oscuro), borde `{estilo.SUPERPOSICION_CLARA_40}`, hover `{estilo.SUPERPOSICION_CLARA_14}` (7.43:1) y foco `:focus` con borde de 2 px en `{ACENTO}` (3.55:1 de contraste en indicador de foco).
    - Se asignó `setObjectName("btnAcercaDe")`, `accessibleName("Acerca de PEA-i")` y `FocusPolicy.StrongFocus` a `btn_acerca`.
    - Se formateó la hoja de estilos de `btn_acerca` mediante f-string: color `{TEXTO_SOBRE_OSCURO_SUAVE}` (7.60:1 sobre el fondo oscuro), hover con `{TEXTO_SOBRE_OSCURO}` y subrayado, y foco `:focus` con borde de 1 px en `{ACENTO}`.
    - Se ajustó el layout vertical `col_sesion` con espaciado de 3 px y alineación centrada verticalmente.
  - En `_crear_pie_institucional()`, se convirtió la regla de `_pastilla_logo` a f-string para resolver el token `{estilo.RADIO_PESTANA_ACTIVA}`.
- En [`src/pea/gui/estilo.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/estilo.py):
  - En `generar_hoja_estilos()`, se añadió la regla explícita `QFrame#barraSuperior QWidget {{ background-color: transparent; }}` para garantizar que cualquier contenedor hijo dentro de la barra superior mantenga fondo transparente y permita lucir el degradado institucional continuo.
- En [`src/pea/gui/pantallas/redes.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/pantallas/redes.py) y [`src/pea/gui/red/vista_red.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/red/vista_red.py):
  - Se corrigieron llamadas con cadenas literales no interpoladas `QColor("{estilo.SUPERFICIE}")` y `self.setStyleSheet("background-color: {estilo.SUPERFICIE};")`.
- En [`tests/unit/test_gui_completa.py`](file:///c:/dev/PEAi-Taller2/tests/unit/test_gui_completa.py):
  - Se añadió la prueba `test_bloque_superior_derecho_contraste_y_estilos`:
    - Valida que `btnCerrarSesion` y `btnAcercaDe` posean nombres de objeto y nombres accesibles no nulos.
    - Comprueba ausencia de plantillas rotas o literales `{estilo.` o `{TEXTO` en sus hojas de estilo.
    - Verifica presencia explícita de los estados `:hover`, `:focus` y `:pressed`.
    - Evalúa matemáticamente los ratios de contraste WCAG: texto de cerrar sesión $\ge 7.0:1$ (11.01:1), texto de acerca de $\ge 7.0:1$ (7.60:1) y anillo de foco $\ge 3.0:1$ (4.72:1).
    - Comprueba visibilidad y tamaños mínimos en 1100×700, 1366×768 y 1920×1080.

## Comandos y resultados
1. `ruff check src tests`:
   - Salida: `All checks passed!`
2. `pytest tests/unit/test_gui_completa.py tests/unit/test_estilo_recursos.py -v`:
   - Salida: 32 passed en 196.66s.
3. `python -m pea.gui --autoprueba`:
   - Salida: 24 capturas oficiales actualizadas exitosamente con 0 barras de desplazamiento.
4. Inspección visual directa de capturas generadas:
   - [`pantalla_00_inicio_1100x700.png`](file:///c:/dev/PEAi-Taller2/datos/capturas/oficiales/pantalla_00_inicio_1100x700.png): fondo oscuro continuo y uniforme, sin recuadros blancos, botones con contraste AAA perfecto.
   - [`pantalla_00_inicio_1366x768.png`](file:///c:/dev/PEAi-Taller2/datos/capturas/oficiales/pantalla_00_inicio_1366x768.png): bloque derecho perfectamente centrado verticalmente, ícono de cerrar sesión nítido.
   - [`pantalla_00_inicio_1920x1080.png`](file:///c:/dev/PEAi-Taller2/datos/capturas/oficiales/pantalla_00_inicio_1920x1080.png): proporción y legibilidad impecables en pantalla panorámica.
5. `python tools/brain/verificar_brain.py`:
   - Salida: 105 notas inspeccionadas, 0 errores, 0 advertencias.

## Decisiones
- Se utilizó `TEXTO_SOBRE_OSCURO` (`#FFFFFF`) para «Cerrar sesión» y `TEXTO_SOBRE_OSCURO_SUAVE` (`#C9D8EA`) para «Acerca de», asegurando jerarquía visual entre el botón de acción principal de la cuenta y el enlace informativo secundario, manteniendo ambos por encima del estándar WCAG AAA ($\ge 7.0:1$).
- Para el foco con teclado, se empleó un anillo en `ACENTO` (`#35B6E8`), que ofrece un ratio de contraste de 4.72:1 contra el fondo oscuro del encabezado, superando el mínimo de 3:1 exigido por WCAG 2.1 para indicadores de interfaz.

## Pendientes y siguiente paso
- Tarea finalizada y verificada en todas las resoluciones.
