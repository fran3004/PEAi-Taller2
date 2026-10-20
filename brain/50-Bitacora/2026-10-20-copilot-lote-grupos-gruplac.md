---
tipo: bitacora
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[Ingesta]]"
origen: "Soporte de importación por lote para códigos GrupLAC proporcionados localmente"
agente: "Copilot"
rama: "feat/python-cierre-francisco"
commit: ""
---

# Bitácora · Lote de grupos GrupLAC

## Objetivo
Permitir que la CLI procese grupos GrupLAC enumerados en un archivo UTF-8 sin
inventar ni versionar códigos reales.

## Qué se hizo
- Se añadió `importar-url --archivo-grupos`; el archivo admite un código por
  línea, comentarios y líneas vacías, y rechaza códigos inválidos.
- Los códigos repetidos se deduplican y las solicitudes se procesan
  secuencialmente con una sola instancia de `ServicioIngesta`.
- Cada grupo escribe sus resultados en un subdirectorio propio. Se conserva
  la política existente de HTTPS, host permitido, caché, pausas y reintentos.
- Se documentó cómo crear el archivo local sin incluir códigos en el repo.
- Se probaron tres casos offline con fixture; no se contactó el portal real.

## Comandos y resultados
- `.venv\Scripts\python.exe -m pytest -q tests\unit\test_cli_importar_url_lote.py`:
  **3 pasaron**.
- `.venv\Scripts\python.exe -m ruff check src tests tools scripts`:
  **All checks passed!**
- `git diff --check`: aprobado.

## Decisiones
No se crean `datos/fuentes/grupos_upc.txt` ni códigos de grupos. Solo el
usuario puede suministrar los códigos autorizados.

## Pendientes y siguiente paso
- Si se requieren más grupos de la UPC, agregar al archivo local únicamente los
  códigos GrupLAC entregados por el usuario y ejecutar la importación de forma
  responsable.
