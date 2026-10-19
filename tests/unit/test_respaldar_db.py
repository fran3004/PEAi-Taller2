from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError

import pytest

from tools.db import respaldar


class Respuesta:
    def __init__(self, contenido: object, content_range: str):
        self._contenido = json.dumps(contenido).encode("utf-8")
        self.headers = {"Content-Range": content_range}

    def __enter__(self) -> Respuesta:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._contenido


def _clave_anon() -> str:
    return "eyJhbGciOiJub25lIn0.eyJyb2xlIjoiYW5vbiJ9.c2ludGV0aWNh"


def test_rechaza_clave_service_role_sin_mostrarla() -> None:
    with pytest.raises(respaldar.ErrorRespaldo, match="nunca una clave secreta"):
        respaldar._validar_clave_publica("service_role_synthetic")


def test_autenticacion_usa_usuario_normal_y_no_imprime_credenciales(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PEA_USUARIO_CORREO", "prueba@example.invalid")
    monkeypatch.setenv("PEA_USUARIO_CLAVE", "contrasena-sintetica")
    capturadas: list[object] = []

    def urlopen(solicitud: object, timeout: int) -> Respuesta:
        capturadas.extend([solicitud, timeout])
        return Respuesta({"access_token": "jwt-sintetico"}, "0-0/1")

    monkeypatch.setattr(respaldar, "urlopen", urlopen)

    token = respaldar.obtener_token_autenticado("https://pea.supabase.co", _clave_anon())

    solicitud = capturadas[0]
    assert token == "jwt-sintetico"
    assert solicitud.get_header("Authorization") is None
    assert solicitud.get_header("Apikey") == _clave_anon()
    payload = json.loads(solicitud.data.decode("utf-8"))
    assert payload == {"email": "prueba@example.invalid", "password": "contrasena-sintetica"}


@pytest.mark.parametrize("codigo", [401, 403, 404])
def test_descarga_no_trata_errores_http_como_tablas_vacias(
    monkeypatch: pytest.MonkeyPatch, codigo: int
) -> None:
    def urlopen(_solicitud: object, timeout: int) -> None:
        raise HTTPError("https://pea.supabase.co/rest/v1/grupos", codigo, "error", None, BytesIO(b""))

    monkeypatch.setattr(respaldar, "urlopen", urlopen)

    with pytest.raises(respaldar.ErrorRespaldo, match=rf"HTTP {codigo}.*incompleto"):
        respaldar.descargar_tabla("https://pea.supabase.co", _clave_anon(), "grupos", "jwt-sintetico")


def test_descarga_verifica_todos_los_lotes_y_conteo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(respaldar, "TAMANO_LOTE", 2)
    respuestas = iter(
        [
            Respuesta([{"id": 1}, {"id": 2}], "0-1/3"),
            Respuesta([{"id": 3}], "2-2/3"),
        ]
    )
    rangos: list[str | None] = []

    def urlopen(solicitud: object, timeout: int) -> Respuesta:
        rangos.append(solicitud.get_header("Range"))
        return next(respuestas)

    monkeypatch.setattr(respaldar, "urlopen", urlopen)

    filas = respaldar.descargar_tabla("https://pea.supabase.co", _clave_anon(), "grupos", "jwt-sintetico")

    assert filas == [{"id": 1}, {"id": 2}, {"id": 3}]
    assert rangos == ["0-1", "2-3"]


def test_descarga_falla_si_falta_content_range(monkeypatch: pytest.MonkeyPatch) -> None:
    respuesta = Respuesta([{"id": 1}], "0-0/1")
    respuesta.headers = {}
    monkeypatch.setattr(respaldar, "urlopen", lambda *_args, **_kwargs: respuesta)

    with pytest.raises(respaldar.ErrorRespaldo, match="no devolvió Content-Range"):
        respaldar.descargar_tabla("https://pea.supabase.co", _clave_anon(), "grupos", "jwt-sintetico")


def test_respaldo_incompleto_devuelve_error_y_no_publica_archivo(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(respaldar, "cargar_configuracion", lambda: ("https://pea.supabase.co", _clave_anon()))
    monkeypatch.setattr(respaldar, "obtener_token_autenticado", lambda *_args: "jwt-sintetico")
    monkeypatch.setattr(respaldar, "consultar_revision_remota", lambda *_args: 7)

    def descargar(_url: str, _clave: str, tabla: str, _token: str) -> list[dict]:
        if tabla == "auditoria_cambios":
            raise respaldar.ErrorRespaldo("HTTP 403; respaldo incompleto.")
        return [{"id": 1}]

    monkeypatch.setattr(respaldar, "descargar_tabla", descargar)

    resultado = respaldar.respaldar()
    salida = capsys.readouterr()

    assert resultado == 1
    assert "[ERROR]" in salida.err
    assert "[OK]" not in salida.out
    assert not list((tmp_path / "datos" / "respaldos").glob("*.json"))


def test_respaldo_valida_y_publica_todas_las_tablas_incluida_auditoria(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(respaldar, "cargar_configuracion", lambda: ("https://pea.supabase.co", _clave_anon()))
    monkeypatch.setattr(respaldar, "obtener_token_autenticado", lambda *_args: "jwt-sintetico")
    revisiones = iter([7, 7])
    monkeypatch.setattr(respaldar, "consultar_revision_remota", lambda *_args: next(revisiones))
    monkeypatch.setattr(
        respaldar,
        "descargar_tabla",
        lambda _url, _clave, tabla, _token: [{"id": 1, "tabla": tabla}],
    )

    resultado = respaldar.respaldar()
    salida = capsys.readouterr()
    archivos = list((tmp_path / "datos" / "respaldos").glob("*.json"))

    assert resultado == 0
    assert "[OK] Respaldo completo e íntegro" in salida.out
    assert len(archivos) == 1
    datos = json.loads(archivos[0].read_text(encoding="utf-8"))
    assert set(datos["tablas"]) == set(respaldar.TABLAS_A_RESPALDAR)
    assert "auditoria_cambios" in datos["tablas"]
    assert datos["metadatos"]["filas_por_tabla"]["auditoria_cambios"] == 1
    assert datos["metadatos"]["revision"] == 7


def test_respaldo_no_publica_archivo_si_la_revision_cambia(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(respaldar, "cargar_configuracion", lambda: ("https://pea.supabase.co", _clave_anon()))
    monkeypatch.setattr(respaldar, "obtener_token_autenticado", lambda *_args: "jwt-sintetico")
    revisiones = iter([7, 8])
    monkeypatch.setattr(respaldar, "consultar_revision_remota", lambda *_args: next(revisiones))
    monkeypatch.setattr(
        respaldar,
        "descargar_tabla",
        lambda _url, _clave, tabla, _token: [{"id": 1, "tabla": tabla}],
    )

    resultado = respaldar.respaldar()
    salida = capsys.readouterr()

    assert resultado == 1
    assert "cambió durante el respaldo" in salida.err
    assert "[OK]" not in salida.out
    assert not list((tmp_path / "datos" / "respaldos").glob("*.json"))
