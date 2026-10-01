#!/usr/bin/env python3
"""Descarga el documento "Modelo" (una URL) y lo convierte a Markdown para el cerebro de Obsidian.

Uso (desde la raíz del proyecto, con el entorno .venv activado):
  python tools/modelo/extraer_modelo.py --url "https://..."
  python tools/modelo/extraer_modelo.py --url "https://..." --archivo "C:/Descargas/Modelo.docx"
  python tools/modelo/extraer_modelo.py --url "https://..." --nombre Modelo-2

Qué deja:
  docs/entrada/<Nombre>.original.<ext>   archivo original tal cual se descargó
  docs/entrada/<Nombre>.md               texto extraído (sin propiedades)
  docs/entrada/<Nombre>.fuente.json      de dónde salió (url, fecha, sha256, método)
  docs/entrada/modelo-media/             imágenes extraídas (intermedio, no va a Git)
  brain/40-Fuentes/<Nombre>-original.md  copia con propiedades para Obsidian (solo lectura)
  brain/_adjuntos/<nombre>-*.png         imágenes del documento
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parents[2]
ENTRADA = RAIZ / "docs" / "entrada"
CEREBRO = RAIZ / "brain"
UA = "Mozilla/5.0 (proyecto universitario UPC - Taller 2 PEA-i)"
EXT_POR_TIPO = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.oasis.opendocument.text": ".odt",
    "text/html": ".html",
}
FORMATO_PANDOC = {".docx": "docx", ".odt": "odt", ".html": "html"}


def salir(mensaje: str) -> None:
    print(f"\nERROR: {mensaje}", file=sys.stderr)
    raise SystemExit(1)


def descargar(url: str) -> tuple[bytes, str]:
    """Descarga la URL. Para Google Docs y Google Drive usa el enlace de exportación."""
    destino = url
    es_drive = False
    m = re.search(r"docs\.google\.com/document/d/([\w-]+)", url)
    if m:
        destino = f"https://docs.google.com/document/d/{m.group(1)}/export?format=docx"
    else:
        m = re.search(r"drive\.google\.com/(?:file/d/|open\?id=|uc\?[^\s]*?id=)([\w-]+)", url)
        if m:
            destino = f"https://drive.google.com/uc?export=download&id={m.group(1)}"
            es_drive = True
    try:
        r = requests.get(destino, headers={"User-Agent": UA}, timeout=(10, 60), allow_redirects=True)
        r.raise_for_status()
    except requests.RequestException as error:
        salir(f"No se pudo descargar: {error}\nSi el enlace es privado, descárgalo desde el navegador y usa --archivo.")
    tipo = r.headers.get("Content-Type", "").split(";")[0].strip().lower()
    pide_sesion = "accounts.google.com" in r.url or b"ServiceLogin" in r.content[:30000]
    if pide_sesion or (es_drive and tipo == "text/html"):
        salir("El enlace pide iniciar sesión o confirmación (documento privado o muy grande).\n"
              "Descárgalo desde el navegador y vuelve a ejecutar con --archivo.")
    return r.content, tipo


def convertir_con_pandoc(entrada: str, formato: str) -> None:
    if shutil.which("pandoc") is None:
        salir("Falta Pandoc. Instálalo con: winget install --id JohnMacFarlane.Pandoc -e  (y abre PowerShell de nuevo)")
    # La plantilla evita que se pierda el título del documento (pandoc lo trata como metadato).
    (ENTRADA / "__plantilla.md").write_text("$if(title)$# $title$\n\n$endif$$body$\n", encoding="utf-8")
    orden = ["pandoc", entrada, "-f", formato, "-t", "gfm", "--wrap=none", "--standalone",
             "--template=__plantilla.md", "--extract-media=modelo-media", "-o", "__salida.md"]
    r = subprocess.run(orden, cwd=ENTRADA, capture_output=True, text=True, encoding="utf-8")
    (ENTRADA / "__plantilla.md").unlink(missing_ok=True)
    if r.returncode != 0:
        salir(f"Pandoc falló: {r.stderr.strip()}")


def html_limpio(contenido: bytes, destino: Path) -> None:
    from bs4 import BeautifulSoup

    sopa = BeautifulSoup(contenido, "lxml")
    for etiqueta in sopa(["script", "style", "nav", "footer", "header", "noscript", "form"]):
        etiqueta.decompose()
    destino.write_text(str(sopa), encoding="utf-8")


def pdf_a_markdown(archivo: Path) -> str:
    import pdfplumber

    partes: list[str] = []
    with pdfplumber.open(archivo) as pdf:
        for n, pagina in enumerate(pdf.pages, 1):
            texto = (pagina.extract_text() or "").strip()
            partes.append(f"## Página {n}\n\n" + (texto or "_(sin texto reconocible: posible imagen escaneada)_"))
            for i, tabla in enumerate(pagina.extract_tables(), 1):
                filas = [[(c or "").replace("\n", " ").strip() for c in fila] for fila in tabla if fila]
                if len(filas) < 2:
                    continue
                ancho = max(len(f) for f in filas)
                filas = [f + [""] * (ancho - len(f)) for f in filas]
                md = ["| " + " | ".join(filas[0]) + " |", "|" + "---|" * ancho]
                md += ["| " + " | ".join(f) + " |" for f in filas[1:]]
                partes.append(f"### Tabla {i} detectada en la página {n}\n\n" + "\n".join(md))
    return "\n\n".join(partes)


def limpiar(texto: str) -> str:
    texto = unicodedata.normalize("NFC", texto.replace("\r\n", "\n").replace("\r", "\n"))
    texto = re.sub(r"!\[[^\]]*\]\(data:image[^)]*\)", "_(imagen incrustada omitida)_", texto)
    texto = "\n".join(linea.rstrip() for linea in texto.split("\n"))
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip() + "\n"


def reenlazar_imagenes(texto: str, nombre: str) -> tuple[str, int]:
    """Copia las imágenes a brain/_adjuntos/ y las enlaza al estilo Obsidian: ![[nombre-imagen.png]]."""
    destino = CEREBRO / "_adjuntos"
    destino.mkdir(parents=True, exist_ok=True)
    prefijo = nombre.lower()
    copiadas: set[str] = set()

    def copiar(ruta: str) -> str | None:
        ruta = ruta.replace("\\", "/")
        origen = ENTRADA / ruta
        if not origen.is_file():
            return None
        nuevo = f"{prefijo}-{origen.name}"
        shutil.copy2(origen, destino / nuevo)
        copiadas.add(nuevo)
        return nuevo

    def md(m: re.Match[str]) -> str:
        nuevo = copiar(m.group(1))
        return f"![[{nuevo}]]" if nuevo else m.group(0)

    def html(m: re.Match[str]) -> str:
        nuevo = copiar(m.group(1))
        return f"![[{nuevo}]]" if nuevo else m.group(0)

    texto = re.sub(r"!\[[^\]]*\]\((modelo-media/[^)\s]+)\)(?:\{[^}]*\})?", md, texto)
    texto = re.sub(r"<img\s[^>]*?src=\"(modelo-media/[^\"]+)\"[^>]*>", html, texto)
    return texto, len(copiadas)


def informe(texto: str, imagenes: int) -> list[str]:
    encabezados = len(re.findall(r"^#{1,6} ", texto, flags=re.M))
    tablas = len(re.findall(r"^\|[\s:|-]+\|$", texto, flags=re.M))
    html_tablas = len(re.findall(r"<table", texto, flags=re.I))
    raros = len(re.findall(r"Ã.|â€|ï¿½|\ufffd", texto))
    print("\n--- Informe de extracción ---")
    print(f"Caracteres: {len(texto)}   Líneas: {texto.count(chr(10))}")
    print(f"Encabezados: {encabezados}   Tablas de Markdown: {tablas}   Imágenes copiadas: {imagenes}")
    avisos: list[str] = []
    if len(texto) < 500:
        avisos.append("Texto casi vacío: el documento puede ser una imagen o estar protegido. Revisa el original.")
    if raros:
        avisos.append(f"Hay {raros} caracteres raros (¿tildes dañadas?). Abre el original y compara.")
    if html_tablas:
        avisos.append(f"Hay {html_tablas} tabla(s) en HTML (celdas combinadas): reescríbelas como tabla simple.")
    if encabezados == 0:
        avisos.append("No hay encabezados: el documento no tiene estructura. Habrá que organizarlo a mano.")
    if "sin texto reconocible" in texto:
        avisos.append("Hay páginas de PDF sin texto (escaneadas): se necesita leerlas como imagen.")
    for aviso in avisos:
        print(f"AVISO: {aviso}")
    if not avisos:
        print("Sin avisos.")
    return avisos


def main() -> int:
    p = argparse.ArgumentParser(description='Extrae el documento "Modelo" a Markdown.')
    p.add_argument("--url", required=True, help="enlace del Modelo tal como aparece en el enunciado")
    p.add_argument("--archivo", help="archivo ya descargado a mano (docx, pdf, html, odt)")
    p.add_argument("--nombre", default="Modelo", help="nombre base de los archivos (por defecto: Modelo)")
    a = p.parse_args()
    nombre = a.nombre

    ENTRADA.mkdir(parents=True, exist_ok=True)
    if a.archivo:
        origen = Path(a.archivo)
        if not origen.is_file():
            salir(f"No existe el archivo: {origen}")
        contenido, ext, metodo = origen.read_bytes(), origen.suffix.lower(), "archivo descargado a mano"
    else:
        contenido, tipo = descargar(a.url)
        ext = EXT_POR_TIPO.get(tipo, "")
        metodo = f"descarga automática ({tipo})"
    if ext not in (".pdf", ".docx", ".odt", ".html"):
        salir(f"Tipo de documento no soportado ({ext or 'desconocido'}). Usa docx, pdf, odt o html.")

    original = ENTRADA / f"{nombre}.original{ext}"
    original.write_bytes(contenido)
    sha = hashlib.sha256(contenido).hexdigest()
    shutil.rmtree(ENTRADA / "modelo-media", ignore_errors=True)

    if ext == ".pdf":
        texto = pdf_a_markdown(original)
    else:
        entrada = original.name
        if ext == ".html":
            html_limpio(contenido, ENTRADA / f"{nombre}.limpio.html")
            entrada = f"{nombre}.limpio.html"
        convertir_con_pandoc(entrada, FORMATO_PANDOC[ext])
        salida = ENTRADA / "__salida.md"
        texto = salida.read_text(encoding="utf-8")
        salida.unlink()

    texto = limpiar(texto)
    texto_cerebro, imagenes = reenlazar_imagenes(texto, nombre)
    (ENTRADA / f"{nombre}.md").write_text(texto, encoding="utf-8", newline="\n")

    ahora = datetime.now().astimezone()
    hoy = ahora.date().isoformat()
    meta = {"nombre": nombre, "url": a.url, "fecha_descarga": ahora.isoformat(timespec="seconds"),
            "sha256": sha, "metodo": metodo, "formato_original": ext, "archivo_original": original.name}
    (ENTRADA / f"{nombre}.fuente.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    url_segura = a.url.replace('"', "%22")
    cabecera = (
        "---\n"
        "tipo: fuente\n"
        "estado: borrador\n"
        f"creado: {hoy}\n"
        f"actualizado: {hoy}\n"
        "relacionado:\n"
        '  - "[[Modelo]]"\n'
        f'origen: "{url_segura}"\n'
        f'url: "{url_segura}"\n'
        f"fecha_descarga: {hoy}\n"
        f"sha256: {sha}\n"
        f'metodo: "{metodo}"\n'
        "---\n\n"
        f"# {nombre} (texto original extraído)\n\n"
        "> Copia fiel y de solo lectura del documento. No se edita. "
        "La versión organizada está en [[Modelo]].\n\n"
    )
    destino = CEREBRO / "40-Fuentes" / f"{nombre}-original.md"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(cabecera + texto_cerebro, encoding="utf-8", newline="\n")

    print(f"Original guardado:   {original.relative_to(RAIZ)}")
    print(f"Texto extraído:      docs/entrada/{nombre}.md")
    print(f"Nota para Obsidian:  {destino.relative_to(RAIZ)}")
    print(f"Fuente registrada:   docs/entrada/{nombre}.fuente.json")
    avisos = informe(texto, imagenes)
    return 1 if any("casi vacío" in x or "caracteres raros" in x for x in avisos) else 0


if __name__ == "__main__":
    raise SystemExit(main())
