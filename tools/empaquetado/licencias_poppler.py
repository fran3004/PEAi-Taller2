"""Incluye fuentes, licencia y receta exactas del lector PDF redistribuido."""

import argparse
import hashlib
import tarfile
from pathlib import Path
from urllib.request import urlopen

VERSION = "26.08.0"
REVISION = "c8df53f1adfa89b3e21554de788db5e0d14689a1"
FUENTE_SHA256 = "dc906e68cea698109706ac6aa3d2c9d4512fcfcac42d90b8afcda486d1b9abd0"
PARCHE_SHA256 = "315356263b5ebee5431a2e079ac76492a8919a04a798f6c6d53c64f44b433db6"


def descargar(url: str, destino: Path, sha256: str | None = None):
    with urlopen(url, timeout=60) as respuesta:
        contenido = respuesta.read()
    if sha256 and hashlib.sha256(contenido).hexdigest() != sha256:
        raise ValueError("La fuente de Poppler no coincide con su suma de comprobación.")
    destino.write_bytes(contenido)


def incluir(destino: Path, version_instalada: str):
    if version_instalada != VERSION + "-1":
        raise ValueError(
            "Actualice la referencia de fuentes de Poppler para la versión instalada antes de redistribuirla."
        )
    destino.mkdir(parents=True, exist_ok=True)
    archivo = destino / f"poppler-{VERSION}.tar.xz"
    descargar(f"https://poppler.freedesktop.org/poppler-{VERSION}.tar.xz", archivo, FUENTE_SHA256)
    base = f"https://raw.githubusercontent.com/msys2/MINGW-packages/{REVISION}/mingw-w64-poppler"
    descargar(base + "/PKGBUILD", destino / "PKGBUILD")
    descargar(
        base + "/0001-nopython-generate-enums.patch", destino / "0001-nopython-generate-enums.patch", PARCHE_SHA256
    )
    with tarfile.open(archivo, "r:xz") as fuentes:
        licencia = fuentes.extractfile(f"poppler-{VERSION}/COPYING")
        if licencia is None:
            raise ValueError("No se encontró la licencia de Poppler en el archivo fuente.")
        (destino / "COPYING").write_bytes(licencia.read())
    (destino / "LEEME.txt").write_text(
        f"Poppler {VERSION}-1 (MSYS2 UCRT64), GPL-2.0-or-later.\n"
        "pdftotext es un programa externo; PEA-i lo ejecuta mediante QProcess.\n"
        "Se adjuntan el código fuente original, el parche y la receta PKGBUILD exacta.\n"
        f"Receta de MSYS2: {REVISION}\nSHA-256 de las fuentes: {FUENTE_SHA256}\n"
        "Construcción: extraer el tar.xz, aplicar el parche y seguir prepare()/build()\n"
        "del PKGBUILD con el entorno y las dependencias MSYS2 allí declarados.\n"
        "Los demás avisos de dependencias están en las carpetas de licencias del paquete.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destino", type=Path)
    parser.add_argument("version_instalada")
    opciones = parser.parse_args()
    incluir(opciones.destino, opciones.version_instalada)
    print("Poppler: fuentes, parche, receta y licencia incluidos y comprobados.")
