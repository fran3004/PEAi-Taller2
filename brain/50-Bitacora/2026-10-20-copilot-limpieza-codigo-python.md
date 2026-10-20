---
tipo: bitacora
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[GUI-Diseno-Python]]"
  - "[[Estructuras]]"
origen: "Limpieza de código sin uso, Ruff/Vulture y espaciado de pestañas solicitado por el usuario"
agente: "Copilot"
rama: "feat/python-cierre-francisco"
commit: ""
---

# Bitácora · Limpieza de código Python

## Objetivo
Completar la limpieza verificada de código Python sin uso, dejar Ruff y Vulture
limpios y mejorar la separación entre las pestañas de navegación.

## Qué se hizo
- Se retiraron `animar_desvanecimiento` y `crear_animacion_propiedad`, que no
  tenían consumidores de producción, junto con sus pruebas específicas.
- Se eliminaron los métodos sin llamadas `limpiar_kpis`, `limpiar_contenido`,
  `limpiar_todos`, `obtener_celda`, `insertar_en`, `eliminar_en`,
  `a_lista_auxiliar`, `obtener_todos`, `simular_expiracion` y `crear_directo`;
  también se retiraron el alias `_pantalla_conectar`, el atributo
  `_columnas_ocultas`, el mapa de categorías redundante y los tokens/helpers de
  estilo sin referencias.
- Se adaptaron las pruebas a `Multilista.iterar_nodos()` y a un reloj simulado
  determinista. `Pila.ver_tope()` se renombró a `Pila.tope()` para ajustarse a
  la operación documentada; `Hipercubo5D.desacumular()` se conservó y ahora
  tiene prueba de reducción, poda y caso ausente.
- Se añadió `vulture>=2.14` a las dependencias de desarrollo y
  `tools/vulture_whitelist.py` documenta únicamente campos Pydantic y callbacks
  virtuales de Qt que Vulture no puede detectar por análisis estático.
- Se aplicaron las correcciones automáticas de Ruff en `tools/` y `scripts/`,
  y se corrigió manualmente la variable de respuesta no usada sin alterar la
  lectura de la respuesta de autenticación.
- La barra superior ahora garantiza una separación mínima de 12 px entre
  pestañas; la prueba verifica igualdad de separación en las tres resoluciones.
- Se conservaron `ajustar_columnas` y `MARGEN_CONTENIDO` porque tienen uso real
  en herramientas del repositorio. El diagnóstico `diagnostico_desborde.py`
  también se conserva: mide mínimos y barras horizontales, no duplica la
  autoprueba estricta de la GUI.

## Comandos y resultados
- `.venv\Scripts\python.exe -m ruff check src tests tools scripts`: aprobado,
  sin errores.
- `.venv\Scripts\python.exe -m vulture src tools/vulture_whitelist.py
  --min-confidence 80`: aprobado, sin hallazgos.
- `QT_QPA_PLATFORM=offscreen .venv\Scripts\python.exe -m pytest -q`: 276
  pasaron y 2 quedaron excluidas por configuración.
- `QT_QPA_PLATFORM=offscreen .venv\Scripts\python.exe -m pea.gui --autoprueba`:
  24 combinaciones pantalla/resolución, cero hallazgos.
- `git diff --check`: aprobado.

## Decisiones
Se preservan las API documentadas de las estructuras hechas a mano y las
sobrescrituras de Qt. Los falsos positivos dinámicos se explican en la lista
blanca, sin ampliar el umbral final de Vulture ni silenciar código sin
justificación.

## Pendientes y siguiente paso
- Continuar con la verificación de conteos remotos, paginación y separación
  entre datos de demostración y datos reales.
- Revisar manualmente las 24 capturas al cerrar las tareas visuales restantes.
