---
tipo: bitacora
estado: revisado
creado: 2026-10-20
actualizado: 2026-10-20
relacionado:
  - "[[GUI-Diseno-Python]]"
origen: "Corrección del solapamiento entre el avatar y el nombre en las fichas laterales"
agente: "Copilot"
rama: "feat/python-cierre-francisco"
commit: ""
---

# Bitácora · Separación entre avatar y nombre de ficha

## Objetivo
Evitar que el nombre de las fichas laterales se superponga con el avatar cuando
el texto se ajusta a varias líneas en ventanas de distintos anchos.

## Qué se hizo
- Se calcula la altura requerida del nombre según el ancho disponible mediante
  `QLabel.heightForWidth()` y se actualiza al cambiar el texto o redimensionar
  el cuerpo de la ficha.
- Se amplió la prueba de no superposición a 1100, 1366 y 1920 px.
- Se documentó la regla responsive en [[GUI-Diseno-Python]].
- Se regeneraron y revisaron las capturas de Investigadores en las tres
  resoluciones; el nombre queda debajo del avatar en todos los casos.

## Comandos y resultados
- `.venv\Scripts\python.exe -m pytest -q tests\unit\test_tabla_ficha_dialogos.py -k avatar_no_se_superpone`:
  **3 pasaron**.
- `.venv\Scripts\python.exe -m pytest -q`: **284 pasaron, 3 excluidas**.
- `.venv\Scripts\python.exe -m ruff check src tests tools scripts`:
  **All checks passed!**
- `.venv\Scripts\python.exe -m vulture src tools\vulture_whitelist.py --min-confidence 80`:
  **sin hallazgos**.
- `.venv\Scripts\python.exe -m pea.gui --autoprueba`: **0 hallazgos en 24
  combinaciones de pantalla y resolución**.
- `.venv\Scripts\python.exe tools\brain\verificar_brain.py`: **0 errores y
  1 advertencia histórica** por un enlace ADR-0016 no resuelto en otra
  bitácora.
- `git diff --check`: aprobado.

## Decisiones
La altura se deriva de la medición de texto de Qt en el ancho efectivo, en vez
de usar una altura fija o modificar el tamaño del avatar. Así se conserva la
tipografía y el diseño existente.

## Pendientes y siguiente paso
- Confirmar los conteos reales de Supabase cuando el entorno disponga de la
  sesión normal y la clave publicable configuradas.
- Revisar la visibilidad privada del repositorio en GitHub.
