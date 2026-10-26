# PEA-i 0.2.1 · Parcial 2 completo

Esta entrega completa la 0.2.0 para el enunciado del Parcial 2:

- **Especificación Word IEEE 830** (`entrega/Especificacion_Tecnica_PEAi.docx`) basada en la plantilla
  del enunciado: 23 requisitos funcionales, requisitos no funcionales, diccionario de datos, diseño de las
  estructuras, estrategia del indicador, diagramas UML de casos de uso, secuencia, clases, despliegue y
  entidad-relación, capturas de ambas aplicaciones y trazabilidad con el parcial. Se regenera con
  `py -3 tools/diagramas_documento.py`, `tools/capturas_documento.py` y `tools/generar_especificacion.py`.
- **Estimación declarada de categorías** (`--estimar-categorias`, casilla en la GUI, campo en la TUI): con las
  URL del enunciado SCIENTI no publica el cuartil, de modo que el modo estricto da 0; el modo estimado puntúa
  con la categoría base de cada tipología y lo declara (ver [parcial-2.md](parcial-2.md)).
- **`respuestas-parcial`**: calcula el indicador del grupo y del investigador del enunciado con las URL oficiales;
  disponible también como `--respuestas` en `Parcial2_FF_SM.py` y `Parcial2_FF_SM.cpp`.
- Correcciones: los catálogos descargados de SCIENTI ya pueden guardarse y reabrirse (fechas «2013/1», «Actual»);
  la cohesión no falla con vínculos vigentes; C++ usa la misma etiqueta «Trabajo dirigido» que Python.
- Verificación cruzada Python/C++ ampliada a los casos con estimación; evidencia con las URL reales en
  `docs/evidencias/parcial-urls-20261025.json`.

El video de sustentación no forma parte del repositorio.
