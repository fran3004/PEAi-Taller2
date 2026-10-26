"""Calcula los indicadores del Parcial 2 con las dos URL del enunciado en Python y C++.

Descarga el GrupLAC y el CvLAC oficiales (solo lectura, sin escribir en Supabase), ejecuta
ambas CLI con y sin estimación de categorías y guarda un resumen comparable en
``docs/evidencias``. Requiere Internet y la compilación de ``cpp/build/pea-cpp.exe``.

Uso::

    .venv\\Scripts\\python.exe tools/interop/evidencia_urls.py [--salida RUTA.json]
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
URL_GRUPO = "https://scienti.minciencias.gov.co/gruplac/jsp/visualiza/visualizagr.jsp?nro=00000000002099"
URL_INVESTIGADOR = "https://scienti.minciencias.gov.co/cvlac/visualizador/generarCurriculoCv.do?cod_rh=0000494917"
CASOS = [("grupo", URL_GRUPO), ("investigador", URL_INVESTIGADOR)]


def ejecutar(lenguaje: str, ambito: str, url: str, estimar: bool, destino: Path) -> dict:
    if lenguaje == "python":
        base = [sys.executable, "-m", "pea.cli"]
    else:
        base = [str(RAIZ / "cpp" / "build" / "pea-cpp.exe")]
    orden = [*base, "indicador", "--ambito", ambito, "--url", url, "--corte", "2023", "--salida", str(destino)]
    if estimar:
        orden.append("--estimar-categorias")
    entorno = {**os.environ, "PYTHONIOENCODING": "utf-8", "PATH": r"C:\msys64\ucrt64\bin;" + os.environ["PATH"]}
    subprocess.run(orden, check=True, capture_output=True, cwd=RAIZ, env=entorno, timeout=600)
    r = json.loads(destino.read_text(encoding="utf-8"))
    return {
        "indicador": round(r["indicador"], 6),
        "completo": r["completo"],
        "incluidos": len(r["incluidos"]),
        "excluidos": len(r["excluidos"]),
        "estimadas": len(r.get("estimadas", [])),
        "brutos": {k: round(v, 6) for k, v in r["brutos"].items()},
        "componentes": {c["componente"]: round(c["aporte"], 6) for c in r["componentes"]},
        "nombre": r["nombre"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--salida", type=Path, default=RAIZ / "docs" / "evidencias" / "parcial-urls-20261025.json")
    args = parser.parse_args()
    resultado: dict = {
        "fecha": datetime.date.today().isoformat(),
        "corte": 2023,
        "urls": {"grupo": URL_GRUPO, "investigador": URL_INVESTIGADOR},
        "nota": "Descarga real de SCIENTI sin escritura remota. SCIENTI no publica cuartil ni nivel de calidad: "
        "el modo estricto excluye esos productos; el modo estimado usa la categoría base de cada tipología.",
        "resultados": {},
    }
    with tempfile.TemporaryDirectory() as tmp:
        for ambito, url in CASOS:
            for estimar in (False, True):
                clave = f"{ambito}_{'estimado' if estimar else 'estricto'}"
                resultado["resultados"][clave] = {
                    lenguaje: ejecutar(lenguaje, ambito, url, estimar, Path(tmp) / f"{clave}-{lenguaje}.json")
                    for lenguaje in ("python", "cpp")
                }
    for por_lenguaje in resultado["resultados"].values():
        py, cpp = por_lenguaje["python"], por_lenguaje["cpp"]
        por_lenguaje["equivalentes"] = abs(py["indicador"] - cpp["indicador"]) < 1e-5 and all(
            abs(py["brutos"][k] - cpp["brutos"][k]) < 1e-4 for k in py["brutos"]
        )
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v["equivalentes"] for k, v in resultado["resultados"].items()}))
    return 0 if all(v["equivalentes"] for v in resultado["resultados"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
