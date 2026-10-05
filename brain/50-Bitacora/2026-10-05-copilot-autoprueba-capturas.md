---
tipo: bitacora
estado: revisado
creado: 2026-10-05
actualizado: 2026-10-05
relacionado:
  - "[[GUI-Diseno-Python]]"
  - "[[2026-10-04-copilot-responsividad-importar-configuracion-acerca]]"
origen: "Solicitud de validacion automatica, organizacion de capturas y auditoria de textos visibles"
agente: "Copilot"
rama: "master"
---

# Autoprueba, capturas y textos visibles

## Que cambie

- `ejecutar_autoprueba` inspecciona cada pantalla en 1100x700, 1366x768 y 1920x1080.
- Las barras horizontales visibles se registran como errores y producen codigo de salida 3.
- Los widgets cuya geometria sale de la ventana se registran como advertencias sin bloquear la ejecucion.
- Se imprime una tabla resumen con pantalla, tamano, barras, widgets fuera y ruta de captura.
- Las 24 capturas oficiales nuevas se guardan en `datos/capturas/oficiales/`.
- Las referencias `ref-*` ya estaban en `brain/_adjuntos/`; no habia referencias con ese patron en `datos/capturas/`.

## Auditoria de textos

Se revisaron textos de botones, titulos, tooltips, placeholders, dialogos y etiquetas de graficos. No se encontraron frases visibles en ingles que requirieran traduccion. Se conservaron siglas tecnicas como CSV, PDF, PNG, URL y nombres propios como Supabase porque no son textos traducibles.

## Verificacion

- `ruff check src tests`: fallo inicial por orden de importacion; corregido reordenando `QAbstractScrollArea`.
- `python -m pea.gui --autoprueba` con `QT_QPA_PLATFORM=offscreen`, `PEA_SIN_ANIMACIONES=1` y `PYTHONPATH=src`: codigo 0; 24 capturas generadas y 0 barras horizontales visibles.
- La autoprueba reporto advertencias de widgets contenidos en areas desplazables que salen del rectangulo de la ventana; no se consideran fallas.
- La prueba unitaria solicitada con `tests/unit/test_ventana_principal.py` no pudo ejecutarse porque ese archivo no existe en el repositorio.

## Archivos

- `src/pea/gui/ventana_principal.py`
- `brain/20-Diseno/GUI-Diseno-Python.md`
- `brain/50-Bitacora/2026-10-05-copilot-autoprueba-capturas.md`
