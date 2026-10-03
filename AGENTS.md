# PEA-i · Contrato del proyecto

## Misión
Construir el Taller 2 de Estructura de Datos (Universidad Popular del Cesar): PEA-i, Programa Estadístico de Análisis de Investigación (grupos, investigadores y productos, con datos de SCIENTI). Son dos aplicaciones de escritorio con interfaz gráfica, Python (PySide6) y C++ (Qt 6 Widgets), que comparten UNA base de datos PostgreSQL alojada en Supabase y accedida por HTTPS (REST/RPC). El proyecto es modular, escalable y mantenible; no se optimiza para "un solo archivo".

## Fuente de verdad (en este orden)
1. docs/entrada/: el enunciado del taller y el documento "Modelo" (docs/entrada/Modelo-2024.md, extraído del PDF oficial M601PR04G01).
2. brain/10-Requisitos/SPEC.md y documentos de requisitos.
3. brain/20-Diseno/ (Arquitectura, Estructuras, Modelo de dominio, Contrato de datos) y brain/30-Decisiones/ (ADR).
4. El código. Si algo contradice al enunciado o al Modelo, gana la fuente normativa y se avisa al usuario.
No inventes requisitos, campos ni categorías. Lo que no esté en las fuentes se marca como "supuesto" en un ADR o se pregunta.

## Arquitectura
- Capas iguales en los dos lenguajes: GUI → servicios → estructuras propias → repositorios REST/RPC → HTTPS → Supabase → PostgreSQL. La GUI nunca toca estructuras, red ni SQL directamente.
- Las colecciones de entidades se guardan en estructuras HECHAS A MANO: lista doblemente enlazada, multilista, pila, cola e hipercubo. No uses list/dict/vector/map/deque nativos como almacenamiento principal de entidades (sí para variables temporales o índices auxiliares documentados en un ADR).
- Las estadísticas se calculan desde el hipercubo, no con consultas SQL (SQL solo se usa en pruebas para verificar).
- Los servicios aplican el cambio en las estructuras y luego lo persisten; si persistir falla, revierten la estructura y muestran el error.
- Desactivar = activo=false (reversible). Eliminar = sacar de las estructuras y de la base, con reglas en cascada documentadas. Todo cambio se apila en la pila de deshacer.

## Base de datos compartida (Supabase / PostgreSQL)
- La base oficial es PostgreSQL en Supabase. NO existe base local: no SQLite, no datos/pea.db, no sqlite3, no copias locales presentadas como datos actuales.
- Python y C++ acceden EXCLUSIVAMENTE por HTTPS con la API REST/RPC de Supabase. Ninguna aplicación se conecta al puerto de PostgreSQL. Nunca se guardan credenciales de PostgreSQL en el código ni en un ejecutable.
- Las migraciones en supabase/migrations/ son la ÚNICA fuente de verdad del esquema. Una migración aplicada nunca se modifica; todo cambio es una migración nueva.
- Las operaciones que afectan varias tablas y exigen atomicidad se hacen con funciones RPC. Las consultas simples usan REST con parámetros de la API, nunca SQL armado con texto. Al leer, se pagina (PostgREST limita las respuestas a 1000 filas por defecto).
- Seguridad con Auth y Row Level Security (RLS). Los clientes usan SOLO la clave publishable. Jamás la clave secret ni service_role en código, ejecutables, notas ni commits.
- meta.revision sube en cada escritura (triggers por sentencia). Cada programa la consulta periódicamente y antes de escribir; si cambió, muestra "La base de datos cambió" y permite recargar. Las RPC de escritura reciben la revisión esperada.
- Sin conexión: se informa el error y se bloquea la escritura; no se muestra una copia como si fuera actual.
- El plan gratuito pausa el proyecto tras 1 semana sin actividad y no hace copias automáticas: existe un keep-alive programado y tools/db/respaldar.py.

## Proyecto único de Supabase (importante)
Existe UN solo proyecto: pea-prod. NO existe pea-test. Cuando un prompt, una nota o un script mencionen pea-test, PEA_SUPABASE_*_TEST, PEA_ENTORNO=prueba, test_reset() o "solo pea-test", léelo así:
- Es el mismo proyecto, en MODO PRUEBA. Las variables _TEST llevan los mismos valores que _PROD.
- Las pruebas automáticas solo crean, modifican o borran filas con es_ejemplo=true Y con el prefijo PRUEBA- en su código o nombre. Nunca tocan filas reales (es_ejemplo=false) ni los datos de ejemplo oficiales.
- PEA_SUPABASE_SECRET_TEST está vacía y NO se usa ninguna clave secret. reiniciar_prueba.py y test_reset() se implementan como borrado de las filas PRUEBA- con la sesión normal del usuario "pruebas" (PEA_USUARIO_CORREO / PEA_USUARIO_CLAVE).
- meta.entorno vale 'produccion'.
- Antes de proponer un "db push": ejecuta tools/db/respaldar.py y "npx supabase db push --dry-run" y muestra el resultado. El push real lo ejecuta el usuario, o tú solo con su confirmación explícita en ese mismo mensaje.
- borrar_datos_ejemplo() (borra TODOS los datos de ejemplo) solo lo ejecuta el usuario, nunca las pruebas.

## Extracción de fuentes (URLs, PDF, CSV)
- Biblioteca oficial para HTML: requests + beautifulsoup4 (analizador lxml); validación y organización con pydantic; PDF con pdfplumber. Otra herramienta requiere un ADR.
- Reglas de scraping responsable: solo hosts permitidos (scienti.minciencias.gov.co), HTTPS, timeout, máximo 3 reintentos con espera creciente, pausa mínima de 1 s entre peticiones, User-Agent que identifique un proyecto universitario, caché en datos/cache/. Si la fuente falla o cambia: mensaje claro y alternativa (CSV/PDF). Nunca simular que se descargó algo ni inventar campos.
- El documento "Modelo" ya está extraído en docs/entrada/ (Modelo.md y Modelo.original.*). No lo vuelvas a descargar: trabaja con esos archivos. Si falta algo, pide al usuario que ejecute tools/modelo/extraer_modelo.py.
- Los datos de investigadores son personales: repositorio privado, solo lo mínimo en tests/fixtures y nada de datos personales en notas de brain/ más allá de lo necesario para entender la estructura.

## Secretos
- Nunca leer, imprimir ni commitear .env, claves sb_secret_*, service_role, contraseñas de base de datos ni tokens. Las variables se leen del entorno. Si un secreto aparece por error en un archivo o en el historial, avisa de inmediato para rotarlo.

## Trabajo con dos agentes (Antigravity y OpenCode)
- Solo UN agente escribe a la vez sobre la misma rama. Antes de empezar: lee las últimas notas de brain/50-Bitacora/ y ejecuta git status. Al terminar: escribe tu nota de bitácora y haz commit.
- Ramas: main (entrega) ← dev (integración) ← feat/<área>-<persona>. Nunca commits directos a main.
- Las skills viven en .agent/skills/ (una sola copia, la leen los dos agentes). Las reglas y flujos de Antigravity están en .agent/rules/ y .agent/workflows/.

## Cerebro (Obsidian)
- brain/ es la bóveda y la ÚNICA casa de la documentación viva. Toda nota tiene las propiedades: tipo, estado (borrador|revisado|aprobado), creado, actualizado, relacionado (enlaces [[...]] entre comillas) y origen.
- Usa SIEMPRE la plantilla de brain/90-Plantillas/ que corresponda. Fechas en formato AAAA-MM-DD. Archivos en UTF-8 sin BOM y fin de línea LF.
- Nombres de archivo sin tildes ni espacios. Enlaces con [[wikienlaces]]; imágenes en brain/_adjuntos/ con ![[nombre.png]].
- Cada decisión de diseño no trivial = una nota ADR en brain/30-Decisiones/ (contexto, opciones, decisión, consecuencias), numeración consecutiva.
- Cada tarea termina con una nota en brain/50-Bitacora/AAAA-MM-DD-<agente>-<tema>.md. Se valida con tools/brain/verificar_brain.py.
- brain/40-Fuentes/Modelo-original.md es una copia fiel y de SOLO LECTURA del Modelo: no se edita. La versión organizada es brain/40-Fuentes/Modelo.md y cada dato lleva su cita al original ([[Modelo-original#Encabezado]]).

## Idioma y estilo
- Interfaz, mensajes, documentación y comentarios en español correcto; ninguna etiqueta en inglés en pantalla ("Dashboard" → "Panel", "Resumen"...).
- Dominio en español sin tildes (Grupo, Investigador, Producto, ListaDoble). Python 3.12 con anotaciones de tipo, ruff. C++17 sin advertencias (-Wall -Wextra -Wpedantic). La consola y las ventanas deben mostrar tildes y ñ (UTF-8).

## Pruebas y verificación
- Ningún módulo está terminado sin pruebas EJECUTADAS. Nunca afirmes que algo funciona sin correrlo y mostrar el resultado. Las pruebas que usan red van marcadas y no corren por defecto.
- scripts/verificar.ps1 compila C++, corre pruebas de C++ y Python, valida la bóveda y devuelve una tabla OK/FALLA.

## Git
Un commit por tarea con prefijo (feat:, fix:, docs:, test:, chore:). Nunca git push --force, nunca reescribir historial, nunca push a main sin que el usuario lo pida.

## Reporte final obligatorio
Objetivo · Archivos cambiados · Comandos ejecutados y resultados · Pruebas (cuántas, cuántas pasaron) · Supuestos · Riesgos · Siguiente paso.

## Roles (los usas uno a la vez)
Analista de requisitos · Arquitecto · Ingeniero de datos · Ingeniero de fuentes · Ingeniero Python · Ingeniero C++ · Ingeniero de interfaz · QA (revisa sin modificar) · Seguridad · Documentador. Antes de dar algo por terminado, cambia al rol QA.
