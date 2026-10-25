# Verificación remota de autorías CSV — 25 de octubre de 2026

La verificación pendiente queda cerrada para los servicios de ingesta Python y C++.
La ejecución completa se realizó de **12:40:47 a 12:41:31, America/Bogota**, contra
`pea-prod` (`wdmchsncexayqbjueamb`), con un usuario normal y clave pública.
No se modificó el código de producción, el esquema ni las políticas de acceso.

## Resultado remoto

| Comprobación | Python | C++ |
| --- | --- | --- |
| Importar una fila CSV con persistencia habilitada | Correcto | Correcto |
| Leer exactamente una autoría remota, activa, `orden_autoria=2`, `es_ejemplo=true` | Correcto | Correcto |
| Importar de nuevo el mismo CSV sin advertencias ni filas erróneas | Correcto | Correcto |
| Conservar la fila completa, incluido ID y timestamps, al repetir | Correcto | Correcto |
| Confirmar el código PostgreSQL de duplicado `23505` | Capturado durante la segunda importación | Confirmado con POST directo y segunda importación idempotente |
| Eliminar autoría, producto e investigador de esta ejecución | Correcto | Correcto |

Se creó un producto y un investigador distintos por lenguaje, con códigos
`PRUEBA-ACSV-…` y `es_ejemplo=true`. El servicio genera la autoría con la misma marca.
El ejecutable C++ usa los repositorios y el servicio de ingesta compilados del proyecto;
no simula las respuestas HTTP. Python consulta de nuevo la relación escrita por C++.

| Tabla | Antes | Después |
| --- | ---: | ---: |
| grupos | 4 | 4 |
| investigadores | 291 | 291 |
| productos | 2352 | 2352 |
| producto_autores | 2356 | 2356 |

Los conteos exactos de **20 tablas públicas** coincidieron, tanto por REST como en
una comprobación SQL independiente por el conector de Supabase. En
`usuarios_autorizados`, REST solo ve 1 fila por RLS y SQL ve 3; ambos conteos se
mantuvieron iguales dentro de su respectivo alcance. Los demás conteos coinciden
entre ambos canales. La consulta SQL final encontró **0 productos y 0 investigadores**
sintéticos residuales con los prefijos usados por estos ensayos y el intento anterior.

Las huellas SHA-256 de todas las filas reales visibles (`es_ejemplo=false`) de
grupos, investigadores, productos y autorías coincidieron antes y después. Los
valores reales se leyeron para calcular las huellas; no se guardaron en la evidencia.

Los triggers incrementaron `meta.revision` de **5690 a 5702** durante la ejecución
completa. Los dos ensayos de preparación anteriores también incrementaron la revisión
al crear y limpiar fixtures. Los IDs secuenciales avanzaron. No se restauraron esos
contadores: hacerlo implicaría alterar el control de concurrencia y las secuencias.
La cantidad de filas de `meta` permaneció en 1.

## Revisión del intento anterior y preparación

Se revisaron `build/verificar_autores.py`, `build/verificar_autores.cpp`, la evidencia
del 23 de octubre y los caminos de ingesta/repositorio actuales de ambos lenguajes.
El intento anterior falló con `23502` al crear un producto incompleto; el último
intento, tras agregar `subtipo`, no dejó un resultado final confirmado.

El comprobador nuevo incluye explícitamente los campos obligatorios de productos e
investigadores. Durante su preparación hubo dos ensayos incompletos: un código de
investigador demasiado largo (`22001`) y campos obligatorios del investigador ausentes
(`23502`). Ambos terminaron con limpieza y conteos/huellas iguales. Se ajustaron los
fixtures al esquema remoto consultado y la tercera ejecución pasó íntegramente.

## Reproducción

Requisitos: entorno Python del proyecto instalado, herramientas MSYS2 UCRT64/Qt6 y
doctest descritas en el README, y acceso HTTPS al proyecto. La configuración se lee
con las mismas funciones de `tools.db.respaldar`: `PEA_SUPABASE_URL`,
`PEA_SUPABASE_PUBLISHABLE_KEY` (o los alias públicos admitidos),
`PEA_USUARIO_CORREO` y `PEA_USUARIO_CLAVE`, desde el entorno o `.env` local.
No usar claves `service_role`/secretas ni escribir credenciales en la línea de comandos.
Se reutiliza un usuario existente; no se crean usuarios anónimos.

Desde la raíz del proyecto, en PowerShell:

```powershell
$env:PATH = 'C:\msys64\ucrt64\bin;' + $env:PATH
& C:\msys64\ucrt64\bin\cmake.exe -S cpp -B build/entrega -G Ninja -DCMAKE_BUILD_TYPE=Release
& C:\msys64\ucrt64\bin\cmake.exe --build build/entrega --target verificar_autores_remoto -j 4
.\.venv\Scripts\python.exe -m tools.db.verificar_autores_remoto --cpp build/entrega/verificar_autores_remoto.exe --salida build/evidencia-autores-remoto.json
```

Cada comando debe terminar con código 0 antes de continuar. El último solo devuelve
0 si se comprobaron ambos lenguajes, la limpieza, los conteos y las huellas. Su JSON
final debe indicar `completa=true`, `conteos_iguales=true`, `reales_sin_cambios=true`
y `errores=[]`. No se ejecuta automáticamente desde pytest ni CTest.

La limpieza está en `finally`, usa códigos exactos y `es_ejemplo=true`, y elimina
primero el par exacto producto/investigador. Busca por código incluso si se perdió la
respuesta de creación. Un error de limpieza se registra por separado y hace fallar
la comprobación. Una terminación forzada del proceso o falta de red podría impedir
limpiar: el archivo de evidencia conserva el prefijo para diagnosticarlo. Nunca usar
el reinicio general de datos de prueba para limpiar esta comprobación.

## Evidencia conservada

- [Ejecución completa](evidencias/autorias-csv-20261025-completa.json): fixtures sintéticos, resultados, conteos, huellas y revisiones.
- [Conteos SQL independientes](evidencias/autorias-csv-20261025-sql.json): las 20 tablas sin el filtro de visibilidad del usuario REST.
- [Ensayo con código largo](evidencias/autorias-csv-20261025-longitud.json) y [ensayo con campos ausentes](evidencias/autorias-csv-20261025-obligatorios.json): fallos reportados y limpieza comprobada.

Validación local: **25 pruebas Python aprobadas** (13 de autorías y 12 del comprobador),
Ruff sin hallazgos en los archivos nuevos, compilación C++ correcta y CTest aprobado.
La comprobación de espacios del cambio CMake pasó; el chequeo global detectó líneas
en blanco finales en tres archivos que ya estaban modificados antes de este trabajo.
Esos cambios ajenos se conservaron.

## Alcance y límites

No queda pendiente ninguna de las comprobaciones solicitadas de guardado, duplicado,
limpieza y conteos. Se verificaron directamente los servicios CSV; no se ejecutaron
las pantallas GUI/TUI ni el paquete portable. Las huellas cubren cuatro tablas reales;
en las otras tablas se compararon conteos. No se probó concurrencia externa ni se
certificó seguridad de producción.

La consulta preventiva de asesores detectó avisos existentes de funciones
`SECURITY DEFINER` ejecutables y políticas compatibles con usuarios anónimos, además
de protección de contraseñas filtradas desactivada. No se cambiaron permisos durante
esta verificación. Referencias: [asesores de base de datos](https://supabase.com/docs/guides/database/database-advisors)
y [protección de contraseñas](https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection).
