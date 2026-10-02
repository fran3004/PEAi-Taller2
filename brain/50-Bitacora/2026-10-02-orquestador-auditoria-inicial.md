---
tipo: bitacora
estado: borrador
creado: 2026-10-02
actualizado: 2026-10-02
relacionado:
  - "[[Modelo-original]]"
origen: "Auditoría de punto de partida solicitada por el usuario al orquestador"
agente: "orquestador"
rama: "master"
commit: ""
---

# Bitácora · Auditoría de punto de partida

## Objetivo
Auditar el repositorio antes de construir nada, contrastarlo con el contrato de AGENTS.md, clasificar cada pieza y detectar trampas (rama equivocada, pea-test, SQLite, service_role, prompts de proyecto vacío, Modelo HTML en vez de PDF 2024). Sin modificar código.

## Qué se hizo
- Se leyó AGENTS.md, .opencode/protocolos/entrega-entre-agentes.md y se comprobó que brain/50-Bitacora/ estaba VACÍA (no hay "últimas 5 notas": nunca se ha usado).
- Inventario completo del árbol: 77 archivos versionados, 3 commits, 0 sin seguimiento, 42 carpetas.
- Se delegaron en paralelo tres auditorías de solo lectura: seguridad (secretos/ramas/trampas) y documentador (fuentes + bóveda). El subagente explorador no arrancó (error del proveedor) y el inventario se hizo directamente en esta sesión.
- Toda afirmación se verificó con `git grep`, `git check-ignore`, `git ls-files`, `Test-Path` y lectura directa.

## Comandos y resultados
- `git status` → "On branch master... nothing to commit, working tree clean".
- `git branch -a -vv` → `* master [origin/master]`, `remotes/origin/master`. **No existen main ni dev.**
- `git log --oneline -20` → solo 3 commits: `094be91` Add Supabase local config · `49433f7` Renombrar directorio .agents · `a35aa1f` chore: configuración manual completa.
- `git grep -n -i -- "master"` → exit 1, 0 resultados. Ningún texto pide trabajar en master; la contradicción es solo del estado del repo.
- `git grep -n -- "\.agents/"` → 1 resultado: AGENTS.md:51. En disco la carpeta es `.agent/` (sin "s"), renombrada en `49433f7`.
- `git grep -i -- "pea-test"` → 3 resultados, los 3 son menciones que aclaran que NO existe (AGENTS.md:31, rules/03:10, SKILL.md:8). Sin violación.
- `git grep -i -- "sqlite|pea.db"` → 2 resultados, ambos prohibiciones (AGENTS.md:21, rules/03:6). Sin violación.
- `git grep -- "service_role|sb_secret"` → 6 resultados: 5 prohibiciones textuales y 1 comentario del template de Supabase CLI (supabase/config.toml:20). Cero claves reales.
- `git check-ignore -v .env` → `.gitignore:19`. `git check-ignore -v supabase/.temp/pooler-url` → `supabase/.gitignore:3`. Ninguna ruta exigida por el contrato está ignorada (`supabase/migrations/x.sql` NO ignorada).
- Comprobación booleana (sin imprimir) de `supabase/.temp/pooler-url`: longitud 92, no contiene `sb_secret`, ni `sb_publishable`, ni contraseña en URL.
- `Test-Path` de 9 rutas del contrato → brain/00-Inicio.md, brain/10-Requisitos/SPEC.md, brain/40-Fuentes/Modelo.md, .github/workflows/keep-alive.yml, scripts/verificar.ps1, tools/brain/verificar_brain.py, tools/db/respaldar.py y supabase/migrations **no existen**.
- `docs/entrada/Modelo.fuente.json:3` → URL `https://minciencias.gov.co/sistemas-informacion/modelo-medicion-grupos`, `formato_original: ".html"`. `docs/entrada/Modelo.md:27` es solo el enlace al PDF 2024, sin contenido normativo.
- Búsqueda de `*.pdf` en todo el árbol (excluye .venv y node_modules) → NINGUNO.

## Decisiones
- No se modificó ningún archivo de código ni documentación. Solo se creó esta nota.
- No se editó brain/40-Fuentes/Modelo-original.md: el contrato lo declara de solo lectura (AGENTS.md:59) y además es "copia fiel" de la página HTML descargada, así que no tiene error propio; el error está en la fuente elegida.
- No se creó brain/40-Fuentes/Modelo.md: las skills piden secciones "Categorías de producto" y "Estados de validación" que la fuente actual no contiene. Escribirla sería 100 % invención (AGENTS.md:11).
- No se commiteó: la rama actual es `master` y el contrato exige `main ← dev ← feat/`. La decisión de ramas es del usuario y va antes que cualquier commit.
- `relacionado` apunta a [[Modelo-original]] (que sí existe) en vez del `[[00-Inicio]]` de la plantilla, para no añadir otro enlace roto; [[00-Inicio]] sigue sin crearse.

## Pendientes y siguiente paso
1. **Bloqueante, decisión del usuario:** el "Modelo" es el PDF "Modelo de Medición de Grupos ... Año 2024", no la página índice. Descargar el PDF exige una excepción de host (`minciencias.gov.co`, no `scienti.minciencias.gov.co`) que debe quedar en un ADR, o el usuario lo baja a mano.
2. **Bloqueante, decisión del usuario:** estrategia de ramas (`master` → `main` + `dev`).
3. Corregir AGENTS.md:51 (`.agents/` → `.agent/`) y AGENTS.md:7 (aclarar que el Modelo es el PDF 2024).
4. Crear en este orden: ADR-0001 (fuente del Modelo + excepción de host), brain/00-Inicio.md, tools/brain/verificar_brain.py, luego regenerar docs/entrada/Modelo.* y brain/40-Fuentes/Modelo.md, y por último brain/10-Requisitos/SPEC.md (rol requisitos).
5. Poner `.github/workflows/keep-alive.yml` (la clave en `secrets`, nunca literal) o pea-prod se pausa a la semana sin copias.
6. Endurecer `opencode.json:39` (`python*` = allow puentea el deny de lectura de .env) y `.gitignore` (sin reglas para `*.pem`, `*.key`, `signing_keys.json`). Añadir los 4 `.gitkeep` que .gitignore declara.
7. `tools/modelo/extraer_modelo.py`: sin lista blanca de hosts, sin reintentos ni caché, `--nombre` sin sanear y `shutil.rmtree` sin confirmar (línea 205).
