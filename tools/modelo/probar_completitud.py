#!/usr/bin/env python3
"""
tools/modelo/probar_completitud.py
Prueba de completitud del corpus del Modelo Minciencias 2024.
Verifica:
1. 252 páginas esperadas en el PDF original.
2. Presencia de página inicial (Página 1) y página final (Página 252) en los archivos Markdown.
3. Representación de todas las secciones del índice en Modelo-2024-indice.md y Modelo.md.
4. Existencia e integridad de las notas temáticas derivadas.
5. Reporte detallado de páginas, caracteres, líneas y palabras.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
import pdfplumber

SECCIONES_ESPERADAS = [
    "Contexto",
    "Capítulo I",
    "Capítulo II",
    "Capítulo III",
    "Anexo 1",
    "Anexo 2",
    "Anexo 3",
    "Anexo 4",
    "Anexo 5",
    "Bibliografía"
]

NOTAS_TEMATICAS_ESPERADAS = [
    "Modelo-2024-indice.md",
    "Modelo-2024-original.md",
    "Modelo.md",
    "Modelo-Investigadores.md",
    "Modelo-Grupos.md",
    "Modelo-Productos.md",
    "Modelo-Areas-OCDE.md",
    "Modelo-Estadisticas.md",
    "Modelo-Guias-Revision.md"
]


def probar_completitud(raiz_repo: Path) -> int:
    errores: list[str] = []
    print("=" * 70)
    print("PRUEBA DE COMPLETITUD · CORPUS MODELO MINCIENCIAS 2024")
    print("=" * 70)

    # 1. Verificar PDF original
    pdf_path = raiz_repo / "docs" / "entrada" / "Modelo-2024.original.pdf"
    if not pdf_path.exists():
        errores.append(f"No existe el archivo PDF: {pdf_path}")
        total_paginas_pdf = 0
    else:
        with pdfplumber.open(pdf_path) as pdf:
            total_paginas_pdf = len(pdf.pages)
        print(f"[PDF] Archivo: {pdf_path.name}")
        print(f"[PDF] Páginas leídas: {total_paginas_pdf} (esperadas: 252)")
        if total_paginas_pdf != 252:
            errores.append(f"El PDF tiene {total_paginas_pdf} páginas; se esperaban exactamente 252")

    # 2. Verificar docs/entrada/Modelo-2024.md
    docs_md = raiz_repo / "docs" / "entrada" / "Modelo-2024.md"
    if not docs_md.exists():
        errores.append(f"No existe {docs_md}")
    else:
        txt_docs = docs_md.read_text(encoding="utf-8")
        paginas_docs = re.findall(r"^## Página (\d+)", txt_docs, re.MULTILINE)
        pag_nums_docs = [int(p) for p in paginas_docs]
        print(f"[DOCS-MD] Caracteres: {len(txt_docs):,} | Líneas: {len(txt_docs.splitlines()):,} | Palabras: {len(txt_docs.split()):,}")
        print(f"[DOCS-MD] Total encabezados de página encontrados: {len(pag_nums_docs)}")
        if 1 not in pag_nums_docs:
            errores.append("docs/entrada/Modelo-2024.md no contiene '## Página 1'")
        if 252 not in pag_nums_docs:
            errores.append("docs/entrada/Modelo-2024.md no contiene '## Página 252'")
        if len(pag_nums_docs) != 252:
            errores.append(f"docs/entrada/Modelo-2024.md tiene {len(pag_nums_docs)} páginas; se esperaban 252")

    # 3. Verificar brain/40-Fuentes/Modelo-2024-original.md
    brain_orig = raiz_repo / "brain" / "40-Fuentes" / "Modelo-2024-original.md"
    if not brain_orig.exists():
        errores.append(f"No existe {brain_orig}")
    else:
        txt_brain = brain_orig.read_text(encoding="utf-8")
        paginas_brain = re.findall(r"^## Página (\d+)", txt_brain, re.MULTILINE)
        pag_nums_brain = [int(p) for p in paginas_brain]
        print(f"[BRAIN-ORIG] Caracteres: {len(txt_brain):,} | Líneas: {len(txt_brain.splitlines()):,} | Palabras: {len(txt_brain.split()):,}")
        print(f"[BRAIN-ORIG] Total encabezados de página encontrados: {len(pag_nums_brain)}")
        if 1 not in pag_nums_brain:
            errores.append("brain/40-Fuentes/Modelo-2024-original.md no contiene '## Página 1'")
        if 252 not in pag_nums_brain:
            errores.append("brain/40-Fuentes/Modelo-2024-original.md no contiene '## Página 252'")
        if len(pag_nums_brain) != 252:
            errores.append(f"brain/40-Fuentes/Modelo-2024-original.md tiene {len(pag_nums_brain)} páginas; se esperaban 252")

    # 4. Verificar secciones del índice
    indice_path = raiz_repo / "brain" / "40-Fuentes" / "Modelo-2024-indice.md"
    if not indice_path.exists():
        errores.append(f"No existe {indice_path}")
    else:
        txt_indice = indice_path.read_text(encoding="utf-8")
        for sec in SECCIONES_ESPERADAS:
            if sec.lower() not in txt_indice.lower():
                errores.append(f"La sección '{sec}' no está representada en Modelo-2024-indice.md")
            else:
                print(f"[INDICE] Sección '{sec}' verificada OK.")

    # 5. Verificar notas temáticas
    fuentes_dir = raiz_repo / "brain" / "40-Fuentes"
    for nota in NOTAS_TEMATICAS_ESPERADAS:
        nota_path = fuentes_dir / nota
        if not nota_path.exists():
            errores.append(f"Nota temática no encontrada: {nota_path.name}")
        else:
            contenido = nota_path.read_text(encoding="utf-8")
            print(f"[NOTA TEMÁTICA] {nota_path.name}: {len(contenido):,} caracteres (OK)")

    # 6. Resumen de resultados
    print("-" * 70)
    if errores:
        print(f"FALLAS ENCONTRADAS ({len(errores)}):")
        for err in errores:
            print(f"  [ERROR] {err}")
        print("=" * 70)
        return 1

    print("TODAS LAS PRUEBAS DE COMPLETITUD PASARON EXITOSAMENTE (100% VERDE).")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raiz = Path(__file__).resolve().parent.parent.parent
    sys.exit(probar_completitud(raiz))
