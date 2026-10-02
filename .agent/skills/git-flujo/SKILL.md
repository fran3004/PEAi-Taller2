---
name: git-flujo
description: Usar al crear ramas, hacer commits, preparar un pull request, resolver choques entre Antigravity y OpenCode o decidir cuándo hacer push.
---
# Git en PEA-i

## Ramas
- `main` es la entrega. `dev` es la integración. Cada persona o agente trabaja en `feat/<área>-<persona>`.
- Nunca commits directos a `main`. Se une a `dev` con un pull request.
- Antes de subir: `git pull --rebase origin dev`.

## Commits
- Uno por tarea, con prefijo: `feat:`, `fix:`, `docs:`, `test:` o `chore:`, y un mensaje claro en español.
- Revisa antes con `git status` y `git diff`. No incluyas `.env`, datos de `datos/` ni paquetes.

## Dos agentes
- Solo UN agente escribe a la vez en una rama. Antes de empezar: `git status` y las últimas bitácoras. Al terminar: bitácora y commit.
- Si Antigravity y OpenCode chocan: `git status` y `git log --oneline -10` en cada rama, explica qué hizo cada uno y propón cómo unir sin perder trabajo. Espera la confirmación del usuario.

## Cosas que NUNCA se hacen
- `git push --force` o `-f`.
- Reescribir el historial publicado.
- `git reset --hard` sin confirmación del usuario.
- `git push` sin que el usuario lo pida.

## Lista de comprobación
- [ ] La rama de trabajo es correcta (`git branch --show-current`).
- [ ] El commit tiene prefijo y solo lo de la tarea.
- [ ] `git check-ignore -v .env` sigue confirmando que `.env` se ignora.
