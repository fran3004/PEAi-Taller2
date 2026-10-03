"""
tests/fuentes/test_extraer_scienti.py
Pruebas automatizadas offline para extracción y modelos Pydantic de SCIENTI (GrupLAC y CvLAC).
"""

import json
from pathlib import Path

import pytest

from tools.fuentes.descargar_scienti import descargar_url
from tools.fuentes.modelos_scienti import GrupoGrupLAC, InvestigadorCvLAC


def test_oraculo_gruplac_canonico_valido():
    fixture_json = Path("tests/fixtures/scienti/gruplac_00000000002099.esperado.json")
    assert fixture_json.exists(), "El fixture esperado de GrupLAC no existe"

    data = json.loads(fixture_json.read_text(encoding="utf-8"))
    grupo = GrupoGrupLAC.model_validate(data)

    assert grupo.codigo_gruplac == "00000000002099"
    assert grupo.departamento_ciudad == "CESAR - VALLEDUPAR"
    assert "C" in (grupo.clasificacion or "")
    assert len(grupo.integrantes) >= 10, "El grupo debe tener al menos 10 integrantes"
    assert len(grupo.articulos) >= 10, "El grupo debe reportar artículos"
    assert len(grupo.softwares) >= 10, "El grupo debe reportar productos de software"


def test_oraculo_gruplac_vacio_valido():
    fixture_json = Path("tests/fixtures/scienti/gruplac_0000000002099.esperado.json")
    assert fixture_json.exists()

    data = json.loads(fixture_json.read_text(encoding="utf-8"))
    grupo = GrupoGrupLAC.model_validate(data)

    assert grupo.codigo_gruplac == "0000000002099"
    assert len(grupo.integrantes) == 0
    assert len(grupo.articulos) == 0


def test_oraculo_cvlac_valido():
    fixture_json = Path("tests/fixtures/scienti/cvlac_0000494917.esperado.json")
    assert fixture_json.exists(), "El fixture esperado de CvLAC no existe"

    data = json.loads(fixture_json.read_text(encoding="utf-8"))
    inv = InvestigadorCvLAC.model_validate(data)

    assert inv.codigo_rh == "0000494917"
    assert "Asociado" in (inv.categoria_declarada or "")
    assert len(inv.formacion) >= 1, "Debe tener registros de formación académica"
    assert len(inv.articulos) >= 10, "Debe tener al menos 10 artículos"
    assert len(inv.softwares) >= 5, "Debe tener productos de software"


def test_seguridad_host_no_permitido():
    url_invalida = "https://otro-servidor.com/datos"
    cache_temp = Path("datos/cache")

    with pytest.raises(ValueError, match="Host no permitido"):
        descargar_url(url_invalida, cache_temp)


def test_seguridad_protocolo_inseguro():
    url_http = "http://scienti.minciencias.gov.co/datos"
    cache_temp = Path("datos/cache")

    with pytest.raises(ValueError, match="Protocolo no permitido"):
        descargar_url(url_http, cache_temp)
