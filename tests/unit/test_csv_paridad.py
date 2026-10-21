from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any


def _casos_csv_compartidos() -> list[dict[str, Any]]:
    archivo = Path(__file__).parents[2] / "cpp" / "tests" / "fixtures" / "csv_paridad.json"
    return json.loads(archivo.read_text(encoding="utf-8"))["casos"]


def test_fixtures_csv_compartidos_conservan_utf8_escapes_y_crlf() -> None:
    for caso in _casos_csv_compartidos():
        salida = io.StringIO(newline="")
        escritor = csv.writer(salida, lineterminator="\r\n")
        escritor.writerow(caso["entrada"])

        assert salida.getvalue() == caso["salida"], caso["nombre"]
        assert salida.getvalue().encode("utf-8").endswith(b"\r\n")
