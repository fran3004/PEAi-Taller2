---
name: seguridad
description: Usar al revisar permisos de la base (RLS), manejo de claves y tokens, fuga de secretos en código, ejecutables o historial de git, inyección, rutas de archivo, scraping y archivos corruptos o malintencionados.
---
# Lista de seguridad de PEA-i

## Claves y credenciales
- En los programas solo va la clave publishable y la URL (config/pea.config.json junto al ejecutable). La clave secret, service_role y la contraseña de PostgreSQL no aparecen en ningún lugar del proyecto.
- Correo y contraseña del usuario se escriben en la ventana de inicio de sesión; los tokens viven solo en memoria.
- `.env` está en `.gitignore` y nunca se lee ni se imprime.
- Buscar secretos: `python tools/interop/buscar_secretos.py` (código, notas, historial de git y paquetes). Si aparece uno: avisar sin imprimirlo completo, rotarlo en Supabase (Settings → API Keys) y regenerar los paquetes. No reescribir historial ni `push --force`.

## Base de datos
- RLS activo en todas las tablas; `anon` sin lectura ni escritura (salvo `ping()`).
- Funciones `security invoker` con `search_path` fijo. Escritura con revisión esperada.
- Filtros solo por parámetros de la API: nunca SQL armado con texto.
- Riesgos conocidos y documentados: la publishable puede extraerse del ejecutable (la protege RLS) y la cuenta del profesor es compartida.

## Entradas externas
- URLs: HTTPS y host permitido. Nombres de archivo y rutas validados; sin salir de la carpeta esperada.
- CSV, PDF y HTML: tamaño máximo, codificación comprobada, filas inválidas reportadas sin detener la carga. Nunca ejecutar contenido de un archivo.
- Datos personales de investigadores: repositorio privado y solo lo mínimo en fixtures y notas.

## Lista de comprobación
- [ ] Búsqueda de secretos sin hallazgos (código, historial y paquetes).
- [ ] Sin sesión, la API devuelve acceso denegado.
- [ ] Ningún log imprime tokens ni claves.
- [ ] Los ejecutables no contienen credenciales administrativas.
