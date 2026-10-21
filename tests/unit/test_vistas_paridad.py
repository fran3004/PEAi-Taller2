from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pea.estructuras.hipercubo import Hipercubo5D
from pea.servicios.servicio_estadisticas import ServicioEstadisticas


def _normalizar_json(valor: Any) -> Any:
    return json.loads(json.dumps(valor, ensure_ascii=False))


def test_vistas_analiticas_coinciden_con_el_contrato_compartido() -> None:
    ruta_fixture = (
        Path(__file__).resolve().parents[2]
        / "cpp"
        / "tests"
        / "fixtures"
        / "vistas_analiticas.json"
    )
    fixture = json.loads(ruta_fixture.read_text(encoding="utf-8"))
    cubo = Hipercubo5D()

    for producto in fixture["productos"]:
        cubo.acumular(
            grupo=producto["grupo"],
            investigador=producto["investigador"],
            categoria=producto["categoria"],
            anio=producto["anio"],
            validacion=producto["validacion"],
            producto_id=producto["id"],
        )

    servicio = ServicioEstadisticas(cubo)
    codigos_investigadores = fixture["investigadores"]
    vistas = {
        "institucional": servicio.obtener_vista_institucional(
            codigos_investigadores=codigos_investigadores
        ),
        "grupo": servicio.obtener_vista_grupo(
            "G1", codigos_investigadores=codigos_investigadores
        ),
        "investigador": servicio.obtener_vista_investigador("I1"),
    }

    assert {
        nombre: _normalizar_json(vista) for nombre, vista in vistas.items()
    } == fixture["esperado"]
