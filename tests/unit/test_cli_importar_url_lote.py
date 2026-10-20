from pathlib import Path
from types import SimpleNamespace

import pytest

import pea.cli as cli
from pea.ingesta.extractor_url import ExtractorURL
from pea.ingesta.servicio_ingesta import ServicioIngesta
from pea.servicios.servicio_dominio import CatalogoInvestigacion


def test_lee_codigos_gruplac_sin_repetirlos(tmp_path: Path) -> None:
    archivo = tmp_path / "grupos_upc.txt"
    archivo.write_text(
        "# Códigos entregados por la institución\n00000000002099\n\n00000000002099\n",
        encoding="utf-8",
    )

    assert cli._leer_codigos_grupos(archivo) == ["00000000002099"]


def test_rechaza_linea_no_numerica_en_archivo_de_grupos(tmp_path: Path) -> None:
    archivo = tmp_path / "grupos_upc.txt"
    archivo.write_text("00000000002099\ncodigo-invalido\n", encoding="utf-8")

    with pytest.raises(ValueError, match="línea 2"):
        cli._leer_codigos_grupos(archivo)


def test_importa_lote_desde_fixture_sin_conexion_de_red(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    codigo = "00000000002099"
    url = (
        "https://scienti.minciencias.gov.co/gruplac/jsp/visualiza/"
        f"visualizagr.jsp?nro={codigo}"
    )
    archivo_codigos = tmp_path / "grupos_upc.txt"
    archivo_codigos.write_text(f"{codigo}\n", encoding="utf-8")
    fixture = Path("tests/fixtures/scienti/gruplac_00000000002099.html")
    html_fixture = fixture.read_bytes()
    solicitudes: list[str] = []

    def obtener_fixture(solicitud_url: str, **_kwargs: object) -> SimpleNamespace:
        solicitudes.append(solicitud_url)
        return SimpleNamespace(
            status_code=200,
            content=html_fixture,
            encoding="ISO-8859-1",
            apparent_encoding="ISO-8859-1",
        )

    servicio_real = ServicioIngesta

    def servicio_con_cache_temporal(catalogo: CatalogoInvestigacion) -> ServicioIngesta:
        return servicio_real(
            catalogo,
            extractor_url=ExtractorURL(cache_dir=tmp_path / "cache"),
        )

    monkeypatch.setattr("pea.ingesta.extractor_url.requests.get", obtener_fixture)
    monkeypatch.setattr(cli, "ServicioIngesta", servicio_con_cache_temporal)

    codigo_salida = cli.main(
        [
            "importar-url",
            "--archivo-grupos",
            str(archivo_codigos),
            "--salida",
            str(tmp_path / "salida"),
        ]
    )

    salida = capsys.readouterr().out
    assert codigo_salida == 0
    assert solicitudes == [url]
    assert f"GrupLAC {codigo}: 1 grupo(s)" in salida
    assert (tmp_path / "salida" / f"GrupLAC-{codigo}" / f"GrupLAC-{codigo}.json").exists()
