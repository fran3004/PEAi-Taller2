"""Prueba el paquete sin rutas de Python, Qt o MSYS2 en PATH y sin credenciales."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def probar(carpeta: Path) -> None:
    entorno = {
        clave: valor for clave, valor in os.environ.items()
        if not clave.startswith(("PEA_", "PYTHON", "QT_"))
    }
    sistema = Path(os.environ["SystemRoot"])
    entorno["PATH"] = str(sistema / "System32") + os.pathsep + str(sistema)
    entorno["PYTHONIOENCODING"] = "utf-8"
    entorno["PEA_SIN_ANIMACIONES"] = "1"
    entorno["PEA_OMITIR_CONFIG_PUBLICA"] = "1"
    comandos = [
        [str(carpeta / "PEAi-Python/pea-cli.exe"), "--version"],
        [str(carpeta / "PEAi-Cpp/pea-cpp.exe"), "--version"],
        [str(carpeta / "PEAi-Cpp/pea-cpp.exe"), "diagnostico-tls"],
        [str(carpeta / "PEAi-Python/pea-cli.exe"), "--verificar-cruzada"],
        [str(carpeta / "PEAi-Cpp/pea-cpp.exe"), "--autoprueba"],
        [str(carpeta / "PEAi-Python/pea-cli.exe"), "--autoprueba-gui"],
    ]
    with tempfile.TemporaryDirectory(prefix="pea-portable-") as temporal:
        for comando in comandos:
            salida = subprocess.run(
                comando, cwd=temporal, env=entorno, capture_output=True,
                timeout=180, encoding="utf-8", errors="replace", check=False,
            )
            print(f"{Path(comando[0]).name} {comando[1]}: codigo {salida.returncode}")
            print(salida.stdout)
            if salida.returncode:
                raise RuntimeError(salida.stderr or "El ejecutable no pudo iniciarse; revise las DLL.")
        resultados = []
        for ejecutable in [carpeta / "PEAi-Python/pea-cli.exe", carpeta / "PEAi-Cpp/pea-cpp.exe"]:
            salida = subprocess.run(
                [str(ejecutable), "indicador", "--archivo", str(carpeta / "datos/ejemplo-parcial.json"),
                 "--ambito", "grupo", "--codigo", "PRUEBA-G1", "--corte", "2023", "--json"],
                cwd=temporal, env=entorno, capture_output=True, encoding="utf-8", timeout=60,
            )
            if salida.returncode:
                raise RuntimeError(salida.stderr or salida.stdout)
            resultados.append(json.loads(salida.stdout))
        if any(abs(r["indicador"] - 4.5) > 1e-10 for r in resultados):
            raise RuntimeError("El indicador del ejemplo portable no coincide con el valor esperado.")
        if resultados[0]["componentes"] != resultados[1]["componentes"]:
            # Tolerancia solo para redondeo de funciones logarítmicas entre runtimes.
            for a, b in zip(resultados[0]["componentes"], resultados[1]["componentes"], strict=True):
                for k in ["bruto", "maximo", "indice", "aporte"]:
                    if abs(a[k] - b[k]) > 1e-8:
                        raise RuntimeError("Discrepancia de componentes en el portable.")
        salida = subprocess.run(
            [str(carpeta / "PEAi-Cpp/pea-cpp.exe"), "importar-pdf", "--archivo", str(carpeta / "pruebas/texto.pdf"),
             "--salida", str(Path(temporal) / "pdf.json")],
            cwd=temporal, env=entorno, capture_output=True, encoding="utf-8", timeout=65,
        )
        if salida.returncode:
            raise RuntimeError(salida.stderr or "El lector PDF no funciona sin toolchain.")
        documento = json.loads((Path(temporal) / "pdf.json").read_text(encoding="utf-8"))
        if documento["total_paginas"] != 1 or "PEA-i Parcial 2" not in documento["paginas"][0]["texto"]:
            raise RuntimeError("La extracción PDF portable no conserva el texto esperado.")
        print("Indicadores Python/C++ y PDF portable: aprobados sin toolchain.")
        # Arranque real del ejecutable sin consola; solo se cierra la instancia de esta prueba.
        entorno["QT_QPA_PLATFORM"] = "offscreen"
        proceso = subprocess.Popen(
            [str(carpeta / "PEAi-Python/pea-gui.exe")], cwd=temporal, env=entorno,
        )
        try:
            try:
                codigo = proceso.wait(timeout=8)
            except subprocess.TimeoutExpired:
                print("pea-gui.exe: permanece abierto tras el arranque")
            else:
                raise RuntimeError(f"La GUI se cerro durante el arranque: {codigo}")
        finally:
            if proceso.poll() is None:
                proceso.terminate()
                proceso.wait(timeout=15)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("carpeta", type=Path)
    probar(parser.parse_args().carpeta.resolve())
