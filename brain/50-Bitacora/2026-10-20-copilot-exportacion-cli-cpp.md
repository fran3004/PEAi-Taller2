---
tipo: bitacora
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[Paridad-Python-Cpp]]"
  - "[[Contrato-de-datos]]"
origen: "Pruebas de la exportación CSV del CLI C++ y del escritor atómico"
agente: "Copilot"
rama: "feat/python-cierre-francisco"
commit: ""
---

# Bitácora · Exportación CLI C++

## Objetivo

Cerrar la brecha de prueba del comando `exportar-csv` en C++ y verificar que
los fallos del guardado atómico se informen sin dejar archivos temporales.

## Qué se hizo

- Se agregó una dependencia explícita de carga de catálogo a `pea::cli::ejecutar`
  para probar el despacho y la escritura sin red. La ruta normal de producción
  sigue creando el cliente configurado, recargando Supabase y cancelando ante
  errores de conexión o lectura.
- El caso de comando recorre `exportar-csv --directorio`, escribe las tres
  tablas y compara los bytes generados, con UTF-8 y CRLF.
- Se trasladó el guardado con `QSaveFile` al exportador de datos. El contrato
  limpia el mensaje de error al iniciar y reporta explícitamente fallos de
  apertura/guardado; la prueba confirma que el fallo no deja temporales.
- La prueba de fallo usa un directorio como destino para forzar un error del
  sistema de archivos; no requiere permisos especiales ni acceso remoto.

## Comandos y resultados

- `cmake --build ... --target pruebas_cpp pea-cpp`: correcto.
- `ctest --test-dir ... --output-on-failure`: 1/1 suite aprobada.
- `pruebas_cpp.exe --no-version`: 51 casos y 506 aserciones aprobados.
- `.venv\Scripts\python.exe -m pytest -q tests\unit\test_cli_exportacion.py`:
  4 pruebas aprobadas.
- `pea-cpp.exe --autoprueba`: 32 combinaciones de pantalla/tamaño y formularios,
  sin hallazgos.
- `git diff --check`: correcto.
- Sin conexiones a Supabase ni modificaciones remotas.

## Decisiones

- La inyección de carga solo evita la red en la prueba del despacho; el
  ejecutable continúa usando el cliente configurado en el entorno.
- El guardado mantiene `QSaveFile`, conversión UTF-8 y reemplazo atómico por
  archivo.

## Pendientes y siguiente paso

- Ejecutar la exportación con sesión autenticada únicamente cuando estén
  disponibles las credenciales normales del usuario de pruebas, siguiendo las
  restricciones de seguridad y sin cargar datos sintéticos en `pea-prod`.
