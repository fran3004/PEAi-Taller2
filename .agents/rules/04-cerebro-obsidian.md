---
trigger: always_on
description: Cómo se escribe en la bóveda de Obsidian (brain/)
---
# Cerebro de Obsidian
- brain/ es la única casa de la documentación viva.
- Toda nota empieza con las propiedades: tipo, estado (borrador, revisado o aprobado), creado, actualizado, relacionado y origen.
- Crea las notas desde la plantilla de brain/90-Plantillas/ que corresponda.
- Enlaces con [[wikienlaces]]; imágenes en brain/_adjuntos/ con ![[nombre.png]].
- Cada decisión importante es un ADR con número consecutivo en brain/30-Decisiones/.
- Cada tarea termina con una nota en brain/50-Bitacora/AAAA-MM-DD-agente-tema.md.
- Modelo-original.md no se edita nunca. Modelo.md cita el original en cada dato.
- Antes de cada commit se ejecuta python tools/brain/verificar_brain.py.

El contrato completo está en AGENTS.md.
