from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from pea import cli
from pea.excepciones import ErrorConexion


def test_exportar_csv_sin_conexion_no_crea_directorio(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    destino = tmp_path / "catalogo"
    monkeypatch.setattr(cli, "_obtener_cliente_desde_entorno", lambda: None)

    assert cli.comando_exportar_csv(str(destino)) == 1
    assert not destino.exists()
    assert "no hay conexión a Supabase" in capsys.readouterr().err


def test_exportar_csv_cancela_si_no_puede_recargar(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    class Catalogo:
        def __init__(self, cliente) -> None:
            self.cliente = cliente

        def recargar_todo(self) -> None:
            raise ErrorConexion("Servicio no disponible")

    destino = tmp_path / "catalogo"
    monkeypatch.setattr(cli, "_obtener_cliente_desde_entorno", lambda: object())
    monkeypatch.setattr(cli, "CatalogoInvestigacion", Catalogo)

    assert cli.comando_exportar_csv(str(destino)) == 1
    assert not destino.exists()
    assert "exportación cancelada" in capsys.readouterr().err


def test_exportar_csv_conserva_esquema_y_escapa_campos(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class Catalogo:
        def __init__(self, cliente) -> None:
            self.grupos = [
                SimpleNamespace(
                    codigo_gruplac="PRUEBA-01",
                    nombre='Grupo, "Investigación"',
                    categoria="A1",
                    lider="Líder",
                    institucion_principal="UPC",
                    activo=True,
                )
            ]
            self.investigadores = []
            self.multilista_productos = []

        def recargar_todo(self) -> None:
            return None

    destino = tmp_path / "catalogo"
    monkeypatch.setattr(cli, "_obtener_cliente_desde_entorno", lambda: object())
    monkeypatch.setattr(cli, "CatalogoInvestigacion", Catalogo)

    assert cli.comando_exportar_csv(str(destino)) == 0
    assert (destino / "grupos.csv").read_bytes() == (
        b"codigo_gruplac,nombre,categoria,lider,institucion_principal,activo\r\n"
        b'PRUEBA-01,"Grupo, ""Investigaci\xc3\xb3n""",A1,L\xc3\xadder,UPC,True\r\n'
    )
    assert (destino / "investigadores.csv").read_bytes().startswith(
        b"codigo_rh,nombre_completo,categoria"
    )
    assert (destino / "productos.csv").read_bytes().startswith(
        b"codigo_identificador,titulo,tipo_mayor"
    )


def test_exportadores_completos_python_cpp_coinciden_con_fixture_compartido(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fixture_path = (
        Path(__file__).parents[2] / "cpp" / "tests" / "fixtures" / "exportacion_csv.json"
    )
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

    class Catalogo:
        def __init__(self, cliente) -> None:
            self.grupos = [SimpleNamespace(**grupo) for grupo in fixture["grupos"]]
            self.investigadores = [
                SimpleNamespace(**investigador) for investigador in fixture["investigadores"]
            ]
            self.multilista_productos = [
                SimpleNamespace(**producto) for producto in fixture["productos"]
            ]

        def recargar_todo(self) -> None:
            return None

    monkeypatch.setattr(cli, "_obtener_cliente_desde_entorno", lambda: object())
    monkeypatch.setattr(cli, "CatalogoInvestigacion", Catalogo)
    destino = tmp_path / "exportacion"

    assert cli.comando_exportar_csv(str(destino)) == 0
    for nombre, esperado in fixture["esperado"].items():
        assert (destino / nombre).read_bytes() == esperado.encode("utf-8"), nombre
