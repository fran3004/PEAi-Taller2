---
tipo: bitacora
estado: revisado
creado: 2026-10-06
actualizado: 2026-10-06
relacionado:
  - "[[GUI-Diseno-Python]]"
  - "[[2026-10-05-antigravity-auditoria-qa-gui]]"
origen: "Auditoría y corrección de botones deshabilitados en Importar y Configuración"
agente: "Antigravity"
rama: "master"
commit: "fix: auditar y corregir botones deshabilitados en importar y configuracion"
---

# Bitácora · Auditoría y Corrección de Botones Deshabilitados en Importar y Configuración

## Objetivo
Auditar y corregir los botones en estado deshabilitado en las pantallas de **Importar** y **Configuración**:
- «Encolar CSV», «Encolar PDF», «Encolar URL SCIENTI», «Procesar siguiente» ([`src/pea/gui/pantallas/importar.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/pantallas/importar.py))
- «Conectar con Supabase» ([`src/pea/gui/pantallas/configuracion.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/pantallas/configuracion.py))

Garantizar:
1. Contraste WCAG 2.1 AA ($\ge 4.5:1$) estricto en estado `:disabled` usando la arquitectura centralizada de tokens de [`src/pea/gui/estilo.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/estilo.py).
2. Ausencia de QSS inline o selectores más específicos que sobrescriban u oculten el estilo deshabilitado.
3. Responsividad y legibilidad completa de los textos de los botones en las tres resoluciones oficiales (1100×700, 1366×768 y 1920×1080), impidiendo que se trunquen o colapsen por empaquetamiento rígido en sus tarjetas.
4. Pruebas de regresión unitarias automatizadas que comprueben la ausencia de estilos inline, el estado `:disabled`, el contraste WCAG y la holgura geométrica ($ancho \ge texto + 20\text{ px}$).

## Diagnóstico y Causa Raíz
1. **Auditoría de Especificidad QSS e Inline**:
   - Se verificó que ninguno de los cinco botones objetivo poseía estilos QSS inline que sobrescribieran la pseudoclase `:disabled`.
   - En [`src/pea/gui/estilo.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/estilo.py), `css_boton()` generaba estilos de variantes (`#primario`, `#secundario`, `#peligro`, `#icono`), pero no incluía explícitamente las reglas de pseudoclases `:disabled` para las variantes locales.
   - En `generar_hoja_estilos()`, `QPushButton#primario:disabled` contaba con fondo `#082338` y texto `#FFFFFF` (contraste 16.06:1), pero faltaba `border: none;` explícito para evitar bordes residuales del estado normal.
2. **Causa Raíz de la Pérdida de Legibilidad / Truncamiento**:
   - En `tarjeta_csv` ([`src/pea/gui/pantallas/importar.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/pantallas/importar.py)), `self._combo_tipo_csv` y `self._btn_encolar_csv` compartían la misma fila horizontal (`fila_tipo`). En 1100×700, donde cada tarjeta mide ~330 px, el combobox forzaba al botón `btn_encolar_csv` a reducirse a solo 104 px, comprimiendo y truncando su texto de 165 px.
   - En `tarjeta_cola`, la botonera de acciones agrupaba múltiples botones en la cabecera, reduciendo `btn_procesar_siguiente` por debajo de su avance de texto de 270 px.
   - El cálculo previo de `QFontMetrics(btn.font())` se realizaba antes de que Qt aplicara la hoja de estilo general (`polish`), por lo que medía la fuente base de 9 pt en lugar de la fuente Inter de 11 pt en negrita requerida por los tokens de diseño.

## Qué se hizo
- En [`src/pea/gui/estilo.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/estilo.py):
  - Se incorporó formalmente el par `(TEXTO_DESHABILITADO, SUPERFICIE_DESHABILITADA)` a `PARES_CONTRASTE_TABLA_4_1` con ratio validado de 6.40:1.
  - Se actualizó `css_boton(variante)` para emitir reglas `:disabled` nativas usando `SUPERFICIE_DESHABILITADA` y `TEXTO_DESHABILITADO` para variantes secundarias, de peligro e iconos.
  - En `generar_hoja_estilos()`, se aseguró que `QPushButton#primario:disabled` aplique `background-color: {PRIMARIO_DESHABILITADO}; color: {TEXTO_DESHABILITADO_SOBRE_PRIMARIO}; border: none;`.
- En [`src/pea/gui/pantallas/importar.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/pantallas/importar.py):
  - Se separó la selección de tipo de CSV del botón de encolado: `combo_tipo_csv` ocupa su propia fila (`fila_tipo`) y `btn_encolar_csv` se ubica en `fila_csv_opts` con stretch elástico.
  - Se incorporó `btn.ensurePolished()` previo a la medición con `QFontMetrics` para garantizar que se mida la tipografía estilizada real (11 pt negrita).
  - Se fijó `setMinimumWidth` con holgura simétrica para `btn_encolar_csv`, `btn_encolar_pdf`, `btn_encolar_url`, `btn_procesar_siguiente` y `btn_procesar_todas`.
- En [`src/pea/gui/pantallas/configuracion.py`](file:///c:/dev/PEAi-Taller2/src/pea/gui/pantallas/configuracion.py):
  - Se agregó `QFontMetrics` y se ejecutó `ensurePolished()` y `setMinimumWidth` sobre `btn_conectar`, `btn_demo` y `btn_desconectar`, impidiendo su colapso dimensional.
- En [`tests/unit/test_gui_completa.py`](file:///c:/dev/PEAi-Taller2/tests/unit/test_gui_completa.py):
  - Se añadió la prueba de regresión `test_botones_deshabilitados_importar_y_configuracion`, comprobando:
    - Ausencia total de QSS inline en los cinco botones.
    - Presencia de reglas de estilo para `:disabled` en la hoja de estilos global con contraste $\ge 4.5:1$.
    - Estado `isEnabled() == False` en condiciones iniciales.
    - Ancho efectivo superior al avance del texto en las tres resoluciones estándar (1100×700, 1366×768, 1920×1080).

## Comandos y resultados
- `ruff check src tests`: Todos los archivos aprobados (0 errores, 0 advertencias).
- `pytest tests/unit/test_gui_completa.py -k test_botones_deshabilitados_importar_y_configuracion -v`: 1/1 aprobado.
- `pytest tests/unit -v`: **206 pasadas**, 1 deseleccionada (red) en 88.55s.
- `python -m pea.gui --autoprueba`: 24 capturas oficiales generadas correctamente en `datos/capturas/oficiales/`; 0 barras horizontales visibles en todas las pantallas y resoluciones (1100×700, 1366×768, 1920×1080).
- `scripts/diagnostico_desborde.py`: `Areas con barra horizontal visible: ninguna` en 1100×700, 1366×768 y 1920×1080.
- `pytest tests/unit/test_estilo_recursos.py::test_guardian_estilos_sin_literales_en_gui`: Aprobado (1/1 OK).
- `tools/brain/verificar_brain.py`: Bóveda validada sin errores (109 notas inspeccionadas).

## Decisiones
- Se mantuvo intacto el sistema de tokens existente sin inventar nuevos colores literales.
- Se resolvió la colisión espacial en Importar reestructurando las filas de `tarjeta_csv` de manera vertical limpia en lugar de forzar anchos artificiales que causaran desbordamiento horizontal.

## Pendientes y siguiente paso
- Continuar con el plan de estabilización y pruebas de integración.

