"""Conserva los avisos de las dependencias de ejecución en la distribución."""

from __future__ import annotations

import argparse
import shutil
from importlib.metadata import distribution
from pathlib import Path

from packaging.requirements import Requirement


def recopilar(destino: Path) -> None:
    pendientes = ["pea"]
    vistos: set[str] = set()
    informe = []
    while pendientes:
        nombre = pendientes.pop()
        normalizado = nombre.lower().replace("_", "-")
        if normalizado in vistos:
            continue
        vistos.add(normalizado)
        paquete = distribution(nombre)
        informe.append(f"{paquete.metadata['Name']}=={paquete.version}")
        for archivo in paquete.files or []:
            if any(x in str(archivo).lower() for x in ("license", "licence", "copying", "notice", "ofl.txt")):
                origen = Path(paquete.locate_file(archivo))
                if origen.is_file():
                    # No reutilizar rutas absolutas ni .. procedentes de metadatos.
                    partes = [p for p in archivo.parts if p not in ("..", ".") and not Path(p).anchor]
                    salida = destino / normalizado / Path(*partes)
                    salida.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(origen, salida)
        for texto in paquete.requires or []:
            requisito = Requirement(texto)
            if requisito.marker is None or requisito.marker.evaluate({"extra": ""}):
                pendientes.append(requisito.name)
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "VERSIONES.txt").write_text("\n".join(sorted(informe)) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destino", type=Path)
    recopilar(parser.parse_args().destino)
