from __future__ import annotations

from typing import Any

import pytest

from pea.datos.repositorios import RepositorioIntegrantes


class ClienteFalso:
    def __init__(self, filas: list[dict[str, Any]]) -> None:
        self.filas = filas
        self.parametros: dict[str, Any] | None = None

    def get_paginado(self, tabla: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        assert tabla == "integrantes_grupo"
        self.parametros = params
        return self.filas


def test_listar_resuelve_codigos_desde_relaciones_postgrest() -> None:
    cliente = ClienteFalso(
        [
            {
                "id": 21,
                "grupo_id": 3,
                "investigador_id": 5,
                "rol": "Investigador",
                "fecha_inicio": "2024-01",
                "activo": True,
                "es_ejemplo": True,
                "grupos": {"codigo_gruplac": "PRUEBA-GRUPO"},
                "investigadores": {"codigo_rh": "PRUEBA-INV"},
            }
        ]
    )

    integrantes = RepositorioIntegrantes(cliente).listar("PRUEBA-GRUPO")

    assert len(integrantes) == 1
    assert integrantes[0].codigo_gruplac == "PRUEBA-GRUPO"
    assert integrantes[0].codigo_rh == "PRUEBA-INV"
    assert integrantes[0].grupo_id == 3
    assert integrantes[0].investigador_id == 5
    assert cliente.parametros == {
        "select": "*,grupos!inner(codigo_gruplac),investigadores!inner(codigo_rh)",
        "grupos.codigo_gruplac": "eq.PRUEBA-GRUPO",
    }


def test_listar_falla_explicito_si_faltan_relaciones() -> None:
    cliente = ClienteFalso([{"id": 21, "grupo_id": 3, "investigador_id": 5}])

    with pytest.raises(ValueError, match="no incluye los códigos"):
        RepositorioIntegrantes(cliente).listar()
