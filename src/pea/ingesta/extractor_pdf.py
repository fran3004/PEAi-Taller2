"""Extractor de documentos PDF mediante pdfplumber para PEA-i.

Cumple con las directrices normativas:
- Extracción fidedigna página por página.
- Extracción de tablas tabulares con análisis de celdas.
- Detección rigurosa y advertencia de páginas o documentos escaneados (sin capa de texto).
- Regla normativa: Jamás inventar datos ni asumir valores ausentes.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pdfplumber

from pea.ingesta.modelos import DocumentoPDF, PaginaPDF


class ResultadoPDF:
    """Contenedor de los resultados de procesamiento de un archivo PDF."""

    def __init__(self, documento: DocumentoPDF) -> None:
        self.documento = documento

    @property
    def total_paginas(self) -> int:
        return self.documento.total_paginas

    @property
    def total_caracteres(self) -> int:
        return self.documento.total_caracteres

    @property
    def es_escaneado(self) -> bool:
        return self.documento.es_escaneado

    @property
    def advertencias(self) -> list[str]:
        return self.documento.advertencias


class ExtractorPDF:
    """Extractor especializado en archivos PDF oficiales de Minciencias y convocatorias."""

    def __init__(self, umbral_caracteres_escaneo: int = 20) -> None:
        self.umbral_caracteres_escaneo = umbral_caracteres_escaneo

    def procesar_archivo(self, ruta_pdf: Path | str, max_paginas: int | None = None) -> DocumentoPDF:
        """Abre el archivo PDF con pdfplumber y extrae texto y tablas página a página.

        Detecta documentos escaneados si carecen de capa de texto vectorial y emite advertencias.
        No inventa ni completa datos faltantes.
        """
        path = Path(ruta_pdf)
        if not path.exists():
            raise FileNotFoundError(f"El archivo PDF no existe en la ruta: {path}")

        raw_bytes = path.read_bytes()
        sha256_hash = hashlib.sha256(raw_bytes).hexdigest()

        paginas_resultado: list[PaginaPDF] = []
        total_caracteres = 0
        total_tablas = 0
        paginas_con_sospecha_escaneo = 0
        advertencias: list[str] = []

        with pdfplumber.open(path) as pdf:
            total_paginas_pdf = len(pdf.pages)
            limite = min(total_paginas_pdf, max_paginas) if max_paginas else total_paginas_pdf

            for idx in range(limite):
                num_pag = idx + 1
                page = pdf.pages[idx]

                # 1. Extraer texto preservando estructura
                texto = page.extract_text(layout=False) or ""
                if not texto.strip():
                    texto = page.extract_text(layout=True) or ""

                # 2. Extraer tablas
                tablas_extraidas = page.extract_tables() or []
                num_tablas_pag = len(tablas_extraidas)

                # 3. Detectar imágenes y posible rasterizado / escaneado
                num_imagenes = len(page.images) if hasattr(page, "images") else 0
                caracteres_pag = len(texto.strip())

                es_sospechosa = False
                if caracteres_pag < self.umbral_caracteres_escaneo:
                    if num_imagenes > 0 or num_tablas_pag == 0:
                        es_sospechosa = True
                        paginas_con_sospecha_escaneo += 1
                        advertencias.append(
                            f"Página {num_pag}: Parece ser una imagen escaneada o rasterizada "
                            f"(solo {caracteres_pag} caracteres detectados, {num_imagenes} imágenes encontradas)."
                        )

                total_caracteres += caracteres_pag
                total_tablas += num_tablas_pag

                paginas_resultado.append(
                    PaginaPDF(
                        numero=num_pag,
                        longitud_texto=caracteres_pag,
                        tablas_encontradas=num_tablas_pag,
                        tiene_imagenes=(num_imagenes > 0),
                        es_escaneada_sospechosa=es_sospechosa,
                        texto=texto,
                        tablas=tablas_extraidas,
                    )
                )

        es_documento_escaneado = False
        if limite > 0 and (paginas_con_sospecha_escaneo / limite) >= 0.5:
            es_documento_escaneado = True
            advertencias.insert(
                0,
                f"ADVERTENCIA GLOBAL: El documento '{path.name}' tiene más del 50% de páginas "
                f"sin capa de texto ({paginas_con_sospecha_escaneo}/{limite}). Se considera documento escaneado.",
            )

        return DocumentoPDF(
            ruta_archivo=str(path.resolve()),
            sha256=sha256_hash,
            total_paginas=limite,
            total_caracteres=total_caracteres,
            total_tablas=total_tablas,
            es_escaneado=es_documento_escaneado,
            advertencias=advertencias,
            paginas=paginas_resultado,
        )

    def exportar_a_markdown(self, documento: DocumentoPDF, destino_md: Path | str) -> Path:
        """Genera una transcripción estructurada en Markdown del contenido extraído."""
        dest = Path(destino_md)
        dest.parent.mkdir(parents=True, exist_ok=True)

        lineas: list[str] = [
            f"# Transcripción de Documento PDF · {Path(documento.ruta_archivo).name}\n",
            f"- **Ruta:** `{documento.ruta_archivo}`",
            f"- **SHA256:** `{documento.sha256}`",
            f"- **Total de páginas procesadas:** {documento.total_paginas}",
            f"- **Total de caracteres:** {documento.total_caracteres}",
            f"- **Total de tablas detectadas:** {documento.total_tablas}",
            f"- **Clasificado como escaneado:** {'Sí (Alerta: Requiere OCR previo)' if documento.es_escaneado else 'No (Texto vectorial)'}\n",
        ]

        if documento.advertencias:
            lineas.append("## Advertencias y Avisos de Integridad\n")
            for adv in documento.advertencias:
                lineas.append(f"> ⚠️ **Aviso:** {adv}")
            lineas.append("\n---\n")

        for pag in documento.paginas:
            lineas.append(f"## Página {pag.numero}\n")
            if pag.es_escaneada_sospechosa:
                lineas.append("> *Aviso: Página identificada como posible imagen rasterizada sin texto seleccionable.*\n")

            if pag.texto.strip():
                lineas.append(f"{pag.texto.strip()}\n")
            else:
                lineas.append("*Sin texto seleccionable en esta página.*\n")

            if pag.tablas:
                lineas.append(f"### Tablas extraídas en Página {pag.numero} ({len(pag.tablas)})\n")
                for tidx, tbl in enumerate(pag.tablas, start=1):
                    lineas.append(f"**Tabla {tidx}:**\n")
                    if tbl and len(tbl) > 0:
                        # Encabezados
                        headers = [str(c or "").replace("\n", " ").strip() for c in tbl[0]]
                        lineas.append("| " + " | ".join(headers) + " |")
                        lineas.append("| " + " | ".join(["---"] * len(headers)) + " |")
                        for row in tbl[1:]:
                            cols = [str(c or "").replace("\n", " ").strip() for c in row]
                            lineas.append("| " + " | ".join(cols) + " |")
                    lineas.append("")

            lineas.append("---\n")

        texto_md = "\n".join(lineas).replace("\r\n", "\n")
        dest.write_text(texto_md, encoding="utf-8")
        return dest
