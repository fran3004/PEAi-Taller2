---
tipo: bitacora
estado: revisado
creado: 2026-10-04
actualizado: 2026-10-04
relacionado:
  - "[[00-Inicio]]"
  - "[[GUI-Diseno-Python]]"
  - "[[ADR-0011-Paridad-arquitectural-Python-Cpp]]"
  - "[[ADR-0012-Diseno-GUI-y-navegacion]]"
  - "[[ADR-0016-Alcance-de-pantallas-y-datos-del-boceto]]"
  - "[[ADR-0017-Tecnologia-de-interfaz-Qt-Widgets]]"
origen: "Pantallas finales de la interfaz Python: Importar (6.6), Configuracion (6.7) y Acerca de (6.8)"
agente: "Antigravity"
rama: "feat/gui-rediseno-faf"
commit: "feat: pantallas de importacion, configuracion y acerca de segun secciones 6.6-6.8"
---

# Bitácora · Pantallas de Importación, Configuración y Acerca de (Secciones 6.6, 6.7 y 6.8)

## Objetivo
Implementar y conectar las tres pantallas finales de la interfaz gráfica institucional de PEA-i (PySide6) conforme a las especificaciones de [[GUI-Diseno-Python]], completando la totalidad de las 8 pantallas oficiales del sistema:
1. **Pantalla de Importación (`PantallaImportar`, Sección 6.6)**:
   - Tres tarjetas superiores (`Tarjeta`): CSV (con combo selector de entidad), PDF oficial de MinCiencias y URL web de GrupLAC/CvLAC.
   - Componente interactivo `ZonaSoltarArchivo(QFrame)` con soporte de arrastrar y soltar (Drag and Drop), verificación de extensiones, botón «Examinar...» y botón de limpieza.
   - Tarjeta inferior con la cola FIFO propia de ingesta en memoria (`ServicioIngesta` / `cola_tareas`).
   - Controles «Tareas pendientes: N», botones «Procesar siguiente» y «Procesar todas», barra de progreso indeterminada durante ejecución.
   - Tabla estilizada (`TablaEstilizada`) con píldoras de estado (`Pendiente`, `En proceso`, `Completada`, `Falló`) mediante `PildoraDelegate`.
   - Notificaciones no bloqueantes tipo toast (`GestorAvisos` / `Toast`) con resumen detallado de entidades importadas.
2. **Pantalla de Configuración (`PantallaConfiguracion`, Sección 6.7)**:
   - Cabecera con selector segmentado (`SelectorSegmentado`) de dos secciones: «Conexión» y «Verificación cruzada».
   - **Sección «Conexión»**:
     - Tarjeta grande de estado con píldora de modo (`Supabase`, `Demostración`, `Desconectado`), servidor HTTPS, correo de usuario autenticado, revisión local/remota y aviso de motivo de bloqueo.
     - Formulario de conexión HTTPS a Supabase (URL, clave publicable protegida, correo, contraseña y casilla de entorno `PEA_USUARIO_CLAVE`).
     - Botones «Conectar con Supabase», «Cargar datos de demostración» y «Cerrar sesión / Desconectar».
   - **Sección «Verificación cruzada»**:
     - Tarjeta de contexto con principio de equivalencia observacional (ADR-0011) y botón «▶ Ejecutar Verificación Cruzada».
     - Banner de estado global (éxito o advertencia).
     - Tabla de pasos con píldoras de coincidencia («✔ COINCIDEN», «✖ DIFIEREN»).
     - Visores comparativos monoespaciados lado a lado (fuente Consolas 10 pt) para salida CLI de Python y CLI de C++.
3. **Pantalla Acerca de (`PantallaAcerca`, Sección 6.8)**:
   - Accesible desde el enlace «ⓘ Acerca de» en la barra superior (no es pestaña central).
   - Botón superior «← Volver al inicio» (`btn_volver`) que emite `volver_solicitado`.
   - Tarjeta institucional con degradado institucional, pastilla blanca con logo de la UPC y textos de la Facultad y Programa.
   - Tarjeta descriptiva del software con nombre oficial, versión y cita formal a la Convocatoria de Medición 2024 de MinCiencias.
   - Ficha técnica completa de arquitectura en capas, estructuras en memoria manuales, cálculo estadístico en Hipercubo 5D y paridad con C++17.
   - Tarjeta del equipo de desarrollo institucional y tarjeta de estado dinámico del sistema (modo, revisiones, cola y deshacer).

## Qué se hizo
- Se crearon los módulos correspondientes en `src/pea/gui/pantallas/`:
  - `importar.py`: `ZonaSoltarArchivo` y `PantallaImportar` con procesamiento asíncrono vía `EjecutorHilos` y fallback sincrónico para pruebas unitarias. Notificaciones flotantes efímeras tipo `Toast` y emisión de señal `datos_modificados`.
  - `configuracion.py`: `PantallaConfiguracion` con `SelectorSegmentado`, `QStackedWidget`, formularios HTTPS con modo enmascarado de claves, ejecución de verificación cruzada con tabla y visores comparativos.
  - `acerca.py`: `PantallaAcerca` con `QScrollArea`, diseño institucional UPC con tokens de `estilo.py`, ficha técnica y sincronización reactiva de estado.
- Se actualizaron las exportaciones públicas en `src/pea/gui/pantallas/__init__.py`.
- Se añadieron métodos de compatibilidad en componentes base:
  - `Pildora.establecer_variante(variante)` y `Pildora.text()`.
  - `TablaEstilizada.model()` para retornar el proxy activo y brindar paridad completa con la interfaz tradicional de `QTableView`.
- Se integraron las tres pantallas en `src/pea/gui/ventana_principal.py`:
  - Se sustituyeron las instancias anteriores por `PantallaImportar`, `PantallaConfiguracion` y `PantallaAcerca`.
  - Se conectaron las señales `volver_solicitado`, `estado_actualizado` y `datos_modificados`.
  - Se amplió la rutina `ejecutar_autoprueba()` para capturar las 8 pantallas oficiales del sistema (`INICIO`, `INVESTIGADORES`, `GRUPOS`, `PRODUCTOS`, `REDES`, `IMPORTAR`, `CONFIGURACION`, `ACERCA`) en las resoluciones oficiales (1100×700, 1366×768, 1920×1080).
- Se implementaron 5 pruebas unitarias completas en `tests/unit/test_pantallas_finales.py`:
  1. `test_zona_soltar_archivo`: interacción de Drag and Drop, establecimiento de ruta, botón de limpieza y señales.
  2. `test_pantalla_importar_estructura_y_encolamiento`: tarjetas de fuentes CSV/PDF/URL, encolamiento en cola FIFO propia, procesamiento secuencial y masivo.
  3. `test_pantalla_configuracion_selector_y_conexion`: alternancia de selector segmentado, conexión, demostración y desconexión.
  4. `test_pantalla_configuracion_verificacion_cruzada`: ejecución del servicio de verificación cruzada, llenado de tabla con píldoras y visores monoespaciados.
  5. `test_pantalla_acerca_contenido_y_volver`: visualización de tarjetas técnicas e institucionales, botón volver y actualización dinámica.

## Verificación
- `ruff check src tests`: 100% aprobado sin errores ni advertencias.
- `pytest tests/unit`: 166 pruebas unitarias aprobadas, 1 deselected (de red), 0 fallas (52.10 s).
- `python -m pea.gui --autoprueba`: Ejecutado exitosamente, generando capturas en PNG para las 8 pantallas en las tres dimensiones estipuladas.
- `python tools/brain/verificar_brain.py`: Bóveda íntegra (88 notas inspeccionadas, 0 errores, 0 advertencias).
