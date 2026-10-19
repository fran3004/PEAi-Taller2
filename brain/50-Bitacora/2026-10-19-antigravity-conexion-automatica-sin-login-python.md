---
tipo: bitacora
estado: revisado
creado: 2026-10-19
actualizado: 2026-10-19
relacionado:
  - "[[00-Inicio]]"
  - "[[GUI-Diseno-Python]]"
origen: "Solicitud del usuario de eliminar el formulario de inicio de sesión manual y conectar automáticamente o cargar demostración en Python"
agente: "Antigravity"
rama: "master"
commit: "pendiente"
---

# Bitácora · Conexión automática sin login manual en Python

## Objetivo
Eliminar el formulario de inicio de sesión manual en la aplicación Python (`pea.gui`) para que directamente al entrar al programa se muestre la opción de cargar la base de datos (conectándose automáticamente desde la configuración del entorno) o cargar los datos de demostración, sin dañar ninguna funcionalidad existente ni tocar el módulo C++.

## Qué se hizo
- Se normalizó `base_url` en `src/pea/cliente_http.py` (`ClienteHTTPSupabase.__init__`) para remover barras finales y el sufijo `/rest/v1` en caso de que la variable de entorno `PEA_SUPABASE_URL_PROD` lo incluya, evitando rutas duplicadas `/rest/v1/rest/v1/...` o `/rest/v1/auth/v1/token`.
- Se añadió carga automática de variables desde `.env` (sin exponer ni imprimir secretos) y conexión automática por defecto en `src/pea/servicios/servicio_aplicacion.py` (`ServicioAplicacion.conectar()`), usando las variables configuradas en el entorno (`usar_clave_entorno=True`).
- Se actualizó `src/pea/gui/pantallas/inicio.py` (`PantallaInicio`) para presentar directamente al inicio las opciones **«Cargar base de datos (Supabase)»** y **«Cargar datos de demostración»**, ejecutando `self._servicio.conectar()` automáticamente al pulsar la primera opción y emitiendo `datos_modificados` hacia `VentanaPrincipal`.
- Se actualizó `src/pea/gui/pantallas/configuracion.py` (`PantallaConfiguracion`) para ocultar los campos de login manual (`URL`, `Clave publicable`, `Correo`, `Contraseña`, `Usuario autenticado`) y presentar la tarjeta **«Origen de Datos (Conexión Automática)»** con los botones de conexión directa y carga de demostración, manteniendo la compatibilidad con todas las pruebas unitarias.
- Se ajustó `src/pea/gui/componentes/estado_vacio.py` para garantizar altura mínima y ancho adaptable en los botones de acción del estado vacío.
- Se añadió la prueba unitaria `test_conexion_automatica_sin_login_manual` en `tests/unit/test_pantalla_inicio.py`.

## Comandos y resultados
- `.\.venv\Scripts\ruff.exe check src/ tests/` → `All checks passed!`.
- `.\.venv\Scripts\pytest.exe tests/unit/test_pantalla_inicio.py tests/unit/test_pantallas_finales.py tests/unit/test_pantallas_compactas.py tests/unit/test_gui_completa.py -v` → `47 passed`.
- `.\.venv\Scripts\python.exe -m pea.gui --autoprueba` → `Autoprueba de GUI Python completada exitosamente` (0 barras y 0 widgets fuera en `06_configuracion` en `1100x700`, `1366x768` y `1920x1080`).
- `.\.venv\Scripts\python.exe tools/brain/verificar_brain.py` → validación de la bóveda `brain/`.

## Decisiones
- Se conservaron los atributos internos `txt_url`, `txt_clave`, `txt_correo`, `txt_pass`, `chk_entorno` y `lbl_usuario` ocultos (`setVisible(False)`) en `PantallaConfiguracion` para eliminar por completo el formulario de login manual de la vista del usuario sin romper contratos de inspección en la suite de pruebas existente.
- La normalización de `base_url` en `ClienteHTTPSupabase` garantiza que tanto URLs raíz (`https://<id>.supabase.co`) como URLs con sufijo REST (`https://<id>.supabase.co/rest/v1/`) funcionen de forma transparente con Auth y PostgREST.

## Pendientes y siguiente paso
- Continuar con las siguientes tareas del proyecto manteniendo la paridad funcional y las pruebas en verde.

