# Entrega 0.1.7 — 25 de octubre de 2026

Esta entrega reúne las correcciones posteriores a `v0.1.6-entrega.20261022` y
actualiza Python y C++ a la versión 0.1.7.

## Cambios incluidos

- Persistencia de autorías CSV antes de actualizar memoria o contabilizar éxitos,
  duplicados idempotentes y errores de guardado visibles en ambos lenguajes.
- Verificación remota reproducible con fixtures `PRUEBA-` y `es_ejemplo=true`,
  limpieza y conteos exactos iguales antes/después. Véase el
  [informe y las evidencias](verificacion-autorias-csv.md).
- Lectura estricta de la revisión remota, validación de años y redirecciones HTTP
  acotadas a los destinos admitidos.
- Identificadores estables de productos CvLAC y descarte de etiquetas interpretadas
  erróneamente como artículos; herramienta de conciliación incluida en el código
  fuente. Empaquetar o arrancar el programa no ejecuta esa conciliación.
- ZIP portable con las dos aplicaciones, bibliotecas, conexión pública existente,
  licencias, documentación académica y evidencia remota. `VERSION-ENTREGA.json`
  identifica su versión y commit.

## Archivos de la Release

- `PEAi-Windows-x64.zip`: descomprimir completamente y ejecutar
  `Iniciar-Python.cmd` o `Iniciar-Cpp.cmd`.
- `PEAi-Codigo-fuente.zip`: código versionado completo del mismo commit.
- `pea-0.1.7-py3-none-any.whl`: distribución Python para desarrolladores.
- `dependencias-python.txt` y `dependencias-msys2.txt`: versiones del entorno de
  construcción de GitHub Actions.
- `SHA256SUMS.txt`: sumas de los archivos anteriores.

La Release se publica después de la compilación y las pruebas en un Windows limpio
de GitHub Actions y de comprobar los ejecutables descargados. El registro del
workflow y las notas de la Release contienen el resultado final de publicación.

## Alcance

Se conserva el acceso académico compartido documentado en el README. El paquete
incluye solo configuración pública; `.env`, contraseñas, tokens, agentes,
preferencias del editor, cachés y respaldos privados quedan fuera de la distribución.
No se aplican migraciones ni se modifican datos reales durante la reempaquetación.

Esta entrega no implementa la ingesta PDF de C++ ni reemplaza el video académico
pendiente. La matriz de paridad conserva esos límites.
