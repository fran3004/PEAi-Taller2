---
trigger: always_on
description: Reglas obligatorias para cualquier trabajo en la interfaz gráfica de Python (src/pea/gui)
---
# Interfaz de Python (PySide6)

- La fuente de verdad visual es `brain/20-Diseno/GUI-Diseno-Python.md`. Léela completa antes de tocar `src/pea/gui/`.
- Las imágenes de referencia están en `brain/_adjuntos/` (`ref-inicio.png`, `ref-inicio-acabado.jpg`, `ref-investigadores.png`, `ref-red-coautorias.png`). Míralas antes de construir cada pantalla y compara tu captura al terminar.
- Si algo de `AUDITORIA-DISENO-PEAI.md`, de bitácoras antiguas o de `GUI-paridad.md` contradice a `GUI-Diseno-Python.md`, gana `GUI-Diseno-Python.md`.
- Estructura y orden como el boceto; **no copies marcas, cifras ni datos inventados**. Lo que PEA-i no tiene (H-Index, ORCID, semilleros, centros, convocatorias, logos de terceros) se reemplaza según la sección 7 de esa nota.
- Colores, tamaños, radios y sombras solo desde los tokens de `src/pea/gui/estilo.py`.
- Solo Qt Widgets + QSS + QPainter + QtSvg. Prohibido QML, QtWebEngine, matplotlib y QtCharts.
- La interfaz solo llama a `ServicioAplicacion`. Red, importación y verificación cruzada, siempre en hilos (`EjecutorAsincrono`).
- Textos en español correcto; cero etiquetas en inglés. Cuerpo de 11 pt o más; contraste de 4,5:1 o más.
- No toques `cpp/`: la interfaz de C++ se rediseña aparte.
- Al terminar: `ruff check`, `pytest tests/unit`, `python -m pea.gui --autoprueba` y una nota en `brain/50-Bitacora/`.
