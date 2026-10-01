---
name: obsidian-brain
description: Usar al crear, editar o validar notas de la bóveda brain/ de Obsidian (propiedades, plantillas, enlaces, ADR, bitácora, tableros Bases, notas de fuentes y la nota organizada del Modelo).
---
# Cerebro de Obsidian (brain/)

## Propiedades obligatorias (arriba de cada nota, entre ---)
- `tipo`: adr, bitacora, requisito, historia-de-usuario, caso-de-uso, fuente, nota-de-diseno, resultado-de-pruebas, informe-de-extraccion o indice.
- `estado`: borrador, revisado o aprobado.
- `creado` y `actualizado`: fecha AAAA-MM-DD. Al editar, actualiza `actualizado`.
- `relacionado`: lista de enlaces entre comillas, por ejemplo `- "[[Arquitectura]]"`.
- `origen`: de dónde sale (una ruta, una URL o el nombre del agente).
- Propias: ADR (`numero`, `decision`), bitácora (`agente`, `rama`, `commit`), fuente (`url`, `fecha_descarga`, `sha256`), resultado de pruebas (`comando`, `resultado`).

## Formato
- UTF-8 sin BOM y LF. Valores con dos puntos entre comillas. Sangría de 2 espacios.
- Nombres de archivo sin tildes ni espacios. Notas siempre desde la plantilla de `90-Plantillas/`.
- Enlaces `[[Nota]]`, a una sección `[[Nota#Encabezado]]`. Imágenes en `_adjuntos/` con `![[imagen.png]]`.
- Diagramas con bloques mermaid. Una idea por nota.

## Carpetas
- 00-Paneles (tableros .base), 10-Requisitos, 20-Diseno, 30-Decisiones (ADR), 40-Fuentes, 50-Bitacora, 60-Pruebas, 70-Manuales, 90-Plantillas, _adjuntos.
- No se crean notas fuera de las carpetas numeradas (salvo 00-Inicio.md).

## ADR y bitácora
- ADR: `ADR-0001-titulo.md`, numeración consecutiva sin huecos; contexto, opciones, decisión, consecuencias.
- Bitácora: `AAAA-MM-DD-<agente>-<tema>.md` al terminar cada tarea.

## El Modelo en la bóveda
- `40-Fuentes/Modelo-original.md`: copia fiel y de SOLO LECTURA. No se edita.
- `40-Fuentes/Modelo.md`: versión organizada, con secciones: Resumen fiel, Categorías de producto, Estados de validación, y una tabla por entidad (Grupo, Investigador, Producto, Integrante, Plan) con las columnas: campo, tipo, obligatorio, descripción, entrada o salida, cita.
- La columna "cita" enlaza al original: `[[Modelo-original#Encabezado exacto]]`. Lo que no tiene cita es un "supuesto" y va en su propia sección.
- Si el original supera 400 líneas, se parte en notas Modelo-Grupo, Modelo-Investigador, Modelo-Producto y Modelo-Catalogos, enlazadas desde Modelo.md.

## Validación
- `python tools/brain/verificar_brain.py` antes de cada commit: propiedades, enlaces, huérfanas y numeración de ADR.
- No edites una nota que el usuario tenga abierta. No toques `brain/.obsidian/`.

## Lista de comprobación
- [ ] Las seis propiedades en cada nota.
- [ ] Cero enlaces rotos y cero notas huérfanas.
- [ ] ADR consecutivos.
- [ ] Cada dato del Modelo organizado tiene su cita.
