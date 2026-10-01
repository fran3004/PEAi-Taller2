---
name: fuentes-scienti
description: Usar al descargar, analizar o normalizar páginas de GrupLAC y CvLAC (SCIENTI), importar CSV o PDF, mantener los fixtures y el oráculo esperado.json, o al trabajar con el documento Modelo extraído en docs/entrada.
---
# Fuentes: SCIENTI, CSV, PDF y el Modelo

## Herramientas
- `requests` para descargar, `beautifulsoup4` con el analizador `lxml` para el HTML, `pydantic` v2 para validar y organizar, `pdfplumber` para PDF. Playwright o Selenium solo si se demuestra con evidencia que una página necesita JavaScript.

## Descarga responsable
- Solo HTTPS y solo el host `scienti.minciencias.gov.co`. Timeout de conexión y de lectura.
- Máximo 3 reintentos con espera creciente. Pausa mínima de 1 segundo entre peticiones.
- User-Agent que diga que es un proyecto universitario de la UPC.
- Caché en `datos/cache/<sha256 de la URL>.html` y su `.meta.json` (url, fecha, código HTTP, codificación, sha256).
- No supongas UTF-8: comprueba cabeceras, etiqueta meta y `apparent_encoding`. Nunca finjas una descarga.

## Del HTML al dato
- Un analizador por sección, tolerante a secciones ausentes, sin inventar datos. Cada función documenta el selector que usa.
- Modelos pydantic con solo campos que existan en el Modelo o en las páginas; todo opcional salvo el identificador; campo `origen` (url, fecha, sha256).
- Normalizar: texto en NFC y sin espacios sobrantes, años como entero, fechas ISO-8601, categorías y validaciones mapeadas al catálogo del Modelo. Lo que no encaje se reporta, no se adivina.
- Exportar: JSON por fuente en `datos/fuentes/`, CSV canónico en `datos/fuentes/csv/` e informe de calidad (campos vacíos, filas descartadas, conteos por sección).

## Pruebas y oráculo
- Fixtures en `tests/fixtures/scienti/` con su `*.esperado.json`. Las pruebas corren sin internet; la de descarga real lleva la marca `red`.
- El analizador de C++ debe producir lo mismo que el esperado.json.
- Casos a cubrir: URL inválida, host no permitido, sin red, HTML incompleto, sección ausente, tildes y ñ, categoría desconocida, respuesta vacía, tiempo agotado.

## El documento Modelo
- Ya está extraído: `docs/entrada/Modelo.md` (texto), `Modelo.original.*` (archivo original), `Modelo.fuente.json` (origen). No se vuelve a descargar.
- Si una imagen del Modelo contiene un diagrama, transcríbelo a una tabla bajo el título "Transcripción de la imagen" y marca la nota como `estado: borrador`.

## Lista de comprobación
- [ ] Datos personales anonimizados en las notas y mínimos en los fixtures.
- [ ] Todo campo extraído tiene su origen; los ausentes quedan vacíos.
- [ ] El CSV canónico coincide con brain/40-Fuentes/Formato-CSV-canonico.md.
