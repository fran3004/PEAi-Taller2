"""Completa las DLL transitivas de UCRT64 que windeployqt no copia."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
from pathlib import Path


def copiar_dependencias(carpeta: Path, bin_msys: Path) -> int:
    """Lee las importaciones PE y solo copia DLL del toolchain, nunca de Windows."""
    sistema = Path(os.environ["SystemRoot"]) / "System32"
    pendientes = list(carpeta.rglob("*.exe")) + list(carpeta.rglob("*.dll"))
    revisados: set[Path] = set()
    copiados = 0
    while pendientes:
        archivo = pendientes.pop()
        if archivo in revisados:
            continue
        revisados.add(archivo)
        salida = subprocess.run(
            [str(bin_msys / "objdump.exe"), "-p", str(archivo)],
            capture_output=True, text=True, check=True,
        ).stdout
        for nombre in re.findall(r"DLL Name:\s*(\S+)", salida):
            if nombre.lower().startswith(("api-ms-", "ext-ms-")):
                continue
            origen = bin_msys / nombre
            destino = carpeta / nombre
            if destino.is_file():
                pendientes.append(destino)
            elif origen.is_file():
                shutil.copy2(origen, destino)
                copiados += 1
                pendientes.append(destino)
            elif not (sistema / nombre).is_file():
                raise RuntimeError(f"Dependencia no resuelta: {nombre} requerida por {archivo.name}")
    return copiados


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("carpeta", type=Path)
    parser.add_argument("bin_msys", type=Path)
    argumentos = parser.parse_args()
    print(f"DLL transitivas copiadas: {copiar_dependencias(argumentos.carpeta, argumentos.bin_msys)}")
