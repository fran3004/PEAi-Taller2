from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any

from pea.ingesta.lector_csv import LectorCSV


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


def test_importacion_grupos_compartida_acepta_registro_multilinea_utf8(
    tmp_path: Path,
) -> None:
    archivo_fixture = (
        Path(__file__).parents[2] / "cpp" / "tests" / "fixtures" / "csv_importacion.json"
    )
    fixture = json.loads(archivo_fixture.read_text(encoding="utf-8"))
    ruta_csv = tmp_path / "grupos.csv"
    ruta_csv.write_bytes(fixture["contenido"].encode("utf-8"))

    grupos, errores = LectorCSV.leer_grupos(ruta_csv)

    assert errores == []
    assert len(grupos) == 1
    grupo = grupos[0]
    esperado = fixture["esperado"]
    assert grupo.codigo_gruplac == esperado["codigo_gruplac"]
    assert grupo.nombre == esperado["nombre"]
    assert grupo.categoria == esperado["categoria"]
    assert grupo.institucion_principal == esperado["institucion_principal"]
    assert grupo.lider == esperado["lider"]
