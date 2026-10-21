---
tipo: bitacora
estado: revisado
creado: 2026-10-21
actualizado: 2026-10-21
relacionado:
  - "[[00-Inicio]]"
  - "[[Despliegue]]"
  - "[[ADR-0023-Entrega-reproducible-Windows]]"
origen: "Solicitud de preparar la ejecución completa desde el repositorio entregado al profesor"
agente: "Codex"
rama: "feat/python-cierre-francisco"
commit: ""
---

# Bitácora · Entrega reproducible

## Objetivo

Hacer instalables y ejecutables ambas aplicaciones desde GitHub, documentar los
pasos para el profesor y retirar del seguimiento los archivos locales de desarrollo.

## Qué se hizo

- Se revisaron el enunciado PDF, requisitos, arranque, configuración, dependencias,
  pruebas, recursos, empaquetado y estado del repositorio remoto.
- Se prepararon scripts de instalación, conexión autenticada y empaquetado portable.
- Se añadieron CI Windows, restricciones de dependencias y documentación de entrega.
- Se adaptó la verificación cruzada a las CLI portables y se añadió diagnóstico TLS.
- Se preservaron localmente las configuraciones de agentes y editor retiradas de Git.

## Comandos y resultados

- Inventario inicial: rama limpia, remoto público y rama principal master 36 commits
  por detrás de la implementación local. La visibilidad pública es anterior a esta tarea
  y contradice la recomendación de repositorio privado del contrato; no se cambió.
- Exportación del índice con `git checkout-index`: copia sin agentes ni configuración privada.
- `pytest -q` en esa copia: 302 aprobadas, 1 omitida por no disponer aún de C++
  en la copia y 3 de red excluidas.
- `python -m build --wheel --no-isolation` desde la copia: correcto; se verificaron
  cinco fuentes Inter y trece SVG dentro del wheel.
- Ruff de los archivos Python modificados y análisis sintáctico de los scripts
  PowerShell: correctos. Bóveda: 172 notas, 0 errores, 1 advertencia preexistente.
- Instalación de dependencias: correcta tras repetir una descarga incompleta de PyPI;
  `pip check` sin incompatibilidades.
- El ejecutable C++ del directorio habitual estaba abierto por el usuario; se
  conservó ese proceso y se compiló en `build/entrega`.
- C++ Release en `build/entrega`: compilación correcta, CTest 1/1 y doctest
  57 casos aprobados, 674 aserciones. Diagnóstico TLS: OpenSSL disponible.
- PyInstaller generó las dos entradas. La primera prueba portable detectó un
  problema de codificación de consola; se corrigió UTF-8 y se está repitiendo.
- Consulta de proyectos con la sesión existente de Supabase CLI: el proyecto
  vinculado es pea-prod y figura ACTIVE_HEALTHY. No valida permisos ni datos.
- Paquetes y publicación: los resultados definitivos de CI y los assets se consultan
  en GitHub Actions y en la Release asociada al commit de esta tarea.
- Respaldo REST sin abrir .env: faltaban variables. Se añadió alternativa CLI por
  Management API HTTPS: 19 tablas, 3070 filas, revisión 2179 estable, integridad validada.
  Archivo local ignorado `respaldo_cli_20261021_153212_140239.json`, SHA-256
  `1fe00c49efeb0878c9d25edef7707af5b4c0ab5a73ef6badc4b187e314b1d66c`.
- Tras dry-run coincidente, se aplicaron 004 y 005 en pea-prod. La lista remota
  confirma ambas y se verificaron 18 triggers de protección. No se borraron datos.
- Inicialmente se bloqueó Auth por falta de autorización específica. El propietario
  aclaró después que quería acceso completo a datos reales, sin limitar escrituras,
  tras advertir que cualquier descargador tendría esos mismos permisos.
- El usuario proporcionó solo la clave publicable para incluirla en la distribución.
- Portable previo sin red: las seis comprobaciones pasaron, TLS OpenSSL activo,
  comparación cruzada 3/3, autopruebas TUI y GUI (24 combinaciones sin hallazgos),
  y arranque del ejecutable sin consola. Repetir tras incorporar el acceso automático.

### Verificación posterior al acceso completo

- Se aplicó 006 para impedir que cuentas nuevas eludieran el diseño inicial. Tras la
  aclaración del propietario, 007 retiró los límites 005/006 sin borrar datos ni
  desactivar RLS. Se conserva el historial de migraciones aplicadas.
- Segundo respaldo completo previo a 007: 20 tablas, 3073 filas, revisión 2179;
  `respaldo_cli_20261021_160556_164207.json`, SHA-256
  `96afce9c5b6e1f36286274d17af0baa7adf650bad5370438b43dded55341f20f`.
- Dry-run: solo 007 pendiente; aplicación correcta. Verificación remota: cero
  políticas restrictivas de evaluación y 20 tablas con RLS habilitado.
- Auth: se aplicó únicamente `enable_anonymous_sign_ins=true` en pea-prod; once
  propiedades no declaradas permanecieron intactas. Se obtuvo sesión automática.
- Prueba HTTPS: lectura de grupos reales; CRUD completo sobre una fila propia
  PRUEBA- con es_ejemplo=true y limpieza comprobada. No se modificaron filas reales.
  La primera tentativa omitió campos obligatorios; corregida la prueba, aprobó.
- Keep-alive público: ping por HTTPS correcto, sin modificar datos.
- Python final: `pytest -q -m 'not red'`: **311 aprobadas, 3 de red excluidas**.
- C++ final: **59 casos y 681 aserciones aprobados**, CTest 1/1.
- Ruff de archivos modificados: correcto. Bóveda: 174 notas, 0 errores y una
  advertencia preexistente de enlace ADR-0016 en la bitácora del 20 de octubre.
- Se comprobó que la GUI requería pulsar Conectar; se añadió arranque automático
  mediante el servicio existente y una prueba específica. Se regenera el portable.

## Decisiones

- [[ADR-0023-Entrega-reproducible-Windows]]: Windows x64 y ZIP conjunto en Releases.
- No se publican credenciales. Los cambios remotos posteriores están documentados
  arriba y en [[ADR-0025-Acceso-academico-completo]], que sustituye el diseño limitado.
- El enunciado pide un video y entrega por correo; el repositorio por sí solo no
  certifica esos requisitos. El enlace de video no se inventa.

## Pendientes y siguiente paso

- Comprobar CI limpio y la publicación de ZIP/SHA256; el informe final de la tarea
  debe distinguir lo verificado localmente de lo ejecutado por GitHub Actions.
- Supuesto: Windows 10/11 x64 con Internet. No se probó el equipo del profesor.
- Riesgo aceptado: cualquier descargador puede operar sobre los datos compartidos;
  el acceso no se desactiva automáticamente después de la calificación.
- Persisten las diferencias funcionales de la matriz de paridad y el enlace de video
  pendiente. El empaquetado no permite afirmar que esos requisitos estén completados.
