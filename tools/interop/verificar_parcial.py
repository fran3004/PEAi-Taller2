"""Paridad real de las dos CLI del Parcial 2, usando exclusivamente archivos locales."""

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

RAIZ = Path(__file__).resolve().parents[2]


def comparar(a, b, ruta="resultado"):
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            raise AssertionError(f"{ruta}: claves distintas: {set(a) ^ set(b)}")
        for k in a:
            comparar(a[k], b[k], f"{ruta}.{k}")
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            raise AssertionError(f"{ruta}: longitudes distintas")
        for i, (x, y) in enumerate(zip(a, b, strict=True)):
            comparar(x, y, f"{ruta}[{i}]")
    elif (
        isinstance(a, (int, float))
        and not isinstance(a, bool)
        and isinstance(b, (int, float))
        and not isinstance(b, bool)
    ):
        if not math.isclose(a, b, rel_tol=1e-11, abs_tol=1e-11):
            raise AssertionError(f"{ruta}: números diferentes: {a}, {b}")
    elif a != b:
        raise AssertionError(f"{ruta}: valores diferentes: {a!r}, {b!r}")


def comprobar(cpp: Path):
    ejemplo = RAIZ / "datos/ejemplo-parcial.json"
    casos = 0
    with TemporaryDirectory(prefix="pea-parcial-") as carpeta:
        temporal = Path(carpeta)
        for ambito, codigo in [("grupo", "PRUEBA-G1"), ("investigador", "PRUEBA-I1")]:
            for corte, desde in [(2023, None), (2023, 2023), (2026, 2022)]:
                args = [
                    "indicador",
                    "--archivo",
                    str(ejemplo),
                    "--ambito",
                    ambito,
                    "--codigo",
                    codigo,
                    "--corte",
                    str(corte),
                    "--json",
                ]
                if desde:
                    args += ["--desde", str(desde)]
                resultados = []
                for nombre, comando in [("python", [sys.executable, "-m", "pea.cli"]), ("cpp", [str(cpp)])]:
                    salida = subprocess.run(
                        comando + args + ["--guardar-catalogo", str(temporal / f"{nombre}.json")],
                        cwd=RAIZ,
                        capture_output=True,
                        encoding="utf-8",
                        timeout=60,
                    )
                    if salida.returncode:
                        raise RuntimeError(f"{nombre}: {salida.stderr or salida.stdout}")
                    resultados.append(json.loads(salida.stdout))
                comparar(*resultados)
                # Cada aplicación debe poder leer la instantánea escrita por la otra.
                for nombre, comando in [("cpp", [sys.executable, "-m", "pea.cli"]), ("python", [str(cpp)])]:
                    cruzada = args.copy()
                    cruzada[cruzada.index("--archivo") + 1] = str(temporal / f"{nombre}.json")
                    salida = subprocess.run(
                        comando + cruzada, cwd=RAIZ, capture_output=True, encoding="utf-8", timeout=60
                    )
                    if salida.returncode:
                        raise RuntimeError(salida.stderr or salida.stdout)
                    comparar(resultados[0], json.loads(salida.stdout))
                casos += 1
        pdf = RAIZ / "tests/fixtures/parcial/texto.pdf"
        salida_pdf = subprocess.run(
            [str(cpp), "importar-pdf", "--archivo", str(pdf), "--salida", str(temporal / "pdf.json")],
            capture_output=True,
            encoding="utf-8",
            timeout=65,
        )
        if salida_pdf.returncode:
            raise RuntimeError(salida_pdf.stderr)
        doc = json.loads((temporal / "pdf.json").read_text(encoding="utf-8"))
        if doc["total_paginas"] != 1 or "PEA-i Parcial 2" not in doc["paginas"][0]["texto"]:
            raise AssertionError("La extracción PDF C++ no conserva la página de prueba.")
    print(f"Parcial 2: {casos} casos con JSON equivalente, 12 lecturas cruzadas y PDF C++ aprobados; sin red.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpp", type=Path, default=RAIZ / "cpp/build/pea-cpp.exe")
    comprobar(parser.parse_args().cpp.resolve())
