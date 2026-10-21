"""Detecta formatos de credenciales y archivos privados sin imprimir sus valores.

Revisa el indice de Git y, opcionalmente, un paquete. Es una comprobacion de
patrones conocidos, no una certificacion de ausencia de cualquier secreto.
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
from pathlib import Path

PATRONES = (
    re.compile(rb"sb_secret_[A-Za-z0-9_-]{20,}"),
    re.compile(rb"sbp_[a-fA-F0-9]{40,}"),
)
JWT = re.compile(rb"eyJ[A-Za-z0-9_-]+\.([A-Za-z0-9_-]+)\.[A-Za-z0-9_-]+")


def contiene_secreto(datos: bytes) -> bool:
    if any(patron.search(datos) for patron in PATRONES):
        return True
    for coincidencia in JWT.finditer(datos):
        try:
            cuerpo = coincidencia.group(1)
            carga = json.loads(base64.urlsafe_b64decode(cuerpo + b"=" * (-len(cuerpo) % 4)))
            if isinstance(carga, dict) and carga.get("role") == "service_role":
                return True
        except (ValueError, UnicodeDecodeError):
            continue
    return False


def revisar(archivo: Path) -> bool:
    if archivo.name == ".env" or (archivo.name.startswith(".env.") and archivo.name != ".env.example"):
        return True  # No abrir el archivo privado.
    with archivo.open("rb") as entrada:
        anterior = b""
        while bloque := entrada.read(1024 * 1024):
            contenido = anterior + bloque
            if contiene_secreto(contenido):
                return True
            anterior = contenido[-4096:]
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paquete", type=Path)
    opciones = parser.parse_args()
    listado = subprocess.run(
        ["git", "ls-files", "--cached", "-z"], capture_output=True, check=True,
    ).stdout.decode("utf-8").split("\0")
    archivos = [Path(nombre) for nombre in listado if nombre and Path(nombre).is_file()]
    if opciones.paquete:
        archivos.extend(archivo for archivo in opciones.paquete.rglob("*") if archivo.is_file())
    hallazgos = [archivo for archivo in archivos if revisar(archivo)]
    for archivo in hallazgos:
        print(f"REVISAR (valor oculto): {archivo}")
    print(f"Archivos comprobados: {len(archivos)}; hallazgos: {len(hallazgos)}")
    return int(bool(hallazgos))


if __name__ == "__main__":
    raise SystemExit(main())
