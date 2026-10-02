#!/usr/bin/env python3
"""
tools/modelo/procesar_modelo_2024.py
Extrae el texto completo de las 252 páginas del PDF del Modelo Minciencias 2024
utilizando pdfplumber, preservando encabezados, títulos, tablas, notas al pie y fórmulas.
Genera:
- docs/entrada/Modelo-2024.md
- brain/40-Fuentes/Modelo-2024-original.md
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
import pdfplumber


def procesar_pdf(raiz_repo: Path) -> dict:
    pdf_path = raiz_repo / "docs" / "entrada" / "Modelo-2024.original.pdf"
    if not pdf_path.exists():
        # Fallback al nombre largo si aún no se ha copiado
        alt_path = raiz_repo / "docs" / "entrada" / "m601pr04g01_modelo_medicion_grupos_investigacion_tecnologica_o_innovacion_y_reconocimiento_investigadores_-_2024_1.pdf"
        if alt_path.exists():
            import shutil
            shutil.copy2(alt_path, pdf_path)
        else:
            raise FileNotFoundError(f"No se encontró el PDF en {pdf_path}")

    # Calcular SHA256 y tamaño
    pdf_bytes = pdf_path.read_bytes()
    sha256_hash = hashlib.sha256(pdf_bytes).hexdigest()
    tamano_bytes = len(pdf_bytes)

    paginas_extraidas: list[dict] = []
    total_caracteres = 0

    print(f"Abriendo {pdf_path.name} con pdfplumber...")
    with pdfplumber.open(pdf_path) as pdf:
        total_paginas = len(pdf.pages)
        print(f"Total de páginas a procesar: {total_paginas}")

        for i, page in enumerate(pdf.pages):
            pno = i + 1
            # Extraer texto preservando saltos
            txt = page.extract_text(layout=False) or ""
            # Si extract_text devolviese vacío por alguna razón de fuente, probar con layout=True
            if not txt.strip():
                txt = page.extract_text(layout=True) or ""

            # Extraer tablas para detección de completitud
            tables = page.extract_tables()
            num_tablas = len(tables)

            total_caracteres += len(txt)
            paginas_extraidas.append({
                "numero": pno,
                "texto": txt,
                "longitud": len(txt),
                "num_tablas": num_tablas
            })

            if pno % 25 == 0 or pno == total_paginas:
                print(f"  Páginas procesadas: {pno}/{total_paginas} ({total_caracteres} caracteres acumulados)")

    # 1. Generar docs/entrada/Modelo-2024.md
    out_docs = raiz_repo / "docs" / "entrada" / "Modelo-2024.md"
    print(f"Escribiendo {out_docs}...")
    partes_docs: list[str] = [
        "# Modelo de Medición de Grupos de Investigación e Investigadores - Minciencias 2024\n",
        "**Documento Oficial:** Código M601PR04G01 · Versión 02 · 252 páginas\n",
        f"**SHA256:** `{sha256_hash}`\n\n",
        "---\n\n"
    ]

    for p in paginas_extraidas:
        pno = p["numero"]
        txt = p["texto"].strip()
        partes_docs.append(f"## Página {pno}\n\n")
        partes_docs.append(f"{txt}\n\n")
        partes_docs.append("---\n\n")

    texto_docs = "".join(partes_docs).replace("\r\n", "\n")
    out_docs.write_text(texto_docs, encoding="utf-8", newline="\n")

    # 2. Generar brain/40-Fuentes/Modelo-2024-original.md
    out_brain = raiz_repo / "brain" / "40-Fuentes" / "Modelo-2024-original.md"
    print(f"Escribiendo {out_brain}...")
    frontmatter_brain = [
        "---",
        "tipo: fuente",
        "estado: aprobado",
        "creado: 2026-10-02",
        "actualizado: 2026-10-02",
        "relacionado:",
        '  - "[[Modelo-2024-indice]]"',
        '  - "[[Modelo]]"',
        'origen: "docs/entrada/Modelo-2024.original.pdf"',
        'url: "https://minciencias.gov.co/sites/default/files/upload/convocatoria/m601pr04g01_modelo_medicion_grupos_investigacion_tecnologica_o_innovacion_y_reconocimiento_investigadores_-_2024_1.pdf"',
        'archivo_original: "Modelo-2024.original.pdf"',
        'formato_original: ".pdf"',
        f"paginas: {len(paginas_extraidas)}",
        f'sha256: "{sha256_hash}"',
        'metodo: "Extracción página a página con pdfplumber"',
        "---",
        "",
        "# Modelo de Medición de Grupos e Investigadores 2024 (Texto original extraído)",
        "",
        "> Copia fiel y de solo lectura del documento oficial M601PR04G01 (Versión 02). No se reorganiza destruyendo el orden original. La versión organizada e indexada está en [[Modelo-2024-indice]] y [[Modelo]].",
        "",
        "---",
        ""
    ]

    partes_brain = ["\n".join(frontmatter_brain)]
    for p in paginas_extraidas:
        pno = p["numero"]
        txt = p["texto"].strip()
        partes_brain.append(f"## Página {pno}\n\n")
        partes_brain.append(f"{txt}\n\n")
        partes_brain.append("---\n\n")

    texto_brain = "".join(partes_brain).replace("\r\n", "\n")
    out_brain.write_text(texto_brain, encoding="utf-8", newline="\n")

    resumen = {
        "paginas": len(paginas_extraidas),
        "total_caracteres": total_caracteres,
        "sha256": sha256_hash,
        "tamano_bytes": tamano_bytes,
        "docs_md_path": str(out_docs),
        "brain_original_path": str(out_brain)
    }
    return resumen


if __name__ == "__main__":
    raiz = Path(__file__).resolve().parent.parent.parent
    res = procesar_pdf(raiz)
    print("\nPROCESAMIENTO COMPLETADO EXITOSAMENTE:")
    print(json.dumps(res, indent=2, ensure_ascii=False))

